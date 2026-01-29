/**
 * Partners API Service
 */
import { apiClient } from '../client'

export interface Partner {
  id: string
  name: string
  type: string
  status: string
  api_key: string
}

export interface PartnerProgram {
  id: string
  partner: string
  program: any
  earn_rate: number
  burn_rate: number
  is_active: boolean
}

export interface Coalition {
  id: string
  name: string
  description: string
  shared_points: boolean
  is_active: boolean
}

export interface PartnerSettlement {
  id: string
  partner: string
  program: any
  period_start: string
  period_end: string
  points_issued: number
  points_redeemed: number
  settlement_amount: number
  status: string
}

export const partnersApi = {
  getAll: () => apiClient.get('/partners/'),
  getById: (id: string) => apiClient.get(`/partners/${id}/`),
  create: (data: Partial<Partner>) => apiClient.post('/partners/', data),
  update: (id: string, data: Partial<Partner>) => apiClient.patch(`/partners/${id}/`, data),
  delete: (id: string) => apiClient.delete(`/partners/${id}/`),
  getPrograms: (id: string) => apiClient.get<PartnerProgram[]>(`/partners/${id}/programs/`),
  getCoalitions: (id: string) => apiClient.get<Coalition[]>(`/partners/${id}/coalitions/`),
  getSettlements: (id: string) => apiClient.get<PartnerSettlement[]>(`/partners/${id}/settlements/`),
  generateApiKey: (id: string) => apiClient.post<{api_key: string}>(`/partners/${id}/generate-api-key/`),
}

