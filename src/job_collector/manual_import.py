from __future__ import annotations

import csv
import hashlib
import html
import re
from html.parser import HTMLParser
from io import StringIO
from typing import Any
from urllib.parse import unquote

from job_collector.crawler_104 import normalize_text, normalize_url
from job_collector.models import JobPost


JOB_URL_PATTERN = re.compile(r"(?:https?:)?//www\.104\.com\.tw/job/([a-z0-9]+)", re.IGNORECASE)
COMPANY_NAME_PATTERN = re.compile(r'custname="([^"]+)"')
HTML_ATTR_PATTERN_TEMPLATE = r'\b{attr}="([^"]*)"'


def stable_manual_id(value: str) -> str:
    digest = hashlib.sha1(value.encode("utf-8")).hexdigest()[:12]
    return f"manual-{digest}"


def infer_company_name(content: str) -> str:
    match = COMPANY_NAME_PATTERN.search(content)
    if match:
        return normalize_text(html.unescape(match.group(1)))
    maps_match = re.search(r"https://maps\.google\.com\.tw/\?q=([^@\"&]+)", content)
    if maps_match:
        return normalize_text(unquote(maps_match.group(1)))
    return ""


def resolve_import_context(content: str, *, keyword: str, company_name: str) -> tuple[str, str]:
    resolved_company = normalize_text(company_name) or infer_company_name(content)
    resolved_keyword = normalize_text(keyword)
    if not resolved_keyword:
        resolved_keyword = f"{resolved_company or '104'} 手動匯入"
    return resolved_keyword, resolved_company


class CompanyJobHTMLParser(HTMLParser):
    def __init__(self, *, keyword: str, company_name: str) -> None:
        super().__init__(convert_charrefs=True)
        self.keyword = keyword
        self.company_name = company_name
        self.jobs: list[JobPost] = []
        self.current: dict[str, Any] | None = None
        self.capture_stack: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value or "" for key, value in attrs}
        class_names = set(attr.get("class", "").split())

        if self.current:
            self.current["depth"] += 1
            for capture in self.capture_stack:
                capture["depth"] += 1

        if tag == "div" and {"info-wrapper", "job-list-container--cprofile"}.issubset(class_names):
            self.current = {
                "depth": 1,
                "title": "",
                "href": "",
                "tags": [],
                "salary": attr.get("jobsalarydesc", ""),
            }
            return

        if not self.current:
            return

        if tag == "a" and attr.get("data-gtm-job") == "點擊工作":
            self.current["href"] = normalize_url(attr.get("href", ""))

        if "info-name" in class_names:
            self.capture_stack.append({"kind": "title", "depth": 1, "text": []})
        elif "info-tags__text" in class_names:
            self.capture_stack.append({"kind": "tag", "depth": 1, "text": []})
        elif "info-othertags__text" in class_names:
            self.capture_stack.append({"kind": "salary", "depth": 1, "text": []})

    def handle_data(self, data: str) -> None:
        if not self.current:
            return
        text = normalize_text(data)
        if not text:
            return
        for capture in self.capture_stack:
            capture["text"].append(text)

    def handle_endtag(self, tag: str) -> None:
        if not self.current:
            return

        finished: list[dict[str, Any]] = []
        for capture in self.capture_stack:
            capture["depth"] -= 1
            if capture["depth"] <= 0:
                finished.append(capture)

        for capture in finished:
            self.capture_stack.remove(capture)
            text = normalize_text(" ".join(capture["text"]))
            if capture["kind"] == "title" and text:
                self.current["title"] = text
            elif capture["kind"] == "tag" and text:
                self.current["tags"].append(text)
            elif capture["kind"] == "salary" and text:
                self.current["salary"] = text

        self.current["depth"] -= 1
        if self.current["depth"] <= 0:
            self.finish_current_job()

    def finish_current_job(self) -> None:
        if not self.current:
            return

        title = normalize_text(self.current.get("title", ""))
        href = normalize_url(self.current.get("href", ""))
        if not title:
            self.current = None
            return

        tags = [normalize_text(tag) for tag in self.current.get("tags", []) if normalize_text(tag)]
        job_id_match = JOB_URL_PATTERN.search(href)
        job_id = job_id_match.group(1) if job_id_match else stable_manual_id(f"{title}|{href}|{tags}")

        self.jobs.append(
            JobPost(
                job_id=job_id,
                source="104-manual-html",
                keyword=self.keyword,
                title=title,
                company_name=self.company_name,
                location=tags[0] if len(tags) > 0 else "",
                experience=tags[1] if len(tags) > 1 else "",
                education=tags[2] if len(tags) > 2 else "",
                salary=normalize_text(self.current.get("salary", "")),
                tags="，".join(tags),
                job_url=href,
            )
        )
        self.current = None


