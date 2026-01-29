<template>
  <div class="rbac-management">
    <div class="section-header">
      <h2>Roles & Permissions</h2>
      <p class="section-description">
        Manage user roles and permissions for access control.
      </p>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-label">Total Roles</div>
        <div class="stat-value">{{ roles.length }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Permissions</div>
        <div class="stat-value">{{ permissions.length }}</div>
      </div>
    </div>

    <div class="roles-section">
      <div class="section-header-inline">
        <h3>Roles</h3>
        <button @click="showCreateRoleModal = true" class="btn-primary">+ Create Role</button>
      </div>

      <div v-if="loading" class="loading">Loading roles...</div>
      <div v-else-if="roles.length === 0" class="empty-state">No roles found</div>
      <div v-else class="roles-list">
        <div v-for="role in roles" :key="role.id" class="role-card">
          <div class="role-header">
            <h4>{{ role.name }}</h4>
            <span class="role-id">ID: {{ role.id }}</span>
          </div>
          <p class="role-description">{{ role.description || 'No description' }}</p>
        </div>
      </div>
    </div>

    <div class="permissions-section">
      <div class="section-header-inline">
        <h3>Permissions</h3>
      </div>

      <div v-if="loading" class="loading">Loading permissions...</div>
      <div v-else-if="permissions.length === 0" class="empty-state">No permissions found</div>
      <div v-else class="permissions-list">
        <div v-for="permission in permissions" :key="permission.id" class="permission-card">
          <div class="permission-name">{{ permission.name }}</div>
          <div class="permission-codename">{{ permission.codename }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api/services/admin'
import { extractData } from '@/utils/api'

const roles = ref<any[]>([])
const permissions = ref<any[]>([])
const loading = ref(false)
const showCreateRoleModal = ref(false)

const loadData = async () => {
  loading.value = true
  try {
    const [rolesRes, permissionsRes] = await Promise.all([
      adminApi.getRoles(),
      adminApi.getPermissions(),
    ])
    
    roles.value = extractData(rolesRes.data)
    permissions.value = extractData(permissionsRes.data)
  } catch (error) {
    console.error('Error loading RBAC data:', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.rbac-management {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.section-header {
  margin-bottom: 1rem;
}

.section-header h2 {
  font-size: 1.5rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 0.5rem 0;
}

.section-description {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.stat-card {
  background: #f9fafb;
  border-radius: 8px;
  padding: 1.5rem;
  border: 1px solid #e0e0e0;
}

.stat-label {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 600;
  color: #2563eb;
}

.roles-section,
.permissions-section {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.section-header-inline {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header-inline h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
}

.loading,
.empty-state {
  text-align: center;
  padding: 3rem;
  color: #666;
}

.roles-list,
.permissions-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.role-card,
.permission-card {
  background: #f9fafb;
  border-radius: 6px;
  padding: 1rem;
  border: 1px solid #e0e0e0;
}

.role-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.role-header h4 {
  margin: 0;
  font-size: 1rem;
  font-weight: 600;
}

.role-id {
  font-size: 0.75rem;
  color: #666;
  font-family: monospace;
}

.role-description {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
}

.permission-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.permission-codename {
  font-size: 0.75rem;
  color: #666;
  font-family: monospace;
}
</style>

