#!/bin/bash

echo "🚀 Starting PM Claude Dashboard..."

# Function to cleanup background processes
cleanup() {
    echo "Stopping services..."
    kill $API_PID $DASHBOARD_PID 2>/dev/null
    exit 0
}

trap cleanup INT

cd "$(dirname "$0")"

# Start API server in background
echo "Starting API server..."
python src/dashboard_api.py &
API_PID=$!

# Wait for API to start
sleep 2

# Start Next.js dashboard in background
echo "Starting Next.js dashboard..."
cd pm-dashboard-nextjs
npm run dev &
DASHBOARD_PID=$!

cd ..

echo ""
echo "✅ Dashboard running!"
echo "📍 Frontend: http://localhost:8100"
echo "📍 API: http://localhost:8101"
echo ""
echo "Press Ctrl+C to stop both services"

# Wait for both processes
wait