# Job Market Insight Lab

個人求職資料整理與反爬蟲學習專案。目標是把使用者可見的公開職缺資訊整理成 SQLite / CSV / Excel，並用 Vue 3 Dashboard 做查詢、篩選與統計。

這不是繞過網站防護的爬蟲框架。本專案不提供繞過 Cloudflare、Turnstile、驗證碼、登入、付費牆或權限限制的功能；診斷收集流程僅保留為小量診斷與學習用途，主要流程是手動匯入使用者在真實瀏覽器中已能看到的內容。

## 目前版本

`v0.2.0` 已包含三個部分：

```text
job-market-insight-lab
├─ src/job_collector
│  ├─ crawler_104.py      # Python + Playwright：小量診斷指定職缺頁
│  ├─ storage.py          # SQLite / CSV / Excel 儲存與查詢
│  ├─ export_static.py    # 匯出 jobs.json 給靜態展示版
│  ├─ api.py              # FastAPI：提供 Dashboard 讀取資料
│  ├─ cli.py              # CLI：命令列執行診斷收集
│  ├─ config.py
│  └─ models.py
├─ dashboard              # Vue 3 + Vite Dashboard
│  ├─ src/services/manualImport.js   # 手動匯入解析器（DOMParser，瀏覽器端執行）
│  └─ public/data/jobs.json   # 靜態展示版資料（預設為虛構示範資料）
├─ .github/workflows/deploy-pages.yml   # GitHub Pages 自動部署
├─ config.example.yaml
├─ requirements.txt
└─ pyproject.toml
```

## 設計原則

- 不登入
- 不抓履歷或個資
- 不繞過驗證碼、防機器人或權限限制
- 低頻率請求，避免造成網站負擔
- 不散布大量職缺資料、debug HTML、截圖或資料庫輸出
- 僅供個人求職分析、資料整理與學習展示使用

## 反爬蟲觀察與負責任使用

本專案在測試 104 公司職缺頁時，曾遇到 Cloudflare challenge。即使頁面在一般 Chrome 中可以正常顯示，Playwright 自動化流程仍可能只拿到「請稍候」或驗證頁，而不是職缺列表。進一步觀察 Network response 後，也可能看不到可直接使用的 JSON，代表網站方不只保護頁面 HTML，也保護背後的資料端點。

因此，本專案採取的結論是：

- 診斷收集只保留為小量測試與診斷，不加入繞過 Cloudflare、驗證碼、Turnstile 或防機器人機制的能力。
- 若網站明確回傳 challenge、access denied 或空資料，系統應顯示診斷結果，而不是偽裝成正常收集成功。
- 主要資料來源改為使用者在真實瀏覽器中已能看到的公開內容，再透過 HTML / 文字 / CSV 貼上匯入。
- 若未來支援 Network JSON 匯入，也應以使用者自行取得且可合法使用的 response 為前提，不自動重放受保護請求。

對網站方來說，這次實驗也整理出幾個防止爬蟲濫用的作法：

- 同時保護頁面與資料 API：不要只擋 HTML，職缺列表、搜尋、分頁、篩選等 JSON 端點也要有一致的存取控制。
- 使用分層防護：結合 WAF、Bot Management、JavaScript challenge、Turnstile、速率限制與行為偵測，而不是只依賴 User-Agent。
- 檢查 session 連續性：IP、Cookie、TLS / JA3 / JA4 指紋、語系、時區與瀏覽器行為應該合理一致。
- 對高風險路徑加強限制：搜尋、分頁、批次列表、詳細頁等容易被大量抓取的端點，應有更嚴格的頻率與異常偵測。
- 提供正式資料管道：若資料有合理再利用需求，優先提供官方 API、授權資料、匯出功能或合作流程，降低使用者用非正式方式抓取的動機。
- 減少個資暴露：公開頁面應避免放出不必要的個人資料，並對可識別資訊採取最小揭露原則。

本工具的定位是個人學習與求職分析，不是繞過網站防護的爬蟲框架。當網站方已透過 Cloudflare 或其他機制表達不接受自動化存取時，應尊重該邊界。

延伸閱讀：

- Thunderbit：如何在抓取時繞過 Cloudflare（2026 年仍然有效的方法）  
  https://thunderbit.com/zh-Hant/blog/how-to-bypass-cloudflare-scraping

## 架構理解

可以把它理解成：

```text
使用者可見的公開職缺內容
   ↓
手動匯入或小量診斷收集
   ↓
SQLite / CSV / Excel
   ↓
FastAPI 後端 API
   ↓
Vue 3 Dashboard
```

手動匯入的解析（HTML / 文字 / CSV）在瀏覽器端以 DOMParser 完成；Python 負責「儲存、查詢、CSV / Excel 匯出」；Vue 3 負責「解析、資料呈現、篩選、分析」。

HTML 解析有三層 fallback：職缺列表卡片 → 單一職缺詳細頁 → 頁面內嵌的 JSON-LD（`<script type="application/ld+json">`）。第三層讀的是 104 為 SEO 主動公開、存在於使用者可見頁面中的 schema.org 結構化資料，因此即使整頁隨手複製也能取得職缺名稱、完整說明與網址；此路徑只讀取頁面已公開的內容，不重放任何受保護的 API 請求。

## 後端安裝

