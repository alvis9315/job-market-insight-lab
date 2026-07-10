<script setup>
import HighlightText from './HighlightText.vue'

defineProps({
  job: {
    type: Object,
    default: null
  },
  highlight: {
    type: String,
    default: ''
  }
})
</script>

<template>
  <article class="panel detail-panel">
    <template v-if="job">
      <div class="section-title-row">
        <h2><HighlightText :text="job.title || '未命名職缺'" :query="highlight" /></h2>
        <a v-if="job.job_url" :href="job.job_url" target="_blank" rel="noreferrer">開啟原始頁</a>
      </div>
      <div class="meta-grid">
        <div><span>公司</span><strong><HighlightText :text="job.company_name || '-'" :query="highlight" /></strong></div>
        <div><span>地點</span><strong><HighlightText :text="job.location || '-'" :query="highlight" /></strong></div>
        <div><span>薪資</span><strong><HighlightText :text="job.salary || '-'" :query="highlight" /></strong></div>
        <div><span>經驗</span><strong><HighlightText :text="job.experience || '-'" :query="highlight" /></strong></div>
        <div><span>學歷</span><strong><HighlightText :text="job.education || '-'" :query="highlight" /></strong></div>
        <div><span>搜尋批次</span><strong><HighlightText :text="job.keyword || '-'" :query="highlight" /></strong></div>
      </div>
      <h3>工作內容</h3>
      <p class="long-text"><HighlightText :text="job.description || '尚未取得工作內容。'" :query="highlight" /></p>
      <h3>條件要求</h3>
      <p class="long-text"><HighlightText :text="job.requirement || '尚未取得條件要求。'" :query="highlight" /></p>
      <h3>標籤文字</h3>
      <p class="tag-text"><HighlightText :text="job.tags || '尚未取得標籤。'" :query="highlight" /></p>
    </template>
    <div v-else class="empty-state">請選擇一筆職缺。</div>
  </article>
</template>
