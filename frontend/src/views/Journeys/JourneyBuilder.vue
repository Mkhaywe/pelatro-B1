<template>
  <div class="journey-builder">
    <div class="builder-header">
      <div class="header-left">
        <h1>{{ journey?.name || 'New Journey' }}</h1>
        <p v-if="journey?.description" class="subtitle">{{ journey.description }}</p>
      </div>
      <div class="header-actions">
        <button @click="previewJourney" class="btn-secondary">Preview</button>
        <button @click="saveJourney" class="btn-primary" :disabled="saving">
          {{ saving ? 'Saving...' : 'Save Journey' }}
        </button>
      </div>
    </div>

    <div class="builder-content">
      <!-- Left Sidebar: Node Palette -->
      <div class="node-palette">
        <h3>Node Types</h3>
        <div class="node-types">
          <div 
            v-for="nodeType in nodeTypes" 
            :key="nodeType.type"
            class="node-type-item"
            draggable="true"
            @dragstart="onDragStart($event, nodeType)"
          >
            <div class="node-icon" :class="`icon-${nodeType.type}`">
              {{ nodeType.icon }}
            </div>
            <div class="node-label">{{ nodeType.label }}</div>
          </div>
        </div>

        <!-- Properties Panel -->
        <div v-if="selectedNode" class="properties-panel">
          <h3>Properties</h3>
          <div class="property-group">
            <label>Node Label</label>
            <input v-model="selectedNode.data.label" @input="updateNode" />
          </div>
          <div class="property-group" v-if="selectedNode.type === 'action'">
            <label>Action Type</label>
            <select v-model="selectedNode.data.actionType" @change="updateNode">
              <option value="send_email">Send Email</option>
              <option value="send_sms">Send SMS</option>
              <option value="send_push">Send Push Notification</option>
              <option value="award_points">Award Points</option>
              <option value="trigger_campaign">Trigger Campaign</option>
            </select>
          </div>
          <div class="property-group" v-if="selectedNode.type === 'condition'">
            <label>Condition Rule (JSONLogic)</label>
            <div class="condition-editor">
              <textarea 
                ref="conditionTextarea"
                :value="conditionText"
                @input="onConditionInput"
                rows="6"
                placeholder='{"and": [{">": {"var": "total_revenue"}, 1000}]}'
                class="condition-input"
              ></textarea>
              <div class="field-selector-wrapper">
                <FieldSelector @field-selected="insertField" />
              </div>
            </div>
            <small class="help-text">
              Use the field selector to insert available fields, or type JSONLogic directly.
            </small>
          </div>
          <div class="property-group" v-if="selectedNode.type === 'wait'">
            <label>Wait Duration</label>
            <input 
              type="number" 
              v-model.number="selectedNode.data.duration" 
              @input="updateNode"
              min="0"
            />
            <select v-model="selectedNode.data.durationUnit" @change="updateNode">
              <option value="minutes">Minutes</option>
              <option value="hours">Hours</option>
              <option value="days">Days</option>
            </select>
          </div>
          <div class="property-group">
            <button 
              @click="deleteSelectedNode" 
              class="btn-danger"
              style="width: 100%; margin-top: 1rem;"
            >
              Delete Node
            </button>
          </div>
        </div>
      </div>

      <!-- Center: Flow Canvas -->
      <div class="flow-canvas-container">
        <div 
          @drop="onDrop"
          @dragover="onDragOver"
          class="flow-canvas-wrapper"
        >
          <VueFlow
            v-model="elements"
            :nodes="nodes"
            :edges="edges"
            :node-types="nodeTypeMap"
            @nodes-change="onNodesChange"
            @edges-change="onEdgesChange"
            @node-click="onNodeClick"
            @connect="onConnect"
            @pane-ready="onPaneReady"
            class="flow-canvas"
          >
          <Background pattern-color="#e0e0e0" :gap="16" />
          <Controls />
          <!-- Minimap removed - use Controls for navigation -->
        </VueFlow>
        </div>
      </div>

      <!-- Right Sidebar: Journey Settings -->
      <div class="journey-settings">
        <h3>Journey Settings</h3>
        <div class="form-group">
          <label>Journey Name</label>
          <input v-model="journey.name" />
        </div>
        <div class="form-group">
          <label>Description</label>
          <textarea v-model="journey.description" rows="3"></textarea>
        </div>
        <div class="form-group">
          <label>Status</label>
          <select v-model="journey.status">
            <option value="draft">Draft</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="archived">Archived</option>
          </select>
        </div>
        <div class="form-group">
          <label>Entry Segment</label>
          <select v-model="journey.entry_segment">
            <option :value="null">All Customers</option>
            <option v-for="segment in segments" :key="segment.id" :value="segment.id">
              {{ segment.name }}
            </option>
          </select>
        </div>
        <div class="form-group">
          <label>
            <input type="checkbox" v-model="journey.is_active" />
            Is Active
          </label>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
