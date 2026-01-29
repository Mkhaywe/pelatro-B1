/**
 * Gamification API Service - Full Feature Set
 */
import { apiClient } from '../client'

export interface Mission {
  id: string
  name: string
  description: string
  program: string
  mission_type: string
  objective: any
  eligibility_rules: any
  reward_points: number
  start_date: string
  end_date: string
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface MissionProgress {
  id: string
  mission: string
  customer_id: string
  progress: number
  target: number
  is_completed: boolean
  completed_at?: string
  metadata: any
}

export interface Badge {
  id: string
  name: string
  description: string
  icon: string
  program: string
  rarity: string
  criteria: any
  is_active: boolean
  created_at: string
}

export interface BadgeAward {
  id: string
  badge: string
  customer_id: string
  awarded_at: string
  reason?: string
}

export interface Leaderboard {
  id: string
  name: string
  description: string
  program: string
  period: string
  metric: string
  top_n: number
  is_active: boolean
  created_at: string
}

export interface LeaderboardEntry {
  id: string
  leaderboard: string
  customer_id: string
  score: number
  rank: number
  metadata: any
}

export interface Streak {
  id: string
  customer_id: string
  program: string
  streak_type: string
  current_streak: number
  longest_streak: number
  last_activity_date: string
  metadata: any
}

export const gamificationApi = {
  // Missions
  getMissions: (params?: { program?: string; is_active?: boolean }) => 
    apiClient.get<Mission[]>('/missions/', { params }),
  
  getMissionById: (id: string) => apiClient.get<Mission>(`/missions/${id}/`),
  
  createMission: (data: Partial<Mission>) => 
    apiClient.post<Mission>('/missions/', data),
  
  updateMission: (id: string, data: Partial<Mission>) =>
    apiClient.patch<Mission>(`/missions/${id}/`, data),
  
  deleteMission: (id: string) => apiClient.delete(`/missions/${id}/`),
  
  getMissionProgress: (missionId: string, customerId?: string) => {
    const params = customerId ? { customer_id: customerId } : {}
    return apiClient.get<MissionProgress[]>(`/missions/${missionId}/progress/`, { params })
  },
  
  // Mission Progress
  getMissionProgressList: (params?: { mission?: string; customer_id?: string; is_completed?: boolean }) =>
    apiClient.get<MissionProgress[]>('/missionProgress/', { params }),
  
  // Badges
  getBadges: (params?: { program?: string; is_active?: boolean }) => 
    apiClient.get<Badge[]>('/badges/', { params }),
  
  getBadgeById: (id: string) => apiClient.get<Badge>(`/badges/${id}/`),
  
  createBadge: (data: Partial<Badge>) => 
    apiClient.post<Badge>('/badges/', data),
  
  updateBadge: (id: string, data: Partial<Badge>) =>
    apiClient.patch<Badge>(`/badges/${id}/`, data),
  
  deleteBadge: (id: string) => apiClient.delete(`/badges/${id}/`),
  
  // Badge Awards
  getBadgeAwards: (params?: { badge?: string; customer_id?: string }) =>
    apiClient.get<BadgeAward[]>('/badgeAwards/', { params }),
  
  // Leaderboards
  getLeaderboards: (params?: { program?: string; is_active?: boolean }) => 
    apiClient.get<Leaderboard[]>('/leaderboards/', { params }),
  
  getLeaderboardById: (id: string) => apiClient.get<Leaderboard>(`/leaderboards/${id}/`),
  
  createLeaderboard: (data: Partial<Leaderboard>) =>
    apiClient.post<Leaderboard>('/leaderboards/', data),
  
  updateLeaderboard: (id: string, data: Partial<Leaderboard>) =>
    apiClient.patch<Leaderboard>(`/leaderboards/${id}/`, data),
  
  deleteLeaderboard: (id: string) => apiClient.delete(`/leaderboards/${id}/`),
  
  getLeaderboardEntries: (leaderboardId: string) =>
    apiClient.get<LeaderboardEntry[]>(`/leaderboards/${leaderboardId}/entries/`),
  
  // Leaderboard Entries
  getLeaderboardEntryList: (params?: { leaderboard?: string; customer_id?: string }) =>
    apiClient.get<LeaderboardEntry[]>('/leaderboardEntries/', { params }),
  
  // Streaks
  getStreaks: (params?: { customer_id?: string; program?: string; streak_type?: string }) =>
    apiClient.get<Streak[]>('/streaks/', { params }),
  
  getStreakById: (id: string) => apiClient.get<Streak>(`/streaks/${id}/`),
  
  createStreak: (data: Partial<Streak>) =>
    apiClient.post<Streak>('/streaks/', data),
  
  updateStreak: (id: string, data: Partial<Streak>) =>
    apiClient.patch<Streak>(`/streaks/${id}/`, data),
}
