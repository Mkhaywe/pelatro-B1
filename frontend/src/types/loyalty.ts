export interface LoyaltyTier {
  id?: number
  name: string
  min_points: number
  priority: number
  benefits: string
}

export interface LoyaltyProgram {
  id: number
  name: string
  description: string
  start_date: string
  end_date: string
  is_active: boolean
  tiers?: LoyaltyTier[]
  earn_rules?: any
  burn_rules?: any
  points_expiry_rules?: any
  earn_caps?: any
  created_at: string
  updated_at: string
}

export interface LoyaltyAccount {
  id: number
  customer_id: string
  program: number
  tier: number | null
  points_balance: number
  status: string
  created_at: string
  updated_at: string
}

export interface LoyaltyTransaction {
  id: number
  account: number
  amount: number
  transaction_type: 'earn' | 'redeem' | 'adjust'
  description: string
  created_at: string
}

export interface Campaign {
  id: number
  name: string
  description: string
  status: 'draft' | 'pending_review' | 'approved' | 'active' | 'paused' | 'retired'
  program: number | null
  segment: number | null
  start_date: string | null
  end_date: string | null
  eligibility_rules?: any
  event_triggers?: any
  schedule_triggers?: any
  threshold_triggers?: any
  channels: string[]
  channel_settings?: any
  frequency_cap: number
  frequency_period: 'day' | 'week' | 'month'
  experiment?: number | null
  version: number
  created_at: string
  updated_at: string
}

export interface Segment {
  id: number
  name: string
  description: string
  program: number | null
  rules: any[]
  is_dynamic: boolean
  is_rfm: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  active_member_count?: number
}

export interface Mission {
  id: number
  name: string
  description: string
  program: number
  mission_type: 'points_earn' | 'points_burn' | 'transaction_count' | 'streak' | 'custom'
  objective: Record<string, any>
  reward_points: number
  start_date: string
  end_date: string
  is_active: boolean
}

export interface Badge {
  id: number
  name: string
  description: string
  program: number | null
  icon_url: string
  rarity: 'common' | 'rare' | 'epic' | 'legendary'
  is_active: boolean
}

export interface LoyaltyTier {
  id: number
  program: number
  name: string
  description: string
  min_points: number
  benefits: string
  priority: number
}

export interface SegmentMember {
  id: number
  segment: number
  customer_id: string
  joined_at: string
  left_at: string | null
  is_active: boolean
}

export interface CampaignExecution {
  id: number
  campaign: number
  customer_id: string
  triggered_at: string
  delivered_at: string | null
  opened_at: string | null
  clicked_at: string | null
  converted_at: string | null
  channel: string
  message_id: string
}

export interface Journey {
  id: string
  name: string
  description?: string
  status: 'draft' | 'active' | 'paused' | 'archived'
  is_active: boolean
  entry_segment?: string | null
  program?: string | null
  structure?: any // JSON structure for nodes and edges
  created_at: string
  updated_at: string
}

