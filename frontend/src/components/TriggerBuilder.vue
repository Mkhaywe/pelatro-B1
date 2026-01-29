<template>
  <div class="trigger-builder">
    <div class="trigger-header">
      <h3>Campaign Triggers</h3>
      <button @click="addTrigger" class="btn-secondary btn-sm">+ Add Trigger</button>
    </div>
    
    <p class="help-text">
      Define when and how campaigns are triggered. Multiple triggers can be combined with AND/OR logic.
    </p>
    
    <div v-if="triggers.length === 0" class="empty-state">
      <p>No triggers defined. Add a trigger to activate this campaign.</p>
    </div>
    
    <div v-else class="triggers-list">
      <div 
        v-for="(trigger, index) in triggers" 
        :key="index"
        class="trigger-card"
      >
        <div class="trigger-header-card">
          <div class="trigger-type-selector">
            <select v-model="trigger.type" @change="onTriggerTypeChange(index)" class="type-select">
              <option value="event">Event Trigger</option>
              <option value="schedule">Schedule Trigger</option>
              <option value="threshold">Threshold Trigger</option>
            </select>
            <span class="trigger-number">Trigger {{ index + 1 }}</span>
          </div>
          <button @click="removeTrigger(index)" class="btn-danger btn-sm">Remove</button>
        </div>
        
        <!-- Event Trigger -->
        <div v-if="trigger.type === 'event'" class="trigger-content">
          <div class="field-group">
            <label>Event Name</label>
            <select 
              v-model="trigger.event_name" 
              @change="updateTriggers"
              class="event-select"
            >
              <option value="">-- Select Event Type --</option>
              <optgroup v-for="category in eventCategories" :key="category.name" :label="category.name">
                <option 
                  v-for="event in category.events" 
                  :key="event.value" 
                  :value="event.value"
                >
                  {{ event.label }}
                </option>
              </optgroup>
              <option value="custom">Custom Event (enter below)</option>
            </select>
            <input 
              v-if="trigger.event_name === 'custom'"
              v-model="trigger.custom_event_name" 
              placeholder="Enter custom event name"
              @input="updateTriggers"
              class="custom-event-input"
            />
          </div>
          <div class="field-group">
            <label>Event Conditions (JSONLogic - Optional)</label>
            <VisualRuleBuilder 
              v-model="trigger.conditions"
              :dwh-columns="dwhColumns"
              @update:model-value="(rules) => { trigger.conditions = rules; updateTriggers() }"
            />
            <small class="help-text">Leave empty to trigger on any event of this name</small>
          </div>
        </div>
        
        <!-- Schedule Trigger -->
        <div v-if="trigger.type === 'schedule'" class="trigger-content">
          <div class="field-group">
            <label>Schedule Type</label>
            <select v-model="trigger.schedule_type" @change="updateTriggers">
              <option value="cron">Cron Expression</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
              <option value="monthly">Monthly</option>
              <option value="once">Once (Specific Date/Time)</option>
            </select>
          </div>
          
          <div v-if="trigger.schedule_type === 'cron'" class="field-group">
            <label>Cron Expression</label>
            <input 
              v-model="trigger.cron_expression" 
              placeholder="e.g., 0 9 * * * (9 AM daily)"
              @input="updateTriggers"
            />
            <small class="help-text">Format: minute hour day month weekday</small>
          </div>
          
          <div v-if="trigger.schedule_type === 'daily'" class="field-group">
            <label>Time</label>
            <input 
              v-model="trigger.time" 
              type="time"
              @input="updateTriggers"
            />
          </div>
          
          <div v-if="trigger.schedule_type === 'weekly'" class="field-group">
            <label>Day of Week</label>
            <select v-model="trigger.day_of_week" @change="updateTriggers">
              <option value="0">Sunday</option>
              <option value="1">Monday</option>
              <option value="2">Tuesday</option>
              <option value="3">Wednesday</option>
              <option value="4">Thursday</option>
              <option value="5">Friday</option>
              <option value="6">Saturday</option>
            </select>
            <label>Time</label>
            <input 
              v-model="trigger.time" 
              type="time"
              @input="updateTriggers"
            />
          </div>
          
          <div v-if="trigger.schedule_type === 'monthly'" class="field-group">
            <label>Day of Month</label>
            <input 
              v-model.number="trigger.day_of_month" 
              type="number"
              min="1"
              max="31"
              @input="updateTriggers"
            />
            <label>Time</label>
            <input 
              v-model="trigger.time" 
              type="time"
              @input="updateTriggers"
            />
          </div>
          
          <div v-if="trigger.schedule_type === 'once'" class="field-group">
            <label>Date & Time</label>
            <input 
              v-model="trigger.datetime" 
              type="datetime-local"
              @input="updateTriggers"
            />
          </div>
        </div>
        
        <!-- Threshold Trigger -->
        <div v-if="trigger.type === 'threshold'" class="trigger-content">
          <div class="field-group">
            <label>Metric</label>
            <select v-model="trigger.metric" @change="updateTriggers">
              <option value="points_balance">Points Balance</option>
              <option value="transaction_count">Transaction Count</option>
              <option value="total_revenue">Total Revenue</option>
              <option value="days_since_last">Days Since Last Activity</option>
              <option value="custom">Custom (DWH Column)</option>
            </select>
          </div>
          
          <div v-if="trigger.metric === 'custom'" class="field-group">
            <label>Custom Metric (DWH Column)</label>
            <input 
              v-model="trigger.custom_metric" 
              placeholder="e.g., lifetime_value"
              @input="updateTriggers"
            />
          </div>
          
          <div class="field-group">
            <label>Operator</label>
            <select v-model="trigger.operator" @change="updateTriggers">
              <option value=">">Greater Than</option>
              <option value=">=">Greater Than or Equal</option>
              <option value="<">Less Than</option>
              <option value="<=">Less Than or Equal</option>
              <option value="==">Equal To</option>
              <option value="!=">Not Equal To</option>
            </select>
          </div>
          
          <div class="field-group">
            <label>Threshold Value</label>
            <input 
              v-model.number="trigger.threshold_value" 
              type="number"
              @input="updateTriggers"
            />
          </div>
          
          <div class="field-group">
            <label>Evaluation Period (Days)</label>
            <input 
              v-model.number="trigger.evaluation_period" 
              type="number"
              min="1"
              placeholder="e.g., 30"
              @input="updateTriggers"
            />
            <small class="help-text">How many days back to evaluate the metric</small>
          </div>
        </div>
        
        <!-- Trigger Logic -->
        <div class="trigger-logic">
          <label>Combine with next trigger:</label>
          <select v-model="trigger.logic" @change="updateTriggers">
            <option value="and">AND</option>
            <option value="or">OR</option>
          </select>
        </div>
      </div>
    </div>
    
    <!-- Trigger Preview -->
    <div v-if="triggers.length > 0" class="trigger-preview">
      <h4>Trigger Logic Preview</h4>
      <div class="preview-logic">
        <span 
          v-for="(trigger, index) in triggers" 
          :key="index"
          class="preview-trigger"
        >
          <span class="trigger-badge" :class="`type-${trigger.type}`">
            {{ getTriggerLabel(trigger) }}
          </span>
          <span v-if="index < triggers.length - 1" class="logic-operator">
            {{ trigger.logic?.toUpperCase() || 'AND' }}
          </span>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import VisualRuleBuilder from './VisualRuleBuilder.vue'

