<template>
  <div class="gamification-dashboard">
    <div class="page-header">
      <div>
        <h1 class="page-title">Gamification</h1>
        <p class="page-description">Manage missions, badges, leaderboards, and streaks</p>
      </div>
      <div class="header-actions">
        <button 
          v-if="activeTab === 'missions'" 
          @click="showCreateMission = true" 
          class="btn-primary"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Create Mission</span>
        </button>
        <button 
          v-if="activeTab === 'badges'" 
          @click="showCreateBadge = true" 
          class="btn-primary"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Create Badge</span>
        </button>
        <button 
          v-if="activeTab === 'leaderboards'" 
          @click="showCreateLeaderboard = true" 
          class="btn-primary"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Create Leaderboard</span>
        </button>
        <button 
          v-if="activeTab === 'streaks'" 
          @click="showCreateStreak = true" 
          class="btn-primary"
        >
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <span>Create Streak</span>
        </button>
      </div>
    </div>

    <!-- Stats Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #6366f1, #8b5cf6);">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">Active Missions</div>
          <div class="stat-value">{{ activeMissionsCount }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #10b981, #34d399);">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M4 22h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">Total Badges</div>
          <div class="stat-value">{{ badges.length }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #f59e0b, #fbbf24);">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M4 22h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">Leaderboards</div>
          <div class="stat-value">{{ leaderboards.length }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon" style="background: linear-gradient(135deg, #3b82f6, #60a5fa);">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
        </div>
        <div class="stat-content">
          <div class="stat-label">Active Streaks</div>
          <div class="stat-value">{{ activeStreaksCount }}</div>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button 
        v-for="tab in tabs" 
        :key="tab.id"
        @click="activeTab = tab.id"
        :class="['tab-button', { active: activeTab === tab.id }]"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Missions Tab -->
      <div v-if="activeTab === 'missions'" class="tab-panel">
        <div class="section-header">
          <h2>Missions</h2>
          <div class="section-actions">
            <select v-model="missionFilter" class="filter-select">
              <option value="">All Missions</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
            <button @click="loadMissions" class="btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <div v-if="filteredMissions.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <circle cx="12" cy="10" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No missions found. Create your first mission to get started.</p>
        </div>

        <div v-else class="missions-grid">
          <div v-for="mission in filteredMissions" :key="mission.id" class="mission-card">
            <div class="card-header">
              <h3>{{ mission.name }}</h3>
              <div class="card-actions">
                <button @click="viewMissionProgress(mission.id)" class="icon-btn" title="View Progress">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <button @click="editMission(mission)" class="icon-btn" title="Edit">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <button @click="deleteMission(mission.id)" class="icon-btn icon-btn-danger" title="Delete">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
            <p class="card-description">{{ mission.description || 'No description' }}</p>
            <div class="card-meta">
              <span class="status-badge" :class="mission.status === 'active' ? 'active' : 'inactive'">
                <span class="status-dot"></span>
                {{ mission.status === 'active' ? 'Active' : 'Inactive' }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M20 7h-4M4 7h4m0 0v12m0-12a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2m-8 0V5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2M4 7v12a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ mission.reward_points }} points
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                {{ formatDate(mission.start_date) }} - {{ formatDate(mission.end_date) }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Badges Tab -->
      <div v-if="activeTab === 'badges'" class="tab-panel">
        <div class="section-header">
          <h2>Badges</h2>
          <div class="section-actions">
            <select v-model="badgeFilter" class="filter-select">
              <option value="">All Badges</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>
            <button @click="loadBadges" class="btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <div v-if="filteredBadges.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M6 9H4.5a2.5 2.5 0 0 1 0-5H6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 9h1.5a2.5 2.5 0 0 0 0-5H18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M4 22h16" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20.24 7 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20.24 17 22" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <path d="M18 2H6v7a6 6 0 0 0 12 0V2Z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No badges found. Create your first badge to get started.</p>
        </div>

        <div v-else class="badges-grid">
          <div v-for="badge in filteredBadges" :key="badge.id" class="badge-card">
            <div class="badge-icon-large">{{ badge.icon || '🏆' }}</div>
            <div class="badge-content">
              <h3>{{ badge.name }}</h3>
              <p>{{ badge.description || 'No description' }}</p>
              <div class="badge-meta">
                <span class="status-badge" :class="badge.status === 'active' ? 'active' : 'inactive'">
                  <span class="status-dot"></span>
                  {{ badge.status === 'active' ? 'Active' : 'Inactive' }}
                </span>
                <span class="rarity-badge" :class="badge.rarity?.toLowerCase() || 'common'">
                  {{ badge.rarity || 'Common' }}
                </span>
              </div>
            </div>
            <div class="card-actions">
              <button @click="viewBadgeAwards(badge.id)" class="icon-btn" title="View Awards">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <button @click="editBadge(badge)" class="icon-btn" title="Edit">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
              <button @click="deleteBadge(badge.id)" class="icon-btn icon-btn-danger" title="Delete">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Leaderboards Tab -->
      <div v-if="activeTab === 'leaderboards'" class="tab-panel">
        <div class="section-header">
          <h2>Leaderboards</h2>
          <div class="section-actions">
            <button @click="loadLeaderboards" class="btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <div v-if="leaderboards.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No leaderboards found. Create your first leaderboard to get started.</p>
        </div>

        <div v-else class="leaderboards-list">
          <div v-for="leaderboard in leaderboards" :key="leaderboard.id" class="leaderboard-card">
            <div class="card-header">
              <div>
                <h3>{{ leaderboard.name }}</h3>
                <p class="card-description">{{ leaderboard.description || 'No description' }}</p>
              </div>
              <div class="card-actions">
                <button @click="viewLeaderboardEntries(leaderboard.id)" class="icon-btn" title="View Entries">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <circle cx="12" cy="12" r="3" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <button @click="editLeaderboard(leaderboard)" class="icon-btn" title="Edit">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <button @click="deleteLeaderboard(leaderboard.id)" class="icon-btn icon-btn-danger" title="Delete">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </div>
            <div class="leaderboard-meta">
              <span class="status-badge" :class="leaderboard.status === 'active' ? 'active' : 'inactive'">
                <span class="status-dot"></span>
                {{ leaderboard.status === 'active' ? 'Active' : 'Inactive' }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <polyline points="12 6 12 12 16 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Period: {{ leaderboard.period }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Metric: {{ leaderboard.metric }}
              </span>
              <span class="meta-item">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <circle cx="9" cy="7" r="4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                </svg>
                Top {{ leaderboard.top_n || 100 }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Streaks Tab -->
      <div v-if="activeTab === 'streaks'" class="tab-panel">
        <div class="section-header">
          <h2>Streaks</h2>
          <div class="section-actions">
            <input 
              v-model="streakSearch" 
              type="text" 
              placeholder="Search by customer ID..." 
              class="search-input"
            />
            <button @click="loadStreaks" class="btn-secondary">
              <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                <polyline points="23 4 23 10 17 10" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <polyline points="1 20 1 14 7 14" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              <span>Refresh</span>
            </button>
          </div>
        </div>

        <div v-if="filteredStreaks.length === 0" class="empty-state">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <polyline points="23 6 13.5 15.5 8.5 10.5 1 18" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <polyline points="17 6 23 6 23 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          <p>No streaks found.</p>
        </div>

        <div v-else class="streaks-table">
          <table class="data-table">
            <thead>
              <tr>
                <th>Customer ID</th>
                <th>Type</th>
                <th>Current Streak</th>
                <th>Longest Streak</th>
                <th>Last Activity</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="streak in filteredStreaks" :key="streak.id">
                <td>{{ formatCustomerId(streak.customer_id) }}</td>
                <td>{{ streak.streak_type }}</td>
                <td>
                  <span class="streak-value">{{ streak.current_streak }}</span>
                </td>
                <td>{{ streak.longest_streak }}</td>
                <td>{{ formatDate(streak.last_activity_date) }}</td>
                <td>
                  <button @click="editStreak(streak)" class="icon-btn" title="Edit">
                    <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                      <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                      <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Create/Edit Mission Modal -->
    <div v-if="showCreateMission || editingMission" class="modal-overlay" @click="closeMissionModal">
      <div class="modal" @click.stop>
        <h2>{{ editingMission ? 'Edit Mission' : 'Create Mission' }}</h2>
        <form @submit.prevent="saveMission">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="missionForm.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="missionForm.description"></textarea>
          </div>
          <div class="form-group">
            <label>Program *</label>
            <select v-model="missionForm.program" required>
              <option value="">-- Select Program --</option>
              <option v-for="prog in programs" :key="prog.id" :value="prog.id">{{ prog.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>Mission Type *</label>
            <select v-model="missionForm.mission_type" required>
              <option value="points_earn">Earn Points</option>
              <option value="points_burn">Burn Points</option>
              <option value="transaction_count">Transaction Count</option>
              <option value="streak">Streak</option>
              <option value="custom">Custom</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Start Date *</label>
              <input v-model="missionForm.start_date" type="datetime-local" required />
            </div>
            <div class="form-group">
              <label>End Date *</label>
              <input v-model="missionForm.end_date" type="datetime-local" required />
            </div>
          </div>
          <div class="form-group">
            <label>Reward Points</label>
            <input v-model.number="missionForm.reward_points" type="number" min="0" />
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="missionForm.status">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeMissionModal" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Create/Edit Badge Modal -->
    <div v-if="showCreateBadge || editingBadge" class="modal-overlay" @click="closeBadgeModal">
      <div class="modal" @click.stop>
        <h2>{{ editingBadge ? 'Edit Badge' : 'Create Badge' }}</h2>
        <form @submit.prevent="saveBadge">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="badgeForm.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="badgeForm.description"></textarea>
          </div>
          <div class="form-group">
            <label>Icon</label>
            <input v-model="badgeForm.icon" placeholder="🏆" />
          </div>
          <div class="form-group">
            <label>Program</label>
            <select v-model="badgeForm.program">
              <option value="">-- Select Program --</option>
              <option v-for="prog in programs" :key="prog.id" :value="prog.id">{{ prog.name }}</option>
            </select>
          </div>
          <div class="form-group">
            <label>Rarity</label>
            <select v-model="badgeForm.rarity">
              <option value="common">Common</option>
              <option value="rare">Rare</option>
              <option value="epic">Epic</option>
              <option value="legendary">Legendary</option>
            </select>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="badgeForm.status">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeBadgeModal" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Create/Edit Leaderboard Modal -->
    <div v-if="showCreateLeaderboard || editingLeaderboard" class="modal-overlay" @click="closeLeaderboardModal">
      <div class="modal" @click.stop>
        <h2>{{ editingLeaderboard ? 'Edit Leaderboard' : 'Create Leaderboard' }}</h2>
        <form @submit.prevent="saveLeaderboard">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="leaderboardForm.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="leaderboardForm.description"></textarea>
          </div>
          <div class="form-group">
            <label>Program</label>
            <select v-model="leaderboardForm.program">
              <option value="">-- Select Program --</option>
              <option v-for="prog in programs" :key="prog.id" :value="prog.id">{{ prog.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <div class="form-group">
              <label>Period *</label>
              <select v-model="leaderboardForm.period" required>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
                <option value="monthly">Monthly</option>
                <option value="yearly">Yearly</option>
                <option value="all_time">All Time</option>
              </select>
            </div>
            <div class="form-group">
              <label>Metric *</label>
              <select v-model="leaderboardForm.metric" required>
                <option value="points_earned">Points Earned</option>
                <option value="points_redeemed">Points Redeemed</option>
                <option value="transactions">Transactions</option>
                <option value="revenue">Revenue</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Top N (Number of entries to show)</label>
            <input v-model.number="leaderboardForm.top_n" type="number" min="1" max="1000" value="100" />
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="leaderboardForm.status">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>
          <div class="modal-actions">
            <button type="button" @click="closeLeaderboardModal" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary">Save</button>
          </div>
        </form>
      </div>
    </div>

    <!-- View Progress/Awards Modals would go here - keeping it concise for now -->
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { gamificationApi, type Mission, type Badge, type Leaderboard, type Streak } from '@/api/services/gamification'
import { programsApi } from '@/api/services/programs'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'
import { useToast } from '@/composables/useToast'

const { showToast } = useToast()

const activeTab = ref<'missions' | 'badges' | 'leaderboards' | 'streaks'>('missions')
const tabs = [
  { id: 'missions', label: 'Missions' },
  { id: 'badges', label: 'Badges' },
  { id: 'leaderboards', label: 'Leaderboards' },
  { id: 'streaks', label: 'Streaks' },
]

const missions = ref<Mission[]>([])
const badges = ref<Badge[]>([])
const leaderboards = ref<Leaderboard[]>([])
const streaks = ref<Streak[]>([])
const programs = ref<any[]>([])

const missionFilter = ref('')
const badgeFilter = ref('')
const streakSearch = ref('')

const showCreateMission = ref(false)
const showCreateBadge = ref(false)
const showCreateLeaderboard = ref(false)
const showCreateStreak = ref(false)
const editingMission = ref<Mission | null>(null)
const editingBadge = ref<Badge | null>(null)
const editingLeaderboard = ref<Leaderboard | null>(null)

const missionForm = ref({
  name: '',
  description: '',
  program: null as string | null,
  mission_type: 'points_earn',
  reward_points: 100,
  is_active: true,
  start_date: new Date().toISOString().slice(0, 16),
  end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
  objective: {},
  eligibility_rules: {},
})

const badgeForm = ref({
  name: '',
  description: '',
  icon: '🏆',
  program: null as string | null,
  rarity: 'common',
  is_active: true,
  criteria: {},
})

const leaderboardForm = ref({
  name: '',
  description: '',
  program: null as string | null,
  period: 'monthly',
  metric: 'points_earned',
  top_n: 100,
  is_active: true,
})

const activeMissionsCount = computed(() => missions.value.filter(m => m.status === 'active').length)
const activeStreaksCount = computed(() => streaks.value.length)

const filteredMissions = computed(() => {
  let result = missions.value
  if (missionFilter.value === 'active') {
    result = result.filter(m => m.status === 'active')
  } else if (missionFilter.value === 'inactive') {
    result = result.filter(m => m.status !== 'active')
  }
  return result
})

const filteredBadges = computed(() => {
  let result = badges.value
  if (badgeFilter.value === 'active') {
    result = result.filter(b => b.status === 'active')
  } else if (badgeFilter.value === 'inactive') {
    result = result.filter(b => b.status !== 'active')
  }
  return result
})

const filteredStreaks = computed(() => {
  let result = streaks.value
  if (streakSearch.value) {
    const search = streakSearch.value.toLowerCase()
    result = result.filter(s => s.customer_id.toLowerCase().includes(search))
  }
  return result
})

const formatDate = (date: string | null | undefined) => {
  if (!date) return '-'
  try {
    return format(new Date(date), 'MMM dd, yyyy HH:mm')
  } catch {
    return '-'
  }
}

const formatCustomerId = (id: string) => {
  if (!id) return '-'
  return id.substring(0, 8) + '...'
}

const loadData = async () => {
  try {
    await Promise.all([
      loadMissions(),
      loadBadges(),
      loadLeaderboards(),
      loadStreaks(),
      loadPrograms()
    ])
  } catch (error) {
    console.error('Error loading gamification data:', error)
  }
}

const loadMissions = async () => {
  try {
    const response = await gamificationApi.getMissions()
    missions.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading missions:', error)
    showToast('Error loading missions', 'error')
  }
}

const loadBadges = async () => {
  try {
    const response = await gamificationApi.getBadges()
    badges.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading badges:', error)
    showToast('Error loading badges', 'error')
  }
}

const loadLeaderboards = async () => {
  try {
    const response = await gamificationApi.getLeaderboards()
    leaderboards.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading leaderboards:', error)
    showToast('Error loading leaderboards', 'error')
  }
}

const loadStreaks = async () => {
  try {
    const response = await gamificationApi.getStreaks()
    streaks.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading streaks:', error)
    showToast('Error loading streaks', 'error')
  }
}

const loadPrograms = async () => {
  try {
    const response = await programsApi.getAll()
    programs.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading programs:', error)
  }
}

const closeMissionModal = () => {
  showCreateMission.value = false
  editingMission.value = null
  missionForm.value = {
    name: '',
    description: '',
    program: null,
    mission_type: 'points_earn',
    reward_points: 100,
    status: 'active',
    start_date: new Date().toISOString().slice(0, 16),
    end_date: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().slice(0, 16),
    objective: {},
    eligibility_rules: {},
  }
}

const saveMission = async () => {
  try {
    if (editingMission.value) {
      await gamificationApi.updateMission(editingMission.value.id, missionForm.value)
      showToast('Mission updated successfully', 'success')
    } else {
      await gamificationApi.createMission(missionForm.value)
      showToast('Mission created successfully', 'success')
    }
    closeMissionModal()
    await loadMissions()
  } catch (error: any) {
    console.error('Error saving mission:', error)
    showToast('Error saving mission: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

const editMission = (mission: Mission) => {
  editingMission.value = mission
  missionForm.value = {
    name: mission.name,
    description: mission.description || '',
    program: mission.program?.toString() || null,
    mission_type: mission.mission_type || 'points_earn',
    reward_points: mission.reward_points || 100,
    status: mission.status || 'active',
    start_date: mission.start_date ? new Date(mission.start_date).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16),
    end_date: mission.end_date ? new Date(mission.end_date).toISOString().slice(0, 16) : new Date().toISOString().slice(0, 16),
    objective: mission.objective || {},
    eligibility_rules: mission.eligibility_rules || {},
  }
}

const deleteMission = async (id: string) => {
  if (!confirm('Are you sure you want to delete this mission?')) return
  try {
    await gamificationApi.deleteMission(id)
    showToast('Mission deleted successfully', 'success')
    await loadMissions()
  } catch (error: any) {
    console.error('Error deleting mission:', error)
    showToast('Error deleting mission', 'error')
  }
}

const viewMissionProgress = async (missionId: string) => {
  // TODO: Open modal with mission progress
  showToast('Mission progress view coming soon', 'info')
}

const closeBadgeModal = () => {
  showCreateBadge.value = false
  editingBadge.value = null
  badgeForm.value = {
    name: '',
    description: '',
    icon: '🏆',
    program: null,
    rarity: 'common',
    status: 'active',
    criteria: {},
  }
}

const saveBadge = async () => {
  try {
    if (editingBadge.value) {
      await gamificationApi.updateBadge(editingBadge.value.id, badgeForm.value)
      showToast('Badge updated successfully', 'success')
    } else {
      await gamificationApi.createBadge(badgeForm.value)
      showToast('Badge created successfully', 'success')
    }
    closeBadgeModal()
    await loadBadges()
  } catch (error: any) {
    console.error('Error saving badge:', error)
    showToast('Error saving badge: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

const editBadge = (badge: Badge) => {
  editingBadge.value = badge
  badgeForm.value = {
    name: badge.name,
    description: badge.description || '',
    icon: badge.icon || '🏆',
    program: badge.program?.toString() || null,
    rarity: badge.rarity || 'common',
    status: badge.status || 'active',
    criteria: badge.criteria || {},
  }
}

const deleteBadge = async (id: string) => {
  if (!confirm('Are you sure you want to delete this badge?')) return
  try {
    await gamificationApi.deleteBadge(id)
    showToast('Badge deleted successfully', 'success')
    await loadBadges()
  } catch (error: any) {
    console.error('Error deleting badge:', error)
    showToast('Error deleting badge', 'error')
  }
}

const viewBadgeAwards = async (badgeId: string) => {
  // TODO: Open modal with badge awards
  showToast('Badge awards view coming soon', 'info')
}

const closeLeaderboardModal = () => {
  showCreateLeaderboard.value = false
  editingLeaderboard.value = null
  leaderboardForm.value = {
    name: '',
    description: '',
    program: null,
    period: 'monthly',
    metric: 'points_earned',
    top_n: 100,
    status: 'active',
  }
}

const saveLeaderboard = async () => {
  try {
    if (editingLeaderboard.value) {
      await gamificationApi.updateLeaderboard(editingLeaderboard.value.id, leaderboardForm.value)
      showToast('Leaderboard updated successfully', 'success')
    } else {
      await gamificationApi.createLeaderboard(leaderboardForm.value)
      showToast('Leaderboard created successfully', 'success')
    }
    closeLeaderboardModal()
    await loadLeaderboards()
  } catch (error: any) {
    console.error('Error saving leaderboard:', error)
    showToast('Error saving leaderboard: ' + (error.response?.data?.detail || error.message), 'error')
  }
}

const editLeaderboard = (leaderboard: Leaderboard) => {
  editingLeaderboard.value = leaderboard
  leaderboardForm.value = {
    name: leaderboard.name,
    description: leaderboard.description || '',
    program: leaderboard.program?.toString() || null,
    period: leaderboard.period || 'monthly',
    metric: leaderboard.metric || 'points_earned',
    top_n: leaderboard.top_n || 100,
    status: leaderboard.status || 'active',
  }
}

const deleteLeaderboard = async (id: string) => {
  if (!confirm('Are you sure you want to delete this leaderboard?')) return
  try {
    await gamificationApi.deleteLeaderboard(id)
    showToast('Leaderboard deleted successfully', 'success')
    await loadLeaderboards()
  } catch (error: any) {
    console.error('Error deleting leaderboard:', error)
    showToast('Error deleting leaderboard', 'error')
  }
}

const viewLeaderboardEntries = async (leaderboardId: string) => {
  // TODO: Open modal with leaderboard entries
  showToast('Leaderboard entries view coming soon', 'info')
}

const editStreak = (streak: Streak) => {
  // TODO: Implement streak editing
  showToast('Streak editing coming soon', 'info')
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.gamification-dashboard {
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-6);
  gap: var(--spacing-4);
}

.page-title {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-1);
}

.page-description {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin: 0;
}

.header-actions {
  display: flex;
  gap: var(--spacing-2);
}

.btn-primary {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-5);
  background: var(--color-primary);
  color: white;
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  box-shadow: var(--shadow-sm);
}

.btn-primary:hover {
  background: var(--color-primary-dark);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.btn-primary svg {
  width: 18px;
  height: 18px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
  gap: var(--spacing-6);
  margin-bottom: var(--spacing-8);
}

.stat-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  gap: var(--spacing-4);
  transition: all var(--transition-base);
}

.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-icon {
  width: 56px;
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: var(--radius-lg);
  color: white;
  flex-shrink: 0;
}

.stat-icon svg {
  width: 28px;
  height: 28px;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin-bottom: var(--spacing-1);
}

.stat-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
}

.tabs {
  display: flex;
  gap: var(--spacing-2);
  margin-bottom: var(--spacing-6);
  border-bottom: 2px solid var(--border-color);
}

.tab-button {
  padding: var(--spacing-3) var(--spacing-5);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-tertiary);
  cursor: pointer;
  transition: all var(--transition-base);
  margin-bottom: -2px;
}

.tab-button:hover {
  color: var(--text-primary);
}

.tab-button.active {
  color: var(--color-primary);
  border-bottom-color: var(--color-primary);
}

.tab-content {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-6);
  box-shadow: var(--shadow-sm);
  border: 1px solid var(--border-color);
}

.tab-panel {
  min-height: 400px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--spacing-6);
}

.section-header h2 {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
}

.section-actions {
  display: flex;
  gap: var(--spacing-2);
  align-items: center;
}

.filter-select,
.search-input {
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
}

.btn-secondary {
  display: flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-3) var(--spacing-4);
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  transition: all var(--transition-base);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--color-gray-200);
  color: var(--text-primary);
}

.btn-secondary svg {
  width: 16px;
  height: 16px;
}

.missions-grid,
.badges-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: var(--spacing-4);
}

.mission-card,
.badge-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
}

.mission-card:hover,
.badge-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-color-dark);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: var(--spacing-3);
}

.card-header h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0;
  flex: 1;
}

.card-actions {
  display: flex;
  gap: var(--spacing-1);
}

.icon-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  transition: all var(--transition-fast);
  border: 1px solid transparent;
}

.icon-btn:hover {
  background: var(--color-primary-50);
  color: var(--color-primary);
  border-color: var(--color-primary-100);
}

.icon-btn-danger:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
  border-color: var(--color-error);
}

