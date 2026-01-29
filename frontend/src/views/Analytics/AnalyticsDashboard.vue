<template>
  <div class="analytics-dashboard">
    <div class="page-header">
      <div class="header-left">
        <h1>Analytics & Optimization</h1>
        <p class="subtitle">Comprehensive analytics for programs, campaigns, and customer behavior</p>
      </div>
      <div class="header-actions">
        <select v-model="timeRange" @change="loadAnalytics" class="time-range-select">
          <option value="7d">Last 7 Days</option>
          <option value="30d">Last 30 Days</option>
          <option value="90d">Last 90 Days</option>
          <option value="1y">Last Year</option>
          <option value="custom">Custom Range</option>
        </select>
        <button @click="exportReport" class="btn-secondary">Export Report</button>
      </div>
    </div>

    <!-- Custom Date Range -->
    <div v-if="timeRange === 'custom'" class="section custom-range">
      <div class="form-row">
        <div class="form-group">
          <label>Start Date</label>
          <input v-model="customStartDate" type="date" />
        </div>
        <div class="form-group">
          <label>End Date</label>
          <input v-model="customEndDate" type="date" />
        </div>
        <div class="form-group">
          <label>&nbsp;</label>
          <button @click="applyCustomRange" class="btn-primary">Apply</button>
        </div>
      </div>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-grid">
      <div class="kpi-card">
        <div class="kpi-label">Total Revenue</div>
        <div class="kpi-value">${{ formatNumber(revenueStats.total || 0) }}</div>
        <div class="kpi-trend" :class="revenueStats.trend || 'neutral'">
          <span>{{ getTrendIcon(revenueStats.trend) }}</span>
          {{ revenueStats.change || 0 }}% vs previous period
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Active Programs</div>
        <div class="kpi-value">{{ programStats.active || 0 }}</div>
        <div class="kpi-trend">
          <span>→</span> {{ programStats.total || 0 }} total
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Campaign Conversion</div>
        <div class="kpi-value">{{ formatNumber(campaignStats.avgConversion || 0) }}%</div>
        <div class="kpi-trend" :class="campaignStats.trend || 'neutral'">
          <span>{{ getTrendIcon(campaignStats.trend) }}</span>
          {{ campaignStats.total || 0 }} campaigns
        </div>
      </div>
      <div class="kpi-card">
        <div class="kpi-label">Segment Growth</div>
        <div class="kpi-value">{{ formatNumber(segmentStats.avgGrowth || 0) }}%</div>
        <div class="kpi-trend">
          <span>→</span> {{ segmentStats.total || 0 }} segments
        </div>
      </div>
    </div>

    <!-- Charts Grid -->
    <div class="charts-grid">
      <!-- Program Performance -->
      <ChartCard title="Program Performance" subtitle="Points issued vs redeemed by program">
        <BarChart
          v-if="programPerformanceData.length > 0"
          :data="programPerformanceData"
          x-key="name"
          :bars="[
            { dataKey: 'points_issued', name: 'Points Issued', fill: '#00C49F' },
            { dataKey: 'points_redeemed', name: 'Points Redeemed', fill: '#FF8042' }
          ]"
        />
        <div v-else class="chart-placeholder">No program data available</div>
      </ChartCard>

      <!-- Campaign Performance -->
      <ChartCard title="Campaign Performance" subtitle="Conversion rates by campaign">
        <BarChart
          v-if="campaignPerformanceData.length > 0"
          :data="campaignPerformanceData"
          x-key="name"
          :bars="[
            { dataKey: 'triggered', name: 'Triggered', fill: '#8884d8' },
            { dataKey: 'delivered', name: 'Delivered', fill: '#82ca9d' },
            { dataKey: 'converted', name: 'Converted', fill: '#00C49F' }
          ]"
        />
        <div v-else class="chart-placeholder">No campaign data available</div>
      </ChartCard>

      <!-- Transaction Trends -->
      <ChartCard title="Transaction Trends" subtitle="Daily transaction volume">
        <LineChart
          v-if="transactionTrendsData.length > 0"
          :data="transactionTrendsData"
          x-key="date"
          :lines="[
            { dataKey: 'earn_count', name: 'Earn', stroke: '#00C49F' },
            { dataKey: 'redeem_count', name: 'Redeem', stroke: '#FF8042' }
          ]"
          :x-formatter="(val) => formatDateShort(val)"
        />
        <div v-else class="chart-placeholder">No transaction data available</div>
      </ChartCard>

      <!-- Revenue Trends -->
      <ChartCard title="Revenue Trends" subtitle="Revenue over time">
        <LineChart
          v-if="revenueTrendsData.length > 0"
          :data="revenueTrendsData"
          x-key="date"
          :lines="[
            { dataKey: 'revenue', name: 'Revenue', stroke: '#2563eb' }
          ]"
          :x-formatter="(val) => formatDateShort(val)"
        />
        <div v-else class="chart-placeholder">No revenue data available</div>
      </ChartCard>

      <!-- Segment Distribution -->
      <ChartCard title="Segment Distribution" subtitle="Members by segment">
        <PieChart
          v-if="segmentDistributionData.length > 0"
          :data="segmentDistributionData"
          data-key="value"
          name-key="name"
        />
        <div v-else class="chart-placeholder">No segment data available</div>
      </ChartCard>

      <!-- Campaign Conversion Funnel -->
      <ChartCard title="Campaign Funnel" subtitle="Average conversion funnel">
        <BarChart
          v-if="funnelData.length > 0"
          :data="funnelData"
          x-key="stage"
          :bars="[
            { dataKey: 'value', name: 'Count', fill: '#2563eb' }
          ]"
        />
        <div v-else class="chart-placeholder">No funnel data available</div>
      </ChartCard>
    </div>

    <!-- Detailed Tables -->
    <div class="tables-grid">
      <!-- Top Programs -->
      <div class="section">
        <h2>Top Performing Programs</h2>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Program</th>
                <th>Members</th>
                <th>Points Issued</th>
                <th>Points Redeemed</th>
                <th>Revenue</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="program in topPrograms" :key="program.program_id">
                <td>{{ program.program_name }}</td>
                <td>{{ formatNumber(program.total_members) }}</td>
                <td>{{ formatNumber(program.points_issued) }}</td>
                <td>{{ formatNumber(program.points_redeemed) }}</td>
                <td>${{ formatNumber(program.revenue || 0) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Top Campaigns -->
      <div class="section">
        <h2>Top Performing Campaigns</h2>
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Campaign</th>
                <th>Triggered</th>
                <th>Delivered</th>
                <th>Converted</th>
                <th>Conversion Rate</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="campaign in topCampaigns" :key="campaign.campaign_id">
                <td>{{ campaign.campaign_name }}</td>
                <td>{{ formatNumber(campaign.triggered) }}</td>
                <td>{{ formatNumber(campaign.delivered) }}</td>
                <td>{{ formatNumber(campaign.converted) }}</td>
                <td>{{ formatNumber(campaign.conversion_rate || 0) }}%</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { analyticsApi } from '@/api/services/analytics'
import ChartCard from '@/components/ChartCard.vue'
import LineChart from '@/components/LineChart.vue'
import BarChart from '@/components/BarChart.vue'
import PieChart from '@/components/PieChart.vue'

const timeRange = ref('30d')
const customStartDate = ref('')
const customEndDate = ref('')

const loading = ref(false)

// Stats
const revenueStats = ref({ total: 0, trend: 'neutral', change: 0 })
const programStats = ref({ active: 0, total: 0 })
const campaignStats = ref({ avgConversion: 0, total: 0, trend: 'neutral' })
const segmentStats = ref({ avgGrowth: 0, total: 0 })

// Chart Data
const programPerformanceData = ref<any[]>([])
const campaignPerformanceData = ref<any[]>([])
const transactionTrendsData = ref<any[]>([])
const revenueTrendsData = ref<any[]>([])
const segmentDistributionData = ref<any[]>([])
const funnelData = ref<any[]>([])

// Table Data
const topPrograms = ref<any[]>([])
const topCampaigns = ref<any[]>([])

const getTimeRangeDates = () => {
  const end = new Date()
  const start = new Date()
  
  switch (timeRange.value) {
    case '7d':
      start.setDate(end.getDate() - 7)
      break
    case '30d':
      start.setDate(end.getDate() - 30)
      break
    case '90d':
      start.setDate(end.getDate() - 90)
      break
    case '1y':
      start.setFullYear(end.getFullYear() - 1)
      break
    case 'custom':
      return {
        start_date: customStartDate.value,
        end_date: customEndDate.value
      }
  }
  
  return {
    start_date: start.toISOString().split('T')[0],
    end_date: end.toISOString().split('T')[0]
  }
}

const loadAnalytics = async () => {
  loading.value = true
  try {
    const timeRangeParams = getTimeRangeDates()
    
    const [programsRes, campaignsRes, segmentsRes, transactionsRes] = await Promise.all([
      analyticsApi.getProgramPerformance(timeRangeParams),
      analyticsApi.getCampaignPerformance(timeRangeParams),
      analyticsApi.getSegmentAnalytics(),
      analyticsApi.getTransactionAnalytics(timeRangeParams),
    ])
    
    // Process program data
    const programs = programsRes.data
    programPerformanceData.value = programs.map((p: any) => ({
      name: p.program_name,
      points_issued: p.points_issued || 0,
      points_redeemed: p.points_redeemed || 0,
    }))
    topPrograms.value = programs.slice(0, 10)
    programStats.value = {
      active: programs.filter((p: any) => p.is_active).length,
      total: programs.length
    }
    
    // Process campaign data
    const campaigns = campaignsRes.data
    campaignPerformanceData.value = campaigns.map((c: any) => ({
      name: c.campaign_name,
      triggered: c.triggered || 0,
      delivered: c.delivered || 0,
      converted: c.converted || 0,
    }))
    topCampaigns.value = campaigns.slice(0, 10)
    const avgConversion = campaigns.length > 0
      ? campaigns.reduce((sum: number, c: any) => sum + (c.conversion_rate || 0), 0) / campaigns.length
      : 0
    campaignStats.value = {
      avgConversion: Math.round(avgConversion * 100) / 100,
      total: campaigns.length,
      trend: 'up'
    }
    
    // Process segment data
    const segments = segmentsRes.data
    segmentDistributionData.value = segments.map((s: any) => ({
      name: s.segment_name,
      value: s.member_count || 0,
    }))
    const avgGrowth = segments.length > 0
      ? segments.reduce((sum: number, s: any) => sum + (s.growth_rate || 0), 0) / segments.length
      : 0
    segmentStats.value = {
      avgGrowth: Math.round(avgGrowth * 100) / 100,
      total: segments.length
    }
    
    // Process transaction data
    const transactions = transactionsRes.data
    transactionTrendsData.value = transactions.map((t: any) => ({
      date: t.date,
      earn_count: t.earn_count || 0,
      redeem_count: t.redeem_count || 0,
    }))
    
    // Generate revenue trends (mock for now)
    revenueTrendsData.value = transactions.map((t: any) => ({
      date: t.date,
      revenue: (t.total_points || 0) * 0.01, // Mock: 1 point = $0.01
    }))
    
    // Calculate revenue stats
    const totalRevenue = revenueTrendsData.value.reduce((sum, t) => sum + t.revenue, 0)
    revenueStats.value = {
      total: totalRevenue,
      trend: 'up',
      change: 12.5 // Mock
    }
    
    // Generate funnel data
    if (campaigns.length > 0) {
      const avgTriggered = campaigns.reduce((sum: number, c: any) => sum + (c.triggered || 0), 0) / campaigns.length
      const avgDelivered = campaigns.reduce((sum: number, c: any) => sum + (c.delivered || 0), 0) / campaigns.length
      const avgConverted = campaigns.reduce((sum: number, c: any) => sum + (c.converted || 0), 0) / campaigns.length
      
      funnelData.value = [
        { stage: 'Triggered', value: Math.round(avgTriggered) },
        { stage: 'Delivered', value: Math.round(avgDelivered) },
        { stage: 'Converted', value: Math.round(avgConverted) },
      ]
    }
    
  } catch (error) {
    console.error('Error loading analytics:', error)
    // Keep default/empty values on error
  } finally {
    loading.value = false
  }
}

const applyCustomRange = () => {
  if (!customStartDate.value || !customEndDate.value) {
    alert('Please select both start and end dates')
    return
  }
  loadAnalytics()
}

const exportReport = async (reportType: 'transactions' | 'programs' | 'campaigns' | 'customers' = 'transactions') => {
  try {
    const response = await analyticsApi.exportReport({
      report_type: reportType,
      format: 'csv',
      date_from: undefined, // Add date filters if needed
      date_to: undefined
    })
    
    // Create download link
    const blob = new Blob([response.data], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `loyalty_report_${reportType}_${new Date().toISOString().split('T')[0]}.csv`
    a.click()
    URL.revokeObjectURL(url)
    
    alert('Report exported successfully!')
  } catch (error: any) {
    console.error('Error exporting report:', error)
    alert('Error exporting report: ' + (error.response?.data?.error || error.message))
  }
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('en-US').format(num)
}

const formatDateShort = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const getTrendIcon = (trend: string) => {
  if (trend === 'up') return '↑'
  if (trend === 'down') return '↓'
  return '→'
}

onMounted(() => {
  loadAnalytics()
})
</script>

<style scoped>
.analytics-dashboard {
  padding: 2rem;
  max-width: 1600px;
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
  align-items: center;
}

.time-range-select {
  padding: 0.5rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
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

.custom-range {
  margin-bottom: 2rem;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  align-items: end;
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

.form-group input {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
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
  font-size: 2rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.5rem;
}

.kpi-trend {
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.kpi-trend.up {
  color: #059669;
}

.kpi-trend.down {
  color: #dc2626;
}

.kpi-trend.neutral {
  color: #666;
}

.charts-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.chart-placeholder {
  padding: 3rem;
  text-align: center;
  color: #999;
  background: #f9fafb;
  border-radius: 6px;
}

.tables-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.table-container {
  overflow-x: auto;
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

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
}
</style>
