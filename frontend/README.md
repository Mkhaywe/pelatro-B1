# Loyalty Console Frontend

Vue 3 + TypeScript frontend for the Loyalty Management System.

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Development

Frontend runs at: `http://localhost:5173`

Backend API should be running at: `http://localhost:8000`

## Environment Variables

Create `.env` file:

```
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

- `src/api/` - API client and services
- `src/components/` - Reusable components
- `src/layouts/` - Layout components
- `src/router/` - Vue Router configuration
- `src/stores/` - Pinia stores
- `src/types/` - TypeScript types
- `src/views/` - Page components

## Features

- ✅ Dashboard with KPIs
- ✅ Programs management
- ✅ Campaigns management
- ✅ Segments management
- ✅ Customer 360 view
- ✅ ML predictions display
- ✅ JSONLogic rule editor

## Tech Stack

- Vue 3 (Composition API)
- TypeScript
- Vite
- Vue Router
- Pinia
- TanStack Query
- Axios
- Recharts
- TanStack Table

## API Integration

All API calls go through `/api/loyalty/v1/` endpoints.

See `src/api/services/` for API service definitions.

## Next Steps

See `FRONTEND_ROADMAP.md` for remaining features to build.
