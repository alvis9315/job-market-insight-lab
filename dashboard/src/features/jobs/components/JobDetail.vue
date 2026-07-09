<script setup>
defineProps({
  job: {
    type: Object,
    default: null
  }
})
</script>

<template>
  <article class="panel detail-panel">
    <template v-if="job">
      <div class="section-title-row">
        <h2>{{ job.title || '未命名職缺' }}</h2>
        <a v-if="job.job_url" :href="job.job_url" target="_blank" rel="noreferrer">開啟原始頁</a>
      </div>
      <div class="meta-grid">
        <div><span>公司</span><strong>{{ job.company_name || '-' }}</strong></div>
        <div><span>地點</span><strong>{{ job.location || '-' }}</strong></div>
        <div><span>薪資</span><strong>{{ job.salary || '-' }}</strong></div>
        <div><span>經驗</span><strong>{{ job.experience || '-' }}</strong></div>
        <div><span>學歷</span><strong>{{ job.education || '-' }}</strong></div>
        <div><span>搜尋批次</span><strong>{{ job.keyword || '-' }}</strong></div>
      </div>
      <h3>工作內容</h3>
      <p class="long-text">{{ job.description || '尚未取得工作內容。' }}</p>
      <h3>條件要求</h3>
      <p class="long-text">{{ job.requirement || '尚未取得條件要求。' }}</p>
      <h3>標籤文字</h3>
      <p class="tag-text">{{ job.tags || '尚未取得標籤。' }}</p>
    </template>
    <div v-else class="empty-state">請選擇一筆職缺。</div>
  </article>
</template>
