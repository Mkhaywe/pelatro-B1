<template>
  <div class="churn-gauge">
    <div class="gauge-container">
      <div class="gauge-label">Churn Risk</div>
      <div class="gauge-value" :class="riskClass">
        {{ Math.round(probability * 100) }}%
      </div>
      <div class="gauge-bar">
        <div 
          class="gauge-fill" 
          :class="riskClass"
          :style="{ width: `${probability * 100}%` }"
        ></div>
      </div>
      <div class="gauge-status" :class="riskClass">
        {{ riskLabel }}
      </div>
    </div>
    <div v-if="details" class="gauge-details">
      <div class="detail-item">
        <span class="detail-label">Confidence:</span>
        <span class="detail-value">{{ Math.round((details.confidence || 0) * 100) }}%</span>
      </div>
      <div class="detail-item" v-if="details.reasons">
        <span class="detail-label">Key Factors:</span>
        <ul class="factors-list">
          <li v-for="(reason, idx) in details.reasons.slice(0, 3)" :key="idx">
            {{ reason }}
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = defineProps<{
  probability: number // 0-1
  details?: {
    confidence?: number
    reasons?: string[]
  }
}>()

const riskClass = computed(() => {
  if (props.probability < 0.3) return 'low'
  if (props.probability < 0.6) return 'medium'
  return 'high'
})

const riskLabel = computed(() => {
  if (props.probability < 0.3) return 'Low Risk'
  if (props.probability < 0.6) return 'Medium Risk'
  return 'High Risk'
})
</script>

<style scoped>
.churn-gauge {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.gauge-container {
  text-align: center;
}

.gauge-label {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.gauge-value {
  font-size: 2.5rem;
  font-weight: 700;
  margin-bottom: 1rem;
}

.gauge-value.low {
  color: #00C49F;
}

.gauge-value.medium {
  color: #FFBB28;
}

.gauge-value.high {
  color: #FF8042;
}

.gauge-bar {
  width: 100%;
  height: 12px;
  background: #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.gauge-fill {
  height: 100%;
  transition: width 0.5s ease;
  border-radius: 6px;
}

.gauge-fill.low {
  background: linear-gradient(90deg, #00C49F, #82ca9d);
}

.gauge-fill.medium {
  background: linear-gradient(90deg, #FFBB28, #ffa726);
}

.gauge-fill.high {
  background: linear-gradient(90deg, #FF8042, #ff5722);
}

.gauge-status {
  font-size: 0.875rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.gauge-status.low {
  color: #00C49F;
}

.gauge-status.medium {
  color: #FFBB28;
}

.gauge-status.high {
  color: #FF8042;
}

.gauge-details {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.detail-item {
  margin-bottom: 1rem;
}

.detail-item:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-size: 0.875rem;
  color: #666;
  font-weight: 500;
  display: block;
  margin-bottom: 0.25rem;
}

.detail-value {
  font-size: 1rem;
  color: #333;
  font-weight: 600;
}

.factors-list {
  list-style: none;
  padding: 0;
  margin: 0.5rem 0 0 0;
}

.factors-list li {
  font-size: 0.875rem;
  color: #666;
  padding: 0.25rem 0;
  padding-left: 1rem;
  position: relative;
}

.factors-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #2563eb;
  font-weight: bold;
}
</style>

