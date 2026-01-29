<template>
  <div class="nbo-offers">
    <div class="offers-header">
      <h3>Next Best Offers</h3>
      <p class="subtitle">Personalized recommendations based on ML predictions</p>
    </div>
    
    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>Loading recommendations...</p>
    </div>
    
    <div v-else-if="offers.length === 0" class="empty-state">
      <p>No offers available</p>
    </div>
    
    <div v-else class="offers-list">
      <div 
        v-for="(offer, index) in sortedOffers" 
        :key="offer.offer_id || index"
        class="offer-card"
        :class="{ 'top-offer': index === 0 }"
      >
        <div class="offer-rank">{{ index + 1 }}</div>
        <div class="offer-content">
          <div class="offer-name">{{ offer.offer_name || `Offer ${offer.offer_id}` }}</div>
          <div class="offer-category">{{ formatCategory(offer.category) }}</div>
          <div class="offer-probability">
            <div class="probability-bar">
              <div 
                class="probability-fill" 
                :style="{ width: `${offer.probability * 100}%` }"
              ></div>
            </div>
            <span class="probability-value">{{ Math.round(offer.probability * 100) }}% match</span>
          </div>
        </div>
        <div v-if="index === 0" class="top-badge">Best Match</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'

interface NBOOffer {
  offer_id: number
  offer_name: string
  category: string
  probability: number
}

const props = defineProps<{
  offers: NBOOffer[]
  loading?: boolean
}>()

const sortedOffers = computed(() => {
  return [...props.offers].sort((a, b) => b.probability - a.probability)
})

const formatCategory = (category: string) => {
  return category
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}
</script>

<style scoped>
.nbo-offers {
  padding: 1.5rem;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.offers-header {
  margin-bottom: 1.5rem;
}

.offers-header h3 {
  font-size: 1.25rem;
  font-weight: 600;
  color: #1a1a1a;
  margin: 0 0 0.25rem 0;
}

.subtitle {
  font-size: 0.875rem;
  color: #666;
  margin: 0;
}

.loading-state,
.empty-state {
  text-align: center;
  padding: 2rem;
  color: #666;
}

.spinner {
  border: 3px solid #f3f3f3;
  border-top: 3px solid #2563eb;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.offers-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.offer-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  transition: all 0.2s;
  position: relative;
}

.offer-card:hover {
  border-color: #2563eb;
  box-shadow: 0 2px 8px rgba(37, 99, 235, 0.1);
}

.offer-card.top-offer {
  border-color: #00C49F;
  background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 100%);
}

.offer-rank {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f0f0f0;
  border-radius: 50%;
  font-weight: 700;
  font-size: 1.125rem;
  color: #666;
  flex-shrink: 0;
}

.offer-card.top-offer .offer-rank {
  background: #00C49F;
  color: white;
}

.offer-content {
  flex: 1;
}

.offer-name {
  font-size: 1rem;
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 0.25rem;
}

.offer-category {
  font-size: 0.875rem;
  color: #666;
  margin-bottom: 0.5rem;
}

.offer-probability {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.probability-bar {
  flex: 1;
  height: 8px;
  background: #f0f0f0;
  border-radius: 4px;
  overflow: hidden;
}

.probability-fill {
  height: 100%;
  background: linear-gradient(90deg, #2563eb, #3b82f6);
  border-radius: 4px;
  transition: width 0.5s ease;
}

.offer-card.top-offer .probability-fill {
  background: linear-gradient(90deg, #00C49F, #10b981);
}

.probability-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: #666;
  white-space: nowrap;
}

.top-badge {
  position: absolute;
  top: -8px;
  right: 12px;
  background: #00C49F;
  color: white;
  padding: 0.25rem 0.75rem;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}
</style>

