from __future__ import annotations

import asyncio
import json
import random
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlencode, urljoin, urlparse, urlunparse

from playwright.async_api import Browser, Page, async_playwright

from job_collector.config import CollectorConfig
from job_collector.models import JobPost


JOB_ID_PATTERN = re.compile(r"/job/([^/?#]+)")
WHITESPACE_PATTERN = re.compile(r"\s+")


@dataclass(slots=True)
class JobLink:
    job_id: str
    url: str
    title_hint: str = ""


def normalize_text(value: str | None) -> str:
    if not value:
        return ""
    return WHITESPACE_PATTERN.sub(" ", value).strip()


def normalize_url(raw_url: str) -> str:
    if raw_url.startswith("//"):
        return "https:" + raw_url
    if raw_url.startswith("/"):
        return urljoin("https://www.104.com.tw", raw_url)
    return raw_url


def get_job_id(url: str) -> str | None:
    match = JOB_ID_PATTERN.search(url)
    if not match:
        return None
    return match.group(1)


def with_page_param(url: str, page_no: int) -> str:
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    query["page"] = str(page_no)
    return urlunparse(parsed._replace(query=urlencode(query, doseq=True)))


def extract_between(text: str, start_labels: list[str], end_labels: list[str], max_chars: int = 3000) -> str:
    start_pos = -1
    selected_label = ""

    for label in start_labels:
        pos = text.find(label)
        if pos != -1 and (start_pos == -1 or pos < start_pos):
            start_pos = pos
            selected_label = label

    if start_pos == -1:
        return ""

    content_start = start_pos + len(selected_label)
    end_pos = len(text)

    for label in end_labels:
        pos = text.find(label, content_start)
        if pos != -1 and pos < end_pos:
            end_pos = pos

    return normalize_text(text[content_start:end_pos])[:max_chars]


def extract_after_label(text: str, labels: list[str], max_chars: int = 120) -> str:
    for label in labels:
        pattern = re.compile(re.escape(label) + r"\s*[:：]?\s*([^\n\r]{1," + str(max_chars) + r"})")
        match = pattern.search(text)
        if match:
            return normalize_text(match.group(1))
    return ""


def infer_fields(body_text: str) -> dict[str, str]:
    text = body_text.replace("\r", "\n")
    return {
        "location": extract_after_label(text, ["工作地點", "上班地點"]),
        "salary": extract_after_label(text, ["工作待遇", "薪資待遇", "待遇"]),
        "experience": extract_after_label(text, ["工作經歷", "經歷要求", "經歷"]),
        "education": extract_after_label(text, ["學歷要求", "學歷"]),
        "description": extract_between(
            text,
            ["工作內容"],
            ["條件要求", "職務需求", "其他條件", "福利制度", "公司介紹", "應徵方式"],
        ),
        "requirement": extract_between(
            text,
            ["條件要求", "職務需求", "其他條件"],
            ["福利制度", "公司介紹", "應徵方式", "聯絡方式"],
        ),
    }


