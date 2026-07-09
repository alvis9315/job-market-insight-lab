from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from job_collector.config import CollectorConfig
from job_collector.crawler_104 import Crawler104
from job_collector.models import JobPost
from job_collector.storage import JobStorage

DEFAULT_DATABASE_PATH = Path("output/jobs.sqlite3")
DEFAULT_OUTPUT_DIR = Path("output")

app = FastAPI(title="Job Market Insight Lab API", version="0.2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CollectRequest(BaseModel):
    keyword: str = Field(default="前端工程師 Vue", min_length=1, max_length=80)
    start_url: str = Field(default="", max_length=1000)
    pages: int = Field(default=1, ge=1, le=10)
    headless: bool = True
    debug: bool = False
    min_delay_seconds: float = Field(default=2, ge=1, le=30)
    max_delay_seconds: float = Field(default=5, ge=1, le=60)


class ImportJobItem(BaseModel):
    job_id: str = Field(min_length=1, max_length=120)
    source: str = Field(default="manual", max_length=40)
    keyword: str = Field(default="", max_length=120)
    title: str = ""
    company_name: str = ""
    location: str = ""
    salary: str = ""
    experience: str = ""
    education: str = ""
    description: str = ""
    requirement: str = ""
    tags: str = ""
    job_url: str = ""
    scraped_at: str = ""


class ImportJobsRequest(BaseModel):
    input_format: str = Field(default="unknown", max_length=20)
    keyword: str = Field(default="", max_length=120)
    company_name: str = Field(default="", max_length=120)
    items: list[ImportJobItem] = Field(min_length=1, max_length=500)


def get_storage() -> JobStorage:
    return JobStorage(DEFAULT_DATABASE_PATH)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/jobs")
def list_jobs(
    keyword: str | None = Query(default=None),
    company: str | None = Query(default=None),
    location: str | None = Query(default=None),
    q: str | None = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> dict[str, Any]:
    storage = get_storage()
    jobs = storage.list_jobs(
        keyword=keyword,
        company=company,
        location=location,
        q=q,
        limit=limit,
        offset=offset,
    )
    return {"items": jobs, "limit": limit, "offset": offset}


@app.get("/api/jobs/{job_id}")
def get_job(job_id: str) -> dict[str, Any]:
    storage = get_storage()
    job = storage.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="找不到這筆職缺")
    return job


@app.get("/api/stats")
def get_stats() -> dict[str, Any]:
    return get_storage().stats()


@app.post("/api/import/jobs")
def import_parsed_jobs(payload: ImportJobsRequest) -> dict[str, Any]:
    jobs = []
    for item in payload.items:
        fields = item.model_dump()
        if not fields["scraped_at"]:
            fields.pop("scraped_at")
        jobs.append(JobPost(**fields))

    storage = get_storage()
    saved_count = storage.upsert_many(jobs)
    csv_path = storage.export_csv(DEFAULT_OUTPUT_DIR / "jobs.csv")
    excel_path = storage.export_excel(DEFAULT_OUTPUT_DIR / "jobs.xlsx")

    return {
        "input_format": payload.input_format,
        "parsed_count": len(jobs),
        "saved_count": saved_count,
        "keyword": jobs[0].keyword if jobs else payload.keyword,
        "company_name": jobs[0].company_name if jobs else payload.company_name,
        "csv_path": str(csv_path),
        "excel_path": str(excel_path),
        "items": [job.to_dict() for job in jobs[:20]],
    }


@app.post("/api/collect")
async def collect_jobs(payload: CollectRequest) -> dict[str, Any]:
    config = CollectorConfig(
        keyword=payload.keyword,
        start_url=payload.start_url.strip(),
        pages=payload.pages,
        headless=payload.headless,
        min_delay_seconds=payload.min_delay_seconds,
        max_delay_seconds=payload.max_delay_seconds,
        output_dir=str(DEFAULT_OUTPUT_DIR),
        database_path=str(DEFAULT_DATABASE_PATH),
        debug=payload.debug,
        debug_dir=str(DEFAULT_OUTPUT_DIR / "debug"),
        export_csv=True,
        export_excel=True,
    )
    crawler = Crawler104(config)
    search_urls = [crawler.build_search_url(page_no) for page_no in range(1, config.pages + 1)]
    jobs = await crawler.collect()

    storage = get_storage()
    saved_count = storage.upsert_many(jobs)
    csv_path = storage.export_csv(DEFAULT_OUTPUT_DIR / "jobs.csv")
    excel_path = storage.export_excel(DEFAULT_OUTPUT_DIR / "jobs.xlsx")

    return {
        "saved_count": saved_count,
        "csv_path": str(csv_path),
        "excel_path": str(excel_path),
        "debug": payload.debug,
        "debug_dir": config.debug_dir if payload.debug else "",
        "keyword": payload.keyword,
        "start_url": config.start_url,
        "source_mode": "custom_url" if config.start_url else "keyword_search",
        "pages": payload.pages,
        "search_urls": search_urls,
        "diagnostics": crawler.diagnostics,
    }


def main() -> None:
    uvicorn.run("job_collector.api:app", host="127.0.0.1", port=8000, reload=False)


if __name__ == "__main__":
    main()