// Minimap removed - using Controls instead
import { journeysApi } from '@/api/services/journeys'
import { segmentsApi } from '@/api/services/segments'
import type { Journey, Segment } from '@/types/loyalty'
import { extractData } from '@/utils/api'
import { useToast } from '@/composables/useToast'
// Custom node components
import StartNode from '@/components/JourneyNodes/StartNode.vue'
import ActionNode from '@/components/JourneyNodes/ActionNode.vue'
import ConditionNode from '@/components/JourneyNodes/ConditionNode.vue'
import WaitNode from '@/components/JourneyNodes/WaitNode.vue'
import EndNode from '@/components/JourneyNodes/EndNode.vue'
import FieldSelector from '@/components/FieldSelector.vue'

const route = useRoute()
const router = useRouter()
const { onConnect: onVueFlowConnect, addEdges, updateNode: updateVueFlowNode } = useVueFlow()
const toast = useToast()

const journey = ref<Partial<Journey>>({
  name: '',
  description: '',
  status: 'draft',
  is_active: false,
  entry_segment: null,
})

const segments = ref<Segment[]>([])
const saving = ref(false)
const selectedNode = ref<any>(null)
const vueFlowInstance = ref<any>(null)
const conditionTextarea = ref<HTMLTextAreaElement | null>(null)

// Condition text computed property (handles both string and object)
const conditionText = computed({
  get: () => {
    if (!selectedNode.value?.data?.condition) return ''
    const cond = selectedNode.value.data.condition
    if (typeof cond === 'string') {
      // Try to parse and format if valid JSON
      try {
        const parsed = JSON.parse(cond)
        return JSON.stringify(parsed, null, 2)
      } catch {
        return cond
      }
    }
    if (typeof cond === 'object') {
      return JSON.stringify(cond, null, 2)
    }
    return String(cond)
  },
  set: (value: string) => {
    if (!selectedNode.value) return
    try {
      // Try to parse as JSON
      const parsed = JSON.parse(value)
      selectedNode.value.data.condition = parsed
    } catch {
      // If not valid JSON, store as string
      selectedNode.value.data.condition = value
    }
    updateNode()
  }
})

const onConditionInput = (event: Event) => {
  const target = event.target as HTMLTextAreaElement
  conditionText.value = target.value
}

// Node types for palette
const nodeTypes = [
  { type: 'start', label: 'Start', icon: '🚀' },
  { type: 'action', label: 'Action', icon: '⚡' },
  { type: 'condition', label: 'Condition', icon: '🔀' },
  { type: 'wait', label: 'Wait', icon: '⏱️' },
  { type: 'end', label: 'End', icon: '🏁' },
]

// Node type map for Vue Flow (using custom components)
const nodeTypeMap = {
  start: StartNode,
  action: ActionNode,
  condition: ConditionNode,
  wait: WaitNode,
  end: EndNode,
}

// Vue Flow elements
const nodes = ref<any[]>([])
const edges = ref<any[]>([])

const elements = computed({
  get: () => [...nodes.value, ...edges.value],
  set: (val) => {
    nodes.value = val.filter((el: any) => el.type !== 'default' || !el.source)
    edges.value = val.filter((el: any) => el.source)
  }
})

