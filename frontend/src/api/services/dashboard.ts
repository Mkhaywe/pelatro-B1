/**
 * Dashboard API Service
 */
import { apiClient } from '../client'

export interface DashboardStats {
  active_programs: number
  active_campaigns: number
  total_members: number
  points_issued_this_month: number
  points_redeemed_this_month: number
  recent_activity: Array<{
    id: string
    customer_id: string
    program_name: string
    type: string
    amount: number
    description: string
    timestamp: string
  }>
}

export const dashboardApi = {
  /**
   * Get dashboard statistics
   */
  getStats: () => apiClient.get<DashboardStats>('/dashboard/stats/'),
}

