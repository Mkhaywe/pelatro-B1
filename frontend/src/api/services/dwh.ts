/**
 * DWH Integration API Service
 */
import { apiClient } from '../client'

export interface DWHColumn {
  name: string
  type: string
  description?: string
  category?: string
  data_source?: string
}

export const dwhApi = {
  /**
   * Get available DWH columns/fields
   */
  getColumns: () => apiClient.get<DWHColumn[]>('/dwh/columns/'),
  
  /**
   * Get customer features
   */
  getCustomerFeatures: (customerId: string) => 
    apiClient.get(`/dwh/customer-features/${customerId}/`),
}

