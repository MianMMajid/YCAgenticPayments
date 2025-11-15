# Vapi Production Setup Guide

This guide covers updating your Vapi assistant with production URLs and testing the end-to-end voice flow.

## Prerequisites

- Vercel deployment completed
- Production URL obtained (e.g., `https://counter-ai.vercel.app`)
- Vapi account with assistant created
- Twilio phone number connected to Vapi

## Step 1: Generate Production Configuration

Use the configuration generator script to create the production tool configuration:

```bash
python scripts/update_vapi_config.py https://your-domain.vercel.app
```

This will output the complete JSON configuration with your production URLs.

## Step 2: Update Vapi Assistant

### Option A: Using Vapi Dashboard (Recommended)

1. **Login to Vapi Dashboard**
   - Go to https://dashboard.vapi.ai
   - Sign in with your account

2. **Navigate to Your Assistant**
   - Click on "Assistants" in the sidebar
   - Select "Counter AI" (or your assistant name)

3. **Update Tool Functions**
   - Go to the "Functions" or "Tools" tab
   - Click "Edit" or "Configure"
   - Replace the existing function URLs with production URLs:

   ```json
   {
     "functions": [
       {
         "name": "search_properties",
         "url": "https://your-domain.vercel.app/api/tools/search",
         "description": "Search for homes matching criteria",
         "parameters": { ... }
       },
       {
         "name": "analyze_risk",
         "url": "https://your-domain.vercel.app/api/tools/analyze-risk",
         "description": "Analyze property for red flags",
         "parameters": { ... }
       },
       {
         "name": "schedule_viewing",
         "url": "https://your-domain.vercel.app/api/tools/schedule",
         "description": "Schedule property viewing",
         "parameters": { ... }
       },
       {
         "name": "draft_offer",
         "url": "https://your-domain.vercel.app/api/tools/draft-offer",
         "description": "Generate purchase agreement",
         "parameters": { ... }
       }
     ]
   }
   ```

4. **Save Configuration**
   - Click "Save" or "Update"
   - Verify no validation errors

### Option B: Using Vapi API

If you prefer to update via API:

```bash
curl -X PATCH https://api.vapi.ai/assistant/{assistant_id} \
  -H "Authorization: Bearer YOUR_VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @vapi_tools_config.json
```

## Step 3: Verify Tool URLs

Double-check each tool URL is correct:

| Tool | Production URL |
|------|---------------|
| search_properties | `https://your-domain.vercel.app/api/tools/search` |
| analyze_risk | `https://your-domain.vercel.app/api/tools/analyze-risk` |
| schedule_viewing | `https://your-domain.vercel.app/api/tools/schedule` |
| draft_offer | `https://your-domain.vercel.app/api/tools/draft-offer` |

Test each endpoint manually:

```bash
# Test search endpoint
curl -X POST https://your-domain.vercel.app/api/tools/search \
  -H "Content-Type: application/json" \
  -d '{
    "location": "Baltimore, MD",
    "max_price": 400000,
    "user_id": "test-user"
  }'

# Test risk analysis endpoint
curl -X POST https://your-domain.vercel.app/api/tools/analyze-risk \
  -H "Content-Type: application/json" \
  -d '{
    "property_id": "test-123",
    "address": "123 Main St, Baltimore, MD",
    "list_price": 400000,
    "user_id": "test-user"
  }'
```

## Step 4: Configure Webhook (Optional)

If using Docusign webhooks:

1. **In Docusign Developer Console**:
   - Go to your app settings
   - Add webhook URL: `https://your-domain.vercel.app/webhooks/docusign`
   - Enable events: "Envelope Sent", "Envelope Completed"

2. **Test Webhook**:
   ```bash
   curl -X POST https://your-domain.vercel.app/webhooks/docusign \
     -H "Content-Type: application/json" \
     -H "X-DocuSign-Signature: test" \
     -d '{"event": "envelope-completed"}'
   ```

## Step 5: Test End-to-End Voice Flow

### Test Scenario 1: Property Search

1. **Call your Vapi phone number**
2. **Say**: "Find me a house in Baltimore under $400,000"
3. **Expected Response**: 
   - Counter should acknowledge the request
   - Play filler phrase ("Let me check the records...")
   - Return 3 properties with addresses and prices
   - Provide 1-sentence summaries

**Verify**:
- Response time < 1 second
- Properties match criteria
- Voice is natural and clear

### Test Scenario 2: Risk Analysis

1. **Continue conversation**
2. **Say**: "Check for red flags on the first property"
3. **Expected Response**:
   - Counter should analyze the property
   - Report any risk flags (overpricing, flood, tax, crime)
   - Provide severity levels

**Verify**:
- Risk analysis completes quickly
- Flags are accurate
- Explanations are clear

### Test Scenario 3: Viewing Scheduler

1. **Continue conversation**
2. **Say**: "Schedule a viewing for tomorrow at 2pm"
3. **Expected Response**:
   - Counter should check calendar availability
   - Confirm time or suggest alternatives
   - Send email to listing agent
   - Create calendar event

**Verify**:
- Calendar check works
- Email is sent
- Confirmation is provided

### Test Scenario 4: Offer Generator

1. **Continue conversation**
2. **Say**: "Make an offer of $350,000, cash, 14 days to close"
3. **Expected Response**:
   - Counter should generate purchase agreement
   - Send Docusign envelope
   - Provide signing URL

**Verify**:
- Offer is generated correctly
- Docusign email received
- Signing URL works

## Step 6: Monitor Production Logs

