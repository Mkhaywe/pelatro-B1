<template>
  <div class="external-systems-config">
    <div class="page-header">
      <h2>External Systems Configuration</h2>
      <p class="subtitle">Configure API connections to external systems (Xiva, CRM, Billing, etc.)</p>
    </div>

    <!-- Actions Bar -->
    <div class="actions-bar">
      <button @click="openAddModal" class="btn-primary">
        <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
          <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        Add External System
      </button>
    </div>

    <!-- Configurations List -->
    <div class="config-list">
      <div v-if="loading" class="loading-state">Loading configurations...</div>
      <div v-else-if="configs.length === 0" class="empty-state">
        <p>No external system configurations found. Add one to get started.</p>
      </div>
      <div v-else class="config-grid">
        <div v-for="config in configs" :key="config?.id || Math.random()" class="config-card">
          <div class="config-header">
            <div class="config-title">
              <h3>{{ config?.name || 'Unknown' }}</h3>
              <span :class="['badge', `badge-${config?.system_type || 'other'}`]">
                {{ (config?.system_type || 'other').toUpperCase() }}
              </span>
              <span v-if="config?.is_production" class="badge badge-production">PROD</span>
              <span v-else class="badge badge-staging">STAGING</span>
            </div>
            <div class="config-status">
              <span :class="['status-indicator', config?.is_active ? 'active' : 'inactive']"></span>
              {{ config?.is_active ? 'Active' : 'Inactive' }}
            </div>
          </div>
          
          <div class="config-details">
            <div class="detail-item">
              <span class="detail-label">Base URL:</span>
              <span class="detail-value">{{ config?.base_url || '-' }}</span>
            </div>
            <div class="detail-item">
              <span class="detail-label">Auth Type:</span>
              <span class="detail-value">{{ getAuthTypeLabel(config?.auth_type) }}</span>
            </div>
            <div class="detail-item" v-if="config?.endpoints && Object.keys(config.endpoints).length > 0">
              <span class="detail-label">Endpoints:</span>
              <span class="detail-value">{{ Object.keys(config.endpoints).length }} configured</span>
            </div>
            <div class="detail-item" v-if="config?.last_tested_at">
              <span class="detail-label">Last Tested:</span>
              <span class="detail-value">{{ formatDate(config.last_tested_at) }}</span>
            </div>
            <div class="detail-item" v-if="config?.last_sync_at">
              <span class="detail-label">Last Sync:</span>
              <span class="detail-value">{{ formatDate(config.last_sync_at) }}</span>
            </div>
          </div>
          
          <div class="config-actions">
            <button @click="testConnection(config)" class="btn-icon" :disabled="testing === config?.id" title="Test Connection">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="22 4 12 14.01 9 11.01" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ testing === config?.id ? 'Testing...' : 'Test' }}
            </button>
            <button @click="syncProducts(config)" class="btn-icon" :disabled="syncing === config?.id" title="Sync Products" v-if="config && ['xiva', 'crm', 'billing'].includes(config.system_type)">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.48L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              {{ syncing === config?.id ? 'Syncing...' : 'Sync' }}
            </button>
            <button @click="openEditModal(config)" class="btn-icon" title="Edit">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
            <button @click="deleteConfig(config?.id)" class="btn-icon btn-delete" title="Delete">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showModal" class="modal-overlay" @click.self="closeModal">
      <div class="modal-content modal-large">
        <h3>{{ editingConfig ? 'Edit External System' : 'Add External System' }}</h3>
        <form @submit.prevent="saveConfig">
          <div class="form-section">
            <h4>Basic Information</h4>
            <div class="form-grid">
              <div class="form-group">
                <label for="name">Configuration Name *</label>
                <input id="name" v-model="currentConfig.name" type="text" required placeholder="e.g., Xiva Production" />
              </div>
              <div class="form-group">
                <label for="system_type">System Type *</label>
                <select id="system_type" v-model="currentConfig.system_type" required>
                  <option value="xiva">Xiva</option>
                  <option value="crm">CRM</option>
                  <option value="billing">Billing/OCS</option>
                  <option value="dwh">Data Warehouse</option>
                  <option value="other">Other</option>
                </select>
              </div>
              <div class="form-group">
                <label for="base_url">Base URL *</label>
                <input id="base_url" v-model="currentConfig.base_url" type="url" required placeholder="https://api.xiva.sa/api" />
              </div>
              <div class="form-group">
                <label for="api_version">API Version</label>
                <input id="api_version" v-model="currentConfig.api_version" type="text" placeholder="v5" />
              </div>
            </div>
            <div class="form-group">
              <label for="description">Description</label>
              <textarea id="description" v-model="currentConfig.description" rows="2"></textarea>
            </div>
          </div>

          <div class="form-section">
            <h4>Authentication</h4>
            <div class="form-grid">
              <div class="form-group">
                <label for="auth_type">Authentication Type *</label>
                <select id="auth_type" v-model="currentConfig.auth_type" required>
                  <option value="jwt">JWT (JSON Web Token)</option>
                  <option value="bearer">Bearer Token</option>
                  <option value="api_key">API Key</option>
                  <option value="basic">Basic Auth</option>
                  <option value="oauth2">OAuth 2.0</option>
                  <option value="none">No Authentication</option>
                </select>
              </div>
              <div class="form-group" v-if="['jwt', 'basic', 'oauth2'].includes(currentConfig.auth_type)">
                <label for="auth_endpoint">Auth Endpoint</label>
                <input id="auth_endpoint" v-model="currentConfig.auth_endpoint" type="text" placeholder="/auth/token/" />
              </div>
              <div class="form-group" v-if="currentConfig.auth_type === 'jwt'">
                <label for="refresh_endpoint">Refresh Endpoint</label>
                <input id="refresh_endpoint" v-model="currentConfig.refresh_endpoint" type="text" placeholder="/auth/token/refresh/" />
              </div>
            </div>
            <div class="form-grid">
              <div class="form-group" v-if="['jwt', 'basic', 'oauth2'].includes(currentConfig.auth_type)">
                <label for="client_id">Client ID / Username *</label>
                <input id="client_id" v-model="currentConfig.client_id" type="text" />
              </div>
              <div class="form-group" v-if="['jwt', 'basic', 'oauth2', 'bearer'].includes(currentConfig.auth_type)">
                <label for="client_secret">Client Secret / Password *</label>
                <input id="client_secret" v-model="currentConfig.client_secret" type="password" />
                <small class="form-hint">Leave blank to keep existing secret</small>
              </div>
              <div class="form-group" v-if="currentConfig.auth_type === 'api_key'">
                <label for="api_key">API Key *</label>
                <input id="api_key" v-model="currentConfig.api_key" type="password" />
                <small class="form-hint">Leave blank to keep existing key</small>
              </div>
              <div class="form-group" v-if="currentConfig.auth_type === 'api_key'">
                <label for="api_key_header">API Key Header</label>
                <input id="api_key_header" v-model="currentConfig.api_key_header" type="text" placeholder="X-API-Key" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>API Endpoints</h4>
            <div class="form-group">
              <label for="endpoints_json">Endpoints (JSON)</label>
              <textarea id="endpoints_json" v-model="endpointsJson" rows="6" placeholder='{"products": "/productCatalogManagement/v5/productOffering/", "categories": "/category/"}'></textarea>
              <small class="form-hint">Define API endpoints as JSON object</small>
            </div>
          </div>

          <div class="form-section">
            <h4>Request Configuration</h4>
            <div class="form-grid">
              <div class="form-group">
                <label for="timeout">Timeout (seconds)</label>
                <input id="timeout" v-model.number="currentConfig.timeout" type="number" min="1" max="300" />
              </div>
              <div class="form-group">
                <label for="max_retries">Max Retries</label>
                <input id="max_retries" v-model.number="currentConfig.max_retries" type="number" min="0" max="10" />
              </div>
              <div class="form-group">
                <label for="retry_backoff">Retry Backoff</label>
                <select id="retry_backoff" v-model="currentConfig.retry_backoff">
                  <option value="exponential">Exponential</option>
                  <option value="linear">Linear</option>
                  <option value="fixed">Fixed</option>
                </select>
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>Rate Limiting</h4>
            <div class="form-grid">
              <div class="form-group">
                <label for="rate_limit_per_minute">Requests per Minute</label>
                <input id="rate_limit_per_minute" v-model.number="currentConfig.rate_limit_per_minute" type="number" min="1" />
              </div>
              <div class="form-group">
                <label for="rate_limit_per_hour">Requests per Hour</label>
                <input id="rate_limit_per_hour" v-model.number="currentConfig.rate_limit_per_hour" type="number" min="1" />
              </div>
            </div>
          </div>

          <div class="form-section">
            <h4>Custom Headers (JSON)</h4>
            <div class="form-group">
              <textarea v-model="customHeadersJson" rows="4" placeholder='{"X-Custom-Header": "value"}'></textarea>
              <small class="form-hint">Additional headers to include in requests</small>
            </div>
          </div>

          <div class="form-section">
            <h4>Status</h4>
            <div class="form-group">
              <label>
                <input type="checkbox" v-model="currentConfig.is_active" />
                Is Active
              </label>
              <label>
                <input type="checkbox" v-model="currentConfig.is_production" />
                Production Environment
              </label>
              <label>
                <input type="checkbox" v-model="currentConfig.verify_ssl" />
                Verify SSL Certificates
              </label>
            </div>
          </div>

          <div class="modal-actions">
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
            <button type="button" @click="closeModal" class="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Message -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { apiClient } from '@/api/client'

