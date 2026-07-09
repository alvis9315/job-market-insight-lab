export function formatErrorDetail(detail, fallback) {
  if (!detail) {
    return fallback
  }
  if (typeof detail === 'string') {
    return detail
  }
  if (Array.isArray(detail)) {
    return detail
      .map(item => {
        if (typeof item === 'string') {
          return item
        }
        const location = Array.isArray(item?.loc) ? item.loc.join('.') : ''
        const message = item?.msg || JSON.stringify(item)
        return location ? `${location}: ${message}` : message
      })
      .join('；')
  }
  if (typeof detail === 'object') {
    return detail.message || detail.msg || JSON.stringify(detail)
  }
  return String(detail)
}

export async function fetchJson(url, options = {}) {
  const response = await fetch(url, options)
  if (!response.ok) {
    const fallback = `HTTP ${response.status}`
    let message = fallback
    try {
      const body = await response.json()
      message = formatErrorDetail(body.detail || body, fallback)
    } catch {
      message = fallback
    }
    throw new Error(message)
  }
  return response.json()
}
