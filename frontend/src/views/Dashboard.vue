<template>
  <div class="dashboard">
    <!-- KPI Cards Grid -->
    <div class="kpi-grid">
      <div class="kpi-card" v-for="kpi in kpis" :key="kpi.label">
        <div class="kpi-header">
          <div class="kpi-icon" :style="{ background: kpi.iconBg }">
            <span v-html="kpi.icon"></span>
          </div>
          <div class="kpi-trend" :class="kpi.trend">
            <svg v-if="kpi.trend === 'up'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else-if="kpi.trend === 'down'" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="23 18 13.5 8.5 8.5 13.5 1 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="17 18 23 18 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <svg v-else viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
          </div>
        </div>
        <div class="kpi-content">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value">{{ kpi.value }}</div>
          <div class="kpi-description">{{ kpi.description }}</div>
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="charts-grid">
      <ChartCard title="Points Activity" subtitle="Last 7 days - Points earned vs redeemed">
        <LineChart
          v-if="pointsActivityData.length > 0"
          :data="pointsActivityData"
          x-key="date"
          :lines="[
            { dataKey: 'earned', name: 'Points Earned', stroke: '#10b981' },
            { dataKey: 'redeemed', name: 'Points Redeemed', stroke: '#ef4444' }
          ]"
          :x-formatter="(val) => formatDateShort(val)"
        />
        <div v-else class="chart-placeholder">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No data available</p>
        </div>
      </ChartCard>

      <ChartCard title="Program Performance" subtitle="Active programs overview">
        <BarChart
          v-if="programPerformanceData.length > 0"
          :data="programPerformanceData"
          x-key="name"
          :bars="[
            { dataKey: 'members', name: 'Members', fill: '#6366f1' },
            { dataKey: 'points', name: 'Points Issued', fill: '#10b981' }
          ]"
        />
        <div v-else class="chart-placeholder">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No program data available</p>
        </div>
      </ChartCard>

      <ChartCard title="Transaction Types" subtitle="Distribution this month">
        <PieChart
          v-if="transactionTypesData.length > 0"
          :data="transactionTypesData"
          data-key="value"
          name-key="name"
        />
        <div v-else class="chart-placeholder">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No transaction data available</p>
        </div>
      </ChartCard>

      <ChartCard title="Campaign Performance" subtitle="Active campaigns metrics">
        <BarChart
          v-if="campaignPerformanceData.length > 0"
          :data="campaignPerformanceData"
          x-key="name"
          :bars="[
            { dataKey: 'triggered', name: 'Triggered', fill: '#8b5cf6' },
            { dataKey: 'delivered', name: 'Delivered', fill: '#10b981' },
            { dataKey: 'converted', name: 'Converted', fill: '#6366f1' }
          ]"
        />
        <div v-else class="chart-placeholder">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No campaign data available</p>
        </div>
      </ChartCard>
    </div>

    <!-- Recent Activity -->
    <div class="activity-section">
      <div class="section-header">
        <div>
          <h2 class="section-title">Recent Activity</h2>
          <p class="section-subtitle">Latest transactions and events</p>
        </div>
        <button @click="refreshActivity" class="btn-secondary" :disabled="loading">
          <svg v-if="!loading" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>{{ loading ? 'Loading...' : 'Refresh' }}</span>
        </button>
      </div>
      <div class="activity-list">
        <div v-if="recentActivity.length === 0 && !loading" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No recent activity</p>
        </div>
        <div v-for="activity in recentActivity" :key="activity.id" class="activity-item">
          <div class="activity-icon" :class="`icon-${activity.type}`">
            <span v-html="getActivityIcon(activity.type)"></span>
          </div>
          <div class="activity-content">
            <div class="activity-title">{{ formatActivityTitle(activity) }}</div>
            <div class="activity-meta">
              <span class="activity-time">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ formatTimeAgo(activity.timestamp) }}
              </span>
              <span class="activity-customer" v-if="activity.customer_id">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ formatCustomerId(activity.customer_id) }}
              </span>
            </div>
          </div>
          <div class="activity-amount" v-if="activity.amount !== undefined">
            <span :class="getAmountClass(activity)">
              {{ formatActivityAmount(activity) }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { dashboardApi } from '@/api/services/dashboard'
import { analyticsApi } from '@/api/services/analytics'
import ChartCard from '@/components/ChartCard.vue'
import LineChart from '@/components/LineChart.vue'
import BarChart from '@/components/BarChart.vue'
import PieChart from '@/components/PieChart.vue'

const stats = ref({
  active_programs: 0,
  active_campaigns: 0,
  total_members: 0,
  points_issued_this_month: 0,
  points_redeemed_this_month: 0,
  recent_activity: [] as any[],
  campaign_performance: [] as any[]
})

// Store real analytics data
const programData = ref<any[]>([])
const campaignData = ref<any[]>([])
const segmentData = ref<any[]>([])
const transactionData = ref<any[]>([])

const loading = ref(false)

const kpis = computed(() => [
  {
    label: 'Active Programs',
    value: stats.value.active_programs || 0,
    description: 'Currently running',
    trend: stats.value.active_programs > 0 ? 'up' : 'neutral',
    icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 7h-4M4 7h4m0 0v12m0-12a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2m-8 0V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M4 7v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    iconBg: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
  },
  {
    label: 'Active Campaigns',
    value: stats.value.active_campaigns || 0,
    description: 'Running now',
    trend: stats.value.active_campaigns > 0 ? 'up' : 'neutral',
    icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    iconBg: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)'
  },
  {
    label: 'Total Members',
    value: formatNumber(stats.value.total_members || 0),
    description: 'Across all programs',
    trend: 'neutral',
    icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    iconBg: 'linear-gradient(135deg, #3b82f6 0%, #60a5fa 100%)'
  },
  {
    label: 'Points Issued',
    value: formatNumber(stats.value.points_issued_this_month || 0),
    description: 'This month',
    trend: 'up',
    icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    iconBg: 'linear-gradient(135deg, #10b981 0%, #34d399 100%)'
  },
  {
    label: 'Points Redeemed',
    value: formatNumber(stats.value.points_redeemed_this_month || 0),
    description: 'This month',
    trend: 'down',
    icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="23 18 13.5 8.5 8.5 13.5 1 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 18 23 18 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    iconBg: 'linear-gradient(135deg, #f59e0b 0%, #fbbf24 100%)'
  },
  {
    label: 'Net Points',
    value: formatNumber((stats.value.points_issued_this_month || 0) - (stats.value.points_redeemed_this_month || 0)),
    description: 'This month',
    trend: (stats.value.points_issued_this_month || 0) - (stats.value.points_redeemed_this_month || 0) >= 0 ? 'up' : 'down',
    icon: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><line x1="12" y1="2" x2="12" y2="22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="19 12 12 19 5 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    iconBg: 'linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%)'
  }
])

