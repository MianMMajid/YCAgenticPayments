# Counter AI - Production Deployment Guide

This guide covers the complete production deployment process for the Counter AI Real Estate Broker system.

## Prerequisites

- Vercel account with CLI installed (`npm i -g vercel`)
- Supabase account
- Upstash or Redis Cloud account
- All required API keys (RentCast, Docusign, Apify, etc.)

## 12.1 Configure Vercel Deployment

### Vercel Configuration

The `vercel.json` file is already configured with:
- Python 3.11 runtime
- 10-second function timeout
- 1024MB memory allocation
- Environment variable placeholders

### Deploy to Vercel

1. **Install Vercel CLI** (if not already installed):
```bash
npm install -g vercel
```

2. **Login to Vercel**:
```bash
vercel login
```

3. **Link your project**:
```bash
vercel link
```

4. **Deploy to production**:
```bash
vercel --prod
```

### Verify Deployment

After deployment, Vercel will provide a production URL (e.g., `https://counter-ai.vercel.app`).

Test the health endpoint:
```bash
curl https://your-domain.vercel.app/api/health
```

## 12.2 Set Up Production Database

### Create Supabase PostgreSQL Instance

1. **Sign up/Login to Supabase**: https://supabase.com

2. **Create a new project**:
   - Project name: `counter-ai-production`
   - Database password: Generate a strong password (save it securely)
   - Region: Choose closest to your users (e.g., `us-east-1`)

3. **Get connection strings**:
   - Go to Project Settings → Database
   - Copy the **Connection Pooling** URL (uses Supavisor)
   - Format: `postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`

### Configure Connection Pooling

Supabase uses Supavisor for connection pooling automatically. The pooler URL (port 6543) provides:
- Transaction mode pooling
- Up to 15 connections per client
- Automatic connection management

### Run Database Migrations

1. **Set the DATABASE_URL locally** (for migration):
```bash
export DATABASE_URL="postgresql://postgres.[project-ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres"
```

2. **Run Alembic migrations**:
```bash
alembic upgrade head
```

3. **Verify tables were created**:
   - Go to Supabase Dashboard → Table Editor
   - Confirm tables: `users`, `search_history`, `risk_analyses`, `viewings`, `offers`

### Database Indexes

The migration script (`alembic/versions/001_initial_schema.py`) already creates these indexes:
- `ix_search_history_user_id_created_at` (composite)
- `ix_risk_analyses_property_id`
- `ix_viewings_user_id_requested_time` (composite)
- `ix_offers_user_id_created_at` (composite)

## 12.3 Set Up Redis Cache

### Option A: Upstash Redis (Recommended for Vercel)

1. **Sign up at Upstash**: https://upstash.com

2. **Create a new Redis database**:
   - Name: `counter-ai-cache`
   - Type: Regional
   - Region: Same as your Vercel deployment
   - TLS: Enabled

3. **Get connection URL**:
   - Copy the `UPSTASH_REDIS_REST_URL` from the dashboard
   - Format: `https://[endpoint].upstash.io`

4. **Get REST token**:
   - Copy the `UPSTASH_REDIS_REST_TOKEN`

### Option B: Redis Cloud

1. **Sign up at Redis Cloud**: https://redis.com/cloud

2. **Create a new database**:
   - Name: `counter-ai-cache`
   - Cloud: AWS
   - Region: Same as your deployment
   - Memory: 30MB (free tier)

3. **Get connection URL**:
   - Format: `redis://default:[password]@[endpoint]:6379`

### Test Cache Connectivity

Create a test script:

```python
# test_redis.py
import os
from services.cache_client import CacheClient

cache = CacheClient()
cache.set("test_key", "test_value", ttl=60)
value = cache.get("test_key")
print(f"Cache test: {value}")  # Should print "test_value"
```

Run:
```bash
python test_redis.py
```

## 12.4 Configure API Keys and Secrets

### Add Secrets to Vercel

Use the Vercel CLI to add environment variables:

