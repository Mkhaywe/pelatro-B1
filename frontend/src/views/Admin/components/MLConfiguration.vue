<template>
  <div class="ml-config">
    <div class="section-header">
      <h2>Machine Learning Configuration</h2>
      <p class="section-description">
        Configure ML models, test predictions, and monitor model status.
      </p>
    </div>

    <!-- ML Status -->
    <div class="status-card">
      <h3>ML System Status</h3>
      <div class="status-grid">
        <div class="status-item">
          <span class="status-label">TensorFlow:</span>
          <span :class="['status-value', mlStatus.tensorflow_available ? 'available' : 'unavailable']">
            {{ mlStatus.tensorflow_available ? 'Available' : 'Not Available' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">NumPy:</span>
          <span :class="['status-value', mlStatus.numpy_available ? 'available' : 'unavailable']">
            {{ mlStatus.numpy_available ? 'Available' : 'Not Available' }}
          </span>
        </div>
        <div class="status-item">
          <span class="status-label">Mock Mode:</span>
          <span :class="['status-value', mlStatus.mock_mode ? 'enabled' : 'disabled']">
            {{ mlStatus.mock_mode ? 'Enabled' : 'Disabled' }}
          </span>
        </div>
      </div>

      <div class="models-status">
        <h4>Model Status</h4>
        <div v-if="!mlStatus.models || Object.keys(mlStatus.models).length === 0" class="no-models-warning">
          <p><strong>⚠️ No model files found!</strong></p>
          <p>To create model files, run one of these scripts:</p>
          <ul>
            <li><code>python create_ml_models.py</code> - Creates placeholder models</li>
            <li><code>python train_models_from_dwh.py</code> - Trains real models from DWH data</li>
          </ul>
          <p v-if="mlStatus.mock_mode" class="mock-mode-note">
            <strong>Note:</strong> Mock mode is enabled. Predictions will use mock data until model files are created.
          </p>
        </div>
        <div v-else class="model-list">
          <div v-for="(model, name) in mlStatus.models" :key="name" class="model-item">
            <div class="model-name">{{ name.toUpperCase() }} Model</div>
            <div class="model-details">
              <span>Path: {{ model.path }}</span>
              <span :class="['model-status', model.exists ? 'exists' : 'missing']">
                {{ model.exists ? 'File Exists' : 'File Missing' }}
              </span>
              <span :class="['model-status', model.loaded ? 'loaded' : 'not-loaded']">
                {{ model.loaded ? 'Loaded' : 'Not Loaded' }}
              </span>
            </div>
            <div v-if="!model.exists" class="model-help">
              <small>Run <code>python create_ml_models.py</code> or <code>python train_models_from_dwh.py</code> to create this model.</small>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ML Testing -->
    <div class="test-card">
      <h3>Test ML Predictions</h3>
      
      <!-- Mode Toggle -->
      <div class="mode-toggle">
        <button 
          :class="['mode-btn', predictionMode === 'single' ? 'active' : '']"
          @click="predictionMode = 'single'; testSegmentId = ''"
          type="button"
        >
          Single Customer
        </button>
        <button 
          :class="['mode-btn', predictionMode === 'batch' ? 'active' : '']"
          @click="predictionMode = 'batch'; testSegmentId = ''"
          type="button"
        >
          Batch (Multiple Customers)
        </button>
        <button 
          :class="['mode-btn', predictionMode === 'segment' ? 'active' : '']"
          @click="handleSegmentModeClick"
          type="button"
        >
          Segment
        </button>
      </div>

      <form @submit.prevent="testPrediction" class="test-form">
        <!-- Single Customer Mode -->
        <div v-if="predictionMode === 'single'" class="form-group">
          <label>Customer ID *</label>
          <input 
            v-model="testCustomerId" 
            type="text"
            placeholder="Enter customer UUID"
            required
          />
        </div>

        <!-- Batch Mode -->
        <div v-if="predictionMode === 'batch'" class="form-group">
          <label>Customer IDs * (one per line)</label>
          <textarea 
            v-model="testCustomerIds" 
            rows="5"
            placeholder="Enter customer UUIDs, one per line&#10;Example:&#10;uuid-1&#10;uuid-2&#10;uuid-3"
            required
            class="customer-ids-input"
          ></textarea>
          <small class="form-hint">
            Enter multiple customer IDs, one per line. Maximum 100 customers per batch.
          </small>
        </div>

        <!-- Segment Mode -->
        <div v-if="predictionMode === 'segment'" class="form-group">
          <label>Segment *</label>
          <select 
            v-model="testSegmentId" 
            required
            :disabled="loadingSegments"
            class="segment-select"
          >
            <option value="">{{ loadingSegments ? 'Loading segments...' : segments.length === 0 ? 'No segments available' : 'Select a segment...' }}</option>
            <option 
              v-for="segment in segments" 
              :key="segment.id" 
              :value="String(segment.id)"
            >
              {{ segment.name }}{{ segment.active_member_count !== undefined ? ` (${segment.active_member_count} members)` : '' }}
            </option>
          </select>
          <div v-if="loadingSegments" class="form-hint">
            Loading segments...
          </div>
          <div v-else-if="segments.length === 0" class="form-hint" style="color: #ef4444;">
            No active segments found. Please create a segment first.
          </div>
          <small class="form-hint" v-else-if="selectedSegment">
            Running predictions for all {{ selectedSegment.active_member_count || 0 }} active members in this segment.
          </small>
          <small class="form-hint" v-else>
            Select a segment to run ML predictions for all customers in that segment.
          </small>
        </div>

        <div class="form-group">
          <label>Prediction Type *</label>
          <select v-model="testPredictionType" required>
            <option value="churn">Churn Prediction</option>
            <option value="nbo">Next Best Offer (NBO)</option>
            <option value="rfm">RFM Analysis</option>
            <option value="ltv">Lifetime Value (LTV) Prediction</option>
            <option value="propensity">Propensity to Buy</option>
            <option value="product">Product Recommendation</option>
            <option value="campaign">Campaign Response Prediction</option>
            <option value="default_risk">Payment Default Risk</option>
            <option value="upsell">Upsell/Cross-sell Propensity</option>
            <option value="engagement">Engagement Score</option>
          </select>
        </div>

        <button type="submit" class="btn-primary" :disabled="testing || (predictionMode === 'segment' && !testSegmentId)">
          {{ 
            testing 
              ? 'Testing...' 
              : predictionMode === 'segment' 
                ? 'Run Segment Prediction' 
                : predictionMode === 'batch' 
                  ? 'Run Batch Prediction' 
                  : 'Run Prediction' 
          }}
        </button>
      </form>

      <!-- Test Results -->
      <div v-if="testResult" class="test-results">
        <h4>Prediction Results</h4>
        
        <!-- Summary Stats -->
        <div v-if="testResult.mode === 'batch' || testResult.mode === 'segment'" class="batch-summary">
          <div class="summary-stats">
            <span class="stat-item">
              <strong>Total:</strong> {{ testResult.total || testResult.total_customers || 0 }}
            </span>
            <span class="stat-item success">
              <strong>Successful:</strong> {{ testResult.successful || testResult.successful_count || 0 }}
            </span>
            <span v-if="(testResult.failed || testResult.failed_count || 0) > 0" class="stat-item error">
              <strong>Failed:</strong> {{ testResult.failed || testResult.failed_count || 0 }}
            </span>
            <span v-if="testResult.segment_id" class="stat-item">
              <strong>Segment:</strong> {{ testResult.segment_name || testResult.segment_id }}
            </span>
          </div>
          
          <!-- Aggregated Stats for Segment/Batch -->
          <div v-if="testResult.aggregated_stats && testResult.type === 'churn'" class="aggregated-stats">
            <h5>Churn Risk Distribution</h5>
            <div class="stats-grid">
              <div class="stat-card high-risk">
                <span class="stat-label">High Risk</span>
                <span class="stat-value">{{ testResult.aggregated_stats.churn?.high || 0 }}</span>
                <span class="stat-percentage">
                  {{ testResult.total_customers ? Math.round((testResult.aggregated_stats.churn?.high || 0) / testResult.total_customers * 100) : 0 }}%
                </span>
              </div>
              <div class="stat-card medium-risk">
                <span class="stat-label">Medium Risk</span>
                <span class="stat-value">{{ testResult.aggregated_stats.churn?.medium || 0 }}</span>
                <span class="stat-percentage">
                  {{ testResult.total_customers ? Math.round((testResult.aggregated_stats.churn?.medium || 0) / testResult.total_customers * 100) : 0 }}%
                </span>
              </div>
              <div class="stat-card low-risk">
                <span class="stat-label">Low Risk</span>
                <span class="stat-value">{{ testResult.aggregated_stats.churn?.low || 0 }}</span>
                <span class="stat-percentage">
                  {{ testResult.total_customers ? Math.round((testResult.aggregated_stats.churn?.low || 0) / testResult.total_customers * 100) : 0 }}%
                </span>
              </div>
            </div>
            <div class="avg-probability">
              <strong>Average Churn Probability:</strong> 
              {{ testResult.aggregated_stats.churn?.avg_probability 
                ? (testResult.aggregated_stats.churn.avg_probability * 100).toFixed(1) + '%' 
                : 'N/A' }}
            </div>
          </div>
          
          <!-- RFM Distribution -->
          <div v-if="testResult.aggregated_stats && testResult.type === 'rfm' && testResult.aggregated_stats.rfm" class="rfm-distribution">
            <h5>RFM Segment Distribution</h5>
            <div class="rfm-segments-list">
              <div 
                v-for="[segment, count] in Object.entries(testResult.aggregated_stats.rfm)" 
                :key="segment"
                class="rfm-segment-item"
              >
                <span class="rfm-segment-label">{{ segment === 'Unknown' ? getRFMSegmentName('') : (segment.length === 3 ? getRFMSegmentName(segment) : segment) }}</span>
                <span class="rfm-segment-code-small">{{ segment.length === 3 ? segment : '' }}</span>
                <span class="rfm-segment-count">{{ count }} customers</span>
                <span class="rfm-segment-percentage">
                  ({{ testResult.total_customers ? Math.round((count as number) / testResult.total_customers * 100) : 0 }}%)
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- Results Table -->
        <div v-if="testResult.results && testResult.results.length > 0" class="results-table-container">
          <h5>Individual Predictions</h5>
          <div class="table-controls">
            <input 
              v-model="resultsFilter" 
              placeholder="Search by Customer ID..." 
              class="filter-input"
            />
            <span class="results-count">
              Showing {{ filteredResults.length }} of {{ testResult.results.length }} results
            </span>
          </div>
          <div class="table-wrapper">
            <table class="results-table">
              <thead>
                <tr>
                  <th>Customer ID</th>
                  <th v-if="testResult.type === 'churn'">Churn Probability</th>
                  <th v-if="testResult.type === 'churn'">Risk Level</th>
                  <th v-if="testResult.type === 'nbo'">Recommended Offer</th>
                  <th v-if="testResult.type === 'nbo'">Confidence</th>
                  <th v-if="testResult.type === 'rfm'">RFM Segment</th>
                  <th>Prediction Logic</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredResults" :key="item.customer_id">
                  <td class="customer-id-cell">
                    <span class="customer-id-short">{{ item.customer_id.substring(0, 8) }}...</span>
                    <span class="customer-id-full" :title="item.customer_id">{{ item.customer_id }}</span>
                  </td>
                  <td v-if="testResult.type === 'churn'" class="probability-cell">
                    <div class="probability-bar">
                      <div 
                        class="probability-fill" 
                        :style="{ width: (item.result.churn_probability * 100) + '%' }"
                        :class="getRiskClass(item.result.churn_probability)"
                      ></div>
                      <span class="probability-text">{{ (item.result.churn_probability * 100).toFixed(1) }}%</span>
                    </div>
                  </td>
                  <td v-if="testResult.type === 'churn'">
                    <span class="risk-badge" :class="item.result.churn_risk">
                      {{ item.result.churn_risk.toUpperCase() }}
                    </span>
                  </td>
                  <td v-if="testResult.type === 'nbo'">
                    {{ item.result.recommended_offer !== undefined ? `Offer #${item.result.recommended_offer}` : 'N/A' }}
                  </td>
                  <td v-if="testResult.type === 'nbo'" class="confidence-cell">
                    {{ item.result.confidence ? (item.result.confidence * 100).toFixed(1) + '%' : 'N/A' }}
                  </td>
                  <td v-if="testResult.type === 'rfm'">
                    <div class="rfm-segment-cell">
                      <span class="rfm-segment-code">{{ item.result.rfm_segment || 'N/A' }}</span>
                      <span class="rfm-segment-name">{{ item.result.segment || getRFMSegmentName(item.result.rfm_segment || '') || 'Unknown' }}</span>
                    </div>
                  </td>
                  <td class="logic-cell">
                    <div class="prediction-logic">
                      {{ getPredictionLogic(item.result, testResult.type) }}
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-if="testResult.has_more_results" class="more-results-note">
            <em>Note: Showing first 100 results. Total results: {{ testResult.total_customers || testResult.total }}</em>
          </div>
        </div>

        <!-- Errors Table -->
        <div v-if="testResult.errors && testResult.errors.length > 0" class="errors-section">
          <h5>Errors ({{ testResult.errors.length }})</h5>
          <div class="table-wrapper">
            <table class="results-table error-table">
              <thead>
                <tr>
                  <th>Customer ID</th>
                  <th>Error Message</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="error in testResult.errors" :key="error.customer_id">
                  <td class="customer-id-cell">{{ error.customer_id.substring(0, 8) }}...</td>
                  <td class="error-message">{{ error.error }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Raw JSON Toggle (for debugging) -->
        <div class="raw-json-toggle">
          <button @click="showRawJson = !showRawJson" class="btn-link">
            {{ showRawJson ? 'Hide' : 'Show' }} Raw JSON
          </button>
        </div>
        <div v-if="showRawJson" class="result-content">
          <pre>{{ JSON.stringify(testResult, null, 2) }}</pre>
        </div>
      </div>

      <div v-if="testError" class="error-message">
        {{ testError }}
      </div>
    </div>

    <!-- ML Configuration -->
    <div class="config-card">
      <h3>ML Configuration</h3>
      <div class="config-info">
        <div class="info-item">
          <span class="info-label">NBO Model Path:</span>
          <span class="info-value">{{ mlConfig.model_nbo_path }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Churn Model Path:</span>
          <span class="info-value">{{ mlConfig.model_churn_path }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Model Input Size:</span>
          <span class="info-value">{{ mlConfig.model_input_size }}</span>
        </div>
        <div class="info-item">
          <span class="info-label">Feature Mapping:</span>
          <span class="info-value">
            {{ Object.keys(mlConfig.feature_mapping || {}).length }} mappings configured
          </span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, nextTick } from 'vue'
import { configApi, type MLConfig, type MLStatus } from '@/api/services/config'
import { segmentsApi } from '@/api/services/segments'
import type { Segment } from '@/types/loyalty'

const mlStatus = ref<MLStatus>({
  tensorflow_available: false,
  numpy_available: false,
  mock_mode: false,
  models: {},
})

const mlConfig = ref<MLConfig>({
  mock_mode: false,
  model_nbo_path: '',
  model_churn_path: '',
  model_input_size: 10,
  feature_mapping: {},
})

const predictionMode = ref<'single' | 'batch' | 'segment'>('single')
const testCustomerId = ref('')
const testCustomerIds = ref('')
const testSegmentId = ref('')
const testPredictionType = ref<'churn' | 'nbo' | 'rfm' | 'ltv' | 'propensity' | 'product' | 'campaign' | 'default_risk' | 'upsell' | 'engagement'>('churn')
const testing = ref(false)
const testResult = ref<any>(null)
const testError = ref<string | null>(null)
const segments = ref<Segment[]>([])
const loadingSegments = ref(false)
const resultsFilter = ref('')
const showRawJson = ref(false)

const selectedSegment = computed(() => {
  if (!testSegmentId.value) return null
  // Handle both string and number IDs
  const segmentId = typeof testSegmentId.value === 'string' 
    ? parseInt(testSegmentId.value, 10) 
    : testSegmentId.value
  return segments.value.find(s => s.id === segmentId)
})

const filteredResults = computed(() => {
  if (!testResult.value?.results) return []
  let results = testResult.value.results
  
  if (resultsFilter.value) {
    const filter = resultsFilter.value.toLowerCase()
    results = results.filter((item: any) => 
      item.customer_id.toLowerCase().includes(filter)
    )
  }
  
  return results
})

const getRiskClass = (probability: number) => {
  if (probability >= 0.7) return 'high-risk'
  if (probability >= 0.4) return 'medium-risk'
  return 'low-risk'
}

const getRFMSegmentName = (rfmCode: string): string => {
  const segmentNames: Record<string, string> = {
    '555': 'Champions', '554': 'Champions', '544': 'Loyal Customers', '545': 'Champions',
    '455': 'Potential Loyalists', '454': 'Potential Loyalists', '445': 'Potential Loyalists', '444': 'Loyal Customers',
    '355': 'At Risk', '354': 'At Risk', '345': 'At Risk', '344': 'Need Attention',
    '255': 'Cannot Lose Them', '254': 'At Risk', '245': 'At Risk', '244': 'At Risk',
    '155': 'Cannot Lose Them', '154': 'Hibernating', '145': 'About to Sleep', '144': 'Lost',
    '111': 'Lost', '112': 'Lost', '113': 'Lost', '114': 'Lost', '115': 'Lost',
  }
  return segmentNames[rfmCode] || 'Regular'
}

const getPredictionLogic = (result: any, type: string): string => {
  // Use explanation from backend if available (more detailed)
  if (result.explanation) {
    return result.explanation
  }
  
  // Fallback to generic explanations if backend doesn't provide one
  if (type === 'churn') {
    const prob = result.churn_probability || 0
    const risk = result.churn_risk || 'unknown'
    
    if (prob >= 0.9) {
      return `⚠️ Extremely high churn risk (${(prob * 100).toFixed(0)}%). Customer shows strong indicators of leaving. Immediate intervention recommended.`
    } else if (prob >= 0.7) {
      return `🔴 High churn risk (${(prob * 100).toFixed(0)}%). Customer behavior patterns suggest likely churn. Proactive retention actions needed.`
    } else if (prob >= 0.4) {
      return `🟡 Medium churn risk (${(prob * 100).toFixed(0)}%). Some concerning patterns detected. Monitor closely and consider engagement campaigns.`
    } else {
      return `🟢 Low churn risk (${(prob * 100).toFixed(0)}%). Customer shows stable engagement patterns. Continue current relationship management.`
    }
  } else if (type === 'nbo') {
    const confidence = result.confidence || 0
    const offer = result.recommended_offer
    return `💡 Recommended Offer #${offer} with ${(confidence * 100).toFixed(0)}% confidence. Based on customer behavior patterns and purchase history.`
  } else if (type === 'rfm') {
    const rfmCode = result.rfm_segment || `${result.r_score || 0}${result.f_score || 0}${result.m_score || 0}`
    const segment = result.segment || getRFMSegmentName(rfmCode)
    const r = result.r_score || result.recency_score || 0
    const f = result.f_score || result.frequency_score || 0
    const m = result.m_score || result.monetary_score || 0
    const recency = result.recency_days || result.recency || 0
    const frequency = result.frequency_count || result.frequency || 0
    const monetary = result.monetary_value || result.monetary || 0
    
    let interpretation = ''
    if (r <= 2 && f <= 2) {
      interpretation = 'Low engagement - high churn risk. Re-engagement campaigns needed.'
    } else if (r >= 4 && f >= 4 && m >= 4) {
      interpretation = 'High-value customer - maintain premium service and loyalty programs.'
    } else if (r <= 2 && f >= 3) {
      interpretation = 'At risk - frequent but inactive recently. Win-back campaigns recommended.'
    } else if (r >= 3 && f <= 2 && m >= 3) {
      interpretation = 'Potential - recent activity but low frequency. Increase engagement opportunities.'
    } else {
      interpretation = 'Regular customer - standard relationship management.'
    }
    
    return `📊 ${segment} (R:${r}, F:${f}, M:${m}). Last purchase: ${recency} days ago, ${frequency} total transactions, $${monetary.toFixed(2)} lifetime value. ${interpretation}`
  }
  return 'Prediction completed successfully.'
}

const loadMLStatus = async () => {
  try {
    const [statusRes, configRes] = await Promise.all([
      configApi.getMLStatus(),
      configApi.getMLConfig(),
    ])
    
    mlStatus.value = statusRes.data
    mlConfig.value = configRes.data
  } catch (error: any) {
    console.error('Error loading ML status:', error)
    testError.value = 'Error loading ML status'
  }
}

const handleSegmentModeClick = () => {
  predictionMode.value = 'segment'
  testSegmentId.value = ''
  // Load segments if not already loaded
  if (segments.value.length === 0 && !loadingSegments.value) {
    loadSegments()
  }
}

const loadSegments = async () => {
  loadingSegments.value = true
  testError.value = null
  try {
    console.log('Loading segments...')
    const response = await segmentsApi.getAll({ is_active: true })
    console.log('Segments API response:', response)
    console.log('Response data:', response.data)
    
    // Handle different response formats
    let segmentsData = response.data
    if (response.data && typeof response.data === 'object' && 'results' in response.data) {
      // Paginated response
      segmentsData = response.data.results
    } else if (Array.isArray(response.data)) {
      segmentsData = response.data
    } else {
      console.warn('Unexpected response format:', response.data)
      segmentsData = []
    }
    
    segments.value = segmentsData
    console.log(`Loaded ${segments.value.length} segments:`, segments.value)
    
    if (segments.value.length === 0) {
      console.warn('No active segments found')
      testError.value = 'No active segments found. Please create a segment first.'
    }
  } catch (error: any) {
    console.error('Error loading segments:', error)
    console.error('Error details:', {
      message: error.message,
      response: error.response,
      data: error.response?.data,
      status: error.response?.status
    })
    testError.value = `Error loading segments: ${error.response?.data?.detail || error.response?.data?.error || error.message || 'Unknown error'}`
    segments.value = []
  } finally {
    loadingSegments.value = false
  }
}

const testPrediction = async () => {
  // Reset state
  testing.value = true
  testResult.value = null
  testError.value = null

  // Use a timeout as a safety net to ensure testing state resets
  let timeoutId: ReturnType<typeof setTimeout> | null = null
  timeoutId = setTimeout(() => {
    if (testing.value) {
      console.warn('Testing timeout - forcing reset of testing state')
      testing.value = false
    }
  }, 30000) // 30 second timeout

  try {
    if (predictionMode.value === 'single') {
      if (!testCustomerId.value.trim()) {
        testError.value = 'Please enter a customer ID'
        return
      }

      const response = await configApi.testMLPrediction(
        testCustomerId.value.trim(),
        testPredictionType.value
      )
      testResult.value = { ...response.data, mode: 'single', type: testPredictionType.value }
    } else if (predictionMode.value === 'batch') {
      // Batch mode
      const customerIds = testCustomerIds.value
        .split('\n')
        .map(id => id.trim())
        .filter(id => id.length > 0)
      
      if (customerIds.length === 0) {
        testError.value = 'Please enter at least one customer ID'
        return
      }

      if (customerIds.length > 100) {
        testError.value = 'Maximum 100 customers per batch. Please reduce the number.'
        return
      }

      const response = await configApi.testMLPredictionBatch(
        customerIds,
        testPredictionType.value
      )
      testResult.value = { ...response.data, mode: 'batch', type: testPredictionType.value }
    } else if (predictionMode.value === 'segment') {
      // Segment mode
      if (!testSegmentId.value) {
        testError.value = 'Please select a segment'
        return
      }

      if (segments.value.length === 0) {
        testError.value = 'No segments available. Please create a segment first.'
        return
      }

      // Convert segment ID to string for API call
      const segmentId = typeof testSegmentId.value === 'string' 
        ? testSegmentId.value 
        : String(testSegmentId.value)

      const response = await segmentsApi.predictML(
        segmentId,
        testPredictionType.value
      )
      
      // Ensure we have the response data
      if (response && response.data) {
        testResult.value = { 
          ...response.data, 
          mode: 'segment', 
          type: testPredictionType.value 
        }
      } else {
        throw new Error('Invalid response format from API')
      }
    }
  } catch (error: any) {
    console.error('Error in testPrediction:', error)
    testError.value = error.response?.data?.error || error.response?.data?.detail || error.message || 'Error running prediction'
  } finally {
    // Clear timeout
    if (timeoutId) {
      clearTimeout(timeoutId)
    }
    // Always reset testing state - this MUST execute
    testing.value = false
    console.log('Testing state reset to false')
  }
}

onMounted(() => {
  loadMLStatus()
  // Don't load segments on mount - load them when segment mode is selected
  // loadSegments()
})
</script>

<style scoped>
.ml-config {
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

.status-card,
.test-card,
.config-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.status-card h3,
.test-card h3,
.config-card h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.status-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.status-label {
  font-size: 0.875rem;
  color: #666;
}

.status-value {
  font-size: 1rem;
  font-weight: 600;
}

.status-value.available {
  color: #10b981;
}

.status-value.unavailable {
  color: #ef4444;
}

.status-value.enabled {
  color: #f59e0b;
}

.status-value.disabled {
  color: #6b7280;
}

.models-status {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.models-status h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}

.model-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.model-item {
  background: white;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.model-name {
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.model-details {
  display: flex;
  gap: 1rem;
  font-size: 0.875rem;
  color: #666;
}

.model-status {
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

.model-status.exists {
  background: #d1fae5;
  color: #065f46;
}

.model-status.missing {
  background: #fee2e2;
  color: #991b1b;
}

.model-status.loaded {
  background: #dbeafe;
  color: #1e40af;
}

.model-status.not-loaded {
  background: #f3f4f6;
  color: #6b7280;
}

.test-form {
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
  font-size: 0.875rem;
  font-weight: 500;
  color: #374151;
}

.form-group input,
.form-group select {
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  align-self: flex-start;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.test-results {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid #e0e0e0;
}

.test-results h4 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}

.result-content {
  background: #1a1a1a;
  border-radius: 6px;
  padding: 1rem;
  overflow-x: auto;
}

.result-content pre {
  margin: 0;
  color: #00ff00;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  line-height: 1.6;
}

.error-message {
  margin-top: 1rem;
  padding: 1rem;
  background: #fee2e2;
  color: #991b1b;
  border-radius: 6px;
  border: 1px solid #ef4444;
}

.config-info {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.info-item {
  display: flex;
  justify-content: space-between;
  padding: 0.75rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.info-label {
  font-weight: 500;
  color: #374151;
}

.info-value {
  color: #666;
  font-family: monospace;
  font-size: 0.875rem;
}

.mode-toggle {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  flex-wrap: wrap;
}

.mode-btn {
  flex: 1;
  padding: 0.75rem;
  background: white;
  border: 2px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.mode-btn:hover {
  border-color: #2563eb;
  background: #f0f7ff;
}

.mode-btn.active {
  background: #2563eb;
  color: white;
  border-color: #2563eb;
}

.customer-ids-input {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
  font-family: monospace;
  resize: vertical;
}

.form-hint {
  display: block;
  margin-top: 0.25rem;
  color: #666;
  font-size: 0.75rem;
}

.batch-summary {
  margin-bottom: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.summary-stats {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
}

.stat-item {
  font-size: 0.875rem;
}

.stat-item strong {
  color: #374151;
}

.stat-item.success {
  color: #10b981;
}

.stat-item.error {
  color: #ef4444;
}

.no-models-warning {
  padding: 1.5rem;
  background: #fef3c7;
  border: 2px solid #f59e0b;
  border-radius: 8px;
  color: #92400e;
}

.no-models-warning p {
  margin: 0.5rem 0;
}

.no-models-warning ul {
  margin: 0.5rem 0 0.5rem 1.5rem;
}

.no-models-warning code {
  background: #fef3c7;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
  border: 1px solid #f59e0b;
}

.mock-mode-note {
  margin-top: 1rem;
  padding: 0.75rem;
  background: #fef3c7;
  border-radius: 6px;
  border-left: 4px solid #f59e0b;
}

.model-help {
  margin-top: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid #e0e0e0;
}

.model-help small {
  color: #666;
  font-size: 0.75rem;
}

.model-help code {
  background: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.75rem;
}

.aggregated-stats {
  margin-top: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.aggregated-stats h5 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 1rem 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.stat-card {
  padding: 1rem;
  border-radius: 6px;
  text-align: center;
  border: 2px solid;
}

.stat-card.high-risk {
  background: #fee2e2;
  border-color: #ef4444;
  color: #991b1b;
}

.stat-card.medium-risk {
  background: #fef3c7;
  border-color: #f59e0b;
  color: #92400e;
}

.stat-card.low-risk {
  background: #d1fae5;
  border-color: #10b981;
  color: #065f46;
}

.stat-card .stat-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.stat-card .stat-value {
  display: block;
  font-size: 1.5rem;
  font-weight: 700;
  margin-bottom: 0.25rem;
}

.stat-card .stat-percentage {
  display: block;
  font-size: 0.875rem;
  opacity: 0.8;
}

.avg-probability {
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
  text-align: center;
  font-size: 0.875rem;
  color: #374151;
}

.results-table-container {
  margin-top: 1.5rem;
}

.results-table-container h5 {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 1rem 0;
}

.table-controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  gap: 1rem;
}

.filter-input {
  flex: 1;
  max-width: 300px;
  padding: 0.5rem 0.75rem;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  font-size: 0.875rem;
}

.results-count {
  font-size: 0.875rem;
  color: #666;
}

.table-wrapper {
  overflow-x: auto;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.results-table {
  width: 100%;
  border-collapse: collapse;
  background: white;
}

.results-table thead {
  background: #f9fafb;
}

.results-table th {
  padding: 0.75rem 1rem;
  text-align: left;
  font-size: 0.75rem;
  font-weight: 600;
  color: #374151;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 2px solid #e0e0e0;
}

.results-table td {
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #f3f4f6;
  font-size: 0.875rem;
}

.results-table tbody tr:hover {
  background: #f9fafb;
}

.customer-id-cell {
  font-family: monospace;
  font-size: 0.75rem;
}

.probability-cell {
  min-width: 150px;
}

.probability-bar {
  position: relative;
  width: 100%;
  height: 24px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.probability-fill {
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  transition: width 0.3s ease;
  border-radius: 4px;
}

.probability-fill.high-risk {
  background: linear-gradient(90deg, #ef4444, #dc2626);
}

.probability-fill.medium-risk {
  background: linear-gradient(90deg, #f59e0b, #d97706);
}

.probability-fill.low-risk {
  background: linear-gradient(90deg, #10b981, #059669);
}

.probability-text {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
  font-size: 0.75rem;
  font-weight: 600;
  color: white;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  z-index: 1;
}

.risk-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
}

.risk-badge.high {
  background: #fee2e2;
  color: #991b1b;
}

.risk-badge.medium {
  background: #fef3c7;
  color: #92400e;
}

.risk-badge.low {
  background: #d1fae5;
  color: #065f46;
}

.logic-cell {
  max-width: 400px;
  font-size: 0.8125rem;
  line-height: 1.5;
}

.prediction-logic {
  color: #374151;
}

.rfm-segment-cell {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.rfm-segment-code {
  font-family: monospace;
  font-weight: 600;
  color: #6366f1;
  font-size: 0.875rem;
}

.rfm-segment-name {
  font-size: 0.75rem;
  color: #666;
  font-weight: 500;
}

.rfm-distribution {
  margin-top: 1rem;
  padding: 1rem;
  background: white;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.rfm-distribution h5 {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
  margin: 0 0 1rem 0;
}

.rfm-segments-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.rfm-segment-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 4px;
  font-size: 0.875rem;
}

.rfm-segment-label {
  font-weight: 600;
  color: #374151;
  min-width: 150px;
}

.rfm-segment-code-small {
  font-family: monospace;
  color: #6366f1;
  font-weight: 600;
  min-width: 40px;
}

.rfm-segment-count {
  color: #666;
  margin-left: auto;
}

.rfm-segment-percentage {
  color: #999;
  font-size: 0.75rem;
}

.error-table {
  margin-top: 1rem;
}

.error-message-cell {
  color: #ef4444;
  font-size: 0.8125rem;
}

.errors-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 2px solid #fee2e2;
}

.errors-section h5 {
  font-size: 1rem;
  font-weight: 600;
  color: #991b1b;
  margin: 0 0 1rem 0;
}

.raw-json-toggle {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.more-results-note {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 4px;
  font-size: 0.75rem;
  color: #666;
  text-align: center;
}
</style>

