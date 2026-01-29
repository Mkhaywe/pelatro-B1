<template>
  <div class="program-list">
    <div class="page-header">
      <div>
        <h1 class="page-title">Loyalty Programs</h1>
        <p class="page-description">Manage and configure your loyalty programs</p>
      </div>
      <button @click="createNewProgram" class="btn-primary">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <span>Create Program</span>
      </button>
    </div>

    <!-- Filters -->
    <div class="filters-bar">
      <div class="filter-group">
        <label class="filter-label">Status</label>
        <select v-model="filters.status" class="filter-select">
          <option value="">All Status</option>
          <option value="active">Active</option>
          <option value="inactive">Inactive</option>
        </select>
      </div>
      <div class="filter-group">
        <label class="filter-label">Search</label>
        <input 
          v-model="filters.search" 
          type="text" 
          placeholder="Search programs..." 
          class="filter-input"
        />
      </div>
    </div>

    <!-- Programs Table -->
    <div class="table-card">
      <div class="table-header">
        <h3 class="table-title">Programs</h3>
        <span class="table-count">{{ filteredPrograms.length }} program{{ filteredPrograms.length !== 1 ? 's' : '' }}</span>
      </div>
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Status</th>
              <th>Start Date</th>
              <th>End Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="filteredPrograms.length === 0">
              <td colspan="5" class="empty-state-cell">
                <div class="empty-state">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M20 7h-4M4 7h4m0 0v12m0-12a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2m-8 0V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M4 7v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                  <p>No programs found. Create your first program to get started.</p>
                </div>
              </td>
            </tr>
            <tr v-for="program in filteredPrograms" :key="program.id" class="table-row">
              <td>
                <div class="cell-content">
                  <div class="cell-primary">{{ program.name || '-' }}</div>
                  <div v-if="program.description" class="cell-secondary">{{ program.description }}</div>
                </div>
              </td>
              <td>
                <span :class="['status-badge', program.is_active ? 'active' : 'inactive']">
                  <span class="status-dot"></span>
                  {{ program.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td>
                <div class="cell-content">
                  <div class="cell-primary">{{ formatDate(program.start_date) }}</div>
                </div>
              </td>
              <td>
                <div class="cell-content">
                  <div class="cell-primary">{{ formatDate(program.end_date) }}</div>
                </div>
              </td>
              <td>
                <div class="action-buttons">
                  <button @click="viewProgram(program.id)" class="action-btn" title="View">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                  <button @click="editProgram(program.id)" class="action-btn" title="Edit">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
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
import { programsApi } from '@/api/services/programs'
import type { LoyaltyProgram } from '@/types/loyalty'
import { format } from 'date-fns'
import { extractData } from '@/utils/api'

const router = useRouter()
const programs = ref<LoyaltyProgram[]>([])
const filters = ref({ status: '', search: '' })

const filteredPrograms = computed(() => {
  let result = programs.value

  if (filters.value.status) {
    const isActive = filters.value.status === 'active'
    result = result.filter(p => p.is_active === isActive)
  }

  if (filters.value.search) {
    const search = filters.value.search.toLowerCase()
    result = result.filter(p => 
      p.name?.toLowerCase().includes(search) ||
      p.description?.toLowerCase().includes(search)
    )
  }

  return result
})

const formatDate = (date: string | null | undefined) => {
  if (!date) return '-'
  try {
    return format(new Date(date), 'MMM dd, yyyy')
  } catch {
    return '-'
  }
}

const loadPrograms = async () => {
  try {
    const response = await programsApi.getAll()
    programs.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading programs:', error)
    programs.value = []
  }
}

const viewProgram = (id: string) => {
  router.push(`/programs/${id}`)
}

const editProgram = (id: string) => {
  router.push(`/programs/${id}/builder`)
}

const createNewProgram = () => {
  router.push('/programs/new')
}

onMounted(() => {
  loadPrograms()
})
</script>

<style scoped>
.program-list {
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

.status-badge.inactive {
  background: var(--color-error-bg);
  color: var(--color-error-dark);
}

.status-badge.inactive .status-dot {
  background: var(--color-error);
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
