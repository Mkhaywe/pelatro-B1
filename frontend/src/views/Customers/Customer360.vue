<template>
  <div class="customer-360">
    <div v-if="loading" class="loading">
      <div class="loading-spinner"></div>
      <p>Loading customer data...</p>
    </div>
    
    <div v-else-if="customerId" class="customer-content">
      <!-- Header -->
      <div class="page-header">
        <div>
          <h1 class="page-title">Customer 360</h1>
          <p class="customer-id">Customer ID: {{ customerId }}</p>
        </div>
        <div class="header-actions">
          <input 
            v-model="searchCustomerId" 
            placeholder="Search by Customer ID"
            class="search-input"
            @keyup.enter="searchCustomer"
          />
          <button @click="searchCustomer" class="btn-primary">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M21 21l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Search</span>
          </button>
        </div>
      </div>

      <!-- Customer Overview -->
      <div class="overview-section">
        <div class="overview-card">
          <div class="card-header">
            <h2>Account Overview</h2>
            <button @click="loadCustomerData" class="btn-secondary" :disabled="loading">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Refresh</span>
            </button>
          </div>
          <div v-if="accounts.length === 0" class="empty-state">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <circle cx="12" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <p>No loyalty accounts found for this customer.</p>
          </div>
          <div v-else class="accounts-grid">
            <div v-for="account in accounts" :key="account.id" class="account-card">
              <div class="account-header">
                <h3>{{ getProgramName(account) }}</h3>
                <span class="status-badge" :class="account.status || 'active'">
                  <span class="status-dot"></span>
                  {{ account.status || 'active' }}
                </span>
              </div>
              <div class="account-stats">
                <div class="stat">
                  <span class="stat-label">Points Balance</span>
                  <span class="stat-value">{{ formatNumber(account.points_balance || 0) }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Tier</span>
                  <span class="stat-value">{{ getTierName(account) }}</span>
                </div>
                <div class="stat">
                  <span class="stat-label">Account ID</span>
                  <span class="stat-value-small">{{ account.id?.toString().substring(0, 8) }}...</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- ML Predictions Section -->
      <div class="ml-section">
        <div class="section-header">
          <h2>AI Insights & Recommendations</h2>
          <button @click="loadMLPredictions" class="btn-secondary" :disabled="mlLoading">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Refresh Predictions</span>
          </button>
        </div>
        
        <div class="ml-cards">
          <!-- Churn Risk -->
          <div class="ml-card">
            <div class="ml-card-header">
              <h3>Churn Risk</h3>
              <button @click="loadChurn" class="icon-btn-sm" :disabled="churnLoading" title="Refresh">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <ChurnGauge 
              v-if="churnPrediction && !churnError"
              :probability="churnPrediction.risk_score || churnPrediction.churn_probability || 0"
              :details="{
                confidence: churnPrediction.confidence,
                reasons: churnPrediction.reasons
              }"
            />
            <div v-else-if="churnLoading" class="loading-state">
              <div class="spinner-small"></div>
              <p>Calculating churn risk...</p>
            </div>
            <div v-else-if="churnError" class="error-state">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <p class="error-title">Unable to calculate churn risk</p>
              <p class="error-detail">{{ formatMLError(churnError) }}</p>
              <button @click="loadChurn" class="btn-link">Try again</button>
            </div>
            <div v-else class="empty-state-small">
              <p>No churn prediction available</p>
              <button @click="loadChurn" class="btn-link">Calculate</button>
            </div>
          </div>

          <!-- NBO Offers -->
          <div class="ml-card">
            <div class="ml-card-header">
              <h3>Next Best Offers</h3>
              <button @click="loadNBO" class="icon-btn-sm" :disabled="nboLoading" title="Refresh">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <NBOOffers 
              v-if="nboPredictions.length > 0 && !nboError"
              :offers="nboPredictions"
              :loading="nboLoading"
            />
            <div v-else-if="nboLoading" class="loading-state">
              <div class="spinner-small"></div>
              <p>Calculating recommendations...</p>
            </div>
            <div v-else-if="nboError" class="error-state">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <p class="error-title">Unable to load offers</p>
              <p class="error-detail">{{ formatMLError(nboError) }}</p>
              <button @click="loadNBO" class="btn-link">Try again</button>
            </div>
            <div v-else class="empty-state-small">
              <p>No offers available</p>
              <p class="help-text">Configure DWH and deploy ML models to enable predictions.</p>
              <button @click="loadNBO" class="btn-link">Calculate</button>
            </div>
          </div>

          <!-- RFM Analysis -->
          <div class="ml-card">
            <div class="ml-card-header">
              <h3>RFM Analysis</h3>
              <button @click="loadRFM" class="icon-btn-sm" :disabled="rfmLoading" title="Refresh">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
            <RFMChart 
              v-if="rfmScores && !rfmError"
              :rfm-data="rfmScores"
              :loading="rfmLoading"
            />
            <div v-else-if="rfmLoading" class="loading-state">
              <div class="spinner-small"></div>
              <p>Calculating RFM scores...</p>
            </div>
            <div v-else-if="rfmError" class="error-state">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="8" x2="12" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="16" x2="12.01" y2="16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <p class="error-title">Unable to calculate RFM</p>
              <p class="error-detail">{{ formatMLError(rfmError) }}</p>
              <button @click="loadRFM" class="btn-link">Try again</button>
            </div>
            <div v-else class="empty-state-small">
              <p>No RFM data available</p>
              <button @click="loadRFM" class="btn-link">Calculate</button>
            </div>
          </div>
        </div>
      </div>

      <!-- Transaction History -->
      <div class="section">
        <div class="section-header">
          <h2>Transaction History</h2>
          <div class="section-actions">
            <input 
              v-model="transactionFilters.search" 
              placeholder="Search transactions..."
              class="search-input"
            />
            <select v-model="transactionFilters.type" class="filter-select">
              <option value="">All Types</option>
              <option value="earn">Earn</option>
              <option value="redeem">Redeem</option>
              <option value="adjust">Adjust</option>
            </select>
            <button @click="exportTransactions" class="btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="7 10 12 15 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <line x1="12" y1="15" x2="12" y2="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Export CSV</span>
            </button>
            <button @click="loadTransactions" class="btn-secondary" :disabled="loadingTransactions">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>
        
        <!-- Transaction Chart -->
        <div v-if="transactions.length > 0" class="chart-container">
          <ChartCard title="Points Balance Over Time" subtitle="Transaction history visualization">
            <LineChart
              :data="chartData"
              x-key="date"
              :lines="[
                { dataKey: 'balance', name: 'Points Balance', stroke: '#6366f1' },
                { dataKey: 'earned', name: 'Points Earned', stroke: '#10b981' },
                { dataKey: 'redeemed', name: 'Points Redeemed', stroke: '#ef4444' }
              ]"
              :x-formatter="(val) => formatDateShort(val)"
            />
          </ChartCard>
        </div>
        
        <div v-if="filteredTransactions.length === 0 && !loadingTransactions" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="14 2 14 8 20 8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="16" y1="13" x2="8" y2="13" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="16" y1="17" x2="8" y2="17" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="10 9 9 9 8 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No transactions found</p>
        </div>
        <div v-else-if="loadingTransactions" class="loading-state">
          <div class="spinner-small"></div>
          <p>Loading transactions...</p>
        </div>
        <div v-else class="transactions-table">
          <table class="data-table">
            <thead>
              <tr>
                <th>Date</th>
                <th>Type</th>
                <th>Points</th>
                <th>Description</th>
                <th>Program</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="tx in filteredTransactions" :key="tx.id">
                <td>{{ formatDate(tx.created_at) }}</td>
                <td>
                  <span class="tx-type" :class="tx.transaction_type || tx.type">
                    {{ (tx.transaction_type || tx.type || 'unknown').toUpperCase() }}
                  </span>
                </td>
                <td>
                  <span :class="(tx.amount || tx.points || 0) > 0 ? 'points-positive' : 'points-negative'">
                    {{ (tx.amount || tx.points || 0) > 0 ? '+' : '' }}{{ formatNumber(Math.abs(tx.amount || tx.points || 0)) }}
                  </span>
                </td>
                <td>{{ tx.description || tx.reason || '-' }}</td>
                <td>{{ getTransactionProgramName(tx) }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- Active Promotions -->
      <div class="section">
        <div class="section-header">
          <h2>Active Promotions</h2>
          <button @click="loadPromotions" class="btn-secondary" :disabled="loadingPromotions">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Refresh</span>
          </button>
        </div>
        <div v-if="promotions.length === 0 && !loadingPromotions" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M20 7h-4M4 7h4m0 0v12m0-12a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2m-8 0V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M4 7v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No active promotions for this customer</p>
        </div>
        <div v-else-if="loadingPromotions" class="loading-state">
          <div class="spinner-small"></div>
          <p>Loading promotions...</p>
        </div>
        <div v-else class="promotions-grid">
          <div v-for="promo in promotions" :key="promo.id" class="promo-card">
            <h4>{{ promo.name }}</h4>
            <p>{{ promo.description || 'No description' }}</p>
            <div class="promo-meta">
              <span>
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Valid until: {{ formatDate(promo.end_date) }}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="search-prompt">
      <div class="prompt-content">
        <h1>Customer 360</h1>
        <p>Enter a Customer ID to view their complete profile and insights</p>
        <div class="search-box">
          <input 
            v-model="searchCustomerId" 
            placeholder="Customer ID (UUID)"
            class="search-input-large"
            @keyup.enter="searchCustomer"
          />
          <button @click="searchCustomer" class="btn-primary-large">
            <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
              <circle cx="11" cy="11" r="8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              <path d="M21 21l-4.35-4.35" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            <span>Search</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { programsApi } from '@/api/services/programs'
import { mlApi } from '@/api/services/ml'
import { customersApi } from '@/api/services/customers'
import ChartCard from '@/components/ChartCard.vue'
import LineChart from '@/components/LineChart.vue'
import ChurnGauge from '@/components/ChurnGauge.vue'
import NBOOffers from '@/components/NBOOffers.vue'
import RFMChart from '@/components/RFMChart.vue'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()

const route = useRoute()
const router = useRouter()

const customerId = ref<string | null>(route.params.id as string || null)
const searchCustomerId = ref('')
const loading = ref(false)
const loadingTransactions = ref(false)
const loadingPromotions = ref(false)
const mlLoading = ref(false)

// Account data
const accounts = ref<any[]>([])
const programsMap = ref<Record<string, any>>({})

// ML Predictions
const nboPredictions = ref<any[]>([])
const nboLoading = ref(false)
const nboError = ref<string | null>(null)

const churnPrediction = ref<any | null>(null)
const churnLoading = ref(false)
const churnError = ref<string | null>(null)

const rfmScores = ref<any | null>(null)
const rfmLoading = ref(false)
const rfmError = ref<string | null>(null)

// Transactions
const transactions = ref<any[]>([])

// Promotions
const promotions = ref<any[]>([])

// Transaction Filters
const transactionFilters = ref({
  search: '',
  type: ''
})

const filteredTransactions = computed(() => {
  let filtered = transactions.value
  
  if (transactionFilters.value.type) {
    filtered = filtered.filter(tx => {
      const txType = tx.transaction_type || tx.type
      return txType === transactionFilters.value.type
    })
  }
  
  if (transactionFilters.value.search) {
    const search = transactionFilters.value.search.toLowerCase()
    filtered = filtered.filter(tx => 
      (tx.description || '').toLowerCase().includes(search) ||
      (getTransactionProgramName(tx) || '').toLowerCase().includes(search)
    )
  }
  
  return filtered
})

const chartData = computed(() => {
  if (transactions.value.length === 0) return []
  
  // Sort transactions by date
  const sorted = [...transactions.value].sort((a, b) => {
    const dateA = new Date(a.created_at).getTime()
    const dateB = new Date(b.created_at).getTime()
    return dateA - dateB
  })
  
  // Calculate running balance and group by date
  let runningBalance = 0
  const dailyData: Record<string, { date: string, balance: number, earned: number, redeemed: number }> = {}
  
  sorted.forEach(tx => {
    const date = new Date(tx.created_at).toISOString().split('T')[0]
    const amount = tx.amount || tx.points || 0
    const type = tx.transaction_type || tx.type || 'earn'
    
    if (!dailyData[date]) {
      dailyData[date] = {
        date,
        balance: runningBalance,
        earned: 0,
        redeemed: 0
      }
    }
    
    if (type === 'earn' || type === 'adjust') {
      runningBalance += amount
      dailyData[date].earned += amount
    } else if (type === 'redeem') {
      runningBalance -= amount
      dailyData[date].redeemed += amount
    }
    
    dailyData[date].balance = runningBalance
  })
  
  return Object.values(dailyData)
})

const formatMLError = (error: string) => {
  if (error.includes('Dimension mismatch')) {
    return 'ML model configuration issue. Please ensure DWH is configured and models are properly trained with 10 features.'
  }
  if (error.includes('not available') || error.includes('not found')) {
    return 'ML models not available. Please configure DWH and deploy trained models.'
  }
  if (error.includes('DWH')) {
    return 'DWH connection issue. Please check DWH configuration.'
  }
  return error.length > 100 ? error.substring(0, 100) + '...' : error
}

const getProgramName = (account: any) => {
  if (account.program_name) return account.program_name
  if (account.program && typeof account.program === 'object') {
    return account.program.name || 'Unknown Program'
  }
  if (account.program && programsMap.value[account.program]) {
    return programsMap.value[account.program].name || 'Unknown Program'
  }
  return 'Unknown Program'
}

const getTierName = (account: any) => {
  if (account.tier_name) return account.tier_name
  if (account.tier && typeof account.tier === 'object') {
    return account.tier.name || 'None'
  }
  return 'None'
}

const getTransactionProgramName = (tx: any) => {
  // Try multiple possible paths for program name
  if (tx.program_name) return tx.program_name
  if (tx.program && typeof tx.program === 'object') {
    return tx.program.name || 'Unknown'
  }
  if (tx.account) {
    if (typeof tx.account === 'object') {
      if (tx.account.program_name) return tx.account.program_name
      if (tx.account.program && typeof tx.account.program === 'object') {
        return tx.account.program.name || 'Unknown'
      }
      if (tx.account.program && programsMap.value[tx.account.program]) {
        return programsMap.value[tx.account.program].name || 'Unknown'
      }
    }
  }
  return 'Unknown'
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

const searchCustomer = () => {
  if (!searchCustomerId.value.trim()) {
    showToast('Please enter a Customer ID', 'warning')
    return
  }
  customerId.value = searchCustomerId.value.trim()
  router.push(`/customers/${customerId.value}`)
  loadCustomerData()
}

const loadCustomerData = async () => {
  if (!customerId.value) return
  
  loading.value = true
  
  try {
    // Load programs map for reference
    const programsResponse = await programsApi.getAll()
    const programsList = extractData(programsResponse.data)
    programsMap.value = {}
    programsList.forEach((p: any) => {
      programsMap.value[p.id] = p
    })
    
    // Load accounts
    const accountsResponse = await customersApi.getAccounts(customerId.value)
    accounts.value = Array.isArray(accountsResponse.data) 
      ? accountsResponse.data 
      : extractData(accountsResponse.data)
    
    // Load transactions and promotions in parallel
    await Promise.all([
      loadTransactions(),
      loadPromotions()
    ])
    
    // Load ML predictions (don't block on these)
    loadMLPredictions()
    
  } catch (error: any) {
    console.error('Error loading customer data:', error)
    showToast('Error loading customer data: ' + (error.response?.data?.detail || error.message), 'error')
  } finally {
    loading.value = false
  }
}

const loadTransactions = async () => {
  if (!customerId.value) return
  
  loadingTransactions.value = true
  try {
    const transactionsResponse = await customersApi.getTransactions(customerId.value)
    const txData = Array.isArray(transactionsResponse.data) 
      ? transactionsResponse.data 
      : extractData(transactionsResponse.data)
    
    transactions.value = txData.map((tx: any) => ({
      ...tx,
      amount: tx.amount || tx.points || 0,
      points: tx.amount || tx.points || 0,
    }))
  } catch (error: any) {
    console.error('Error loading transactions:', error)
    showToast('Error loading transactions', 'error')
    transactions.value = []
  } finally {
    loadingTransactions.value = false
  }
}

const loadPromotions = async () => {
  if (!customerId.value) return
  
  loadingPromotions.value = true
  try {
    const promotionsResponse = await customersApi.getPromotions(customerId.value)
    promotions.value = Array.isArray(promotionsResponse.data) 
      ? promotionsResponse.data 
      : extractData(promotionsResponse.data)
  } catch (error: any) {
    console.error('Error loading promotions:', error)
    promotions.value = []
  } finally {
    loadingPromotions.value = false
  }
}

const loadMLPredictions = async () => {
  if (!customerId.value) return
  mlLoading.value = true
  
  await Promise.all([
    loadNBO(),
    loadChurn(),
    loadRFM()
  ])
  
  mlLoading.value = false
}

const loadNBO = async () => {
  if (!customerId.value) return
  
  nboLoading.value = true
  nboError.value = null
  
  try {
    const response = await mlApi.predictNBO(customerId.value)
    
    // Handle different response formats
    if (response.data.error) {
      nboError.value = response.data.error
      nboPredictions.value = []
      return
    }
    
    // Transform backend response to frontend format
    if (response.data.offers && Array.isArray(response.data.offers)) {
      nboPredictions.value = response.data.offers
    } else if (response.data.offer_scores && Array.isArray(response.data.offer_scores)) {
      // Fallback: use offer_scores array
      nboPredictions.value = response.data.offer_scores.map((score: number, idx: number) => ({
        offer_id: idx,
        offer_name: `Offer ${idx + 1}`,
        category: 'general',
        probability: score
      })).sort((a: any, b: any) => b.probability - a.probability).slice(0, 5)
    } else {
      nboPredictions.value = []
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to load NBO predictions'
    nboError.value = errorMsg
    nboPredictions.value = []
    console.error('Error loading NBO:', error)
  } finally {
    nboLoading.value = false
  }
}

const loadChurn = async () => {
  if (!customerId.value) return
  
  churnLoading.value = true
  churnError.value = null
  
  try {
    const response = await mlApi.predictChurn(customerId.value)
    
    if (response.data.error) {
      churnError.value = response.data.error
      churnPrediction.value = null
      return
    }
    
    churnPrediction.value = {
      risk_score: response.data.churn_probability || 0,
      churn_probability: response.data.churn_probability || 0,
      churn_risk: response.data.churn_risk || 'low',
      confidence: response.data.confidence,
      reasons: response.data.reasons || []
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to load churn prediction'
    churnError.value = errorMsg
    churnPrediction.value = null
    console.error('Error loading churn:', error)
  } finally {
    churnLoading.value = false
  }
}

const loadRFM = async () => {
  if (!customerId.value) return
  
  rfmLoading.value = true
  rfmError.value = null
  
  try {
    const response = await mlApi.calculateRFM(customerId.value)
    
    if (response.data.error) {
      rfmError.value = response.data.error
      rfmScores.value = null
      return
    }
    
    rfmScores.value = {
      recency_score: response.data.r_score || 0,
      frequency_score: response.data.f_score || 0,
      monetary_score: response.data.m_score || 0,
      recency_days: response.data.recency || 0,
      frequency_count: response.data.frequency || 0,
      monetary_value: response.data.monetary || 0,
      segment: response.data.rfm_segment || '000'
    }
  } catch (error: any) {
    const errorMsg = error.response?.data?.error || error.response?.data?.detail || error.message || 'Failed to load RFM scores'
    rfmError.value = errorMsg
    rfmScores.value = null
    console.error('Error loading RFM:', error)
  } finally {
    rfmLoading.value = false
  }
}

const exportTransactions = () => {
  const csv = [
    ['Date', 'Type', 'Points', 'Description', 'Program'],
    ...filteredTransactions.value.map(tx => [
      formatDate(tx.created_at),
      tx.transaction_type || tx.type || 'unknown',
      tx.amount || tx.points || 0,
      tx.description || '',
      getTransactionProgramName(tx)
    ])
  ].map(row => row.join(',')).join('\n')
  
  const blob = new Blob([csv], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `transactions-${customerId.value}-${new Date().toISOString().split('T')[0]}.csv`
  a.click()
  URL.revokeObjectURL(url)
  showToast('Transactions exported successfully', 'success')
}

watch(() => route.params.id, (newId) => {
  if (newId) {
    customerId.value = newId as string
    searchCustomerId.value = newId as string
    loadCustomerData()
  }
})

onMounted(() => {
  if (customerId.value) {
    searchCustomerId.value = customerId.value
    loadCustomerData()
  }
})
</script>

<style scoped>
.customer-360 {
  max-width: 1600px;
  margin: 0 auto;
  padding: var(--spacing-8);
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  gap: var(--spacing-4);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid var(--color-gray-200);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-6);
  gap: var(--spacing-4);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.customer-id {
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
  font-family: var(--font-family-mono);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
}

.search-input {
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  min-width: 250px;
  transition: all var(--transition-base);
}

.search-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-50);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-5);
  background: var(--color-primary);
  color: white;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.search-prompt {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 60vh;
}

.prompt-content {
  text-align: center;
  max-width: 600px;
  padding: var(--spacing-8);
}

.prompt-content h1 {
  font-size: var(--font-size-4xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-4);
}

.prompt-content p {
  font-size: var(--font-size-lg);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-8);
}

.search-box {
  display: flex;
  gap: var(--spacing-3);
  align-items: stretch;
}

.search-input-large {
  flex: 1;
  padding: var(--spacing-4) var(--spacing-5);
  border: 2px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  transition: all var(--transition-base);
}

.search-input-large:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 4px var(--color-primary-50);
}

.btn-primary-large {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-4) var(--spacing-6);
  background: var(--color-primary);
  color: white;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-md);
}

