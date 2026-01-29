<template>
  <div class="segment-list">
    <div class="page-header">
      <h1>Segments</h1>
      <button @click="showCreateModal = true" class="btn-primary">
        + Create Segment
      </button>
    </div>

    <!-- Segments Table -->
    <div class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Type</th>
            <th>Members</th>
            <th>Status</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="segments.length === 0">
            <td colspan="5" style="text-align: center; padding: 2rem; color: #666;">
              No segments found. Create your first segment to get started.
            </td>
          </tr>
          <tr v-for="segment in segments" :key="segment.id" v-else>
            <td>{{ segment.name || '-' }}</td>
            <td>
              <span v-if="segment.is_dynamic" class="badge">Dynamic</span>
              <span v-else class="badge">Static</span>
            </td>
            <td>{{ getMemberCount(segment) }}</td>
            <td>
              <span :class="['status-badge', segment.is_active ? 'active' : 'inactive']">
                {{ segment.is_active ? 'Active' : 'Inactive' }}
              </span>
            </td>
            <td>
              <button @click="viewSegment(segment.id)" class="btn-link">View</button>
              <button @click="recalculateSegment(segment.id)" class="btn-link">
                Recalculate
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <h2>Create Segment</h2>
        <form @submit.prevent="createSegment">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="newSegment.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newSegment.description"></textarea>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="newSegment.is_dynamic" />
              Dynamic Segment (recalculates automatically)
            </label>
          </div>
          <div class="form-group">
            <label>
              <input type="checkbox" v-model="newSegment.is_rfm" />
              RFM Segment
            </label>
          </div>
          <div class="form-group full-width">
            <label>Rules (JSONLogic)</label>
            <p class="help-text">Use the Segment Builder for visual rule creation. For now, enter JSONLogic rules as JSON array.</p>
            <textarea 
              v-model="newSegment.rulesJson" 
              placeholder='[{"and": [{">": {"var": "total_revenue"}, 1000}]}]'
              rows="4"
            ></textarea>
            <small class="help-text">After creating, use "Edit" to access the visual rule builder</small>
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
import { useRouter } from 'vue-router'
import { segmentsApi } from '@/api/services/segments'
import type { Segment } from '@/types/loyalty'
import { extractData } from '@/utils/api'

const router = useRouter()
const segments = ref<Segment[]>([])
const showCreateModal = ref(false)
const newSegment = ref({
  name: '',
  description: '',
  is_dynamic: true,
  is_rfm: false,
  is_active: true,
  rulesJson: '[]'
})

const loadSegments = async () => {
  try {
    const response = await segmentsApi.getAll()
    segments.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading segments:', error)
    segments.value = []
  }
}

const viewSegment = (id: string) => {
  router.push(`/segments/${id}`)
}

const recalculateSegment = async (id: string) => {
  try {
    await segmentsApi.calculate(id)
    alert('Segment recalculated successfully!')
    loadSegments()
  } catch (error) {
    console.error('Error recalculating segment:', error)
    alert('Error recalculating segment')
  }
}

const getMemberCount = (segment: Segment) => {
  // Try multiple possible field names
  return segment.member_count || segment.active_member_count || segment.members?.length || 0
}

const createSegment = async () => {
  try {
    // Parse JSON rules
    let rules = []
    try {
      rules = JSON.parse(newSegment.value.rulesJson || '[]')
    } catch (e) {
      alert('Invalid JSON in rules field. Please check the format.')
      return
    }

    const segmentData = {
      name: newSegment.value.name,
      description: newSegment.value.description,
      is_dynamic: newSegment.value.is_dynamic,
      is_rfm: newSegment.value.is_rfm,
      is_active: newSegment.value.is_active,
      rules: rules
    }

    await segmentsApi.create(segmentData)
    showCreateModal.value = false
    newSegment.value = {
      name: '',
      description: '',
      is_dynamic: true,
      is_rfm: false,
      is_active: true,
      rulesJson: '[]'
    }
    loadSegments()
    alert('Segment created successfully!')
  } catch (error: any) {
    console.error('Error creating segment:', error)
    alert('Error creating segment: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadSegments()
})
</script>

<style scoped>
.segment-list {
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

.table-container {
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

.badge {
  padding: 0.25rem 0.75rem;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 12px;
  font-size: 0.875rem;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
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
  margin-right: 1rem;
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
  max-height: 90vh;
  overflow-y: auto;
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
.form-group textarea {
  width: 100%;
  padding: 0.75rem;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.form-group input[type="checkbox"] {
  width: auto;
  margin-right: 0.5rem;
}

.help-text {
  display: block;
  margin-top: 0.25rem;
  font-size: 0.875rem;
  color: #666;
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