// Load journey
const loadJourney = async (id: string) => {
  try {
    const response = await journeysApi.getById(id)
    journey.value = response.data
    
    // First, try to load from structure field (preferred - matches what we save)
    if (journey.value.structure) {
      const structure = typeof journey.value.structure === 'string' 
        ? JSON.parse(journey.value.structure) 
        : journey.value.structure
      
      if (structure.nodes && Array.isArray(structure.nodes)) {
        nodes.value = structure.nodes.map((node: any) => ({
          ...node,
          type: node.type || 'default',
          data: node.data || { label: node.label || 'Node' }
        }))
      }
      if (structure.edges && Array.isArray(structure.edges)) {
        edges.value = structure.edges.map((edge: any) => ({
          ...edge,
          source: edge.source || edge.from_node,
          target: edge.target || edge.to_node
        }))
      }
    }
    
    // Fallback: Use nodes and edges from API response (from JourneySerializer)
    if ((!nodes.value || nodes.value.length === 0) && journey.value.nodes && Array.isArray(journey.value.nodes)) {
      nodes.value = journey.value.nodes.map((node: any) => ({
        id: node.id?.toString() || `node-${node.node_type}-${Date.now()}`,
        type: node.node_type || 'default',
        position: { 
          x: node.position_x || 100, 
          y: node.position_y || 100 
        },
        data: { 
          label: node.name || 'Node',
          ...(node.config || {})
        }
      }))
    }
    
    if ((!edges.value || edges.value.length === 0) && journey.value.edges && Array.isArray(journey.value.edges)) {
      edges.value = journey.value.edges.map((edge: any) => ({
        id: edge.id?.toString() || `edge-${Date.now()}`,
        source: edge.from_node?.toString() || '',
        target: edge.to_node?.toString() || '',
        label: edge.condition || '',
        ...(edge.config || {})
      }))
    }
    
    // If still no nodes, create default start node
    if (!nodes.value || nodes.value.length === 0) {
      nodes.value = [{
        id: 'start-1',
        type: 'start',
        position: { x: 100, y: 100 },
        data: { label: 'Start' }
      }]
    }
  } catch (error: any) {
    console.error('Error loading journey:', error)
    toast.error('Failed to load journey. Please try again.')
  }
}

// Load segments
const loadSegments = async () => {
  try {
    const response = await segmentsApi.getAll()
    segments.value = extractData(response.data)
  } catch (error) {
    console.error('Error loading segments:', error)
  }
}

// Drag and drop
const onDragStart = (event: DragEvent, nodeType: any) => {
  if (event.dataTransfer) {
    event.dataTransfer.setData('application/vueflow', JSON.stringify(nodeType))
    event.dataTransfer.effectAllowed = 'move'
  }
}

// Vue Flow event handlers
const onNodesChange = (changes: any[]) => {
  // Handle node changes (position, selection, etc.)
  changes.forEach((change) => {
    if (change.type === 'select' && change.selected) {
      selectedNode.value = nodes.value.find(n => n.id === change.id)
    } else if (change.type === 'select' && !change.selected) {
      if (selectedNode.value?.id === change.id) {
        selectedNode.value = null
      }
    }
  })
}

const onEdgesChange = (changes: any[]) => {
  // Handle edge changes
}

const onNodeClick = (event: any) => {
  selectedNode.value = event.node
}

const onConnect = (params: any) => {
  edges.value.push({
    id: `edge-${params.source}-${params.target}`,
    source: params.source,
    target: params.target,
    type: 'default',
    animated: true,
  })
}

const onPaneReady = (instance: any) => {
  // Handle drop on pane
  if (instance && instance.screenToFlowCoordinate) {
    // Store instance for drop handler
    vueFlowInstance.value = instance
  }
}

// Handle drop on canvas
const onDrop = (event: DragEvent) => {
  event.preventDefault()
  if (!vueFlowInstance.value) return
  
  const data = event.dataTransfer?.getData('application/vueflow')
  if (data) {
    try {
      const nodeType = JSON.parse(data)
      const position = vueFlowInstance.value.screenToFlowCoordinate({
        x: event.clientX,
        y: event.clientY,
      })
      
      const newNode = {
        id: `${nodeType.type}-${Date.now()}`,
        type: nodeType.type || 'default',
        position,
        data: {
          label: nodeType.label || nodeType.type,
          actionType: nodeType.type === 'action' ? 'send_email' : undefined,
          condition: nodeType.type === 'condition' ? '{}' : undefined,
          duration: nodeType.type === 'wait' ? 1 : undefined,
          durationUnit: nodeType.type === 'wait' ? 'days' : undefined,
        }
      }
      
      nodes.value.push(newNode)
    } catch (e) {
      console.error('Error parsing drop data:', e)
    }
  }
}

