import { fetchJson } from './apiClient'
import { fetchJobsStatic, fetchStatsStatic } from './staticJobs'

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

export function importPastedJobs(payload) {
  if (isStaticMode) {
    return Promise.reject(new Error('靜態展示版不提供手動匯入，請在本地啟動 API 使用。'))
  }
  return fetchJson(`${apiBase}/api/import/paste`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
}
