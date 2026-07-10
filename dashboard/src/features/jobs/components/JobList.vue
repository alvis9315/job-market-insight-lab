<script setup>
import { computed } from 'vue'
import { shortText } from '../../../utils/formatters'
import { exportJobsCsv, exportJobsJson } from '../../../utils/exporters'
import HighlightText from './HighlightText.vue'

const props = defineProps({
  jobs: {
    type: Array,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  selectedJob: {
    type: Object,
    default: null
  },
  highlight: {
    type: String,
    default: ''
  }
})

defineEmits(['select'])

const hasJobs = computed(() => props.jobs.length > 0)
</script>

<template>
  <article class="panel list-panel">
    <div class="section-title-row">
      <h2>職缺列表</h2>
      <div class="list-actions">
        <button type="button" class="secondary" :disabled="!hasJobs" @click="exportJobsCsv(jobs)">
          匯出 CSV
        </button>
        <button type="button" class="secondary" :disabled="!hasJobs" @click="exportJobsJson(jobs)">
          匯出 JSON
        </button>
        <span>{{ loading ? '讀取中...' : `${jobs.length} 筆` }}</span>
      </div>
    </div>
    <div v-if="!hasJobs" class="empty-state">
      目前沒有資料。可使用手動匯入貼上 HTML / 文字 / CSV。
    </div>
    <button
      v-for="job in jobs"
      :key="job.job_id"
      class="job-card"
      type="button"
      :class="{ active: selectedJob?.job_id === job.job_id }"
      @click="$emit('select', job)"
    >
      <strong><HighlightText :text="job.title || '未命名職缺'" :query="highlight" /></strong>
      <span><HighlightText :text="job.company_name || '未取得公司名稱'" :query="highlight" /></span>
      <small>
        <HighlightText
          :text="shortText([job.location, job.salary, job.experience].filter(Boolean).join('｜'), 120)"
          :query="highlight"
        />
      </small>
    </button>
  </article>
</template>