.btn-primary-large:hover {
  background: var(--color-primary-dark);
  box-shadow: var(--shadow-lg);
  transform: translateY(-2px);
}

.btn-primary-large svg {
  width: 20px;
  height: 20px;
}

.overview-section {
  margin-bottom: var(--spacing-8);
}

.overview-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
}

.card-header h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
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

.accounts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: var(--spacing-4);
  margin-top: var(--spacing-4);
}

.account-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
}

.account-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-color-dark);
}

.account-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
}

.account-header h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.status-badge.active {
  background: var(--color-success-bg);
  color: var(--color-success-dark);
}

.status-badge.active .status-dot {
  background: var(--color-success);
}

.account-stats {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-3);
}

.stat {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-2) 0;
  border-bottom: 1px solid var(--border-color-light);
}

.stat:last-child {
  border-bottom: none;
}

.stat-label {
  color: var(--text-tertiary);
  font-size: var(--font-size-sm);
}

.stat-value {
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  font-size: var(--font-size-base);
}

.stat-value-small {
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  font-size: var(--font-size-xs);
  font-family: var(--font-family-mono);
}

.ml-section {
  margin-bottom: var(--spacing-8);
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
}

.section-header h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.ml-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--spacing-6);
}

.ml-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  min-height: 300px;
}

