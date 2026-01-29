/**
 * Authentication API Service
 */
import axios from 'axios'

const authClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json'
  }
})

export interface LoginResponse {
  token: string
  user: {
    id: number
    username: string
    email: string
    first_name: string
    last_name: string
    is_staff: boolean
    is_superuser: boolean
  }
  permissions: string[]
}

export interface UserInfo {
  user: {
    id: number
    username: string
    email: string
    first_name: string
    last_name: string
    is_staff: boolean
    is_superuser: boolean
  }
  permissions: string[]
}

export const authApi = {
  /**
   * Login with username and password
   */
  login: (username: string, password: string) =>
    authClient.post<LoginResponse>('/auth/login/', { username, password }),

  /**
   * Logout (requires authentication)
   */
  logout: (token: string) =>
    authClient.post('/auth/logout/', {}, {
      headers: { Authorization: `Token ${token}` }
    }),

  /**
   * Get current user info (requires authentication)
   */
  getMe: (token: string) =>
    authClient.get<UserInfo>('/auth/me/', {
      headers: { Authorization: `Token ${token}` }
    }),

  /**
   * Check if user has a specific permission
   */
  checkPermission: (token: string, permission: string) =>
    authClient.post('/auth/check-permission/', { permission }, {
      headers: { Authorization: `Token ${token}` }
    }),
}

