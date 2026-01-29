/**
 * Experiments (A/B Tests) API Service
 */
import { apiClient } from '../client'

export interface Experiment {
  id: string
  name: string
  description: string
  status: string
  start_date: string
  end_date: string
}

export const experimentsApi = {
  getAll: () => apiClient.get('/experiments/'),
  getById: (id: string) => apiClient.get(`/experiments/${id}/`),
  create: (data: Partial<Experiment>) => apiClient.post('/experiments/', data),
  update: (id: string, data: Partial<Experiment>) => apiClient.patch(`/experiments/${id}/`, data),
  delete: (id: string) => apiClient.delete(`/experiments/${id}/`),
  getResults: (id: string) => apiClient.get(`/experiments/${id}/results/`),
  getAssignments: (id: string) => apiClient.get(`/experimentAssignments/?experiment=${id}`),
  start: (id: string) => apiClient.post(`/experiments/${id}/start/`),
  stop: (id: string) => apiClient.post(`/experiments/${id}/stop/`),
}

