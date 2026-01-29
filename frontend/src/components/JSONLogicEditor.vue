<template>
  <div class="jsonlogic-editor">
    <div class="editor-header">
      <h3>JSONLogic Rule Editor</h3>
      <div class="editor-actions">
        <button @click="formatJSON" class="btn-secondary">Format</button>
        <button @click="validateJSON" class="btn-secondary">Validate</button>
        <button @click="testRule" class="btn-primary">Test Rule</button>
      </div>
    </div>
    
    <div class="editor-container">
      <div class="editor-main">
        <textarea
          ref="editorRef"
          v-model="ruleJson"
          class="code-editor"
          :class="{ 'error': hasError }"
          @input="onInput"
          placeholder='{"and": [{">": {"var": "total_revenue"}, 1000}]}'
        ></textarea>
        <div v-if="errorMessage" class="error-message">
          {{ errorMessage }}
        </div>
      </div>
      
      <div class="editor-sidebar">
        <h4>Quick Insert</h4>
        <div class="quick-insert">
          <button @click="insertComparison" class="insert-btn">Comparison</button>
          <button @click="insertAnd" class="insert-btn">AND</button>
          <button @click="insertOr" class="insert-btn">OR</button>
          <button @click="insertVar" class="insert-btn">Variable</button>
        </div>
        
        <h4>DWH Columns</h4>
        <div class="dwh-columns">
          <button
            v-for="col in dwhColumns"
            :key="col"
            @click="insertColumn(col)"
            class="column-btn"
          >
            {{ col }}
          </button>
        </div>
        
        <div v-if="testResult !== null" class="test-result">
          <h4>Test Result</h4>
          <div :class="['result', testResult ? 'pass' : 'fail']">
            {{ testResult ? '✓ Rule matches' : '✗ Rule does not match' }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  modelValue?: string | object
  rules?: string | object
  dwhColumns?: string[]
  testData?: Record<string, any>
}>()

const emit = defineEmits<{
  'update:modelValue': [value: string]
  'update:rules': [value: object]
  'change': [value: object]
  'test': [result: boolean]
}>()

const editorRef = ref<HTMLTextAreaElement>()
const ruleJson = ref('')
const hasError = ref(false)
const errorMessage = ref('')
const testResult = ref<boolean | null>(null)

// Default DWH columns if not provided
const dwhColumns = ref(props.dwhColumns || [
  'total_revenue',
  'transaction_count',
  'days_since_last_purchase',
  'avg_transaction_value',
  'lifetime_value',
  'churn_score',
  'segment'
])

// Initialize ruleJson from modelValue or rules prop
const initializeRuleJson = () => {
  const source = props.rules || props.modelValue
  if (typeof source === 'string') {
    ruleJson.value = source
  } else if (source) {
    ruleJson.value = JSON.stringify(source, null, 2)
  } else {
    ruleJson.value = '{}'
  }
}

initializeRuleJson()

watch(() => props.modelValue, (newVal) => {
  if (typeof newVal === 'string') {
    ruleJson.value = newVal
  } else if (newVal) {
    ruleJson.value = JSON.stringify(newVal, null, 2)
  }
})

watch(() => props.rules, (newVal) => {
  if (typeof newVal === 'string') {
    ruleJson.value = newVal
  } else if (newVal) {
    ruleJson.value = JSON.stringify(newVal, null, 2)
  }
})

const onInput = () => {
  hasError.value = false
  errorMessage.value = ''
  testResult.value = null
  
  try {
    const parsed = JSON.parse(ruleJson.value)
    if (props.rules !== undefined) {
      emit('update:rules', parsed)
    } else {
      emit('update:modelValue', ruleJson.value)
    }
    emit('change', parsed)
  } catch (e) {
    // Invalid JSON, but don't show error while typing
  }
}

const formatJSON = () => {
  try {
    const parsed = JSON.parse(ruleJson.value)
    ruleJson.value = JSON.stringify(parsed, null, 2)
    if (props.rules !== undefined) {
      emit('update:rules', parsed)
    } else {
      emit('update:modelValue', ruleJson.value)
    }
    emit('change', parsed)
    hasError.value = false
    errorMessage.value = ''
  } catch (e: any) {
    hasError.value = true
    errorMessage.value = `Invalid JSON: ${e.message}`
  }
}

const validateJSON = () => {
  try {
    const parsed = JSON.parse(ruleJson.value)
    // Basic JSONLogic validation
    if (typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('Rule must be a JSON object')
    }
    hasError.value = false
    errorMessage.value = '✓ Valid JSONLogic rule'
    setTimeout(() => {
      errorMessage.value = ''
    }, 2000)
  } catch (e: any) {
    hasError.value = true
    errorMessage.value = `Invalid JSONLogic: ${e.message}`
  }
}