def parse_html_jobs(content: str, *, keyword: str, company_name: str) -> list[JobPost]:
    parser = CompanyJobHTMLParser(keyword=keyword, company_name=company_name)
    parser.feed(content)
    if parser.jobs:
        return parser.jobs
    return parse_detail_html_job(content, keyword=keyword, company_name=company_name)


def normalize_multiline(value: str | None) -> str:
    if not value:
        return ""
    lines = [normalize_text(line) for line in value.splitlines()]
    return "\n".join(line for line in lines if line)


def extract_html_attr(content: str, attr: str) -> str:
    pattern = HTML_ATTR_PATTERN_TEMPLATE.format(attr=re.escape(attr))
    match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return html.unescape(match.group(1))


def strip_tags(value: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", " ", value))


def extract_detail_title(content: str) -> str:
    patterns = [
        r'<meta[^>]+property="og:title"[^>]+content="([^"]+)"',
        r'<meta[^>]+name="title"[^>]+content="([^"]+)"',
        r'<h1[^>]*>(.*?)</h1>',
        r'class="[^"]*(?:job-title|jobName|job-name)[^"]*"[^>]*>(.*?)<',
    ]
    for pattern in patterns:
        match = re.search(pattern, content, flags=re.IGNORECASE | re.DOTALL)
        if match:
            title = normalize_text(strip_tags(match.group(1)))
            if title:
                return title
    return ""


def extract_detail_description(content: str) -> str:
    attr_description = extract_html_attr(content, "jobdescription")
    if attr_description:
        return normalize_multiline(attr_description)

    match = re.search(
        r'class="[^"]*job-description__content[^"]*"[^>]*>(.*?)</p>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if match:
        return normalize_multiline(strip_tags(match.group(1)))
    return ""


def split_description_requirement(description: str) -> tuple[str, str]:
    marker = "【需求條件】"
    if marker not in description:
        return description, ""
    before, after = description.split(marker, 1)
    return normalize_multiline(before), normalize_multiline(after)


def extract_detail_categories(content: str) -> list[str]:
    categories = []
    for match in re.finditer(
        r'data-gtm-content="職務類別".*?<u[^>]*>(.*?)</u>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    ):
        category = normalize_text(strip_tags(match.group(1)))
        if category and category not in categories:
            categories.append(category)
    return categories


def extract_detail_location(content: str) -> str:
    area = normalize_text(extract_html_attr(content, "addressarea"))
    address_match = re.search(
        r'class="[^"]*job-address[^"]*"[^>]*>.*?<span[^>]*>(.*?)</span>',
        content,
        flags=re.IGNORECASE | re.DOTALL,
    )
    address = normalize_text(strip_tags(address_match.group(1))) if address_match else ""
    if area and address and not address.startswith(area):
        return f"{area} {address}"
    return address or area


def parse_detail_html_job(content: str, *, keyword: str, company_name: str) -> list[JobPost]:
    description = extract_detail_description(content)
    salary = normalize_text(extract_html_attr(content, "salary"))
    location = extract_detail_location(content)
    categories = extract_detail_categories(content)

    if not any([description, salary, location, categories]):
        return []

    title = extract_detail_title(content) or "單一職缺詳細內容"
    description, requirement = split_description_requirement(description)
    tags = "，".join(categories)
    job_url_match = re.search(r'(?:https?:)?//www\.104\.com\.tw/job/[a-z0-9]+[^"\s<]*', content, flags=re.IGNORECASE)
    job_url = normalize_url(job_url_match.group(0)) if job_url_match else ""
    job_id_match = JOB_URL_PATTERN.search(job_url)
    job_id = job_id_match.group(1) if job_id_match else stable_manual_id(f"{title}|{company_name}|{location}|{description[:80]}")

    return [
        JobPost(
            job_id=job_id,
            source="manual-html-detail",
            keyword=keyword,
            title=title,
            company_name=company_name,
            location=location,
            salary=salary,
            description=description,
            requirement=requirement,
            tags=tags,
            job_url=job_url,
        )
    ]


def parse_csv_jobs(content: str, *, keyword: str, company_name: str) -> list[JobPost]:
    reader = csv.DictReader(StringIO(content))
    jobs: list[JobPost] = []

    for row in reader:
        title = normalize_text(row.get("title") or row.get("職缺") or row.get("職稱") or "")
        if not title:
            continue
        job_url = normalize_text(row.get("job_url") or row.get("url") or row.get("網址") or "")
        match = JOB_URL_PATTERN.search(job_url)
        job_id = row.get("job_id") or (match.group(1) if match else stable_manual_id(f"{title}|{job_url}"))
        jobs.append(
            JobPost(
                job_id=normalize_text(job_id),
                source="manual-csv",
                keyword=normalize_text(row.get("keyword") or keyword),
                title=title,
                company_name=normalize_text(row.get("company_name") or row.get("公司") or company_name),
                location=normalize_text(row.get("location") or row.get("地點") or ""),
                salary=normalize_text(row.get("salary") or row.get("薪資") or ""),
                experience=normalize_text(row.get("experience") or row.get("經驗") or ""),
                education=normalize_text(row.get("education") or row.get("學歷") or ""),
                description=normalize_text(row.get("description") or row.get("描述") or ""),
                requirement=normalize_text(row.get("requirement") or row.get("條件") or ""),
                tags=normalize_text(row.get("tags") or row.get("標籤") or ""),
                job_url=job_url,
            )
        )
    return jobs


def parse_text_jobs(content: str, *, keyword: str, company_name: str) -> list[JobPost]:
    lines = [normalize_text(line) for line in content.splitlines()]
    lines = [line for line in lines if line]
    jobs: list[JobPost] = []

    for index, line in enumerate(lines):
        if "工程師" not in line and "專員" not in line and "經理" not in line and "顧問" not in line:
            continue
        if len(line) > 80:
            continue
        next_line = lines[index + 1] if index + 1 < len(lines) else ""
        parts = [normalize_text(part) for part in re.split(r"[｜|]", next_line) if normalize_text(part)]
        jobs.append(
            JobPost(
                job_id=stable_manual_id(f"{line}|{next_line}|{index}"),
                source="manual-text",
                keyword=keyword,
                title=line,
                company_name=company_name,
                location=parts[0] if len(parts) > 0 else "",
                experience=parts[1] if len(parts) > 1 else "",
                education=parts[2] if len(parts) > 2 else "",
                tags=next_line,
            )
        )
    return jobs


def parse_manual_jobs(
    content: str,
    *,
    keyword: str,
    company_name: str,
    input_format: str = "auto",
) -> tuple[str, list[JobPost]]:
    text = content.strip()
    if not text:
        return "empty", []

    keyword, company_name = resolve_import_context(text, keyword=keyword, company_name=company_name)

    selected_format = input_format
    if input_format == "auto":
        if "<" in text and ">" in text:
            selected_format = "html"
        elif "," in text.splitlines()[0] and ("title" in text.splitlines()[0] or "職缺" in text.splitlines()[0]):
            selected_format = "csv"
        else:
            selected_format = "text"

    if selected_format == "html":
        return selected_format, parse_html_jobs(text, keyword=keyword, company_name=company_name)
    if selected_format == "csv":
        return selected_format, parse_csv_jobs(text, keyword=keyword, company_name=company_name)
    return selected_format, parse_text_jobs(text, keyword=keyword, company_name=company_name)
