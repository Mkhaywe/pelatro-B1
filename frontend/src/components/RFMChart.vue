<template>
  <div class="rfm-chart">
    <div class="chart-header">
      <h3>RFM Analysis</h3>
      <p class="subtitle">Recency, Frequency, Monetary Value</p>
    </div>
    
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Calculating RFM scores...</p>
    </div>
    
    <div v-else-if="!rfmData" class="empty-state">
      <p>No RFM data available</p>
    </div>
    
    <div v-else class="rfm-content">
      <!-- RFM Scores -->
      <div class="rfm-scores">
        <div class="score-item">
          <div class="score-label">Recency</div>
          <div class="score-value" :class="getScoreClass(rfmData.recency_score)">
            {{ rfmData.recency_score }}
          </div>
          <div class="score-detail">{{ rfmData.recency_days }} days ago</div>
        </div>
        <div class="score-item">
          <div class="score-label">Frequency</div>
          <div class="score-value" :class="getScoreClass(rfmData.frequency_score)">
            {{ rfmData.frequency_score }}
          </div>
          <div class="score-detail">{{ rfmData.frequency_count }} transactions</div>
        </div>
        <div class="score-item">
          <div class="score-label">Monetary</div>
          <div class="score-value" :class="getScoreClass(rfmData.monetary_score)">
            {{ rfmData.monetary_score }}
          </div>
          <div class="score-detail">${{ formatNumber(rfmData.monetary_value) }}</div>
        </div>
      </div>
      
      <!-- RFM Segment -->
      <div class="rfm-segment">
        <div class="segment-label">Customer Segment</div>
        <div class="segment-value" :class="getSegmentClass(rfmData.segment)">
          {{ rfmData.segment || 'Unknown' }}
        </div>
        <div class="segment-description">
          {{ getSegmentDescription(rfmData.segment) }}
        </div>
      </div>
      
      <!-- Visual Chart -->
      <div class="rfm-visual">
        <v-chart class="chart" :option="barChartOption" autoresize />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import {
  TooltipComponent,
  GridComponent,
} from 'echarts/components'
import VChart from 'vue-echarts'

use([
  CanvasRenderer,
  BarChart,
  TooltipComponent,
  GridComponent,
])

interface RFMData {
  recency_score: number
  recency_days: number
  frequency_score: number
  frequency_count: number
  monetary_score: number
  monetary_value: number
  segment?: string
}

const props = defineProps<{
  rfmData: RFMData | null
  loading?: boolean
}>()

const chartData = computed(() => {
  if (!props.rfmData) return []
  return [
    { name: 'Recency', score: props.rfmData.recency_score },
    { name: 'Frequency', score: props.rfmData.frequency_score },
    { name: 'Monetary', score: props.rfmData.monetary_score },
  ]
})

const barChartOption = computed(() => {
  if (!props.rfmData) return {}
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true,
    },
    xAxis: {
      type: 'category',
      data: chartData.value.map(item => item.name.charAt(0)),
      axisLabel: {
        formatter: (value: string, index: number) => chartData.value[index]?.name || value,
      },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 5,
    },
    series: [
      {
        name: 'RFM Score',
        type: 'bar',
        data: chartData.value.map((item, index) => ({
          value: item.score,
          itemStyle: {
            color: getBarColor(item.score),
          },
        })),
        barWidth: '60%',
      },
    ],
  }
})

const getScoreClass = (score: number) => {
  if (score >= 4) return 'high'
  if (score >= 2) return 'medium'
  return 'low'
}

const getBarColor = (score: number) => {
  if (score >= 4) return '#00C49F'
  if (score >= 2) return '#FFBB28'
  return '#FF8042'
}

const getSegmentClass = (segment?: string) => {
  if (!segment) return ''
  const segmentLower = segment.toLowerCase()
  if (segmentLower.includes('champion') || segmentLower.includes('loyal')) return 'champion'
  if (segmentLower.includes('at risk') || segmentLower.includes('lost')) return 'at-risk'
  if (segmentLower.includes('potential') || segmentLower.includes('new')) return 'potential'
  return 'regular'
}

const getSegmentDescription = (segment?: string) => {
  if (!segment) return 'No segment assigned'
  const descriptions: Record<string, string> = {
    'Champions': 'High value, frequent customers. Reward them.',
    'Loyal Customers': 'Regular customers who are loyal to your brand.',
    'Potential Loyalists': 'Recent customers with high potential.',
    'New Customers': 'Newly acquired customers. Nurture them.',
    'Promising': 'Recent customers with good frequency.',
    'Need Attention': 'Customers who need re-engagement.',
    'About to Sleep': 'Customers at risk of churning.',
    'At Risk': 'Customers who haven\'t purchased recently.',
    'Cannot Lose Them': 'High value customers at risk.',
    'Hibernating': 'Inactive customers who may be lost.',
    'Lost': 'Customers who have churned.',
  }
  
  for (const [key, desc] of Object.entries(descriptions)) {
    if (segment.toLowerCase().includes(key.toLowerCase())) {
      return desc
    }
  }
  
  return 'Customer segment analysis'
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('en-US', {
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(num)
}
</script>

<style scoped>
.rfm-chart {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.chart-header {
  margin-bottom: 1.5rem;
}

.chart-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 0.25rem 0;
}

.subtitle {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.rfm-scores {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.score-item {
  text-align: center;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
}

.score-label {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.score-value {
  font-size: 2rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.score-value.high {
  color: #00C49F;
}

.score-value.medium {
  color: #FFBB28;
}

.score-value.low {
  color: #FF8042;
}

.score-detail {
  font-size: 0.75rem;
  color: #999;
}

.rfm-segment {
  text-align: center;
  padding: 1.5rem;
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 100%);
  border-radius: 8px;
  margin-bottom: 1.5rem;
  border: 2px solid #e0f2fe;
}

.segment-label {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.segment-value {
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.5rem;
}

.segment-value.champion {
  color: #00C49F;
}

.segment-value.at-risk {
  color: #FF8042;
}

.segment-value.potential {
  color: #2563eb;
}

.segment-value.regular {
  color: #666;
}

.segment-description {
  font-size: 0.875rem;
  color: #666;
  font-style: italic;
}

.rfm-visual {
  margin-top: 1.5rem;
  height: 200px;
}

.chart {
  width: 100%;
  height: 100%;
}

/* Responsive tweaks to avoid overlap in narrow cards (e.g. when DevTools is open) */
@media (max-width: 1200px) {
  .rfm-scores {
    grid-template-columns: 1fr;
  }

  .score-value {
    font-size: 1.6rem;
  }
}
</style>

