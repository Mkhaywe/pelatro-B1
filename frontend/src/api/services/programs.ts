/**
 * Loyalty Programs API Service
 */
import { apiClient } from '../client'
import type { LoyaltyProgram, LoyaltyTier } from '@/types/loyalty'

export const programsApi = {
  /**
   * Get all programs
   */
  getAll: () => apiClient.get<LoyaltyProgram[]>('/loyaltyPrograms/'),

  /**
   * Get program by ID
   */
  getById: (id: string) => apiClient.get<LoyaltyProgram>(`/loyaltyPrograms/${id}/`),

  /**
   * Create program
   */
  create: (data: Partial<LoyaltyProgram>) => apiClient.post<LoyaltyProgram>('/loyaltyPrograms/', data),

  /**
   * Update program
   */
  update: (id: string, data: Partial<LoyaltyProgram>) => apiClient.patch<LoyaltyProgram>(`/loyaltyPrograms/${id}/`, data),

  /**
   * Delete program
   */
  delete: (id: string) => apiClient.delete(`/loyaltyPrograms/${id}/`),

  /**
   * Get program tiers
   */
  getTiers: (programId: string) => apiClient.get<LoyaltyTier[]>(`/loyaltyPrograms/${programId}/tiers/`),

  /**
   * Get program analytics
   */
  getAnalytics: (id: string) => apiClient.get<any>(`/loyaltyPrograms/${id}/analytics/`),

  /**
   * Simulate program behavior
   */
  simulate: (id: string, data: { customer_id?: string; transaction_amount?: number; transaction_context?: any }) =>
    apiClient.post<any>(`/loyaltyPrograms/${id}/simulate/`, data),
}

