<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart, PieChart } from 'echarts/charts'
import { GridComponent, LegendComponent, TooltipComponent } from 'echarts/components'

const props = defineProps({
  stats: {
    type: Object,
    required: true
  }
})

use([CanvasRenderer, BarChart, PieChart, GridComponent, LegendComponent, TooltipComponent])

const keywordChartOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 40, right: 20, bottom: 70, top: 20 },
  xAxis: {
    type: 'category',
    data: props.stats.keywords.map(item => item.name),
    axisLabel: { rotate: 35 }
  },
  yAxis: { type: 'value' },
  series: [{ type: 'bar', data: props.stats.keywords.map(item => item.count) }]
}))

const companyChartOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { bottom: 0 },
  series: [
    {
      type: 'pie',
      radius: ['45%', '70%'],
      avoidLabelOverlap: true,
      data: props.stats.companies.slice(0, 8).map(item => ({ name: item.name, value: item.count }))
    }
  ]
}))
</script>

<template>
  <section class="charts-grid">
    <article class="panel chart-panel">
      <h2>關鍵字資料量</h2>
      <VChart class="chart" :option="keywordChartOption" autoresize />
    </article>
    <article class="panel chart-panel">
      <h2>公司分布 Top 8</h2>
      <VChart class="chart" :option="companyChartOption" autoresize />
    </article>
  </section>
</template>
