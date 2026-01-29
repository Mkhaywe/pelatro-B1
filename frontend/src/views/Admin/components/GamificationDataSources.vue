<template>
  <div class="gamification-data-sources">
    <div class="section-header">
      <h2>Gamification Data Sources</h2>
      <p class="section-description">
        Configure external systems to send customer events for gamification (missions, badges, leaderboards).
        Use webhooks to receive real-time customer events.
      </p>
    </div>

    <!-- Webhook Info Card -->
    <div class="info-card">
      <h3>📡 Webhook Endpoint</h3>
      <p>Send customer events to this endpoint:</p>
      <div class="webhook-url">
        <code>{{ webhookUrl }}</code>
        <button @click="copyWebhookUrl" class="btn-copy">Copy</button>
      </div>
      <p class="webhook-note">
        <strong>Note:</strong> This system uses HTTP webhooks (no Kafka required). 
        External systems can POST customer events to this endpoint.
      </p>
    </div>

    <!-- Data Sources List -->
    <div class="sources-section">
      <div class="section-header-inline">
        <h3>Configured Data Sources</h3>
        <button @click="showCreateForm = true" class="btn-primary">
          + Add Data Source
        </button>
      </div>

      <div v-if="loading" class="loading">Loading data sources...</div>
      
      <div v-else-if="dataSources.length === 0" class="empty-state">
        <p>No data sources configured yet.</p>
        <p>Click "Add Data Source" to configure an external system.</p>
      </div>

      <div v-else class="sources-list">
        <div v-for="source in dataSources" :key="source.id" class="source-card">
          <div class="source-header">
            <div>
              <h4>{{ source.name || source.source_name }}</h4>
              <span class="source-type">{{ getSourceTypeLabel(source.source_type) }}</span>
            </div>
            <div class="source-actions">
              <span :class="['status-badge', source.is_active ? 'active' : 'inactive']">
                {{ source.is_active ? 'Active' : 'Inactive' }}
              </span>
              <button @click="editSource(source)" class="btn-edit">Edit</button>
              <button @click="deleteSource(source.id)" class="btn-delete">Delete</button>
            </div>
          </div>
          
          <div v-if="source.description" class="source-description">
            {{ source.description }}
          </div>

          <div class="source-details">
            <div class="detail-item">
              <span class="detail-label">Sync Frequency:</span>
              <span class="detail-value">{{ source.sync_frequency || 'N/A' }}</span>
            </div>
            <div v-if="source.last_synced" class="detail-item">
              <span class="detail-label">Last Synced:</span>
              <span class="detail-value">{{ formatDate(source.last_synced) }}</span>
            </div>
            <div v-if="source.connection_config" class="detail-item">
              <span class="detail-label">Connection:</span>
              <span class="detail-value">{{ getConnectionSummary(source.connection_config) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Create/Edit Form Modal -->
    <div v-if="showCreateForm || editingSource" class="modal-overlay" @click="closeForm">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>{{ editingSource ? 'Edit' : 'Create' }} Data Source</h3>
          <button @click="closeForm" class="btn-close">×</button>
        </div>

        <form @submit.prevent="saveSource" class="source-form">
          <div class="form-group">
            <label>Source Name *</label>
            <input 
              v-model="formData.name" 
              type="text"
              placeholder="e.g., CDR System, Billing System"
              required
            />
          </div>

          <div class="form-group">
            <label>Source Type *</label>
            <select v-model="formData.source_type" required>
              <option value="">Select type...</option>
              <option value="cdr">CDR (Call Detail Records)</option>
              <option value="billing">Billing/OCS</option>
              <option value="crm">CRM/Subscriber DB</option>
              <option value="app">App/Web/USSD</option>
              <option value="network">Network/QoE</option>
              <option value="dwh">Data Warehouse</option>
              <option value="xiva">Xiva System</option>
              <option value="custom">Custom/Webhook</option>
            </select>
          </div>

          <div class="form-group">
            <label>Description</label>
            <textarea 
              v-model="formData.description" 
              rows="3"
              placeholder="Describe this data source..."
            ></textarea>
          </div>

          <div class="form-group">
            <label>Connection Configuration (JSON)</label>
            <textarea 
              v-model="connectionConfigJson" 
              rows="6"
              placeholder='{"api_endpoint": "https://example.com/api", "auth_token": "..."}'
            ></textarea>
            <small>For webhooks, you can leave this empty. The system will use the webhook endpoint above.</small>
          </div>

          <div class="form-group">
            <label>Event Mapping (JSON)</label>
            <textarea 
              v-model="eventMappingJson" 
              rows="6"
              placeholder='{"customer_id_field": "customer_id", "event_type_field": "event_type", "timestamp_field": "timestamp"}'
            ></textarea>
            <small>Map your event fields to normalized format. Required: customer_id_field, event_type_field, timestamp_field</small>
          </div>

          <div class="form-group">
            <label>Sync Frequency</label>
            <select v-model="formData.sync_frequency">
              <option value="realtime">Real-time (Webhook)</option>
              <option value="hourly">Hourly</option>
              <option value="daily">Daily</option>
              <option value="weekly">Weekly</option>
            </select>
          </div>

          <div class="form-group">
            <label>
              <input 
                v-model="formData.is_active" 
                type="checkbox"
              />
              Active
            </label>
          </div>

          <div class="form-actions">
            <button type="button" @click="closeForm" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '@/api/client'

interface DataSource {
  id: number
  name?: string
  source_name: string
  source_type: string
  description?: string
  connection_config?: any
  event_mapping?: any
  sync_frequency?: string
  last_synced?: string
  is_active: boolean
}

const dataSources = ref<DataSource[]>([])
const loading = ref(false)
const saving = ref(false)
const showCreateForm = ref(false)
const editingSource = ref<DataSource | null>(null)

const formData = ref({
  name: '',
  source_type: '',
  description: '',
  connection_config: {},
  event_mapping: {},
  sync_frequency: 'realtime',
  is_active: true,
})

const connectionConfigJson = ref('{}')
const eventMappingJson = ref('{}')

const webhookUrl = computed(() => {
  const baseUrl = window.location.origin
  return `${baseUrl}/api/loyalty/v1/webhooks/customer-events/`
})

const getSourceTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    cdr: 'CDR',
    billing: 'Billing',
    crm: 'CRM',
    app: 'App/Web',
    network: 'Network',
    dwh: 'Data Warehouse',
    xiva: 'Xiva',
    custom: 'Custom',
  }
  return labels[type] || type
}

