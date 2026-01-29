<template>
  <div class="experiment-list">
    <div class="page-header">
      <h1>A/B Testing</h1>
      <button @click="showCreateModal = true" class="btn-primary">+ Create Experiment</button>
    </div>

    <div v-if="experiments.length === 0" class="empty-state">
      <p>No experiments found. Create your first A/B test to get started.</p>
      <p class="help-text">A/B tests help you optimize campaigns and programs by testing different variants.</p>
    </div>

    <div v-else class="experiments-table">
      <table class="data-table">
        <thead>
          <tr>
            <th>Name</th>
            <th>Status</th>
            <th>Start Date</th>
            <th>End Date</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="experiment in experiments" :key="experiment.id">
            <td>{{ experiment.name }}</td>
            <td>
              <span class="status-badge" :class="experiment.status">{{ experiment.status }}</span>
            </td>
            <td>{{ formatDate(experiment.start_date) }}</td>
            <td>{{ formatDate(experiment.end_date) }}</td>
            <td>
              <button @click="viewExperiment(experiment.id)" class="btn-link">View</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create Modal -->
    <div v-if="showCreateModal" class="modal-overlay" @click="showCreateModal = false">
      <div class="modal" @click.stop>
        <h2>Create A/B Test</h2>
        <form @submit.prevent="createExperiment">
          <div class="form-group">
            <label>Name *</label>
            <input v-model="newExperiment.name" required />
          </div>
          <div class="form-group">
            <label>Description</label>
            <textarea v-model="newExperiment.description"></textarea>
          </div>
          <div class="form-group">
            <label>Status</label>
            <select v-model="newExperiment.status">
              <option value="draft">Draft</option>
              <option value="running">Running</option>
              <option value="paused">Paused</option>
            </select>
          </div>
          <div class="form-group">
            <label>Start Date</label>
            <input v-model="newExperiment.start_date" type="datetime-local" />
          </div>
          <div class="form-group">
            <label>End Date</label>
            <input v-model="newExperiment.end_date" type="datetime-local" />
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
import { experimentsApi } from '@/api/services/experiments'
import { extractData } from '@/utils/api'
import { format } from 'date-fns'

const router = useRouter()

const experiments = ref<any[]>([])
const showCreateModal = ref(false)
const newExperiment = ref({
  name: '',
  description: '',
  status: 'draft',
  start_date: '',
  end_date: ''
})

const formatDate = (date: string | null | undefined) => {
  if (!date) return '-'
  try {
    return format(new Date(date), 'MMM dd, yyyy')
  } catch {
    return '-'
  }
}

const createExperiment = async () => {
  try {
    await experimentsApi.create(newExperiment.value)
    showCreateModal.value = false
    newExperiment.value = {
      name: '',
      description: '',
      status: 'draft',
      start_date: '',
      end_date: ''
    }
    loadExperiments()
    alert('Experiment created successfully!')
  } catch (error: any) {
    console.error('Error creating experiment:', error)
    alert('Error creating experiment: ' + (error.response?.data?.detail || error.message))
  }
}

const loadExperiments = async () => {
  try {
    const response = await experimentsApi.getAll()
    experiments.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading experiments:', error)
    experiments.value = []
  }
}

const viewExperiment = (id: string) => {
  router.push(`/experiments/${id}`)
}

onMounted(() => {
  loadExperiments()
})
</script>

<style scoped>
.experiment-list {
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

.experiments-table {
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

