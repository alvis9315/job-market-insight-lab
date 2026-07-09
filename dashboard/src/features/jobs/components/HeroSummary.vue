<script setup>
import { computed } from 'vue'
import { formatDateTime } from '../../../utils/date'

const props = defineProps({
  stats: {
    type: Object,
    required: true
  }
})

const latestUpdatedAt = computed(() => formatDateTime(props.stats.latest_scraped_at))
</script>

<template>
  <section class="hero">
    <div>
      <p class="eyebrow">Personal Job Intelligence</p>
      <h1>Job Market Insight Lab</h1>
      <p class="subtitle">整理使用者可見的公開職缺內容，支援手動貼上 HTML / 文字 / CSV 後匯入分析，並保留小量診斷收集流程作為學習紀錄。</p>
    </div>
    <div class="summary-card">
      <span>目前資料量</span>
      <strong>{{ stats.total }}</strong>
      <small>最近更新：{{ latestUpdatedAt }}</small>
    </div>
  </section>
</template>
