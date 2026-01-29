<template>
  <div class="customer-list">
    <div class="page-header">
      <h1>Customers</h1>
      <div class="header-actions">
        <input 
          v-model="searchQuery" 
          placeholder="Search by Customer ID or Name..."
          class="search-input"
          @keyup.enter="searchCustomers"
        />
        <button @click="searchCustomers" class="btn-primary">Search</button>
        <button @click="loadCustomers" class="btn-secondary">Refresh</button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading customers...</div>
    
    <div v-else-if="error" class="error-message">
      {{ error }}
    </div>

    <div v-else class="customers-content">
      <!-- Customers Table -->
      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Customer ID</th>
              <th>Name</th>
              <th>Status</th>
              <th>Type</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="customers.length === 0">
              <td colspan="5" style="text-align: center; padding: 2rem; color: #666;">
                No customers found. Try searching or refreshing.
              </td>
            </tr>
            <tr v-for="customer in customers" :key="customer.id" v-else>
              <td class="customer-id">{{ customer.id }}</td>
              <td>{{ customer.name || '-' }}</td>
              <td>
                <span :class="['status-badge', customer.status === 'active' ? 'active' : 'inactive']">
                  {{ customer.status || 'unknown' }}
                </span>
              </td>
              <td>{{ customer.customerType || customer.customer_type || '-' }}</td>
              <td>
                <button @click="viewCustomer(customer.id)" class="btn-link">View 360</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Pagination Info -->
      <div v-if="customers.length > 0" class="pagination-info">
        <p>Showing {{ customers.length }} customer(s)</p>
        <p v-if="hasMore" class="help-text">
          Note: Only showing first 50 customers. Use search to find specific customers.
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { externalApi } from '@/api/services/external'

const router = useRouter()

const customers = ref<any[]>([])
const loading = ref(false)
const error = ref('')
const searchQuery = ref('')
const hasMore = ref(false)

const loadCustomers = async () => {
  loading.value = true
  error.value = ''
  
  try {
    // Fetch from Xiva API via backend
    const response = await externalApi.searchCustomers()
    
    if (response.data.results && Array.isArray(response.data.results)) {
      customers.value = response.data.results
      hasMore.value = response.data.results.length >= 50
    } else if (Array.isArray(response.data)) {
      customers.value = response.data
      hasMore.value = response.data.length >= 50
    } else {
      customers.value = []
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || err.message || 'Error loading customers'
    console.error('Error loading customers:', err)
    customers.value = []
  } finally {
    loading.value = false
  }
}

const searchCustomers = async () => {
  if (!searchQuery.value.trim()) {
    loadCustomers()
    return
  }
  
  loading.value = true
  error.value = ''
  
  try {
    const response = await externalApi.searchCustomers({ search: searchQuery.value })
    
    if (response.data.results && Array.isArray(response.data.results)) {
      customers.value = response.data.results
    } else if (Array.isArray(response.data)) {
      customers.value = response.data
    } else {
      customers.value = []
    }
  } catch (err: any) {
    error.value = err.response?.data?.error || err.message || 'Error searching customers'
    console.error('Error searching customers:', err)
    customers.value = []
  } finally {
    loading.value = false
  }
}

const viewCustomer = (customerId: string) => {
  router.push({ name: 'customer-360', params: { id: customerId } })
}

onMounted(() => {
  loadCustomers()
})
</script>

<style scoped>
.customer-list {
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.search-input {
  padding: 0.75rem 1rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
  min-width: 300px;
}

.btn-primary {
  padding: 0.75rem 1.5rem;
  background: #2563eb;
  color: white;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-primary:hover {
  background: #1d4ed8;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #f3f4f6;
  color: #374151;
  border: none;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #e5e7eb;
}

.loading {
  padding: 3rem;
  text-align: center;
  color: #666;
}

.error-message {
  padding: 1rem;
  background: #fee2e2;
  color: #dc2626;
  border-radius: 6px;
  margin-bottom: 1rem;
}

.table-container {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table thead {
  background: #f9fafb;
}

.data-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.875rem;
  color: #374151;
  border-bottom: 1px solid #e5e7eb;
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
  font-size: 0.875rem;
}

.data-table tbody tr:hover {
  background: #f9fafb;
}

.customer-id {
  font-family: monospace;
  font-size: 0.75rem;
  color: #6b7280;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 500;
  text-transform: capitalize;
}

.status-badge.active {
  background: #d1fae5;
  color: #065f46;
}

.status-badge.inactive {
  background: #fee2e2;
  color: #991b1b;
}

.btn-link {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  font-weight: 500;
  text-decoration: underline;
  padding: 0;
}

.btn-link:hover {
  color: #1d4ed8;
}

.pagination-info {
  margin-top: 1rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #6b7280;
}

.help-text {
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: #9ca3af;
}
</style>

