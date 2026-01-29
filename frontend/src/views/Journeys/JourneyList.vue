<template>
  <div class="journey-list">
    <div class="page-header">
      <h1>Journey Builder</h1>
      <div style="display: flex; gap: 1rem;">
        <button @click="showCreateModal = true" class="btn-primary">+ Create Journey</button>
        <router-link to="/journeys/new/builder" class="btn-secondary" style="text-decoration: none; display: inline-block; padding: 0.75rem 1.5rem; background: #f3f4f6; color: #374151; border-radius: 6px; font-weight: 500;">Build New Journey</router-link>
      </div>
    </div>

    <div v-if="journeys.length === 0" class="empty-state">
      <p>No journeys found. Create your first journey to get started.</p>
      <p class="help-text">Journeys allow you to create multi-step customer experiences with triggers and actions.</p>
    </div>

    <div v-else class="journeys-grid">
      <div v-for="journey in journeys" :key="journey.id" class="journey-card">
        <h3>{{ journey.name }}</h3>
        <p>{{ journey.description || 'No description' }}</p>
        <div class="journey-meta">
          <span class="status-badge" :class="journey.status">{{ journey.status }}</span>
        </div>
        <div class="journey-actions">
          <button @click="viewJourney(journey.id)" class="btn-link">View</button>
          <button @click="editJourney(journey.id)" class="btn-link">Edit</button>
        </div>
      </div>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <h2>Create Journey</h2>
        <form @submit.prevent="createJourney">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="newJourney.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newJourney.description"></textarea>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="newJourney.status">
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="paused">Paused</option>
            </select>
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
import { journeysApi } from '@/api/services/journeys'
import { extractData } from '@/utils/api'

const router = useRouter()
const journeys = ref<any[]>([])
const showCreateModal = ref(false)
const newJourney = ref({
  name: '',
  description: '',
  status: 'draft',
  program: null
})

const loadJourneys = async () => {
  try {
    const response = await journeysApi.getAll()
    journeys.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading journeys:', error)
    journeys.value = []
  }
}

const viewJourney = (id: string) => {
  router.push(`/journeys/${id}/builder`)
}

const editJourney = (id: string) => {
  router.push(`/journeys/${id}/builder`)
}

const createJourney = async () => {
  try {
    await journeysApi.create(newJourney.value)
    showCreateModal.value = false
    newJourney.value = {
      name: '',
      description: '',
      status: 'draft',
      program: null
    }
    loadJourneys()
    alert('Journey created successfully!')
  } catch (error: any) {
    console.error('Error creating journey:', error)
    alert('Error creating journey: ' + (error.response?.data?.detail || error.message))
  }
}

onMounted(() => {
  loadJourneys()
})
</script>

<style scoped>
.journey-list {
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

.journeys-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1.5rem;
}

.journey-card {
  background: white;
  border-radius: 8px;
  padding: 1.5rem;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.journey-card h3 {
  margin-bottom: 0.5rem;
}

.journey-meta {
  margin: 1rem 0;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.875rem;
  font-weight: 500;
}

.journey-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.btn-link {
  background: none;
  border: none;
  color: #2563eb;
  cursor: pointer;
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
.form-group textarea,
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

