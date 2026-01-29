/**
 * Journeys API Service
 */
import { apiClient } from '../client'
import type { Journey } from '@/types/loyalty'

export const journeysApi = {
  getAll: () => apiClient.get<{ results: Journey[] }>('/journeys/'),
  getById: (id: string) => apiClient.get<Journey>(`/journeys/${id}/`),
  create: (data: Partial<Journey>) => apiClient.post<Journey>('/journeys/', data),
  update: (id: string, data: Partial<Journey>) => apiClient.patch<Journey>(`/journeys/${id}/`, data),
  delete: (id: string) => apiClient.delete(`/journeys/${id}/`),
  preview: (id: string, customerId?: string) => 
    apiClient.post<any>(`/journeys/${id}/preview/`, { customer_id: customerId || 'test-customer-123' }),
}

