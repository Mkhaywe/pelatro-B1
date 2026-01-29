<template>
  <div class="product-catalog">
    <div class="page-header">
      <h2>Product Catalog</h2>
      <p class="subtitle">Manage products and plans from external systems (Xiva, CRM, Billing)</p>
    </div>

    <!-- Statistics Cards -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📦</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total || 0 }}</div>
          <div class="stat-label">Total Products</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.active || 0 }}</div>
          <div class="stat-label">Active Products</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🛒</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.available || 0 }}</div>
          <div class="stat-label">Available for Purchase</div>
        </div>
      </div>
    </div>

    <!-- Actions Bar -->
    <div class="actions-bar">
      <div class="filters">
        <select v-model="filters.product_type" @change="loadProducts" class="filter-select">
          <option value="">All Types</option>
          <option value="voice">Voice Plan</option>
          <option value="data">Data Plan</option>
          <option value="sms">SMS Plan</option>
          <option value="bundle">Bundle Plan</option>
          <option value="device">Device</option>
          <option value="service">Service</option>
          <option value="addon">Add-on</option>
        </select>
        
        <select v-model="filters.external_system" @change="loadProducts" class="filter-select">
          <option value="">All Systems</option>
          <option value="xiva">Xiva</option>
          <option value="crm">CRM</option>
          <option value="billing">Billing/OCS</option>
          <option value="manual">Manual</option>
        </select>
        
        <select v-model="filters.is_active" @change="loadProducts" class="filter-select">
          <option value="">All Status</option>
          <option value="true">Active</option>
          <option value="false">Inactive</option>
        </select>
        
        <input
          v-model="filters.search"
          @input="loadProducts"
          type="text"
          placeholder="Search products..."
          class="search-input"
        />
      </div>
      
      <div class="action-buttons">
        <button @click="openSyncModal" class="btn-primary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0 1 14.85-3.48L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Sync from External System
        </button>
        <button @click="openAddModal" class="btn-secondary">
          <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <line x1="12" y1="5" x2="12" y2="19" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
            <line x1="5" y1="12" x2="19" y2="12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
          </svg>
          Add Product
        </button>
      </div>
    </div>

    <!-- Products Table -->
    <div class="table-container">
      <div v-if="loading" class="loading-state">Loading products...</div>
      <div v-else-if="products.length === 0" class="empty-state">
        <p>No products found. Add a product or sync from external system.</p>
      </div>
      <table v-else class="products-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Category</th>
            <th>Price</th>
            <th>System</th>
            <th>Status</th>
            <th>Last Synced</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="product in products" :key="product.id">
            <td>
              <div class="product-name">{{ product.name }}</div>
              <div class="product-id">ID: {{ product.external_product_id }}</div>
            </td>
            <td>
              <span class="badge badge-type">{{ getProductTypeLabel(product.product_type) }}</span>
            </td>
            <td>{{ product.category || '-' }}</td>
            <td>
              <span v-if="product.price">{{ product.currency }} {{ product.price }}</span>
              <span v-else class="text-muted">-</span>
            </td>
            <td>
              <span class="badge badge-system">{{ (product.external_system || 'manual').toUpperCase() }}</span>
            </td>
            <td>
              <span :class="['badge', product.is_active && product.is_available ? 'badge-success' : 'badge-inactive']">
                {{ product.is_active && product.is_available ? 'Available' : 'Unavailable' }}
              </span>
            </td>
            <td>
              <span v-if="product.last_synced">{{ formatDate(product.last_synced) }}</span>
              <span v-else class="text-muted">Never</span>
            </td>
            <td>
              <div class="action-buttons-cell">
                <button @click="openEditModal(product)" class="btn-icon" title="Edit">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
                <button @click="deleteProduct(product.id)" class="btn-icon btn-delete" title="Delete">
                  <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <polyline points="3 6 5 6 21 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Sync Modal -->
    <div v-if="showSyncModal" class="modal-overlay" @click.self="closeSyncModal">
      <div class="modal-content">
        <h3>Sync Products from External System</h3>
        <form @submit.prevent="syncProducts">
          <div class="form-group">
            <label for="externalSystem">External System Configuration *</label>
            <select id="externalSystem" v-model="selectedExternalSystemId" required>
              <option :value="null">-- Select External System --</option>
              <option v-for="system in externalSystems" :key="system.id" :value="system.id">
                {{ system.name }} ({{ system.system_type }})
              </option>
            </select>
            <p class="form-help" style="font-size: 0.85rem; color: var(--text-tertiary); margin-top: 0.5rem;">
              Configure external systems in Admin > External Systems Config. The system will call the Xiva API endpoint you configured (e.g., /api/productCatalogManagement/v5/productOffering/).
            </p>
          </div>
          <div v-if="externalSystems.length === 0" class="form-warning" style="padding: 1rem; background: var(--color-warning-bg); border-radius: var(--radius-lg); margin-bottom: 1rem;">
            <p style="margin: 0; color: var(--color-warning-dark);">No external systems configured. Please configure Xiva in Admin > External Systems Config first.</p>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn-primary" :disabled="syncing || !selectedExternalSystemId">
              {{ syncing ? 'Syncing...' : 'Sync Products' }}
            </button>
            <button type="button" @click="closeSyncModal" class="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddEditModal" class="modal-overlay" @click.self="closeAddEditModal">
      <div class="modal-content">
        <h3>{{ editingProduct ? 'Edit Product' : 'Add New Product' }}</h3>
        <form @submit.prevent="saveProduct">
          <div class="form-group">
            <label for="name">Product Name *</label>
            <input id="name" v-model="currentProduct.name" type="text" required />
          </div>
          <div class="form-group">
            <label for="external_product_id">External Product ID *</label>
            <input id="external_product_id" v-model="currentProduct.external_product_id" type="text" required />
          </div>
          <div class="form-group">
            <label for="product_type">Product Type</label>
            <select id="product_type" v-model="currentProduct.product_type">
              <option value="voice">Voice Plan</option>
              <option value="data">Data Plan</option>
              <option value="sms">SMS Plan</option>
              <option value="bundle">Bundle Plan</option>
              <option value="device">Device</option>
              <option value="service">Service</option>
              <option value="addon">Add-on</option>
            </select>
          </div>
          <div class="form-group">
            <label for="description">Description</label>
            <textarea id="description" v-model="currentProduct.description" rows="3"></textarea>
          </div>
          <div class="form-group">
            <label for="price">Price</label>
            <input id="price" v-model.number="currentProduct.price" type="number" step="0.01" />
          </div>
          <div class="form-group">
            <label for="currency">Currency</label>
            <input id="currency" v-model="currentProduct.currency" type="text" />
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="currentProduct.is_active" />
              Active
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="currentProduct.is_available" />
              Available for Purchase
            </label>
          </div>
          <div class="modal-actions">
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? 'Saving...' : 'Save' }}
            </button>
            <button type="button" @click="closeAddEditModal" class="btn-secondary">Cancel</button>
          </div>
        </form>
      </div>
    </div>

    <!-- Message -->
    <div v-if="message" :class="['message', messageType]">
      {{ message }}
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { apiClient } from '@/api/client'

