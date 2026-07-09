export function shortText(value, maxLength = 90) {
  const text = String(value || '').trim()
  if (text.length <= maxLength) {
    return text
  }
  return `${text.slice(0, maxLength)}...`
}
