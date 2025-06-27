# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

elPyFi Dashboard is a Next.js-based trading dashboard that displays real-time positions, signals, and performance metrics. It uses TypeScript, Tailwind CSS v4, and modern React patterns.

## Common Development Commands

```bash
# Start development server with Turbopack
npm run dev

# Build for production
npm run build

# Run production server
npm start

# Run linting
npm run lint

# Type checking (if needed)
npx tsc --noEmit
```

## Architecture & Structure

### Key Technologies
- **Next.js 15** with App Router (not Pages Router)
- **TypeScript** for type safety
- **Tailwind CSS v4** with simplified configuration
- **SWR** for data fetching and caching
- **Chart.js** for performance visualizations
- **Socket.io-client** for WebSocket connections

### Directory Structure
- `/app` - Next.js App Router pages and layouts
- `/components` - Reusable React components
- `/lib` - Business logic, API clients, and utilities
- `/types` - TypeScript type definitions
- `/utils` - Helper functions

### Important Patterns

1. **Data Fetching**: Uses SWR hooks with automatic refresh intervals
   ```typescript
   const { data, error } = useSWR('key', fetcher, { refreshInterval: 5000 })
   ```

2. **Dark Mode**: Implemented via Tailwind's dark: prefix, toggled in Navigation component
   - Theme state stored in localStorage
   - Applied to document.documentElement classList

3. **Mock Data**: Currently uses mock data from `/lib/api.ts`
   - Replace fetchPositions, fetchSignals, etc. with real API calls when backend is ready

4. **Component Architecture**: 
   - Client components marked with "use client"
   - Server components by default in App Router
   - Real-time updates handled in client components only

### API Integration Points

When connecting to a real backend:
1. Update functions in `/lib/api.ts` to make actual HTTP requests
2. Configure WebSocket URL in `.env.local`
3. Update mock data delays to match real network latency
4. Add error handling and retry logic as needed

### Styling Guidelines

- Use Tailwind CSS classes exclusively
- Dark mode: Always provide both light and dark variants
- Responsive design: Mobile-first approach with sm:, md:, lg: breakpoints
- Component styling: Keep styles within component files, no separate CSS

### Testing Considerations

When adding tests:
- Use React Testing Library for component tests
- Mock SWR hooks in tests
- Test dark/light mode toggle functionality
- Ensure responsive layouts work at all breakpoints

### Performance Optimization

- Components use React.memo where appropriate
- SWR handles caching automatically
- Images should use Next.js Image component
- Lazy load heavy components like charts

### Security Notes

- Environment variables prefixed with NEXT_PUBLIC_ are exposed to the browser
- Never commit real API keys or secrets
- WebSocket connections should use wss:// in production
- Implement proper CORS headers on the backend

## PM Claude Status
*Updated by PM Claude on 2025-06-25 23:26:53*

- **Service Status**: stopped

### Integration with PM Claude
This service is managed by PM Claude and uses:
- Shared Python 3.11 virtual environment
- Centralized secrets management
- Automated health monitoring
- Unified test runner

### Known Issues
- [RESOLVED] [818d735b] Add loading states and error handling for API calls
  - SWR hooks in components don't show loading spinners or error messages. Add proper loading states and error displays for better UX when API is down or slow. ~20 lines across components.
- [RESOLVED] [677c187a] Add error boundary components to prevent full app crashes
  - Wrap main components in React error boundaries to catch and display errors gracefully instead of white screen. Add to PositionsTable, SignalsTable, and PerformanceChart components. ~50 lines total.
- [RESOLVED] [c22f137b] Known Issues section missing
  - CLAUDE.md updater not adding issues - need to check service ID matching
- [RESOLVED] [ea138c82] Hydration warning with Dark Reader
  - Dark Reader browser extension causes hydration mismatch in Navigation.tsx SVG elements
