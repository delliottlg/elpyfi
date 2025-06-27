#!/bin/bash
# Deploy to Railway

echo "🚂 Deploying ElPyFi to Railway..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "❌ Railway CLI not found. Install it with:"
    echo "   brew install railway"
    echo "   or"
    echo "   npm install -g @railway/cli"
    exit 1
fi

# Login to Railway
echo "📝 Logging in to Railway..."
railway login

# Link to project (first time only)
if [ ! -f ".railway/config.json" ]; then
    echo "🔗 Linking to Railway project..."
    railway link
fi

# Deploy with docker-compose
echo "🚀 Deploying services..."
railway up

echo "✅ Deployment complete!"
echo ""
echo "📊 View your services at:"
echo "   https://railway.app/dashboard"