interface Product {
  id?: number
  external_product_id: string
  external_system: string
  name: string
  description: string
  product_type: string
  category: string
  price?: number
  currency: string
  recurring: boolean
  billing_cycle: string
  features: Record<string, any>
  attributes: Record<string, any>
  is_active: boolean
  is_available: boolean
  target_segments: string[]
  min_customer_value?: number
  max_customer_value?: number
  last_synced?: string
  sync_frequency: string
  created_at?: string
  updated_at?: string
}

const products = ref<Product[]>([])
const loading = ref(false)
const stats = ref({ total: 0, active: 0, available: 0 })
const filters = ref({
  product_type: '',
  external_system: '',
  is_active: '',
  search: '',
})
const showSyncModal = ref(false)
const showAddEditModal = ref(false)
const editingProduct = ref<Product | null>(null)
const currentProduct = ref<Partial<Product>>({
  external_system: 'manual',
  product_type: 'bundle',
  currency: 'USD',
  billing_cycle: 'monthly',
  is_active: true,
  is_available: true,
  recurring: false,
  features: {},
  attributes: {},
  target_segments: [],
  sync_frequency: 'daily',
})
const syncing = ref(false)
const saving = ref(false)
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const externalSystems = ref<any[]>([])
const selectedExternalSystemId = ref<number | null>(null)