const testRule = async () => {
  try {
    const rule = JSON.parse(ruleJson.value)
    const testData = props.testData || {
      total_revenue: 5000,
      transaction_count: 25,
      days_since_last_purchase: 5
    }
    
    // Simple JSONLogic evaluation (basic implementation)
    const result = evaluateJSONLogic(rule, testData)
    testResult.value = result
    emit('test', result)
  } catch (e: any) {
    testResult.value = false
    errorMessage.value = `Test failed: ${e.message}`
  }
}

// Basic JSONLogic evaluator (simplified)
const evaluateJSONLogic = (rule: any, data: Record<string, any>): boolean => {
  if (typeof rule === 'boolean') return rule
  if (typeof rule === 'number') return rule !== 0
  if (typeof rule === 'string') return rule !== ''
  
  if (Array.isArray(rule)) {
    return rule.every(r => evaluateJSONLogic(r, data))
  }
  
  if (typeof rule === 'object') {
    // Handle operators
    if ('and' in rule) {
      return rule.and.every((r: any) => evaluateJSONLogic(r, data))
    }
    if ('or' in rule) {
      return rule.or.some((r: any) => evaluateJSONLogic(r, data))
    }
    if ('>' in rule) {
      const left = evaluateValue(rule['>'][0], data)
      const right = evaluateValue(rule['>'][1], data)
      return left > right
    }
    if ('<' in rule) {
      const left = evaluateValue(rule['<'][0], data)
      const right = evaluateValue(rule['<'][1], data)
      return left < right
    }
    if ('>=' in rule) {
      const left = evaluateValue(rule['>='][0], data)
      const right = evaluateValue(rule['>='][1], data)
      return left >= right
    }
    if ('<=' in rule) {
      const left = evaluateValue(rule['<='][0], data)
      const right = evaluateValue(rule['<='][1], data)
      return left <= right
    }
    if ('==' in rule) {
      const left = evaluateValue(rule['=='][0], data)
      const right = evaluateValue(rule['=='][1], data)
      return left === right
    }
    if ('!=' in rule) {
      const left = evaluateValue(rule['!='][0], data)
      const right = evaluateValue(rule['!='][1], data)
      return left !== right
    }
  }
  
  return false
}

const evaluateValue = (value: any, data: Record<string, any>): any => {
  if (typeof value === 'object' && value !== null && 'var' in value) {
    return data[value.var] || 0
  }
  return value
}

const insertComparison = () => {
  const template = `{
  ">": [
    {"var": "total_revenue"},
    1000
  ]
}`
  insertAtCursor(template)
}

const insertAnd = () => {
  const template = `{
  "and": [
    {"var": "column1"},
    {"var": "column2"}
  ]
}`
  insertAtCursor(template)
}

const insertOr = () => {
  const template = `{
  "or": [
    {"var": "column1"},
    {"var": "column2"}
  ]
}`
  insertAtCursor(template)
}

const insertVar = () => {
  const template = '{"var": "column_name"}'
  insertAtCursor(template)
}

const insertColumn = (column: string) => {
  const template = `{"var": "${column}"}`
  insertAtCursor(template)
}

const insertAtCursor = (text: string) => {
  const textarea = editorRef.value
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const current = ruleJson.value
  
  ruleJson.value = current.substring(0, start) + text + current.substring(end)
  textarea.focus()
  textarea.setSelectionRange(start + text.length, start + text.length)
  
  onInput()
}
</script>

<style scoped>
.jsonlogic-editor {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.editor-header {
  background: #f9fafb;
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.editor-header h3 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.editor-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-secondary {
  padding: 0.5rem 1rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-primary {
  padding: 0.5rem 1rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
}

.editor-container {
  display: flex;
  height: 400px;
}

.editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.code-editor {
  flex: 1;
  padding: 1rem;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  border: none;
  resize: none;
  outline: none;
  background: #1e1e1e;
  color: #d4d4d4;
  line-height: 1.5;
}

.code-editor.error {
  border: 2px solid #ef4444;
}

.error-message {
  padding: 0.5rem 1rem;
  background: #fee2e2;
  color: #991b1b;
  font-size: 0.875rem;
}

.editor-sidebar {
  width: 250px;
  background: #f9fafb;
  border-left: 1px solid #e5e7eb;
  padding: 1rem;
  overflow-y: auto;
}

.editor-sidebar h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.quick-insert {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.insert-btn {
  padding: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  text-align: left;
}

.insert-btn:hover {
  background: #f3f4f6;
}

.dwh-columns {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
}

.column-btn {
  padding: 0.5rem;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.75rem;
  text-align: left;
  font-family: monospace;
}

.column-btn:hover {
  background: #eff6ff;
  border-color: #2563eb;
}

.test-result {
  margin-top: 1.5rem;
  padding-top: 1rem;
  border-top: 1px solid #e5e7eb;
}

.result {
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
  text-align: center;
}

.result.pass {
  background: #d1fae5;
  color: #065f46;
}

.result.fail {
  background: #fee2e2;
  color: #991b1b;
}
</style>