### macOS / Linux

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
playwright install chromium
```

## 方式一：用 CLI 做小量診斷收集

```bash
cp config.example.yaml config.yaml
python -m job_collector.cli --config config.yaml
```

也可以直接帶參數：

```bash
python -m job_collector.cli --keyword "前端工程師 Vue" --pages 3 --headless
```

輸出位置：

```text
output/
├─ jobs.sqlite3
├─ jobs.csv
└─ jobs.xlsx
```

## 方式二：啟動 API

先啟動 FastAPI：

```bash
python -m job_collector.api
```

預設 API：

```text
http://127.0.0.1:8000
```

可用端點：

| Method | Path | 說明 |
|---|---|---|
| GET | `/health` | 健康檢查 |
| GET | `/api/jobs` | 查詢職缺列表 |
| GET | `/api/jobs/{job_id}` | 查詢單筆職缺 |
| GET | `/api/stats` | 查詢統計資料 |
| POST | `/api/import/jobs` | 儲存前端解析完成的匯入職缺 |
| POST | `/api/collect` | 透過 API 觸發小量診斷收集 |

常用查詢：

```bash
curl "http://127.0.0.1:8000/api/jobs?q=Vue&limit=20"
curl "http://127.0.0.1:8000/api/stats"
```

## 啟動 Vue 3 Dashboard

另開一個 Terminal：

```bash
cd dashboard
npm install
npm run dev
```

開啟：

```text
http://127.0.0.1:5173
```

Dashboard 目前包含：

- 職缺列表
- 單筆職缺詳細內容
- 全文搜尋（符合的字樣會以黃底標示）
- 關鍵字、公司、地點篩選
- 匯出篩選結果為 CSV / JSON（CSV 帶 BOM，Excel 可直接開啟；JSON 適合餵給 AI 工具）
- 關鍵字資料量圖表
- 公司分布圖表
- 從畫面觸發小量診斷收集
- 手動貼上 HTML / 文字 / CSV 匯入
- 反爬蟲觀察與負責任使用提示（常駐區塊）

Dashboard 有兩種資料模式：

- **API 模式（預設，本地開發）**：`npm run dev`，手動匯入在瀏覽器端解析後交給 FastAPI 寫入 SQLite，支援診斷收集。
- **靜態模式（展示部署）**：`npm run dev:static` 或 `npm run build:pages`，讀取 `public/data/jobs.json`；手動匯入照常可用，解析後存入瀏覽器 localStorage（只留在訪客自己的瀏覽器），診斷收集面板隱藏。

## 建議使用流程

第一次可以用 CLI 做小量診斷，確認環境與資料流正常：

```bash
python -m job_collector.cli --keyword "前端工程師 Vue" --pages 1 --show-browser
```

若有可用資料寫入 `output/jobs.sqlite3`，再啟動 API 與 Dashboard。若遇到 Cloudflare challenge，請改用 Dashboard 的手動匯入流程：

```bash
python -m job_collector.api
```

```bash
cd dashboard
npm install
npm run dev
```

## 靜態展示版與 GitHub Pages 部署

本專案的展示部署走純靜態路線：GitHub Pages 只放 Vue Dashboard 的 build 結果，沒有後端。FastAPI + SQLite 僅在本地作為資料整理工具使用。

資料流：

```text
本地整理資料（手動匯入 → SQLite）
   ↓ python -m job_collector.export_static
dashboard/public/data/jobs.json
   ↓ npm run build:pages
GitHub Pages 靜態網站（瀏覽器端篩選與統計）
```

repo 內建一份**虛構的示範資料**（`dashboard/public/data/jobs.json`），讓展示版開箱就有內容。若要改放自己的資料：

```bash
python -m job_collector.export_static
```

注意：`public/data/jobs.json` 會隨 repo 一起公開。依照本專案原則，請勿將大量真實職缺資料匯出後上傳，展示用途建議保留示範資料或僅放少量、去識別化的內容。

部署方式：push 到 `main` 後，`.github/workflows/deploy-pages.yml` 會自動 build 並發佈。首次使用需在 GitHub repo 的 **Settings → Pages → Source** 選擇 **GitHub Actions**。

本地預覽靜態版：

```bash
cd dashboard
npm run dev:static      # 開發模式
npm run build:pages && npm run preview   # 或看 build 結果
```

## 公開展示建議

若將本專案設為 public，建議遵守以下原則：

- Repo 名稱與 README 使用中性描述，例如 `job-market-insight-lab`，避免將作品包裝成特定網站爬蟲。
- 不提交 `output/`、SQLite、CSV、Excel、debug HTML、截圖或任何真實職缺資料。
- 診斷收集僅描述為學習用途，主流程強調手動匯入使用者可見內容。
- 不加入繞過 Cloudflare、Turnstile、驗證碼、登入或付費牆的程式碼與教學。
- 若引用外部文章，應放在延伸閱讀或反思來源，而不是作為照做的繞過指南。

## 後續可擴充

- 多關鍵字批次收集
- 公司黑名單 / 白名單
- 技能關鍵字統計
- 薪資文字標準化
- 履歷與職缺匹配分數
- 求職追蹤狀態：想投、已投、面試中、已拒絕
- Vue Dashboard 匯出篩選結果
- 將資料庫改為 PostgreSQL
