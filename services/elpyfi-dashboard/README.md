# elPyFi Dashboard

A real-time trading dashboard built with Next.js, TypeScript, and Tailwind CSS for monitoring positions, signals, and performance metrics.

## Features

- 📊 Real-time position tracking
- 📈 Live trading signals feed
- 💹 Performance analytics and charts
- 🌓 Dark mode support
- 📱 Fully responsive design
- ⚡ WebSocket support for live updates
- 🎯 Pattern Day Trader (PDT) status monitoring

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/elpyfi-dashboard.git
cd elpyfi-dashboard
```

2. Install dependencies:
```bash
npm install
```

3. Copy the environment variables:
```bash
cp .env.example .env.local
```

4. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

## Development

### Available Scripts

- `npm run dev` - Start the development server with Turbopack
- `npm run build` - Build for production
- `npm run start` - Start the production server
- `npm run lint` - Run ESLint

### Project Structure

```
elpyfi-dashboard/
├── app/                 # Next.js app router pages
│   ├── page.tsx        # Main dashboard
│   ├── strategies/     # Strategies page
│   └── analytics/      # Analytics page
├── components/         # React components
│   ├── Navigation.tsx  # Top navigation bar
│   ├── PositionCard.tsx
│   ├── SignalFeed.tsx
│   ├── PDTStatus.tsx
│   └── PerformanceChart.tsx
├── lib/                # Utilities and API
│   ├── api.ts         # API client and types
│   └── websocket.ts   # WebSocket manager
└── public/            # Static assets
```

### Technologies Used

- **Framework**: Next.js 15 with App Router
- **Language**: TypeScript
- **Styling**: Tailwind CSS v4
- **Data Fetching**: SWR
- **Charts**: Chart.js with react-chartjs-2
- **WebSocket**: Socket.io-client
- **Date Formatting**: date-fns

## Deployment

This project is optimized for deployment on:
- [Vercel](https://vercel.com) (recommended)
- [Railway](https://railway.app)
- [Render](https://render.com)

### Deploy to Vercel

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/yourusername/elpyfi-dashboard)

### Environment Variables

Set these environment variables in your deployment:

```env
NEXT_PUBLIC_WS_URL=wss://your-websocket-server.com
NEXT_PUBLIC_API_URL=https://your-api-server.com/api
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.