interface ExternalSystemConfig {
  id?: number
  name: string
  system_type: string
  base_url: string
  api_version: string
  auth_type: string
  auth_endpoint: string
  refresh_endpoint: string
  client_id: string
  client_secret: string
  api_key: string
  api_key_header: string
  custom_headers: Record<string, any>
  endpoints: Record<string, string>
  timeout: number
  max_retries: number
  retry_backoff: string
  rate_limit_per_minute: number
  rate_limit_per_hour: number
  verify_ssl: boolean
  is_active: boolean
  is_production: boolean
  description: string
  last_tested_at?: string
  last_sync_at?: string
}

const configs = ref<ExternalSystemConfig[]>([])
const loading = ref(false)
const showModal = ref(false)
const editingConfig = ref<ExternalSystemConfig | null>(null)
const currentConfig = ref<Partial<ExternalSystemConfig>>({
  system_type: 'xiva',
  auth_type: 'jwt',
  timeout: 30,
  max_retries: 3,
  retry_backoff: 'exponential',
  rate_limit_per_minute: 300,
  rate_limit_per_hour: 10000,
  verify_ssl: true,
  is_active: true,
  is_production: false,
  custom_headers: {},
  endpoints: {},
  api_key_header: 'X-API-Key',
})
const saving = ref(false)
const testing = ref<number | null>(null)
const syncing = ref<number | null>(null)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const endpointsJson = computed({
  get: () => JSON.stringify(currentConfig.value.endpoints || {}, null, 2),
  set: (value) => {
    try {
      currentConfig.value.endpoints = JSON.parse(value)
    } catch (e) {
      console.error('Invalid JSON for endpoints:', e)
    }
  },
})

