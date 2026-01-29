<template>
  <div class="caps-config">
    <div class="config-header">
      <h3>Earn Caps</h3>
      <button @click="addCap" class="btn-secondary btn-sm">+ Add Cap</button>
    </div>
    
    <p class="help-text">
      Set limits on how many points customers can earn within a time period.
    </p>
    
    <div v-if="caps.length === 0" class="empty-state">
      <p>No earn caps defined. Points can be earned without limits.</p>
    </div>
    
    <div v-else class="caps-list">
      <div 
        v-for="(cap, index) in caps" 
        :key="index"
        class="cap-card"
      >
        <div class="cap-header">
          <span class="cap-number">Cap {{ index + 1 }}</span>
          <button @click="removeCap(index)" class="btn-danger btn-sm">Remove</button>
        </div>
        
        <div class="cap-fields">
          <div class="field-group">
            <label>Cap Amount (Points)</label>
            <input 
              type="number" 
              v-model.number="cap.max_points" 
              min="0"
              @input="updateCaps"
              placeholder="e.g., 10000"
            />
            <small>0 = Unlimited</small>
          </div>
          
          <div class="field-group">
            <label>Period</label>
            <select v-model="cap.period" @change="updateCaps">
              <option value="day">Per Day</option>
              <option value="week">Per Week</option>
              <option value="month">Per Month</option>
              <option value="year">Per Year</option>
              <option value="lifetime">Lifetime</option>
            </select>
          </div>
          
          <div class="field-group">
            <label>Cap Type</label>
            <select v-model="cap.cap_type" @change="updateCaps">
              <option value="total">Total Points</option>
              <option value="per_transaction">Per Transaction</option>
              <option value="per_rule">Per Earn Rule</option>
            </select>
          </div>
          
          <div class="field-group">
            <label>Applicable Rules (JSONLogic - Optional)</label>
            <textarea 
              v-model="cap.rule_filter" 
              placeholder='{"and": [{"==": {"var": "transaction_type"}, "purchase"}]}'
              rows="3"
              @input="updateCaps"
            ></textarea>
            <small class="help-text">Leave empty to apply to all earn rules</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface EarnCap {
  max_points: number
  period: 'day' | 'week' | 'month' | 'year' | 'lifetime'
  cap_type: 'total' | 'per_transaction' | 'per_rule'
  rule_filter?: string
}

const props = defineProps<{
  caps: EarnCap[]
}>()

const emit = defineEmits(['update:caps'])

const caps = ref<EarnCap[]>([...props.caps])

watch(() => props.caps, (newCaps) => {
  caps.value = [...newCaps]
}, { deep: true })

const updateCaps = () => {
  emit('update:caps', [...caps.value])
}

const addCap = () => {
  caps.value.push({
    max_points: 10000,
    period: 'month',
    cap_type: 'total',
    rule_filter: ''
  })
  updateCaps()
}

const removeCap = (index: number) => {
  caps.value.splice(index, 1)
  updateCaps()
}
</script>

<style scoped>
.caps-config {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.config-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.help-text {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 1.5rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #666;
  background: #f9fafb;
  border-radius: 6px;
}

.caps-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.cap-card {
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9fafb;
}

.cap-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.cap-number {
  font-weight: 600;
  color: #2563eb;
}

.cap-fields {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
}

.field-group input,
.field-group select,
.field-group textarea {
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.field-group textarea {
  resize: vertical;
  font-family: monospace;
}

.field-group small {
  font-size: 0.75rem;
  color: #999;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}
</style>

