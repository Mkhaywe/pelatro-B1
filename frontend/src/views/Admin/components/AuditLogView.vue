<template>
  <div class="audit-log-view">
    <div class="section-header">
      <h2>Audit Log</h2>
      <p class="section-description">
        View system activity and audit trail.
      </p>
    </div>

    <div class="filters">
      <input 
        v-model="searchQuery" 
        type="text"
        placeholder="Search audit logs..."
        class="search-input"
      />
      <select v-model="filterAction" class="filter-select">
        <option value="">All Actions</option>
        <option value="CREATE">Create</option>
        <option value="UPDATE">Update</option>
        <option value="DELETE">Delete</option>
        <option value="SEGMENT_RECALCULATED">Segment Recalculated</option>
        <option value="CAMPAIGN_ACTIVATED">Campaign Activated</option>
      </select>
      <button @click="loadAuditLogs" class="btn-refresh">Refresh</button>
    </div>

    <div class="audit-table-container">
      <table class="audit-table">
        <thead>
          <tr>
            <th>Timestamp</th>
            <th>Action</th>
            <th>Object Type</th>
            <th>Object ID</th>
            <th>User</th>
            <th>Status</th>
            <th>Details</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="7" class="loading-cell">Loading audit logs...</td>
          </tr>
          <tr v-else-if="auditLogs.length === 0">
            <td colspan="7" class="empty-cell">No audit logs found</td>
          </tr>
          <tr v-else v-for="log in filteredLogs" :key="log.id">
            <td>{{ formatDate(log.created_at) }}</td>
            <td>
              <span :class="['action-badge', getActionClass(log.action)]">
                {{ log.action }}
              </span>
            </td>
            <td>{{ log.object_type || '-' }}</td>
            <td class="object-id">{{ truncateId(log.object_id) }}</td>
            <td>{{ log.user || 'System' }}</td>
            <td>
              <span :class="['status-badge', log.status === 'success' ? 'success' : 'error']">
                {{ log.status || 'success' }}
              </span>
            </td>
            <td class="details-cell">
              <button @click="showDetails(log)" class="btn-details">View</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Details Modal -->
    <div v-if="selectedLog" class="modal-overlay" @click="selectedLog = null">
      <div class="modal" @click.stop>
        <h3>Audit Log Details</h3>
        <div class="modal-content">
          <div class="detail-item">
            <label>ID:</label>
            <span>{{ selectedLog.id }}</span>
          </div>
          <div class="detail-item">
            <label>Timestamp:</label>
            <span>{{ formatDate(selectedLog.created_at) }}</span>
          </div>
          <div class="detail-item">
            <label>Action:</label>
            <span>{{ selectedLog.action }}</span>
          </div>
          <div class="detail-item">
            <label>Object Type:</label>
            <span>{{ selectedLog.object_type || '-' }}</span>
          </div>
          <div class="detail-item">
            <label>Object ID:</label>
            <span>{{ selectedLog.object_id }}</span>
          </div>
          <div class="detail-item">
            <label>User:</label>
            <span>{{ selectedLog.user || 'System' }}</span>
          </div>
          <div class="detail-item">
            <label>Status:</label>
            <span>{{ selectedLog.status || 'success' }}</span>
          </div>
          <div v-if="selectedLog.details" class="detail-item full-width">
            <label>Details:</label>
            <pre>{{ JSON.stringify(selectedLog.details, null, 2) }}</pre>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="selectedLog = null" class="btn-secondary">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminApi } from '@/api/services/admin'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'

const auditLogs = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const filterAction = ref('')
const selectedLog = ref<any>(null)

const filteredLogs = computed(() => {
  let filtered = auditLogs.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(log => 
      log.action?.toLowerCase().includes(query) ||
      log.object_type?.toLowerCase().includes(query) ||
      log.object_id?.toLowerCase().includes(query)
    )
  }

  if (filterAction.value) {
    filtered = filtered.filter(log => log.action === filterAction.value)
  }

  return filtered
})

const loadAuditLogs = async () => {
  loading.value = true
  try {
    const response = await adminApi.getAuditLogs({ limit: 1000 })
    auditLogs.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading audit logs:', error)
    auditLogs.value = []
  } finally {
    loading.value = false
  }
}

const formatDate = (dateString: string) => {
  try {
    return format(new Date(dateString), 'MMM dd, yyyy HH:mm:ss')
  } catch {
    return dateString
  }
}

const truncateId = (id: string) => {
  if (!id) return '-'
  return id.length > 20 ? id.substring(0, 20) + '...' : id
}

const getActionClass = (action: string) => {
  if (!action) return ''
  if (action.includes('CREATE')) return 'create'
  if (action.includes('UPDATE')) return 'update'
  if (action.includes('DELETE')) return 'delete'
  return 'other'
}

const showDetails = (log: any) => {
  selectedLog.value = log
}

onMounted(() => {
  loadAuditLogs()
})
</script>

<style scoped>
.audit-log-view {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.section-header {
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 0.5rem 0;
}

.section-description {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
}

.filters {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input,
.filter-select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.search-input {
  flex: 1;
}

.btn-refresh {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.audit-table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.audit-table {
  width: 100%;
  border-collapse: collapse;
}

.audit-table th {
  background: #f9fafb;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  border-bottom: 2px solid #e0e0e0;
}

.audit-table td {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  font-size: 0.875rem;
}

.loading-cell,
.empty-cell {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.action-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.action-badge.create {
  background: #d1fae5;
  color: #065f46;
}

.action-badge.update {
  background: #dbeafe;
  color: #1e40af;
}

.action-badge.delete {
  background: #fee2e2;
  color: #991b1b;
}

.action-badge.other {
  background: #f3f4f6;
  color: #374151;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.status-badge.success {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.error {
  background: #fee2e2;
  color: #991b1b;
}

.object-id {
  font-family: monospace;
  font-size: 0.75rem;
}

.btn-details {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #374151;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal h3 {
  margin: 0 0 1.5rem 0;
}

.modal-content {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.detail-item {
  display: flex;
  gap: 1rem;
}

.detail-item.full-width {
  flex-direction: column;
}

.detail-item label {
  font-weight: 500;
  min-width: 120px;
}

.detail-item pre {
  background: #1a1a1a;
  color: #00ff00;
  padding: 1rem;
  border-radius: 6px;
  overflow-x: auto;
  font-size: 0.875rem;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #e5e7eb;
  color: #374151;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>