const loadProducts = async () => {
  loading.value = true
  try {
    const params = new URLSearchParams()
    if (filters.value.product_type) params.append('product_type', filters.value.product_type)
    if (filters.value.external_system) params.append('external_system', filters.value.external_system)
    if (filters.value.is_active) params.append('is_active', filters.value.is_active)
    if (filters.value.search) params.append('search', filters.value.search)
    
    const response = await apiClient.get(`/products/?${params.toString()}`)
    // Handle paginated response
    if (response.data && response.data.results) {
      products.value = response.data.results
    } else if (Array.isArray(response.data)) {
      products.value = response.data
    } else {
      products.value = []
    }
  } catch (error: any) {
    console.error('Error loading products:', error)
    showMessage('Failed to load products.', 'error')
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await apiClient.get('/products/stats/')
    stats.value = response.data
  } catch (error) {
    console.error('Error loading stats:', error)
  }
}

const loadExternalSystems = async () => {
  try {
    const response = await apiClient.get('/external-systems/')
    externalSystems.value = response.data.results || response.data || []
    // Filter to only show systems that support product sync
    externalSystems.value = externalSystems.value.filter((sys: any) => 
      ['xiva', 'crm', 'billing'].includes(sys.system_type)
    )
  } catch (error) {
    console.error('Error loading external systems:', error)
  }
}

const openSyncModal = () => {
  loadExternalSystems()
  showSyncModal.value = true
}

const closeSyncModal = () => {
  showSyncModal.value = false
  selectedExternalSystemId.value = null
}

const syncProducts = async () => {
  if (!selectedExternalSystemId.value) {
    showMessage('Please select an external system', 'error')
    return
  }
  
  syncing.value = true
  try {
    const response = await apiClient.post('/products/sync/', {
      external_system_id: selectedExternalSystemId.value,
    })
    if (response.data.success) {
      showMessage(
        `Successfully synced ${response.data.created + response.data.updated} products (${response.data.created} created, ${response.data.updated} updated)`,
        'success'
      )
      await loadProducts()
      await loadStats()
      closeSyncModal()
    } else {
      showMessage(`Sync failed: ${response.data.error}`, 'error')
    }
  } catch (error: any) {
    console.error('Error syncing products:', error)
    showMessage(`Failed to sync products: ${error.response?.data?.error || error.message}`, 'error')
  } finally {
    syncing.value = false
  }
}

const openAddModal = () => {
  editingProduct.value = null
  currentProduct.value = {
    external_system: 'manual',
    product_type: 'bundle',
    currency: 'USD',
    billing_cycle: 'monthly',
    is_active: true,
    is_available: true,
    recurring: false,
    features: {},
    attributes: {},
    target_segments: [],
    sync_frequency: 'daily',
  }
  showAddEditModal.value = true
}

const openEditModal = (product: Product) => {
  editingProduct.value = product
  currentProduct.value = { ...product }
  showAddEditModal.value = true
}

const closeAddEditModal = () => {
  showAddEditModal.value = false
  editingProduct.value = null
}

const saveProduct = async () => {
  if (!currentProduct.value.name || !currentProduct.value.external_product_id) {
    showMessage('Product Name and External Product ID are required', 'error')
    return
  }

  saving.value = true
  try {
    if (editingProduct.value?.id) {
      await apiClient.put(`/products/${editingProduct.value.id}/`, currentProduct.value)
      showMessage('Product updated successfully!', 'success')
    } else {
      await apiClient.post('/products/', currentProduct.value)
      showMessage('Product added successfully!', 'success')
    }
    await loadProducts()
    await loadStats()
    closeAddEditModal()
  } catch (error: any) {
    console.error('Error saving product:', error)
    showMessage(error.response?.data?.error || 'Error saving product', 'error')
  } finally {
    saving.value = false
  }
}

