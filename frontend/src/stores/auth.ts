import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/services/auth'
import type { User } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const token = ref<string | null>(localStorage.getItem('auth_token'))
  const permissions = ref<string[]>([])
  
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  
  async function login(username: string, password: string) {
    try {
      const response = await authApi.login(username, password)
      token.value = response.data.token
      user.value = {
        id: response.data.user.id.toString(),
        username: response.data.user.username,
        email: response.data.user.email,
        first_name: response.data.user.first_name,
        last_name: response.data.user.last_name,
        is_staff: response.data.user.is_staff,
        is_superuser: response.data.user.is_superuser,
      }
      permissions.value = response.data.permissions
      localStorage.setItem('auth_token', token.value)
      return { token: token.value, user: user.value }
    } catch (error: any) {
      const errorMessage = error.response?.data?.error || 'Login failed'
      throw new Error(errorMessage)
    }
  }
  
  async function logout() {
    try {
      if (token.value) {
        await authApi.logout(token.value)
      }
    } catch (error) {
      // Continue with logout even if API call fails
      console.error('Logout API call failed:', error)
    } finally {
      token.value = null
      user.value = null
      permissions.value = []
      localStorage.removeItem('auth_token')
    }
  }
  
  async function fetchUser() {
    if (!token.value) {
      throw new Error('No token available')
    }
    
    try {
      const response = await authApi.getMe(token.value)
      user.value = {
        id: response.data.user.id.toString(),
        username: response.data.user.username,
        email: response.data.user.email,
        first_name: response.data.user.first_name,
        last_name: response.data.user.last_name,
        is_staff: response.data.user.is_staff,
        is_superuser: response.data.user.is_superuser,
      }
      permissions.value = response.data.permissions
      return response.data
    } catch (error) {
      logout()
      throw error
    }
  }
  
  function hasPermission(permission: string): boolean {
    if (!permissions.value.length) return false
    // Wildcard means all permissions
    if (permissions.value.includes('*')) return true
    return permissions.value.includes(permission)
  }
  
  // Initialize: try to fetch user if token exists
  if (token.value) {
    fetchUser().catch(() => {
      // Token is invalid, clear it
      token.value = null
      localStorage.removeItem('auth_token')
    })
  }
  
  return {
    user,
    token,
    permissions,
    isAuthenticated,
    login,
    logout,
    fetchUser,
    hasPermission
  }
})

