from __future__ import annotations

import argparse
import asyncio
from pathlib import Path

from job_collector.config import CollectorConfig
from job_collector.crawler_104 import Crawler104
from job_collector.storage import JobStorage


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Job Market Insight Lab 小量診斷收集工具")
    parser.add_argument("--config", default=None, help="設定檔路徑，例如 config.yaml")
    parser.add_argument("--keyword", default=None, help="搜尋關鍵字，例如：前端工程師 Vue")
    parser.add_argument("--start-url", default=None, help="職缺列表網址；提供後會優先使用此網址並依 pages 替換 page 參數")
    parser.add_argument("--pages", type=int, default=None, help="要讀取的搜尋結果頁數")
    parser.add_argument("--headless", action="store_true", help="使用無頭瀏覽器模式")
    parser.add_argument("--show-browser", action="store_true", help="顯示瀏覽器執行過程")
    parser.add_argument("--database-path", default=None, help="SQLite 輸出路徑")
    parser.add_argument("--output-dir", default=None, help="CSV / Excel 輸出資料夾")
    parser.add_argument("--debug", action="store_true", help="輸出 HTML、截圖與 anchors 清單到 output/debug")
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> CollectorConfig:
    if args.config:
        config = CollectorConfig.from_file(args.config)
    else:
        config = CollectorConfig()

    headless = None
    if args.headless:
        headless = True
    if args.show_browser:
        headless = False

    return config.override(
        keyword=args.keyword,
        start_url=args.start_url,
        pages=args.pages,
        headless=headless,
        database_path=args.database_path,
        output_dir=args.output_dir,
        debug=True if args.debug else None,
    )


async def main_async() -> None:
    args = parse_args()
    config = load_config(args)

    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    crawler = Crawler104(config)
    jobs = await crawler.collect()

    storage = JobStorage(config.database_path)
    saved_count = storage.upsert_many(jobs)
    print(f"已寫入 / 更新 {saved_count} 筆到 SQLite：{config.database_path}")

    if config.export_csv:
        csv_path = storage.export_csv(output_dir / "jobs.csv")
        print(f"已匯出 CSV：{csv_path}")

    if config.export_excel:
        excel_path = storage.export_excel(output_dir / "jobs.xlsx")
        print(f"已匯出 Excel：{excel_path}")


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
