<template>
  <v-chart :option="chartOption" autoresize style="width: 100%; height: 300px" />
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { LineChart as LineChartComponent } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useThemeStore } from '@/store/modules/theme'

use([LineChartComponent, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  title: { type: String, default: '' },
  xData: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
})

const themeStore = useThemeStore()

const chartOption = computed(() => {
  const d = themeStore.isDark
  const axisColor = d ? 'rgba(255,255,255,0.5)' : '#9ca3af'
  const axisLineColor = d ? 'rgba(255,255,255,0.2)' : '#e5e7eb'
  const splitColor = d ? 'rgba(255,255,255,0.1)' : '#f3f4f6'
  return {
    title: { text: props.title, textStyle: { color: d ? '#fff' : '#1f2937' } },
    tooltip: {
      trigger: 'axis',
      backgroundColor: d ? 'rgba(20, 25, 40, 0.95)' : 'rgba(255,255,255,0.96)',
      borderColor: d ? 'rgba(255,255,255,0.2)' : '#e5e7eb',
      textStyle: { color: d ? '#fff' : '#374151' },
    },
    legend: { textStyle: { color: d ? 'rgba(255,255,255,0.6)' : '#6b7280' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: {
      type: 'category',
      data: props.xData,
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: axisLineColor } },
      splitLine: { lineStyle: { color: splitColor } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: axisLineColor } },
      splitLine: { lineStyle: { color: splitColor } },
    },
    series: props.series.map((s) => ({ ...s, type: 'line', smooth: true })),
  }
})
</script>