```bash
# Database
vercel env add DATABASE_URL production
# Paste your Supabase connection pooling URL

# Redis
vercel env add REDIS_URL production
# Paste your Upstash or Redis Cloud URL

# RentCast API
vercel env add RENTCAST_API_KEY production
# Get from: https://developers.rentcast.io/

# Docusign
vercel env add DOCUSIGN_INTEGRATION_KEY production
vercel env add DOCUSIGN_SECRET_KEY production
vercel env add DOCUSIGN_ACCOUNT_ID production
vercel env add DOCUSIGN_WEBHOOK_SECRET production
# Get from: https://developers.docusign.com/

# Apify
vercel env add APIFY_API_TOKEN production
# Get from: https://console.apify.com/account/integrations

# Google Calendar OAuth
vercel env add GOOGLE_CALENDAR_CLIENT_ID production
vercel env add GOOGLE_CALENDAR_CLIENT_SECRET production
# Get from: https://console.cloud.google.com/apis/credentials

# Encryption Key (for PII)
vercel env add ENCRYPTION_KEY production
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# OpenAI (for property summaries)
vercel env add OPENAI_API_KEY production
# Get from: https://platform.openai.com/api-keys

# SendGrid (for emails)
vercel env add SENDGRID_API_KEY production
# Get from: https://app.sendgrid.com/settings/api_keys

# CrimeoMeter (optional)
vercel env add CRIMEOMETER_API_KEY production
# Get from: https://www.crimeometer.com/
```

### Generate Encryption Key

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Save this key securely - you'll need it to decrypt PII data.

### Verify Environment Variables

```bash
vercel env ls
```

## 12.5 Update Vapi Assistant with Production URLs

### Get Your Production Domain

After deploying to Vercel, you'll have a domain like:
- `https://counter-ai.vercel.app` (auto-generated)
- Or your custom domain if configured

### Update Vapi Tool URLs

1. **Login to Vapi Dashboard**: https://dashboard.vapi.ai

2. **Navigate to your Assistant**:
   - Go to Assistants → Counter AI

3. **Update Tool Function URLs**:

Edit each tool's `url` field:

```json
{
  "functions": [
    {
      "name": "search_properties",
      "url": "https://your-domain.vercel.app/api/tools/search",
      "description": "Search for homes matching criteria",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string"},
          "max_price": {"type": "integer"},
          "min_beds": {"type": "integer"},
          "min_baths": {"type": "number"},
          "user_id": {"type": "string"}
        },
        "required": ["location", "max_price", "user_id"]
      }
    },
    {
      "name": "analyze_risk",
      "url": "https://your-domain.vercel.app/api/tools/analyze-risk",
      "description": "Check property for red flags",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {"type": "string"},
          "address": {"type": "string"},
          "list_price": {"type": "integer"},
          "user_id": {"type": "string"}
        },
        "required": ["property_id", "address", "list_price", "user_id"]
      }
    },
    {
      "name": "schedule_viewing",
      "url": "https://your-domain.vercel.app/api/tools/schedule",
      "description": "Book a property showing",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {"type": "string"},
          "listing_url": {"type": "string"},
          "requested_time": {"type": "string"},
          "user_id": {"type": "string"},
          "user_name": {"type": "string"},
          "user_email": {"type": "string"}
        },
        "required": ["property_id", "listing_url", "requested_time", "user_id", "user_name", "user_email"]
      }
    },
    {
      "name": "draft_offer",
      "url": "https://your-domain.vercel.app/api/tools/draft-offer",
      "description": "Create purchase agreement",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {"type": "string"},
          "address": {"type": "string"},
          "offer_price": {"type": "integer"},
          "closing_days": {"type": "integer"},
          "financing_type": {"type": "string"},
          "contingencies": {"type": "array", "items": {"type": "string"}},
          "user_id": {"type": "string"},
          "user_email": {"type": "string"}
        },
        "required": ["property_id", "address", "offer_price", "closing_days", "financing_type", "user_id", "user_email"]
      }
    }
  ]
}
```

4. **Save the Assistant configuration**

