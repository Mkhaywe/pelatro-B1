<template>
  <div class="admin-dashboard">
    <div class="page-header">
      <h1>System Administration & Configuration</h1>
      <p class="subtitle">Manage data sources, ML models, and system settings</p>
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
      <!-- Data Sources Tab (Xiva/DWH) -->
      <div v-if="activeTab === 'data-sources'" class="tab-panel">
        <DataSourceConfig />
      </div>

      <!-- Gamification Data Sources Tab -->
      <div v-if="activeTab === 'gamification-sources'" class="tab-panel">
        <GamificationDataSources />
      </div>

      <!-- External Systems Configuration Tab -->
      <div v-if="activeTab === 'external-systems'" class="tab-panel">
        <ExternalSystemsConfig />
      </div>

      <!-- ML Configuration Tab -->
      <div v-if="activeTab === 'ml'" class="tab-panel">
        <MLConfiguration />
      </div>

      <!-- Product Catalog Tab -->
      <div v-if="activeTab === 'product-catalog'" class="tab-panel">
        <ProductCatalog />
      </div>

      <!-- System Settings Tab -->
      <div v-if="activeTab === 'settings'" class="tab-panel">
        <SystemSettings />
      </div>

      <!-- Audit Log Tab -->
      <div v-if="activeTab === 'audit'" class="tab-panel">
        <AuditLogView />
      </div>

      <!-- Roles & Permissions Tab -->
      <div v-if="activeTab === 'rbac'" class="tab-panel">
        <RBACManagement />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import DataSourceConfig from './components/DataSourceConfig.vue'
import GamificationDataSources from './components/GamificationDataSources.vue'
import MLConfiguration from './components/MLConfiguration.vue'
import SystemSettings from './components/SystemSettings.vue'
import AuditLogView from './components/AuditLogView.vue'
import RBACManagement from './components/RBACManagement.vue'
import ProductCatalog from './components/ProductCatalog.vue'
import ExternalSystemsConfig from './components/ExternalSystemsConfig.vue'

const activeTab = ref('data-sources')

const tabs = [
  { id: 'data-sources', label: 'Data Sources (Xiva/DWH)' },
  { id: 'gamification-sources', label: 'Gamification Sources' },
  { id: 'external-systems', label: 'External Systems Config' },
  { id: 'ml', label: 'ML & AI' },
  { id: 'product-catalog', label: 'Product Catalog' },
  { id: 'settings', label: 'System Settings' },
  { id: 'audit', label: 'Audit Log' },
  { id: 'rbac', label: 'Roles & Permissions' },
]
</script>

<style scoped>
.admin-dashboard {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 0.5rem 0;
}

.subtitle {
  color: #666;
  font-size: 1rem;
  margin: 0;
}

.tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 2rem;
  border-bottom: 2px solid #e0e0e0;
}

.tab-button {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: -2px;
}

.tab-button:hover {
  color: #2563eb;
}

.tab-button.active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

.tab-content {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.tab-panel {
  min-height: 400px;
}
</style>