const customHeadersJson = computed({
  get: () => JSON.stringify(currentConfig.value.custom_headers || {}, null, 2),
  set: (value) => {
    try {
      currentConfig.value.custom_headers = JSON.parse(value)
    } catch (e) {
      console.error('Invalid JSON for custom headers:', e)
    }
  },
})

const loadConfigs = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/external-systems/')
    configs.value = response.data
  } catch (error: any) {
    console.error('Error loading configurations:', error)
    showMessage('Failed to load configurations.', 'error')
  } finally {
    loading.value = false
  }
}

const openAddModal = () => {
  editingConfig.value = null
  currentConfig.value = {
    system_type: 'xiva',
    auth_type: 'jwt',
    timeout: 30,
    max_retries: 3,
    retry_backoff: 'exponential',
    rate_limit_per_minute: 300,
    rate_limit_per_hour: 10000,
    verify_ssl: true,
    is_active: true,
    is_production: false,
    custom_headers: {},
    endpoints: {},
    api_key_header: 'X-API-Key',
  }
  showModal.value = true
}

const openEditModal = (config: ExternalSystemConfig) => {
  editingConfig.value = config
  currentConfig.value = { ...config }
  showModal.value = true
}

const closeModal = () => {
  showModal.value = false
  editingConfig.value = null
}

const saveConfig = async () => {
  saving.value = true
  try {
    const payload = { ...currentConfig.value }
    
    // Don't send empty secrets (to keep existing ones)
    if (!payload.client_secret) delete payload.client_secret
    if (!payload.api_key) delete payload.api_key
    
    if (editingConfig.value?.id) {
      await apiClient.put(`/external-systems/${editingConfig.value.id}/`, payload)
      showMessage('Configuration updated successfully!', 'success')
    } else {
      await apiClient.post('/external-systems/', payload)
      showMessage('Configuration added successfully!', 'success')
    }
    await loadConfigs()
    closeModal()
  } catch (error: any) {
    console.error('Error saving configuration:', error)
    showMessage(`Failed to save: ${error.response?.data?.detail || error.message}`, 'error')
  } finally {
    saving.value = false
  }
}

const deleteConfig = async (id: number) => {
  if (!confirm('Are you sure you want to delete this configuration?')) return
  
  try {
    await apiClient.delete(`/external-systems/${id}/`)
    showMessage('Configuration deleted successfully!', 'success')
    await loadConfigs()
  } catch (error: any) {
    console.error('Error deleting configuration:', error)
    showMessage(`Failed to delete: ${error.response?.data?.detail || error.message}`, 'error')
  }
}

const testConnection = async (config: ExternalSystemConfig) => {
  testing.value = config.id!
  try {
    const response = await apiClient.post(`/external-systems/${config.id}/test/`)
    if (response.data.success) {
      showMessage('Connection test successful!', 'success')
      await loadConfigs()
    } else {
      showMessage(`Connection test failed: ${response.data.error}`, 'error')
    }
  } catch (error: any) {
    console.error('Error testing connection:', error)
    showMessage(`Connection test failed: ${error.response?.data?.error || error.message}`, 'error')
  } finally {
    testing.value = null
  }
}

