const dataUrl = `${import.meta.env.BASE_URL}data/jobs.json`

const FULL_TEXT_FIELDS = [
  'title',
  'company_name',
  'location',
  'salary',
  'experience',
  'education',
  'description',
  'requirement',
  'tags'
]

const STORAGE_KEY = 'jmil-manual-jobs'

let demoCache = null

async function loadDemoJobs() {
  if (!demoCache) {
    const response = await fetch(dataUrl)
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }
    const data = await response.json()
    demoCache = data.items || []
  }
  return demoCache
}

function loadStoredJobs() {
  try {
    const items = JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]')
    return Array.isArray(items) ? items : []
  } catch {
    return []
  }
}

export function saveJobsStatic(jobs) {
  const merged = new Map(loadStoredJobs().map(job => [job.job_id, job]))
  jobs.forEach(job => merged.set(job.job_id, job))
  localStorage.setItem(STORAGE_KEY, JSON.stringify([...merged.values()]))
  return jobs.length
}

async function loadAllJobs() {
  const merged = new Map((await loadDemoJobs()).map(job => [job.job_id, job]))
  loadStoredJobs().forEach(job => merged.set(job.job_id, job))
  return [...merged.values()].sort((a, b) =>
    String(b.scraped_at || '').localeCompare(String(a.scraped_at || ''))
  )
}

function includes(value, term) {
  return String(value || '').toLowerCase().includes(term.toLowerCase())
}

function countBy(jobs, field) {
  const counts = new Map()
  jobs.forEach(job => {
    const name = String(job[field] || '').trim()
    if (name) {
      counts.set(name, (counts.get(name) || 0) + 1)
    }
  })
  return [...counts.entries()]
    .map(([name, count]) => ({ name, count }))
    .sort((a, b) => b.count - a.count || a.name.localeCompare(b.name))
    .slice(0, 20)
}

export async function fetchJobsStatic(filters = {}) {
  const jobs = await loadAllJobs()
  const keyword = String(filters.keyword || '').trim()
  const company = String(filters.company || '').trim()
  const location = String(filters.location || '').trim()
  const q = String(filters.q || '').trim()

  const items = jobs
    .filter(
      job =>
        (!keyword || includes(job.keyword, keyword)) &&
        (!company || includes(job.company_name, company)) &&
        (!location || includes(job.location, location)) &&
        (!q || FULL_TEXT_FIELDS.some(field => includes(job[field], q)))
    )
    .slice(0, 200)

  return { items, limit: 200, offset: 0 }
}

export async function fetchStatsStatic() {
  const jobs = await loadAllJobs()
  return {
    total: jobs.length,
    latest_scraped_at: jobs.length ? jobs[0].scraped_at : null,
    keywords: countBy(jobs, 'keyword'),
    companies: countBy(jobs, 'company_name'),
    locations: countBy(jobs, 'location')
  }
}
