<template>
  <div class="journey-node end-node">
    <Handle type="target" :position="Position.Top" />
    <div class="node-header">
      <span class="node-icon">🏁</span>
      <span class="node-title">{{ data.label || 'End' }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  data: {
    label?: string
  }
}>()
</script>

<style scoped>
.end-node {
  background: #ffe6e6;
  border: 2px solid #ef4444;
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
  color: #991b1b;
}
</style>