const syncProducts = async (config: ExternalSystemConfig) => {
  syncing.value = config.id!
  try {
    const response = await apiClient.post(`/external-systems/${config.id}/sync-products/`)
    if (response.data.success) {
      showMessage(`Successfully synced ${response.data.created + response.data.updated} products!`, 'success')
      await loadConfigs()
    } else {
      showMessage(`Sync failed: ${response.data.error}`, 'error')
    }
  } catch (error: any) {
    console.error('Error syncing products:', error)
    showMessage(`Sync failed: ${error.response?.data?.error || error.message}`, 'error')
  } finally {
    syncing.value = null
  }
}

const getAuthTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    jwt: 'JWT',
    bearer: 'Bearer Token',
    api_key: 'API Key',
    basic: 'Basic Auth',
    oauth2: 'OAuth 2.0',
    none: 'None',
  }
  return labels[type] || type
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const showMessage = (msg: string, type: 'success' | 'error') => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 5000)
}

onMounted(() => {
  loadConfigs()
})
</script>

<style scoped>
.external-systems-config {
  padding: 1.5rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h2 {
  font-size: 1.8rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.actions-bar {
  margin-bottom: 1.5rem;
}

.btn-primary {
  padding: 0.6rem 1.2rem;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: var(--radius-md);
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.btn-primary:hover:not(:disabled) {
  background: var(--color-primary-dark);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.config-list {
  margin-top: 1.5rem;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 1.5rem;
}

.config-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  box-shadow: var(--shadow-sm);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1rem;
}

.config-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.config-title h3 {
  margin: 0;
  font-size: 1.1rem;
  color: var(--text-primary);
}

.badge {
  padding: 0.25rem 0.5rem;
  border-radius: var(--radius-full);
  font-size: 0.75rem;
  font-weight: var(--font-weight-medium);
}

.badge-xiva { background: #e3f2fd; color: #1976d2; }
.badge-crm { background: #fff3e0; color: #f57c00; }
.badge-billing { background: #e8f5e9; color: #388e3c; }
.badge-production { background: #ffebee; color: #d32f2f; }
.badge-staging { background: #f3e5f5; color: #8e24aa; }

.status-indicator {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  display: inline-block;
  margin-right: 0.5rem;
}

.status-indicator.active {
  background: var(--color-success);
}

.status-indicator.inactive {
  background: var(--color-error);
}

.config-details {
  margin-bottom: 1rem;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  padding: 0.5rem 0;
  border-bottom: 1px solid var(--border-color-light);
}

.detail-label {
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.detail-value {
  color: var(--text-primary);
  font-size: 0.9rem;
  text-align: right;
  word-break: break-word;
}

.config-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
}

.btn-icon {
  background: none;
  border: none;
  color: var(--text-secondary);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: var(--radius-sm);
  transition: all 0.2s ease;
}

.btn-icon:hover:not(:disabled) {
  background-color: var(--bg-tertiary);
  color: var(--text-primary);
}

.btn-icon:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-icon.btn-delete:hover {
  color: var(--color-error);
}

.btn-icon svg {
  width: 18px;
  height: 18px;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  overflow-y: auto;
  padding: 2rem;
}

.modal-content {
  background: var(--bg-primary);
  padding: 2rem;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-large {
  max-width: 900px;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.form-section {
  margin-bottom: 2rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid var(--border-color-light);
}

.form-section:last-of-type {
  border-bottom: none;
}

.form-section h4 {
  margin-top: 0;
  margin-bottom: 1rem;
  color: var(--text-primary);
  font-size: 1.1rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-secondary);
  font-weight: var(--font-weight-medium);
  font-size: 0.9rem;
}

.form-group input[type="text"],
.form-group input[type="url"],
.form-group input[type="number"],
.form-group input[type="password"],
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  background-color: var(--bg-input);
  color: var(--text-primary);
  font-size: 0.9rem;
}

.form-group textarea {
  font-family: 'Fira Code', 'Consolas', monospace;
  resize: vertical;
}

.form-hint {
  font-size: 0.8rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
  display: block;
}

.form-group input[type="checkbox"] {
  margin-right: 0.5rem;
}

.modal-actions {
  margin-top: 2rem;
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: 0.6rem 1.2rem;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: var(--color-gray-200);
  color: var(--text-primary);
}

.message {
  padding: 1rem;
  border-radius: var(--radius-md);
  margin-top: 1rem;
  font-weight: var(--font-weight-medium);
}

.message.success {
  background-color: var(--color-success-bg);
  color: var(--color-success);
  border: 1px solid var(--color-success);
}

.message.error {
  background-color: var(--color-error-bg);
  color: var(--color-error);
  border: 1px solid var(--color-error);
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 3rem;
  color: var(--text-secondary);
}
</style>

