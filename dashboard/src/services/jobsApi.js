import { fetchJson } from './apiClient'
import { fetchJobsStatic, fetchStatsStatic, saveJobsStatic } from './staticJobs'

export const isStaticMode = import.meta.env.VITE_STATIC_DATA === '1'

const apiBase = ''

export function buildJobsQuery(filters) {
  const params = new URLSearchParams()
  Object.entries(filters).forEach(([key, value]) => {
    const trimmedValue = String(value || '').trim()
    if (trimmedValue) {
      params.set(key, trimmedValue)
    }
  })
  params.set('limit', '200')
  return params.toString()
}

export function fetchJobs(filters) {
  if (isStaticMode) {
    return fetchJobsStatic(filters)
  }
  return fetchJson(`${apiBase}/api/jobs?${buildJobsQuery(filters)}`)
}

export function fetchStats() {
  if (isStaticMode) {
    return fetchStatsStatic()
  }
  return fetchJson(`${apiBase}/api/stats`)
}

export function collectJobs(payload) {
  if (isStaticMode) {
    return Promise.reject(new Error('靜態展示版不提供診斷收集，請在本地啟動 API 使用。'))
  }
  return fetchJson(`${apiBase}/api/collect`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}

export async function importParsedJobs(parsed) {
  const summary = {
    input_format: parsed.inputFormat,
    parsed_count: parsed.jobs.length,
    saved_count: 0,
    keyword: parsed.keyword,
    company_name: parsed.companyName,
    items: parsed.jobs.slice(0, 20)
  }

  if (!parsed.jobs.length) {
    return summary
  }

  if (isStaticMode) {
    return { ...summary, saved_count: saveJobsStatic(parsed.jobs) }
  }

  return fetchJson(`${apiBase}/api/import/jobs`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      input_format: parsed.inputFormat,
      keyword: parsed.keyword,
      company_name: parsed.companyName,
      items: parsed.jobs
    })
  })
}
