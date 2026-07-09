from __future__ import annotations

from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class CollectorConfig:
    keyword: str = "前端工程師 Vue"
    start_url: str = ""
    pages: int = 3
    headless: bool = True
    min_delay_seconds: float = 2
    max_delay_seconds: float = 5
    output_dir: str = "output"
    database_path: str = "output/jobs.sqlite3"
    debug: bool = False
    debug_dir: str = "output/debug"
    export_csv: bool = True
    export_excel: bool = True
    extra_query: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_file(cls, path: str | Path) -> "CollectorConfig":
        config_path = Path(path)
        if not config_path.exists():
            raise FileNotFoundError(f"找不到設定檔：{config_path}")

        data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
        return cls(**data)

    def override(self, **kwargs: Any) -> "CollectorConfig":
        overrides = {key: value for key, value in kwargs.items() if value is not None}
        return replace(self, **overrides)
