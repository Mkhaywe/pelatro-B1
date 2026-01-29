<template>
  <div class="field-selector">
    <div class="field-selector-header">
      <h4>Available Fields</h4>
      <input 
        v-model="searchQuery" 
        type="text" 
        placeholder="Search fields..." 
        class="field-search"
      />
    </div>
    
    <div v-if="loading" class="loading-state">
      <p>Loading available fields...</p>
    </div>
    
    <div v-else-if="error" class="error-state">
      <p>{{ error }}</p>
      <button @click="loadFields" class="btn-secondary btn-sm">Retry</button>
    </div>
    
    <div v-else class="fields-list">
      <div 
        v-for="category in filteredCategories" 
        :key="category.name"
        class="field-category"
      >
        <div class="category-header" @click="toggleCategory(category.name)">
          <span class="category-name">{{ category.name }}</span>
          <span class="category-count">({{ category.fields.length }})</span>
          <span class="category-toggle">{{ expandedCategories.has(category.name) ? '−' : '+' }}</span>
        </div>
        
        <div v-if="expandedCategories.has(category.name)" class="category-fields">
          <div
            v-for="field in category.fields"
            :key="field.name"
            class="field-item"
            @click="selectField(field)"
            :title="field.description || field.name"
          >
            <div class="field-name">{{ formatFieldName(field.name) }}</div>
            <div class="field-meta">
              <span class="field-type">{{ field.type }}</span>
              <span v-if="field.description" class="field-desc">{{ field.description }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="field-selector-footer">
      <small>Click a field to insert it into your condition</small>
      <div class="examples">
        <strong>Examples:</strong>
        <div class="example-item">
          <code>{"var": "total_revenue"}</code> - Field reference
        </div>
        <div class="example-item">
          <code>{">": [{"var": "total_revenue"}, 1000]}</code> - Greater than
        </div>
        <div class="example-item">
          <code>{"==": [{"var": "customer_status"}, "active"]}</code> - Equals
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { dwhApi } from '@/api/services/dwh'

interface Field {
  name: string
  type: string
  description?: string
  category?: string
  data_source?: string
}

interface FieldCategory {
  name: string
  fields: Field[]
}

const emit = defineEmits<{
  fieldSelected: [field: Field]
}>()

const fields = ref<Field[]>([])
const loading = ref(false)
const error = ref<string | null>(null)
const searchQuery = ref('')
const expandedCategories = ref<Set<string>>(new Set())

const fieldCategories = computed(() => {
  const categories = new Map<string, Field[]>()
  
  fields.value.forEach(field => {
    const categoryName = field.category || 'Other'
    if (!categories.has(categoryName)) {
      categories.set(categoryName, [])
    }
    categories.get(categoryName)!.push(field)
  })
  
  // Sort categories
  const categoryOrder = [
    'Financial',
    'Transaction',
    'Loyalty',
    'Profile',
    'Demographic',
    'Engagement',
    'ML',
    'Segmentation',
    'Service',
    'Other'
  ]
  
  return Array.from(categories.entries())
    .map(([name, fields]) => ({ name, fields: fields.sort((a, b) => a.name.localeCompare(b.name)) }))
    .sort((a, b) => {
      const aIndex = categoryOrder.indexOf(a.name)
      const bIndex = categoryOrder.indexOf(b.name)
      if (aIndex === -1 && bIndex === -1) return a.name.localeCompare(b.name)
      if (aIndex === -1) return 1
      if (bIndex === -1) return -1
      return aIndex - bIndex
    })
})

const filteredCategories = computed(() => {
  if (!searchQuery.value.trim()) {
    return fieldCategories.value
  }
  
  const query = searchQuery.value.toLowerCase()
  return fieldCategories.value
    .map(category => ({
      ...category,
      fields: category.fields.filter(field => 
        field.name.toLowerCase().includes(query) ||
        (field.description && field.description.toLowerCase().includes(query))
      )
    }))
    .filter(category => category.fields.length > 0)
})

const formatFieldName = (name: string) => {
  return name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())
}

const toggleCategory = (categoryName: string) => {
  if (expandedCategories.value.has(categoryName)) {
    expandedCategories.value.delete(categoryName)
  } else {
    expandedCategories.value.add(categoryName)
  }
}

const selectField = (field: Field) => {
  emit('fieldSelected', field)
}

const loadFields = async () => {
  loading.value = true
  error.value = null
  
  try {
    const response = await dwhApi.getColumns()
    fields.value = response.data || []
    
    // Expand first 3 categories by default
    const categories = fieldCategories.value.slice(0, 3)
    categories.forEach(cat => expandedCategories.value.add(cat.name))
  } catch (err: any) {
    error.value = err.response?.data?.error || 'Failed to load available fields'
    console.error('Error loading fields:', err)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadFields()
})
</script>

<style scoped>
.field-selector {
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  max-height: 400px;
  display: flex;
  flex-direction: column;
}

.field-selector-header {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
}

.field-selector-header h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.875rem;
  font-weight: 600;
  color: #1f2937;
}

.field-search {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 0.875rem;
}

.field-search:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}

.loading-state,
.error-state {
  padding: 2rem;
  text-align: center;
  color: #6b7280;
  font-size: 0.875rem;
}

.error-state {
  color: #ef4444;
}

.fields-list {
  flex: 1;
  overflow-y: auto;
  padding: 0.5rem;
}

.field-category {
  margin-bottom: 0.5rem;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 4px;
  cursor: pointer;
  user-select: none;
  transition: background 0.2s;
}

.category-header:hover {
  background: #f3f4f6;
}

.category-name {
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  flex: 1;
}

.category-count {
  font-size: 0.75rem;
  color: #6b7280;
}

.category-toggle {
  font-size: 1.25rem;
  color: #6b7280;
  font-weight: bold;
  width: 20px;
  text-align: center;
}

.category-fields {
  margin-top: 0.25rem;
  padding-left: 0.5rem;
}

.field-item {
  padding: 0.5rem;
  margin-bottom: 0.25rem;
  border: 1px solid #e5e7eb;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.field-item:hover {
  background: #f0f9ff;
  border-color: #2563eb;
}

.field-name {
  font-weight: 500;
  font-size: 0.875rem;
  color: #1f2937;
  margin-bottom: 0.25rem;
}

.field-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.field-type {
  background: #e5e7eb;
  color: #374151;
  padding: 0.125rem 0.375rem;
  border-radius: 3px;
  font-weight: 500;
}

.field-desc {
  color: #6b7280;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.field-selector-footer {
  padding: 0.75rem 1rem;
  border-top: 1px solid #e0e0e0;
  background: #f9fafb;
}

.field-selector-footer small {
  color: #6b7280;
  font-size: 0.75rem;
  display: block;
  margin-bottom: 0.75rem;
}

.examples {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid #e5e7eb;
}

.examples strong {
  display: block;
  font-size: 0.75rem;
  color: #374151;
  margin-bottom: 0.5rem;
}

.example-item {
  font-size: 0.7rem;
  color: #6b7280;
  margin-bottom: 0.375rem;
  line-height: 1.4;
}

.example-item code {
  background: #f3f4f6;
  padding: 0.125rem 0.25rem;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 0.7rem;
  color: #1f2937;
}
</style>

