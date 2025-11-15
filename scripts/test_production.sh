#!/bin/bash

# Counter AI - Production Testing Script
# This script tests all production endpoints

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "🧪 Counter AI - Production Testing"
echo "==================================="
echo ""

# Check if production URL is provided
if [ -z "$1" ]; then
    echo -e "${RED}❌ Production URL not provided${NC}"
    echo ""
    echo "Usage: ./scripts/test_production.sh https://your-domain.vercel.app"
    exit 1
fi

PROD_URL=$1
echo "Testing: $PROD_URL"
echo ""

# Test counter
PASSED=0
FAILED=0

# Function to test endpoint
test_endpoint() {
    local name=$1
    local endpoint=$2
    local data=$3
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${BLUE}Testing: $name${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Endpoint: $endpoint"
    echo ""
    
    # Make request and capture response
    response=$(curl -s -w "\n%{http_code}\n%{time_total}" -X POST "$PROD_URL$endpoint" \
        -H "Content-Type: application/json" \
        -d "$data")
    
    # Parse response
    http_code=$(echo "$response" | tail -n 2 | head -n 1)
    time_total=$(echo "$response" | tail -n 1)
    body=$(echo "$response" | head -n -2)
    
    # Check status code
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}✓ Status: 200 OK${NC}"
        echo -e "${GREEN}✓ Response time: ${time_total}s${NC}"
        
        # Check response time
        if (( $(echo "$time_total < 1.0" | bc -l) )); then
            echo -e "${GREEN}✓ Performance: Under 1 second${NC}"
        else
            echo -e "${YELLOW}⚠️  Performance: Over 1 second${NC}"
        fi
        
        # Show response preview
        echo ""
        echo "Response preview:"
        echo "$body" | head -c 200
        echo "..."
        echo ""
        
        PASSED=$((PASSED + 1))
        return 0
    else
        echo -e "${RED}❌ Status: $http_code${NC}"
        echo ""
        echo "Error response:"
        echo "$body"
        echo ""
        
        FAILED=$((FAILED + 1))
        return 1
    fi
}

# Test 1: Health Check
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${BLUE}Testing: Health Check${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Endpoint: /api/health"
echo ""

health_response=$(curl -s -w "\n%{http_code}" "$PROD_URL/api/health")
health_code=$(echo "$health_response" | tail -n 1)
health_body=$(echo "$health_response" | head -n -1)

if [ "$health_code" = "200" ]; then
    echo -e "${GREEN}✓ Health check passed${NC}"
    echo "$health_body"
    echo ""
    PASSED=$((PASSED + 1))
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "$health_body"
    echo ""
    FAILED=$((FAILED + 1))
fi

# Test 2: Property Search
test_endpoint \
    "Property Search" \
    "/api/tools/search" \
    '{
        "location": "Baltimore, MD",
        "max_price": 400000,
        "min_beds": 3,
        "user_id": "test-user-prod"
    }'

# Test 3: Risk Analysis
test_endpoint \
    "Risk Analysis" \
    "/api/tools/analyze-risk" \
    '{
        "property_id": "test-property-123",
        "address": "123 Main St, Baltimore, MD 21201",
        "list_price": 400000,
        "user_id": "test-user-prod"
    }'

# Test 4: Schedule Viewing
test_endpoint \
    "Schedule Viewing" \
    "/api/tools/schedule" \
    '{
        "property_id": "test-property-123",
        "listing_url": "https://www.zillow.com/homedetails/123-Main-St/12345_zpid/",
        "requested_time": "2025-11-20T14:00:00",
        "user_id": "test-user-prod",
        "user_name": "Test User",
        "user_email": "test@example.com"
    }'

# Test 5: Draft Offer
test_endpoint \
    "Draft Offer" \
    "/api/tools/draft-offer" \
    '{
        "property_id": "test-property-123",
        "address": "123 Main St, Baltimore, MD 21201",
        "offer_price": 380000,
        "closing_days": 30,
        "financing_type": "conventional",
        "contingencies": ["inspection", "appraisal"],
        "user_id": "test-user-prod",
        "user_email": "test@example.com"
    }'

# Summary
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST SUMMARY"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo -e "${GREEN}Passed: $PASSED${NC}"
echo -e "${RED}Failed: $FAILED${NC}"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo ""
    echo "Production deployment is working correctly."
    echo ""
    echo "Next steps:"
    echo "  1. Test voice flow by calling Vapi phone number"
    echo "  2. Monitor logs: vercel logs --follow"
    echo "  3. Check metrics in Vercel dashboard"
    echo ""
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check Vercel logs: vercel logs -n 100"
    echo "  2. Verify environment variables: vercel env ls"
    echo "  3. Test endpoints individually with curl"
    echo "  4. Review error messages above"
    echo ""
    exit 1
fi
