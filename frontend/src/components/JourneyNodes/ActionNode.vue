<template>
  <div class="journey-node action-node">
    <Handle type="target" :position="Position.Top" />
    <div class="node-header">
      <span class="node-icon">⚡</span>
      <span class="node-title">{{ data.label || 'Action' }}</span>
    </div>
    <div v-if="data.actionType" class="node-subtitle">
      {{ getActionLabel(data.actionType) }}
    </div>
    <Handle type="source" :position="Position.Bottom" />
  </div>
</template>

<script setup lang="ts">
import { Handle, Position } from '@vue-flow/core'

defineProps<{
  data: {
    label?: string
    actionType?: string
  }
}>()

const getActionLabel = (actionType: string) => {
  const labels: Record<string, string> = {
    send_email: 'Send Email',
    send_sms: 'Send SMS',
    send_push: 'Send Push',
    award_points: 'Award Points',
    trigger_campaign: 'Trigger Campaign',
  }
  return labels[actionType] || actionType
}
</script>

<style scoped>
.action-node {
  background: #fff4e6;
  border: 2px solid #f59e0b;
  border-radius: 8px;
  padding: 0.75rem 1rem;
  min-width: 140px;
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
  color: #92400e;
}

.node-subtitle {
  font-size: 0.75rem;
  color: #78350f;
  font-style: italic;
}
</style>