### Test End-to-End Voice Flow

1. **Call your Vapi phone number** (configured in Twilio integration)

2. **Test each tool**:
   - "Find me a house in Baltimore under $400k" → Should trigger `search_properties`
   - "Check for red flags on 123 Main Street" → Should trigger `analyze_risk`
   - "Schedule a viewing for tomorrow at 2pm" → Should trigger `schedule_viewing`
   - "Make an offer of $350k" → Should trigger `draft_offer`

3. **Monitor Vercel logs**:
```bash
vercel logs --follow
```

4. **Check for errors**:
   - Verify tool responses are returned within 1 second
   - Confirm database writes are successful
   - Check cache hit rates

## Post-Deployment Checklist

- [ ] Vercel deployment successful
- [ ] Production URL accessible
- [ ] Database migrations completed
- [ ] All tables and indexes created
- [ ] Redis cache connected and tested
- [ ] All environment variables configured
- [ ] Vapi assistant updated with production URLs
- [ ] End-to-end voice test successful
- [ ] Error monitoring configured (Sentry)
- [ ] Rate limiting active
- [ ] Logs accessible via `vercel logs`

## Monitoring and Maintenance

### View Logs

```bash
# Real-time logs
vercel logs --follow

# Last 100 lines
vercel logs -n 100

# Filter by function
vercel logs --filter="api/tools/search"
```

### Monitor Performance

- **Vercel Dashboard**: https://vercel.com/dashboard
  - Function execution time
  - Error rates
  - Bandwidth usage

- **Supabase Dashboard**: https://app.supabase.com
  - Database connections
  - Query performance
  - Storage usage

- **Upstash Dashboard**: https://console.upstash.com
  - Cache hit rate
  - Memory usage
  - Request count

### Rollback Deployment

If issues occur:

```bash
# List deployments
vercel ls

# Rollback to previous deployment
vercel rollback [deployment-url]
```

## Troubleshooting

### Database Connection Issues

**Error**: `connection refused` or `timeout`

**Solution**:
- Verify DATABASE_URL uses the pooler endpoint (port 6543)
- Check Supabase project is not paused
- Verify IP allowlist in Supabase (should allow all for pooler)

### Redis Connection Issues

**Error**: `ECONNREFUSED` or `authentication failed`

**Solution**:
- Verify REDIS_URL format is correct
- Check TLS is enabled for Upstash
- Test connection locally first

### Tool Execution Timeout

**Error**: `Function execution timed out`

**Solution**:
- Verify `maxDuration: 10` in vercel.json
- Check external API response times
- Add more aggressive caching

### Environment Variables Not Loading

**Error**: `KeyError: 'RENTCAST_API_KEY'`

**Solution**:
```bash
# Verify env vars are set
vercel env ls

# Pull env vars locally for testing
vercel env pull .env.local
```

## Security Best Practices

1. **Never commit secrets** to git
2. **Rotate API keys** every 90 days
3. **Use Vercel secrets** for all sensitive data
4. **Enable Vercel authentication** for preview deployments
5. **Monitor Sentry** for security-related errors
6. **Review Supabase logs** for suspicious database activity

## Cost Estimates

### Free Tier Limits

- **Vercel**: 100GB bandwidth, 100 hours execution time
- **Supabase**: 500MB database, 2GB bandwidth
- **Upstash**: 10,000 commands/day
- **RentCast**: 500 requests/month (check current pricing)

### Estimated Monthly Costs (Production)

- Vercel Pro: $20/month (if exceeding free tier)
- Supabase Pro: $25/month (for production workloads)
- Upstash: $0-10/month (pay-as-you-go)
- External APIs: $50-200/month (varies by usage)

**Total**: ~$100-250/month for moderate usage

## Support

For deployment issues:
- Vercel: https://vercel.com/support
- Supabase: https://supabase.com/support
- Upstash: https://upstash.com/docs

For application issues:
- Check logs: `vercel logs`
- Review error tracking in Sentry
- Test endpoints with curl or Postman
