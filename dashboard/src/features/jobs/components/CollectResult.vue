<script setup>
defineProps({
  result: {
    type: Object,
    required: true
  }
})
</script>

<template>
  <section class="panel collect-result">
    <div class="section-title-row">
      <h2>收集診斷結果</h2>
      <span>寫入 / 更新 {{ result.saved_count }} 筆</span>
    </div>
    <p>
      來源：{{ result.source_mode === 'custom_url' ? '自訂 URL' : '關鍵字搜尋' }}；
      關鍵字：{{ result.keyword }}，頁數：{{ result.pages }}。
    </p>
    <p v-if="result.debug_dir">
      Debug：{{ result.debug_dir }}，包含 HTML、截圖與 anchors 清單。
    </p>
    <div v-if="result.diagnostics?.length" class="diagnostics-list">
      <div
        v-for="item in result.diagnostics"
        :key="`${item.page}-${item.url}`"
        :class="['diagnostic-item', { warning: item.warning }]"
      >
        <strong>第 {{ item.page }} 頁：{{ item.page_title || '未取得標題' }}</strong>
        <span>Playwright 掃到 {{ item.anchor_count }} 個連結</span>
        <small v-if="item.warning">{{ item.warning }}</small>
      </div>
    </div>
    <div class="url-list">
      <a
        v-for="(url, index) in result.search_urls || []"
        :key="url"
        :href="url"
        target="_blank"
        rel="noreferrer"
      >
        第 {{ index + 1 }} 頁：{{ url }}
      </a>
    </div>
  </section>
</template>
