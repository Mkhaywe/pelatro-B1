/**
 * Segments API Service
 */
import { apiClient } from '../client'
import type { Segment, SegmentMember } from '@/types/loyalty'

export const segmentsApi = {
  /**
   * Get all segments
   */
  getAll: (params?: { program?: string; is_active?: boolean }) => 
    apiClient.get<Segment[]>('/segments/', { params }),

  /**
   * Get segment by ID
   */
  getById: (id: string) => apiClient.get<Segment>(`/segments/${id}/`),

  /**
   * Create segment
   */
  create: (data: Partial<Segment>) => apiClient.post<Segment>('/segments/', data),

  /**
   * Update segment
   */
  update: (id: string, data: Partial<Segment>) => apiClient.patch<Segment>(`/segments/${id}/`, data),

  /**
   * Delete segment
   */
  delete: (id: string) => apiClient.delete(`/segments/${id}/`),

  /**
   * Calculate/recalculate segment membership
   */
  calculate: (id: string, customerIds?: string[]) => 
    apiClient.post(`/segments/${id}/calculate/`, { customer_ids: customerIds }),

  /**
   * Get segment members
   */
  getMembers: (id: string) => apiClient.get<SegmentMember[]>(`/segments/${id}/members/`),

  /**
   * Get segment snapshots
   */
  getSnapshots: (id: string) => apiClient.get<any[]>(`/segmentSnapshots/?segment=${id}`),

  /**
   * Get segment metrics
   */
  getMetrics: (id: string) => apiClient.get<any>(`/segments/${id}/metrics/`),

  /**
   * Run ML prediction on segment
   */
  predictML: (id: string, type: 'churn' | 'nbo' | 'rfm' = 'churn') =>
    apiClient.post(`/segments/${id}/ml/predict/`, { type }),

  /**
   * Get ML statistics for segment
   */
  getMLStats: (id: string) => apiClient.get<any>(`/segments/${id}/ml/stats/`),
}