.icon-btn svg {
  width: 16px;
  height: 16px;
}

.card-description {
  font-size: var(--font-size-sm);
  color: var(--text-tertiary);
  margin: 0 0 var(--spacing-3) 0;
  line-height: var(--line-height-relaxed);
}

.card-meta {
  display: flex;
  gap: var(--spacing-3);
  flex-wrap: wrap;
  align-items: center;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--spacing-2);
  padding: var(--spacing-1) var(--spacing-3);
  border-radius: var(--radius-full);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: var(--radius-full);
  flex-shrink: 0;
}

.status-badge.active {
  background: var(--color-success-bg);
  color: var(--color-success-dark);
}

.status-badge.active .status-dot {
  background: var(--color-success);
}

.status-badge.inactive {
  background: var(--color-error-bg);
  color: var(--color-error-dark);
}

.status-badge.inactive .status-dot {
  background: var(--color-error);
}

.meta-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-1);
  font-size: var(--font-size-xs);
  color: var(--text-tertiary);
}

.meta-item svg {
  width: 14px;
  height: 14px;
}

.badge-icon-large {
  font-size: 4rem;
  text-align: center;
  margin-bottom: var(--spacing-3);
}

.badge-content {
  text-align: center;
}

.badge-content h3 {
  font-size: var(--font-size-lg);
  font-weight: var(--font-weight-semibold);
  color: var(--text-primary);
  margin: 0 0 var(--spacing-2) 0;
}

