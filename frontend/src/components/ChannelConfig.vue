<template>
  <div class="channel-config">
    <div class="config-header">
      <h3>Delivery Channels</h3>
    </div>
    
    <p class="help-text">
      Select the channels through which this campaign will be delivered.
    </p>
    
    <div class="channels-grid">
      <label 
        v-for="channel in availableChannels" 
        :key="channel.id"
        class="channel-card"
        :class="{ 'active': selectedChannels.includes(channel.id) }"
      >
        <input 
          type="checkbox" 
          :value="channel.id"
          v-model="selectedChannels"
          @change="updateChannels"
        />
        <div class="channel-icon">{{ channel.icon }}</div>
        <div class="channel-info">
          <div class="channel-name">{{ channel.name }}</div>
          <div class="channel-desc">{{ channel.description }}</div>
        </div>
      </label>
    </div>
    
    <!-- Channel-specific Configuration -->
    <div v-if="selectedChannels.length > 0" class="channel-settings">
      <h4>Channel Settings</h4>
      
      <div v-if="selectedChannels.includes('email')" class="channel-setting-group">
        <h5>Email Settings</h5>
        <div class="field-group">
          <label>Subject Line</label>
          <input 
            v-model="channelSettings.email.subject" 
            placeholder="Campaign email subject"
            @input="updateChannelSettings"
          />
        </div>
        <div class="field-group">
          <label>From Name</label>
          <input 
            v-model="channelSettings.email.from_name" 
            placeholder="Sender name"
            @input="updateChannelSettings"
          />
        </div>
        <div class="field-group">
          <label>Template ID (Optional)</label>
          <input 
            v-model="channelSettings.email.template_id" 
            placeholder="Email template ID"
            @input="updateChannelSettings"
          />
        </div>
      </div>
      
      <div v-if="selectedChannels.includes('sms')" class="channel-setting-group">
        <h5>SMS Settings</h5>
        <div class="field-group">
          <label>Message Template</label>
          <textarea 
            v-model="channelSettings.sms.message" 
            rows="3"
            placeholder="SMS message template"
            @input="updateChannelSettings"
          ></textarea>
          <small class="help-text">Use {{variable}} for dynamic content</small>
        </div>
        <div class="field-group">
          <label>Sender ID</label>
          <input 
            v-model="channelSettings.sms.sender_id" 
            placeholder="SMS sender ID"
            @input="updateChannelSettings"
          />
        </div>
      </div>
      
      <div v-if="selectedChannels.includes('push')" class="channel-setting-group">
        <h5>Push Notification Settings</h5>
        <div class="field-group">
          <label>Title</label>
          <input 
            v-model="channelSettings.push.title" 
            placeholder="Push notification title"
            @input="updateChannelSettings"
          />
        </div>
        <div class="field-group">
          <label>Body</label>
          <textarea 
            v-model="channelSettings.push.body" 
            rows="3"
            placeholder="Push notification body"
            @input="updateChannelSettings"
          ></textarea>
        </div>
        <div class="field-group">
          <label>Deep Link (Optional)</label>
          <input 
            v-model="channelSettings.push.deep_link" 
            placeholder="e.g., app://campaign/123"
            @input="updateChannelSettings"
          />
        </div>
      </div>
      
      <div v-if="selectedChannels.includes('in_app')" class="channel-setting-group">
        <h5>In-App Settings</h5>
        <div class="field-group">
          <label>Banner Title</label>
          <input 
            v-model="channelSettings.in_app.title" 
            placeholder="In-app banner title"
            @input="updateChannelSettings"
          />
        </div>
        <div class="field-group">
          <label>Banner Message</label>
          <textarea 
            v-model="channelSettings.in_app.message" 
            rows="3"
            placeholder="In-app banner message"
            @input="updateChannelSettings"
          ></textarea>
        </div>
        <div class="field-group">
          <label>Action Button Text</label>
          <input 
            v-model="channelSettings.in_app.action_text" 
            placeholder="e.g., View Offer"
            @input="updateChannelSettings"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  channels: string[]
}>()

const emit = defineEmits(['update:channels'])

const availableChannels = [
  { id: 'email', name: 'Email', icon: '📧', description: 'Send via email' },
  { id: 'sms', name: 'SMS', icon: '💬', description: 'Send via SMS' },
  { id: 'push', name: 'Push Notification', icon: '🔔', description: 'Mobile push notification' },
  { id: 'in_app', name: 'In-App', icon: '📱', description: 'In-app message/banner' },
]

const selectedChannels = ref<string[]>([...props.channels])

watch(() => props.channels, (newChannels) => {
  selectedChannels.value = [...newChannels]
})

const updateChannels = () => {
  emit('update:channels', [...selectedChannels.value])
}
</script>

<style scoped>
.channel-config {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.config-header {
  margin-bottom: 1rem;
}

.config-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0;
}

.help-text {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 1.5rem;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 2rem;
}

.channel-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.channel-card:hover {
  border-color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.channel-card.active {
  border-color: #2563eb;
  background: #eff6ff;
}

.channel-card input[type="checkbox"] {
  width: 20px;
  height: 20px;
  cursor: pointer;
}

.channel-icon {
  font-size: 2rem;
}

.channel-info {
  flex: 1;
}

.channel-name {
  font-weight: 600;
  margin-bottom: 0.25rem;
}

.channel-desc {
  font-size: 0.875rem;
  color: #666;
}

.channel-settings {
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 2px solid #e0e0e0;
}

.channel-settings h4 {
  font-size: 1rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.channel-setting-group {
  margin-bottom: 2rem;
  padding: 1rem;
  background: #f9fafb;
  border-radius: 6px;
}

.channel-setting-group h5 {
  font-size: 0.875rem;
  font-weight: 600;
  margin-bottom: 1rem;
  color: #2563eb;
}

.field-group {
  margin-bottom: 1rem;
}

.field-group label {
  display: block;
  font-size: 0.875rem;
  font-weight: 500;
  color: #666;
  margin-bottom: 0.5rem;
}

.field-group input,
.field-group textarea {
  width: 100%;
  padding: 0.5rem;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
  font-size: 0.875rem;
}

.field-group textarea {
  resize: vertical;
}

.field-group small {
  font-size: 0.75rem;
  color: #999;
  margin-top: 0.25rem;
  display: block;
}
</style>

