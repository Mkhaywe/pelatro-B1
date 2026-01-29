<template>
  <div class="program-builder">
    <div class="page-header">
      <div class="header-left">
        <h1>Program Builder: {{ program.name || 'New Program' }}</h1>
        <p v-if="program.description" class="subtitle">{{ program.description }}</p>
      </div>
      <div class="header-actions">
        <button @click="simulateProgram" class="btn-secondary">Simulate</button>
        <button @click="saveProgram" class="btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Program' }}
        </button>
      </div>
    </div>

    <div class="builder-content">
      <!-- Program Info -->
      <div class="section">
        <h2>Program Information</h2>
        <div class="form-grid">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="program.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="program.description" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>Start Date</label>
            <input v-model="program.start_date" type="datetime-local" required />
          </div>
          <div class="form-group">
            <label>End Date</label>
            <input v-model="program.end_date" type="datetime-local" required />
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="program.is_active" />
              Is Active
            </label>
          </div>
        </div>
      </div>

      <!-- Tier Management -->
      <div class="section">
        <TierManager 
          :tiers="program.tiers || []"
          @update:tiers="program.tiers = $event"
        />
      </div>

      <!-- Earn Rules -->
      <div class="section">
        <h2>Earn Rules (JSONLogic)</h2>
        <p class="help-text">
          Define rules for how customers earn points. Use JSONLogic to create dynamic rules based on transaction data.
        </p>
        <VisualRuleBuilder 
          :model-value="typeof program.earn_rules === 'string' ? program.earn_rules : JSON.stringify(program.earn_rules || {})"
          @update:model-value="handleEarnRulesUpdate"
          :dwh-columns="dwhColumns"
        />
      </div>

      <!-- Burn Rules -->
      <div class="section">
        <h2>Burn Rules (JSONLogic)</h2>
        <p class="help-text">
          Define rules for how customers redeem/burn points. Use JSONLogic to create dynamic redemption rules.
        </p>
        <VisualRuleBuilder 
          :model-value="typeof program.burn_rules === 'string' ? program.burn_rules : JSON.stringify(program.burn_rules || {})"
          @update:model-value="handleBurnRulesUpdate"
          :dwh-columns="dwhColumns"
        />
      </div>

      <!-- Points Expiry Rules -->
      <div class="section">
        <PointsExpiryConfig 
          :rules="parsedExpiryRules"
          :available-tiers="program.tiers || []"
          @update:rules="parsedExpiryRules = $event"
        />
      </div>

      <!-- Earn Caps -->
      <div class="section">
        <EarnCapsConfig 
          :caps="parsedEarnCaps"
          @update:caps="parsedEarnCaps = $event"
        />
      </div>

      <!-- Simulation Panel -->
      <div v-if="showSimulation" class="section simulation-panel">
        <div class="simulation-header">
          <h2>Simulation Results</h2>
          <button @click="showSimulation = false" class="btn-secondary btn-sm">Close</button>
        </div>
        <div class="simulation-content">
          <pre>{{ JSON.stringify(simulationResults, null, 2) }}</pre>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { programsApi } from '@/api/services/programs'
import type { LoyaltyProgram } from '@/types/loyalty'
import VisualRuleBuilder from '@/components/VisualRuleBuilder.vue'
import TierManager from '@/components/TierManager.vue'
import PointsExpiryConfig from '@/components/PointsExpiryConfig.vue'
import EarnCapsConfig from '@/components/EarnCapsConfig.vue'

const route = useRoute()
const router = useRouter()
const program = ref<Partial<LoyaltyProgram>>({
  name: '',
  description: '',
  start_date: '',
  end_date: '',
  is_active: true,
  tiers: [],
  earn_rules: {},
  burn_rules: {},
  points_expiry_rules: {},
  earn_caps: {},
})

const saving = ref(false)
const showSimulation = ref(false)
const simulationResults = ref({})

// DWH columns for JSONLogic editor - loaded dynamically
const dwhColumns = ref<string[]>([])

const loadDWHColumns = async () => {
  try {
    const { mlApi } = await import('@/api/services/ml')
    const response = await mlApi.getDWHColumns()
    dwhColumns.value = response.data.map((col: any) => col.name)
  } catch (error) {
    console.error('Error loading DWH columns:', error)
    // Fallback to default columns
    dwhColumns.value = [
      'total_revenue',
      'transaction_count',
      'last_purchase_days_ago',
      'customer_tier',
      'city',
      'age',
      'points_balance',
      'lifetime_value'
    ]
  }
}

