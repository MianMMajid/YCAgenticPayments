#!/bin/bash

# Counter AI - API Keys and Secrets Configuration Script
# This script helps configure all required environment variables in Vercel

set -e  # Exit on error

echo "🔐 Counter AI - Secrets Configuration"
echo "======================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${RED}❌ Vercel CLI not found${NC}"
    echo "Install with: npm install -g vercel"
    exit 1
fi

echo -e "${GREEN}✓ Vercel CLI found${NC}"
echo ""

# Check if logged in
if ! vercel whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Vercel${NC}"
    echo "Running: vercel login"
    vercel login
fi

echo -e "${GREEN}✓ Logged in to Vercel${NC}"
echo ""

echo "This script will help you configure all required API keys and secrets."
echo "You can skip any that are already configured."
echo ""

# Function to add environment variable
add_env_var() {
    local var_name=$1
    local description=$2
    local source_url=$3
    local optional=$4
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}$var_name${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Description: $description"
    if [ ! -z "$source_url" ]; then
        echo "Get from: $source_url"
    fi
    if [ "$optional" = "true" ]; then
        echo -e "${YELLOW}(Optional)${NC}"
    fi
    echo ""
    
    read -p "Configure $var_name? (y/n/skip) " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Adding $var_name to Vercel..."
        vercel env add $var_name production
        echo -e "${GREEN}✓ $var_name configured${NC}"
    elif [[ $REPLY =~ ^[Ss]$ ]]; then
        echo -e "${YELLOW}⊘ Skipped $var_name${NC}"
    else
        echo -e "${YELLOW}⊘ Skipped $var_name${NC}"
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "REQUIRED ENVIRONMENT VARIABLES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Database
add_env_var "DATABASE_URL" \
    "Supabase PostgreSQL connection pooling URL (port 6543)" \
    "Supabase Dashboard → Settings → Database → Connection Pooling" \
    "false"

# Redis
add_env_var "REDIS_URL" \
    "Redis cache connection URL (Upstash or Redis Cloud)" \
    "Upstash: https://console.upstash.com OR Redis Cloud: https://app.redislabs.com" \
    "false"

# RentCast
add_env_var "RENTCAST_API_KEY" \
    "RentCast API key for property listings and data" \
    "https://developers.rentcast.io/" \
    "false"

# Docusign
add_env_var "DOCUSIGN_INTEGRATION_KEY" \
    "Docusign integration key (Client ID)" \
    "https://developers.docusign.com/" \
    "false"

add_env_var "DOCUSIGN_SECRET_KEY" \
    "Docusign secret key (Client Secret)" \
    "https://developers.docusign.com/" \
    "false"

add_env_var "DOCUSIGN_ACCOUNT_ID" \
    "Docusign account ID" \
    "https://developers.docusign.com/" \
    "false"

add_env_var "DOCUSIGN_WEBHOOK_SECRET" \
    "Docusign webhook secret for signature validation" \
    "Generate a random string or use: openssl rand -hex 32" \
    "false"

# Apify
add_env_var "APIFY_API_TOKEN" \
    "Apify API token for Zillow agent scraper" \
    "https://console.apify.com/account/integrations" \
    "false"

# Google Calendar
add_env_var "GOOGLE_CALENDAR_CLIENT_ID" \
    "Google Calendar OAuth client ID" \
    "https://console.cloud.google.com/apis/credentials" \
    "false"

add_env_var "GOOGLE_CALENDAR_CLIENT_SECRET" \
    "Google Calendar OAuth client secret" \
    "https://console.cloud.google.com/apis/credentials" \
    "false"

# Encryption Key
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}ENCRYPTION_KEY${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Description: Fernet encryption key for PII fields"
echo "Generate with: python scripts/generate_encryption_key.py"
echo ""
read -p "Generate and configure ENCRYPTION_KEY? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "Generating encryption key..."
    python scripts/generate_encryption_key.py
    echo ""
    echo "Now adding to Vercel..."
    vercel env add ENCRYPTION_KEY production
    echo -e "${GREEN}✓ ENCRYPTION_KEY configured${NC}"
else
    echo -e "${YELLOW}⊘ Skipped ENCRYPTION_KEY${NC}"
fi

# OpenAI
add_env_var "OPENAI_API_KEY" \
    "OpenAI API key for property summaries (GPT-4o-mini)" \
    "https://platform.openai.com/api-keys" \
    "false"

# SendGrid
add_env_var "SENDGRID_API_KEY" \
    "SendGrid API key for sending emails to listing agents" \
    "https://app.sendgrid.com/settings/api_keys" \
    "false"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "OPTIONAL ENVIRONMENT VARIABLES"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# CrimeoMeter
add_env_var "CRIMEOMETER_API_KEY" \
    "CrimeoMeter API key for crime statistics" \
    "https://www.crimeometer.com/" \
    "true"

# FEMA
add_env_var "FEMA_API_KEY" \
    "FEMA API key (optional, public API)" \
    "https://www.fema.gov/about/openfema/api" \
    "true"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "VERIFICATION"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "Checking configured environment variables..."
echo ""

vercel env ls

echo ""
echo -e "${GREEN}✅ Secrets configuration complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Verify all required variables are set: vercel env ls"
echo "  2. Deploy to production: vercel --prod"
echo "  3. Update Vapi with production URLs"
echo "  4. Test end-to-end voice flow"
echo ""
echo "Security reminders:"
echo "  ⚠️  Never commit secrets to git"
echo "  ⚠️  Rotate API keys every 90 days"
echo "  ⚠️  Store encryption key in password manager"
echo "  ⚠️  Monitor API usage and costs"
echo ""
