<template>
  <div class="experiment-detail">
    <div v-if="loading" class="loading">Loading experiment...</div>
    
    <div v-else-if="experiment" class="experiment-content">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <h1>{{ experiment.name }}</h1>
          <p class="subtitle">{{ experiment.description || 'No description' }}</p>
          <div class="experiment-meta">
            <span class="status-badge" :class="experiment.status">{{ experiment.status }}</span>
            <span class="meta-item">
              <strong>Start:</strong> {{ formatDate(experiment.start_date) }}
            </span>
            <span class="meta-item">
              <strong>End:</strong> {{ formatDate(experiment.end_date) }}
            </span>
            <span class="meta-item" v-if="experiment.campaign">
              <strong>Campaign:</strong> {{ campaignName }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="editExperiment" class="btn-secondary">Edit Experiment</button>
          <button 
            v-if="experiment.status === 'draft'"
            @click="startExperiment" 
            class="btn-primary"
          >
            Start Experiment
          </button>
          <button 
            v-if="experiment.status === 'running'"
            @click="stopExperiment" 
            class="btn-secondary"
          >
            Stop Experiment
          </button>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Total Assignments</div>
          <div class="kpi-value">{{ results.total_assignments || 0 }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> Participants
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Variants</div>
          <div class="kpi-value">{{ variantCount }}</div>
          <div class="kpi-trend">
            <span class="trend-neutral">→</span> Test Groups
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Holdout Group</div>
          <div class="kpi-value">{{ holdoutCount }}</div>
          <div class="kpi-trend">
            <span class="trend-neutral">→</span> Control
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Conversion Rate</div>
          <div class="kpi-value">{{ overallConversionRate }}%</div>
          <div class="kpi-trend">
            <span :class="overallConversionRate >= 10 ? 'trend-up' : 'trend-down'">
              {{ overallConversionRate >= 10 ? '↑' : '↓' }}
            </span>
            Overall
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
            <h2>Experiment Information</h2>
            <div class="info-grid">
              <div class="info-item">
                <label>Name</label>
                <div>{{ experiment.name }}</div>
              </div>
              <div class="info-item">
                <label>Description</label>
                <div>{{ experiment.description || 'No description' }}</div>
              </div>
              <div class="info-item">
                <label>Status</label>
                <div>
                  <span class="status-badge" :class="experiment.status">
                    {{ experiment.status }}
                  </span>
                </div>
              </div>
              <div class="info-item">
                <label>Start Date</label>
                <div>{{ formatDate(experiment.start_date) }}</div>
              </div>
              <div class="info-item">
                <label>End Date</label>
                <div>{{ formatDate(experiment.end_date) }}</div>
              </div>
              <div class="info-item">
                <label>Campaign</label>
                <div>{{ campaignName || 'No campaign' }}</div>
              </div>
              <div class="info-item">
                <label>Traffic Split</label>
                <div>{{ trafficSplit }}</div>
              </div>
              <div class="info-item">
                <label>Created</label>
                <div>{{ formatDate(experiment.created_at) }}</div>
              </div>
            </div>
          </div>

          <div class="section">
            <h2>Variants</h2>
            <div v-if="!parsedVariants || parsedVariants.length === 0" class="empty-state">
              No variants configured
            </div>
            <div v-else class="variants-list">
              <div v-for="(variant, idx) in parsedVariants" :key="idx" class="variant-card">
                <div class="variant-header">
                  <h3>{{ variant.name || `Variant ${idx + 1}` }}</h3>
                  <span class="variant-traffic">{{ variant.traffic_percentage || 0 }}%</span>
                </div>
                <div class="variant-content">
                  <p v-if="variant.description">{{ variant.description }}</p>
                  <div class="variant-stats">
                    <div class="stat">
                      <span class="stat-label">Assignments:</span>
                      <span class="stat-value">{{ variantCounts[variant.name] || 0 }}</span>
                    </div>
                    <div class="stat">
                      <span class="stat-label">Conversions:</span>
                      <span class="stat-value">{{ variantConversions[variant.name] || 0 }}</span>
                    </div>
                    <div class="stat">
                      <span class="stat-label">Conversion Rate:</span>
                      <span class="stat-value">
                        {{ getVariantConversionRate(variant.name) }}%
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Results Tab -->
        <div v-if="activeTab === 'results'" class="tab-panel">
          <div class="section">
            <h2>Experiment Results</h2>
            <div class="results-summary">
              <div class="summary-card">
                <h3>Overall Performance</h3>
                <div class="summary-stats">
                  <div class="summary-stat">
                    <span class="stat-label">Total Participants</span>
                    <span class="stat-value">{{ results.total_assignments || 0 }}</span>
                  </div>
                  <div class="summary-stat">
                    <span class="stat-label">Total Conversions</span>
                    <span class="stat-value">{{ totalConversions }}</span>
                  </div>
                  <div class="summary-stat">
                    <span class="stat-label">Overall Conversion Rate</span>
                    <span class="stat-value">{{ overallConversionRate }}%</span>
                  </div>
                </div>
              </div>
            </div>

            <ChartCard title="Variant Performance" subtitle="Assignments and conversions by variant">
              <BarChart
                v-if="variantChartData.length > 0"
                :data="variantChartData"
                x-key="variant"
                :bars="[
                  { dataKey: 'assignments', name: 'Assignments', fill: '#2563eb' },
                  { dataKey: 'conversions', name: 'Conversions', fill: '#00C49F' }
                ]"
              />
              <div v-else class="chart-placeholder">No variant data available</div>
            </ChartCard>

            <ChartCard title="Conversion Rates by Variant" subtitle="Percentage conversion">
              <BarChart
                v-if="conversionRateData.length > 0"
                :data="conversionRateData"
                x-key="variant"
                :bars="[
                  { dataKey: 'rate', name: 'Conversion Rate %', fill: '#8884d8' }
                ]"
              />
              <div v-else class="chart-placeholder">No conversion data available</div>
            </ChartCard>
          </div>
        </div>

        <!-- Assignments Tab -->
        <div v-if="activeTab === 'assignments'" class="tab-panel">
          <div class="section">
            <div class="section-header">
              <h2>Experiment Assignments</h2>
              <div class="section-actions">
                <input 
                  v-model="assignmentSearch" 
                  placeholder="Search customer ID..."
                  class="search-input"
                />
                <button @click="loadAssignments" class="btn-secondary">Refresh</button>
              </div>
            </div>
            <div v-if="assignments.length === 0" class="empty-state">
              No assignments yet
            </div>
            <div v-else class="assignments-table">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Customer ID</th>
                    <th>Variant</th>
                    <th>Assigned At</th>
                    <th>Converted</th>
                    <th>Conversion Date</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="assignment in filteredAssignments" :key="assignment.id">
                    <td>{{ formatCustomerId(assignment.customer_id) }}</td>
                    <td>
                      <span class="variant-badge">{{ assignment.variant }}</span>
                    </td>
                    <td>{{ formatDate(assignment.assigned_at) }}</td>
                    <td>
                      <span class="status-badge" :class="assignment.converted ? 'active' : 'inactive'">
                        {{ assignment.converted ? 'Yes' : 'No' }}
                      </span>
                    </td>
                    <td>{{ formatDate(assignment.converted_at) || '-' }}</td>
                  </tr>
                </tbody>
              </table>
              <div v-if="filteredAssignments.length > 100" class="more-assignments">
                Showing first 100 of {{ filteredAssignments.length }} assignments
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <h2>Experiment not found</h2>
      <p>The experiment you're looking for doesn't exist or has been deleted.</p>
      <button @click="$router.push('/experiments')" class="btn-primary">Back to Experiments</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { experimentsApi } from '@/api/services/experiments'
