from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable, Any

import pandas as pd

from job_collector.models import JobPost


COLUMNS = [
    "job_id",
    "source",
    "keyword",
    "title",
    "company_name",
    "location",
    "salary",
    "experience",
    "education",
    "description",
    "requirement",
    "tags",
    "job_url",
    "scraped_at",
]


class JobStorage:
    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.database_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    source TEXT NOT NULL,
                    keyword TEXT NOT NULL,
                    title TEXT,
                    company_name TEXT,
                    location TEXT,
                    salary TEXT,
                    experience TEXT,
                    education TEXT,
                    description TEXT,
                    requirement TEXT,
                    tags TEXT,
                    job_url TEXT,
                    scraped_at TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_keyword ON jobs(keyword)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_scraped_at ON jobs(scraped_at)")

    def upsert_many(self, jobs: Iterable[JobPost]) -> int:
        rows = [job.to_dict() for job in jobs]
        if not rows:
            return 0

        placeholders = ", ".join([f":{column}" for column in COLUMNS])
        assignments = ", ".join([f"{column}=excluded.{column}" for column in COLUMNS if column != "job_id"])

        sql = f"""
            INSERT INTO jobs ({", ".join(COLUMNS)})
            VALUES ({placeholders})
            ON CONFLICT(job_id) DO UPDATE SET {assignments}
        """

        with self._connect() as conn:
            conn.executemany(sql, rows)

        return len(rows)

    def list_jobs(
        self,
        *,
        keyword: str | None = None,
        company: str | None = None,
        location: str | None = None,
        q: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[dict[str, Any]]:
        where: list[str] = []
        params: dict[str, Any] = {
            "limit": max(1, min(limit, 500)),
            "offset": max(0, offset),
        }

        if keyword:
            where.append("keyword LIKE :keyword")
            params["keyword"] = f"%{keyword}%"

        if company:
            where.append("company_name LIKE :company")
            params["company"] = f"%{company}%"

        if location:
            where.append("location LIKE :location")
            params["location"] = f"%{location}%"

        if q:
            where.append(
                "(" 
                "title LIKE :q OR company_name LIKE :q OR location LIKE :q OR "
                "salary LIKE :q OR experience LIKE :q OR education LIKE :q OR "
                "description LIKE :q OR requirement LIKE :q OR tags LIKE :q"
                ")"
            )
            params["q"] = f"%{q}%"

        where_sql = f"WHERE {' AND '.join(where)}" if where else ""
        sql = f"""
            SELECT *
            FROM jobs
            {where_sql}
            ORDER BY scraped_at DESC
            LIMIT :limit OFFSET :offset
        """

        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [dict(row) for row in rows]

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM jobs WHERE job_id = :job_id", {"job_id": job_id}).fetchone()
            return dict(row) if row else None

    def stats(self) -> dict[str, Any]:
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) AS count FROM jobs").fetchone()["count"]
            keywords = conn.execute(
                """
                SELECT keyword AS name, COUNT(*) AS count
                FROM jobs
                GROUP BY keyword
                ORDER BY count DESC, keyword ASC
                LIMIT 20
                """
            ).fetchall()
            companies = conn.execute(
                """
                SELECT company_name AS name, COUNT(*) AS count
                FROM jobs
                WHERE COALESCE(company_name, '') != ''
                GROUP BY company_name
                ORDER BY count DESC, company_name ASC
                LIMIT 20
                """
            ).fetchall()
            locations = conn.execute(
                """
                SELECT location AS name, COUNT(*) AS count
                FROM jobs
                WHERE COALESCE(location, '') != ''
                GROUP BY location
                ORDER BY count DESC, location ASC
                LIMIT 20
                """
            ).fetchall()
            latest = conn.execute("SELECT MAX(scraped_at) AS latest FROM jobs").fetchone()["latest"]

        return {
            "total": total,
            "latest_scraped_at": latest,
            "keywords": [dict(row) for row in keywords],
            "companies": [dict(row) for row in companies],
            "locations": [dict(row) for row in locations],
        }

    def to_dataframe(self) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query("SELECT * FROM jobs ORDER BY scraped_at DESC", conn)

    def export_csv(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_csv(path, index=False, encoding="utf-8-sig")
        return path

    def export_excel(self, output_path: str | Path) -> Path:
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.to_dataframe().to_excel(path, index=False)
        return path