// Parsed rules for expiry and caps
const parsedExpiryRules = ref<any[]>([])
const parsedEarnCaps = ref<any[]>([])

// Watch for changes to update program object
watch(() => parsedExpiryRules.value, (newRules) => {
  program.value.points_expiry_rules = newRules
}, { deep: true })

watch(() => parsedEarnCaps.value, (newCaps) => {
  program.value.earn_caps = newCaps
}, { deep: true })

const loadProgram = async (id: string) => {
  try {
    const response = await programsApi.getById(id)
    program.value = response.data
    
    // Format dates for datetime-local inputs (remove milliseconds and timezone)
    if (program.value.start_date) {
      const startDate = new Date(program.value.start_date)
      const year = startDate.getFullYear()
      const month = String(startDate.getMonth() + 1).padStart(2, '0')
      const day = String(startDate.getDate()).padStart(2, '0')
      const hours = String(startDate.getHours()).padStart(2, '0')
      const minutes = String(startDate.getMinutes()).padStart(2, '0')
      program.value.start_date = `${year}-${month}-${day}T${hours}:${minutes}`
    }
    if (program.value.end_date) {
      const endDate = new Date(program.value.end_date)
      const year = endDate.getFullYear()
      const month = String(endDate.getMonth() + 1).padStart(2, '0')
      const day = String(endDate.getDate()).padStart(2, '0')
      const hours = String(endDate.getHours()).padStart(2, '0')
      const minutes = String(endDate.getMinutes()).padStart(2, '0')
      program.value.end_date = `${year}-${month}-${day}T${hours}:${minutes}`
    }
    
    // Django JSONField returns objects, but VisualRuleBuilder expects JSON strings
    // Convert objects to JSON strings for VisualRuleBuilder
    const convertRuleForDisplay = (rule: any): string => {
      if (!rule) return ''
      if (typeof rule === 'string') {
        // Already a string - validate it's valid JSON
        if (rule.trim() === '') return ''
        try {
          JSON.parse(rule) // Validate it's valid JSON
          return rule
        } catch {
          return ''
        }
      }
      if (typeof rule === 'object') {
        // Convert object to JSON string
        // Even empty objects {} should be converted to "{}" so VisualRuleBuilder can handle them
        try {
          return JSON.stringify(rule)
        } catch {
          return ''
        }
      }
      return ''
    }
    
    program.value.earn_rules = convertRuleForDisplay(program.value.earn_rules)
    program.value.burn_rules = convertRuleForDisplay(program.value.burn_rules)
    
    // Debug: Log what we loaded
    if (import.meta.env.DEV) {
      console.log('Loaded program rules:', {
        earn_rules_original: program.value.earn_rules,
        earn_rules_type: typeof program.value.earn_rules,
        burn_rules_original: program.value.burn_rules,
        burn_rules_type: typeof program.value.burn_rules
      })
    }
    
    // Parse expiry rules
    if (typeof program.value.points_expiry_rules === 'string') {
      parsedExpiryRules.value = JSON.parse(program.value.points_expiry_rules || '[]')
    } else if (Array.isArray(program.value.points_expiry_rules)) {
      parsedExpiryRules.value = program.value.points_expiry_rules
    } else {
      parsedExpiryRules.value = []
    }
    
    // Parse earn caps (check both earn_caps and earn_caps_config for backward compatibility)
    const earnCapsSource = program.value.earn_caps_config || program.value.earn_caps
    if (typeof earnCapsSource === 'string') {
      parsedEarnCaps.value = JSON.parse(earnCapsSource || '[]')
    } else if (Array.isArray(earnCapsSource)) {
      parsedEarnCaps.value = earnCapsSource
    } else {
      parsedEarnCaps.value = []
    }
    
    // Ensure tiers array exists
    if (!program.value.tiers) {
      program.value.tiers = []
    }
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading program:', error)
    }
  }
}

