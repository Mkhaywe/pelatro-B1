<template>
  <div class="partner-detail">
    <div v-if="loading" class="loading">Loading partner...</div>
    
    <div v-else-if="partner" class="partner-content">
      <!-- Header -->
      <div class="page-header">
        <div class="header-left">
          <h1>{{ partner.name }}</h1>
          <p class="subtitle">{{ partner.description || 'No description' }}</p>
          <div class="partner-meta">
            <span class="type-badge" :class="partner.partner_type">
              {{ getPartnerTypeLabel(partner.partner_type) }}
            </span>
            <span class="status-badge" :class="partner.is_active ? 'active' : 'inactive'">
              {{ partner.is_active ? 'Active' : 'Inactive' }}
            </span>
          </div>
        </div>
        <div class="header-actions">
          <button @click="editPartner" class="btn-secondary">Edit Partner</button>
          <button @click="generateApiKey" class="btn-secondary" v-if="!partner.api_key">Generate API Key</button>
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
        <!-- Overview -->
        <div v-if="activeTab === 'overview'" class="tab-panel">
          <div class="info-grid">
            <div class="info-card">
              <h3>Contact Information</h3>
              <div class="info-item">
                <label>Email:</label>
                <span>{{ partner.contact_email || 'Not set' }}</span>
              </div>
              <div class="info-item">
                <label>Phone:</label>
                <span>{{ partner.contact_phone || 'Not set' }}</span>
              </div>
            </div>

            <div class="info-card">
              <h3>Settlement</h3>
              <div class="info-item">
                <label>Settlement Frequency:</label>
                <span>{{ getSettlementFrequencyLabel(partner.settlement_frequency) }}</span>
              </div>
              <div class="info-item">
                <label>API Key:</label>
                <code class="api-key">{{ partner.api_key ? maskApiKey(partner.api_key) : 'Not generated' }}</code>
                <button v-if="partner.api_key" @click="copyApiKey" class="btn-link btn-sm">Copy</button>
              </div>
            </div>
          </div>
        </div>

        <!-- Programs -->
        <div v-if="activeTab === 'programs'" class="tab-panel">
          <div class="section-header">
            <h3>Partner Programs</h3>
            <button @click="showAddProgramModal = true" class="btn-primary">+ Add Program</button>
          </div>

          <div v-if="partnerPrograms.length === 0" class="empty-state">
            No programs configured for this partner.
          </div>

          <div v-else class="programs-list">
            <div v-for="program in partnerPrograms" :key="program.id" class="program-card">
              <div class="program-header">
                <h4>{{ program.program?.name || 'Program' }}</h4>
                <span class="status-badge" :class="program.is_active ? 'active' : 'inactive'">
                  {{ program.is_active ? 'Active' : 'Inactive' }}
                </span>
              </div>
              <div class="program-details">
                <div class="detail-item">
                  <label>Earn Rate:</label>
                  <span>{{ program.earn_rate || 0 }}%</span>
                </div>
                <div class="detail-item">
                  <label>Burn Rate:</label>
                  <span>{{ program.burn_rate || 0 }}%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Coalitions -->
        <div v-if="activeTab === 'coalitions'" class="tab-panel">
          <div class="section-header">
            <h3>Coalitions</h3>
            <button @click="showAddCoalitionModal = true" class="btn-primary">+ Join Coalition</button>
          </div>

          <div v-if="coalitions.length === 0" class="empty-state">
            This partner is not part of any coalitions.
          </div>

          <div v-else class="coalitions-list">
            <div v-for="coalition in coalitions" :key="coalition.id" class="coalition-card">
              <h4>{{ coalition.name }}</h4>
              <p>{{ coalition.description || 'No description' }}</p>
              <div class="coalition-features">
                <span class="feature-badge" v-if="coalition.shared_points">
                  Shared Points
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Settlements -->
        <div v-if="activeTab === 'settlements'" class="tab-panel">
          <div class="section-header">
            <h3>Settlement History</h3>
            <button @click="createSettlement" class="btn-primary">+ Create Settlement</button>
          </div>

          <div v-if="settlements.length === 0" class="empty-state">
            No settlements found.
          </div>

          <div v-else class="settlements-table">
            <table class="data-table">
              <thead>
                <tr>
                  <th>Period</th>
                  <th>Program</th>
                  <th>Points Issued</th>
                  <th>Points Redeemed</th>
                  <th>Amount</th>
                  <th>Status</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="settlement in settlements" :key="settlement.id">
                  <td>{{ formatDateRange(settlement.period_start, settlement.period_end) }}</td>
                  <td>{{ settlement.program?.name || '-' }}</td>
                  <td>{{ settlement.points_issued || 0 }}</td>
                  <td>{{ settlement.points_redeemed || 0 }}</td>
                  <td>${{ formatNumber(settlement.settlement_amount || 0) }}</td>
                  <td>
                    <span class="status-badge" :class="settlement.status">
                      {{ settlement.status }}
                    </span>
                  </td>
                  <td>
                    <button @click="viewSettlement(settlement.id)" class="btn-link">View</button>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="error-state">
      <h2>Partner not found</h2>
      <button @click="$router.push('/partners')" class="btn-primary">Back to Partners</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { partnersApi } from '@/api/services/partners'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'

