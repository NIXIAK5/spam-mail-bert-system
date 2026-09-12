<template>
  <v-chart :option="chartOption" autoresize :style="{ width: '100%', height: height }" />
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { RadarChart as RadarChartComponent } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useThemeStore } from '@/store/modules/theme'

use([RadarChartComponent, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  // [{ name: '模型A', values: [acc, precision, recall, f1] }, ...]
  series: { type: Array, default: () => [] },
  height: { type: String, default: '320px' },
})

const themeStore = useThemeStore()

const INDICATORS = [
  { name: '准确率', max: 100 },
  { name: '精确率', max: 100 },
  { name: '召回率', max: 100 },
  { name: 'F1 分数', max: 100 },
]

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']

const chartOption = computed(() => {
  const d = themeStore.isDark
  const textColor = d ? 'rgba(255,255,255,0.6)' : '#6b7280'
  const lineColor = d ? 'rgba(255,255,255,0.15)' : '#e5e7eb'

  return {
    tooltip: {
      trigger: 'item',
      backgroundColor: d ? 'rgba(20,25,40,0.95)' : 'rgba(255,255,255,0.96)',
      borderColor: d ? 'rgba(255,255,255,0.2)' : '#e5e7eb',
      textStyle: { color: d ? '#fff' : '#374151' },
      formatter(params) {
        const vals = params.value
        return [
          `<b>${params.name}</b>`,
          ...INDICATORS.map((ind, i) => `${ind.name}: <b>${Number(vals[i]).toFixed(2)}%</b>`),
        ].join('<br/>')
      },
    },
    legend: {
      bottom: 0,
      textStyle: { color: textColor },
      data: props.series.map(s => s.name),
    },
    radar: {
      indicator: INDICATORS,
      center: ['50%', '48%'],
      radius: '62%',
      axisName: { color: textColor, fontSize: 12 },
      splitLine: { lineStyle: { color: lineColor } },
      splitArea: { areaStyle: { color: d ? ['rgba(255,255,255,0.02)', 'rgba(255,255,255,0.05)'] : ['rgba(250,250,250,0.3)', 'rgba(200,200,200,0.1)'] } },
      axisLine: { lineStyle: { color: lineColor } },
    },
    series: [{
      type: 'radar',
      data: props.series.map((s, i) => ({
        name: s.name,
        value: s.values,
        lineStyle: { color: COLORS[i % COLORS.length], width: 2 },
        itemStyle: { color: COLORS[i % COLORS.length] },
        areaStyle: { color: COLORS[i % COLORS.length], opacity: 0.15 },
      })),
    }],
  }
})
</script>
