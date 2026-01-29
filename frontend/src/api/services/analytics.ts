/**
 * Analytics API Service
 */
import { apiClient } from '../client'

export interface AnalyticsTimeRange {
  start_date: string
  end_date: string
}

export interface ProgramPerformance {
  program_id: number
  program_name: string
  total_members: number
  points_issued: number
  points_redeemed: number
  active_campaigns: number
  revenue: number
}

export interface CampaignPerformance {
  campaign_id: number
  campaign_name: string
  triggered: number
  delivered: number
  opened: number
  clicked: number
  converted: number
  conversion_rate: number
}

export interface SegmentAnalytics {
  segment_id: number
  segment_name: string
  member_count: number
  growth_rate: number
  avg_points_balance: number
  avg_lifetime_value: number
}

export interface TransactionAnalytics {
  date: string
  earn_count: number
  redeem_count: number
  adjust_count: number
  total_points: number
}

export const analyticsApi = {
  /**
   * Get program performance analytics
   */
  getProgramPerformance: (timeRange?: AnalyticsTimeRange) => 
    apiClient.get<ProgramPerformance[]>('/loyaltyAnalytics/program-performance/', {
      params: timeRange
    }),

  /**
   * Get campaign performance analytics
   */
  getCampaignPerformance: (timeRange?: AnalyticsTimeRange) => 
    apiClient.get<CampaignPerformance[]>('/loyaltyAnalytics/campaign-performance/', {
      params: timeRange
    }),

  /**
   * Get segment analytics
   */
  getSegmentAnalytics: () => 
    apiClient.get<SegmentAnalytics[]>('/loyaltyAnalytics/segment-analytics/'),

  /**
   * Get transaction analytics
   */
  getTransactionAnalytics: (timeRange?: AnalyticsTimeRange) => 
    apiClient.get<TransactionAnalytics[]>('/loyaltyAnalytics/transaction-analytics/', {
      params: timeRange
    }),

  /**
   * Get revenue analytics
   */
  getRevenueAnalytics: (timeRange?: AnalyticsTimeRange) => 
    apiClient.get<any>('/loyaltyAnalytics/revenue-analytics/', {
      params: timeRange
    }),

  /**
   * Get customer cohort analysis
   */
  getCohortAnalysis: (cohortType: 'month' | 'week' | 'day' = 'month') => 
    apiClient.get<any>(`/loyaltyAnalytics/cohort-analysis/?cohort_type=${cohortType}`),

  /**
   * Export analytics report
   */
  exportReport: (data: {
    report_type: 'transactions' | 'programs' | 'campaigns' | 'customers'
    format?: 'csv' | 'json'
    filters?: any
    date_from?: string
    date_to?: string
  }) => apiClient.post('/loyaltyAnalytics/export/', data, { responseType: 'blob' }),
}

