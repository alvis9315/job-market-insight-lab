<script setup>
import { ChevronDown, ChevronUp, LoaderCircle } from '@lucide/vue'
import { ref } from 'vue'

defineProps({
  importing: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: null
  }
})

const model = defineModel({
  type: Object,
  required: true
})

defineEmits(['submit'])

const isOpen = ref(true)
</script>

<template>
  <section class="panel collapsible-panel manual-import-panel">
    <div class="section-title-row collapsible-title-row">
      <div>
        <h2>手動匯入</h2>
        <p>貼上 DevTools 複製的職缺列表或單一職缺詳細 HTML，也可貼純文字或 CSV。</p>
      </div>
      <div class="header-actions">
        <span v-if="result">解析 {{ result.parsed_count }} 筆，寫入 {{ result.saved_count }} 筆</span>
        <button
          type="button"
          class="icon-button"
          :aria-label="isOpen ? '收合手動匯入' : '展開手動匯入'"
          :title="isOpen ? '收合' : '展開'"
          @click="isOpen = !isOpen"
        >
          <ChevronUp v-if="isOpen" :size="20" />
          <ChevronDown v-else :size="20" />
        </button>
      </div>
    </div>

    <form v-if="isOpen" class="manual-import-form" @submit.prevent="$emit('submit')">
      <label>
        公司名稱
        <input v-model="model.companyName" type="text" placeholder="公司名稱" />
      </label>
      <label>
        格式
        <select v-model="model.inputFormat">
          <option value="auto">自動判斷</option>
          <option value="html">HTML</option>
          <option value="text">純文字</option>
          <option value="csv">CSV</option>
        </select>
      </label>
      <div v-if="model.inputFormat === 'html'" class="import-help">
        <strong>HTML 複製方式</strong>
        <span>在目標頁面按 F12 打開 DevTools，切到 Elements，對 body、職缺列表父層或單一職缺詳細區塊按右鍵，選 Copy，再選 Copy element，最後貼到下方輸入區。若貼單一職缺，建議連同頁面上方職缺標題一起複製。</span>
      </div>
      <label class="paste-field">
        貼上內容
        <textarea
          v-model="model.content"
          rows="10"
          placeholder="貼上職缺列表或單一職缺詳細 element outerHTML、頁面文字，或含 title/company_name/location 欄位的 CSV"
        ></textarea>
      </label>
      <button type="submit" :class="{ 'is-loading': importing }" :disabled="importing || !model.content.trim()">
        <span class="button-content">
          <LoaderCircle v-if="importing" class="spin-icon" :size="18" />
          {{ importing ? '匯入中...' : '解析並匯入' }}
        </span>
      </button>
    </form>

    <div v-if="isOpen && result?.items?.length" class="import-preview">
      <strong>匯入預覽：{{ result.keyword }}｜{{ result.company_name || '未取得公司' }}</strong>
      <div v-for="job in result.items.slice(0, 5)" :key="job.job_id" class="preview-row">
        <span>{{ job.title }}</span>
        <small>{{ [job.location, job.salary, job.experience].filter(Boolean).join('｜') }}</small>
      </div>
    </div>
  </section>
</template>
