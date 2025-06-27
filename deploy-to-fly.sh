#!/bin/bash
# Deploy all services to Fly.io

echo "🚀 Deploying ElPyFi to Fly.io..."

# Load environment variables from .env.fly
if [ -f .env.fly ]; then
    export $(cat .env.fly | grep -v '^#' | xargs)
    echo "✅ Loaded secrets from .env.fly"
else
    echo "❌ .env.fly not found! Create it with your API keys."
    exit 1
fi

# Install flyctl if not installed
if ! command -v flyctl &> /dev/null; then
    echo "Installing flyctl..."
    curl -L https://fly.io/install.sh | sh
fi

# Ensure we're logged in
flyctl auth login

# Skip Postgres for now (Fly.io Postgres is broken in transition)
echo "⏭️  Skipping PostgreSQL - deploying services without database for now..."

# Create and deploy each app
for service in core ai api dashboard; do
    echo ""
    echo "🔧 Setting up elpyfi-$service..."
    
    # Create app if it doesn't exist
    flyctl apps create elpyfi-$service --machines || echo "App elpyfi-$service already exists"
    
    # Skip database attachment for now
    echo "⏭️  Skipping database attachment (PostgreSQL will be added later)"
    
    # Set secrets based on service
    case $service in
        core)
            flyctl secrets set \
                CORE_ALPACA_API_KEY="$ALPACA_API_KEY" \
                CORE_ALPACA_SECRET_KEY="$ALPACA_SECRET_KEY" \
                --app elpyfi-core
            ;;
        ai)
            flyctl secrets set \
                AI_ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
                AI_OPENAI_API_KEY="$OPENAI_API_KEY" \
                --app elpyfi-ai
            ;;
        api)
            flyctl secrets set \
                ELPYFI_API_KEYS='["dashboard-api-key-123"]' \
                --app elpyfi-api
            ;;
        dashboard)
            flyctl secrets set \
                NEXT_PUBLIC_API_BASE_URL="https://elpyfi-api.fly.dev" \
                NEXT_PUBLIC_WEBSOCKET_URL="wss://elpyfi-api.fly.dev" \
                --app elpyfi-dashboard
            ;;
    esac
    
    # Deploy with proper context
    echo "🚀 Deploying elpyfi-$service..."
    case $service in
        core)
            flyctl deploy services/elpyfi-core/elpyfi-engine --config fly.$service.toml --app elpyfi-$service
            ;;
        dashboard)
            flyctl deploy services/elpyfi-dashboard --config fly.$service.toml --app elpyfi-$service
            ;;
        *)
            flyctl deploy services/elpyfi-$service --config fly.$service.toml --app elpyfi-$service
            ;;
    esac
done

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🌐 Your services are available at:"
echo "   API: https://elpyfi-api.fly.dev"
echo "   AI: https://elpyfi-ai.fly.dev"
echo "   Dashboard: https://elpyfi-dashboard.fly.dev"
echo ""
echo "📊 View status with: flyctl status --app elpyfi-core"