const getConnectionSummary = (config: any) => {
  if (!config || typeof config !== 'object') return 'N/A'
  if (config.api_endpoint) return `API: ${config.api_endpoint}`
  if (config.kafka_topic) return `Kafka: ${config.kafka_topic}`
  if (config.db_table) return `DB Table: ${config.db_table}`
  return 'Webhook'
}

const formatDate = (dateStr: string) => {
  if (!dateStr) return 'Never'
  return new Date(dateStr).toLocaleString()
}

const copyWebhookUrl = () => {
  navigator.clipboard.writeText(webhookUrl.value)
  alert('Webhook URL copied to clipboard!')
}

const loadDataSources = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/data-sources/')
    dataSources.value = Array.isArray(response.data) ? response.data : response.data.results || []
  } catch (error: any) {
    console.error('Error loading data sources:', error)
    alert('Error loading data sources: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const saveSource = async () => {
  saving.value = true
  try {
    // Parse JSON fields
    let connectionConfig = {}
    let eventMapping = {}
    
    try {
      connectionConfig = connectionConfigJson.value ? JSON.parse(connectionConfigJson.value) : {}
    } catch (e) {
      alert('Invalid JSON in Connection Configuration')
      saving.value = false
      return
    }
    
    try {
      eventMapping = eventMappingJson.value ? JSON.parse(eventMappingJson.value) : {}
    } catch (e) {
      alert('Invalid JSON in Event Mapping')
      saving.value = false
      return
    }

    const payload = {
      ...formData.value,
      source_name: formData.value.name,
      connection_config: connectionConfig,
      event_mapping: eventMapping,
    }

    if (editingSource.value) {
      await apiClient.put(`/data-sources/${editingSource.value.id}/`, payload)
    } else {
      await apiClient.post('/data-sources/', payload)
    }

    await loadDataSources()
    closeForm()
    alert('Data source saved successfully!')
  } catch (error: any) {
    console.error('Error saving data source:', error)
    alert('Error saving data source: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

const editSource = (source: DataSource) => {
  editingSource.value = source
  formData.value = {
    name: source.name || source.source_name,
    source_type: source.source_type,
    description: source.description || '',
    connection_config: source.connection_config || {},
    event_mapping: source.event_mapping || {},
    sync_frequency: source.sync_frequency || 'realtime',
    is_active: source.is_active,
  }
  connectionConfigJson.value = JSON.stringify(source.connection_config || {}, null, 2)
  eventMappingJson.value = JSON.stringify(source.event_mapping || {}, null, 2)
  showCreateForm.value = true
}

const deleteSource = async (id: number) => {
  if (!confirm('Are you sure you want to delete this data source?')) return
  
  try {
    await apiClient.delete(`/data-sources/${id}/`)
    await loadDataSources()
    alert('Data source deleted successfully!')
  } catch (error: any) {
    console.error('Error deleting data source:', error)
    alert('Error deleting data source: ' + (error.response?.data?.detail || error.message))
  }
}

const closeForm = () => {
  showCreateForm.value = false
  editingSource.value = null
  formData.value = {
    name: '',
    source_type: '',
    description: '',
    connection_config: {},
    event_mapping: {},
    sync_frequency: 'realtime',
    is_active: true,
  }
  connectionConfigJson.value = '{}'
  eventMappingJson.value = '{}'
}

onMounted(() => {
  loadDataSources()
})
</script>

<style scoped>
.gamification-data-sources {
  padding: 1rem;
}

.section-header {
  margin-bottom: 2rem;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.5rem 0;
}

.section-description {
  color: #666;
  margin: 0;
}

.info-card {
  background: #f0f9ff;
  border: 1px solid #bae6fd;
  border-radius: 8px;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.info-card h3 {
  margin: 0 0 1rem 0;
  font-size: 1.125rem;
}

.webhook-url {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin: 1rem 0;
}

.webhook-url code {
  flex: 1;
  background: white;
  padding: 0.75rem;
  border-radius: 4px;
  border: 1px solid #ddd;
  font-family: monospace;
  word-break: break-all;
}

.btn-copy {
  padding: 0.75rem 1rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.webhook-note {
  margin: 1rem 0 0 0;
  color: #666;
  font-size: 0.875rem;
}

.section-header-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.sources-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.source-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1.5rem;
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.source-header h4 {
  margin: 0 0 0.25rem 0;
  font-size: 1.125rem;
}

.source-type {
  display: inline-block;
  background: #f3f4f6;
  color: #6b7280;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 500;
}

.source-actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
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

.btn-edit, .btn-delete {
  padding: 0.5rem 1rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.875rem;
}

.btn-edit {
  background: white;
  color: #2563eb;
}

.btn-delete {
  background: white;
  color: #dc2626;
}

.source-details {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.detail-item {
  display: flex;
  gap: 0.5rem;
}

.detail-label {
  font-weight: 500;
  color: #666;
}

.detail-value {
  color: #1a1a1a;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 8px;
  width: 90%;
  max-width: 700px;
  max-height: 90vh;
  overflow-y: auto;
  padding: 2rem;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.btn-close {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #666;
}

.source-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 0.875rem;
}

.form-group small {
  color: #666;
  font-size: 0.75rem;
}

.form-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 1rem;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: white;
  color: #666;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #666;
}
</style>

