<template>
  <div class="journey-node start-node">
    <div class="node-header">
      <span class="node-icon">🚀</span>
      <span class="node-title">{{ data.label || 'Start' }}</span>
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
.start-node {
  background: #e6f7f0;
  border: 2px solid #10b981;
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
  color: #065f46;
}
</style>