.ml-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-4);
}

.ml-card-header h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.icon-btn-sm {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.icon-btn-sm:hover:not(:disabled) {
  background: var(--color-primary-50);
  color: var(--color-primary);
  border-color: var(--color-primary-100);
}

.icon-btn-sm:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.icon-btn-sm svg {
  width: 16px;
  height: 16px;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-8);
  gap: var(--spacing-3);
  color: var(--text-tertiary);
}

.spinner-small {
  width: 32px;
  height: 32px;
  border: 3px solid var(--color-gray-200);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-6);
  gap: var(--spacing-3);
  text-align: center;
}

.error-state svg {
  width: 48px;
  height: 48px;
  color: var(--color-error);
  opacity: 0.7;
}

.error-title {
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.error-detail {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin: 0;
  max-width: 300px;
}

.btn-link {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  padding: var(--spacing-2) 0;
  text-decoration: underline;
  text-underline-offset: 2px;
}

.btn-link:hover {
  color: var(--color-primary-dark);
}

.empty-state-small {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-6);
  gap: var(--spacing-2);
  text-align: center;
  color: var(--text-tertiary);
}

.help-text {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin: 0;
}

.section {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  margin-bottom: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.section h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-6);
}

.section-actions {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
  flex-wrap: wrap;
}

.filter-select {
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.chart-container {
  margin-bottom: var(--spacing-6);
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
  text-align: center;
}

.transactions-table {
  overflow-x: auto;
  margin-top: var(--spacing-4);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: var(--bg-secondary);
}

.data-table th {
  padding: var(--spacing-4) var(--spacing-5);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-color);
}

