#!/bin/bash
# Test Docker setup locally

echo "🐳 Testing Docker setup locally..."

# Check Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker Desktop."
    exit 1
fi

# Copy example env if needed
if [ ! -f .env ]; then
    echo "📝 Creating .env from example..."
    cp .env.example .env
    echo "⚠️  Please edit .env with your actual API keys!"
    exit 1
fi

# Build and run
echo "🔨 Building containers..."
docker-compose build

echo "🚀 Starting services..."
docker-compose up -d

echo "⏳ Waiting for services to start..."
sleep 10

echo "📊 Service status:"
docker-compose ps

echo ""
echo "🌐 Services available at:"
echo "   AI Service:  http://localhost:9000"
echo "   API:         http://localhost:9002"
echo "   Dashboard:   http://localhost:9003"
echo ""
echo "📋 View logs with: docker-compose logs -f"
echo "🛑 Stop with: docker-compose down"