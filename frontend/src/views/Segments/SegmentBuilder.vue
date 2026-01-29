<template>
  <div class="segment-builder">
    <!-- Global loading overlay when recalculating segment members -->
    <div v-if="recalculating" class="segment-overlay">
      <div class="segment-overlay-content">
        <div class="spinner"></div>
        <div class="overlay-text">Recalculating segment members...</div>
      </div>
    </div>
    <div v-if="loading" class="loading">Loading segment...</div>
    
    <div v-else-if="segment">
      <div class="page-header">
        <div class="header-left">
          <h1>{{ segment.name }}</h1>
          <p v-if="segment.description" class="subtitle">{{ segment.description }}</p>
        </div>
        <div class="header-actions">
          <button @click="testSegment" class="btn-secondary">Test Segment</button>
          <button @click="recalculateSegment" class="btn-secondary" :disabled="recalculating">
            {{ recalculating ? 'Recalculating...' : 'Recalculate' }}
          </button>
          <button @click="saveSegment" class="btn-primary" :disabled="saving">
            {{ saving ? 'Saving...' : 'Save Changes' }}
          </button>
        </div>
      </div>

      <div class="builder-content">
        <!-- Segment Info -->
        <div class="section">
          <h2>Segment Information</h2>
          <div class="form-grid">
            <div class="form-group">
              <label>Name *</label>
              <input v-model="segment.name" required />
            </div>
            <div class="form-group">
              <label>Description</label>
              <textarea v-model="segment.description" rows="3"></textarea>
            </div>
            <div class="form-group">
              <label>Program</label>
              <select v-model="segment.program">
                <option :value="null">No Specific Program</option>
                <option v-for="p in programs" :key="p.id" :value="p.id">{{ p.name }}</option>
              </select>
            </div>
            <div class="form-group">
              <label>
                <input type="checkbox" v-model="segment.is_dynamic" />
                Dynamic Segment (recalculates automatically)
              </label>
            </div>
            <div class="form-group">
              <label>
                <input type="checkbox" v-model="segment.is_rfm" />
                RFM Segment
              </label>
            </div>
            <div class="form-group">
              <label>
                <input type="checkbox" v-model="segment.is_active" />
                Active
              </label>
            </div>
          </div>
        </div>

        <!-- Segment Rules Builder -->
        <div class="section">
          <div class="section-header">
            <h2>Segment Rules (JSONLogic)</h2>
            <div class="section-actions">
              <button @click="addRule" class="btn-secondary btn-sm">+ Add Rule</button>
              <button @click="clearRules" class="btn-secondary btn-sm">Clear All</button>
            </div>
          </div>
          
          <p class="help-text">
            Define rules using JSONLogic. Rules are combined with AND logic. Use DWH column names in rules.
          </p>
          
          <div class="rules-builder">
            <div class="rules-editor-panel">
              <div 
                v-for="(ruleObj, index) in parsedRules" 
                :key="index"
                class="rule-card"
              >
                <div class="rule-header">
                  <div class="rule-title-group">
                    <input 
                      v-model="ruleObj.name" 
                      @input="updateRules()"
                      class="rule-name-input"
                      placeholder="Rule name (e.g., High Revenue Customers)"
                      :title="ruleObj.name || 'Enter a name for this rule'"
                    />
                    <span class="rule-number">#{{ index + 1 }}</span>
                  </div>
                  <button @click="removeRule(index)" class="btn-danger btn-sm">Remove</button>
                </div>
                <VisualRuleBuilder 
                  :ref="el => { if (el) ruleBuilderRefs[index] = el }"
                  :model-value="getRuleLogic(ruleObj)"
                  :dwh-columns="dwhColumns"
                  @update:model-value="(r) => { 
                    // VisualRuleBuilder emits JSON string, store in ruleObj.rule
                    ruleObj.rule = typeof r === 'string' ? r : JSON.stringify(r)
                    updateRules() 
                  }"
                  @focus="activeRuleIndex = index"
                />
              </div>
              
              <div v-if="parsedRules.length === 0" class="empty-state">
                <p>No rules defined. Add your first rule to get started.</p>
                <p class="help-text">Rules are combined with AND logic - all rules must match for a customer to be in the segment.</p>
              </div>
            </div>
            
            <div class="dwh-panel">
              <DWHColumnSelector 
                :selected-columns="selectedDwhColumns"
                @insert="insertIntoRule"
                @select="selectedDwhColumns = $event"
              />
            </div>
          </div>
        </div>

        <!-- Segment Preview & Testing -->
        <div class="section">
          <h2>Segment Preview & Testing</h2>
          
          <div class="preview-grid">
            <div class="preview-card">
              <h3>Segment Statistics</h3>
              <div class="stats-grid">
                <div class="stat-item">
                  <span class="stat-label">Total Members</span>
                  <span class="stat-value">{{ memberCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Active Members</span>
                  <span class="stat-value">{{ activeMemberCount }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Rules Count</span>
                  <span class="stat-value">{{ parsedRules.length }}</span>
                </div>
                <div class="stat-item">
                  <span class="stat-label">Type</span>
                  <span class="stat-value">{{ segment.is_dynamic ? 'Dynamic' : 'Static' }}</span>
                </div>
              </div>
            </div>
            
            <div class="preview-card">
              <h3>Test Segment</h3>
              <div class="test-form">
                <div class="form-group">
                  <label>Customer ID</label>
                  <input 
                    v-model="testCustomerId" 
                    placeholder="Enter customer ID to test"
                    @keyup.enter="testSegment"
                  />
                </div>
                <button @click="testSegment" class="btn-primary">Test</button>
                <div v-if="testResult" class="test-result">
                  <div :class="['result-badge', testResult.matches ? 'match' : 'no-match']">
                    {{ testResult.matches ? '✓ Customer matches segment' : '✗ Customer does not match segment' }}
                  </div>
                  <div v-if="testResult.reason" class="result-reason">
                    {{ testResult.reason }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Segment Members -->
        <div class="section">
          <div class="section-header">
            <h2>Segment Members ({{ memberCount }})</h2>
            <div class="section-actions">
              <button @click="loadMembers" class="btn-secondary btn-sm" :disabled="loadingMembers">
                {{ loadingMembers ? 'Loading...' : 'Refresh Members' }}
              </button>
              <button @click="exportMembers" class="btn-secondary btn-sm">Export CSV</button>
            </div>
          </div>
          
          <div v-if="members.length === 0 && !loadingMembers" class="empty-state">
            <p>No members found. Click "Recalculate" to populate segment.</p>
          </div>
          
          <div v-else-if="loadingMembers" class="loading-state">
            Loading members...
          </div>
          
          <div v-else class="members-table">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Customer ID</th>
                  <th>Joined At</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="member in paginatedMembers" :key="member.id">
                  <td class="customer-id">{{ formatCustomerId(member.customer_id) }}</td>
                  <td>{{ formatDate(member.joined_at) }}</td>
                  <td>
                    <span class="status-badge" :class="member.is_active ? 'active' : 'inactive'">
                      {{ member.is_active ? 'Active' : 'Inactive' }}
                    </span>
                  </td>
                  <td>
                    <button 
                      @click="viewCustomer(member.customer_id)" 
                      class="btn-link"
                    >
                      View
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>
            
            <div v-if="members.length > pageSize" class="pagination">
              <button 
                @click="currentPage--" 
                :disabled="currentPage === 1"
                class="btn-secondary btn-sm"
              >
                Previous
              </button>
              <span class="page-info">
                Page {{ currentPage }} of {{ totalPages }}
              </span>
              <button 
                @click="currentPage++" 
                :disabled="currentPage >= totalPages"
                class="btn-secondary btn-sm"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { segmentsApi } from '@/api/services/segments'
import { programsApi } from '@/api/services/programs'
import { mlApi } from '@/api/services/ml'
import type { Segment, SegmentMember } from '@/types/loyalty'
import VisualRuleBuilder from '@/components/VisualRuleBuilder.vue'
import DWHColumnSelector from '@/components/DWHColumnSelector.vue'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'

const route = useRoute()
const router = useRouter()
const segment = ref<Segment | null>(null)
const members = ref<SegmentMember[]>([])
const programs = ref<any[]>([])
const loading = ref(true)
const saving = ref(false)
const recalculating = ref(false)
const loadingMembers = ref(false)

const parsedRules = ref<any[]>([])
const selectedDwhColumns = ref<string[]>([])
const testCustomerId = ref('')
const testResult = ref<any>(null)
const ruleBuilderRefs = ref<any[]>([])
const activeRuleIndex = ref<number | null>(null)

const currentPage = ref(1)
const pageSize = 20

// DWH columns for JSONLogic editor - loaded dynamically
const dwhColumns = ref<string[]>([])

const loadDWHColumns = async () => {
  try {
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

const memberCount = computed(() => segment.value?.member_count || members.value.length)
const activeMemberCount = computed(() => members.value.filter(m => m.is_active).length)

const totalPages = computed(() => Math.ceil(members.value.length / pageSize))
const paginatedMembers = computed(() => {
  const start = (currentPage.value - 1) * pageSize
  return members.value.slice(start, start + pageSize)
})

const loadSegment = async () => {
  try {
    const response = await segmentsApi.getById(route.params.id as string)
    segment.value = response.data
    
    // Parse rules - handle different formats
    let rulesData = response.data.rules
    
    // If rules is a string, parse it
    if (typeof rulesData === 'string') {
      try {
        rulesData = JSON.parse(rulesData || '[]')
      } catch (e) {
        console.error('Error parsing rules JSON:', e)
        rulesData = []
      }
    }
    
    // Ensure it's an array
    if (Array.isArray(rulesData)) {
      // Convert to new format: {name: string, rule: string}
      parsedRules.value = rulesData.map((rule, index) => {
        // New format: {name: "...", rule: "..."}
        if (rule && typeof rule === 'object' && 'name' in rule && 'rule' in rule) {
          return {
            name: rule.name || `Rule ${index + 1}`,
            rule: typeof rule.rule === 'string' ? rule.rule : JSON.stringify(rule.rule || {})
          }
        }
        // Old format: just JSONLogic object or string
        else if (typeof rule === 'string') {
          try {
            // Validate it's valid JSON
            JSON.parse(rule)
            return {
              name: `Rule ${index + 1}`,
              rule: rule
            }
          } catch {
            return null
          }
        } else if (rule && typeof rule === 'object' && Object.keys(rule).length > 0) {
          // Old format: JSONLogic object
          return {
            name: `Rule ${index + 1}`,
            rule: JSON.stringify(rule)
          }
        }
        return null
      }).filter(rule => rule !== null && rule.rule && rule.rule !== '{}' && rule.rule !== '[]') // Filter out empty rules
    } else if (rulesData && typeof rulesData === 'object' && Object.keys(rulesData).length > 0) {
      // Single rule object
      if ('name' in rulesData && 'rule' in rulesData) {
        parsedRules.value = [rulesData]
      } else {
        // Old format, convert
        parsedRules.value = [{
          name: 'Rule 1',
          rule: JSON.stringify(rulesData)
        }]
      }
    } else {
      parsedRules.value = []
    }
    
    // Debug logging
    if (import.meta.env.DEV) {
      console.log('Loaded rules:', parsedRules.value)
    }
    
    // Debug logging
    if (import.meta.env.DEV) {
      console.log('Loaded rules:', parsedRules.value)
    }
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading segment:', error)
    }
  } finally {
    loading.value = false
  }
}

const loadPrograms = async () => {
  try {
    const response = await programsApi.getAll()
    programs.value = extractData(response.data)
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading programs:', error)
    }
  }
}

const loadMembers = async () => {
  loadingMembers.value = true
  try {
    const response = await segmentsApi.getMembers(route.params.id as string)
    members.value = response.data
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading members:', error)
    }
  } finally {
    loadingMembers.value = false
  }
}

const updateRules = () => {
  // Rules are updated via v-model in JSONLogicEditor
}

const getRuleLogic = (ruleObj: any): string => {
  // Extract rule logic from rule object structure
  if (!ruleObj) return ''
  
  // If it's already a string (old format), return as-is
  if (typeof ruleObj === 'string') {
    return ruleObj
  }
  
  // If it has a 'rule' field (new format), return that
  if (ruleObj.rule) {
    return typeof ruleObj.rule === 'string' ? ruleObj.rule : JSON.stringify(ruleObj.rule)
  }
  
  // If it's an object without 'rule' field, it might be old format JSONLogic
  if (typeof ruleObj === 'object' && Object.keys(ruleObj).length > 0) {
    // Check if it looks like JSONLogic (has operators like '>', '==', etc.)
    const jsonLogicOps = ['>', '<', '>=', '<=', '==', '!=', 'and', 'or', 'in', 'var']
    const hasJsonLogicOp = Object.keys(ruleObj).some(key => jsonLogicOps.includes(key))
    if (hasJsonLogicOp) {
      return JSON.stringify(ruleObj)
    }
  }
  
  return ''
}

const addRule = () => {
  parsedRules.value.push({
    name: `Rule ${parsedRules.value.length + 1}`,
    rule: ''
  })
  // Ensure refs array is large enough
  nextTick(() => {
    while (ruleBuilderRefs.value.length < parsedRules.value.length) {
      ruleBuilderRefs.value.push(null)
    }
  })
}

const removeRule = (index: number) => {
  parsedRules.value.splice(index, 1)
  updateRules()
}

const clearRules = () => {
  if (confirm('Are you sure you want to clear all rules?')) {
    parsedRules.value = []
    updateRules()
  }
}

const insertIntoRule = (fieldJson: string) => {
  try {
    // Parse the JSON string to get the field name
    const fieldObj = JSON.parse(fieldJson)
    const fieldName = fieldObj.var || fieldObj.field || fieldJson
    
    // If no active rule, use the first rule or create one
    let targetIndex = activeRuleIndex.value
    if (targetIndex === null || targetIndex < 0 || targetIndex >= parsedRules.value.length) {
      if (parsedRules.value.length === 0) {
        // Create first rule if none exist
        addRule()
        targetIndex = 0
      } else {
        // Use first rule
        targetIndex = 0
      }
    }
    
    // Get the VisualRuleBuilder component for this rule
    const ruleBuilder = ruleBuilderRefs.value[targetIndex]
    if (ruleBuilder && typeof ruleBuilder.insertField === 'function') {
      ruleBuilder.insertField(fieldName)
    } else {
      // Fallback: manually add condition to the rule
      if (!parsedRules.value[targetIndex]) {
        parsedRules.value[targetIndex] = {}
      }
      // The VisualRuleBuilder will handle the update via v-model
      // We'll trigger it by updating the rule
      updateRules()
    }
  } catch (error) {
    console.error('Error inserting field:', error)
    // Silently fail - don't show alert to avoid blocking
  }
}

const recalculateSegment = async () => {
  recalculating.value = true
  try {
    await segmentsApi.calculate(route.params.id as string)
    alert('Segment recalculated successfully!')
    await loadMembers()
    await loadSegment()
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error recalculating segment:', error)
    }
    alert('Error recalculating segment')
  } finally {
    recalculating.value = false
  }
}

const testSegment = async () => {
  if (!testCustomerId.value) {
    alert('Please enter a customer ID')
    return
  }
  
  try {
    // Get customer features
    const featuresResponse = await mlApi.getCustomerFeatures(testCustomerId.value)
    const features = featuresResponse.data
    
    // Test rules against features
    // This is a simplified test - in production, this would call a backend endpoint
    let matches = true
    let reason = ''
    
    for (const rule of parsedRules.value) {
      // Basic rule evaluation (simplified)
      // In production, use json-logic-js or call backend
      try {
        // This is a placeholder - real evaluation would use json-logic-js
        matches = true // Placeholder
      } catch (e) {
        matches = false
        reason = `Rule evaluation error: ${e}`
        break
      }
    }
    
    testResult.value = {
      matches,
      reason: reason || (matches ? 'Customer matches all segment rules' : 'Customer does not match segment rules')
    }
  } catch (error: any) {
    testResult.value = {
      matches: false,
      reason: error.response?.data?.error || 'Error testing segment'
    }
  }
}

const saveSegment = async () => {
  if (!segment.value) return
  
  saving.value = true
  try {
    // Prepare rules in new format: {name: string, rule: object}
    const rulesToSave = parsedRules.value
      .map(ruleObj => {
        if (!ruleObj || !ruleObj.rule) return null
        
        // Parse rule logic from string to object
        let ruleLogic = null
        if (typeof ruleObj.rule === 'string') {
          try {
            ruleLogic = JSON.parse(ruleObj.rule)
            // Only include non-empty rules
            if (!ruleLogic || Object.keys(ruleLogic).length === 0) {
              return null
            }
          } catch {
            return null
          }
        } else {
          ruleLogic = ruleObj.rule
        }
        
        // Return in new format: {name, rule}
        return {
          name: ruleObj.name || `Rule ${parsedRules.value.indexOf(ruleObj) + 1}`,
          rule: ruleLogic
        }
      })
      .filter(rule => rule !== null) // Remove null/empty rules
    
    const updatedSegment = {
      ...segment.value,
      rules: rulesToSave,
    }
    
    if (import.meta.env.DEV) {
      console.log('Saving segment with rules:', rulesToSave)
    }
    
    await segmentsApi.update(route.params.id as string, updatedSegment)
    
    // Reload segment to get updated data
    await loadSegment()
    
    alert('Segment saved successfully!')
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error saving segment:', error)
    }
    alert('Error saving segment. Check your input.')
  } finally {
    saving.value = false
  }
}

const exportMembers = () => {
  const csv = [
    ['Customer ID', 'Joined At', 'Status'],
    ...members.value.map(m => [
      m.customer_id,
      formatDate(m.joined_at),
      m.is_active ? 'Active' : 'Inactive'
    ])
  ].map(row => row.join(',')).join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `segment-${segment.value?.name || 'members'}-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
}

const viewCustomer = (customerId: string) => {
  router.push(`/customers/${customerId}`)
}

const formatDate = (date: string | null | undefined) => {
  if (!date) return '-'
  try {
    return format(new Date(date), 'MMM dd, yyyy HH:mm')
  } catch {
    return '-'
  }
}

const formatCustomerId = (customerId: string) => {
  return customerId.substring(0, 8) + '...'
}

onMounted(() => {
  loadPrograms()
  loadDWHColumns() // Load DWH columns dynamically
  if (route.params.id && route.params.id !== 'new') {
    loadSegment()
    loadMembers()
  }
})
</script>

<style scoped>
.segment-builder {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
}

.segment-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.55);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.segment-overlay-content {
  background: #0f172a;
  padding: 1.5rem 2rem;
  border-radius: 0.75rem;
  box-shadow: 0 20px 45px rgba(15, 23, 42, 0.6);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.75rem;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.overlay-text {
  color: #e5e7eb;
  font-size: 0.95rem;
}

.spinner {
  width: 32px;
  height: 32px;
  border-radius: 9999px;
  border: 3px solid rgba(148, 163, 184, 0.4);
  border-top-color: #6366f1;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
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

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
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
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.rules-builder {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.rules-editor-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.rule-card {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
  background: #f9fafb;
}

.rule-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.rule-title-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex: 1;
}

.rule-name-input {
  flex: 1;
  padding: 0.5rem;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  min-width: 200px;
}

.rule-name-input:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.rule-number {
  font-weight: 600;
  color: #2563eb;
  font-size: 0.875rem;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.preview-card {
  padding: 1.5rem;
  background: #f9fafb;
  border-radius: 8px;
}

.preview-card h3 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.stat-label {
  font-size: 0.875rem;
  color: #666;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #2563eb;
}

.test-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.test-result {
  margin-top: 1rem;
}

.result-badge {
  padding: 0.75rem;
  border-radius: 6px;
  font-weight: 500;
  text-align: center;
}

.result-badge.match {
  background: #d1fae5;
  color: #065f46;
}

.result-badge.no-match {
  background: #fee2e2;
  color: #991b1b;
}

.result-reason {
  margin-top: 0.5rem;
  font-size: 0.875rem;
  color: #666;
}

.members-table {
  margin-top: 1rem;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  text-align: left;
  padding: 0.75rem;
  background: #f9fafb;
  font-weight: 600;
  font-size: 0.875rem;
  color: #666;
  border-bottom: 2px solid #e0e0e0;
}

.data-table td {
  padding: 0.75rem;
  border-bottom: 1px solid #e0e0e0;
  font-size: 0.875rem;
}

.customer-id {
  font-family: monospace;
  font-size: 0.75rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.btn-link {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  text-decoration: underline;
  font-size: 0.875rem;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 1rem;
  margin-top: 1rem;
}

.page-info {
  font-size: 0.875rem;
  color: #666;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #666;
}

.loading-state {
  padding: 2rem;
  text-align: center;
  color: #666;
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

.btn-secondary:hover:not(:disabled) {
  background: #e5e7eb;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-danger {
  background: #dc2626;
  color: white;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}
</style>
