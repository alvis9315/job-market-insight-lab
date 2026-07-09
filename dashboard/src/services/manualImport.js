// 手動匯入解析器：與原本後端 manual_import.py 行為對齊，
// HTML 解析改用瀏覽器內建 DOMParser。

const JOB_URL_PATTERN = /(?:https?:)?\/\/www\.104\.com\.tw\/job\/([a-z0-9]+)/i
const CUSTNAME_PATTERN = /custname="([^"]+)"/
const MAPS_PATTERN = /https:\/\/maps\.google\.com\.tw\/\?q=([^@"&]+)/

function normalizeText(value) {
  if (!value) {
    return ''
  }
  return String(value).replace(/\s+/g, ' ').trim()
}

function normalizeUrl(rawUrl) {
  const url = String(rawUrl || '')
  if (url.startsWith('//')) {
    return `https:${url}`
  }
  if (url.startsWith('/')) {
    return new URL(url, 'https://www.104.com.tw').href
  }
  return url
}

function normalizeMultiline(value) {
  if (!value) {
    return ''
  }
  return String(value)
    .split(/\r?\n/)
    .map(normalizeText)
    .filter(Boolean)
    .join('\n')
}

function unescapeHtml(value) {
  const doc = new DOMParser().parseFromString(String(value), 'text/html')
  return doc.documentElement.textContent || ''
}

async function stableManualId(value) {
  const data = new TextEncoder().encode(value)
  const digest = await crypto.subtle.digest('SHA-1', data)
  const hex = [...new Uint8Array(digest)].map(byte => byte.toString(16).padStart(2, '0')).join('')
  return `manual-${hex.slice(0, 12)}`
}

// 對齊 Python 版以 f-string 內插 list 產生的字串（tags 參與 job_id 雜湊時的格式）
function pyListRepr(items) {
  return `[${items.map(item => `'${item}'`).join(', ')}]`
}

function scrapedAtNow() {
  return new Date().toISOString().replace('Z', '+00:00')
}

function makeJob(fields) {
  return {
    job_id: '',
    source: '',
    keyword: '',
    title: '',
    company_name: '',
    location: '',
    salary: '',
    experience: '',
    education: '',
    description: '',
    requirement: '',
    tags: '',
    job_url: '',
    scraped_at: scrapedAtNow(),
    ...fields
  }
}

function inferCompanyName(content) {
  const custMatch = CUSTNAME_PATTERN.exec(content)
  if (custMatch) {
    return normalizeText(unescapeHtml(custMatch[1]))
  }
  const mapsMatch = MAPS_PATTERN.exec(content)
  if (mapsMatch) {
    try {
      return normalizeText(decodeURIComponent(mapsMatch[1]))
    } catch {
      return normalizeText(mapsMatch[1])
    }
  }
  return ''
}

function resolveImportContext(content, keyword, companyName) {
  const resolvedCompany = normalizeText(companyName) || inferCompanyName(content)
  let resolvedKeyword = normalizeText(keyword)
  if (!resolvedKeyword) {
    resolvedKeyword = `${resolvedCompany || '104'} 手動匯入`
  }
  return { keyword: resolvedKeyword, companyName: resolvedCompany }
}

// 對齊 Python HTMLParser 逐段收集文字再以空白串接的行為
function textJoin(element) {
  const walker = element.ownerDocument.createTreeWalker(element, NodeFilter.SHOW_TEXT)
  const chunks = []
  while (walker.nextNode()) {
    const text = normalizeText(walker.currentNode.nodeValue)
    if (text) {
      chunks.push(text)
    }
  }
  return normalizeText(chunks.join(' '))
}

function lastNonEmpty(values) {
  for (let i = values.length - 1; i >= 0; i -= 1) {
    if (values[i]) {
      return values[i]
    }
  }
  return ''
}

async function parseListHtmlJobs(doc, { keyword, companyName }) {
  const jobs = []
  const containers = doc.querySelectorAll('div.info-wrapper.job-list-container--cprofile')

  for (const container of containers) {
    const title = lastNonEmpty([...container.querySelectorAll('.info-name')].map(textJoin))
    if (!title) {
      continue
    }

    const anchors = container.querySelectorAll('a[data-gtm-job="點擊工作"]')
    const href = anchors.length ? normalizeUrl(anchors[anchors.length - 1].getAttribute('href') || '') : ''
    const tags = [...container.querySelectorAll('.info-tags__text')].map(textJoin).filter(Boolean)
    const salary =
      lastNonEmpty([...container.querySelectorAll('.info-othertags__text')].map(textJoin)) ||
      normalizeText(container.getAttribute('jobsalarydesc') || '')

    const idMatch = JOB_URL_PATTERN.exec(href)
    const jobId = idMatch ? idMatch[1] : await stableManualId(`${title}|${href}|${pyListRepr(tags)}`)

    jobs.push(
      makeJob({
        job_id: jobId,
        source: '104-manual-html',
        keyword,
        title,
        company_name: companyName,
        location: tags[0] || '',
        experience: tags[1] || '',
        education: tags[2] || '',
        salary,
        tags: tags.join('，'),
        job_url: href
      })
    )
  }
  return jobs
}

function extractDetailTitle(doc) {
  const candidates = [
    doc.querySelector('meta[property="og:title"]')?.getAttribute('content'),
    doc.querySelector('meta[name="title"]')?.getAttribute('content'),
    doc.querySelector('h1')?.textContent,
    doc.querySelector('[class*="job-title"], [class*="jobName"], [class*="job-name"]')?.textContent
  ]
  for (const candidate of candidates) {
    const title = normalizeText(candidate)
    if (title) {
      return title
    }
  }
  return ''
}

function extractDetailDescription(doc) {
  const attrDescription = doc.querySelector('[jobdescription]')?.getAttribute('jobdescription')
  if (attrDescription) {
    return normalizeMultiline(attrDescription)
  }
  const element = doc.querySelector('[class*="job-description__content"]')
  return element ? normalizeMultiline(element.textContent) : ''
}

function splitDescriptionRequirement(description) {
  const marker = '【需求條件】'
  if (!description.includes(marker)) {
    return { description, requirement: '' }
  }
  const index = description.indexOf(marker)
  return {
    description: normalizeMultiline(description.slice(0, index)),
    requirement: normalizeMultiline(description.slice(index + marker.length))
  }
}

function extractDetailCategories(doc) {
  const categories = []
  doc.querySelectorAll('[data-gtm-content="職務類別"] u').forEach(node => {
    const category = normalizeText(node.textContent)
    if (category && !categories.includes(category)) {
      categories.push(category)
    }
  })
  return categories
}

function extractDetailLocation(doc) {
  const area = normalizeText(doc.querySelector('[addressarea]')?.getAttribute('addressarea'))
  const address = normalizeText(doc.querySelector('.job-address span')?.textContent)
  if (area && address && !address.startsWith(area)) {
    return `${area} ${address}`
  }
  return address || area
}

async function parseDetailHtmlJob(doc, rawContent, { keyword, companyName }) {
  const rawDescription = extractDetailDescription(doc)
  const salary = normalizeText(doc.querySelector('[salary]')?.getAttribute('salary'))
  const location = extractDetailLocation(doc)
  const categories = extractDetailCategories(doc)

  if (!rawDescription && !salary && !location && !categories.length) {
    return []
  }

  const title = extractDetailTitle(doc) || '單一職缺詳細內容'
  const { description, requirement } = splitDescriptionRequirement(rawDescription)
  const urlMatch = /(?:https?:)?\/\/www\.104\.com\.tw\/job\/[a-z0-9]+[^"\s<]*/i.exec(rawContent)
  const jobUrl = urlMatch ? normalizeUrl(urlMatch[0]) : ''
  const idMatch = JOB_URL_PATTERN.exec(jobUrl)
  const jobId = idMatch
    ? idMatch[1]
    : await stableManualId(`${title}|${companyName}|${location}|${description.slice(0, 80)}`)

  return [
    makeJob({
      job_id: jobId,
      source: 'manual-html-detail',
      keyword,
      title,
      company_name: companyName,
      location,
      salary,
      description,
      requirement,
      tags: categories.join('，'),
      job_url: jobUrl
    })
  ]
}

async function parseHtmlJobs(content, context) {
  const doc = new DOMParser().parseFromString(content, 'text/html')
  const listJobs = await parseListHtmlJobs(doc, context)
  if (listJobs.length) {
    return listJobs
  }
  return parseDetailHtmlJob(doc, content, context)
}

// 極簡 RFC 4180 CSV 解析：支援引號欄位、跳脫的雙引號與欄內換行
function parseCsvRows(text) {
  const rows = []
  let row = []
  let field = ''
  let inQuotes = false

  for (let i = 0; i < text.length; i += 1) {
    const char = text[i]
    if (inQuotes) {
      if (char === '"') {
        if (text[i + 1] === '"') {
          field += '"'
          i += 1
        } else {
          inQuotes = false
        }
      } else {
        field += char
      }
    } else if (char === '"') {
      inQuotes = true
    } else if (char === ',') {
      row.push(field)
      field = ''
    } else if (char === '\n' || char === '\r') {
      if (char === '\r' && text[i + 1] === '\n') {
        i += 1
      }
      row.push(field)
      field = ''
      rows.push(row)
      row = []
    } else {
      field += char
    }
  }
  if (field !== '' || row.length) {
    row.push(field)
    rows.push(row)
  }
  return rows.filter(cells => cells.some(cell => cell.trim() !== ''))
}

async function parseCsvJobs(content, { keyword, companyName }) {
  const rows = parseCsvRows(content)
  if (rows.length < 2) {
    return []
  }
  const headers = rows[0].map(header => header.trim())
  const jobs = []

  for (const cells of rows.slice(1)) {
    const record = {}
    headers.forEach((header, index) => {
      record[header] = cells[index] ?? ''
    })
    const pick = (...keys) => {
      for (const key of keys) {
        if (record[key]) {
          return record[key]
        }
      }
      return ''
    }

    const title = normalizeText(pick('title', '職缺', '職稱'))
    if (!title) {
      continue
    }
    const jobUrl = normalizeText(pick('job_url', 'url', '網址'))
    const idMatch = JOB_URL_PATTERN.exec(jobUrl)
    const jobId = record.job_id || (idMatch ? idMatch[1] : await stableManualId(`${title}|${jobUrl}`))

    jobs.push(
      makeJob({
        job_id: normalizeText(jobId),
        source: 'manual-csv',
        keyword: normalizeText(pick('keyword')) || keyword,
        title,
        company_name: normalizeText(pick('company_name', '公司')) || companyName,
        location: normalizeText(pick('location', '地點')),
        salary: normalizeText(pick('salary', '薪資')),
        experience: normalizeText(pick('experience', '經驗')),
        education: normalizeText(pick('education', '學歷')),
        description: normalizeText(pick('description', '描述')),
        requirement: normalizeText(pick('requirement', '條件')),
        tags: normalizeText(pick('tags', '標籤')),
        job_url: jobUrl
      })
    )
  }
  return jobs
}

async function parseTextJobs(content, { keyword, companyName }) {
  const lines = content
    .split(/\r?\n/)
    .map(normalizeText)
    .filter(Boolean)
  const jobs = []

  for (let index = 0; index < lines.length; index += 1) {
    const line = lines[index]
    if (!['工程師', '專員', '經理', '顧問'].some(word => line.includes(word))) {
      continue
    }
    if (line.length > 80) {
      continue
    }
    const nextLine = lines[index + 1] || ''
    const parts = nextLine
      .split(/[｜|]/)
      .map(normalizeText)
      .filter(Boolean)

    jobs.push(
      makeJob({
        job_id: await stableManualId(`${line}|${nextLine}|${index}`),
        source: 'manual-text',
        keyword,
        title: line,
        company_name: companyName,
        location: parts[0] || '',
        experience: parts[1] || '',
        education: parts[2] || '',
        tags: nextLine
      })
    )
  }
  return jobs
}

function detectFormat(text) {
  if (text.includes('<') && text.includes('>')) {
    return 'html'
  }
  const firstLine = text.split(/\r?\n/, 1)[0]
  if (firstLine.includes(',') && (firstLine.includes('title') || firstLine.includes('職缺'))) {
    return 'csv'
  }
  return 'text'
}

export async function parseManualJobs(content, { keyword = '', companyName = '', inputFormat = 'auto' } = {}) {
  const text = String(content || '').trim()
  if (!text) {
    return { inputFormat: 'empty', keyword: '', companyName: '', jobs: [] }
  }

  const context = resolveImportContext(text, keyword, companyName)
  const selectedFormat = inputFormat === 'auto' ? detectFormat(text) : inputFormat

  let jobs
  if (selectedFormat === 'html') {
    jobs = await parseHtmlJobs(text, context)
  } else if (selectedFormat === 'csv') {
    jobs = await parseCsvJobs(text, context)
  } else {
    jobs = await parseTextJobs(text, context)
  }

  return { inputFormat: selectedFormat, keyword: context.keyword, companyName: context.companyName, jobs }
}
