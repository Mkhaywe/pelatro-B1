/**
 * ML & DWH Integration API Service
 */
import { apiClient } from '../client'

export interface NBOResult {
  customer_id: string
  offer_scores: number[]
  recommended_offer: number
  confidence: number
}

export interface ChurnResult {
  customer_id: string
  churn_probability: number
  churn_risk: 'low' | 'medium' | 'high'
}

export interface RFMResult {
  customer_id: string
  recency: number
  frequency: number
  monetary: number
  r_score: number
  f_score: number
  m_score: number
  rfm_segment: string
}

export interface CustomerFeatures {
  [key: string]: any
}

export const mlApi = {
  /**
   * Predict Next Best Offer
   */
  getNBO: (customerId: string) => 
    apiClient.post<NBOResult>('/dwh/ml/nbo/', { customer_id: customerId }),
  
  predictNBO: (customerId: string) => 
    apiClient.post<NBOResult>('/dwh/ml/nbo/', { customer_id: customerId }),

  /**
   * Predict churn
   */
  getChurn: (customerId: string) => 
    apiClient.post<ChurnResult>('/dwh/ml/churn/', { customer_id: customerId }),
  
  predictChurn: (customerId: string) => 
    apiClient.post<ChurnResult>('/dwh/ml/churn/', { customer_id: customerId }),

  /**
   * Calculate RFM
   */
  getRFM: (customerId: string) => 
    apiClient.post<RFMResult>('/dwh/ml/rfm/', { customer_id: customerId }),
  
  calculateRFM: (customerId: string) => 
    apiClient.post<RFMResult>('/dwh/ml/rfm/', { customer_id: customerId }),

  /**
   * Get customer features from DWH
   */
  getCustomerFeatures: (customerId: string) => 
    apiClient.get<CustomerFeatures>(`/dwh/features/${customerId}/`),

  /**
   * Batch get customer features
   */
  batchGetFeatures: (customerIds: string[]) => 
    apiClient.post<Record<string, CustomerFeatures>>('/dwh/features/batch/', { customer_ids: customerIds }),

  /**
   * Invalidate feature cache
   */
  invalidateCache: (customerId?: string, customerIds?: string[]) => 
    apiClient.post('/dwh/cache/invalidate/', { customer_id: customerId, customer_ids: customerIds }),

  /**
   * List available DWH columns
   * @param source - Data source: 'dwh', 'xiva', or 'auto' (default: 'auto')
   */
  getDWHColumns: (source: string = 'auto') => 
    apiClient.get<Array<{name: string; type: string; description?: string; data_source?: string; category?: string; display_name?: string}>>(
      `/dwh/columns/?source=${source}`
    ),

  /**
   * List available event types
   */
  getEventTypes: () => apiClient.get<Array<{value: string; label: string; category: string}>>('/dwh/event-types/'),
}