const saveProgram = async () => {
  saving.value = true
  try {
    // Format dates for datetime-local inputs (remove milliseconds and timezone)
    const formatDateForInput = (dateStr: string | null | undefined) => {
      if (!dateStr) return null
      const date = new Date(dateStr)
      const year = date.getFullYear()
      const month = String(date.getMonth() + 1).padStart(2, '0')
      const day = String(date.getDate()).padStart(2, '0')
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      return `${year}-${month}-${day}T${hours}:${minutes}`
    }
    
    // Convert rules from string to object if needed (VisualRuleBuilder emits JSON strings)
    // Django JSONField expects objects (even empty {} is valid)
    const parseRuleForSave = (rule: any) => {
      if (!rule || rule === '') {
        return {} // Empty string/null becomes empty object
      }
      if (typeof rule === 'string') {
        try {
          const parsed = JSON.parse(rule)
          // Always return the parsed object, even if empty
          // Django JSONField can store empty objects
          return parsed && typeof parsed === 'object' ? parsed : {}
        } catch (e) {
          console.warn('Failed to parse rule for save:', e, rule)
          return {}
        }
      }
      // Already an object - return as-is (even if empty {})
      if (typeof rule === 'object') {
        return rule
      }
      return {}
    }
    
    const earnRulesObj = parseRuleForSave(program.value.earn_rules)
    const burnRulesObj = parseRuleForSave(program.value.burn_rules)
    
    // Debug: Log what we're saving
    console.log('Saving program rules:', {
      earn_rules_input: program.value.earn_rules,
      earn_rules_input_type: typeof program.value.earn_rules,
      earn_rules_parsed: earnRulesObj,
      earn_rules_keys: Object.keys(earnRulesObj),
      earn_rules_stringified: JSON.stringify(earnRulesObj),
      burn_rules_input: program.value.burn_rules,
      burn_rules_input_type: typeof program.value.burn_rules,
      burn_rules_parsed: burnRulesObj,
      burn_rules_keys: Object.keys(burnRulesObj),
      burn_rules_stringified: JSON.stringify(burnRulesObj)
    })
    
    const programToSave = {
      ...program.value,
      start_date: formatDateForInput(program.value.start_date),
      end_date: formatDateForInput(program.value.end_date),
      // Django JSONField expects objects (even empty {} is valid)
      earn_rules: earnRulesObj,
      burn_rules: burnRulesObj,
      points_expiry_rules: parsedExpiryRules.value || [],
      earn_caps_config: parsedEarnCaps.value || [],
      tiers: program.value.tiers || [], // Include tiers in save
    }
    
    if (route.params.id === 'new') {
      const response = await programsApi.create(programToSave)
      console.log('Program created:', response.data)
      alert('Program created successfully!')
      router.push('/programs')
    } else {
      const response = await programsApi.update(route.params.id as string, programToSave)
      console.log('Program updated:', response.data)
      // Reload the program to see the saved rules
      await loadProgram(route.params.id as string)
      alert('Program updated successfully!')
    }
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error saving program:', error)
    }
    alert('Error saving program. Check your input.')
  } finally {
    saving.value = false
  }
}

const simulateProgram = async () => {
  try {
    const response = await programsApi.simulate(route.params.id as string, {
      customer_id: 'test-customer-123',
      transaction_amount: 100.0,
      transaction_context: {}
    })
    simulationResults.value = response.data
    showSimulation.value = true
  } catch (error: any) {
    if (import.meta.env.DEV) {
      console.error('Error simulating program:', error)
    }
    alert('Error simulating program: ' + (error.response?.data?.error || error.message))
  }
}

// Handle rule updates from VisualRuleBuilder
const handleEarnRulesUpdate = (value: string) => {
  try {
    program.value.earn_rules = JSON.parse(value || '{}')
  } catch {
    program.value.earn_rules = {}
  }
}

const handleBurnRulesUpdate = (value: string) => {
  try {
    program.value.burn_rules = JSON.parse(value || '{}')
  } catch {
    program.value.burn_rules = {}
  }
}

onMounted(() => {
  loadDWHColumns() // Load DWH columns dynamically
  if (route.params.id && route.params.id !== 'new') {
    loadProgram(route.params.id as string)
  } else {
    // Initialize with empty tiers array
    program.value.tiers = []
    parsedExpiryRules.value = []
    parsedEarnCaps.value = []
  }
})
</script>

<style scoped>
.program-builder {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 2px solid #e0e0e0;
}

.header-left h1 {
  font-size: 1.75rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.builder-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.help-text {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #333;
}

.form-group input,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.form-group textarea {
  resize: vertical;
}

.simulation-panel {
  background: #f9fafb;
  border: 2px solid #2563eb;
}

.simulation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.simulation-content {
  background: white;
  border-radius: 6px;
  padding: 1rem;
  max-height: 400px;
  overflow-y: auto;
}

.simulation-content pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}

.btn-secondary:hover {
  background: #e5e7eb;
}
</style>