// Computed chart data - Points Activity (last 7 days)
const pointsActivityData = computed(() => {
  // If we have transaction data from analytics API, use it
  if (transactionData.value.length > 0) {
    return transactionData.value.slice(-7).map((t: any) => ({
      date: t.date,
      earned: t.earn_count || 0,
      redeemed: Math.abs(t.redeem_count || 0)
    }))
  }
  
  // Fallback: aggregate from recent activity
  const days = []
  const now = new Date()
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    
    const dayActivity = stats.value.recent_activity.filter((a: any) => {
      const activityDate = new Date(a.timestamp).toISOString().split('T')[0]
      return activityDate === dateStr
    })
    
    const earned = dayActivity
      .filter((a: any) => a.type === 'earn' || a.type === 'adjust')
      .reduce((sum: number, a: any) => sum + Math.abs(a.amount || 0), 0)
    
    const redeemed = dayActivity
      .filter((a: any) => a.type === 'redeem')
      .reduce((sum: number, a: any) => sum + Math.abs(a.amount || 0), 0)
    
    days.push({
      date: dateStr,
      earned,
      redeemed
    })
  }
  return days
})

// Program Performance - use real data from analytics API
const programPerformanceData = computed(() => {
  if (programData.value.length > 0) {
    return programData.value.map((p: any) => ({
      name: (p.program_name || 'Unknown').substring(0, 20),
      members: p.total_members || 0,
      points: p.points_issued || 0
    }))
  }
  return []
})

