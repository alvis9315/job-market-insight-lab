<script setup>
import { onMounted, ref, watch } from 'vue'

import CollectPanel from '../features/jobs/components/CollectPanel.vue'
import CollectResult from '../features/jobs/components/CollectResult.vue'
import CrawlerLessons from '../features/jobs/components/CrawlerLessons.vue'
import FiltersPanel from '../features/jobs/components/FiltersPanel.vue'
import HeroSummary from '../features/jobs/components/HeroSummary.vue'
import JobDetail from '../features/jobs/components/JobDetail.vue'
import JobList from '../features/jobs/components/JobList.vue'
import ManualImportPanel from '../features/jobs/components/ManualImportPanel.vue'
import StatsCharts from '../features/jobs/components/StatsCharts.vue'
import { collectJobs, fetchJobs, fetchStats, importParsedJobs, isStaticMode } from '../services/jobsApi'
import { parseManualJobs } from '../services/manualImport'

const jobs = ref([])
const stats = ref({ total: 0, keywords: [], companies: [], locations: [], latest_scraped_at: '' })
const loading = ref(false)
const collecting = ref(false)
const importing = ref(false)
const errorMessage = ref('')
const collectResult = ref(null)
const importResult = ref(null)
const selectedJob = ref(null)

const filters = ref({
  q: '',
  keyword: '',
  company: '',
  location: ''
})

const collectForm = ref({
  keyword: '前端工程師 Vue',
  startUrl: '',
  pages: 1,
  headless: true,
  debug: true
})

const importForm = ref({
  companyName: '',
  inputFormat: 'auto',
  content: ''
})

async function loadJobs() {
  loading.value = true
  errorMessage.value = ''
  try {
    const data = await fetchJobs(filters.value)
    jobs.value = data.items
    if (!data.items.length) {
      selectedJob.value = null
    } else if (!selectedJob.value || !data.items.some(job => job.job_id === selectedJob.value.job_id)) {
      selectedJob.value = data.items[0]
    }
  } catch (error) {
    errorMessage.value = `讀取職缺失敗：${error.message}`
  } finally {
    loading.value = false
  }
}

async function loadStats() {
  try {
    stats.value = await fetchStats()
  } catch (error) {
    errorMessage.value = `讀取統計失敗：${error.message}`
  }
}

async function reloadAll() {
  await Promise.all([loadJobs(), loadStats()])
}

async function handleCollect() {
  collecting.value = true
  errorMessage.value = ''
  collectResult.value = null
  try {
    const result = await collectJobs({
      keyword: collectForm.value.keyword,
      start_url: collectForm.value.startUrl.trim(),
      pages: Number(collectForm.value.pages),
      headless: collectForm.value.headless,
      debug: collectForm.value.debug
    })
    collectResult.value = result
    filters.value.keyword = collectForm.value.keyword
    await reloadAll()
  } catch (error) {
    errorMessage.value = `收集職缺失敗：${error.message}`
  } finally {
    collecting.value = false
  }
}

async function handleManualImport() {
  importing.value = true
  errorMessage.value = ''
  importResult.value = null
  try {
    const parsed = await parseManualJobs(importForm.value.content, {
      keyword: '',
      companyName: importForm.value.companyName,
      inputFormat: importForm.value.inputFormat
    })
    const result = await importParsedJobs(parsed)
    importResult.value = result
    filters.value.keyword = result.keyword || ''
    await reloadAll()
    const importedJobId = result.items?.[0]?.job_id
    if (importedJobId) {
      selectedJob.value = jobs.value.find(job => job.job_id === importedJobId) || result.items[0]
    }
  } catch (error) {
    errorMessage.value = `手動匯入失敗：${error.message}`
  } finally {
    importing.value = false
  }
}

function resetFilters() {
  filters.value = { q: '', keyword: '', company: '', location: '' }
  loadJobs()
}

function openJob(job) {
  selectedJob.value = job
}

watch(
  () => importForm.value.content,
  () => {
    importResult.value = null
  }
)

onMounted(reloadAll)
</script>

<template>
  <main class="page-shell">
    <HeroSummary :stats="stats" />
    <section v-if="isStaticMode" class="panel static-note">
      <p>
        這是 GitHub Pages 靜態展示版：內建資料為虛構示範職缺，篩選、統計與手動匯入解析皆在瀏覽器端完成。
        你匯入的資料只會存在自己瀏覽器的 localStorage，不會上傳；診斷收集需在本地啟動 FastAPI 才能使用。
      </p>
    </section>
    <template v-if="!isStaticMode">
      <CollectPanel v-model="collectForm" :collecting="collecting" @submit="handleCollect" />
      <CollectResult v-if="collectResult" :result="collectResult" />
    </template>
    <CrawlerLessons />
    <ManualImportPanel v-model="importForm" :importing="importing" :result="importResult" @submit="handleManualImport" />

    <p v-if="errorMessage" class="error-message">{{ errorMessage }}</p>

    <FiltersPanel v-model="filters" :stats="stats" @apply="loadJobs" @reset="resetFilters" />

    <section class="content-grid">
      <JobList :jobs="jobs" :loading="loading" :selected-job="selectedJob" :highlight="filters.q" @select="openJob" />
      <JobDetail :job="selectedJob" :highlight="filters.q" />
    </section>

    <StatsCharts :stats="stats" />
  </main>
</template>
