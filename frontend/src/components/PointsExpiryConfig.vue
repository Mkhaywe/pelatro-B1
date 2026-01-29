<template>
  <div class="expiry-config">
    <div class="config-header">
      <h3>Points Expiry Rules</h3>
      <button @click="addRule" class="btn-secondary btn-sm">+ Add Rule</button>
    </div>
    
    <p class="help-text">
      Configure when and how points expire. Rules are evaluated in order.
    </p>
    
    <div v-if="rules.length === 0" class="empty-state">
      <p>No expiry rules defined. Points will never expire.</p>
    </div>
    
    <div v-else class="rules-list">
      <div 
        v-for="(rule, index) in rules" 
        :key="index"
        class="rule-card"
      >
        <div class="rule-header">
          <span class="rule-number">Rule {{ index + 1 }}</span>
          <button @click="removeRule(index)" class="btn-danger btn-sm">Remove</button>
        </div>
        
        <div class="rule-fields">
          <div class="field-group">
            <label>Expiry Period (Days)</label>
            <input 
              type="number" 
              v-model.number="rule.expiry_days" 
              min="1"
              @input="updateRules"
              placeholder="e.g., 365"
            />
          </div>
          
          <div class="field-group">
            <label>Expiry Type</label>
            <select v-model="rule.expiry_type" @change="updateRules">
              <option value="fixed">Fixed (from earn date)</option>
              <option value="rolling">Rolling (from last activity)</option>
              <option value="tier_based">Tier Based</option>
            </select>
          </div>
          
          <div class="field-group" v-if="rule.expiry_type === 'tier_based'">
            <label>Applicable Tiers</label>
            <select v-model="rule.applicable_tiers" @change="updateRules" multiple>
              <option v-for="tier in availableTiers" :key="tier.id" :value="tier.id">
                {{ tier.name }}
              </option>
            </select>
          </div>
          
          <div class="field-group">
            <label>Eligibility Rule (JSONLogic - Optional)</label>
            <textarea 
              v-model="rule.eligibility_rule" 
              placeholder='{"and": [{">": {"var": "points_balance"}, 1000}]}'
              rows="3"
              @input="updateRules"
            ></textarea>
            <small class="help-text">Leave empty to apply to all points</small>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

interface ExpiryRule {
  expiry_days: number
  expiry_type: 'fixed' | 'rolling' | 'tier_based'
  applicable_tiers?: number[]
  eligibility_rule?: string
}

const props = defineProps<{
  rules: ExpiryRule[]
  availableTiers?: Array<{ id: number, name: string }>
}>()

const emit = defineEmits(['update:rules'])

const rules = ref<ExpiryRule[]>([...props.rules])

watch(() => props.rules, (newRules) => {
  rules.value = [...newRules]
}, { deep: true })

const updateRules = () => {
  emit('update:rules', [...rules.value])
}

const addRule = () => {
  rules.value.push({
    expiry_days: 365,
    expiry_type: 'fixed',
    eligibility_rule: ''
  })
  updateRules()
}

const removeRule = (index: number) => {
  rules.value.splice(index, 1)
  updateRules()
}
</script>

<style scoped>
.expiry-config {
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

.rules-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.rule-card {
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  background: #f9fafb;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.rule-number {
  font-weight: 600;
  color: #2563eb;
}

.rule-fields {
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

