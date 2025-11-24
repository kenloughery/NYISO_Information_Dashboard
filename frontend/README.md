# NYISO Trading Dashboard - Frontend

React + TypeScript dashboard for NYISO Power Trading Command Center.

## Tech Stack

- **React 19** with **TypeScript**
- **Vite** - Build tool and dev server
- **TanStack Query (React Query)** - Server state management
- **Zustand** - Client state management
- **Recharts** - Chart library
- **Leaflet** - Geographic visualizations
- **Material-UI** - Component library
- **Tailwind CSS** - Utility-first styling

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Backend API running on `http://localhost:8000` (see main project README)

### Installation

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The app will be available at `http://localhost:3000`

### Environment Variables

Create a `.env` file (or copy `.env.example`):

```env
VITE_API_BASE_URL=http://localhost:8000
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── common/          # Reusable UI components
│   │   ├── charts/          # Chart components
│   │   ├── maps/            # Geographic visualizations
│   │   └── sections/        # Dashboard section components
│   ├── hooks/               # Custom React hooks
│   │   ├── useRealTimeData.ts    # Real-time data hooks (5-min refresh)
│   │   └── useHistoricalData.ts  # Historical data hooks
│   ├── services/            # API clients
│   │   ├── api.ts           # API client with all endpoints
│   │   └── queryClient.ts   # React Query configuration
│   ├── store/               # State management
│   │   └── dashboardStore.ts    # Zustand store
│   ├── types/               # TypeScript types
│   │   └── api.ts           # API response types
│   ├── utils/               # Utility functions
│   ├── constants/           # Constants and config
│   │   └── config.ts        # App configuration
│   ├── App.tsx              # Main app component
│   └── main.tsx             # Entry point
├── public/                  # Static assets
└── package.json
```

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## API Integration

All API endpoints are available through typed hooks:

```typescript
// Real-time data (auto-refreshes every 5 minutes)
import { useRealTimeLBMP, useConstraints } from '@/hooks/useRealTimeData';

// Historical data
import { useDayAheadLBMP, useRTDASpreads } from '@/hooks/useHistoricalData';

// Usage in component
const { data, isLoading, error } = useRealTimeLBMP({ zones: ['WEST', 'NYC'] });
```

## State Management

### Server State (React Query)
- All API data fetching
- Automatic caching and refetching
- Real-time data auto-refresh

### Client State (Zustand)
- User preferences (selected zones, time ranges)
- UI state (sidebar, active section)
- Portfolio positions
- Alert filters

```typescript
import { useDashboardStore } from '@/store/dashboardStore';

const selectedZones = useDashboardStore((state) => state.selectedZones);
const setSelectedZones = useDashboardStore((state) => state.setSelectedZones);
```

## Development

### Path Aliases

Use `@/` prefix for imports from `src/`:

```typescript
import { Layout } from '@/components/common/Layout';
import { useRealTimeLBMP } from '@/hooks/useRealTimeData';
import { API_BASE_URL } from '@/constants/config';
```

### Adding New Components

1. Create component in appropriate directory (`components/common`, `components/charts`, etc.)
2. Export from component file
3. Import using path alias: `import { Component } from '@/components/...'`

### Adding New API Endpoints

1. Add type to `src/types/api.ts`
2. Add function to `src/services/api.ts`
3. Create hook in `src/hooks/useRealTimeData.ts` or `useHistoricalData.ts`

## Building for Production

```bash
npm run build
```

Output will be in `dist/` directory. Deploy to your hosting service (Vercel, Netlify, etc.).

## Next Steps

Phase 2 is complete! Ready to begin Phase 3: Dashboard Sections Implementation.

See `DASHBOARD_IMPLEMENTATION_PLAN.md` in the root directory for the full implementation plan.
