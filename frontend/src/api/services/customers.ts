/**
 * Customer API Service
 */
import { apiClient } from '../client'
import type { LoyaltyAccount, LoyaltyTransaction } from '@/types/loyalty'

export interface CustomerPromotion {
  id: number
  name: string
  description: string
  is_active: boolean
  start_date: string
  end_date: string
}

export const customersApi = {
  /**
   * Get all loyalty accounts for a customer
   */
  getAccounts: (customerId: string) => 
    apiClient.get<LoyaltyAccount[]>(`/loyaltyAccounts/customer/${customerId}/`),

  /**
   * Get all transactions for a customer
   */
  getTransactions: (customerId: string) => 
    apiClient.get<LoyaltyTransaction[]>(`/loyaltyTransactions/customer/${customerId}/`),

  /**
   * Get active promotions for a customer
   */
  getPromotions: (customerId: string) => 
    apiClient.get<CustomerPromotion[]>(`/promotions/customer/${customerId}/`),
}

