from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass(slots=True)
class JobPost:
    job_id: str
    source: str
    keyword: str
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
    scraped_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
