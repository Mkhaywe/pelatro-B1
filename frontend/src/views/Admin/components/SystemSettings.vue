<template>
  <div class="system-settings">
    <div class="section-header">
      <h2>System Settings</h2>
      <p class="section-description">
        Configure system-wide settings and feature flags.
      </p>
    </div>

    <div class="settings-card">
      <h3>Feature Store Configuration</h3>
      <div class="settings-grid">
        <div class="setting-item">
          <label>Data Source Priority</label>
          <select v-model="featureStoreConfig.data_source">
            <option value="auto">Auto (Both Xiva & DWH)</option>
            <option value="xiva">Xiva Only</option>
            <option value="dwh">DWH Only</option>
          </select>
          <small>Determines which data source to use for customer features</small>
        </div>

        <div class="setting-item">
          <label>Merge Strategy</label>
          <select v-model="featureStoreConfig.merge_strategy">
            <option value="xiva_first">Xiva First (Xiva overrides DWH)</option>
            <option value="dwh_first">DWH First (DWH overrides Xiva)</option>
            <option value="merge">Merge (Combine both sources)</option>
          </select>
          <small>How to merge features when using multiple sources</small>
        </div>
      </div>
    </div>

    <div class="settings-card">
      <h3>ML Feature Mapping</h3>
      <p class="card-description">
        Map DWH column names to ML model feature names. This tells the ML system which DWH columns to use for predictions.
      </p>
      <div class="feature-mapping-editor">
        <div v-for="(dwhColumn, modelFeature, index) in mlFeatureMapping" :key="index" class="mapping-row">
          <input 
            v-model="mlFeatureMapping[modelFeature]" 
            :placeholder="`DWH column name (e.g., total_revenue)`"
            class="mapping-input"
            @input="updateMLFeatureMapping"
          />
          <span class="mapping-arrow">→</span>
          <input 
            :value="modelFeature" 
            readonly
            class="mapping-input readonly"
            placeholder="Model feature name"
          />
          <button @click="removeMapping(modelFeature)" class="btn-danger btn-sm">Remove</button>
        </div>
        <div class="add-mapping">
          <input 
            v-model="newMapping.modelFeature" 
            placeholder="Model feature name (e.g., revenue)"
            class="mapping-input"
          />
          <span class="mapping-arrow">→</span>
          <input 
            v-model="newMapping.dwhColumn" 
            placeholder="DWH column name (e.g., total_revenue)"
            class="mapping-input"
          />
          <button @click="addMapping" class="btn-primary btn-sm">Add Mapping</button>
        </div>
      </div>
      <div class="setting-item">
        <label>Model Input Size</label>
        <input 
          type="number" 
          v-model.number="mlConfig.model_input_size" 
          min="1" 
          max="100"
          @input="updateMLConfig"
        />
        <small>Number of features expected by ML models</small>
      </div>
      <button @click="saveMLConfig" class="btn-primary" :disabled="savingML">
        {{ savingML ? 'Saving...' : 'Save ML Configuration' }}
      </button>
    </div>

    <div class="settings-card">
      <h3>DWH Features Configuration</h3>
      <p class="card-description">
        Configure which DWH table/view to use for customer features and optionally provide a custom SQL query.
      </p>
      <div class="settings-grid">
        <div class="setting-item">
          <label>Customer Features Table/View</label>
          <input 
            v-model="dwhFeaturesConfig.customer_features_table" 
            placeholder="customer_features_view"
            @input="updateDWHFeaturesConfig"
          />
          <small>Table or view name in DWH (e.g., "customer_features_view" or "schema.view_name")</small>
        </div>
        <div class="setting-item full-width">
          <label>Custom SQL Query (Optional)</label>
          <textarea 
            v-model="dwhFeaturesConfig.customer_features_query" 
            rows="6"
            placeholder='SELECT customer_id, total_revenue, transaction_count FROM your_table WHERE customer_id = :customer_id'
            @input="updateDWHFeaturesConfig"
          ></textarea>
          <small>If provided, this query will be used instead of selecting from the table. Use :customer_id as parameter.</small>
        </div>
      </div>
      <button @click="saveDWHFeaturesConfig" class="btn-primary" :disabled="savingDWH">
        {{ savingDWH ? 'Saving...' : 'Save DWH Features Configuration' }}
      </button>
    </div>

    <div class="settings-card">
      <h3>Delivery Channel Configuration</h3>
      <p class="card-description">
        Configure how campaigns are delivered through each channel. Choose between Kafka topics or direct API calls.
      </p>
      
      <div class="channels-config">
        <div v-for="channel in channels" :key="channel.channel" class="channel-config-card">
          <div class="channel-header">
            <div class="channel-title">
              <input 
                type="checkbox" 
                v-model="channel.is_enabled"
                @change="updateChannel(channel)"
              />
              <h4>{{ channelLabels[channel.channel] }}</h4>
              <span class="channel-badge" :class="channel.delivery_mode">
                {{ channel.delivery_mode === 'kafka' ? 'Kafka' : 'API' }}
              </span>
            </div>
          </div>
          
          <div v-if="channel.is_enabled" class="channel-body">
            <div class="setting-item">
              <label>Delivery Mode</label>
              <select v-model="channel.delivery_mode" @change="updateChannel(channel)">
                <option value="kafka">Kafka Topics</option>
                <option value="api">Direct API Calls</option>
              </select>
            </div>
            
            <!-- Kafka Configuration -->
            <div v-if="channel.delivery_mode === 'kafka'" class="kafka-config">
              <div class="setting-item">
                <label>Kafka Topic</label>
                <input 
                  v-model="channel.kafka_topic" 
                  placeholder="e.g., loyalty.email.notifications"
                  @input="updateChannel(channel)"
                />
              </div>
              <div class="setting-item full-width">
                <label>Kafka Brokers (comma-separated URLs)</label>
                <input 
                  v-model="channel.kafka_brokers_input" 
                  placeholder="e.g., localhost:9092, broker2:9092"
                  @input="updateKafkaBrokers(channel)"
                />
                <small>Enter broker URLs separated by commas</small>
              </div>
              <div class="setting-item full-width">
                <label>Additional Kafka Config (JSON)</label>
                <textarea 
                  v-model="channel.kafka_config_json"
                  rows="3"
                  placeholder='{"acks": "all", "retries": 3}'
                  @input="updateKafkaConfig(channel)"
                ></textarea>
              </div>
            </div>
            
            <!-- API Configuration -->
            <div v-if="channel.delivery_mode === 'api'" class="api-config">
              <div class="setting-item">
                <label>API Endpoint URL</label>
                <input 
                  v-model="channel.api_endpoint" 
                  placeholder="https://api.example.com/send"
                  @input="updateChannel(channel)"
                />
              </div>
              <div class="setting-item">
                <label>HTTP Method</label>
                <select v-model="channel.api_method" @change="updateChannel(channel)">
                  <option value="POST">POST</option>
                  <option value="PUT">PUT</option>
                  <option value="PATCH">PATCH</option>
                </select>
              </div>
              <div class="setting-item">
                <label>Authentication Type</label>
                <select v-model="channel.api_auth_type" @change="updateChannel(channel)">
                  <option value="none">None</option>
                  <option value="bearer">Bearer Token</option>
                  <option value="basic">Basic Auth</option>
                  <option value="api_key">API Key</option>
                </select>
              </div>
              <div v-if="channel.api_auth_type !== 'none'" class="setting-item full-width">
                <label>Auth Configuration (JSON)</label>
                <textarea 
                  v-model="channel.api_auth_config_json"
                  rows="3"
                  :placeholder="getAuthPlaceholder(channel.api_auth_type)"
                  @input="updateAuthConfig(channel)"
                ></textarea>
                <small>Enter credentials as JSON (e.g., {"token": "your-token"} or {"username": "user", "password": "pass"})</small>
              </div>
              <div class="setting-item full-width">
                <label>Additional Headers (JSON)</label>
                <textarea 
                  v-model="channel.api_headers_json"
                  rows="2"
                  placeholder='{"Content-Type": "application/json"}'
                  @input="updateHeaders(channel)"
                ></textarea>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <button @click="saveDeliveryChannels" class="btn-primary" :disabled="savingChannels">
        {{ savingChannels ? 'Saving...' : 'Save Delivery Channel Configuration' }}
      </button>
    </div>

    <div class="settings-card">
      <h3>System Information</h3>
      <div class="info-grid">
        <div class="info-item">
          <span class="info-label">Django Version:</span>
          <span class="info-value">5.2.9</span>
        </div>
        <div class="info-item">
          <span class="info-label">Python Version:</span>
          <span class="info-value">3.x</span>
        </div>
        <div class="info-item">
          <span class="info-label">Database:</span>
          <span class="info-value">{{ databaseType }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { configApi } from '@/api/services/config'

const featureStoreConfig = ref({
  data_source: 'auto',
  merge_strategy: 'xiva_first',
})

const mlConfig = ref({
  feature_mapping: {} as Record<string, string>,
  model_input_size: 5,
  model_nbo_path: 'models/nbo.tflite',
  model_churn_path: 'models/churn.tflite',
  mock_mode: false,
})

const mlFeatureMapping = ref<Record<string, string>>({})

const newMapping = ref({
  modelFeature: '',
  dwhColumn: '',
})

const dwhFeaturesConfig = ref({
  customer_features_table: 'customer_features_view',
  customer_features_query: '',
})

const databaseType = ref('SQLite')
const savingML = ref(false)
const savingDWH = ref(false)
const savingChannels = ref(false)

const channelLabels: Record<string, string> = {
  email: '📧 Email',
  sms: '💬 SMS',
  push: '🔔 Push Notification',
  in_app: '📱 In-App',
}

const channels = ref<any[]>([])

const loadSettings = async () => {
  try {
    const response = await configApi.getAll()
    if (response.data.feature_store) {
      featureStoreConfig.value = response.data.feature_store
    }
    if (response.data.ml) {
      mlConfig.value = {
        feature_mapping: response.data.ml.feature_mapping || {},
        model_input_size: response.data.ml.model_input_size || 5,
        model_nbo_path: response.data.ml.model_nbo_path || 'models/nbo.tflite',
        model_churn_path: response.data.ml.model_churn_path || 'models/churn.tflite',
        mock_mode: response.data.ml.mock_mode || false,
      }
      mlFeatureMapping.value = response.data.ml.feature_mapping || {}
    }
    if (response.data.dwh) {
      dwhFeaturesConfig.value = {
        customer_features_table: response.data.dwh.customer_features_table || 'customer_features_view',
        customer_features_query: response.data.dwh.customer_features_query || '',
      }
    }
    await loadDeliveryChannels()
  } catch (error) {
    console.error('Error loading settings:', error)
  }
}

const loadDeliveryChannels = async () => {
  try {
    const response = await configApi.getDeliveryChannels()
    const channelsData = response.data
    
    // Initialize channels with defaults if not present
    const channelTypes = ['email', 'sms', 'push', 'in_app']
    channels.value = channelTypes.map(channelType => {
      const existing = channelsData[channelType]
      if (existing) {
        return {
          ...existing,
          kafka_brokers_input: Array.isArray(existing.kafka_brokers) ? existing.kafka_brokers.join(', ') : '',
          kafka_config_json: JSON.stringify(existing.kafka_config || {}, null, 2),
          api_headers_json: JSON.stringify(existing.api_headers || {}, null, 2),
          api_auth_config_json: JSON.stringify(existing.api_auth_config || {}, null, 2),
        }
      }
      return {
        channel: channelType,
        is_enabled: false,
        delivery_mode: 'api',
        kafka_topic: '',
        kafka_brokers: [],
        kafka_brokers_input: '',
        kafka_config: {},
        kafka_config_json: '{}',
        api_endpoint: '',
        api_method: 'POST',
        api_headers: {},
        api_headers_json: '{}',
        api_auth_type: 'none',
        api_auth_config: {},
        api_auth_config_json: '{}',
        channel_settings: {},
      }
    })
  } catch (error) {
    console.error('Error loading delivery channels:', error)
  }
}

const updateChannel = (channel: any) => {
  // Auto-save on change
}

const updateKafkaBrokers = (channel: any) => {
  channel.kafka_brokers = channel.kafka_brokers_input.split(',').map((b: string) => b.trim()).filter((b: string) => b)
}

const updateKafkaConfig = (channel: any) => {
  try {
    channel.kafka_config = JSON.parse(channel.kafka_config_json || '{}')
  } catch (e) {
    // Invalid JSON, ignore
  }
}

const updateHeaders = (channel: any) => {
  try {
    channel.api_headers = JSON.parse(channel.api_headers_json || '{}')
  } catch (e) {
    // Invalid JSON, ignore
  }
}

const updateAuthConfig = (channel: any) => {
  try {
    channel.api_auth_config = JSON.parse(channel.api_auth_config_json || '{}')
  } catch (e) {
    // Invalid JSON, ignore
  }
}

const getAuthPlaceholder = (authType: string) => {
  switch (authType) {
    case 'bearer':
      return '{"token": "your-bearer-token"}'
    case 'basic':
      return '{"username": "user", "password": "pass"}'
    case 'api_key':
      return '{"key": "your-api-key", "header": "X-API-Key"}'
    default:
      return '{}'
  }
}

const saveDeliveryChannels = async () => {
  savingChannels.value = true
  try {
    const channelsData: Record<string, any> = {}
    channels.value.forEach(channel => {
      channelsData[channel.channel] = {
        is_enabled: channel.is_enabled,
        delivery_mode: channel.delivery_mode,
        kafka_topic: channel.kafka_topic || '',
        kafka_brokers: channel.kafka_brokers || [],
        kafka_config: channel.kafka_config || {},
        api_endpoint: channel.api_endpoint || '',
        api_method: channel.api_method || 'POST',
        api_headers: channel.api_headers || {},
        api_auth_type: channel.api_auth_type || 'none',
        api_auth_config: channel.api_auth_config || {},
        channel_settings: channel.channel_settings || {},
      }
    })
    await configApi.updateDeliveryChannels(channelsData)
    alert('Delivery channel configuration saved successfully!')
  } catch (error: any) {
    alert('Error saving delivery channel configuration: ' + (error.response?.data?.error || error.message))
  } finally {
    savingChannels.value = false
  }
}

const updateMLFeatureMapping = () => {
  mlConfig.value.feature_mapping = { ...mlFeatureMapping.value }
}

const addMapping = () => {
  if (newMapping.value.modelFeature && newMapping.value.dwhColumn) {
    mlFeatureMapping.value[newMapping.value.modelFeature] = newMapping.value.dwhColumn
    updateMLFeatureMapping()
    newMapping.value = { modelFeature: '', dwhColumn: '' }
  }
}

const removeMapping = (modelFeature: string) => {
  delete mlFeatureMapping.value[modelFeature]
  updateMLFeatureMapping()
}

const updateMLConfig = () => {
  // Auto-save on change
}

const updateDWHFeaturesConfig = () => {
  // Auto-save on change
}

const saveMLConfig = async () => {
  savingML.value = true
  try {
    await configApi.updateMLConfig({
      feature_mapping: mlFeatureMapping.value,
      model_input_size: mlConfig.value.model_input_size,
      model_nbo_path: mlConfig.value.model_nbo_path,
      model_churn_path: mlConfig.value.model_churn_path,
      mock_mode: mlConfig.value.mock_mode,
    })
    alert('ML configuration saved successfully! Restart Django server to apply changes.')
  } catch (error: any) {
    alert('Error saving ML configuration: ' + (error.response?.data?.error || error.message))
  } finally {
    savingML.value = false
  }
}

const saveDWHFeaturesConfig = async () => {
  savingDWH.value = true
  try {
    await configApi.updateDWHFeaturesConfig({
      customer_features_table: dwhFeaturesConfig.value.customer_features_table,
      customer_features_query: dwhFeaturesConfig.value.customer_features_query,
    })
    alert('DWH features configuration saved successfully! Restart Django server to apply changes.')
  } catch (error: any) {
    alert('Error saving DWH features configuration: ' + (error.response?.data?.error || error.message))
  } finally {
    savingDWH.value = false
  }
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.system-settings {
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

.settings-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.settings-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1.5rem;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.setting-item label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.setting-item select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.setting-item small {
  font-size: 0.75rem;
  color: #666;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.info-label {
  font-size: 0.875rem;
  color: #666;
}

.info-value {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
}

.card-description {
  color: #666;
  font-size: 0.875rem;
  margin: 0 0 1rem 0;
}

.feature-mapping-editor {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.mapping-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.mapping-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.mapping-input.readonly {
  background: #f3f4f6;
  color: #6b7280;
  cursor: not-allowed;
}

.mapping-arrow {
  color: #6b7280;
  font-weight: 600;
}

.add-mapping {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px dashed #d1d5db;
}

.setting-item.full-width {
  grid-column: 1 / -1;
}

.setting-item textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  font-family: 'Courier New', monospace;
}

.setting-item input[type="number"] {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn-danger {
  background: #ef4444;
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-danger:hover {
  background: #dc2626;
}

.channels-config {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.channel-config-card {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 1rem;
}

.channel-header {
  margin-bottom: 1rem;
}

.channel-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.channel-title input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.channel-title h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  flex: 1;
}

.channel-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.channel-badge.kafka {
  background: #f3f4f6;
  color: #374151;
}

.channel-badge.api {
  background: #dbeafe;
  color: #1e40af;
}

.channel-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #f3f4f6;
}

.kafka-config,
.api-config {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}
</style>