// Transaction Types - use real data
const transactionTypesData = computed(() => {
  // Aggregate transaction types from recent activity
  const types = new Map<string, number>()
  
  stats.value.recent_activity.forEach((activity: any) => {
    const type = activity.type || 'unknown'
    types.set(type, (types.get(type) || 0) + Math.abs(activity.amount || 0))
  })
  
  // Also add from transaction data if available
  if (transactionData.value.length > 0) {
    let earnTotal = 0
    let redeemTotal = 0
    transactionData.value.forEach((t: any) => {
      earnTotal += t.earn_count || 0
      redeemTotal += Math.abs(t.redeem_count || 0)
    })
    if (earnTotal > 0 || redeemTotal > 0) {
      types.set('earn', earnTotal)
      types.set('redeem', redeemTotal)
    }
  }
  
  return Array.from(types.entries())
    .filter(([_, value]) => value > 0)
    .map(([name, value]) => ({
      name: name.charAt(0).toUpperCase() + name.slice(1),
      value
    }))
})

// Campaign Performance - use real data from analytics API
const campaignPerformanceData = computed(() => {
  if (campaignData.value.length > 0) {
    return campaignData.value.slice(0, 5).map((c: any) => ({
      name: (c.campaign_name || 'Unknown').substring(0, 20),
      triggered: c.triggered || 0,
      delivered: c.delivered || 0,
      converted: c.converted || 0
    }))
  }
  // Fallback to stats if available
  if (stats.value.campaign_performance && Array.isArray(stats.value.campaign_performance)) {
    return stats.value.campaign_performance
  }
  return []
})

const recentActivity = computed(() => {
  return (stats.value.recent_activity || []).slice(0, 10)
})

const loadDashboardData = async () => {
  loading.value = true
  try {
    // Load dashboard stats and analytics data in parallel
    const [dashboardRes, programsRes, campaignsRes, transactionsRes] = await Promise.all([
      dashboardApi.getStats().catch(e => ({ data: {} })),
      analyticsApi.getProgramPerformance({ start_date: getLastWeekDate(), end_date: getTodayDate() }).catch(e => ({ data: [] })),
      analyticsApi.getCampaignPerformance({ start_date: getLastWeekDate(), end_date: getTodayDate() }).catch(e => ({ data: [] })),
      analyticsApi.getTransactionAnalytics({ start_date: getLastWeekDate(), end_date: getTodayDate() }).catch(e => ({ data: [] })),
    ])
    
    // Update stats
    stats.value = {
      ...stats.value,
      ...dashboardRes.data
    }
    
    // Update chart data from analytics API
    programData.value = Array.isArray(programsRes.data) ? programsRes.data : []
    campaignData.value = Array.isArray(campaignsRes.data) ? campaignsRes.data : []
    transactionData.value = Array.isArray(transactionsRes.data) ? transactionsRes.data : []
    
    console.log('Dashboard data loaded:', {
      stats: stats.value,
      programs: programData.value,
      campaigns: campaignData.value,
      transactions: transactionData.value
    })
  } catch (error) {
    console.error('Error loading dashboard data:', error)
  } finally {
    loading.value = false
  }
}

// Helper functions for date ranges
const getTodayDate = () => new Date().toISOString().split('T')[0]
const getLastWeekDate = () => {
  const date = new Date()
  date.setDate(date.getDate() - 7)
  return date.toISOString().split('T')[0]
}

const refreshActivity = () => {
  loadDashboardData()
}

// Formatting functions
const formatNumber = (num: number) => {
  return new Intl.NumberFormat('en-US').format(num)
}

const formatDateShort = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const formatTimeAgo = (timestamp: string) => {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return date.toLocaleDateString()
}

const formatActivityTitle = (activity: any) => {
  const type = activity.type || 'transaction'
  const amount = activity.amount || 0
  const program = activity.program_name || 'Program'
  
  if (type === 'earn') {
    return `Earned ${formatNumber(amount)} points in ${program}`
  } else if (type === 'redeem') {
    return `Redeemed ${formatNumber(Math.abs(amount))} points in ${program}`
  } else if (type === 'adjust') {
    return `Adjusted ${amount > 0 ? '+' : ''}${formatNumber(amount)} points in ${program}`
  }
  return `${type} in ${program}`
}

const formatCustomerId = (customerId: string) => {
  return customerId.substring(0, 8) + '...'
}

