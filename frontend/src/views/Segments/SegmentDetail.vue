<template>
  <div class="segment-detail">
    <div v-if="loading" class="loading">Loading segment...</div>
    
    <div v-else-if="segment" class="segment-content">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <h1>{{ segment.name }}</h1>
          <p class="subtitle">{{ segment.description || 'No description' }}</p>
          <div class="segment-meta">
            <span class="status-badge" :class="segment.is_active ? 'active' : 'inactive'">
              {{ segment.is_active ? 'Active' : 'Inactive' }}
            </span>
            <span class="meta-item">
              <strong>Type:</strong> {{ segmentType }}
            </span>
            <span class="meta-item">
              <strong>Members:</strong> {{ memberCount }}
            </span>
            <span class="meta-item" v-if="segment.program">
              <strong>Program:</strong> {{ programName }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="editSegment" class="btn-secondary">Edit Segment</button>
          <button @click="recalculateSegment" class="btn-primary" :disabled="recalculating">
            {{ recalculating ? 'Recalculating...' : 'Recalculate' }}
          </button>
        </div>
      </div>

      <!-- KPI Cards -->
      <div class="kpi-grid">
        <div class="kpi-card">
          <div class="kpi-label">Total Members</div>
          <div class="kpi-value">{{ memberCount }}</div>
          <div class="kpi-trend">
            <span class="trend-up">↑</span> Active
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Segment Type</div>
          <div class="kpi-value">{{ segmentType }}</div>
          <div class="kpi-trend">
            <span class="trend-neutral">→</span> {{ segment.is_dynamic ? 'Auto-updates' : 'Manual' }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Last Calculated</div>
          <div class="kpi-value">{{ formatDateShort(lastCalculated) }}</div>
          <div class="kpi-trend">
            <span class="trend-neutral">→</span> {{ formatTimeAgo(lastCalculated) }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">Snapshots</div>
          <div class="kpi-value">{{ snapshots.length }}</div>
          <div class="kpi-trend">
            <span class="trend-neutral">→</span> Historical
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
            <h2>Segment Information</h2>
            <div class="info-grid">
              <div class="info-item">
                <label>Name</label>
                <div>{{ segment.name }}</div>
              </div>
              <div class="info-item">
                <label>Description</label>
                <div>{{ segment.description || 'No description' }}</div>
              </div>
              <div class="info-item">
                <label>Status</label>
                <div>
                  <span class="status-badge" :class="segment.is_active ? 'active' : 'inactive'">
                    {{ segment.is_active ? 'Active' : 'Inactive' }}
                  </span>
                </div>
              </div>
              <div class="info-item">
                <label>Type</label>
                <div>{{ segmentType }}</div>
              </div>
              <div class="info-item">
                <label>Program</label>
                <div>{{ programName || 'No specific program' }}</div>
              </div>
              <div class="info-item">
                <label>Created</label>
                <div>{{ formatDate(segment.created_at) }}</div>
              </div>
              <div class="info-item">
                <label>Last Updated</label>
                <div>{{ formatDate(segment.updated_at) }}</div>
              </div>
            </div>
          </div>

          <div class="section">
            <h2>Segment Rules (JSONLogic)</h2>
            <div class="rules-display">
              <pre>{{ JSON.stringify(parsedRules, null, 2) }}</pre>
            </div>
          </div>
        </div>

        <!-- Members Tab -->
        <div v-if="activeTab === 'members'" class="tab-panel">
          <div class="section">
            <div class="section-header">
              <h2>Segment Members ({{ members.length }})</h2>
              <div class="section-actions">
                <input 
                  v-model="memberSearch" 
                  placeholder="Search customer ID..."
                  class="search-input"
                />
                <button @click="loadMembers" class="btn-secondary">Refresh</button>
                <button @click="exportMembers" class="btn-secondary">Export CSV</button>
              </div>
            </div>
            <div v-if="members.length === 0" class="empty-state">
              No members found. Click "Recalculate" to populate segment.
            </div>
            <div v-else class="members-table">
              <table class="data-table">
                <thead>
                  <tr>
                    <th>Customer ID</th>
                    <th>Joined At</th>
                    <th>Left At</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="member in filteredMembers" :key="member.id">
                    <td>{{ formatCustomerId(member.customer_id) }}</td>
                    <td>{{ formatDate(member.joined_at) }}</td>
                    <td>{{ formatDate(member.left_at) || '-' }}</td>
                    <td>
                      <span class="status-badge" :class="member.is_active ? 'active' : 'inactive'">
                        {{ member.is_active ? 'Active' : 'Inactive' }}
                      </span>
                    </td>
                  </tr>
                </tbody>
              </table>
              <div v-if="filteredMembers.length > 100" class="more-members">
                Showing first 100 of {{ filteredMembers.length }} members
              </div>
            </div>
          </div>
        </div>

        <!-- Snapshots Tab -->
        <div v-if="activeTab === 'snapshots'" class="tab-panel">
          <div class="section">
            <div class="section-header">
              <h2>Segment Snapshots</h2>
              <button @click="loadSnapshots" class="btn-secondary">Refresh</button>
            </div>
            <div v-if="snapshots.length === 0" class="empty-state">
              <p>No snapshots available.</p>
              <p class="empty-hint">Click "Recalculate" on the Overview tab to generate a snapshot.</p>
            </div>
            <div v-else class="snapshots-list">
              <div v-for="(snapshot, idx) in sortedSnapshots" :key="snapshot.id || idx" class="snapshot-card">
                <div class="snapshot-header">
                  <h3>Snapshot #{{ sortedSnapshots.length - idx }}</h3>
                  <span class="snapshot-date">{{ formatSnapshotDate(snapshot) }}</span>
                </div>
                <div class="snapshot-content">
                  <div class="snapshot-stat">
                    <span class="stat-label">Snapshot Date:</span>
                    <span class="stat-value">{{ formatFullDate(snapshot.snapshot_date || snapshot.created_at) }}</span>
                  </div>
                  <div class="snapshot-stat">
                    <span class="stat-label">Member Count:</span>
                    <span class="stat-value highlight">{{ snapshot.member_count || 0 }}</span>
                  </div>
                  <div class="snapshot-stat" v-if="idx < sortedSnapshots.length - 1">
                    <span class="stat-label">Change:</span>
                    <span class="stat-value" :class="getChangeClass(snapshot, sortedSnapshots[idx + 1])">
                      {{ getChangeText(snapshot, sortedSnapshots[idx + 1]) }}
                    </span>
                  </div>
                  <div class="snapshot-stat">
                    <span class="stat-label">Time Ago:</span>
                    <span class="stat-value">{{ formatTimeAgo(snapshot.snapshot_date || snapshot.created_at) }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ML Predictions Tab -->
        <div v-if="activeTab === 'ml'" class="tab-panel">
          <div class="section">
            <div class="section-header">
              <h2>Machine Learning Predictions</h2>
              <div class="ml-actions">
                <select v-model="mlPredictionType" class="ml-type-select">
                  <option value="churn">Churn Prediction</option>
                  <option value="nbo">Next Best Offer (NBO)</option>
                  <option value="rfm">RFM Segmentation</option>
                  <option value="ltv">Lifetime Value (LTV)</option>
                  <option value="propensity">Propensity Score</option>
                  <option value="product">Product Recommendation</option>
                  <option value="campaign">Campaign Response</option>
                  <option value="default_risk">Default Risk</option>
                  <option value="upsell">Upsell Probability</option>
                  <option value="engagement">Engagement Score</option>
                </select>
                <button @click="runMLPrediction" class="btn-primary" :disabled="runningML">
                  {{ runningML ? 'Running...' : 'Run ML Prediction' }}
                </button>
                <button @click="loadMLStats" class="btn-secondary" :disabled="loadingMLStats">
                  {{ loadingMLStats ? 'Loading...' : 'Load Stats' }}
                </button>
              </div>
            </div>
            
            <div v-if="mlStats || mlResult?.aggregated_stats" class="ml-stats-container">
              <!-- Summary KPI Cards - Show relevant KPIs based on prediction type -->
              <div class="ml-kpi-grid">
                <div class="ml-kpi-card">
                  <div class="kpi-icon high">📊</div>
                  <div class="kpi-content">
                    <span class="kpi-value">{{ getTotalAnalyzed() }}</span>
                    <span class="kpi-label">Customers Analyzed</span>
                  </div>
                </div>
                <!-- Churn KPIs - only for churn prediction -->
                <template v-if="mlPredictionType === 'churn'">
                  <div class="ml-kpi-card" v-if="getChurnStats()">
                    <div class="kpi-icon danger">⚠️</div>
                    <div class="kpi-content">
                      <span class="kpi-value">{{ getChurnStats().high || 0 }}</span>
                      <span class="kpi-label">High Churn Risk</span>
                    </div>
                  </div>
                  <div class="ml-kpi-card" v-if="getChurnStats()">
                    <div class="kpi-icon info">📈</div>
                    <div class="kpi-content">
                      <span class="kpi-value">{{ ((getChurnStats().avg_probability || 0) * 100).toFixed(0) }}%</span>
                      <span class="kpi-label">Avg Churn Probability</span>
                    </div>
                  </div>
                </template>
                <!-- Default Risk KPIs - only for default_risk prediction -->
                <template v-if="mlPredictionType === 'default_risk'">
                  <div class="ml-kpi-card" v-if="getDefaultRiskStats()">
                    <div class="kpi-icon danger">💳</div>
                    <div class="kpi-content">
                      <span class="kpi-value">{{ getDefaultRiskStats().high || 0 }}</span>
                      <span class="kpi-label">High Default Risk</span>
                    </div>
                  </div>
                  <div class="ml-kpi-card" v-if="getDefaultRiskStats()">
                    <div class="kpi-icon success">✅</div>
                    <div class="kpi-content">
                      <span class="kpi-value">{{ getDefaultRiskStats().low || 0 }}</span>
                      <span class="kpi-label">Low Default Risk</span>
                    </div>
                  </div>
                </template>
                <!-- RFM KPIs - only for rfm prediction -->
                <template v-if="mlPredictionType === 'rfm'">
                  <div class="ml-kpi-card" v-if="getRfmStats()">
                    <div class="kpi-icon success">🏆</div>
                    <div class="kpi-content">
                      <span class="kpi-value">{{ getRfmStats().distribution?.Champions || 0 }}</span>
                      <span class="kpi-label">Champions</span>
                    </div>
                  </div>
                  <div class="ml-kpi-card" v-if="getRfmStats()">
                    <div class="kpi-icon warning">⚡</div>
                    <div class="kpi-content">
                      <span class="kpi-value">{{ (getRfmStats().distribution?.['At Risk'] || 0) + (getRfmStats().distribution?.['Need Attention'] || 0) }}</span>
                      <span class="kpi-label">At Risk / Need Attention</span>
                    </div>
                  </div>
                </template>
                <!-- NBO KPIs - only for nbo prediction -->
                <template v-if="mlPredictionType === 'nbo'">
                  <div class="ml-kpi-card" v-if="getNboStats()">
                    <div class="kpi-icon info">🎯</div>
                    <div class="kpi-content">
                      <span class="kpi-value">{{ Object.keys(getNboStats().distribution || {}).length }}</span>
                      <span class="kpi-label">Unique Offers</span>
                    </div>
                  </div>
                </template>
              </div>

              <!-- CHURN: Churn Risk Analysis -->
              <div v-if="mlPredictionType === 'churn' && getChurnStats()" class="ml-section">
                <h3 class="section-title">🔴 Churn Risk Analysis</h3>
                <div class="table-container">
                  <table class="ml-table">
                    <thead>
                      <tr>
                        <th>Risk Level</th>
                        <th>Customers</th>
                        <th>Percentage</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><span class="risk-badge high">High Risk</span></td>
                        <td>{{ getChurnStats().high || 0 }}</td>
                        <td>{{ (getChurnStats().high_percentage || 0).toFixed(1) }}%</td>
                        <td><span class="status-indicator danger">Requires Action</span></td>
                      </tr>
                      <tr>
                        <td><span class="risk-badge medium">Medium Risk</span></td>
                        <td>{{ getChurnStats().medium || 0 }}</td>
                        <td>{{ (getChurnStats().medium_percentage || 0).toFixed(1) }}%</td>
                        <td><span class="status-indicator warning">Monitor</span></td>
                      </tr>
                      <tr>
                        <td><span class="risk-badge low">Low Risk</span></td>
                        <td>{{ getChurnStats().low || 0 }}</td>
                        <td>{{ (getChurnStats().low_percentage || 0).toFixed(1) }}%</td>
                        <td><span class="status-indicator success">Healthy</span></td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr>
                        <td><strong>Total</strong></td>
                        <td><strong>{{ getChurnStats().count || 0 }}</strong></td>
                        <td><strong>100%</strong></td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              <!-- RFM: Customer Segments -->
              <div v-if="mlPredictionType === 'rfm' && getRfmStats()" class="ml-section">
                <h3 class="section-title">👥 Customer Segmentation (RFM Analysis)</h3>
                <div class="table-container">
                  <table class="ml-table">
                    <thead>
                      <tr>
                        <th>Segment</th>
                        <th>Customers</th>
                        <th>% of Total</th>
                        <th>Recommendation</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="[segment, count] in (getRfmStats().top_segments || [])" :key="segment">
                        <td><span :class="'segment-badge ' + getSegmentClass(segment)">{{ segment }}</span></td>
                        <td>{{ count }}</td>
                        <td>{{ getTotalAnalyzed() > 0 ? ((count / getTotalAnalyzed()) * 100).toFixed(1) : 0 }}%</td>
                        <td>{{ getSegmentRecommendation(segment) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- NBO: Next Best Offer Recommendations -->
              <div v-if="mlPredictionType === 'nbo' && getNboStats()" class="ml-section">
                <h3 class="section-title">🎯 Next Best Offer Recommendations</h3>
                <div class="table-container">
                  <table class="ml-table">
                    <thead>
                      <tr>
                        <th>Offer ID</th>
                        <th>Recommended For</th>
                        <th>% of Customers</th>
                        <th>Priority</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="([offerId, count], idx) in (getNboStats().top_offers || [])" :key="offerId">
                        <td><strong>Offer #{{ offerId }}</strong></td>
                        <td>{{ count }} customers</td>
                        <td>{{ getTotalAnalyzed() > 0 ? ((count / getTotalAnalyzed()) * 100).toFixed(1) : 0 }}%</td>
                        <td><span :class="'priority-badge ' + (idx === 0 ? 'high' : idx === 1 ? 'medium' : 'low')">
                          {{ idx === 0 ? 'Top Priority' : idx === 1 ? 'High' : 'Standard' }}
                        </span></td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              <!-- DEFAULT RISK: Default Risk Analysis -->
              <div v-if="mlPredictionType === 'default_risk' && getDefaultRiskStats()" class="ml-section">
                <h3 class="section-title">💳 Default Risk Analysis</h3>
                <p class="section-desc">Predicting likelihood of customer payment defaults</p>
                <div class="table-container">
                  <table class="ml-table">
                    <thead>
                      <tr>
                        <th>Risk Level</th>
                        <th>Customers</th>
                        <th>Percentage</th>
                        <th>Recommended Action</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><span class="risk-badge high">High Risk</span></td>
                        <td>{{ getDefaultRiskStats().high || 0 }}</td>
                        <td>{{ getDefaultRiskPercent('high') }}%</td>
                        <td><span class="status-indicator danger">Review Credit Limits</span></td>
                      </tr>
                      <tr>
                        <td><span class="risk-badge medium">Medium Risk</span></td>
                        <td>{{ getDefaultRiskStats().medium || 0 }}</td>
                        <td>{{ getDefaultRiskPercent('medium') }}%</td>
                        <td><span class="status-indicator warning">Monitor Closely</span></td>
                      </tr>
                      <tr>
                        <td><span class="risk-badge low">Low Risk</span></td>
                        <td>{{ getDefaultRiskStats().low || 0 }}</td>
                        <td>{{ getDefaultRiskPercent('low') }}%</td>
                        <td><span class="status-indicator success">Standard Terms</span></td>
                      </tr>
                    </tbody>
                    <tfoot>
                      <tr>
                        <td><strong>Total</strong></td>
                        <td><strong>{{ getDefaultRiskTotal() }}</strong></td>
                        <td><strong>100%</strong></td>
                        <td></td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              <!-- PROPENSITY / UPSELL / ENGAGEMENT: Generic Score Display -->
              <div v-if="['propensity', 'upsell', 'engagement', 'ltv', 'campaign', 'product'].includes(mlPredictionType)" class="ml-section">
                <h3 class="section-title">{{ getModelTitle() }}</h3>
                <p class="section-desc">{{ getModelDescription() }}</p>
                <div class="info-message">
                  <p>Prediction completed for {{ getTotalAnalyzed() }} customers.</p>
                  <p v-if="mlResult?.successful">Successfully processed: {{ mlResult.successful }} customers</p>
                </div>
              </div>

              <!-- Individual Prediction Results Table -->
              <div v-if="mlResult?.results && mlResult.results.length > 0" class="ml-section">
                <h3 class="section-title">📋 Individual Customer Results</h3>
                <p class="section-desc">Detailed predictions for each customer (showing first 20)</p>
                <div class="table-container">
                  <table class="ml-table">
                    <thead>
                      <tr>
                        <th>Customer ID</th>
                        <th>Score</th>
                        <th>Risk Level</th>
                        <th>Prediction</th>
                        <th>Confidence</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="item in mlResult.results.slice(0, 20)" :key="item.customer_id">
                        <td><code>{{ formatCustomerId(item.customer_id) }}</code></td>
                        <td>{{ formatRiskScore(item.result) }}</td>
                        <td>
                          <span :class="'risk-badge ' + (item.result?.risk_level || 'low')">
                            {{ (item.result?.risk_level || 'N/A').toUpperCase() }}
                          </span>
                        </td>
                        <td>{{ getPredictionLabel(item.result) }}</td>
                        <td>{{ ((item.result?.confidence || 0) * 100).toFixed(0) }}%</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
                <p v-if="mlResult.results.length > 20" class="table-note">
                  Showing 20 of {{ mlResult.results.length }} results
                </p>
              </div>
            </div>
            
            <div v-if="mlResult" class="ml-result">
              <h3>Prediction Results</h3>
              <div class="result-summary">
                <p><strong>Total Customers:</strong> {{ mlResult.total_customers || 0 }}</p>
                <p><strong>Processed:</strong> {{ mlResult.processed || 0 }}</p>
                <p><strong>Successful:</strong> {{ mlResult.successful || 0 }}</p>
                <p v-if="mlResult.failed"><strong>Failed:</strong> {{ mlResult.failed || 0 }}</p>
                <p v-if="mlResult.warning" class="warning-text">{{ mlResult.warning }}</p>
              </div>
            </div>
            
            <div v-if="!mlStats && !mlResult && !runningML" class="empty-state">
              Click "Run ML Prediction" to analyze this segment with machine learning.
            </div>
          </div>
        </div>

        <!-- Analytics Tab -->
        <div v-if="activeTab === 'analytics'" class="tab-panel">
          <div class="section">
            <h2>Member Growth Over Time</h2>
            <ChartCard title="Member Count History" subtitle="Based on snapshots">
              <LineChart
                v-if="snapshotChartData.length > 0"
                :data="snapshotChartData"
                x-key="date"
                :lines="[
                  { dataKey: 'count', name: 'Member Count', stroke: '#2563eb' }
                ]"
                :x-formatter="(val) => formatDateShort(val)"
              />
              <div v-else class="chart-placeholder">No snapshot data available</div>
            </ChartCard>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <h2>Segment not found</h2>
      <p>The segment you're looking for doesn't exist or has been deleted.</p>
      <button @click="$router.push('/segments')" class="btn-primary">Back to Segments</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { segmentsApi } from '@/api/services/segments'
import { programsApi } from '@/api/services/programs'
import type { Segment, SegmentMember } from '@/types/loyalty'
import ChartCard from '@/components/ChartCard.vue'
import LineChart from '@/components/LineChart.vue'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'

const route = useRoute()
const router = useRouter()

const segment = ref<Segment | null>(null)
const members = ref<SegmentMember[]>([])
const snapshots = ref<any[]>([])
const programName = ref('')
const loading = ref(true)
const recalculating = ref(false)
const activeTab = ref('overview')
const memberSearch = ref('')
const mlPredictionType = ref<'churn' | 'nbo' | 'rfm' | 'ltv' | 'propensity' | 'product' | 'campaign' | 'default_risk' | 'upsell' | 'engagement'>('churn')
const runningML = ref(false)
const loadingMLStats = ref(false)
const mlResult = ref<any>(null)
const mlStats = ref<any>(null)

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'members', label: 'Members' },
  { id: 'snapshots', label: 'Snapshots' },
  { id: 'ml', label: 'ML Predictions' },
  { id: 'analytics', label: 'Analytics' },
]

const segmentType = computed(() => {
  if (segment.value?.is_rfm) return 'RFM Segment'
  if (segment.value?.is_dynamic) return 'Dynamic Segment'
  return 'Static Segment'
})

const memberCount = computed(() => {
  if (!segment.value) return 0
  // Try multiple possible field names from backend
  return segment.value.member_count || 
         segment.value.active_member_count || 
         members.value.length || 
         0
})

const lastCalculated = computed(() => {
  if (snapshots.value.length > 0) {
    return snapshots.value[0].created_at
  }
  return segment.value?.updated_at || segment.value?.created_at
})

const parsedRules = computed(() => {
  if (!segment.value?.rules) return {}
  if (typeof segment.value.rules === 'string') {
    try {
      return JSON.parse(segment.value.rules)
    } catch {
      return {}
    }
  }
  return segment.value.rules
})

const filteredMembers = computed(() => {
  let filtered = members.value
  
  if (memberSearch.value) {
    const search = memberSearch.value.toLowerCase()
    filtered = filtered.filter(m => 
      m.customer_id.toLowerCase().includes(search)
    )
  }
  
  return filtered.slice(0, 100) // Limit to first 100 for performance
})

const snapshotChartData = computed(() => {
  return snapshots.value
    .sort((a, b) => new Date(a.created_at || a.snapshot_date).getTime() - new Date(b.created_at || b.snapshot_date).getTime())
    .map(s => ({
      date: s.created_at || s.snapshot_date,
      count: s.member_count || 0
    }))
})

// Sorted snapshots (newest first)
const sortedSnapshots = computed(() => {
  return [...snapshots.value].sort((a, b) => {
    const dateA = new Date(a.snapshot_date || a.created_at).getTime()
    const dateB = new Date(b.snapshot_date || b.created_at).getTime()
    return dateB - dateA  // Descending (newest first)
  })
})

const formatSnapshotDate = (snapshot: any) => {
  const date = snapshot.snapshot_date || snapshot.created_at
  if (!date) return '-'
  try {
    return format(new Date(date), 'MMM dd, yyyy')
  } catch {
    return '-'
  }
}

const formatFullDate = (date: string | null | undefined) => {
  if (!date) return '-'
  try {
    return format(new Date(date), 'EEEE, MMM dd, yyyy \'at\' HH:mm')
  } catch {
    return '-'
  }
}

const getChangeClass = (current: any, previous: any) => {
  const currentCount = current.member_count || 0
  const prevCount = previous.member_count || 0
  if (currentCount > prevCount) return 'trend-up'
  if (currentCount < prevCount) return 'trend-down'
  return 'trend-neutral'
}

const getChangeText = (current: any, previous: any) => {
  const currentCount = current.member_count || 0
  const prevCount = previous.member_count || 0
  const diff = currentCount - prevCount
  const pct = prevCount > 0 ? ((diff / prevCount) * 100).toFixed(1) : '0'
  if (diff > 0) return `+${diff} (+${pct}%)`
  if (diff < 0) return `${diff} (${pct}%)`
  return 'No change'
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

const formatDateShort = (dateStr: string) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}

const formatTimeAgo = (dateStr: string | null | undefined) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMins = Math.floor(diffMs / 60000)
  const diffHours = Math.floor(diffMs / 3600000)
  const diffDays = Math.floor(diffMs / 86400000)
  
  if (diffMins < 1) return 'Just now'
  if (diffMins < 60) return `${diffMins}m ago`
  if (diffHours < 24) return `${diffHours}h ago`
  if (diffDays < 7) return `${diffDays}d ago`
  return formatDate(dateStr)
}

const formatCustomerId = (id: string) => {
  if (!id) return '-'
  return id.substring(0, 8) + '...'
}

const loadSegment = async () => {
  loading.value = true
  try {
    const response = await segmentsApi.getById(route.params.id as string)
    segment.value = response.data
    
    // Load program name
    if (segment.value.program) {
      try {
        const programResponse = await programsApi.getById(segment.value.program.toString())
        programName.value = programResponse.data.name
      } catch (error) {
        console.error('Error loading program:', error)
      }
    }
    
    // Load members, snapshots, and metrics
    await Promise.all([
      loadMembers(),
      loadSnapshots(),
      loadMetrics()
    ])
  } catch (error) {
    console.error('Error loading segment:', error)
    segment.value = null
  } finally {
    loading.value = false
  }
}

const loadMembers = async () => {
  try {
    const response = await segmentsApi.getMembers(route.params.id as string)
    members.value = Array.isArray(response.data) ? response.data : []
  } catch (error) {
    console.error('Error loading members:', error)
    members.value = []
  }
}

const loadSnapshots = async () => {
  try {
    const response = await segmentsApi.getSnapshots(route.params.id as string)
    snapshots.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading snapshots:', error)
    snapshots.value = []
  }
}

const loadMetrics = async () => {
  try {
    const response = await segmentsApi.getMetrics(route.params.id as string)
    // Update member count from metrics if available
    if (response.data.total_members !== undefined && segment.value) {
      segment.value.member_count = response.data.total_members
    }
    // Update snapshots from metrics if available
    if (response.data.snapshots && response.data.snapshots.length > 0) {
      snapshots.value = response.data.snapshots.map((s: any) => ({
        id: s.date,
        created_at: s.date,
        member_count: s.member_count,
        snapshot_date: s.date,
      }))
    }
  } catch (error) {
    console.error('Error loading metrics:', error)
  }
}

const recalculateSegment = async () => {
  recalculating.value = true
  try {
    const response = await segmentsApi.calculate(route.params.id as string)
    const result = response.data
    
    // Reload segment data
    await loadSegment()
    await loadMembers()
    await loadMetrics()
    
    // Show success message with details
    const message = `Segment recalculated successfully!\n\n` +
      `Added: ${result.added || 0} members\n` +
      `Removed: ${result.removed || 0} members\n` +
      `Total: ${result.total || 0} members`
    alert(message)
    await Promise.all([
      loadSegment(),
      loadMembers()
    ])
  } catch (error: any) {
    console.error('Error recalculating segment:', error)
    alert('Error recalculating segment: ' + (error.response?.data?.detail || error.message))
  } finally {
    recalculating.value = false
  }
}

const editSegment = () => {
  router.push(`/segments/${route.params.id}/builder`)
}

const exportMembers = () => {
  const csv = [
    ['Customer ID', 'Joined At', 'Left At', 'Status'],
    ...filteredMembers.value.map(m => [
      m.customer_id,
      formatDate(m.joined_at),
      formatDate(m.left_at) || '',
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

const runMLPrediction = async () => {
  if (!segment.value) return
  runningML.value = true
  mlResult.value = null
  mlStats.value = null
  
  try {
    const response = await segmentsApi.predictML(route.params.id as string, mlPredictionType.value)
    mlResult.value = response.data
    // Also load stats after prediction
    await loadMLStats()
  } catch (error: any) {
    console.error('Error running ML prediction:', error)
    alert('Error running ML prediction: ' + (error.response?.data?.error || error.message))
  } finally {
    runningML.value = false
  }
}

const loadMLStats = async () => {
  if (!segment.value) return
  loadingMLStats.value = true
  mlStats.value = null
  
  try {
    const response = await segmentsApi.getMLStats(route.params.id as string)
    mlStats.value = response.data
  } catch (error: any) {
    console.error('Error loading ML stats:', error)
    alert('Error loading ML stats: ' + (error.response?.data?.error || error.message))
  } finally {
    loadingMLStats.value = false
  }
}

// Helper methods for ML Stats display
const getTotalAnalyzed = () => {
  if (!mlStats.value?.stats) return 0
  if (mlStats.value.stats.churn?.count) return mlStats.value.stats.churn.count
  if (mlStats.value.stats.rfm?.distribution) {
    return Object.values(mlStats.value.stats.rfm.distribution as Record<string, number>).reduce((a, b) => a + b, 0)
  }
  return mlResult.value?.total_customers || 0
}

const getSegmentClass = (segment: string) => {
  const classMap: Record<string, string> = {
    'Champions': 'champions',
    'Loyal Customers': 'loyal',
    'Potential Loyalists': 'potential',
    'New Customers': 'new',
    'Promising': 'promising',
    'Need Attention': 'attention',
    'About To Sleep': 'sleep',
    'At Risk': 'risk',
    'Can\'t Lose Them': 'cantlose',
    'Lost': 'lost',
    'Regular': 'regular',
    'Hibernating': 'hibernating'
  }
  return classMap[segment] || 'default'
}

const getSegmentRecommendation = (segment: string) => {
  const recommendations: Record<string, string> = {
    'Champions': 'Reward them! Engage with exclusive offers',
    'Loyal Customers': 'Upsell premium products',
    'Potential Loyalists': 'Offer membership/loyalty programs',
    'New Customers': 'Send onboarding nurture campaigns',
    'Promising': 'Create brand awareness campaigns',
    'Need Attention': 'Send reactivation campaigns',
    'About To Sleep': 'Win them back with time-limited offers',
    'At Risk': 'Personalized retention campaigns urgently',
    'Can\'t Lose Them': 'Highest priority - personal outreach',
    'Lost': 'Attempt win-back with strong incentives',
    'Regular': 'Maintain engagement with relevant content',
    'Hibernating': 'Reactivation campaign needed'
  }
  return recommendations[segment] || 'Analyze and create targeted campaign'
}

// Stats helper functions for each model type
const getChurnStats = () => {
  if (mlStats.value?.stats?.churn) {
    return mlStats.value.stats.churn
  }
  if (mlResult.value?.aggregated_stats?.churn) {
    return mlResult.value.aggregated_stats.churn
  }
  return null
}

const getRfmStats = () => {
  if (mlStats.value?.stats?.rfm) {
    return mlStats.value.stats.rfm
  }
  if (mlResult.value?.aggregated_stats?.rfm) {
    return mlResult.value.aggregated_stats.rfm
  }
  return null
}

const getNboStats = () => {
  if (mlStats.value?.stats?.nbo) {
    return mlStats.value.stats.nbo
  }
  if (mlResult.value?.aggregated_stats?.nbo) {
    return mlResult.value.aggregated_stats.nbo
  }
  return null
}

// Default Risk helpers
const getDefaultRiskStats = () => {
  // Check both sources for default_risk data
  if (mlStats.value?.stats?.default_risk) {
    return mlStats.value.stats.default_risk
  }
  if (mlResult.value?.aggregated_stats?.default_risk) {
    return mlResult.value.aggregated_stats.default_risk
  }
  return null
}

// Model title and description helpers
const getModelTitle = () => {
  const titles: Record<string, string> = {
    'churn': '🔴 Churn Prediction',
    'rfm': '👥 RFM Analysis',
    'nbo': '🎯 Next Best Offer',
    'ltv': '💰 Customer Lifetime Value',
    'propensity': '📊 Propensity Score',
    'campaign': '📢 Campaign Response',
    'default_risk': '💳 Default Risk',
    'upsell': '📈 Upsell Potential',
    'engagement': '🎮 Engagement Score',
    'product': '🛍️ Product Recommendations'
  }
  return titles[mlPredictionType.value] || '📊 ML Prediction'
}

const getModelDescription = () => {
  const descriptions: Record<string, string> = {
    'churn': 'Predicting likelihood of customer churn based on behavior patterns',
    'rfm': 'Segmenting customers based on Recency, Frequency, and Monetary value',
    'nbo': 'Recommending the best next offer for each customer',
    'ltv': 'Estimating the lifetime value of each customer',
    'propensity': 'Scoring likelihood of customer actions',
    'campaign': 'Predicting response to marketing campaigns',
    'default_risk': 'Assessing risk of payment default',
    'upsell': 'Identifying upsell opportunities for each customer',
    'engagement': 'Measuring customer engagement levels',
    'product': 'Recommending products based on customer preferences'
  }
  return descriptions[mlPredictionType.value] || 'Running machine learning predictions'
}

const getDefaultRiskTotal = () => {
  const stats = getDefaultRiskStats()
  if (!stats) return 0
  return (stats.high || 0) + (stats.medium || 0) + (stats.low || 0)
}

const getDefaultRiskPercent = (level: string) => {
  const stats = getDefaultRiskStats()
  const total = getDefaultRiskTotal()
  if (!stats || total === 0) return '0.0'
  const value = stats[level] || 0
  return ((value / total) * 100).toFixed(1)
}

const formatRiskScore = (result: any) => {
  if (!result) return 'N/A'
  // Check for various score fields
  const score = result.default_risk_score ?? result.default_risk ?? result.churn_probability ?? result.score ?? 0
  return (score * 100).toFixed(1) + '%'
}

const getPredictionLabel = (result: any) => {
  if (!result) return 'N/A'
  // Check various prediction fields
  if (result.will_default !== undefined) {
    return result.will_default ? '⚠️ Likely to Default' : '✅ Unlikely to Default'
  }
  if (result.will_churn !== undefined) {
    return result.will_churn ? '⚠️ Likely to Churn' : '✅ Likely to Stay'
  }
  if (result.risk_level) {
    return result.risk_level === 'high' ? '⚠️ High Risk' : 
           result.risk_level === 'medium' ? '⚡ Medium Risk' : '✅ Low Risk'
  }
  return 'Analyzed'
}

// Clear results when switching ML prediction type
watch(mlPredictionType, () => {
  mlResult.value = null
  mlStats.value = null
})

onMounted(() => {
  loadSegment()
})
</script>

<style scoped>
.segment-detail {
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

.segment-meta {
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

.members-table {
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

.more-members {
  padding: 1rem;
  text-align: center;
  color: #666;
  font-size: 0.875rem;
}

.snapshots-list {
  display: grid;
  gap: 1rem;
}

.snapshot-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.snapshot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.snapshot-header h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.snapshot-date {
  font-size: 0.875rem;
  color: #666;
}

.snapshot-content {
  display: grid;
  gap: 0.75rem;
}

.snapshot-stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.stat-label {
  font-size: 0.875rem;
  color: #666;
}

.stat-value {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
}

.stat-value.highlight {
  font-size: 1.25rem;
  color: #2563eb;
}

.stat-value.trend-up {
  color: #10b981;
}

.stat-value.trend-down {
  color: #ef4444;
}

.stat-value.trend-neutral {
  color: #666;
}

.snapshot-metadata {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.snapshot-metadata pre {
  background: #1a1a1a;
  color: #00ff00;
  padding: 0.75rem;
  border-radius: 4px;
  font-size: 0.875rem;
  overflow-x: auto;
  margin: 0.5rem 0 0 0;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  background: #f9fafb;
  border-radius: 6px;
}

.empty-state p {
  margin: 0.5rem 0;
}

.empty-hint {
  font-size: 0.875rem;
  color: #999;
  font-style: italic;
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

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-secondary:hover {
  background: #d1d5db;
}

.ml-actions {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.ml-type-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

/* ML Stats Container */
.ml-stats-container {
  margin-top: 1.5rem;
}

/* KPI Grid */
.ml-kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.ml-kpi-card {
  background: white;
  border-radius: 12px;
  padding: 1.25rem;
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.kpi-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
}

.kpi-icon.high { background: linear-gradient(135deg, #3b82f6, #1d4ed8); }
.kpi-icon.danger { background: linear-gradient(135deg, #ef4444, #dc2626); }
.kpi-icon.success { background: linear-gradient(135deg, #10b981, #059669); }
.kpi-icon.info { background: linear-gradient(135deg, #8b5cf6, #7c3aed); }

.kpi-content {
  display: flex;
  flex-direction: column;
}

.kpi-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: #1a1a1a;
  line-height: 1.2;
}

.kpi-label {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 500;
}

/* ML Sections */
.ml-section {
  background: white;
  border-radius: 12px;
  padding: 1.5rem;
  margin-bottom: 1.5rem;
  border: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.section-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.section-desc {
  font-size: 0.875rem;
  color: #6b7280;
  margin: -0.5rem 0 1rem 0;
}

/* ML Tables */
.table-container {
  overflow-x: auto;
}

.ml-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.875rem;
}

.ml-table th {
  background: #f9fafb;
  padding: 0.875rem 1rem;
  text-align: left;
  font-weight: 600;
  color: #374151;
  border-bottom: 2px solid #e5e7eb;
}

.ml-table td {
  padding: 0.875rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  color: #1a1a1a;
}

.ml-table tbody tr:hover {
  background: #f9fafb;
}

.ml-table tfoot td {
  background: #f9fafb;
  font-weight: 600;
}

/* Risk Badges */
.risk-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.risk-badge.high { background: #fef2f2; color: #dc2626; }
.risk-badge.medium { background: #fffbeb; color: #d97706; }
.risk-badge.low { background: #f0fdf4; color: #16a34a; }

/* Status Indicators */
.status-indicator {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
  text-transform: uppercase;
}

.status-indicator.danger { background: #dc2626; color: white; }
.status-indicator.warning { background: #f59e0b; color: white; }
.status-indicator.success { background: #10b981; color: white; }

/* Segment Badges */
.segment-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 20px;
  font-size: 0.75rem;
  font-weight: 600;
}

.segment-badge.champions { background: #fef3c7; color: #92400e; }
.segment-badge.loyal { background: #d1fae5; color: #065f46; }
.segment-badge.potential { background: #e0e7ff; color: #3730a3; }
.segment-badge.new { background: #dbeafe; color: #1e40af; }
.segment-badge.promising { background: #f3e8ff; color: #6b21a8; }
.segment-badge.attention { background: #fff7ed; color: #c2410c; }
.segment-badge.sleep { background: #f3f4f6; color: #4b5563; }
.segment-badge.risk { background: #fee2e2; color: #b91c1c; }
.segment-badge.cantlose { background: #fce7f3; color: #be185d; }
.segment-badge.lost { background: #fef2f2; color: #991b1b; }
.segment-badge.regular { background: #ecfdf5; color: #047857; }
.segment-badge.hibernating { background: #e5e7eb; color: #374151; }
.segment-badge.default { background: #f3f4f6; color: #6b7280; }

/* Priority Badges */
.priority-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 600;
}

.priority-badge.high { background: #dc2626; color: white; }
.priority-badge.medium { background: #f59e0b; color: white; }
.priority-badge.low { background: #6b7280; color: white; }

/* Info Message */
.info-message {
  background: #f0f9ff;
  border: 1px solid #bfdbfe;
  border-radius: 8px;
  padding: 1rem 1.25rem;
}

.info-message p {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  color: #1e40af;
}

.info-message ul {
  margin: 0;
  padding-left: 1.5rem;
}

.info-message li {
  font-size: 0.875rem;
  color: #374151;
  margin: 0.25rem 0;
}

/* Individual Results Table Styles */
.ml-table code {
  background: #f3f4f6;
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
}

.table-note {
  text-align: center;
  font-size: 0.75rem;
  color: #6b7280;
  margin-top: 0.75rem;
  font-style: italic;
}

.ml-result {
  margin-top: 1.5rem;
  padding: 1.5rem;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #bfdbfe;
}

.ml-result h3 {
  font-size: 1.125rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.result-summary p {
  margin: 0.5rem 0;
  font-size: 0.875rem;
  color: #374151;
}

.warning-text {
  color: #d97706;
  font-weight: 500;
}
</style>