interface Trigger {
  type: 'event' | 'schedule' | 'threshold'
  logic?: 'and' | 'or'
  // Event trigger fields
  event_name?: string
  custom_event_name?: string
  conditions?: any
  // Schedule trigger fields
  schedule_type?: 'cron' | 'daily' | 'weekly' | 'monthly' | 'once'
  cron_expression?: string
  time?: string
  day_of_week?: string
  day_of_month?: number
  datetime?: string
  // Threshold trigger fields
  metric?: string
  custom_metric?: string
  operator?: string
  threshold_value?: number
  evaluation_period?: number
}

const props = defineProps<{
  triggers: Trigger[]
  dwhColumns?: string[]
}>()

const emit = defineEmits(['update:triggers'])

const triggers = ref<Trigger[]>([...props.triggers])
const eventTypes = ref<Array<{value: string; label: string; category: string}>>([])
const loadingEvents = ref(false)

// Load event types from backend
const loadEventTypes = async () => {
  loadingEvents.value = true
  try {
    const { mlApi } = await import('@/api/services/ml')
    const response = await mlApi.getEventTypes()
    eventTypes.value = response.data
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading event types:', error)
    }
    // Fallback to default events
    eventTypes.value = [
      { value: 'customer.login', label: 'Customer Login', category: 'customer' },
      { value: 'transaction.purchase', label: 'Purchase Made', category: 'transaction' },
      { value: 'loyalty.points_earned', label: 'Points Earned', category: 'loyalty' },
      { value: 'loyalty.tier_upgraded', label: 'Tier Upgraded', category: 'loyalty' },
    ]
  } finally {
    loadingEvents.value = false
  }
}

