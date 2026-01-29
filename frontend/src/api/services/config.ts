/**
 * Configuration API Service
 */
import { apiClient } from '../client'

export interface XivaConfig {
  base_url: string
  auth_type: 'JWT' | 'TOKEN'
  username: string
  password?: string
  auth_token?: string
  timeout: number
}

export interface DWHConfig {
  type: 'postgresql' | 'oracle' | 'snowflake'
  postgres_connection_string?: string
  oracle_connection_string?: string
  snowflake_account?: string
  user?: string
  password?: string
  customer_features_query?: string
  customer_features_table?: string
}

export interface MLConfig {
  mock_mode: boolean
  model_nbo_path: string
  model_churn_path: string
  model_input_size: number
  feature_mapping: Record<string, string>
}

export interface MLStatus {
  tensorflow_available: boolean
  numpy_available: boolean
  mock_mode: boolean
  models: {
    [key: string]: {
      path: string
      exists: boolean
      loaded: boolean
    }
  }
}

export interface DeliveryChannelConfig {
  id?: number
  channel: 'email' | 'sms' | 'push' | 'in_app'
  is_enabled: boolean
  delivery_mode: 'kafka' | 'api'
  kafka_topic?: string
  kafka_brokers?: string[]
  kafka_config?: Record<string, any>
  api_endpoint?: string
  api_method?: 'POST' | 'PUT' | 'PATCH'
  api_headers?: Record<string, string>
  api_auth_type?: 'none' | 'bearer' | 'basic' | 'api_key'
  api_auth_config?: Record<string, any>
  channel_settings?: Record<string, any>
}

export const configApi = {
  getAll: () => apiClient.get('/config/get_all/'),
  
  // Xiva
  getXivaConfig: () => apiClient.get('/config/xiva/'),
  updateXivaConfig: (config: Partial<XivaConfig>) => 
    apiClient.post('/config/xiva/', config),
  testXivaConnection: () => apiClient.get('/config/xiva/test/'),
  
  // DWH
  getDWHConfig: () => apiClient.get('/config/dwh/'),
  updateDWHConfig: (config: Partial<DWHConfig>) => 
    apiClient.post('/config/dwh/', config),
  testDWHConnection: () => apiClient.get('/config/dwh/test/'),
  
  // ML
  getMLConfig: () => apiClient.get('/config/ml/'),
  getMLStatus: () => apiClient.get('/config/ml/status/'),
  testMLPrediction: (customerId: string, type: 'churn' | 'nbo' | 'rfm' = 'churn') =>
    apiClient.post('/config/ml/test/', { customer_id: customerId, type }),
  testMLPredictionBatch: (customerIds: string[], type: 'churn' | 'nbo' | 'rfm' = 'churn') =>
    apiClient.post('/config/ml/test/', { customer_ids: customerIds, type }),
  
  updateMLConfig: (config: {
    feature_mapping?: Record<string, string>;
    model_input_size?: number;
    model_nbo_path?: string;
    model_churn_path?: string;
    mock_mode?: boolean;
  }) => apiClient.post('/config/ml/', config),
  
  updateDWHFeaturesConfig: (config: {
    customer_features_table?: string;
    customer_features_query?: string;
  }) => apiClient.post('/config/dwh/features/', config),
  
  // Delivery Channels
  getDeliveryChannels: () => apiClient.get('/config/delivery-channels/'),
  updateDeliveryChannels: (channels: Record<string, Partial<DeliveryChannelConfig>>) =>
    apiClient.post('/config/delivery-channels/', channels),
}

