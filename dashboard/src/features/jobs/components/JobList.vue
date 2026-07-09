<script setup>
import { computed } from 'vue'
import { shortText } from '../../../utils/formatters'

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
  }
})

defineEmits(['select'])

const hasJobs = computed(() => props.jobs.length > 0)
</script>

<template>
  <article class="panel list-panel">
    <div class="section-title-row">
      <h2>職缺列表</h2>
      <span>{{ loading ? '讀取中...' : `${jobs.length} 筆` }}</span>
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
      <strong>{{ job.title || '未命名職缺' }}</strong>
      <span>{{ job.company_name || '未取得公司名稱' }}</span>
      <small>{{ shortText([job.location, job.salary, job.experience].filter(Boolean).join('｜'), 120) }}</small>
    </button>
  </article>
</template>
