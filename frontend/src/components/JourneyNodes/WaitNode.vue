<template>
  <div class="journey-node wait-node">
    <Handle type="target" :position="Position.Top" />
    <div class="node-header">
      <span class="node-icon">⏱️</span>
      <span class="node-title">{{ data.label || 'Wait' }}</span>
    </div>
    <div v-if="data.duration" class="node-subtitle">
      {{ data.duration }} {{ data.durationUnit || 'days' }}
    </div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  data: {
    label?: string
    duration?: number
    durationUnit?: string
  }
}>()
</script>

<style scoped>
.wait-node {
  background: #f0f0f0;
  border: 2px solid #6b7280;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  min-width: 120px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.node-icon {
  font-size: 1.25rem;
}

.node-title {
  font-weight: 600;
  color: #374151;
}

.node-subtitle {
  font-size: 0.75rem;
  color: #4b5563;
  font-style: italic;
}
</style>

