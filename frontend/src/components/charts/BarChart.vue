<template>
  <v-chart :option="chartOption" autoresize :style="{ width: '100%', height: height }" />
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { BarChart as BarChartComponent } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useThemeStore } from '@/store/modules/theme'

use([BarChartComponent, TitleComponent, TooltipComponent, GridComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  title: { type: String, default: '' },
  xData: { type: Array, default: () => [] },
  series: { type: Array, default: () => [] },
  height: { type: String, default: '300px' },
  horizontal: { type: Boolean, default: false },
})

const themeStore = useThemeStore()

const chartOption = computed(() => {
  const d = themeStore.isDark
  const axisColor = d ? 'rgba(255,255,255,0.5)' : '#9ca3af'
  const axisLineColor = d ? 'rgba(255,255,255,0.2)' : '#e5e7eb'
  const splitColor = d ? 'rgba(255,255,255,0.1)' : '#f3f4f6'

  const baseAxis = { type: 'category', data: props.xData, axisLabel: { interval: 0 } }
  const valueAxis = { type: 'value' }

  const axisStyle = (axis) => ({
    axisLabel: { ...axis.axisLabel, color: axisColor },
    axisLine: { lineStyle: { color: axisLineColor } },
    splitLine: { lineStyle: { color: splitColor } },
  })
  return {
    title: { text: props.title, left: 'center', textStyle: { fontSize: 14, fontWeight: 600, color: d ? '#fff' : '#1f2937' } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: d ? 'rgba(20, 25, 40, 0.95)' : 'rgba(255,255,255,0.96)',
      borderColor: d ? 'rgba(255,255,255,0.2)' : '#e5e7eb',
      textStyle: { color: d ? '#fff' : '#374151' },
    },
    legend: { bottom: 0, textStyle: { color: d ? 'rgba(255,255,255,0.6)' : '#6b7280' } },
    grid: { left: '3%', right: '4%', bottom: '12%', top: props.title ? '15%' : '8%', containLabel: true },
    xAxis: { ...(props.horizontal ? valueAxis : baseAxis), ...axisStyle(props.horizontal ? valueAxis : baseAxis) },
    yAxis: { ...(props.horizontal ? baseAxis : valueAxis), ...axisStyle(props.horizontal ? baseAxis : valueAxis) },
    series: props.series.map((s) => ({
      ...s,
      type: 'bar',
      barMaxWidth: 40,
      itemStyle: { borderRadius: [4, 4, 0, 0], ...s.itemStyle },
    })),
  }
})
</script>