class Crawler104:
    def __init__(self, config: CollectorConfig) -> None:
        self.config = config
        self.diagnostics: list[dict[str, Any]] = []

    def build_search_url(self, page_no: int) -> str:
        if self.config.start_url:
            return with_page_param(self.config.start_url, page_no)

        query: dict[str, Any] = {
            "keyword": self.config.keyword,
            "page": page_no,
            "jobsource": "joblist_search",
        }
        query.update(self.config.extra_query)
        return "https://www.104.com.tw/jobs/search/?" + urlencode(query)

    async def collect(self) -> list[JobPost]:
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.config.headless)
            context = await browser.new_context(locale="zh-TW")
            page = await context.new_page()

            try:
                links = await self.collect_links(page)
                print(f"共找到 {len(links)} 個職缺連結，開始讀取詳細頁")

                jobs: list[JobPost] = []
                for index, link in enumerate(links, start=1):
                    await self.delay()
                    print(f"[{index}/{len(links)}] 讀取：{link.title_hint or link.job_id}")
                    job = await self.parse_detail_page(page, link)
                    jobs.append(job)

                return jobs
            finally:
                await browser.close()

    async def collect_links(self, page: Page) -> list[JobLink]:
        all_links: dict[str, JobLink] = {}

        for page_no in range(1, self.config.pages + 1):
            search_url = self.build_search_url(page_no)
            print(f"讀取搜尋頁第 {page_no} 頁：{search_url}")
            await page.goto(search_url, wait_until="domcontentloaded", timeout=60_000)
            await self.safe_wait_network_idle(page)
            await self.auto_scroll(page)

            anchors = await page.evaluate(
                """
                () => Array.from(document.querySelectorAll('a')).map(a => ({
                    href: a.href || '',
                    text: (a.innerText || a.title || '').trim()
                }))
                """
            )
            page_title = await page.title()
            self.record_diagnostics(page_no, search_url, page_title, anchors)
            await self.write_debug_snapshot(page, page_no, search_url, page_title, anchors)

            before_count = len(all_links)
            for anchor in anchors:
                raw_href = anchor.get("href", "")
                href = normalize_url(raw_href)
                if not self.is_valid_job_url(href):
                    continue

                job_id = get_job_id(href)
                if not job_id:
                    continue

                if job_id not in all_links:
                    all_links[job_id] = JobLink(
                        job_id=job_id,
                        url=href,
                        title_hint=normalize_text(anchor.get("text", "")),
                    )

            print(f"第 {page_no} 頁掃到 {len(anchors)} 個連結，新增 {len(all_links) - before_count} 筆")
            await self.delay()

        return list(all_links.values())

    async def parse_detail_page(self, page: Page, link: JobLink) -> JobPost:
        try:
            await page.goto(link.url, wait_until="domcontentloaded", timeout=60_000)
            await self.safe_wait_network_idle(page)

            raw = await page.evaluate(
                """
                () => {
                    const metaDescription = document.querySelector('meta[name="description"]')?.content || '';
                    const ogTitle = document.querySelector('meta[property="og:title"]')?.content || '';
                    const h1 = document.querySelector('h1')?.innerText || '';
                    const title = h1 || ogTitle || document.title || '';
                    const company = Array.from(document.querySelectorAll('a[href*="/company/"]'))
                        .map(el => (el.innerText || '').trim())
                        .find(Boolean) || '';
                    const tags = Array.from(document.querySelectorAll('a, span, button'))
                        .map(el => (el.innerText || '').trim())
                        .filter(text => text.length > 1 && text.length <= 24)
                        .slice(0, 80)
                        .join(', ');
                    const bodyText = document.body?.innerText || '';
                    return { title, company, tags, metaDescription, bodyText };
                }
                """
            )

            body_text = raw.get("bodyText", "") or ""
            inferred = infer_fields(body_text)

            title = normalize_text(raw.get("title", "")) or link.title_hint
            company = normalize_text(raw.get("company", ""))

            if not inferred["description"]:
                inferred["description"] = normalize_text(raw.get("metaDescription", ""))[:1500]

            return JobPost(
                job_id=link.job_id,
                source="104",
                keyword=self.config.keyword,
                title=title,
                company_name=company,
                location=inferred["location"],
                salary=inferred["salary"],
                experience=inferred["experience"],
                education=inferred["education"],
                description=inferred["description"],
                requirement=inferred["requirement"],
                tags=normalize_text(raw.get("tags", ""))[:1500],
                job_url=link.url,
            )
        except Exception as exc:
            print(f"讀取失敗：{link.url}，原因：{exc}")
            return JobPost(
                job_id=link.job_id,
                source="104",
                keyword=self.config.keyword,
                title=link.title_hint,
                job_url=link.url,
                description=f"讀取失敗：{exc}",
            )

    @staticmethod
    def is_valid_job_url(url: str) -> bool:
        parsed = urlparse(url)
        if "104.com.tw" not in parsed.netloc:
            return False
        if "/job/" not in parsed.path:
            return False
        return get_job_id(url) is not None

    async def delay(self) -> None:
        min_delay = self.config.min_delay_seconds
        max_delay = max(self.config.max_delay_seconds, min_delay)
        await asyncio.sleep(random.uniform(min_delay, max_delay))

    def record_diagnostics(
        self,
        page_no: int,
        search_url: str,
        page_title: str,
        anchors: list[dict[str, str]],
    ) -> None:
        anchor_hosts = [urlparse(anchor.get("href", "")).netloc for anchor in anchors]
        is_cloudflare = "請稍候" in page_title or any("cloudflare.com" in host for host in anchor_hosts)
        warning = ""
        if is_cloudflare:
            warning = "Playwright 看到的是 Cloudflare 請稍候/驗證頁，不是真正的職缺列表。"

        self.diagnostics.append(
            {
                "page": page_no,
                "url": search_url,
                "page_title": page_title,
                "anchor_count": len(anchors),
                "is_cloudflare_challenge": is_cloudflare,
                "warning": warning,
            }
        )

    async def write_debug_snapshot(
        self,
        page: Page,
        page_no: int,
        search_url: str,
        page_title: str,
        anchors: list[dict[str, str]],
    ) -> None:
        if not self.config.debug:
            return

        debug_dir = Path(self.config.debug_dir)
        debug_dir.mkdir(parents=True, exist_ok=True)
        prefix = debug_dir / f"page-{page_no}"

        html_path = prefix.with_suffix(".html")
        png_path = prefix.with_suffix(".png")
        anchors_path = debug_dir / f"page-{page_no}-anchors.json"

        html_path.write_text(await page.content(), encoding="utf-8")
        anchors_payload = {
            "url": search_url,
            "page_title": page_title,
            "anchor_count": len(anchors),
            "anchors": anchors,
        }
        anchors_path.write_text(json.dumps(anchors_payload, ensure_ascii=False, indent=2), encoding="utf-8")
        await page.screenshot(path=str(png_path), full_page=True)

        print(f"Debug 輸出：{html_path} / {png_path} / {anchors_path}")

    @staticmethod
    async def safe_wait_network_idle(page: Page) -> None:
        try:
            await page.wait_for_load_state("networkidle", timeout=15_000)
        except Exception:
            pass

    @staticmethod
    async def auto_scroll(page: Page) -> None:
        await page.evaluate(
            """
            async () => {
                const delay = ms => new Promise(resolve => setTimeout(resolve, ms));
                const maxScrolls = 6;
                for (let i = 0; i < maxScrolls; i++) {
                    window.scrollTo(0, document.body.scrollHeight);
                    await delay(500);
                }
                window.scrollTo(0, 0);
            }
            """
        )