// Group events by category
const eventCategories = computed(() => {
  const categories = new Map<string, Array<{value: string; label: string}>>()
  eventTypes.value.forEach(event => {
    if (!categories.has(event.category)) {
      categories.set(event.category, [])
    }
    categories.get(event.category)!.push({ value: event.value, label: event.label })
  })
  return Array.from(categories.entries()).map(([name, events]) => ({ name, events }))
})

watch(() => props.triggers, (newTriggers) => {
  triggers.value = [...newTriggers]
}, { deep: true })

const updateTriggers = () => {
  emit('update:triggers', [...triggers.value])
}

// Load event types on component mount
onMounted(() => {
  loadEventTypes()
})

const addTrigger = () => {
  triggers.value.push({
    type: 'event',
    logic: 'and',
    event_name: '',
    custom_event_name: '',
    conditions: {}
  })
  updateTriggers()
}

const removeTrigger = (index: number) => {
  triggers.value.splice(index, 1)
  updateTriggers()
}

const onTriggerTypeChange = (index: number) => {
  // Reset trigger-specific fields when type changes
  const trigger = triggers.value[index]
  if (trigger.type === 'event') {
    trigger.event_name = ''
    trigger.custom_event_name = ''
    trigger.conditions = {}
  } else if (trigger.type === 'schedule') {
    trigger.schedule_type = 'daily'
    trigger.time = '09:00'
    trigger.cron_expression = ''
  } else if (trigger.type === 'threshold') {
    trigger.metric = 'points_balance'
    trigger.operator = '>'
    trigger.threshold_value = 0
    trigger.evaluation_period = 30
  }
  updateTriggers()
}

const getTriggerLabel = (trigger: Trigger): string => {
  if (trigger.type === 'event') {
    const eventName = trigger.event_name === 'custom' ? trigger.custom_event_name : trigger.event_name
    return `Event: ${eventName || 'unnamed'}`
  } else if (trigger.type === 'schedule') {
    if (trigger.schedule_type === 'cron') {
      return `Cron: ${trigger.cron_expression || 'not set'}`
    } else if (trigger.schedule_type === 'daily') {
      return `Daily at ${trigger.time || '09:00'}`
    } else if (trigger.schedule_type === 'weekly') {
      const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
      return `Weekly: ${days[parseInt(trigger.day_of_week || '0')]} at ${trigger.time || '09:00'}`
    } else if (trigger.schedule_type === 'monthly') {
      return `Monthly: Day ${trigger.day_of_month || 1} at ${trigger.time || '09:00'}`
    } else if (trigger.schedule_type === 'once') {
      return `Once: ${trigger.datetime || 'not set'}`
    }
    return 'Schedule'
  } else if (trigger.type === 'threshold') {
    const metric = trigger.custom_metric || trigger.metric || 'metric'
    return `Threshold: ${metric} ${trigger.operator || '>'} ${trigger.threshold_value || 0}`
  }
  return 'Unknown'
}
</script>

<style scoped>
.trigger-builder {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.trigger-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.trigger-header h3 {
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

.triggers-list {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.trigger-card {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
  background: #f9fafb;
}

.trigger-header-card {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.trigger-type-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.type-select {
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-weight: 600;
  background: white;
}

.trigger-number {
  font-size: 0.875rem;
  color: #666;
  font-weight: 500;
}

.trigger-content {
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
.field-group select {
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.field-group small {
  font-size: 0.75rem;
  color: #999;
}

.trigger-logic {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.trigger-logic label {
  font-size: 0.875rem;
  font-weight: 500;
}

.trigger-logic select {
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.trigger-preview {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e0e0e0;
}

.trigger-preview h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.preview-logic {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.preview-trigger {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.trigger-badge {
  padding: 0.5rem 1rem;
  border-radius: 20px;
  font-size: 0.875rem;
  font-weight: 500;
  background: #e5e7eb;
  color: #374151;
}

.trigger-badge.type-event {
  background: #dbeafe;
  color: #1e40af;
}

.trigger-badge.type-schedule {
  background: #fef3c7;
  color: #92400e;
}

.trigger-badge.type-threshold {
  background: #d1fae5;
  color: #065f46;
}

.logic-operator {
  font-weight: 700;
  color: #6b7280;
  font-size: 0.875rem;
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

