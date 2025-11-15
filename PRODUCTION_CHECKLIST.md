# Production Deployment Checklist

Use this checklist to ensure all deployment steps are completed correctly.

## Pre-Deployment

### 12.1 Vercel Configuration
- [ ] Vercel CLI installed (`npm install -g vercel`)
- [ ] Logged in to Vercel (`vercel login`)
- [ ] Project linked (`vercel link`)
- [ ] `vercel.json` configured with Python 3.11 runtime
- [ ] Function timeout set to 10 seconds
- [ ] Memory allocation set to 1024MB

### 12.2 Production Database (Supabase)
- [ ] Supabase account created
- [ ] New project created: `counter-ai-production`
- [ ] Database password saved securely
- [ ] Connection pooling URL copied (port 6543)
- [ ] Database migrations run (`alembic upgrade head`)
- [ ] Tables verified in Supabase dashboard:
  - [ ] `users`
  - [ ] `search_history`
  - [ ] `risk_analyses`
  - [ ] `viewings`
  - [ ] `offers`
- [ ] Indexes created and verified
- [ ] Connection pooling tested

### 12.3 Redis Cache
- [ ] Redis provider chosen (Upstash or Redis Cloud)
- [ ] Redis instance created
- [ ] Connection URL obtained
- [ ] Cache connectivity tested locally
- [ ] TTL settings verified

### 12.4 API Keys and Secrets

#### Required API Keys
- [ ] **RentCast API Key**
  - Source: https://developers.rentcast.io/
  - Added to Vercel: `vercel env add RENTCAST_API_KEY production`

- [ ] **Docusign Integration**
  - [ ] Integration Key
  - [ ] Secret Key
  - [ ] Account ID
  - [ ] Webhook Secret
  - Source: https://developers.docusign.com/
  - Added to Vercel

- [ ] **Apify API Token**
  - Source: https://console.apify.com/account/integrations
  - Added to Vercel: `vercel env add APIFY_API_TOKEN production`

- [ ] **Google Calendar OAuth**
  - [ ] Client ID
  - [ ] Client Secret
  - Source: https://console.cloud.google.com/apis/credentials
  - Added to Vercel

- [ ] **Encryption Key**
  - Generated with: `python scripts/generate_encryption_key.py`
  - Stored securely in password manager
  - Added to Vercel: `vercel env add ENCRYPTION_KEY production`

- [ ] **OpenAI API Key**
  - Source: https://platform.openai.com/api-keys
  - Added to Vercel: `vercel env add OPENAI_API_KEY production`

- [ ] **SendGrid API Key**
  - Source: https://app.sendgrid.com/settings/api_keys
  - Added to Vercel: `vercel env add SENDGRID_API_KEY production`

#### Optional API Keys
- [ ] **CrimeoMeter API Key** (optional)
  - Source: https://www.crimeometer.com/
  - Added to Vercel: `vercel env add CRIMEOMETER_API_KEY production`

- [ ] **FEMA API Key** (optional, public API)
  - Source: https://www.fema.gov/about/openfema/api
  - Added to Vercel: `vercel env add FEMA_API_KEY production`

#### Database & Cache URLs
- [ ] **DATABASE_URL**
  - Supabase connection pooling URL
  - Format: `postgresql://postgres.[ref]:[password]@[region].pooler.supabase.com:6543/postgres`
  - Added to Vercel: `vercel env add DATABASE_URL production`

- [ ] **REDIS_URL**
  - Upstash or Redis Cloud URL
  - Added to Vercel: `vercel env add REDIS_URL production`

#### Verify All Environment Variables
- [ ] Run `vercel env ls` to verify all variables are set
- [ ] Confirm variables are set for "production" environment

## Deployment

### Deploy to Production
- [ ] Run deployment script: `./scripts/deploy.sh`
  - OR manually: `vercel --prod`
- [ ] Deployment successful (no errors)
- [ ] Production URL obtained
- [ ] Health endpoint tested: `curl https://your-domain.vercel.app/api/health`

### 12.5 Update Vapi Assistant

- [ ] Login to Vapi Dashboard: https://dashboard.vapi.ai
- [ ] Navigate to Counter AI assistant
- [ ] Update tool URLs with production domain:
  - [ ] `search_properties`: `https://your-domain.vercel.app/api/tools/search`
  - [ ] `analyze_risk`: `https://your-domain.vercel.app/api/tools/analyze-risk`
  - [ ] `schedule_viewing`: `https://your-domain.vercel.app/api/tools/schedule`
  - [ ] `draft_offer`: `https://your-domain.vercel.app/api/tools/draft-offer`
- [ ] Save assistant configuration
- [ ] Verify Twilio phone number is connected

## Post-Deployment Testing

