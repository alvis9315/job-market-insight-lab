from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from job_collector.storage import JobStorage

DEFAULT_DATABASE_PATH = Path("output/jobs.sqlite3")
DEFAULT_OUTPUT_PATH = Path("dashboard/public/data/jobs.json")


def export_static_json(database_path: str | Path, output_path: str | Path) -> Path:
    storage = JobStorage(database_path)
    dataframe = storage.to_dataframe()
    items = json.loads(dataframe.to_json(orient="records", force_ascii=False))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(items),
        "items": items,
    }

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description="將 SQLite 職缺資料匯出成 Dashboard 靜態展示版使用的 jobs.json")
    parser.add_argument("--database", default=str(DEFAULT_DATABASE_PATH), help="SQLite 資料庫路徑")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH), help="輸出 JSON 路徑")
    args = parser.parse_args()

    path = export_static_json(args.database, args.output)
    print(f"已匯出靜態資料：{path}")


if __name__ == "__main__":
    main()
