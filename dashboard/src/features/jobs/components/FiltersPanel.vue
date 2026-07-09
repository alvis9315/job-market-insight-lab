<script setup>
import { computed } from 'vue'

const props = defineProps({
  stats: {
    type: Object,
    required: true
  }
})

const model = defineModel({
  type: Object,
  required: true
})

defineEmits(['apply', 'reset'])

const keywordOptions = computed(() => props.stats.keywords || [])
const companyOptions = computed(() => props.stats.companies || [])
const locationOptions = computed(() => props.stats.locations || [])
</script>

<template>
  <section class="panel filters-panel">
    <div class="section-title-row filters-title-row">
      <h2>職缺篩選</h2>
      <button type="button" class="secondary" @click="$emit('reset')">清除</button>
    </div>
    <div class="filters-grid">
      <label>
        全文搜尋
        <input v-model="model.q" type="text" placeholder="Vue、React、AI、遠端..." @input="$emit('apply')" />
      </label>
      <label>
        關鍵字批次
        <select v-model="model.keyword" @change="$emit('apply')">
          <option value="">全部批次</option>
          <option v-for="item in keywordOptions" :key="item.name" :value="item.name">
            {{ item.name }}（{{ item.count }}）
          </option>
        </select>
      </label>
      <label>
        公司
        <select v-model="model.company" @change="$emit('apply')">
          <option value="">全部公司</option>
          <option v-for="item in companyOptions" :key="item.name" :value="item.name">
            {{ item.name }}（{{ item.count }}）
          </option>
        </select>
      </label>
      <label>
        地點
        <select v-model="model.location" @change="$emit('apply')">
          <option value="">全部地點</option>
          <option v-for="item in locationOptions" :key="item.name" :value="item.name">
            {{ item.name }}（{{ item.count }}）
          </option>
        </select>
      </label>
    </div>
  </section>
</template>