const onDragOver = (event: DragEvent) => {
  event.preventDefault()
  if (event.dataTransfer) {
    event.dataTransfer.dropEffect = 'move'
  }
}

const updateNode = () => {
  if (selectedNode.value && vueFlowInstance.value) {
    const nodeIndex = nodes.value.findIndex(n => n.id === selectedNode.value.id)
    if (nodeIndex >= 0) {
      nodes.value[nodeIndex] = { ...selectedNode.value }
      // Update in Vue Flow
      if (updateVueFlowNode) {
        updateVueFlowNode(selectedNode.value.id, {
          data: selectedNode.value.data,
          type: selectedNode.value.type || 'default'
        })
      }
    }
  }
}

const deleteSelectedNode = () => {
  if (!selectedNode.value) return
  
  const nodeId = selectedNode.value.id
  
  // Don't allow deleting start node if it's the only node
  if (selectedNode.value.type === 'start' && nodes.value.length === 1) {
    toast.warning('Cannot delete the only start node. Add more nodes first.')
    return
  }
  
  // Remove node
  nodes.value = nodes.value.filter(n => n.id !== nodeId)
  
  // Remove connected edges
  edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
  
  // Clear selection
  selectedNode.value = null
  
  toast.success('Node deleted successfully')
}

// Handle keyboard delete key
const handleKeyDown = (event: KeyboardEvent) => {
  if ((event.key === 'Delete' || event.key === 'Backspace') && selectedNode.value) {
    // Don't delete if typing in an input
    if (event.target instanceof HTMLInputElement || event.target instanceof HTMLTextAreaElement) {
      return
    }
    event.preventDefault()
    deleteSelectedNode()
  }
}

// Insert field into condition textarea
const insertField = (field: { name: string; type: string; description?: string }) => {
  if (!conditionTextarea.value || !selectedNode.value) return
  
  const textarea = conditionTextarea.value
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const currentValue = conditionText.value
  
  // Insert field reference: {"var": "field_name"}
  const fieldRef = `{"var": "${field.name}"}`
  
  const newValue = currentValue.slice(0, start) + fieldRef + currentValue.slice(end)
  conditionText.value = newValue
  
  // Update cursor position
  setTimeout(() => {
    textarea.focus()
    const newCursorPos = start + fieldRef.length
    textarea.setSelectionRange(newCursorPos, newCursorPos)
  }, 0)
  
  toast.info(`Inserted field: ${field.name}`)
}

// Save journey
const saveJourney = async () => {
  saving.value = true
  try {
    // Prepare structure as object (backend will handle JSON serialization)
    const structure = {
      nodes: nodes.value.map((node: any) => ({
        id: node.id,
        type: node.type,
        position: node.position,
        data: node.data
      })),
      edges: edges.value.map((edge: any) => ({
        id: edge.id,
        source: edge.source,
        target: edge.target,
        label: edge.label,
        condition: edge.condition
      }))
    }
    
    const journeyToSave = {
      ...journey.value,
      structure: structure  // Send as object, not string
    }
    
    console.log('Saving journey:', journeyToSave)
    
    if (route.params.id === 'new') {
      const response = await journeysApi.create(journeyToSave)
      toast.success('Journey created successfully')
      router.push('/journeys')
    } else {
      const response = await journeysApi.update(route.params.id as string, journeyToSave)
      console.log('Journey updated:', response.data)
      toast.success('Journey saved successfully')
      // Reload journey to see changes
      await loadJourney(route.params.id as string)
    }
  } catch (error: any) {
    console.error('Error saving journey:', error)
    const errorMsg = error.response?.data?.error || error.message || 'Failed to save journey. Please check your input.'
    toast.error(errorMsg)
  } finally {
    saving.value = false
  }
}

