<template>
  <div class="campaign-builder">
    <div class="page-header">
      <div class="header-left">
        <h1>Campaign Builder: {{ campaign.name || 'New Campaign' }}</h1>
        <p v-if="campaign.description" class="subtitle">{{ campaign.description }}</p>
      </div>
      <div class="header-actions">
        <button @click="previewCampaign" class="btn-secondary">Preview</button>
        <button @click="saveCampaign" class="btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Campaign' }}
        </button>
      </div>
    </div>

    <div class="builder-content">
      <!-- Campaign Information -->
      <div class="section">
        <h2>Campaign Information</h2>
        <div class="form-grid">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="campaign.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="campaign.description" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="campaign.status">
              <option value="draft">Draft</option>
              <option value="pending_review">Pending Review</option>
              <option value="approved">Approved</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
              <option value="retired">Retired</option>
            </select>
          </div>
          <div class="form-group">
            <label>Program</label>
            <select v-model="campaign.program">
              <option :value="null">No Specific Program</option>
              <option v-for="p in programs" :key="p.id" :value="p.id">{{ p.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>Start Date</label>
            <input v-model="campaign.start_date" type="datetime-local" />
          </div>
          <div class="form-group">
            <label>End Date</label>
            <input v-model="campaign.end_date" type="datetime-local" />
          </div>
        </div>
      </div>

      <!-- Targeting -->
      <div class="section">
        <h2>Targeting</h2>
        <div class="form-group">
          <label>Segment</label>
          <select v-model="campaign.segment">
            <option :value="null">No Specific Segment</option>
            <option v-for="s in segments" :key="s.id" :value="s.id">{{ s.name }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>Eligibility Rules (JSONLogic)</label>
          <p class="help-text">
            Define additional eligibility criteria beyond segment membership.
          </p>
          <VisualRuleBuilder 
            v-model="campaign.eligibility_rules" 
            :dwh-columns="dwhColumns"
          />
        </div>
      </div>

      <!-- Triggers -->
      <div class="section">
        <TriggerBuilder 
          :triggers="parsedTriggers"
          :dwh-columns="dwhColumns"
          @update:triggers="parsedTriggers = $event"
        />
      </div>

      <!-- Channels -->
      <div class="section">
        <ChannelConfig 
          :channels="parsedChannels"
          @update:channels="parsedChannels = $event"
        />
      </div>

      <!-- Frequency Capping -->
      <div class="section">
        <h2>Frequency Capping</h2>
        <p class="help-text">
          Limit how often customers receive this campaign within a time period.
        </p>
        <div class="form-grid">
          <div class="form-group">
            <label>Cap (0 = Unlimited)</label>
            <input 
              type="number" 
              v-model.number="campaign.frequency_cap" 
              min="0"
              placeholder="e.g., 3"
            />
          </div>
          <div class="form-group">
            <label>Period</label>
            <select v-model="campaign.frequency_period">
              <option value="day">Per Day</option>
              <option value="week">Per Week</option>
              <option value="month">Per Month</option>
              <option value="lifetime">Lifetime</option>
            </select>
          </div>
        </div>
      </div>

      <!-- A/B Testing -->
      <div class="section">
        <h2>A/B Testing</h2>
        <div class="form-group">
          <label>Experiment</label>
          <select v-model="campaign.experiment">
            <option :value="null">No Experiment</option>
            <option v-for="exp in experiments" :key="exp.id" :value="exp.id">{{ exp.name }}</option>
          </select>
          <small class="help-text">Link this campaign to an A/B test experiment</small>
        </div>
      </div>

      <!-- Campaign Preview -->
      <div v-if="showPreview" class="section preview-panel">
        <div class="preview-header">
          <h2>Campaign Preview</h2>
          <button @click="showPreview = false" class="btn-secondary btn-sm">Close</button>
        </div>
        <div class="preview-content">
          <div class="preview-item">
            <strong>Name:</strong> {{ campaign.name || 'Untitled' }}
          </div>
          <div class="preview-item">
            <strong>Status:</strong> {{ campaign.status || 'draft' }}
          </div>
          <div class="preview-item">
            <strong>Triggers:</strong> {{ parsedTriggers.length }} trigger(s)
          </div>
          <div class="preview-item">
            <strong>Channels:</strong> {{ parsedChannels.join(', ') || 'None' }}
          </div>
          <div class="preview-item">
            <strong>Frequency Cap:</strong> 
            {{ campaign.frequency_cap === 0 ? 'Unlimited' : `${campaign.frequency_cap} per ${campaign.frequency_period}` }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { campaignsApi } from '@/api/services/campaigns'
import { segmentsApi } from '@/api/services/segments'
import { programsApi } from '@/api/services/programs'
import { experimentsApi } from '@/api/services/experiments'
import { mlApi } from '@/api/services/ml'
import type { Campaign, Segment, Experiment } from '@/types/loyalty'
import VisualRuleBuilder from '@/components/VisualRuleBuilder.vue'
import TriggerBuilder from '@/components/TriggerBuilder.vue'
import ChannelConfig from '@/components/ChannelConfig.vue'
import { extractData } from '@/utils/api'

const route = useRoute()
const router = useRouter()
const campaign = ref<Partial<Campaign>>({
  name: '',
  description: '',
  status: 'draft',
  eligibility_rules: {},
  program: null,
  segment: null,
  start_date: '',
  end_date: '',
  frequency_cap: 0,
  frequency_period: 'day',
  experiment: null,
})

const saving = ref(false)
const showPreview = ref(false)

const segments = ref<Segment[]>([])
const programs = ref<any[]>([])
const experiments = ref<Experiment[]>([])

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

// Parsed triggers and channels
const parsedTriggers = ref<any[]>([])
const parsedChannels = ref<string[]>([])

// Watch for changes to update campaign object
watch(() => parsedTriggers.value, (newTriggers) => {
  campaign.value.event_triggers = newTriggers.filter(t => t.type === 'event')
  campaign.value.schedule_triggers = newTriggers.filter(t => t.type === 'schedule')
  campaign.value.threshold_triggers = newTriggers.filter(t => t.type === 'threshold')
}, { deep: true })

watch(() => parsedChannels.value, (newChannels) => {
  campaign.value.channels = newChannels
})

const loadCampaign = async (id: string) => {
  try {
    const response = await campaignsApi.getById(id)
    campaign.value = response.data
    
    // Parse JSON fields if they come as strings
    if (typeof campaign.value.eligibility_rules === 'string') {
      campaign.value.eligibility_rules = JSON.parse(campaign.value.eligibility_rules || '{}')
    }
    
    // Parse triggers
    const eventTriggers = typeof campaign.value.event_triggers === 'string' 
      ? JSON.parse(campaign.value.event_triggers || '[]')
      : (campaign.value.event_triggers || [])
    const scheduleTriggers = typeof campaign.value.schedule_triggers === 'string'
      ? JSON.parse(campaign.value.schedule_triggers || '[]')
      : (campaign.value.schedule_triggers || [])
    const thresholdTriggers = typeof campaign.value.threshold_triggers === 'string'
      ? JSON.parse(campaign.value.threshold_triggers || '[]')
      : (campaign.value.threshold_triggers || [])
    
    // Combine all triggers
    parsedTriggers.value = [
      ...eventTriggers.map((t: any) => ({ ...t, type: 'event' })),
      ...scheduleTriggers.map((t: any) => ({ ...t, type: 'schedule' })),
      ...thresholdTriggers.map((t: any) => ({ ...t, type: 'threshold' }))
    ]
    
    // Parse channels
    if (typeof campaign.value.channels === 'string') {
      parsedChannels.value = JSON.parse(campaign.value.channels || '[]')
    } else if (Array.isArray(campaign.value.channels)) {
      parsedChannels.value = campaign.value.channels
    } else {
      parsedChannels.value = []
    }
    
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading campaign:', error)
    }
  }
}

const loadSegmentsAndPrograms = async () => {
  try {
    const [segmentsRes, programsRes, experimentsRes] = await Promise.all([
      segmentsApi.getAll(),
      programsApi.getAll(),
      experimentsApi.getAll(),
    ])
    segments.value = extractData(segmentsRes.data)
    programs.value = extractData(programsRes.data)
    experiments.value = extractData(experimentsRes.data)
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading segments, programs, or experiments:', error)
    }
  }
}

const saveCampaign = async () => {
  saving.value = true
  try {
    const campaignToSave = {
      ...campaign.value,
      eligibility_rules: typeof campaign.value.eligibility_rules === 'object'
        ? JSON.stringify(campaign.value.eligibility_rules)
        : campaign.value.eligibility_rules,
      event_triggers: JSON.stringify(parsedTriggers.value.filter(t => t.type === 'event')),
      schedule_triggers: JSON.stringify(parsedTriggers.value.filter(t => t.type === 'schedule')),
      threshold_triggers: JSON.stringify(parsedTriggers.value.filter(t => t.type === 'threshold')),
      channels: JSON.stringify(parsedChannels.value),
    }
    
    if (route.params.id === 'new') {
      await campaignsApi.create(campaignToSave)
      alert('Campaign created successfully!')
      router.push('/campaigns')
    } else {
      await campaignsApi.update(route.params.id as string, campaignToSave)
      alert('Campaign updated successfully!')
    }
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error saving campaign:', error)
    }
    alert('Error saving campaign. Check your input.')
  } finally {
    saving.value = false
  }
}

const previewCampaign = () => {
  showPreview.value = true
}

onMounted(() => {
  loadSegmentsAndPrograms()
  loadDWHColumns() // Load DWH columns dynamically
  if (route.params.id && route.params.id !== 'new') {
    loadCampaign(route.params.id as string)
  } else {
    // Initialize with empty arrays for new campaigns
    parsedTriggers.value = []
    parsedChannels.value = []
  }
})
</script>

<style scoped>
.campaign-builder {
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
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.form-group textarea {
  resize: vertical;
}

.preview-panel {
  background: #f9fafb;
  border: 2px solid #2563eb;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.preview-content {
  background: white;
  border-radius: 6px;
  padding: 1rem;
}

.preview-item {
  padding: 0.75rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.preview-item:last-child {
  border-bottom: none;
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

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}
</style>
