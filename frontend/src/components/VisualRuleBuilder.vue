<template>
  <div class="visual-rule-builder">
    <div class="builder-header">
      <h3>Rule Builder</h3>
      <div class="header-actions">
        <button @click="addCondition" class="btn-secondary btn-sm">+ Add Condition</button>
        <button @click="clearAll" class="btn-secondary btn-sm">Clear All</button>
        <button @click="testRule" class="btn-primary btn-sm">Test Rule</button>
      </div>
    </div>

    <div v-if="conditions.length === 0" class="empty-state">
      <p>No conditions defined. Add your first condition to build a rule.</p>
      <p class="help-text">Rules are evaluated with {{ logicOperator }} logic - all conditions must match.</p>
    </div>

    <div v-else class="rules-container">
      <div class="logic-selector">
        <label>Combine conditions with:</label>
        <select v-model="logicOperator" @change="updateRule">
          <option value="and">AND (all must match)</option>
          <option value="or">OR (any can match)</option>
        </select>
      </div>

      <div class="conditions-list">
        <div 
          v-for="(condition, index) in conditions" 
          :key="index"
          class="condition-card"
        >
          <div class="condition-header">
            <span class="condition-number">Condition {{ index + 1 }}</span>
            <button @click="removeCondition(index)" class="btn-danger btn-sm">Remove</button>
          </div>

          <div class="condition-body">
            <div class="field-group">
              <label>Field</label>
              <select 
                v-model="condition.field" 
                @change="updateRule"
                @focus="emit('focus')"
              >
                <option value="">-- Select Field --</option>
                <optgroup v-for="category in fieldCategories" :key="category.name" :label="category.name">
                  <option 
                    v-for="field in category.fields" 
                    :key="field.value" 
                    :value="field.value"
                  >
                    {{ field.label }}
                  </option>
                </optgroup>
              </select>
            </div>

            <div class="field-group">
              <label>Operator</label>
              <select v-model="condition.operator" @change="updateRule">
                <option value="equals">Equals (=)</option>
                <option value="not_equals">Not Equals (≠)</option>
                <option value="greater_than">Greater Than (>)</option>
                <option value="less_than">Less Than (<)</option>
                <option value="greater_equal">Greater or Equal (≥)</option>
                <option value="less_equal">Less or Equal (≤)</option>
                <option value="contains">Contains</option>
                <option value="not_contains">Does Not Contain</option>
                <option value="starts_with">Starts With</option>
                <option value="ends_with">Ends With</option>
                <option value="in">In List</option>
                <option value="not_in">Not In List</option>
              </select>
            </div>

            <div class="field-group">
              <label>Value</label>
              <input 
                v-if="!isListOperator(condition.operator)"
                v-model="condition.value" 
                :type="getInputType(condition.field)"
                :placeholder="getPlaceholder(condition.field)"
                @input="updateRule"
              />
              <textarea 
                v-else
                v-model="condition.value" 
                placeholder="Enter values separated by commas (e.g., Gold, Silver, Bronze)"
                rows="2"
                @input="updateRule"
              />
              <small v-if="isListOperator(condition.operator)" class="help-text">
                Separate multiple values with commas
              </small>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="testResult !== null" class="test-result">
      <h4>Test Result</h4>
      <div :class="['result', testResult ? 'pass' : 'fail']">
        <span v-if="testResult">✓ Rule matches test data</span>
        <span v-else>✗ Rule does not match test data</span>
      </div>
    </div>

    <div class="json-preview" v-if="showJsonPreview">
      <h4>JSON Preview</h4>
      <pre>{{ jsonOutput }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'

interface Condition {
  field: string
  operator: string
  value: string | number
}

const props = defineProps<{
  modelValue?: string | object
  dwhColumns?: string[]
  testData?: Record<string, any>
  showJsonPreview?: boolean
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'change': [value: object]
  'test': [result: boolean]
  'focus': []
}>()

// Expose method to insert field from parent
const insertField = (fieldName: string) => {
  // If no conditions exist, add one
  if (conditions.value.length === 0) {
    addCondition()
  }
  
  // Find first condition without a field, or use the first one
  const targetCondition = conditions.value.find(c => !c.field) || conditions.value[0]
  if (targetCondition) {
    targetCondition.field = fieldName
    updateRule()
  }
}

defineExpose({
  insertField
})

const conditions = ref<Condition[]>([])
const logicOperator = ref<'and' | 'or'>('and')
const testResult = ref<boolean | null>(null)
const isInternalUpdate = ref(false) // Flag to prevent circular updates

// Field categories for better organization
const fieldCategories = computed(() => {
  const categories = new Map<string, Array<{value: string; label: string; type: string}>>()
  
  // Financial Fields
  categories.set('Financial', [
    { value: 'total_revenue', label: 'Total Revenue', type: 'number' },
    { value: 'lifetime_value', label: 'Lifetime Value', type: 'number' },
    { value: 'avg_transaction_value', label: 'Avg Transaction Value', type: 'number' },
    { value: 'points_balance', label: 'Points Balance', type: 'number' },
  ])
  
  // Activity Fields
  categories.set('Activity', [
    { value: 'transaction_count', label: 'Transaction Count', type: 'number' },
    { value: 'last_purchase_days_ago', label: 'Days Since Last Purchase', type: 'number' },
    { value: 'last_login_days_ago', label: 'Days Since Last Login', type: 'number' },
  ])
  
  // Customer Profile
  categories.set('Profile', [
    { value: 'customer_tier', label: 'Customer Tier', type: 'string' },
    { value: 'segment', label: 'Segment', type: 'string' },
    { value: 'city', label: 'City', type: 'string' },
    { value: 'region', label: 'Region', type: 'string' },
    { value: 'country', label: 'Country', type: 'string' },
    { value: 'age', label: 'Age', type: 'number' },
    { value: 'gender', label: 'Gender', type: 'string' },
  ])
  
  // Risk & Engagement
  categories.set('Risk & Engagement', [
    { value: 'churn_score', label: 'Churn Score', type: 'number' },
    { value: 'campaign_engagement_rate', label: 'Campaign Engagement Rate', type: 'number' },
    { value: 'email_verified', label: 'Email Verified', type: 'boolean' },
    { value: 'phone_verified', label: 'Phone Verified', type: 'boolean' },
  ])
  
  // Add DWH columns if provided
  if (props.dwhColumns && props.dwhColumns.length > 0) {
    const dwhFields = props.dwhColumns.map(col => ({
      value: col,
      label: col.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
      type: 'string'
    }))
    if (dwhFields.length > 0) {
      categories.set('DWH Columns', dwhFields)
    }
  }
  
  return Array.from(categories.entries()).map(([name, fields]) => ({ name, fields }))
})

// Initialize from modelValue
const initializeFromValue = () => {
  const source = props.modelValue
  
  // Handle empty/null/empty string
  // Note: "{}" (empty JSON object) is valid and should be parsed
  if (!source || (typeof source === 'string' && source.trim() === '')) {
    // Only reset if we don't have conditions (user might be editing)
    if (conditions.value.length === 0) {
      conditions.value = []
      logicOperator.value = 'and'
    }
    return
  }
  
  // Don't return early for empty objects - they might be valid JSONLogic rules
  // We'll check after parsing
  
  try {
    const parsed = typeof source === 'string' ? JSON.parse(source) : source
    
    // Try to parse JSONLogic format
    if (parsed && (parsed.and || parsed.or)) {
      const op = parsed.and ? 'and' : 'or'
      const rules = parsed[op] || []
      logicOperator.value = op
      
      const newConditions = rules.map((rule: any) => {
        // Parse JSONLogic operators - handle {">": [{"var": "field"}, value]} format
        if (rule && typeof rule === 'object') {
          // Map of JSONLogic operators to our operator names
          const operatorMap: Record<string, string> = {
            '>': 'greater_than',
            '<': 'less_than',
            '>=': 'greater_equal',
            '<=': 'less_equal',
            '==': 'equals',
            '!=': 'not_equals'
          }
          
          // Check for operator keys
          for (const [jsonOp, ourOp] of Object.entries(operatorMap)) {
            if (rule[jsonOp]) {
              const args = rule[jsonOp]
              if (Array.isArray(args) && args.length === 2) {
                const fieldVar = args[0]
                const value = args[1]
                const field = fieldVar?.var || (typeof fieldVar === 'string' ? fieldVar : '')
                
                if (field) {
                  return {
                    field: field,
                    operator: ourOp,
                    value: value
                  }
                }
              }
              break // Found operator, no need to check others
            }
          }
          
          // Handle "in" operator separately (value is an array)
          if (rule['in']) {
            const args = rule['in']
            if (Array.isArray(args) && args.length === 2) {
              const fieldVar = args[0]
              const values = args[1]
              const field = fieldVar?.var || (typeof fieldVar === 'string' ? fieldVar : '')
              if (field && Array.isArray(values)) {
                return {
                  field: field,
                  operator: 'in',
                  value: values.join(', ')
                }
              }
            }
          }
        }
        return null
      }).filter((c: Condition | null): c is Condition => c !== null && c.field !== '' && c.value !== '')
      
      // Update conditions if we got valid ones
      if (newConditions.length > 0) {
        conditions.value = newConditions
      } else if (conditions.value.length === 0) {
        // No valid conditions found, reset if we don't have any
        conditions.value = []
      }
    } else {
      // Empty or invalid rule - only reset if we don't have conditions
      if (conditions.value.length === 0) {
        conditions.value = []
        logicOperator.value = 'and'
      }
    }
  } catch (e) {
    console.error('Error initializing rule from value:', e, source)
    // On parse error, don't reset if user is editing
    if (conditions.value.length === 0) {
      conditions.value = []
      logicOperator.value = 'and'
    }
  }
}

initializeFromValue()

watch(() => props.modelValue, (newValue, oldValue) => {
  // Only reinitialize if the change came from outside (not from our own update)
  if (!isInternalUpdate.value) {
    // Check if the value actually changed (avoid unnecessary reinitialization)
    const newStr = typeof newValue === 'string' ? newValue : JSON.stringify(newValue || {})
    const oldStr = typeof oldValue === 'string' ? oldValue : JSON.stringify(oldValue || {})
    
    // Also check if the new value matches what we would generate from current conditions
    // If it does, don't reinitialize (prevents circular updates)
    const currentJsonLogic = convertToJSONLogic()
    const currentStr = JSON.stringify(currentJsonLogic)
    const newParsed = typeof newValue === 'string' ? (() => {
      try { return JSON.parse(newValue) } catch { return {} }
    })() : newValue
    
    // Only reinitialize if the value is truly different from what we have
    if (newStr !== oldStr && newStr !== currentStr) {
      initializeFromValue()
    }
  }
  isInternalUpdate.value = false // Reset flag after check
}, { deep: true })

const getInputType = (field: string): string => {
  const fieldInfo = fieldCategories.value
    .flatMap(cat => cat.fields)
    .find(f => f.value === field)
  
  if (fieldInfo?.type === 'number') return 'number'
  if (fieldInfo?.type === 'boolean') return 'checkbox'
  return 'text'
}

const getPlaceholder = (field: string): string => {
  const examples: Record<string, string> = {
    'total_revenue': 'e.g., 10000',
    'transaction_count': 'e.g., 5',
    'last_purchase_days_ago': 'e.g., 30',
    'customer_tier': 'e.g., Gold, Silver, Bronze',
    'city': 'e.g., New York',
    'churn_score': 'e.g., 0.5 (0-1 scale)',
  }
  return examples[field] || 'Enter value'
}

const isListOperator = (operator: string): boolean => {
  return operator === 'in' || operator === 'not_in'
}

const addCondition = () => {
  conditions.value.push({
    field: '',
    operator: 'equals',
    value: ''
  })
}

const removeCondition = (index: number) => {
  conditions.value.splice(index, 1)
  updateRule()
}

const clearAll = () => {
  conditions.value = []
  updateRule()
}

const convertToJSONLogic = (): object => {
  if (conditions.value.length === 0) {
    return {}
  }
  
  const logicRules = conditions.value
    .filter(c => c.field && c.value !== '')
    .map(condition => {
      const fieldVar = { var: condition.field }
      const value = condition.field === 'age' || condition.field === 'churn_score' || 
                    condition.field.includes('count') || condition.field.includes('revenue') ||
                    condition.field.includes('value') || condition.field.includes('balance') ||
                    condition.field.includes('days') || condition.field.includes('rate')
        ? parseFloat(condition.value as string) || 0
        : condition.value
      
      switch (condition.operator) {
        case 'equals':
          return { '==': [fieldVar, value] }
        case 'not_equals':
          return { '!=': [fieldVar, value] }
        case 'greater_than':
          return { '>': [fieldVar, value] }
        case 'less_than':
          return { '<': [fieldVar, value] }
        case 'greater_equal':
          return { '>=': [fieldVar, value] }
        case 'less_equal':
          return { '<=': [fieldVar, value] }
        case 'contains':
          return { 'in': [value, fieldVar] }
        case 'not_contains':
          return { '!': { 'in': [value, fieldVar] } }
        case 'starts_with':
          return { '==': [{ 'substr': [fieldVar, 0, (value as string).length] }, value] }
        case 'ends_with':
          return { '==': [{ 'substr': [fieldVar, -((value as string).length)] }, value] }
        case 'in':
          const values = (condition.value as string).split(',').map(v => v.trim())
          return { 'in': [fieldVar, values] }
        case 'not_in':
          const notValues = (condition.value as string).split(',').map(v => v.trim())
          return { '!': { 'in': [fieldVar, notValues] } }
        default:
          return { '==': [fieldVar, value] }
      }
    })
  
  if (logicRules.length === 0) {
    return {}
  }
  
  if (logicRules.length === 1) {
    return logicRules[0]
  }
  
  return {
    [logicOperator.value]: logicRules
  }
}

const updateRule = () => {
  isInternalUpdate.value = true // Set flag before emitting
  const jsonLogic = convertToJSONLogic()
  const jsonString = JSON.stringify(jsonLogic)
  emit('update:modelValue', jsonString)
  emit('change', jsonLogic)
}

const testRule = () => {
  if (!props.testData) {
    alert('No test data provided. Please provide test data to test the rule.')
    return
  }
  
  try {
    const jsonLogic = convertToJSONLogic()
    const result = evaluateJSONLogic(jsonLogic, props.testData)
    testResult.value = result
    emit('test', result)
  } catch (error) {
    testResult.value = false
    alert('Error testing rule: ' + (error as Error).message)
  }
}

const evaluateJSONLogic = (rule: any, data: Record<string, any>): boolean => {
  if (!rule || Object.keys(rule).length === 0) return true
  
  if (rule.and) {
    return rule.and.every((r: any) => evaluateJSONLogic(r, data))
  }
  
  if (rule.or) {
    return rule.or.some((r: any) => evaluateJSONLogic(r, data))
  }
  
  if (rule['==']) {
    const [left, right] = rule['==']
    const leftVal = left.var ? data[left.var] : left
    return leftVal === right
  }
  
  if (rule['!=']) {
    const [left, right] = rule['!=']
    const leftVal = left.var ? data[left.var] : left
    return leftVal !== right
  }
  
  if (rule['>']) {
    const [left, right] = rule['>']
    const leftVal = left.var ? data[left.var] : left
    return Number(leftVal) > Number(right)
  }
  
  if (rule['<']) {
    const [left, right] = rule['<']
    const leftVal = left.var ? data[left.var] : left
    return Number(leftVal) < Number(right)
  }
  
  if (rule['>=']) {
    const [left, right] = rule['>=']
    const leftVal = left.var ? data[left.var] : left
    return Number(leftVal) >= Number(right)
  }
  
  if (rule['<=']) {
    const [left, right] = rule['<=']
    const leftVal = left.var ? data[left.var] : left
    return Number(leftVal) <= Number(right)
  }
  
  if (rule['!']) {
    return !evaluateJSONLogic(rule['!'], data)
  }
  
  if (rule.in) {
    const [item, array] = rule.in
    const itemVal = item.var ? data[item.var] : item
    return Array.isArray(array) && array.includes(itemVal)
  }
  
  return false
}

const jsonOutput = computed(() => {
  return JSON.stringify(convertToJSONLogic(), null, 2)
})
</script>

<style scoped>
.visual-rule-builder {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.builder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.builder-header h3 {
  margin: 0;
  font-size: 1.25rem;
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-primary {
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #666;
}

.help-text {
  font-size: 0.875rem;
  color: #999;
  margin-top: 0.5rem;
}

.logic-selector {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
}

.logic-selector label {
  margin-right: 1rem;
  font-weight: 500;
}

.logic-selector select {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.conditions-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.condition-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: #fafafa;
}

.condition-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.condition-number {
  font-weight: 600;
  color: #2563eb;
}

.condition-body {
  display: grid;
  grid-template-columns: 2fr 1.5fr 2fr;
  gap: 1rem;
}

.field-group {
  display: flex;
  flex-direction: column;
}

.field-group label {
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #666;
}

.field-group select,
.field-group input,
.field-group textarea {
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.875rem;
}

.test-result {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
}

.test-result h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1rem;
}

.result {
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
}

.result.pass {
  background: #d1fae5;
  color: #065f46;
}

.result.fail {
  background: #fee2e2;
  color: #991b1b;
}

.json-preview {
  margin-top: 1.5rem;
  padding: 1rem;
  background: #1e1e1e;
  border-radius: 6px;
}

.json-preview h4 {
  color: white;
  margin: 0 0 0.5rem 0;
}

.json-preview pre {
  color: #d4d4d4;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  margin: 0;
  overflow-x: auto;
}
</style>