### API Endpoint Tests
- [ ] Test search endpoint:
  ```bash
  curl -X POST https://your-domain.vercel.app/api/tools/search \
    -H "Content-Type: application/json" \
    -d '{"location":"Baltimore, MD","max_price":400000,"user_id":"test"}'
  ```

- [ ] Test risk analysis endpoint:
  ```bash
  curl -X POST https://your-domain.vercel.app/api/tools/analyze-risk \
    -H "Content-Type: application/json" \
    -d '{"property_id":"test","address":"123 Main St","list_price":400000,"user_id":"test"}'
  ```

- [ ] Verify responses are returned within 1 second
- [ ] Check Vercel logs for errors: `vercel logs --follow`

### Voice Flow Tests
- [ ] Call Vapi phone number
- [ ] Test property search: "Find me a house in Baltimore under $400k"
- [ ] Test risk analysis: "Check for red flags"
- [ ] Test viewing scheduler: "Schedule a viewing for tomorrow at 2pm"
- [ ] Test offer generator: "Make an offer of $350k"
- [ ] Verify all tools execute successfully
- [ ] Confirm responses are natural and timely

### Database Tests
- [ ] Verify user records are created
- [ ] Check search history is saved
- [ ] Confirm risk analyses are stored
- [ ] Validate viewing requests are logged
- [ ] Test offer records are created

### Cache Tests
- [ ] Verify cache hits in logs
- [ ] Check Redis dashboard for activity
- [ ] Confirm TTL settings are working
- [ ] Test cache invalidation

## Monitoring Setup

### Vercel Dashboard
- [ ] Access Vercel dashboard: https://vercel.com/dashboard
- [ ] Review function execution times
- [ ] Check error rates
- [ ] Monitor bandwidth usage
- [ ] Set up alerts for errors

### Database Monitoring
- [ ] Access Supabase dashboard
- [ ] Review connection pool usage
- [ ] Check query performance
- [ ] Monitor storage usage
- [ ] Set up alerts for high load

### Cache Monitoring
- [ ] Access Redis dashboard (Upstash/Redis Cloud)
- [ ] Review cache hit rate
- [ ] Check memory usage
- [ ] Monitor request count
- [ ] Set up alerts for high memory

### Error Tracking (Optional)
- [ ] Sentry configured (if using)
- [ ] Error sampling set up
- [ ] Custom context added
- [ ] Alerts configured

## Security Verification

- [ ] All secrets stored in Vercel environment variables (not in code)
- [ ] No API keys committed to git
- [ ] PII encryption working (test with user creation)
- [ ] Rate limiting active (test with multiple requests)
- [ ] HTTPS enforced on all endpoints
- [ ] Docusign webhook signature validation working
- [ ] Database connection uses TLS
- [ ] Redis connection uses TLS (if applicable)

## Documentation

- [ ] Production URL documented
- [ ] Environment variables documented
- [ ] Deployment process documented
- [ ] Rollback procedure documented
- [ ] Monitoring dashboards bookmarked
- [ ] Support contacts saved
- [ ] Incident response plan created

## Rollback Plan

In case of issues:
- [ ] Previous deployment URL saved
- [ ] Rollback command ready: `vercel rollback [deployment-url]`
- [ ] Database backup created
- [ ] Environment variables backed up
- [ ] Vapi configuration backed up

## Cost Monitoring

- [ ] Vercel usage reviewed
- [ ] Supabase usage reviewed
- [ ] Redis usage reviewed
- [ ] External API usage reviewed
- [ ] Billing alerts set up
- [ ] Budget limits configured

## Final Sign-Off

- [ ] All checklist items completed
- [ ] Production deployment successful
- [ ] End-to-end tests passed
- [ ] Monitoring active
- [ ] Team notified of deployment
- [ ] Documentation updated
- [ ] Deployment date recorded: _______________
- [ ] Deployed by: _______________

---

## Quick Reference

### Useful Commands

```bash
# Deploy to production
vercel --prod

# View logs
vercel logs --follow

# List deployments
vercel ls

# Rollback
vercel rollback [deployment-url]

# Check environment variables
vercel env ls

# Pull environment variables locally
vercel env pull .env.local

# Run database migrations
alembic upgrade head

# Generate encryption key
python scripts/generate_encryption_key.py

# Test Redis connection
python -c "from services.cache_client import CacheClient; c=CacheClient(); c.set('test','ok'); print(c.get('test'))"
```

### Important URLs

- Vercel Dashboard: https://vercel.com/dashboard
- Supabase Dashboard: https://app.supabase.com
- Vapi Dashboard: https://dashboard.vapi.ai
- Upstash Console: https://console.upstash.com
- Docusign Developer: https://developers.docusign.com

### Support Contacts

- Vercel Support: https://vercel.com/support
- Supabase Support: https://supabase.com/support
- Vapi Support: https://vapi.ai/support

---

**Last Updated**: [Date]
**Next Review**: [Date + 30 days]
