# Frontend Development Guide

## Overview

Vue 3 + TypeScript frontend for the Loyalty Console. Built to match Pelatro mViva features with modern UI/UX.

## Tech Stack

- **Vue 3** - Composition API
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Vue Router** - Routing
- **Pinia** - State management
- **Axios** - HTTP client
- **ECharts** - Charts and visualizations
- **Vue Flow** - Journey builder
- **JSONLogic** - Rule evaluation

---

## Project Structure

```
frontend/
├── src/
│   ├── api/
│   │   ├── client.ts              # Axios client
│   │   └── services/              # API services
│   │       ├── programs.ts
│   │       ├── campaigns.ts
│   │       ├── segments.ts
│   │       └── ml.ts
│   ├── components/                # Reusable components
│   │   ├── VisualRuleBuilder.vue # JSONLogic rule builder
│   │   └── ...
│   ├── layouts/
│   │   └── DashboardLayout.vue   # Main layout
│   ├── router/
│   │   └── index.ts              # Routes
│   ├── stores/
│   │   └── auth.ts               # Auth store
│   ├── types/
│   │   ├── auth.ts
│   │   └── loyalty.ts
│   ├── views/
│   │   ├── Dashboard.vue
│   │   ├── Login.vue
│   │   ├── Programs/
│   │   │   ├── ProgramList.vue
│   │   │   ├── ProgramDetail.vue
│   │   │   └── ProgramBuilder.vue
│   │   ├── Campaigns/
│   │   ├── Segments/
│   │   ├── Customers/
│   │   └── ...
│   ├── App.vue
│   └── main.ts
├── package.json
├── vite.config.ts
└── tsconfig.json
```

---

## Getting Started

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API Base URL

The frontend is configured to proxy API requests to `http://localhost:8000` via Vite proxy.

Or create `frontend/.env`:

```
VITE_API_BASE_URL=http://localhost:8000
```

### 3. Start Dev Server

```bash
npm run dev
```

Frontend runs at: `http://localhost:5173`

---

## Features Implemented

### ✅ Core Pages

- **Dashboard** - Overview, KPIs, charts
- **Login** - Authentication
- **Programs List** - List/create/edit programs
- **Program Builder** - Create/edit programs with tiers and rules
- **Campaigns List** - List/manage campaigns
- **Campaign Detail** - View campaign metrics
- **Segments List** - List/manage segments
- **Segment Builder** - Visual JSONLogic rule editor
- **Segment Detail** - View segment metrics
- **Customer 360** - Customer view with ML predictions
- **Admin Dashboard** - System configuration

### ✅ API Services

- `programsApi` - Program CRUD
- `campaignsApi` - Campaign management
- `segmentsApi` - Segment management
- `mlApi` - ML predictions, DWH features
- `configApi` - System configuration

### ✅ Components

- **VisualRuleBuilder** - Visual JSONLogic rule builder
- **TierManager** - Program tier management
- **DashboardLayout** - Main layout with sidebar
- **Charts** - ECharts integration for analytics

---

## Development Roadmap

### Phase 1: Core Features ✅

- [x] Program Builder with tiers and rules
- [x] Campaign Builder
- [x] Segment Builder with visual rule editor
- [x] Customer 360 with ML predictions

### Phase 2: Advanced Features

- [ ] Journey Builder enhancements
- [ ] A/B Testing UI
- [ ] Analytics Dashboard
- [ ] Gamification UI
- [ ] Partner Management UI

---

## API Integration Examples

### Using ML API

```typescript
import { mlApi } from '@/api/services/ml'

// Predict NBO
const nbo = await mlApi.predictNBO(customerId)
console.log('Recommended offer:', nbo.data.recommended_offer)

// Predict churn
const churn = await mlApi.predictChurn(customerId)
if (churn.data.churn_risk === 'high') {
  // Trigger retention campaign
}

// Get DWH features
const features = await mlApi.getCustomerFeatures(customerId)
console.log('Customer features:', features.data)
```

### Using Segments API

```typescript
import { segmentsApi } from '@/api/services/segments'

// Create segment
const segment = await segmentsApi.create({
  name: 'VIP Customers',
  rules: [{
    "and": [
      {">": [{"var": "total_revenue"}, 1000]}
    ]
  }],
  is_dynamic: true
})

// Recalculate segment
await segmentsApi.recalculate(segment.data.id)

// Get members
const members = await segmentsApi.getMembers(segment.data.id)
```

---

## Component Guidelines

### 1. Use Composition API

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { programsApi } from '@/api/services/programs'

const programs = ref([])

onMounted(async () => {
  const response = await programsApi.getAll()
  programs.value = response.data
})
</script>
```

### 2. Use TypeScript Types

```typescript
import type { Campaign } from '@/types/loyalty'

const campaign = ref<Campaign | null>(null)
```

### 3. Error Handling

```typescript
try {
  await campaignsApi.create(data)
} catch (error: any) {
  console.error('Error:', error)
  alert(error.response?.data?.message || 'Error creating campaign')
}
```

---

## Styling

Using scoped CSS in components. For global styles, add to `src/style.css`.

**Color scheme:**
- Primary: `#2563eb` (Blue)
- Success: `#10b981` (Green)
- Warning: `#f59e0b` (Orange)
- Danger: `#ef4444` (Red)

---

## Development Commands

```bash
# Run dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview

# Type check
npm run type-check

# Lint
npm run lint
```

---

## Next Steps

- See [USER_GUIDE.md](USER_GUIDE.md) for using the platform
- See [API_REFERENCE.md](API_REFERENCE.md) for API details
- See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for common issues

