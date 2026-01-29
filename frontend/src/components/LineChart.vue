<template>
  <div class="line-chart-container">
    <v-chart class="chart" :option="chartOption" autoresize />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart } from 'echarts/charts'
import {
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  LineChart,
  TitleComponent,
  TooltipComponent,
  LegendComponent,
  GridComponent,
])

const props = defineProps<{
  data: any[]
  xKey: string
  lines: Array<{
    dataKey: string
    name: string
    stroke?: string
    type?: string
  }>
  xFormatter?: (value: any) => string
  tooltipFormatter?: (value: any, name: string) => [string, string]
}>()

const chartOption = computed(() => {
  const xAxisData = props.data.map(item => {
    const value = item[props.xKey]
    return props.xFormatter ? props.xFormatter(value) : value
  })

  const series = props.lines.map(line => ({
    name: line.name,
    type: 'line',
    data: props.data.map(item => item[line.dataKey] || 0),
    smooth: line.type === 'monotone',
    lineStyle: {
      color: line.stroke || '#8884d8',
      width: 2,
    },
    itemStyle: {
      color: line.stroke || '#8884d8',
    },
  }))

  return {
    tooltip: {
      trigger: 'axis',
      formatter: props.tooltipFormatter
        ? (params: any) => {
            const result = props.tooltipFormatter!(params[0].value, params[0].seriesName)
            return `${result[0]}: ${result[1]}`
          }
        : undefined,
    },
    legend: {
      data: props.lines.map(l => l.name),
      bottom: 0,
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: xAxisData,
      axisLabel: {
        rotate: -45,
        interval: 0,
      },
    },
    yAxis: {
      type: 'value',
    },
    series,
  }
})
</script>

<style scoped>
.line-chart-container {
  width: 100%;
  height: 300px;
}

.chart {
  width: 100%;
  height: 100%;
}
</style>
