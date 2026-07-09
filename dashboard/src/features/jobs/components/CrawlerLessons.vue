<script setup>
import { AlertTriangle } from '@lucide/vue'
</script>

<template>
  <section class="panel crawler-lessons">
    <div class="lesson-icon" aria-hidden="true">
      <AlertTriangle :size="22" />
    </div>
    <div>
      <h2>反爬蟲觀察</h2>
      <p>
        這次測試顯示：職缺頁與 Network response 都可能被 Cloudflare challenge 擋下，因此本工具不做繞過，
        改採使用者可見內容的手動匯入。
      </p>
      <ul>
        <li>有效防護不是只擋 HTML，也要保護 JSON API 與分頁端點。</li>
        <li>Cloudflare、速率限制、session 連續性與行為檢查可以互補。</li>
        <li>資料工具應保留診斷與人工匯入路徑，避免把反爬偵測當成要硬闖的障礙。</li>
      </ul>
      <a
        class="lesson-link"
        href="https://thunderbit.com/zh-Hant/blog/how-to-bypass-cloudflare-scraping"
        target="_blank"
        rel="noreferrer"
      >
        延伸閱讀：Cloudflare scraping 方法整理
      </a>
    </div>
  </section>
</template>
