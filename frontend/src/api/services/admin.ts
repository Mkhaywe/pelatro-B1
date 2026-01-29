/**
 * Admin API Service
 */
import { apiClient } from '../client'

export interface Role {
  id: string
  name: string
  description: string
}

export interface Permission {
  id: string
  name: string
  codename: string
}

export const adminApi = {
  getRoles: () => apiClient.get('/roles/'),
  getPermissions: () => apiClient.get('/permissions/'),
  getAuditLogs: (params?: { limit?: number }) => 
    apiClient.get('/auditLogs/', { params }),
}