.badge-meta {
  display: flex;
  gap: var(--spacing-2);
  justify-content: center;
  margin-top: var(--spacing-3);
}

.rarity-badge {
  padding: var(--spacing-1) var(--spacing-2);
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  text-transform: capitalize;
}

.rarity-badge.common {
  background: var(--color-gray-200);
  color: var(--color-gray-700);
}

.rarity-badge.rare {
  background: var(--color-info-bg);
  color: var(--color-info-dark);
}

.rarity-badge.epic {
  background: var(--color-primary-50);
  color: var(--color-primary-dark);
}

.rarity-badge.legendary {
  background: var(--color-warning-bg);
  color: var(--color-warning-dark);
}

.leaderboards-list {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-4);
}

.leaderboard-card {
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  padding: var(--spacing-5);
  border: 1px solid var(--border-color);
  transition: all var(--transition-base);
}

.leaderboard-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--border-color-dark);
}

.leaderboard-meta {
  display: flex;
  gap: var(--spacing-4);
  flex-wrap: wrap;
  margin-top: var(--spacing-3);
}

.streaks-table {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: var(--bg-secondary);
}

.data-table th {
  padding: var(--spacing-4) var(--spacing-5);
  text-align: left;
  font-weight: var(--font-weight-semibold);
  font-size: var(--font-size-xs);
  color: var(--text-secondary);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  border-bottom: 1px solid var(--border-color);
}