const route = useRoute()
const router = useRouter()

const partner = ref<any>(null)
const partnerPrograms = ref<any[]>([])
const coalitions = ref<any[]>([])
const settlements = ref<any[]>([])
const loading = ref(true)
const activeTab = ref('overview')
const showAddProgramModal = ref(false)
const showAddCoalitionModal = ref(false)

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'programs', label: 'Programs' },
  { id: 'coalitions', label: 'Coalitions' },
  { id: 'settlements', label: 'Settlements' },
]

const loadPartner = async () => {
  loading.value = true
  try {
    const response = await partnersApi.getById(route.params.id as string)
    partner.value = response.data
    
    // Load related data
    await Promise.all([
      loadPartnerPrograms(),
      loadCoalitions(),
      loadSettlements()
    ])
  } catch (error) {
    console.error('Error loading partner:', error)
    partner.value = null
  } finally {
    loading.value = false
  }
}

const loadPartnerPrograms = async () => {
  try {
    const response = await partnersApi.getPrograms(route.params.id as string)
    partnerPrograms.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading partner programs:', error)
    partnerPrograms.value = []
  }
}

const loadCoalitions = async () => {
  try {
    const response = await partnersApi.getCoalitions(route.params.id as string)
    coalitions.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading coalitions:', error)
    coalitions.value = []
  }
}

const loadSettlements = async () => {
  try {
    const response = await partnersApi.getSettlements(route.params.id as string)
    settlements.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading settlements:', error)
    settlements.value = []
  }
}

const getPartnerTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    'coalition': 'Coalition Partner',
    'merchant': 'Merchant Partner',
    'affiliate': 'Affiliate',
  }
  return labels[type] || type
}

const getSettlementFrequencyLabel = (freq: string) => {
  const labels: Record<string, string> = {
    'daily': 'Daily',
    'weekly': 'Weekly',
    'monthly': 'Monthly',
  }
  return labels[freq] || freq
}

const maskApiKey = (key: string) => {
  if (!key) return 'Not set'
  return key.substring(0, 8) + '••••••••' + key.substring(key.length - 4)
}

const copyApiKey = async () => {
  if (partner.value?.api_key) {
    await navigator.clipboard.writeText(partner.value.api_key)
    alert('API key copied to clipboard')
  }
}

const generateApiKey = async () => {
  try {
    const response = await partnersApi.generateApiKey(route.params.id as string)
    partner.value.api_key = response.data.api_key
    alert('API key generated successfully')
  } catch (error: any) {
    alert('Error generating API key: ' + (error.response?.data?.error || error.message))
  }
}

const editPartner = () => {
  router.push(`/partners/${route.params.id}/edit`)
}

const createSettlement = () => {
  // TODO: Open settlement creation modal
  alert('Settlement creation coming soon')
}

const viewSettlement = (id: string) => {
  // TODO: Open settlement detail
  alert('Settlement detail coming soon')
}

const formatDateRange = (start: string, end: string) => {
  try {
    return `${format(new Date(start), 'MMM dd')} - ${format(new Date(end), 'MMM dd, yyyy')}`
  } catch {
    return `${start} - ${end}`
  }
}

const formatNumber = (num: number) => {
  return new Intl.NumberFormat('en-US').format(num)
}

onMounted(() => {
  loadPartner()
})
</script>

<style scoped>
.partner-detail {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
}

.loading {
  text-align: center;
  padding: 3rem;
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
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: #666;
  margin: 0 0 1rem 0;
}

.partner-meta {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.type-badge,
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

.type-badge.coalition {
  background: #dbeafe;
  color: #1e40af;
}

.type-badge.merchant {
  background: #fef3c7;
  color: #92400e;
}

.type-badge.affiliate {
  background: #e9d5ff;
  color: #6b21a8;
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
  margin-bottom: -2px;
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

.info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.info-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.info-card h3 {
  font-size: 1.125rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem 0;
  border-bottom: 1px solid #e0e0e0;
}

.info-item:last-child {
  border-bottom: none;
}

.info-item label {
  font-weight: 500;
  color: #666;
}

.api-key {
  font-family: monospace;
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
  background: #f9fafb;
  border-radius: 6px;
}

.programs-list,
.coalitions-list {
  display: grid;
  gap: 1rem;
}

.program-card,
.coalition-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.program-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.program-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
}

.settlements-table {
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
  border-bottom: 2px solid #e0e0e0;
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.btn-primary,
.btn-secondary,
.btn-link {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-secondary {
  background: #e5e7eb;
  color: #374151;
}

.btn-link {
  background: none;
  color: #2563eb;
  text-decoration: underline;
  padding: 0.5rem;
}
</style>