import { campaignsApi } from '@/api/services/campaigns'
import ChartCard from '@/components/ChartCard.vue'
import BarChart from '@/components/BarChart.vue'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'

const route = useRoute()
const router = useRouter()

const experiment = ref<any>(null)
const results = ref<any>({})
const assignments = ref<any[]>([])
const campaignName = ref('')
const loading = ref(true)
const activeTab = ref('overview')
const assignmentSearch = ref('')

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'results', label: 'Results' },
  { id: 'assignments', label: 'Assignments' },
]

const parsedVariants = computed(() => {
  if (!experiment.value?.variants) return []
  if (Array.isArray(experiment.value.variants)) return experiment.value.variants
  try {
    return JSON.parse(experiment.value.variants)
  } catch {
    return []
  }
})

const variantCount = computed(() => {
  return parsedVariants.value.length
})

const holdoutCount = computed(() => {
  // TODO: Get from holdout groups
  return 0
})

const variantCounts = computed(() => {
  return results.value.variant_counts || {}
})

const variantConversions = computed(() => {
  // Calculate from results
  return results.value.variant_conversions || {}
})

const totalConversions = computed(() => {
  return Object.values(variantConversions.value).reduce((sum: number, val: any) => sum + (val || 0), 0)
})

const overallConversionRate = computed(() => {
  const total = results.value.total_assignments || 0
  if (total === 0) return 0
  return Math.round((totalConversions.value / total) * 100)
})

