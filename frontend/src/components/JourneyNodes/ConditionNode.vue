<template>
  <div class="journey-node condition-node">
    <Handle type="target" :position="Position.Top" />
    <div class="node-header">
      <span class="node-icon">🔀</span>
      <span class="node-title">{{ data.label || 'Condition' }}</span>
    </div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  data: {
    label?: string
    condition?: string
  }
}>()
</script>

<style scoped>
.condition-node {
  background: #e6f0ff;
  border: 2px solid #2563eb;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  min-width: 120px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.node-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.node-icon {
  font-size: 1.25rem;
}

.node-title {
  font-weight: 600;
  color: #1e40af;
}
</style>

