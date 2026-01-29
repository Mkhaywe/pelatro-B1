/**
 * Campaigns API Service
 */
import { apiClient } from '../client'
import type { Campaign, CampaignExecution } from '@/types/loyalty'

export const campaignsApi = {
  /**
   * Get all campaigns
   */
  getAll: (params?: { status?: string; program?: string }) => 
    apiClient.get<Campaign[]>('/campaigns/', { params }),

  /**
   * Get campaign by ID
   */
  getById: (id: string) => apiClient.get<Campaign>(`/campaigns/${id}/`),

  /**
   * Create campaign
   */
  create: (data: Partial<Campaign>) => apiClient.post<Campaign>('/campaigns/', data),

  /**
   * Update campaign
   */
  update: (id: string, data: Partial<Campaign>) => apiClient.patch<Campaign>(`/campaigns/${id}/`, data),

  /**
   * Delete campaign
   */
  delete: (id: string) => apiClient.delete(`/campaigns/${id}/`),

  /**
   * Activate campaign
   */
  activate: (id: string) => apiClient.post(`/campaigns/${id}/activate/`),

  /**
   * Pause campaign
   */
  pause: (id: string) => apiClient.post(`/campaigns/${id}/pause/`),

  /**
   * Get campaign performance
   */
  getPerformance: (id: string) => apiClient.get(`/campaigns/${id}/performance/`),

  /**
   * Get campaign executions
   */
  getExecutions: (campaignId: string) => apiClient.get<CampaignExecution[]>(`/campaignExecutions/?campaign=${campaignId}`),
}

