<template>
  <v-chart :option="chartOption" autoresize style="width: 100%; height: 300px" />
</template>

<script setup>
import { computed } from 'vue'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { PieChart as PieChartComponent } from 'echarts/charts'
import { TitleComponent, TooltipComponent, LegendComponent } from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import { useThemeStore } from '@/store/modules/theme'

use([PieChartComponent, TitleComponent, TooltipComponent, LegendComponent, CanvasRenderer])

const props = defineProps({
  title: { type: String, default: '' },
  data: { type: Array, default: () => [] },
})

const themeStore = useThemeStore()

const chartOption = computed(() => {
  const d = themeStore.isDark
  return {
    title: { text: props.title, left: 'center', textStyle: { color: d ? '#fff' : '#1f2937' } },
    tooltip: {
      trigger: 'item',
      backgroundColor: d ? 'rgba(20, 25, 40, 0.95)' : 'rgba(255,255,255,0.96)',
      borderColor: d ? 'rgba(255,255,255,0.2)' : '#e5e7eb',
      textStyle: { color: d ? '#fff' : '#374151' },
    },
    legend: { bottom: '0', textStyle: { color: d ? 'rgba(255,255,255,0.6)' : '#6b7280' } },
    series: [{
      type: 'pie',
      radius: '60%',
      data: props.data,
      label: { color: d ? '#fff' : '#374151' },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' },
      },
    }],
  }
})
</script>
