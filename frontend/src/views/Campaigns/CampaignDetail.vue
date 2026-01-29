<template>
  <div class="campaign-detail">
    <div v-if="loading" class="loading">Loading campaign...</div>
    
    <div v-else-if="campaign" class="campaign-content">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <h1>{{ campaign.name }}</h1>
          <p class="subtitle">{{ campaign.description || 'No description' }}</p>
          <div class="campaign-meta">
            <span class="status-badge" :class="campaign.status">{{ campaign.status }}</span>
            <span class="meta-item">
              <strong>Start:</strong> {{ formatDate(campaign.start_date) }}
            </span>
            <span class="meta-item">
              <strong>End:</strong> {{ formatDate(campaign.end_date) }}
            </span>
            <span class="meta-item">
              <strong>Version:</strong> {{ campaign.version }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="editCampaign" class="btn-secondary">Edit Campaign</button>
          <button 
            v-if="campaign.status === 'draft' || campaign.status === 'pending_review'"
            @click="activateCampaign" 
            class="btn-primary"
          >
            Activate
          </button>
          <button 
            v-if="campaign.status === 'active'"
            @click="pauseCampaign" 
            class="btn-secondary"
          >
            Pause
          </button>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Total Sent</div>
          <div class="kpi-value">{{ performance.total_sent || 0 }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> All Time
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Delivered</div>
          <div class="kpi-value">{{ performance.delivered || 0 }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> 
            {{ performance.total_sent > 0 ? Math.round((performance.delivered / performance.total_sent) * 100) : 0 }}%
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Opened</div>
          <div class="kpi-value">{{ performance.opened || 0 }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span>
            {{ performance.delivered > 0 ? Math.round((performance.opened / performance.delivered) * 100) : 0 }}%
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Clicked</div>
          <div class="kpi-value">{{ performance.clicked || 0 }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span>
            {{ performance.opened > 0 ? Math.round((performance.clicked / performance.opened) * 100) : 0 }}%
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Converted</div>
          <div class="kpi-value">{{ performance.converted || 0 }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span>
            {{ performance.clicked > 0 ? Math.round((performance.converted / performance.clicked) * 100) : 0 }}%
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Conversion Rate</div>
          <div class="kpi-value">{{ conversionRate }}%</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> Overall
          </div>
        </div>
      </div>

      <!-- Tabs -->
      <div class="tabs">
        <button 
          v-for="tab in tabs" 
          :key="tab.id"
          @click="activeTab = tab.id"
          :class="['tab-button', { active: activeTab === tab.id }]"
        >
          {{ tab.label }}
        </button>
      </div>

      <!-- Tab Content -->
      <div class="tab-content">
        <!-- Overview Tab -->
        <div v-if="activeTab === 'overview'" class="tab-panel">
          <div class="section">
            <h2>Campaign Information</h2>
            <div class="info-grid">
              <div class="info-item">
                <label>Name</label>
                <div>{{ campaign.name }}</div>
              </div>
              <div class="info-item">
                <label>Description</label>
                <div>{{ campaign.description || 'No description' }}</div>
              </div>
              <div class="info-item">
                <label>Status</label>
                <div>
                  <span class="status-badge" :class="campaign.status">
                    {{ campaign.status }}
                  </span>
                </div>
              </div>
              <div class="info-item">
                <label>Program</label>
                <div>{{ programName || 'No program' }}</div>
              </div>
              <div class="info-item">
                <label>Segment</label>
                <div>{{ segmentName || 'All Customers' }}</div>
              </div>
              <div class="info-item">
                <label>Start Date</label>
                <div>{{ formatDate(campaign.start_date) }}</div>
              </div>
              <div class="info-item">
                <label>End Date</label>
                <div>{{ formatDate(campaign.end_date) }}</div>
              </div>
              <div class="info-item">
                <label>Channels</label>
                <div>
                  <span v-for="channel in parsedChannels" :key="channel" class="channel-badge">
                    {{ channel }}
                  </span>
                  <span v-if="parsedChannels.length === 0">No channels</span>
                </div>
              </div>
              <div class="info-item">
                <label>Frequency Cap</label>
                <div>{{ campaign.frequency_cap }} per {{ campaign.frequency_period }}</div>
              </div>
              <div class="info-item">
                <label>Version</label>
                <div>{{ campaign.version }}</div>
              </div>
            </div>
          </div>

          <div class="section">
            <h2>Performance Overview</h2>
            <div class="analytics-grid">
              <ChartCard title="Campaign Funnel" subtitle="Conversion funnel">
                <BarChart
                  :data="funnelData"
                  x-key="stage"
                  :bars="[
                    { dataKey: 'count', name: 'Count', fill: '#2563eb' }
                  ]"
                />
              </ChartCard>

              <ChartCard title="Engagement Rate" subtitle="Opened vs Clicked">
                <PieChart
                  :data="engagementData"
                  data-key="value"
                  name-key="name"
                />
              </ChartCard>
            </div>
          </div>
        </div>

        <!-- Triggers Tab -->
        <div v-if="activeTab === 'triggers'" class="tab-panel">
          <div class="section">
            <h2>Event Triggers</h2>
            <div v-if="!parsedEventTriggers || parsedEventTriggers.length === 0" class="empty-state">
              No event triggers configured
            </div>
            <div v-else class="triggers-list">
              <div v-for="(trigger, idx) in parsedEventTriggers" :key="idx" class="trigger-card">
                <div class="trigger-header">
                  <h3>Event Trigger {{ idx + 1 }}</h3>
                  <span class="trigger-type">Event-based</span>
                </div>
                <div class="trigger-content">
                  <div class="trigger-field">
                    <label>Event Type:</label>
                    <span>{{ trigger.event_type || 'N/A' }}</span>
                  </div>
                  <div class="trigger-field" v-if="trigger.conditions">
                    <label>Conditions:</label>
                    <pre>{{ JSON.stringify(trigger.conditions, null, 2) }}</pre>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="section">
            <h2>Schedule Triggers</h2>
            <div v-if="!parsedScheduleTriggers || parsedScheduleTriggers.length === 0" class="empty-state">
              No schedule triggers configured
            </div>
            <div v-else class="triggers-list">
              <div v-for="(trigger, idx) in parsedScheduleTriggers" :key="idx" class="trigger-card">
                <div class="trigger-header">
                  <h3>Schedule Trigger {{ idx + 1 }}</h3>
                  <span class="trigger-type">Schedule-based</span>
                </div>
                <div class="trigger-content">
                  <div class="trigger-field">
                    <label>Cron Expression:</label>
                    <span>{{ trigger.cron || trigger.schedule || 'N/A' }}</span>
                  </div>
                  <div class="trigger-field" v-if="trigger.timezone">
                    <label>Timezone:</label>
                    <span>{{ trigger.timezone }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="section">
            <h2>Threshold Triggers</h2>
            <div v-if="!parsedThresholdTriggers || parsedThresholdTriggers.length === 0" class="empty-state">
              No threshold triggers configured
            </div>
            <div v-else class="triggers-list">
              <div v-for="(trigger, idx) in parsedThresholdTriggers" :key="idx" class="trigger-card">
                <div class="trigger-header">
                  <h3>Threshold Trigger {{ idx + 1 }}</h3>
                  <span class="trigger-type">Threshold-based</span>
                </div>
                <div class="trigger-content">
                  <div class="trigger-field">
                    <label>Metric:</label>
                    <span>{{ trigger.metric || 'N/A' }}</span>
                  </div>
                  <div class="trigger-field">
                    <label>Operator:</label>
                    <span>{{ trigger.operator || 'N/A' }}</span>
                  </div>
                  <div class="trigger-field">
                    <label>Value:</label>
                    <span>{{ trigger.value || 'N/A' }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Executions Tab -->
        <div v-if="activeTab === 'executions'" class="tab-panel">
          <div class="section">
            <div class="section-header">
              <h2>Campaign Executions</h2>
              <button @click="loadExecutions" class="btn-secondary">Refresh</button>
            </div>
            <div v-if="executions.length === 0" class="empty-state">
              No executions yet
            </div>
            <div v-else class="executions-table">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Customer ID</th>
                    <th>Channel</th>
                    <th>Triggered At</th>
                    <th>Delivered</th>
                    <th>Opened</th>
                    <th>Clicked</th>
                    <th>Converted</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="execution in executions.slice(0, 50)" :key="execution.id">
                    <td>{{ formatCustomerId(execution.customer_id) }}</td>
                    <td>{{ execution.channel }}</td>
                    <td>{{ formatDate(execution.triggered_at) }}</td>
                    <td>
                      <span v-if="execution.delivered_at" class="status-badge active">✓</span>
                      <span v-else class="status-badge inactive">-</span>
                    </td>
                    <td>
                      <span v-if="execution.opened_at" class="status-badge active">✓</span>
                      <span v-else class="status-badge inactive">-</span>
                    </td>
                    <td>
                      <span v-if="execution.clicked_at" class="status-badge active">✓</span>
                      <span v-else class="status-badge inactive">-</span>
                    </td>
                    <td>
                      <span v-if="execution.converted_at" class="status-badge active">✓</span>
                      <span v-else class="status-badge inactive">-</span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="executions.length > 50" class="more-executions">
                Showing first 50 of {{ executions.length }} executions
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <h2>Campaign not found</h2>
      <p>The campaign you're looking for doesn't exist or has been deleted.</p>
      <button @click="$router.push('/campaigns')" class="btn-primary">Back to Campaigns</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { campaignsApi } from '@/api/services/campaigns'
import { programsApi } from '@/api/services/programs'
import { segmentsApi } from '@/api/services/segments'
import type { Campaign, CampaignExecution } from '@/types/loyalty'
import ChartCard from '@/components/ChartCard.vue'
import BarChart from '@/components/BarChart.vue'
import PieChart from '@/components/PieChart.vue'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'

const route = useRoute()
const router = useRouter()

const campaign = ref<Campaign | null>(null)
const performance = ref<any>({})
const executions = ref<CampaignExecution[]>([])
const programName = ref('')
const segmentName = ref('')
const loading = ref(true)
const activeTab = ref('overview')

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'triggers', label: 'Triggers' },
  { id: 'executions', label: 'Executions' },
]

const parsedChannels = computed(() => {
  if (!campaign.value?.channels) return []
  if (Array.isArray(campaign.value.channels)) return campaign.value.channels
  try {
    return JSON.parse(campaign.value.channels)
  } catch {
    return []
  }
})

const parsedEventTriggers = computed(() => {
  if (!campaign.value?.event_triggers) return []
  if (Array.isArray(campaign.value.event_triggers)) return campaign.value.event_triggers
  try {
    return JSON.parse(campaign.value.event_triggers)
  } catch {
    return []
  }
})

const parsedScheduleTriggers = computed(() => {
  if (!campaign.value?.schedule_triggers) return []
  if (Array.isArray(campaign.value.schedule_triggers)) return campaign.value.schedule_triggers
  try {
    return JSON.parse(campaign.value.schedule_triggers)
  } catch {
    return []
  }
})

const parsedThresholdTriggers = computed(() => {
  if (!campaign.value?.threshold_triggers) return []
  if (Array.isArray(campaign.value.threshold_triggers)) return campaign.value.threshold_triggers
  try {
    return JSON.parse(campaign.value.threshold_triggers)
  } catch {
    return []
  }
})

const conversionRate = computed(() => {
  if (!performance.value.total_sent || performance.value.total_sent === 0) return 0
  return Math.round((performance.value.converted / performance.value.total_sent) * 100)
})

const funnelData = computed(() => {
  return [
    { stage: 'Sent', count: performance.value.total_sent || 0 },
    { stage: 'Delivered', count: performance.value.delivered || 0 },
    { stage: 'Opened', count: performance.value.opened || 0 },
    { stage: 'Clicked', count: performance.value.clicked || 0 },
    { stage: 'Converted', count: performance.value.converted || 0 },
  ]
})

const engagementData = computed(() => {
  const opened = performance.value.opened || 0
  const clicked = performance.value.clicked || 0
  const notClicked = opened - clicked
  return [
    { name: 'Clicked', value: clicked },
    { name: 'Opened (Not Clicked)', value: notClicked },
  ]
})

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('en-US').format(num)
}

const formatDate = (date: string | null | undefined) => {
  if (!date) return '-'
  try {
    return format(new Date(date), 'MMM dd, yyyy HH:mm')
  } catch {
    return '-'
  }
}

const formatCustomerId = (id: string) => {
  if (!id) return '-'
  return id.substring(0, 8) + '...'
}

const loadCampaign = async () => {
  loading.value = true
  try {
    const response = await campaignsApi.getById(route.params.id as string)
    campaign.value = response.data
    
    // Load program name
    if (campaign.value.program) {
      try {
        const programResponse = await programsApi.getById(campaign.value.program.toString())
        programName.value = programResponse.data.name
      } catch (error) {
        console.error('Error loading program:', error)
      }
    }
    
    // Load segment name
    if (campaign.value.segment) {
      try {
        const segmentResponse = await segmentsApi.getById(campaign.value.segment.toString())
        segmentName.value = segmentResponse.data.name
      } catch (error) {
        console.error('Error loading segment:', error)
      }
    }
    
    // Load performance
    try {
      const performanceResponse = await campaignsApi.getPerformance(route.params.id as string)
      performance.value = performanceResponse.data
    } catch (error) {
      console.error('Error loading performance:', error)
    }
    
    // Load executions
    await loadExecutions()
  } catch (error) {
    console.error('Error loading campaign:', error)
    campaign.value = null
  } finally {
    loading.value = false
  }
}

const loadExecutions = async () => {
  try {
    const response = await campaignsApi.getExecutions(route.params.id as string)
    executions.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading executions:', error)
    executions.value = []
  }
}

const editCampaign = () => {
  router.push({ name: 'campaign-builder', params: { id: route.params.id } })
}

const activateCampaign = async () => {
  if (!campaign.value) return
  
  try {
    await campaignsApi.activate(route.params.id as string)
    campaign.value.status = 'active'
    alert('Campaign activated successfully!')
    loadCampaign()
  } catch (error: any) {
    console.error('Error activating campaign:', error)
    alert('Error activating campaign: ' + (error.response?.data?.detail || error.message))
  }
}

const pauseCampaign = async () => {
  if (!campaign.value) return
  
  try {
    await campaignsApi.pause(route.params.id as string)
    campaign.value.status = 'paused'
    alert('Campaign paused successfully!')
    loadCampaign()
  } catch (error: any) {
    console.error('Error pausing campaign:', error)
    alert('Error pausing campaign: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadCampaign()
})
</script>

<style scoped>
.campaign-detail {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.loading {
  text-align: center;
  padding: 3rem;
  font-size: 1.125rem;
  color: #666;
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
  margin: 0 0 1rem 0;
}

.campaign-meta {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive,
.status-badge.paused {
  background: #fee2e2;
  color: #991b1b;
}

.status-badge.draft {
  background: #e5e7eb;
  color: #374151;
}

.status-badge.pending_review {
  background: #fef3c7;
  color: #92400e;
}

.meta-item {
  font-size: 0.875rem;
  color: #666;
}

.meta-item strong {
  color: #333;
  margin-right: 0.25rem;
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.kpi-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.kpi-label {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.kpi-value {
  font-size: 1.75rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.kpi-trend {
  font-size: 0.75rem;
  color: #666;
}

.trend-up {
  color: #059669;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #e0e0e0;
}

.tab-button {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: #2563eb;
}

.tab-button.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

.tab-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section {
  margin-bottom: 2rem;
}

.section:last-child {
  margin-bottom: 0;
}

.section h2 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 1rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.info-item {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
}

.info-item label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
  margin-bottom: 0.5rem;
}

.info-item div {
  font-size: 1rem;
  color: #1a1a1a;
}

.channel-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 4px;
  font-size: 0.875rem;
  margin-right: 0.5rem;
  margin-bottom: 0.25rem;
}

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

.triggers-list {
  display: grid;
  gap: 1rem;
}

.trigger-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.trigger-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.trigger-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.trigger-type {
  font-size: 0.875rem;
  color: #666;
  background: white;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
}

.trigger-content {
  display: grid;
  gap: 0.75rem;
}

.trigger-field {
  display: flex;
  flex-direction: column;
}

.trigger-field label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
  margin-bottom: 0.25rem;
}

.trigger-field span {
  font-size: 1rem;
  color: #1a1a1a;
}

.trigger-field pre {
  background: #1a1a1a;
  color: #00ff00;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  overflow-x: auto;
  margin: 0;
}

.executions-table {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f9fafb;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  border-bottom: 2px solid #e0e0e0;
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  font-size: 0.875rem;
  color: #1a1a1a;
}

.more-executions {
  padding: 1rem;
  text-align: center;
  color: #666;
  font-size: 0.875rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  background: #f9fafb;
  border-radius: 6px;
}

.error-state {
  text-align: center;
  padding: 3rem;
}

.error-state h2 {
  color: #dc2626;
  margin-bottom: 1rem;
}

.btn-primary, .btn-secondary {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}
</style>
