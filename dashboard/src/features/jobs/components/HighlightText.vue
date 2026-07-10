<script setup>
import { computed } from 'vue'

const props = defineProps({
  text: {
    type: [String, Number],
    default: ''
  },
  query: {
    type: String,
    default: ''
  }
})

const segments = computed(() => {
  const text = String(props.text ?? '')
  const query = String(props.query || '').trim()
  if (!query || !text) {
    return [{ match: false, value: text }]
  }

  const lowerText = text.toLowerCase()
  const lowerQuery = query.toLowerCase()
  const result = []
  let cursor = 0

  while (cursor <= text.length) {
    const index = lowerText.indexOf(lowerQuery, cursor)
    if (index === -1) {
      result.push({ match: false, value: text.slice(cursor) })
      break
    }
    if (index > cursor) {
      result.push({ match: false, value: text.slice(cursor, index) })
    }
    result.push({ match: true, value: text.slice(index, index + query.length) })
    cursor = index + query.length
  }

  return result.filter(segment => segment.value)
})
</script>

<template>
  <template v-for="(segment, index) in segments" :key="index">
    <mark v-if="segment.match" class="text-highlight">{{ segment.value }}</mark>
    <template v-else>{{ segment.value }}</template>
  </template>
</template>