### Vercel Logs

Monitor function execution in real-time:

```bash
# Follow logs
vercel logs --follow

# Filter by tool
vercel logs --filter="api/tools/search"

# Show last 100 lines
vercel logs -n 100
```

### Vapi Logs

1. Go to Vapi Dashboard → Logs
2. Filter by assistant
3. Review call transcripts
4. Check tool execution times

### Key Metrics to Monitor

- **Response Time**: Should be < 1000ms for 95% of requests
- **Error Rate**: Should be < 1%
- **Cache Hit Rate**: Should be > 50% for searches
- **Tool Success Rate**: Should be > 95%

## Step 7: Performance Testing

### Load Test

Test with multiple concurrent calls:

```bash
# Install artillery (if not installed)
npm install -g artillery

# Create test script
cat > load-test.yml << EOF
config:
  target: "https://your-domain.vercel.app"
  phases:
    - duration: 60
      arrivalRate: 5
scenarios:
  - name: "Property Search"
    flow:
      - post:
          url: "/api/tools/search"
          json:
            location: "Baltimore, MD"
            max_price: 400000
            user_id: "load-test-{{ \$randomNumber() }}"
EOF

# Run load test
artillery run load-test.yml
```

### Latency Test

Measure end-to-end latency:

```bash
# Test search endpoint
time curl -X POST https://your-domain.vercel.app/api/tools/search \
  -H "Content-Type: application/json" \
  -d '{"location":"Baltimore, MD","max_price":400000,"user_id":"test"}'
```

Target: < 500ms for cached results, < 1000ms for fresh queries

## Troubleshooting

### Tool Not Executing

**Symptoms**: Vapi doesn't call your tool, or returns error

**Solutions**:
1. Verify tool URL is correct (no typos)
2. Check endpoint is accessible: `curl https://your-domain.vercel.app/api/tools/search`
3. Review Vapi logs for error messages
4. Verify function parameters match expected schema

### Slow Response Times

**Symptoms**: Voice flow feels sluggish, long pauses

**Solutions**:
1. Check Vercel function execution time in dashboard
2. Review external API latency (RentCast, FEMA, etc.)
3. Verify caching is working (check Redis dashboard)
4. Consider increasing Vercel function memory

### Authentication Errors

**Symptoms**: 401 or 403 errors in logs

**Solutions**:
1. Verify all API keys are set in Vercel: `vercel env ls`
2. Check API keys haven't expired
3. Verify API key permissions are correct
4. Test API keys locally first

### Database Connection Issues

**Symptoms**: Database timeout or connection refused

**Solutions**:
1. Verify DATABASE_URL uses pooler (port 6543)
2. Check Supabase project is active
3. Review connection pool settings
4. Check for connection leaks in code

### Cache Not Working

**Symptoms**: Slow repeated queries, high API costs

**Solutions**:
1. Verify REDIS_URL is set correctly
2. Test Redis connection: `python scripts/verify_redis.py`
3. Check Redis dashboard for activity
4. Review cache TTL settings

## Production Checklist

Before going live:

- [ ] All tool URLs updated with production domain
- [ ] Each tool tested manually with curl
- [ ] End-to-end voice flow tested
- [ ] All 4 test scenarios passed
- [ ] Response times < 1 second
- [ ] Error monitoring configured
- [ ] Logs accessible and readable
- [ ] Performance metrics baseline established
- [ ] Rollback plan documented
- [ ] Support contacts saved

## Monitoring Dashboard

Set up a monitoring dashboard with these metrics:

### Vercel Metrics
- Function execution time (p50, p95, p99)
- Error rate
- Invocation count
- Bandwidth usage

### Vapi Metrics
- Call duration
- Tool execution count
- Error rate
- User satisfaction (if available)

### Database Metrics
- Connection pool usage
- Query latency
- Active connections
- Slow queries

### Cache Metrics
- Hit rate
- Miss rate
- Memory usage
- Eviction rate

## Rollback Procedure

If issues occur in production:

1. **Immediate Rollback**:
   ```bash
   vercel rollback [previous-deployment-url]
   ```

2. **Update Vapi** (if needed):
   - Revert tool URLs to previous deployment
   - Or temporarily disable problematic tools

3. **Investigate**:
   - Review logs: `vercel logs -n 500`
   - Check error tracking (Sentry)
   - Test locally with production data

4. **Fix and Redeploy**:
   - Fix issues in code
   - Test thoroughly
   - Deploy again: `vercel --prod`

## Support and Resources

### Documentation
- Vapi Docs: https://docs.vapi.ai
- Vercel Docs: https://vercel.com/docs
- Counter AI Deployment Guide: `docs/deployment_guide.md`

### Dashboards
- Vapi: https://dashboard.vapi.ai
- Vercel: https://vercel.com/dashboard
- Supabase: https://app.supabase.com
- Upstash: https://console.upstash.com

### Support
- Vapi Support: https://vapi.ai/support
- Vercel Support: https://vercel.com/support

---

## Quick Reference Commands

```bash
# Generate Vapi config
python scripts/update_vapi_config.py https://your-domain.vercel.app

# Test endpoint
curl -X POST https://your-domain.vercel.app/api/tools/search \
  -H "Content-Type: application/json" \
  -d '{"location":"Baltimore, MD","max_price":400000,"user_id":"test"}'

# View logs
vercel logs --follow

# Check environment variables
vercel env ls

# Rollback deployment
vercel rollback [deployment-url]
```

---

**Last Updated**: November 2025
