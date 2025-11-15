#!/bin/bash

# Counter AI - Redis Cache Setup Script
# This script helps set up and test Redis cache connection

set -e  # Exit on error

echo "💾 Counter AI - Redis Cache Setup"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "Choose your Redis provider:"
echo ""
echo "  1) Upstash (Recommended for Vercel)"
echo "     - Serverless Redis"
echo "     - Pay-as-you-go pricing"
echo "     - Global edge network"
echo "     - Free tier: 10,000 commands/day"
echo ""
echo "  2) Redis Cloud"
echo "     - Managed Redis"
echo "     - Free tier: 30MB storage"
echo "     - Traditional Redis protocol"
echo ""

read -p "Enter choice (1 or 2): " -n 1 -r
echo ""
echo ""

if [[ $REPLY == "1" ]]; then
    echo -e "${BLUE}Setting up Upstash Redis${NC}"
    echo "========================"
    echo ""
    echo "Steps:"
    echo "  1. Go to https://upstash.com"
    echo "  2. Sign up or log in"
    echo "  3. Click 'Create Database'"
    echo "  4. Configure:"
    echo "     - Name: counter-ai-cache"
    echo "     - Type: Regional"
    echo "     - Region: (same as your Vercel deployment)"
    echo "     - TLS: Enabled"
    echo "  5. Copy the connection details"
    echo ""
    echo "You'll need:"
    echo "  - UPSTASH_REDIS_REST_URL"
    echo "  - UPSTASH_REDIS_REST_TOKEN"
    echo ""
    
elif [[ $REPLY == "2" ]]; then
    echo -e "${BLUE}Setting up Redis Cloud${NC}"
    echo "======================"
    echo ""
    echo "Steps:"
    echo "  1. Go to https://redis.com/cloud"
    echo "  2. Sign up or log in"
    echo "  3. Click 'New Database'"
    echo "  4. Configure:"
    echo "     - Name: counter-ai-cache"
    echo "     - Cloud: AWS"
    echo "     - Region: (same as your deployment)"
    echo "     - Memory: 30MB (free tier)"
    echo "  5. Copy the connection URL"
    echo ""
    echo "Connection URL format:"
    echo "  redis://default:[password]@[endpoint]:6379"
    echo ""
else
    echo "Invalid choice"
    exit 1
fi

read -p "Press Enter when you have your Redis URL..."
echo ""

# Check if REDIS_URL is set
if [ -z "$REDIS_URL" ]; then
    echo -e "${YELLOW}⚠️  REDIS_URL not set${NC}"
    echo ""
    echo "Please set your Redis connection URL:"
    echo ""
    if [[ $REPLY == "1" ]]; then
        echo "  export REDIS_URL='https://[endpoint].upstash.io'"
    else
        echo "  export REDIS_URL='redis://default:[password]@[endpoint]:6379'"
    fi
    echo ""
    read -p "Would you like to set it now? (y/n) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter REDIS_URL: " REDIS_URL
        export REDIS_URL
        echo ""
        echo -e "${GREEN}✓ REDIS_URL set${NC}"
    else
        echo "Please set REDIS_URL and run this script again"
        exit 1
    fi
else
    echo -e "${GREEN}✓ REDIS_URL is set${NC}"
fi

echo ""

# Test Redis connection
echo "Testing Redis connection..."
echo ""

python scripts/verify_redis.py

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN}✅ Redis setup complete!${NC}"
    echo ""
    echo "Next steps:"
    echo "  1. Add REDIS_URL to Vercel:"
    echo "     vercel env add REDIS_URL production"
    echo "  2. Deploy your application"
    echo "  3. Monitor cache performance in Redis dashboard"
    echo ""
    
    if [[ $REPLY == "1" ]]; then
        echo "Upstash Dashboard: https://console.upstash.com"
    else
        echo "Redis Cloud Dashboard: https://app.redislabs.com"
    fi
    echo ""
else
    echo ""
    echo -e "${RED}❌ Redis connection test failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  - Verify REDIS_URL is correct"
    echo "  - Check that TLS is enabled (for Upstash)"
    echo "  - Verify firewall/network settings"
    echo "  - Check Redis dashboard for connection logs"
    echo ""
    exit 1
fi