const previewJourney = async () => {
  if (!route.params.id || route.params.id === 'new') {
    toast.warning('Please save the journey first before previewing.')
    return
  }
  
  try {
    const response = await journeysApi.preview(route.params.id as string, 'test-customer-123')
    const preview = response.data.preview
    const steps = preview.steps_completed || 0
    const duration = preview.estimated_duration_minutes || 0
    
    if (steps === 0) {
      toast.warning('Journey preview shows no steps. Make sure you have nodes and edges connected.')
    } else {
      toast.info(`Journey Preview: ${steps} steps, ${duration} minutes estimated duration`)
    }
    
    console.log('Journey Preview:', response.data)
  } catch (error: any) {
    console.error('Error previewing journey:', error)
    toast.error('Failed to preview journey: ' + (error.response?.data?.error || error.message))
  }
}

onMounted(() => {
  loadSegments()
  if (route.params.id && route.params.id !== 'new') {
    loadJourney(route.params.id as string)
  } else {
    // Create default start node for new journey
    nodes.value = [{
      id: 'start-1',
      type: 'start',
      position: { x: 100, y: 100 },
      data: { label: 'Start' }
    }]
  }
  
  // Add keyboard listener for delete key
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  // Remove keyboard listener
  window.removeEventListener('keydown', handleKeyDown)
})
</script>

<style scoped>
.journey-builder {
  display: flex;
  flex-direction: column;
  height: calc(100vh - 64px);
  background: #f5f5f5;
}

.builder-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  background: white;
  border-bottom: 1px solid #e0e0e0;
}

.header-left h1 {
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 0.25rem 0;
}

.subtitle {
  color: #666;
  font-size: 0.875rem;
  margin: 0;
}

.header-actions {
  display: flex;
  gap: 1rem;
}

.builder-content {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.node-palette {
  width: 340px;
  background: white;
  border-right: 1px solid #e0e0e0;
  overflow-y: auto;
  padding: 1rem;
}

.node-palette h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}

.node-types {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 2rem;
}

.node-type-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
}

.node-type-item:hover {
  background: #f5f5f5;
  border-color: #2563eb;
}

.node-type-item:active {
  cursor: grabbing;
}

.node-icon {
  font-size: 1.5rem;
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 6px;
  background: #f0f0f0;
}

.icon-start {
  background: #e6f7f0;
}

.icon-action {
  background: #fff4e6;
}

.icon-condition {
  background: #e6f0ff;
}

.icon-wait {
  background: #f0f0f0;
}

.icon-end {
  background: #ffe6e6;
}

.node-label {
  font-weight: 500;
}

.properties-panel {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid #e0e0e0;
}

.property-group {
  margin-bottom: 1rem;
}

.property-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #333;
}

.property-group input,
.property-group select,
.property-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 0.875rem;
}

.btn-danger {
  background: #ef4444;
  color: white;
  border: none;
  padding: 0.5rem 1rem;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 500;
  transition: background 0.2s;
}

.btn-danger:hover {
  background: #dc2626;
}

.btn-danger:active {
  background: #b91c1c;
}

.condition-editor {
  display: flex;
  gap: 1rem;
  align-items: flex-start;
}

.condition-input {
  flex: 1;
  font-family: 'Courier New', monospace;
  font-size: 0.875rem;
}

.field-selector-wrapper {
  width: 340px;
  flex-shrink: 0;
}

.help-text {
  display: block;
  margin-top: 0.5rem;
  color: #6b7280;
  font-size: 0.75rem;
}

.flow-canvas-container {
  flex: 1;
  position: relative;
}

.flow-canvas {
  width: 100%;
  height: 100%;
}

.journey-settings {
  width: 300px;
  background: white;
  border-left: 1px solid #e0e0e0;
  overflow-y: auto;
  padding: 1rem;
}

@media (max-width: 1280px) {
  .condition-editor {
    flex-direction: column;
  }

  .field-selector-wrapper {
    width: 100%;
  }
}

.journey-settings h3 {
  font-size: 1rem;
  font-weight: 600;
  margin: 0 0 1rem 0;
}

.form-group {
  margin-bottom: 1rem;
}

.form-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
  color: #333;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 0.875rem;
}

.btn-primary,
.btn-secondary {
  padding: 0.5rem 1rem;
  border-radius: 6px;
  font-weight: 500;
  cursor: pointer;
  border: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563eb;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #1d4ed8;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.btn-secondary:hover {
  background: #e0e0e0;
}
</style>