const trafficSplit = computed(() => {
  const variants = parsedVariants.value
  if (variants.length === 0) return 'N/A'
  return variants.map((v: any) => `${v.name}: ${v.traffic_percentage || 0}%`).join(', ')
})

const variantChartData = computed(() => {
  const variants = parsedVariants.value
  return variants.map((v: any) => ({
    variant: v.name || 'Unknown',
    assignments: variantCounts.value[v.name] || 0,
    conversions: variantConversions.value[v.name] || 0
  }))
})

const conversionRateData = computed(() => {
  const variants = parsedVariants.value
  return variants.map((v: any) => ({
    variant: v.name || 'Unknown',
    rate: getVariantConversionRate(v.name)
  }))
})

const filteredAssignments = computed(() => {
  let filtered = assignments.value
  
  if (assignmentSearch.value) {
    const search = assignmentSearch.value.toLowerCase()
    filtered = filtered.filter(a => 
      a.customer_id?.toLowerCase().includes(search) ||
      a.variant?.toLowerCase().includes(search)
    )
  }
  
  return filtered.slice(0, 100) // Limit to first 100 for performance
})

const getVariantConversionRate = (variantName: string) => {
  const assignments = variantCounts.value[variantName] || 0
  const conversions = variantConversions.value[variantName] || 0
  if (assignments === 0) return 0
  return Math.round((conversions / assignments) * 100)
}

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

const loadExperiment = async () => {
  loading.value = true
  try {
    const response = await experimentsApi.getById(route.params.id as string)
    experiment.value = response.data
    
    // Load campaign name
    if (experiment.value.campaign) {
      try {
        const campaignResponse = await campaignsApi.getById(experiment.value.campaign.toString())
        campaignName.value = campaignResponse.data.name
      } catch (error) {
        console.error('Error loading campaign:', error)
      }
    }
    
    // Load results and assignments
    await Promise.all([
      loadResults(),
      loadAssignments()
    ])
  } catch (error) {
    console.error('Error loading experiment:', error)
    experiment.value = null
  } finally {
    loading.value = false
  }
}

const loadResults = async () => {
  try {
    const response = await experimentsApi.getResults(route.params.id as string)
    results.value = response.data
  } catch (error) {
    console.error('Error loading results:', error)
    results.value = {}
  }
}

const loadAssignments = async () => {
  try {
    const response = await experimentsApi.getAssignments(route.params.id as string)
    assignments.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading assignments:', error)
    assignments.value = []
  }
}

const editExperiment = () => {
  // TODO: Navigate to experiment builder
  console.log('Edit experiment:', route.params.id)
}

const startExperiment = async () => {
  try {
    await experimentsApi.start(route.params.id as string)
    alert('Experiment started successfully!')
    await loadExperiment()
  } catch (error: any) {
    console.error('Error starting experiment:', error)
    alert('Error starting experiment: ' + (error.response?.data?.error || error.message))
  }
}

const stopExperiment = async () => {
  try {
    await experimentsApi.stop(route.params.id as string)
    alert('Experiment stopped successfully!')
    await loadExperiment()
  } catch (error: any) {
    console.error('Error stopping experiment:', error)
    alert('Error stopping experiment: ' + (error.response?.data?.error || error.message))
  }
}

onMounted(() => {
  loadExperiment()
})
</script>

<style scoped>
.experiment-detail {
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

.experiment-meta {
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

.status-badge.running {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.draft {
  background: #e5e7eb;
  color: #374151;
}

.status-badge.completed {
  background: #dbeafe;
  color: #1e40af;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #991b1b;
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

.trend-down {
  color: #dc2626;
}

.trend-neutral {
  color: #666;
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

.section-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.search-input {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
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

.variants-list {
  display: grid;
  gap: 1rem;
}

.variant-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.variant-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.variant-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.variant-traffic {
  font-size: 0.875rem;
  color: #666;
  background: white;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
}

.variant-content p {
  color: #666;
  margin-bottom: 1rem;
}

.variant-stats {
  display: flex;
  gap: 2rem;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
}

.results-summary {
  margin-bottom: 2rem;
}

.summary-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.summary-card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.summary-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.summary-stat {
  display: flex;
  flex-direction: column;
}

.assignments-table {
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

.variant-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 4px;
  font-size: 0.875rem;
}

.more-assignments {
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

.chart-placeholder {
  padding: 2rem;
  text-align: center;
  color: #666;
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

