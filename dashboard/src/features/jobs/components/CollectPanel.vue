<script setup>
import { ChevronDown, ChevronUp } from '@lucide/vue'
import { ref } from 'vue'

defineProps({
  collecting: {
    type: Boolean,
    default: false
  }
})

const model = defineModel({
  type: Object,
  required: true
})

defineEmits(['submit'])

const isOpen = ref(false)
</script>

<template>
  <section class="panel collapsible-panel collect-panel">
    <div class="section-title-row collapsible-title-row">
      <div class="collect-title">
        <h2>診斷收集</h2>
        <div v-if="isOpen" class="collect-options" aria-label="診斷收集選項">
          <label class="checkbox-label compact-checkbox">
            <input v-model="model.headless" type="checkbox" />
            背景執行
          </label>
          <label class="checkbox-label compact-checkbox">
            <input v-model="model.debug" type="checkbox" />
            輸出 debug
          </label>
        </div>
        <p>保留 Playwright 小量診斷流程；若目標網站回 Cloudflare challenge，系統會顯示診斷結果。</p>
      </div>
      <button
        type="button"
        class="icon-button"
        :aria-label="isOpen ? '收合診斷收集' : '展開診斷收集'"
        :title="isOpen ? '收合' : '展開'"
        @click="isOpen = !isOpen"
      >
        <ChevronUp v-if="isOpen" :size="20" />
        <ChevronDown v-else :size="20" />
      </button>
    </div>
    <form v-if="isOpen" class="collect-form" @submit.prevent="$emit('submit')">
      <label>
        關鍵字
        <input v-model="model.keyword" type="text" placeholder="前端工程師 Vue" />
      </label>
      <label class="url-field">
        職缺列表網址
        <input
          v-model="model.startUrl"
          type="url"
          placeholder="貼上你要診斷的公開職缺列表網址"
        />
      </label>
      <label>
        頁數
        <input v-model="model.pages" type="number" min="1" max="10" />
      </label>
      <button type="submit" :disabled="collecting">
        {{ collecting ? '收集中...' : '開始收集' }}
      </button>
    </form>
  </section>
</template>
