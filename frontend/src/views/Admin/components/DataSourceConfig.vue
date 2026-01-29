<template>
  <div class="data-source-config">
    <div class="section-header">
      <h2>Data Source Configuration</h2>
      <p class="section-description">
        Configure connections to Xiva BSS and Data Warehouse (DWH) for customer data and features.
      </p>
    </div>

    <!-- Xiva Configuration -->
    <div class="config-card">
      <div class="card-header">
        <h3>Xiva BSS Integration</h3>
        <div class="connection-status">
          <span :class="['status-indicator', xivaStatus.connected ? 'connected' : 'disconnected']"></span>
          <span>{{ xivaStatus.connected ? 'Connected' : 'Not Connected' }}</span>
          <button @click="testXivaConnection" class="btn-test" :disabled="testingXiva">
            {{ testingXiva ? 'Testing...' : 'Test Connection' }}
          </button>
        </div>
      </div>

      <form @submit.prevent="saveXivaConfig" class="config-form">
        <div class="form-grid">
          <div class="form-group">
            <label>Base URL *</label>
            <input 
              v-model="xivaConfig.base_url" 
              type="url"
              placeholder="https://www.xiva.ca/api"
              required
            />
          </div>

          <div class="form-group">
            <label>Authentication Type *</label>
            <select v-model="xivaConfig.auth_type" required>
              <option value="JWT">JWT (Username/Password)</option>
              <option value="TOKEN">Token</option>
            </select>
          </div>

          <div v-if="xivaConfig.auth_type === 'JWT'" class="form-group">
            <label>Username *</label>
            <input 
              v-model="xivaConfig.username" 
              type="text"
              placeholder="xiva_username"
              required
            />
          </div>

          <div v-if="xivaConfig.auth_type === 'JWT'" class="form-group">
            <label>Password *</label>
            <input 
              v-model="xivaConfig.password" 
              type="password"
              placeholder="••••••••"
              required
            />
          </div>

          <div v-if="xivaConfig.auth_type === 'TOKEN'" class="form-group">
            <label>Auth Token *</label>
            <input 
              v-model="xivaConfig.auth_token" 
              type="password"
              placeholder="••••••••"
              required
            />
          </div>

          <div class="form-group">
            <label>Timeout (seconds)</label>
            <input 
              v-model.number="xivaConfig.timeout" 
              type="number"
              min="10"
              max="300"
            />
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="savingXiva">
            {{ savingXiva ? 'Saving...' : 'Save Xiva Configuration' }}
          </button>
        </div>
      </form>
    </div>

    <!-- DWH Configuration -->
    <div class="config-card">
      <div class="card-header">
        <h3>Data Warehouse (DWH) Integration</h3>
        <div class="connection-status">
          <span :class="['status-indicator', dwhStatus.connected ? 'connected' : 'disconnected']"></span>
          <span>{{ dwhStatus.connected ? 'Connected' : 'Not Connected' }}</span>
          <button @click="testDWHConnection" class="btn-test" :disabled="testingDWH">
            {{ testingDWH ? 'Testing...' : 'Test Connection' }}
          </button>
        </div>
      </div>

      <form @submit.prevent="saveDWHConfig" class="config-form">
        <div class="form-grid">
          <div class="form-group">
            <label>DWH Type *</label>
            <select v-model="dwhConfig.type" required>
              <option value="postgresql">PostgreSQL</option>
              <option value="oracle">Oracle</option>
              <option value="snowflake">Snowflake</option>
            </select>
          </div>

          <div v-if="dwhConfig.type === 'postgresql'" class="form-group full-width">
            <label>PostgreSQL Connection String *</label>
            <input 
              v-model="dwhConfig.postgres_connection_string" 
              type="text"
              placeholder="postgresql://user:password@host:port/database"
              required
            />
          </div>

          <div v-if="dwhConfig.type === 'oracle'" class="form-group full-width">
            <label>Oracle Connection String *</label>
            <input 
              v-model="dwhConfig.oracle_connection_string" 
              type="text"
              placeholder="host:port/service_name"
              required
            />
          </div>

          <div v-if="dwhConfig.type === 'snowflake'" class="form-group">
            <label>Snowflake Account *</label>
            <input 
              v-model="dwhConfig.snowflake_account" 
              type="text"
              placeholder="account.snowflakecomputing.com"
              required
            />
          </div>

          <div class="form-group">
            <label>Database User</label>
            <input 
              v-model="dwhConfig.user" 
              type="text"
              placeholder="dwh_user"
            />
          </div>

          <div class="form-group">
            <label>Database Password</label>
            <input 
              v-model="dwhConfig.password" 
              type="password"
              placeholder="••••••••"
            />
          </div>

          <div class="form-group full-width">
            <label>Customer Features Query (Optional)</label>
            <textarea 
              v-model="dwhConfig.customer_features_query" 
              rows="4"
              placeholder="SELECT * FROM customer_features WHERE customer_id = :customer_id"
            ></textarea>
            <small>If not provided, will use table/view name below</small>
          </div>

          <div class="form-group">
            <label>Customer Features Table/View</label>
            <input 
              v-model="dwhConfig.customer_features_table" 
              type="text"
              placeholder="customer_features_view"
            />
          </div>
        </div>

        <div class="form-actions">
          <button type="submit" class="btn-primary" :disabled="savingDWH">
            {{ savingDWH ? 'Saving...' : 'Save DWH Configuration' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Success/Error Messages -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { configApi, type XivaConfig, type DWHConfig } from '@/api/services/config'
import { extractData } from '@/utils/api'

const xivaConfig = ref<Partial<XivaConfig>>({
  base_url: '',
  auth_type: 'JWT',
  username: '',
  password: '',
  timeout: 30,
})

const dwhConfig = ref<Partial<DWHConfig>>({
  type: 'postgresql',
  customer_features_table: 'customer_features_view',
})

const xivaStatus = ref({ connected: false, error: null as string | null })
const dwhStatus = ref({ connected: false, error: null as string | null })
const testingXiva = ref(false)
const testingDWH = ref(false)
const savingXiva = ref(false)
const savingDWH = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')

const loadConfigs = async () => {
  try {
    const response = await configApi.getAll()
    const data = response.data
    
    if (data.xiva) {
      xivaConfig.value = { ...data.xiva, password: '' }
    }
    if (data.dwh) {
      dwhConfig.value = { ...data.dwh, password: '' }
    }
    
    // Test connections
    await Promise.all([
      testXivaConnection(),
      testDWHConnection()
    ])
  } catch (error: any) {
    console.error('Error loading configs:', error)
    showMessage('Error loading configurations', 'error')
  }
}

const testXivaConnection = async () => {
  testingXiva.value = true
  try {
    const response = await configApi.testXivaConnection()
    xivaStatus.value = {
      connected: response.data.connected || false,
      error: response.data.error || null
    }
    if (response.data.connected) {
      showMessage('Xiva connection successful!', 'success')
    } else {
      showMessage(`Xiva connection failed: ${response.data.error}`, 'error')
    }
  } catch (error: any) {
    xivaStatus.value = { connected: false, error: error.message }
    showMessage('Error testing Xiva connection', 'error')
  } finally {
    testingXiva.value = false
  }
}

const testDWHConnection = async () => {
  testingDWH.value = true
  try {
    const response = await configApi.testDWHConnection()
    dwhStatus.value = {
      connected: response.data.connected || false,
      error: response.data.error || null
    }
    if (response.data.connected) {
      showMessage('DWH connection successful!', 'success')
    } else {
      showMessage(`DWH connection failed: ${response.data.error}`, 'error')
    }
  } catch (error: any) {
    dwhStatus.value = { connected: false, error: error.message }
    showMessage('Error testing DWH connection', 'error')
  } finally {
    testingDWH.value = false
  }
}

const saveXivaConfig = async () => {
  savingXiva.value = true
  try {
    await configApi.updateXivaConfig(xivaConfig.value)
    showMessage('Xiva configuration saved! Restart Django server to apply changes.', 'success')
    await testXivaConnection()
  } catch (error: any) {
    showMessage(`Error saving Xiva config: ${error.response?.data?.error || error.message}`, 'error')
  } finally {
    savingXiva.value = false
  }
}

const saveDWHConfig = async () => {
  savingDWH.value = true
  try {
    await configApi.updateDWHConfig(dwhConfig.value)
    showMessage('DWH configuration saved! Restart Django server to apply changes.', 'success')
    await testDWHConnection()
  } catch (error: any) {
    showMessage(`Error saving DWH config: ${error.response?.data?.error || error.message}`, 'error')
  } finally {
    savingDWH.value = false
  }
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
.data-source-config {
  display: flex;
  flex-direction: column;
  gap: 2rem;
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

.config-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.card-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0;
}

.connection-status {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.status-indicator.connected {
  background: #10b981;
}

.status-indicator.disconnected {
  background: #ef4444;
}

.btn-test {
  padding: 0.5rem 1rem;
  background: #e5e7eb;
  color: #374151;
  border: none;
  border-radius: 6px;
  font-size: 0.875rem;
  cursor: pointer;
  font-weight: 500;
}

.btn-test:hover:not(:disabled) {
  background: #d1d5db;
}

.btn-test:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.config-form {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group.full-width {
  grid-column: 1 / -1;
}

.form-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select,
.form-group textarea {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.form-group textarea {
  font-family: monospace;
  resize: vertical;
}

.form-group small {
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.25rem;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.message {
  padding: 1rem;
  border-radius: 6px;
  font-size: 0.875rem;
}

.message.success {
  background: #d1fae5;
  color: #065f46;
  border: 1px solid #10b981;
}

.message.error {
  background: #fee2e2;
  color: #991b1b;
  border: 1px solid #ef4444;
}
</style>