const getActivityIcon = (type: string) => {
  const icons: Record<string, string> = {
    earn: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    redeem: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M20 7h-4M4 7h4m0 0v12m0-12a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2m-8 0V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M4 7v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    adjust: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><path d="M12 1v6m0 6v6M5.64 5.64l4.24 4.24m4.24 4.24l4.24 4.24M1 12h6m6 0h6M5.64 18.36l4.24-4.24m4.24-4.24l4.24-4.24" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>',
    expire: '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
  }
  return icons[type] || '<svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/><polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
}

const getAmountClass = (activity: any) => {
  if (activity.type === 'redeem') return 'negative'
  if (activity.type === 'earn' || activity.type === 'adjust') return 'positive'
  return activity.amount > 0 ? 'positive' : 'negative'
}

const formatActivityAmount = (activity: any) => {
  const amount = Math.abs(activity.amount || 0)
  if (activity.type === 'redeem') {
    return `-${formatNumber(amount)}`
  }
  return `+${formatNumber(amount)}`
}

onMounted(() => {
  loadDashboardData()
})
</script>

<style scoped>
.dashboard {
  max-width: 1600px;
  margin: 0 auto;
}

/* KPI Cards */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-8);
}

.kpi-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.kpi-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: linear-gradient(90deg, var(--color-primary), var(--color-secondary));
}

.kpi-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.kpi-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
}

.kpi-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  color: white;
}

.kpi-icon svg {
  width: 24px;
  height: 24px;
}

.kpi-trend {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-md);
  background: var(--bg-tertiary);
}

.kpi-trend.up {
  color: var(--color-success);
  background: var(--color-success-bg);
}

.kpi-trend.down {
  color: var(--color-error);
  background: var(--color-error-bg);
}

.kpi-trend svg {
  width: 16px;
  height: 16px;
}

.kpi-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
}

.kpi-label {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  font-weight: var(--font-weight-medium);
}

.kpi-value {
  font-size: var(--font-size-3xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  line-height: var(--line-height-tight);
}

.kpi-description {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

/* Charts Grid */
.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-8);
}

.chart-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: var(--text-tertiary);
  gap: var(--spacing-3);
}

.chart-placeholder svg {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.chart-placeholder p {
  font-size: var(--font-size-sm);
  font-style: italic;
}

/* Activity Section */
.activity-section {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-6);
  gap: var(--spacing-4);
}

.section-title {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.section-subtitle {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin: 0;
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover:not(:disabled) {
  background: var(--color-gray-200);
  color: var(--text-primary);
  border-color: var(--border-color-dark);
}

.btn-secondary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary svg {
  width: 16px;
  height: 16px;
}

.activity-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.activity-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  padding: var(--spacing-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
  background: var(--bg-secondary);
}

.activity-item:hover {
  background: var(--bg-tertiary);
  border-color: var(--border-color-dark);
  box-shadow: var(--shadow-xs);
}

.activity-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  background: var(--bg-tertiary);
}

.activity-icon svg {
  width: 24px;
  height: 24px;
}

.icon-earn {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.icon-redeem {
  background: var(--color-warning-bg);
  color: var(--color-warning);
}

.icon-adjust {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.activity-content {
  flex: 1;
  min-width: 0;
}

.activity-title {
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
  margin-bottom: var(--spacing-2);
  line-height: var(--line-height-normal);
}

.activity-meta {
  display: flex;
  gap: var(--spacing-4);
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  flex-wrap: wrap;
}

.activity-meta svg {
  width: 14px;
  height: 14px;
  margin-right: var(--spacing-1);
  vertical-align: middle;
}

.activity-time,
.activity-customer {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
}

.activity-amount {
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-lg);
  flex-shrink: 0;
}

.positive {
  color: var(--color-success);
}

.negative {
  color: var(--color-error);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  color: var(--text-tertiary);
  gap: var(--spacing-3);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.empty-state p {
  font-size: var(--font-size-base);
  font-style: italic;
}

/* Responsive */
@media (max-width: 1400px) {
  .charts-grid {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 1100px) {
  .charts-grid {
    grid-template-columns: 1fr;
  }
  
  .kpi-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .kpi-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .kpi-grid {
    grid-template-columns: 1fr;
  }
  
  .section-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .activity-item {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--spacing-3);
  }
  
  .activity-amount {
    align-self: flex-end;
  }
}
</style>
