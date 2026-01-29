<template>
  <div class="pie-chart-container">
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { PieChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  PieChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
])

const defaultColors = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d']

const props = withDefaults(defineProps<{
  data: any[]
  dataKey: string
  nameKey?: string
  outerRadius?: number
  innerRadius?: number
  colors?: string[]
  labelFormatter?: (entry: any) => string
  tooltipFormatter?: (value: any, name: string) => [string, string]
}>(), {
  outerRadius: 75,
  innerRadius: 45,
  nameKey: 'name'
})

const chartColors = computed(() => props.colors || defaultColors)

const chartOption = computed(() => {
  const chartData = props.data.map((item, index) => ({
    value: item[props.dataKey] || 0,
    name: item[props.nameKey || 'name'] || `Item ${index + 1}`,
    itemStyle: {
      color: chartColors.value[index % chartColors.value.length],
    },
  }))

  return {
    tooltip: {
      trigger: 'item',
      formatter: props.tooltipFormatter
        ? (params: any) => {
            const result = props.tooltipFormatter!(params.value, params.name)
            return `${result[0]}: ${result[1]}`
          }
        : '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'horizontal',
      bottom: 10,
      left: 'center',
    },
    series: [
      {
        name: 'Data',
        type: 'pie',
        radius: [`${props.innerRadius}%`, `${props.outerRadius}%`],
        center: ['50%', '45%'],
        avoidLabelOverlap: true,
        itemStyle: {
          borderRadius: 8,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          show: false,
        },
        emphasis: {
          label: {
            show: true,
            fontSize: 14,
            fontWeight: 'bold',
          },
        },
        data: chartData,
      },
    ],
  }
})
</script>

<style scoped>
.pie-chart-container {
  width: 100%;
  height: 320px;
  min-height: 280px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
