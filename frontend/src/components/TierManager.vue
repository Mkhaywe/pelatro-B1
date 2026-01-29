<template>
  <div class="tier-manager">
    <div class="tier-manager-header">
      <h3>Tier Management</h3>
      <button @click="addTier" class="btn-secondary btn-sm">+ Add Tier</button>
    </div>
    
    <div v-if="tiers.length === 0" class="empty-state">
      <p>No tiers defined. Add your first tier to get started.</p>
    </div>
    
    <div v-else class="tiers-list">
      <div 
        v-for="(tier, index) in sortedTiers" 
        :key="tier.id || `tier-${index}`"
        class="tier-card"
        :class="{ 'dragging': draggedIndex === index }"
        draggable="true"
        @dragstart="onDragStart($event, index)"
        @dragover.prevent="onDragOver($event, index)"
        @drop="onDrop($event, index)"
        @dragend="draggedIndex = null"
      >
        <div class="tier-handle">
          <span class="drag-icon">☰</span>
          <span class="tier-number">{{ index + 1 }}</span>
        </div>
        
        <div class="tier-content">
          <div class="tier-header">
            <input 
              v-model="tier.name" 
              placeholder="Tier Name (e.g., Bronze, Silver, Gold)"
              class="tier-name-input"
              @input="updateTier(index)"
            />
            <button @click="removeTier(index)" class="btn-danger btn-sm">Remove</button>
          </div>
          
          <div class="tier-fields">
            <div class="field-group">
              <label>Minimum Points</label>
              <input 
                type="number" 
                v-model.number="tier.min_points" 
                min="0"
                @input="updateTier(index)"
                class="tier-input"
              />
            </div>
            
            <div class="field-group">
              <label>Priority</label>
              <input 
                type="number" 
                v-model.number="tier.priority" 
                min="0"
                @input="updateTier(index)"
                class="tier-input"
                placeholder="Higher = Better"
              />
            </div>
          </div>
          
          <div class="field-group">
            <label>Benefits (Description)</label>
            <textarea 
              v-model="tier.benefits" 
              placeholder="Describe tier benefits..."
              rows="3"
              @input="updateTier(index)"
              class="tier-textarea"
            ></textarea>
          </div>
          
          <div class="tier-visual">
            <div class="tier-bar">
              <div 
                class="tier-fill" 
                :style="{ width: `${getTierProgress(tier)}%` }"
              ></div>
            </div>
            <div class="tier-stats">
              <span>Min: {{ tier.min_points || 0 }} pts</span>
              <span v-if="getNextTier(index)">→ Next: {{ getNextTier(index)?.min_points || 'Max' }} pts</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Tier Preview -->
    <div v-if="tiers.length > 0" class="tier-preview">
      <h4>Tier Progression Preview</h4>
      <div class="preview-bars">
        <div 
          v-for="(tier, index) in sortedTiers" 
          :key="tier.id || `preview-${index}`"
          class="preview-bar"
        >
          <div class="preview-label">{{ tier.name || `Tier ${index + 1}` }}</div>
          <div class="preview-progress">
            <div 
              class="preview-fill" 
              :style="{ 
                width: `${getTierWidth(index)}%`,
                left: `${getTierOffset(index)}%`
              }"
            ></div>
          </div>
          <div class="preview-points">{{ tier.min_points || 0 }}+</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

interface Tier {
  id?: number
  name: string
  min_points: number
  priority: number
  benefits: string
}

const props = defineProps<{
  tiers: Tier[]
}>()

const emit = defineEmits(['update:tiers'])

const draggedIndex = ref<number | null>(null)

const sortedTiers = computed(() => {
  return [...props.tiers].sort((a, b) => (a.min_points || 0) - (b.min_points || 0))
})

const updateTier = (index: number) => {
  emit('update:tiers', [...props.tiers])
}

const addTier = () => {
  const newTier: Tier = {
    name: '',
    min_points: 0,
    priority: props.tiers.length,
    benefits: ''
  }
  emit('update:tiers', [...props.tiers, newTier])
}

const removeTier = (index: number) => {
  const updated = [...props.tiers]
  updated.splice(index, 1)
  emit('update:tiers', updated)
}