.data-table td {
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
  font-size: var(--font-size-sm);
}

.tx-type {
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: uppercase;
}

.tx-type.earn {
  background: var(--color-success-bg);
  color: var(--color-success-dark);
}

.tx-type.redeem {
  background: var(--color-error-bg);
  color: var(--color-error-dark);
}

.tx-type.adjust {
  background: var(--color-info-bg);
  color: var(--color-info-dark);
}

.points-positive {
  color: var(--color-success);
  font-weight: var(--font-weight-semibold);
}

.points-negative {
  color: var(--color-error);
  font-weight: var(--font-weight-semibold);
}

.promotions-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: var(--spacing-4);
  margin-top: var(--spacing-4);
}

.promo-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
}

.promo-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-color-dark);
}

.promo-card h4 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-2) 0;
}

.promo-card p {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin: 0 0 var(--spacing-3) 0;
  line-height: var(--line-height-relaxed);
}

.promo-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  margin-top: var(--spacing-3);
  padding-top: var(--spacing-3);
  border-top: 1px solid var(--border-color-light);
}

.promo-meta svg {
  width: 14px;
  height: 14px;
}

/* Responsive */
@media (max-width: 768px) {
  .customer-360 {
    padding: var(--spacing-4);
  }
  
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .ml-cards {
    grid-template-columns: 1fr;
  }
  
  .accounts-grid {
    grid-template-columns: 1fr;
  }
  
  .section-actions {
    flex-direction: column;
    align-items: stretch;
  }
  
  .search-input,
  .filter-select {
    width: 100%;
  }
}
</style>