const deleteProduct = async (id?: number) => {
  if (!id) return
  if (confirm('Are you sure you want to delete this product?')) {
    try {
      await apiClient.delete(`/products/${id}/`)
      showMessage('Product deleted successfully!', 'success')
      await loadProducts()
      await loadStats()
    } catch (error: any) {
      console.error('Error deleting product:', error)
      showMessage(error.response?.data?.error || 'Error deleting product', 'error')
    }
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleString()
}

const showMessage = (msg: string, type: 'success' | 'error') => {
  message.value = msg
  messageType.value = type
  setTimeout(() => {
    message.value = ''
  }, 5000)
}

const getProductTypeLabel = (type: string) => {
  const labels: Record<string, string> = {
    voice: 'Voice Plan',
    data: 'Data Plan',
    sms: 'SMS Plan',
    bundle: 'Bundle Plan',
    device: 'Device',
    service: 'Service',
    addon: 'Add-on',
  }
  return labels[type] || type
}

onMounted(() => {
  loadProducts()
  loadStats()
  loadExternalSystems()
})
</script>

<style scoped>
.product-catalog {
  padding: 1.5rem;
}

.page-header {
  margin-bottom: 2rem;
}

.page-header h2 {
  font-size: 1.8rem;
  color: var(--text-primary);
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-secondary);
  font-size: 0.9rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: var(--text-primary);
}

.stat-label {
  font-size: 0.85rem;
  color: var(--text-tertiary);
}

.actions-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.filters {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
}

.filter-select,
.search-input {
  padding: 0.5rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 0.9rem;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.search-input {
  min-width: 250px;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: var(--radius-lg);
  font-size: 0.9rem;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.2s;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
  border: none;
}

.btn-primary:hover {
  background: var(--color-primary-dark);
}

.btn-secondary {
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  border: 1px solid var(--border-color);
}

.btn-secondary:hover {
  background: var(--bg-secondary);
}

.table-container {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  overflow: hidden;
  border: 1px solid var(--border-color);
}

.products-table {
  width: 100%;
  border-collapse: collapse;
}

.products-table th {
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  font-size: 0.85rem;
  text-transform: uppercase;
  color: var(--text-secondary);
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-secondary);
}

.products-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color-light);
}

.product-name {
  font-weight: 500;
  color: var(--text-primary);
}

.product-id {
  font-size: 0.85rem;
  color: var(--text-tertiary);
  margin-top: 0.25rem;
}

.badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: var(--radius-full);
  font-size: 0.85rem;
  font-weight: 500;
}

.badge-type {
  background: var(--color-primary-bg);
  color: var(--color-primary);
}

.badge-system {
  background: var(--color-info-bg);
  color: var(--color-info);
}

.badge-success {
  background: var(--color-success-bg);
  color: var(--color-success);
}

.badge-inactive {
  background: var(--color-gray-200);
  color: var(--color-gray-700);
}

.action-buttons-cell {
  display: flex;
  gap: 0.5rem;
}

.btn-icon {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  cursor: pointer;
  transition: all 0.2s;
}

.btn-icon:hover {
  background: var(--bg-secondary);
  color: var(--color-primary);
}

.btn-delete:hover {
  background: var(--color-error-bg);
  color: var(--color-error);
}

.btn-icon svg {
  width: 16px;
  height: 16px;
}

.loading-state,
.empty-state {
  padding: 3rem;
  text-align: center;
  color: var(--text-tertiary);
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  padding: 2rem;
  max-width: 500px;
  width: 90%;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-content h3 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  color: var(--text-primary);
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: var(--text-primary);
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid var(--border-color);
  border-radius: var(--radius-lg);
  font-size: 0.9rem;
  background: var(--bg-primary);
  color: var(--text-primary);
}

.modal-actions {
  display: flex;
  gap: 0.5rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.message {
  position: fixed;
  top: 2rem;
  right: 2rem;
  padding: 1rem 1.5rem;
  border-radius: var(--radius-lg);
  font-weight: 500;
  z-index: 2000;
  box-shadow: var(--shadow-lg);
}

.message.success {
  background: var(--color-success);
  color: white;
}

.message.error {
  background: var(--color-error);
  color: white;
}
</style>
