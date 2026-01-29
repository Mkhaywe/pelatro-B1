<template>
  <div class="campaign-list">
    <div class="page-header">
      <div>
        <h1 class="page-title">Campaigns</h1>
        <p class="page-description">Create and manage marketing campaigns</p>
      </div>
      <button @click="createNewCampaign" class="btn-primary">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Create Campaign</span>
      </button>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="filter-group">
        <label class="filter-label">Status</label>
        <select v-model="filters.status" class="filter-select">
          <option value="">All Status</option>
          <option value="draft">Draft</option>
          <option value="active">Active</option>
          <option value="paused">Paused</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Search</label>
        <input 
          v-model="filters.search" 
          type="text" 
          placeholder="Search campaigns..." 
          class="filter-input"
        />
      </div>
    </div>

    <!-- Campaigns Table -->
    <div class="table-card">
      <div class="table-header">
        <h3 class="table-title">Campaigns</h3>
        <span class="table-count">{{ filteredCampaigns.length }} campaign{{ filteredCampaigns.length !== 1 ? 's' : '' }}</span>
      </div>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Segment</th>
              <th>Performance</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredCampaigns.length === 0">
              <td colspan="5" class="empty-state-cell">
                <div class="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <p>No campaigns found. Create your first campaign to get started.</p>
                </div>
              </td>
            </tr>
            <tr v-for="campaign in filteredCampaigns" :key="campaign.id" class="table-row">
              <td>
                <div class="cell-content">
                  <div class="cell-primary">{{ campaign.name || '-' }}</div>
                  <div v-if="campaign.description" class="cell-secondary">{{ campaign.description }}</div>
                </div>
              </td>
              <td>
                <span :class="['status-badge', campaign.status]">
                  <span class="status-dot"></span>
                  {{ formatStatus(campaign.status) }}
                </span>
              </td>
              <td>
                <div class="cell-content">
                  <div class="cell-primary">{{ campaign.segment || 'All' }}</div>
                </div>
              </td>
              <td>
                <button @click="viewPerformance(campaign.id)" class="link-btn">
                  View Metrics
                </button>
              </td>
              <td>
                <div class="action-buttons">
                  <button @click="viewCampaign(campaign.id)" class="action-btn" title="View">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="editCampaign(campaign.id)" class="action-btn" title="Edit">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button 
                    v-if="campaign.status === 'draft'" 
                    @click="activateCampaign(campaign.id)" 
                    class="action-btn action-btn-success"
                    title="Activate"
                  >
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <polyline points="20 6 9 17 4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button 
                    v-if="campaign.status === 'active'" 
                    @click="pauseCampaign(campaign.id)" 
                    class="action-btn action-btn-warning"
                    title="Pause"
                  >
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <rect x="6" y="4" width="4" height="16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <rect x="14" y="4" width="4" height="16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { campaignsApi } from '@/api/services/campaigns'
import type { Campaign } from '@/types/loyalty'
import { extractData } from '@/utils/api'

const router = useRouter()
const campaigns = ref<Campaign[]>([])
const filters = ref({ status: '', search: '' })

const filteredCampaigns = computed(() => {
  let result = campaigns.value

  if (filters.value.status) {
    result = result.filter(c => c.status === filters.value.status)
  }

  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    result = result.filter(c => 
      c.name?.toLowerCase().includes(search) ||
      c.description?.toLowerCase().includes(search)
    )
  }

  return result
})

const formatStatus = (status: string | undefined) => {
  if (!status) return 'Unknown'
  return status.charAt(0).toUpperCase() + status.slice(1).replace('_', ' ')
}

const loadCampaigns = async () => {
  try {
    const response = await campaignsApi.getAll(filters.value)
    campaigns.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading campaigns:', error)
    campaigns.value = []
  }
}

const viewCampaign = (id: string) => {
  router.push(`/campaigns/${id}`)
}

const editCampaign = (id: string) => {
  router.push(`/campaigns/${id}/builder`)
}

const createNewCampaign = () => {
  router.push('/campaigns/new')
}

const activateCampaign = async (id: string) => {
  try {
    await campaignsApi.activate(id)
    loadCampaigns()
  } catch (error) {
    console.error('Error activating campaign:', error)
  }
}

const pauseCampaign = async (id: string) => {
  try {
    await campaignsApi.pause(id)
    loadCampaigns()
  } catch (error) {
    console.error('Error pausing campaign:', error)
  }
}

const viewPerformance = async (id: string) => {
  router.push(`/campaigns/${id}`)
}

onMounted(() => {
  loadCampaigns()
})
</script>

<style scoped>
.campaign-list {
  max-width: 1400px;
  margin: 0 auto;
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

.page-description {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin: 0;
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

.btn-primary:hover {
  background: var(--color-primary-dark);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

/* Filters */
.filters-bar {
  display: flex;
  gap: var(--spacing-4);
  margin-bottom: var(--spacing-6);
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-2);
  min-width: 200px;
}

.filter-label {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.filter-select,
.filter-input {
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all var(--transition-base);
}

.filter-select:focus,
.filter-input:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-50);
}

.filter-input {
  min-width: 250px;
}

/* Table Card */
.table-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  overflow: hidden;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-5) var(--spacing-6);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.table-title {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.table-count {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  font-weight: var(--font-weight-medium);
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: var(--bg-secondary);
}

.data-table th {
  padding: var(--spacing-4) var(--spacing-6);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-color);
}

.data-table td {
  padding: var(--spacing-5) var(--spacing-6);
  border-bottom: 1px solid var(--border-color-light);
}

.table-row {
  transition: background var(--transition-fast);
}

.table-row:hover {
  background: var(--bg-secondary);
}

.cell-content {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-1);
}

.cell-primary {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-primary);
}

.cell-secondary {
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
  line-height: var(--line-height-normal);
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

.status-badge.paused {
  background: var(--color-warning-bg);
  color: var(--color-warning-dark);
}

.status-badge.paused .status-dot {
  background: var(--color-warning);
}

.status-badge.draft {
  background: var(--color-gray-200);
  color: var(--color-gray-700);
}

.status-badge.draft .status-dot {
  background: var(--color-gray-500);
}

.link-btn {
  background: none;
  border: none;
  color: var(--color-primary);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  cursor: pointer;
  padding: 0;
  transition: color var(--transition-fast);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.link-btn:hover {
  color: var(--color-primary-dark);
}

.action-buttons {
  display: flex;
  gap: var(--spacing-2);
}

.action-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.action-btn:hover {
  background: var(--color-primary-50);
  color: var(--color-primary);
  border-color: var(--color-primary-100);
}

.action-btn-success:hover {
  background: var(--color-success-bg);
  color: var(--color-success);
  border-color: var(--color-success);
}

.action-btn-warning:hover {
  background: var(--color-warning-bg);
  color: var(--color-warning);
  border-color: var(--color-warning);
}

.action-btn svg {
  width: 16px;
  height: 16px;
}

.empty-state-cell {
  padding: var(--spacing-12) !important;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--spacing-3);
  color: var(--text-tertiary);
}

.empty-state svg {
  width: 48px;
  height: 48px;
  opacity: 0.5;
}

.empty-state p {
  font-size: var(--font-size-sm);
  text-align: center;
  max-width: 400px;
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .filters-bar {
    flex-direction: column;
  }
  
  .filter-group {
    min-width: 100%;
  }
  
  .filter-input {
    min-width: 100%;
  }
  
  .table-container {
    overflow-x: scroll;
  }
}
</style>
