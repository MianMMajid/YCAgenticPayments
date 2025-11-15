#!/bin/bash

# Counter AI - Production Deployment Script
# This script helps automate the deployment process

set -e  # Exit on error

echo "🚀 Counter AI - Production Deployment"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI not found${NC}"
    echo "Install with: npm install -g vercel"
    exit 1
fi

echo -e "${GREEN}✓ Vercel CLI found${NC}"

# Check if user is logged in to Vercel
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}⚠ Not logged in to Vercel${NC}"
    echo "Running: vercel login"
    vercel login
fi

echo -e "${GREEN}✓ Logged in to Vercel${NC}"
echo ""

# Step 1: Verify environment variables
echo "📋 Step 1: Checking environment variables"
echo "=========================================="

REQUIRED_VARS=(
    "DATABASE_URL"
    "REDIS_URL"
    "RENTCAST_API_KEY"
    "DOCUSIGN_INTEGRATION_KEY"
    "DOCUSIGN_SECRET_KEY"
    "DOCUSIGN_ACCOUNT_ID"
    "ENCRYPTION_KEY"
    "OPENAI_API_KEY"
)

echo "Required environment variables:"
for var in "${REQUIRED_VARS[@]}"; do
    echo "  - $var"
done

echo ""
read -p "Have you configured all environment variables in Vercel? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠ Please configure environment variables first${NC}"
    echo ""
    echo "Run these commands to add each variable:"
    echo ""
    for var in "${REQUIRED_VARS[@]}"; do
        echo "  vercel env add $var production"
    done
    echo ""
    echo "See docs/deployment_guide.md for details"
    exit 1
fi

echo -e "${GREEN}✓ Environment variables configured${NC}"
echo ""

# Step 2: Run database migrations
echo "🗄️  Step 2: Database migrations"
echo "==============================="

read -p "Have you run database migrations on your production database? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠ Please run migrations first${NC}"
    echo ""
    echo "1. Set DATABASE_URL to your production database:"
    echo "   export DATABASE_URL='your-supabase-pooler-url'"
    echo ""
    echo "2. Run migrations:"
    echo "   alembic upgrade head"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Database migrations completed${NC}"
echo ""

# Step 3: Test Redis connection
echo "💾 Step 3: Redis cache"
echo "======================"

read -p "Have you set up Redis (Upstash or Redis Cloud)? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}⚠ Please set up Redis first${NC}"
    echo ""
    echo "Option A - Upstash (Recommended):"
    echo "  1. Sign up at https://upstash.com"
    echo "  2. Create a new Redis database"
    echo "  3. Copy the UPSTASH_REDIS_REST_URL"
    echo "  4. Add to Vercel: vercel env add REDIS_URL production"
    echo ""
    echo "Option B - Redis Cloud:"
    echo "  1. Sign up at https://redis.com/cloud"
    echo "  2. Create a new database"
    echo "  3. Copy the connection URL"
    echo "  4. Add to Vercel: vercel env add REDIS_URL production"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ Redis configured${NC}"
echo ""

# Step 4: Deploy to Vercel
echo "🚢 Step 4: Deploying to Vercel"
echo "==============================="

read -p "Ready to deploy to production? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

echo ""
echo "Deploying to production..."
echo ""

# Deploy to production
vercel --prod

echo ""
echo -e "${GREEN}✓ Deployment successful!${NC}"
echo ""

# Step 5: Get deployment URL
DEPLOYMENT_URL=$(vercel ls --prod | grep -m 1 "counter" | awk '{print $2}')

if [ -z "$DEPLOYMENT_URL" ]; then
    echo "Getting deployment URL..."
    DEPLOYMENT_URL=$(vercel ls | head -n 2 | tail -n 1 | awk '{print $2}')
fi

echo "📍 Production URL: https://$DEPLOYMENT_URL"
echo ""

# Step 6: Test deployment
echo "🧪 Step 5: Testing deployment"
echo "=============================="

echo "Testing health endpoint..."

if curl -s "https://$DEPLOYMENT_URL/api/health" > /dev/null; then
    echo -e "${GREEN}✓ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "Check logs with: vercel logs --follow"
fi

echo ""

# Step 7: Update Vapi
echo "🎙️  Step 6: Update Vapi Assistant"
echo "=================================="

echo "Update your Vapi assistant with these URLs:"
echo ""
echo "  search_properties:  https://$DEPLOYMENT_URL/api/tools/search"
echo "  analyze_risk:       https://$DEPLOYMENT_URL/api/tools/analyze-risk"
echo "  schedule_viewing:   https://$DEPLOYMENT_URL/api/tools/schedule"
echo "  draft_offer:        https://$DEPLOYMENT_URL/api/tools/draft-offer"
echo ""
echo "Go to: https://dashboard.vapi.ai"
echo ""

read -p "Press Enter when you've updated Vapi..."

echo ""
echo -e "${GREEN}✅ Deployment Complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Test voice flow by calling your Vapi phone number"
echo "  2. Monitor logs: vercel logs --follow"
echo "  3. Check Vercel dashboard: https://vercel.com/dashboard"
echo "  4. Review deployment guide: docs/deployment_guide.md"
echo ""
echo "Troubleshooting:"
echo "  - View logs: vercel logs -n 100"
echo "  - Rollback: vercel rollback [deployment-url]"
echo "  - Check env vars: vercel env ls"
echo ""