.data-table td {
  padding: var(--spacing-4) var(--spacing-5);
  border-bottom: 1px solid var(--border-color-light);
  font-size: var(--font-size-sm);
}

.streak-value {
  font-weight: var(--font-weight-semibold);
  color: var(--color-primary);
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-12);
  color: var(--text-tertiary);
  gap: var(--spacing-3);
}

.empty-state svg {
  width: 64px;
  height: 64px;
  opacity: 0.5;
}

.empty-state p {
  font-size: var(--font-size-base);
  text-align: center;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--bg-overlay);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: var(--z-modal);
  backdrop-filter: blur(4px);
}

.modal {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: var(--spacing-8);
  width: 90%;
  max-width: 600px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: var(--shadow-2xl);
}

.modal h2 {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text-primary);
  margin-bottom: var(--spacing-6);
}

.form-group {
  margin-bottom: var(--spacing-5);
}

.form-group label {
  display: block;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
  color: var(--text-secondary);
  margin-bottom: var(--spacing-2);
}

.form-group input,
.form-group textarea,
.form-group select {
  width: 100%;
  padding: var(--spacing-3) var(--spacing-4);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: var(--font-size-sm);
  background: var(--bg-primary);
  color: var(--text-primary);
  transition: all var(--transition-base);
}

.form-group input:focus,
.form-group textarea:focus,
.form-group select:focus {
  outline: none;
  border-color: var(--color-primary);
  box-shadow: 0 0 0 3px var(--color-primary-50);
}

.form-group textarea {
  min-height: 100px;
  resize: vertical;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: var(--spacing-2);
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: var(--spacing-4);
}

.modal-actions {
  display: flex;
  gap: var(--spacing-3);
  justify-content: flex-end;
  margin-top: var(--spacing-8);
  padding-top: var(--spacing-6);
  border-top: 1px solid var(--border-color);
}

/* Responsive */
@media (max-width: 768px) {
  .page-header {
    flex-direction: column;
    align-items: stretch;
  }
  
  .missions-grid,
  .badges-grid {
    grid-template-columns: 1fr;
  }
  
  .form-row {
    grid-template-columns: 1fr;
  }
}
</style>
