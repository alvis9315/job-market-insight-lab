# 本機啟動指令備忘

## 日常啟動(兩個 Terminal)

```bash
# Terminal 1:後端 API(在專案根目錄執行)
cd ~/Projects/job-market-insight-lab
source .venv/bin/activate
python -m job_collector.api
# → http://127.0.0.1:8000(健康檢查:http://127.0.0.1:8000/health)

# Terminal 2:前端 Dashboard(一定要先進 dashboard/)
cd ~/Projects/job-market-insight-lab/dashboard
npm run dev
# → 看 Terminal 顯示的網址,通常是 http://127.0.0.1:5173
#   若 5173 被別的專案佔用,vite 會自動換埠(5174、5175...),以畫面顯示為準
```

## 只有第一次(或重建環境時)才需要

```bash
cd ~/Projects/job-market-insight-lab

# Python 環境(需要 Python 3.10+,系統內建 3.9 不行,用 Homebrew 的)
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -e .
playwright install chromium        # 只有要用診斷收集功能才需要

# 前端依賴
cd dashboard
npm install
```

## 其他常用指令

```bash
# 本機預覽「靜態展示版」(跟 GitHub Pages 上一樣的版本)
cd dashboard && npm run dev:static

# 把 SQLite 資料匯出成靜態展示版用的 jobs.json
python -m job_collector.export_static

# CLI 小量診斷收集
python -m job_collector.cli --keyword "前端工程師 Vue" --pages 1 --show-browser
```

## 常見狀況

- `npm run dev` 報 `Missing script` 或找不到 package.json → 你在專案根目錄,要先 `cd dashboard`
- `python -m job_collector.api` 報 `No module named 'job_collector'` → venv 沒裝好,重跑 `pip install -e .`
- 資料都存在 `output/jobs.sqlite3`,想清空重來就刪掉 `output/` 下的 jobs.* 檔再重啟 API
- 部署:push 到 main 就會自動部署到 https://alvis9315.github.io/job-market-insight-lab/
