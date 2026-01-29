/**
 * External System Integration API Service (Xiva, etc.)
 */
import axios, { AxiosInstance } from 'axios'
import { useAuthStore } from '@/stores/auth'

// External API client (different base URL)
const externalApiClient: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL?.replace('/api/loyalty/v1', '') || '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

// Request interceptor for auth
externalApiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Token ${authStore.token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

export interface XivaCustomer {
  id: string
  name: string
  status: string
  customerType?: string
  customer_type?: string
  email?: string
  phone?: string
}

export const externalApi = {
  /**
   * Search customers in Xiva
   */
  searchCustomers: (params?: { search?: string; status?: string; customer_type?: string; ordering?: string }) =>
    externalApiClient.get<{ count: number; results: XivaCustomer[] }>('/external/xiva/customers/', { params }),

  /**
   * Get customer from Xiva
   */
  getCustomer: (customerId: string) =>
    externalApiClient.get<XivaCustomer>(`/external/xiva/customers/${customerId}/`),

  /**
   * Get customer 360 services from Xiva
   */
  getCustomer360Services: (customerId: string) =>
    externalApiClient.get(`/external/xiva/customers/${customerId}/360/services/`),

  /**
   * Get customer 360 usage from Xiva
   */
  getCustomer360Usage: (customerId: string, params?: { start_date?: string; end_date?: string; usage_type?: string; current_month_only?: boolean }) =>
    externalApiClient.get(`/external/xiva/customers/${customerId}/360/usage/`, { params }),

  /**
   * Get customer full context from Xiva
   */
  getCustomerContext: (customerId: string) =>
    externalApiClient.get(`/external/xiva/customers/${customerId}/context/`),

  /**
   * Test Xiva connection
   */
  testXivaConnection: () =>
    externalApiClient.get('/external/xiva/test/'),
}

