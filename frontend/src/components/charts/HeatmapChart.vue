<template>
  <v-chart :option="chartOption" autoresize :style="{ width: '100%', height: height }" />
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { HeatmapChart as HeatmapChartComponent } from 'echarts/charts'
import { TitleComponent, TooltipComponent, GridComponent, VisualMapComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useThemeStore } from '@/store/modules/theme'

use([HeatmapChartComponent, TitleComponent, TooltipComponent, GridComponent, VisualMapComponent, CanvasRenderer])

const props = defineProps({
  // 归一化后的矩阵数据 [[TN%, FP%], [FN%, TP%]]
  data: { type: Array, default: () => [[0, 0], [0, 0]] },
  // 原始计数矩阵
  rawData: { type: Array, default: () => [[0, 0], [0, 0]] },
  height: { type: String, default: '320px' },
})

const themeStore = useThemeStore()

const chartOption = computed(() => {
  const d = themeStore.isDark
  const axisColor = d ? 'rgba(255,255,255,0.7)' : '#374151'

  // ECharts heatmap 需要 [x, y, value] 格式，x=预测，y=真实（从下到上）
  const heatData = []
  const labels = ['Ham (正常)', 'Spam (垃圾)']
  for (let row = 0; row < 2; row++) {
    for (let col = 0; col < 2; col++) {
      heatData.push([col, 1 - row, props.data[row][col]])
    }
  }

  return {
    tooltip: {
      formatter(params) {
        const [predIdx, trueIdxFlipped] = params.data
        const trueIdx = 1 - trueIdxFlipped
        const raw = props.rawData[trueIdx]?.[predIdx] ?? 0
        const pct = params.data[2]
        return [
          `真实: <b>${labels[trueIdx]}</b>`,
          `预测: <b>${labels[predIdx]}</b>`,
          `占比: <b>${pct.toFixed(1)}%</b>`,
          `数量: <b>${raw}</b>`,
        ].join('<br/>')
      },
      backgroundColor: d ? 'rgba(20,25,40,0.95)' : 'rgba(255,255,255,0.96)',
      borderColor: d ? 'rgba(255,255,255,0.2)' : '#e5e7eb',
      textStyle: { color: d ? '#fff' : '#374151' },
    },
    grid: { left: '15%', right: '12%', bottom: '18%', top: '8%' },
    xAxis: {
      type: 'category',
      data: labels,
      name: '预测标签',
      nameLocation: 'middle',
      nameGap: 32,
      nameTextStyle: { color: axisColor, fontSize: 12 },
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: d ? 'rgba(255,255,255,0.2)' : '#e5e7eb' } },
      splitLine: { show: false },
    },
    yAxis: {
      type: 'category',
      data: [...labels].reverse(),
      name: '真实标签',
      nameLocation: 'middle',
      nameGap: 68,
      nameTextStyle: { color: axisColor, fontSize: 12 },
      axisLabel: { color: axisColor },
      axisLine: { lineStyle: { color: d ? 'rgba(255,255,255,0.2)' : '#e5e7eb' } },
      splitLine: { show: false },
    },
    visualMap: {
      min: 0,
      max: 100,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: '2%',
      inRange: { color: d ? ['#1e3a5f', '#1d4ed8', '#3b82f6', '#93c5fd'] : ['#eff6ff', '#bfdbfe', '#3b82f6', '#1d4ed8'] },
      textStyle: { color: axisColor },
      text: ['100%', '0%'],
    },
    series: [{
      type: 'heatmap',
      data: heatData,
      label: {
        show: true,
        formatter(params) {
          const [predIdx, trueIdxFlipped] = params.data
          const trueIdx = 1 - trueIdxFlipped
          const raw = props.rawData[trueIdx]?.[predIdx] ?? 0
          return `${params.data[2].toFixed(1)}%\n(${raw})`
        },
        color: '#fff',
        fontSize: 13,
        fontWeight: 600,
      },
      emphasis: { itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,0,0,0.5)' } },
    }],
  }
})
</script>
