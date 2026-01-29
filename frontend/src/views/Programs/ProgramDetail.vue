<template>
  <div class="program-detail">
    <div v-if="loading" class="loading">Loading program...</div>
    
    <div v-else-if="program" class="program-content">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <h1>{{ program.name }}</h1>
          <p class="subtitle">{{ program.description || 'No description' }}</p>
          <div class="program-meta">
            <span class="status-badge" :class="program.is_active ? 'active' : 'inactive'">
              {{ program.is_active ? 'Active' : 'Inactive' }}
            </span>
            <span class="meta-item">
              <strong>Start:</strong> {{ formatDate(program.start_date) }}
            </span>
            <span class="meta-item">
              <strong>End:</strong> {{ formatDate(program.end_date) }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="editProgram" class="btn-secondary">Edit Program</button>
          <button @click="toggleActive" class="btn-primary">
            {{ program.is_active ? 'Deactivate' : 'Activate' }}
          </button>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Total Members</div>
          <div class="kpi-value">{{ analytics.total_members || 0 }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> Active Accounts
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Points Issued</div>
          <div class="kpi-value">{{ formatNumber(analytics.total_points_issued || 0) }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> All Time
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Points Redeemed</div>
          <div class="kpi-value">{{ formatNumber(analytics.total_points_redeemed || 0) }}</div>
          <div class="kpi-trend">
            <span class="trend-down">↓</span> All Time
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Net Points</div>
          <div class="kpi-value">{{ formatNumber((analytics.total_points_issued || 0) - (analytics.total_points_redeemed || 0)) }}</div>
          <div class="kpi-trend">
            <span :class="(analytics.total_points_issued || 0) - (analytics.total_points_redeemed || 0) >= 0 ? 'trend-up' : 'trend-down'">
              {{ (analytics.total_points_issued || 0) - (analytics.total_points_redeemed || 0) >= 0 ? '↑' : '↓' }}
            </span>
            Outstanding
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Avg Points/Member</div>
          <div class="kpi-value">{{ formatNumber(analytics.avg_points_per_member || 0) }}</div>
          <div class="kpi-trend">
            <span class="trend-neutral">→</span> Average
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Recent Activity (30d)</div>
          <div class="kpi-value">{{ formatNumber(analytics.recent_transactions || 0) }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> Transactions
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
            <h2>Program Information</h2>
            <div class="info-grid">
              <div class="info-item">
                <label>Name</label>
                <div>{{ program.name }}</div>
              </div>
              <div class="info-item">
                <label>Description</label>
                <div>{{ program.description || 'No description' }}</div>
              </div>
              <div class="info-item">
                <label>Status</label>
                <div>
                  <span class="status-badge" :class="program.is_active ? 'active' : 'inactive'">
                    {{ program.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
              </div>
              <div class="info-item">
                <label>Start Date</label>
                <div>{{ formatDate(program.start_date) }}</div>
              </div>
              <div class="info-item">
                <label>End Date</label>
                <div>{{ formatDate(program.end_date) }}</div>
              </div>
              <div class="info-item">
                <label>Created</label>
                <div>{{ formatDate(program.created_at) }}</div>
              </div>
            </div>
          </div>

          <div class="section">
            <h2>Tier Distribution</h2>
            <div v-if="Object.keys(analytics.tier_distribution || {}).length === 0" class="empty-state">
              No tiers configured
            </div>
            <div v-else class="tier-distribution">
              <ChartCard title="Members by Tier">
                <PieChart
                  :data="tierDistributionData"
                  data-key="value"
                  name-key="name"
                />
              </ChartCard>
            </div>
          </div>
        </div>

        <!-- Tiers Tab -->
        <div v-if="activeTab === 'tiers'" class="tab-panel">
          <div class="section">
            <div class="section-header">
              <h2>Program Tiers</h2>
              <button @click="editProgram" class="btn-secondary">Edit Tiers</button>
            </div>
            <div v-if="!program.tiers || program.tiers.length === 0" class="empty-state">
              No tiers configured. Add tiers in the Program Builder.
            </div>
            <div v-else class="tiers-list">
              <div v-for="tier in sortedTiers" :key="tier.id" class="tier-card">
                <div class="tier-header">
                  <h3>{{ tier.name }}</h3>
                  <span class="tier-priority">Priority: {{ tier.priority }}</span>
                </div>
                <div class="tier-content">
                  <p>{{ tier.description || 'No description' }}</p>
                  <div class="tier-stats">
                    <div class="stat">
                      <span class="stat-label">Min Points:</span>
                      <span class="stat-value">{{ formatNumber(tier.min_points) }}</span>
                    </div>
                    <div class="stat">
                      <span class="stat-label">Members:</span>
                      <span class="stat-value">{{ analytics.tier_distribution?.[tier.name] || 0 }}</span>
                    </div>
                  </div>
                  <div v-if="tier.benefits" class="tier-benefits">
                    <strong>Benefits:</strong> {{ tier.benefits }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Analytics Tab -->
        <div v-if="activeTab === 'analytics'" class="tab-panel">
          <div class="section">
            <h2>Program Performance</h2>
            <div class="analytics-grid">
              <ChartCard title="Points Activity" subtitle="Issued vs Redeemed">
                <BarChart
                  :data="pointsActivityData"
                  x-key="period"
                  :bars="[
                    { dataKey: 'issued', name: 'Issued', fill: '#00C49F' },
                    { dataKey: 'redeemed', name: 'Redeemed', fill: '#FF8042' }
                  ]"
                />
              </ChartCard>

              <ChartCard title="Tier Distribution" subtitle="Members by tier">
                <PieChart
                  :data="tierDistributionData"
                  data-key="value"
                  name-key="name"
                />
              </ChartCard>
            </div>
          </div>
        </div>

        <!-- Rules Tab -->
        <div v-if="activeTab === 'rules'" class="tab-panel">
          <div class="section">
            <h2>Earn Rules</h2>
            <div v-if="!program.earn_rules || Object.keys(parsedEarnRules).length === 0" class="empty-state">
              No earn rules configured
            </div>
            <div v-else class="rules-display">
              <pre>{{ JSON.stringify(parsedEarnRules, null, 2) }}</pre>
            </div>
          </div>

          <div class="section">
            <h2>Burn Rules</h2>
            <div v-if="!program.burn_rules || Object.keys(parsedBurnRules).length === 0" class="empty-state">
              No burn rules configured
            </div>
            <div v-else class="rules-display">
              <pre>{{ JSON.stringify(parsedBurnRules, null, 2) }}</pre>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <h2>Program not found</h2>
      <p>The program you're looking for doesn't exist or has been deleted.</p>
      <button @click="$router.push('/programs')" class="btn-primary">Back to Programs</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { programsApi } from '@/api/services/programs'
import type { LoyaltyProgram, LoyaltyTier } from '@/types/loyalty'
import ChartCard from '@/components/ChartCard.vue'
import BarChart from '@/components/BarChart.vue'
import PieChart from '@/components/PieChart.vue'
import { format } from 'date-fns'

const route = useRoute()
const router = useRouter()

const program = ref<LoyaltyProgram | null>(null)
const analytics = ref<any>({})
const loading = ref(true)
const activeTab = ref('overview')

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'tiers', label: 'Tiers' },
  { id: 'analytics', label: 'Analytics' },
  { id: 'rules', label: 'Rules' },
]

const sortedTiers = computed(() => {
  if (!program.value?.tiers) return []
  return [...program.value.tiers].sort((a, b) => (a.priority || 0) - (b.priority || 0))
})

const parsedEarnRules = computed(() => {
  if (!program.value?.earn_rules) return {}
  if (typeof program.value.earn_rules === 'string') {
    try {
      return JSON.parse(program.value.earn_rules)
    } catch {
      return {}
    }
  }
  return program.value.earn_rules
})

const parsedBurnRules = computed(() => {
  if (!program.value?.burn_rules) return {}
  if (typeof program.value.burn_rules === 'string') {
    try {
      return JSON.parse(program.value.burn_rules)
    } catch {
      return {}
    }
  }
  return program.value.burn_rules
})

const tierDistributionData = computed(() => {
  const distribution = analytics.value.tier_distribution || {}
  return Object.entries(distribution).map(([name, value]) => ({
    name,
    value: value as number
  }))
})

const pointsActivityData = computed(() => {
  // Mock data for now - would need time-series endpoint
  return [
    { period: 'This Month', issued: analytics.value.total_points_issued || 0, redeemed: analytics.value.total_points_redeemed || 0 },
    { period: 'Last Month', issued: Math.floor((analytics.value.total_points_issued || 0) * 0.8), redeemed: Math.floor((analytics.value.total_points_redeemed || 0) * 0.8) },
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

const loadProgram = async () => {
  loading.value = true
  try {
    const response = await programsApi.getById(route.params.id as string)
    program.value = response.data
    
    // Load analytics
    try {
      const analyticsResponse = await programsApi.getAnalytics(route.params.id as string)
      analytics.value = analyticsResponse.data
    } catch (error) {
      console.error('Error loading analytics:', error)
    }
  } catch (error) {
    console.error('Error loading program:', error)
    program.value = null
  } finally {
    loading.value = false
  }
}

const editProgram = () => {
  router.push({ name: 'program-builder', params: { id: route.params.id } })
}

const toggleActive = async () => {
  if (!program.value) return
  
  try {
    await programsApi.update(route.params.id as string, {
      is_active: !program.value.is_active
    })
    program.value.is_active = !program.value.is_active
    alert(`Program ${program.value.is_active ? 'activated' : 'deactivated'} successfully!`)
  } catch (error: any) {
    console.error('Error toggling program status:', error)
    alert('Error updating program status: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadProgram()
})
</script>

<style scoped>
.program-detail {
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

.program-meta {
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

.tier-distribution {
  margin-top: 1rem;
}

.tiers-list {
  display: grid;
  gap: 1rem;
}

.tier-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.tier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.tier-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.tier-priority {
  font-size: 0.875rem;
  color: #666;
  background: white;
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
}

.tier-content p {
  color: #666;
  margin-bottom: 1rem;
}

.tier-stats {
  display: flex;
  gap: 2rem;
  margin-bottom: 1rem;
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

.tier-benefits {
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  font-size: 0.875rem;
  color: #666;
}

.rules-display {
  background: #1a1a1a;
  color: #00ff00;
  padding: 1.5rem;
  border-radius: 6px;
  overflow-x: auto;
}

.rules-display pre {
  margin: 0;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
}

.analytics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
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
