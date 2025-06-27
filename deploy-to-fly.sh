#!/bin/bash
# Deploy all services to Fly.io

echo "🚀 Deploying ElPyFi to Fly.io..."

# Install flyctl if not installed
if ! command -v flyctl &> /dev/null; then
    echo "Installing flyctl..."
    curl -L https://fly.io/install.sh | sh
fi

# Ensure we're logged in
flyctl auth login

# Create Postgres cluster first
echo "📊 Creating PostgreSQL database..."
flyctl postgres create elpyfi-db --region sjc || echo "Database might already exist"

# Create and deploy each app
for service in core ai api dashboard; do
    echo ""
    echo "🔧 Setting up elpyfi-$service..."
    
    # Create app if it doesn't exist
    flyctl apps create elpyfi-$service --machines || echo "App elpyfi-$service already exists"
    
    # Attach to database (except dashboard)
    if [ "$service" != "dashboard" ]; then
        flyctl postgres attach elpyfi-db --app elpyfi-$service || echo "Already attached"
    fi
    
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
    
    # Deploy
    echo "🚀 Deploying elpyfi-$service..."
    flyctl deploy --config fly.$service.toml --app elpyfi-$service
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