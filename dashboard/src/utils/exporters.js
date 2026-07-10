const EXPORT_COLUMNS = [
  'job_id',
  'source',
  'keyword',
  'title',
  'company_name',
  'location',
  'salary',
  'experience',
  'education',
  'description',
  'requirement',
  'tags',
  'job_url',
  'scraped_at'
]

function csvEscape(value) {
  const text = String(value ?? '')
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`
  }
  return text
}

function downloadFile(filename, content, mimeType) {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  link.click()
  URL.revokeObjectURL(url)
}

function dateStamp() {
  return new Date().toISOString().slice(0, 10)
}

export function exportJobsCsv(jobs) {
  const rows = [EXPORT_COLUMNS.join(',')]
  jobs.forEach(job => {
    rows.push(EXPORT_COLUMNS.map(column => csvEscape(job[column])).join(','))
  })
  // BOM 讓 Excel 直接開啟時正確辨識 UTF-8 中文
  downloadFile(`jobs-${dateStamp()}.csv`, '\ufeff' + rows.join('\r\n'), 'text/csv;charset=utf-8')
}

export function exportJobsJson(jobs) {
  const payload = jobs.map(job =>
    Object.fromEntries(EXPORT_COLUMNS.map(column => [column, job[column] ?? '']))
  )
  downloadFile(`jobs-${dateStamp()}.json`, JSON.stringify(payload, null, 2), 'application/json')
}