const getTierProgress = (tier: Tier) => {
  if (!tier.min_points) return 0
  const maxPoints = Math.max(...props.tiers.map(t => t.min_points || 0), 1000)
  return Math.min((tier.min_points / maxPoints) * 100, 100)
}

const getNextTier = (index: number) => {
  const sorted = sortedTiers.value
  return sorted[index + 1]
}

const getTierWidth = (index: number) => {
  const sorted = sortedTiers.value
  const current = sorted[index]
  const next = sorted[index + 1]
  const max = Math.max(...sorted.map(t => t.min_points || 0), 1000)
  
  if (next) {
    return ((next.min_points - current.min_points) / max) * 100
  }
  return ((max - current.min_points) / max) * 100
}

const getTierOffset = (index: number) => {
  const sorted = sortedTiers.value
  const max = Math.max(...sorted.map(t => t.min_points || 0), 1000)
  let offset = 0
  
  for (let i = 0; i < index; i++) {
    offset += getTierWidth(i)
  }
  
  return offset
}

// Drag and drop
const onDragStart = (event: DragEvent, index: number) => {
  draggedIndex.value = index
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', index.toString())
  }
}

const onDragOver = (event: DragEvent, index: number) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const onDrop = (event: DragEvent, dropIndex: number) => {
  event.preventDefault()
  if (draggedIndex.value === null) return
  
  const dragged = draggedIndex.value
  if (dragged === dropIndex) return
  
  const updated = [...props.tiers]
  const [removed] = updated.splice(dragged, 1)
  updated.splice(dropIndex, 0, removed)
  
  // Update priorities based on new order
  updated.forEach((tier, idx) => {
    tier.priority = idx
  })
  
  emit('update:tiers', updated)
  draggedIndex.value = null
}
</script>

<style scoped>
.tier-manager {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.tier-manager-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.tier-manager-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.875rem;
}

.empty-state {
  padding: 2rem;
  text-align: center;
  color: #666;
  background: #f9fafb;
  border-radius: 6px;
}

.tiers-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.tier-card {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  background: white;
  transition: all 0.2s;
  cursor: move;
}

.tier-card:hover {
  border-color: #2563eb;
  box-shadow: 0 4px 8px rgba(37, 99, 235, 0.1);
}

.tier-card.dragging {
  opacity: 0.5;
}

.tier-handle {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: #f9fafb;
  border-radius: 6px;
  min-width: 50px;
}

.drag-icon {
  font-size: 1.25rem;
  color: #999;
  cursor: grab;
}

.drag-icon:active {
  cursor: grabbing;
}

.tier-number {
  font-weight: 700;
  color: #2563eb;
  font-size: 1.125rem;
}

.tier-content {
  flex: 1;
}

.tier-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.tier-name-input {
  flex: 1;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 1.125rem;
  font-weight: 600;
  margin-right: 1rem;
}

.tier-fields {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1rem;
}

.field-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.field-group label {
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
}

.tier-input,
.tier-textarea {
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.tier-textarea {
  resize: vertical;
  font-family: inherit;
}

.tier-visual {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid #e0e0e0;
}

.tier-bar {
  width: 100%;
  height: 12px;
  background: #f0f0f0;
  border-radius: 6px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}

.tier-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #3b82f6);
  border-radius: 6px;
  transition: width 0.3s ease;
}

.tier-stats {
  display: flex;
  justify-content: space-between;
  font-size: 0.875rem;
  color: #666;
}

.tier-preview {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e0e0e0;
}

.tier-preview h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.preview-bars {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.preview-bar {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.preview-label {
  min-width: 100px;
  font-weight: 500;
  font-size: 0.875rem;
}

.preview-progress {
  flex: 1;
  height: 24px;
  background: #f0f0f0;
  border-radius: 12px;
  position: relative;
  overflow: hidden;
}

.preview-fill {
  position: absolute;
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #3b82f6);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.preview-points {
  min-width: 80px;
  text-align: right;
  font-size: 0.875rem;
  color: #666;
  font-weight: 600;
}

.btn-danger {
  background: #dc2626;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-danger:hover {
  background: #b91c1c;
}

.btn-secondary {
  background: #f3f4f6;
  color: #374151;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-secondary:hover {
  background: #e5e7eb;
}
</style>

