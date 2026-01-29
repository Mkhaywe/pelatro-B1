<template>
  <div class="dwh-column-selector">
    <div class="selector-header">
      <h4>Available Fields</h4>
      <button @click="refreshColumns" class="btn-secondary btn-sm" :disabled="loading">
        {{ loading ? 'Loading...' : 'Refresh' }}
      </button>
    </div>
    
    <!-- Data Source Selector -->
    <div class="source-selector">
      <label>Data Source:</label>
      <select v-model="dataSource" @change="refreshColumns" class="source-select">
        <option value="auto">Auto (Both)</option>
        <option value="xiva">Xiva Only</option>
        <option value="dwh">DWH Only</option>
      </select>
    </div>
    
    <div v-if="loading" class="loading-state">
      Loading DWH columns...
    </div>
    
    <div v-else-if="columns.length === 0" class="empty-state">
      <p>No DWH columns available. Configure DWH connection first.</p>
    </div>
    
    <div v-else class="columns-list">
      <!-- Category Filter -->
      <div v-if="categories.length > 0" class="category-filter">
        <label>Category:</label>
        <select v-model="selectedCategory" class="category-select">
          <option value="all">All Categories</option>
          <option v-for="cat in categories" :key="cat" :value="cat">
            {{ cat.charAt(0).toUpperCase() + cat.slice(1) }}
          </option>
        </select>
      </div>
      
      <div 
        v-for="column in filteredColumns" 
        :key="column.name"
        class="column-item"
        :class="{ 'selected': selectedColumns.includes(column.name) }"
        @click="toggleColumn(column.name)"
      >
        <div class="column-info">
          <div class="column-header">
            <div class="column-name">{{ column.display_name || column.name }}</div>
            <div class="column-badges">
              <span class="badge badge-type">{{ column.type }}</span>
              <span v-if="column.data_source" class="badge badge-source">{{ column.data_source }}</span>
              <span v-if="column.category" class="badge badge-category">{{ column.category }}</span>
            </div>
          </div>
          <div v-if="column.description" class="column-desc">{{ column.description }}</div>
        </div>
        <div class="column-actions">
          <button 
            @click.stop="insertColumn(column.name)" 
            class="btn-insert"
            title="Insert into rule"
          >
            Insert
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="columns.length > 0" class="search-box">
      <input 
        v-model="searchQuery" 
        placeholder="Search columns..."
        class="search-input"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { mlApi } from '@/api/services/ml'

interface DWHColumn {
  name: string
  type: string
  description?: string
  data_source?: string
  category?: string
  display_name?: string
}

const props = defineProps<{
  selectedColumns?: string[]
}>()

const emit = defineEmits(['insert', 'select'])

const columns = ref<DWHColumn[]>([])
const loading = ref(false)
const searchQuery = ref('')
const selectedColumns = ref<string[]>(props.selectedColumns || [])
const dataSource = ref('auto')
const selectedCategory = ref('all')

const filteredColumns = computed(() => {
  let filtered = columns.value
  
  // Filter by category
  if (selectedCategory.value !== 'all') {
    filtered = filtered.filter(col => col.category === selectedCategory.value)
  }
  
  // Filter by search query
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(col => 
      col.name.toLowerCase().includes(query) ||
      (col.display_name || '').toLowerCase().includes(query) ||
      col.type.toLowerCase().includes(query) ||
      col.description?.toLowerCase().includes(query) ||
      col.category?.toLowerCase().includes(query)
    )
  }
  
  return filtered
})

const categories = computed(() => {
  const cats = new Set<string>()
  columns.value.forEach(col => {
    if (col.category) cats.add(col.category)
  })
  return Array.from(cats).sort()
})

const refreshColumns = async () => {
  loading.value = true
  try {
    // Get columns from dedicated endpoint with data source parameter
    const response = await mlApi.getDWHColumns(dataSource.value)
    columns.value = response.data
  } catch (error) {
    if (import.meta.env.DEV) {
      console.error('Error loading columns:', error)
    }
    // Fallback to default columns
    columns.value = getDefaultColumns()
  } finally {
    loading.value = false
  }
}

const getDefaultColumns = (): DWHColumn[] => {
  return [
    { name: 'total_revenue', type: 'number', description: 'Total customer revenue' },
    { name: 'transaction_count', type: 'number', description: 'Number of transactions' },
    { name: 'last_purchase_days_ago', type: 'number', description: 'Days since last purchase' },
    { name: 'avg_transaction_value', type: 'number', description: 'Average transaction value' },
    { name: 'lifetime_value', type: 'number', description: 'Customer lifetime value' },
    { name: 'churn_score', type: 'number', description: 'Churn risk score' },
    { name: 'customer_tier', type: 'string', description: 'Current loyalty tier' },
    { name: 'points_balance', type: 'number', description: 'Current points balance' },
    { name: 'city', type: 'string', description: 'Customer city' },
    { name: 'age', type: 'number', description: 'Customer age' },
    { name: 'gender', type: 'string', description: 'Customer gender' },
    { name: 'segment', type: 'string', description: 'Current segment' },
  ]
}

const toggleColumn = (columnName: string) => {
  const index = selectedColumns.value.indexOf(columnName)
  if (index > -1) {
    selectedColumns.value.splice(index, 1)
  } else {
    selectedColumns.value.push(columnName)
  }
  emit('select', [...selectedColumns.value])
}

const insertColumn = (columnName: string) => {
  emit('insert', `{"var": "${columnName}"}`)
}

onMounted(() => {
  refreshColumns()
})
</script>

<style scoped>
.dwh-column-selector {
  padding: 1rem;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.selector-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.selector-header h4 {
  font-size: 0.875rem;
  font-weight: 600;
  margin: 0;
}

.loading-state,
.empty-state {
  padding: 2rem;
  text-align: center;
  color: #666;
  font-size: 0.875rem;
}

.columns-list {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.column-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.column-item:hover {
  border-color: #2563eb;
  box-shadow: 0 2px 4px rgba(37, 99, 235, 0.1);
}

.column-item.selected {
  border-color: #2563eb;
  background: #eff6ff;
}

.column-info {
  flex: 1;
}

.column-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: #1a1a1a;
  font-family: monospace;
}

.column-type {
  font-size: 0.75rem;
  color: #666;
  margin-top: 0.25rem;
}

.column-desc {
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.25rem;
}

.column-actions {
  margin-left: 1rem;
}

.btn-insert {
  padding: 0.25rem 0.75rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 0.75rem;
  cursor: pointer;
  font-weight: 500;
}

.btn-insert:hover {
  background: #1d4ed8;
}

.search-box {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.search-input {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.source-selector {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.source-selector label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #666;
}

.source-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.category-filter {
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.category-filter label {
  display: block;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #666;
}

.category-select {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.column-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.25rem;
}

.column-badges {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.badge {
  padding: 0.125rem 0.5rem;
  border-radius: 4px;
  font-size: 0.625rem;
  font-weight: 600;
  text-transform: uppercase;
}

.badge-type {
  background: #e0e7ff;
  color: #3730a3;
}

.badge-source {
  background: #dbeafe;
  color: #1e40af;
}

.badge-category {
  background: #f3f4f6;
  color: #374151;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>

