# 104 Job Dashboard

Vue 3 + Vite Dashboard，讀取 FastAPI 的職缺資料。

## 啟動

先在專案根目錄啟動後端：

```bash
python -m job_collector.api
```

再啟動前端：

```bash
cd dashboard
npm install
npm run dev
```

開啟：

```text
http://127.0.0.1:5173
```

## API Proxy

Vite dev server 已設定 proxy：

```js
server: {
  proxy: {
    '/api': 'http://127.0.0.1:8000',
    '/health': 'http://127.0.0.1:8000'
  }
}
```

所以前端可以直接呼叫 `/api/jobs`、`/api/stats`。
