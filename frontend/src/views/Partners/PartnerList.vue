<template>
  <div class="partner-list">
    <div class="page-header">
      <h1>Partners & Coalitions</h1>
      <button @click="showCreateModal = true" class="btn-primary">+ Add Partner</button>
    </div>

    <div v-if="partners.length === 0" class="empty-state">
      <p>No partners found. Add your first partner to get started.</p>
      <p class="help-text">Partners enable coalition programs and cross-program rewards.</p>
    </div>

    <div v-else class="partners-table">
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Status</th>
            <th>API Key</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="partner in partners" :key="partner.id">
            <td>{{ partner.name }}</td>
            <td>{{ partner.type }}</td>
            <td>
              <span class="status-badge" :class="partner.status">{{ partner.status }}</span>
            </td>
            <td>
              <code class="api-key">{{ partner.api_key ? '••••••••' : 'Not set' }}</code>
            </td>
            <td>
              <button @click="viewPartner(partner.id)" class="btn-link">View</button>
              <button @click="editPartner(partner.id)" class="btn-link">Edit</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <h2>Add Partner</h2>
        <form @submit.prevent="createPartner">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="newPartner.name" required />
          </div>
          <div class="form-group">
            <label>Type</label>
            <select v-model="newPartner.type">
              <option value="merchant">Merchant</option>
              <option value="coalition">Coalition</option>
              <option value="affiliate">Affiliate</option>
            </select>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="newPartner.status">
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
              <option value="pending">Pending</option>
            </select>
          </div>
          <div class="form-group">
            <label>API Key</label>
            <input v-model="newPartner.api_key" placeholder="Leave empty to auto-generate" />
          </div>
          <div class="modal-actions">
            <button type="button" @click="showCreateModal = false" class="btn-secondary">Cancel</button>
            <button type="submit" class="btn-primary">Create</button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { partnersApi } from '@/api/services/partners'
import { extractData } from '@/utils/api'

const partners = ref<any[]>([])
const showCreateModal = ref(false)
const newPartner = ref({
  name: '',
  type: 'merchant',
  status: 'active',
  api_key: ''
})

const loadPartners = async () => {
  try {
    const response = await partnersApi.getAll()
    partners.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading partners:', error)
    partners.value = []
  }
}

const viewPartner = (id: string) => {
  router.push(`/partners/${id}`)
}

const editPartner = (id: string) => {
  router.push(`/partners/${id}/edit`)
}

const createPartner = async () => {
  try {
    await partnersApi.create(newPartner.value)
    showCreateModal.value = false
    newPartner.value = {
      name: '',
      type: 'merchant',
      status: 'active',
      api_key: ''
    }
    loadPartners()
    alert('Partner created successfully!')
  } catch (error: any) {
    console.error('Error creating partner:', error)
    alert('Error creating partner: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadPartners()
})
</script>

<style scoped>
.partner-list {
  padding: 2rem;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
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

.empty-state {
  background: white;
  border-radius: 8px;
  padding: 3rem;
  text-align: center;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.help-text {
  color: #666;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

.partners-table {
  background: white;
  border-radius: 8px;
  overflow: hidden;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: #f9fafb;
  padding: 1rem;
  text-align: left;
  font-weight: 600;
  border-bottom: 1px solid #e5e7eb;
}

.data-table td {
  padding: 1rem;
  border-bottom: 1px solid #e5e7eb;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.api-key {
  font-family: monospace;
  background: #f3f4f6;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-size: 0.875rem;
}

.btn-link {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
  margin-right: 1rem;
  text-decoration: underline;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: white;
  border-radius: 8px;
  padding: 2rem;
  width: 90%;
  max-width: 500px;
}

.modal h2 {
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 1.5rem;
}

.btn-secondary {
  padding: 0.75rem 1.5rem;
  background: #f3f4f6;
  color: #374151;
  border: none;
  border-radius: 6px;
  cursor: pointer;
}
</style>

