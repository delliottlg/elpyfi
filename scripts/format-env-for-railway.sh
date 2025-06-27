#!/bin/bash
# Format .env file for Railway's Variables UI

echo "📋 Formatting environment variables for Railway..."
echo ""
echo "Copy and paste this into Railway's Raw Editor:"
echo "=============================================="
echo ""

# Read .env and format for Railway
# Skip comments and empty lines
grep -v '^#' .env | grep -v '^$' | while IFS= read -r line; do
    echo "$line"
done

echo ""
echo "=============================================="
echo ""
echo "📌 Steps:"
echo "1. Go to your Railway project dashboard"
echo "2. Click on Variables tab"
echo "3. Click 'Raw Editor' button"
echo "4. Paste the above variables"
echo "5. Click 'Save'"
echo ""
echo "🔒 Railway will encrypt and store these securely!"