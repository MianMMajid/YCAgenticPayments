# API Keys and Secrets Reference

This document provides detailed information about all required API keys and how to obtain them.

## Required API Keys

### 1. Database (Supabase)

**Variable**: `DATABASE_URL`

**Purpose**: PostgreSQL database connection with connection pooling

**How to get**:
1. Sign up at https://supabase.com
2. Create a new project
3. Go to Settings → Database
4. Copy the "Connection Pooling" URL (port 6543)
5. Format: `postgresql://postgres.[ref]:[password]@[region].pooler.supabase.com:6543/postgres`

**Cost**: Free tier available (500MB database)

---

### 2. Redis Cache

**Variable**: `REDIS_URL`

**Purpose**: Caching for property searches, agent info, and risk analyses

**Option A - Upstash (Recommended)**:
1. Sign up at https://upstash.com
2. Create a new Redis database
3. Choose "Regional" type
4. Enable TLS
5. Copy the REST URL
6. Format: `https://[endpoint].upstash.io`

**Option B - Redis Cloud**:
1. Sign up at https://redis.com/cloud
2. Create a new database
3. Copy the connection URL
4. Format: `redis://default:[password]@[endpoint]:6379`

**Cost**: 
- Upstash: Free tier (10,000 commands/day)
- Redis Cloud: Free tier (30MB storage)

---

### 3. RentCast API

**Variable**: `RENTCAST_API_KEY`

**Purpose**: Property listings, estimated values, tax assessments

**How to get**:
1. Sign up at https://developers.rentcast.io/
2. Go to API Keys section
3. Create a new API key
4. Copy the key

**API Endpoints Used**:
- `/listings/sale` - Search for properties
- `/properties/{id}` - Get property details
- `/avm/value` - Get estimated value

**Cost**: 
- Free tier: 500 requests/month
- Paid plans start at $49/month

**Rate Limits**: 
- Free: 10 requests/minute
- Paid: 60 requests/minute

---

### 4. Docusign

**Variables**: 
- `DOCUSIGN_INTEGRATION_KEY`
- `DOCUSIGN_SECRET_KEY`
- `DOCUSIGN_ACCOUNT_ID`
- `DOCUSIGN_WEBHOOK_SECRET`

**Purpose**: Generate and e-sign purchase agreements

**How to get**:
1. Sign up at https://developers.docusign.com/
2. Create a new app in the Developer Console
3. Note the Integration Key (Client ID)
4. Generate a Secret Key (Client Secret)
5. Get your Account ID from Settings
6. Generate webhook secret: `openssl rand -hex 32`

**Setup Steps**:
1. Create purchase agreement templates for each state
2. Add text tabs and checkbox tabs for dynamic fields
3. Configure webhook URL: `https://your-domain.vercel.app/webhooks/docusign`
4. Enable "Envelope Sent" and "Envelope Completed" events

**Cost**: 
- Developer sandbox: Free
- Production: Pay per envelope (starts at $0.50/envelope)

---

### 5. Apify

**Variable**: `APIFY_API_TOKEN`

**Purpose**: Scrape Zillow for listing agent contact information

**How to get**:
1. Sign up at https://apify.com
2. Go to Settings → Integrations
3. Create a new API token
4. Copy the token

**Actor Used**: `zillow-agent-scraper`

**Cost**: 
- Free tier: $5 credit/month
- Paid plans start at $49/month

**Usage**: ~$0.01 per agent lookup

---

### 6. Google Calendar

**Variables**:
- `GOOGLE_CALENDAR_CLIENT_ID`
- `GOOGLE_CALENDAR_CLIENT_SECRET`

**Purpose**: Check availability and create viewing appointments

**How to get**:
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable Google Calendar API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Application type: Web application
6. Add authorized redirect URI: `https://your-domain.vercel.app/auth/google/callback`
7. Copy Client ID and Client Secret

**Scopes Required**:
- `https://www.googleapis.com/auth/calendar`
- `https://www.googleapis.com/auth/calendar.events`

**Cost**: Free (no quota limits for Calendar API)

---

### 7. Encryption Key

**Variable**: `ENCRYPTION_KEY`

**Purpose**: Encrypt PII fields (phone numbers, emails) in database

**How to generate**:
```bash
python scripts/generate_encryption_key.py
```

Or manually:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Important**:
- Store this key securely in a password manager
- Never commit to git
- If lost, encrypted data cannot be recovered
- Rotate every 90 days

**Format**: Base64-encoded 32-byte key (e.g., `gAAAAABh...`)

---

### 8. OpenAI

**Variable**: `OPENAI_API_KEY`

**Purpose**: Generate property summaries using GPT-4o-mini

**How to get**:
1. Sign up at https://platform.openai.com/
2. Go to API Keys
3. Create a new secret key
4. Copy the key (starts with `sk-`)

**Model Used**: `gpt-4o-mini` (fast and cost-effective)

**Cost**: 
- ~$0.0001 per property summary
- $5 free credit for new accounts

---

### 9. SendGrid

**Variable**: `SENDGRID_API_KEY`

**Purpose**: Send emails to listing agents for viewing requests

**How to get**:
1. Sign up at https://sendgrid.com
2. Go to Settings → API Keys
3. Create a new API key
4. Choose "Full Access" or "Mail Send" permission
5. Copy the key (starts with `SG.`)

**Setup**:
1. Verify sender email address
2. Configure sender identity
3. Set up email templates (optional)

**Cost**: 
- Free tier: 100 emails/day
- Paid plans start at $15/month (40,000 emails)

---

## Optional API Keys

### 10. CrimeoMeter

**Variable**: `CRIMEOMETER_API_KEY`

**Purpose**: Crime statistics for risk analysis

**How to get**:
1. Sign up at https://www.crimeometer.com/
2. Request API access
3. Copy the API key

**Cost**: Contact for pricing

**Note**: If not configured, crime risk analysis will be skipped

---

### 11. FEMA

**Variable**: `FEMA_API_KEY`

**Purpose**: Flood zone data (public API, key optional)

**How to get**:
1. Go to https://www.fema.gov/about/openfema/api
2. Register for an API key (optional)
3. Copy the key

**Cost**: Free

**Note**: API works without key but has lower rate limits

---

## Environment Variable Summary

### Required (11 variables)
```bash
DATABASE_URL                    # Supabase PostgreSQL
REDIS_URL                       # Upstash or Redis Cloud
RENTCAST_API_KEY               # Property data
DOCUSIGN_INTEGRATION_KEY       # Contract generation
DOCUSIGN_SECRET_KEY            # Contract generation
DOCUSIGN_ACCOUNT_ID            # Contract generation
DOCUSIGN_WEBHOOK_SECRET        # Webhook validation
APIFY_API_TOKEN                # Agent scraping
GOOGLE_CALENDAR_CLIENT_ID      # Calendar integration
GOOGLE_CALENDAR_CLIENT_SECRET  # Calendar integration
ENCRYPTION_KEY                 # PII encryption
OPENAI_API_KEY                 # Property summaries
SENDGRID_API_KEY               # Email sending
```

### Optional (2 variables)
```bash
CRIMEOMETER_API_KEY            # Crime statistics
FEMA_API_KEY                   # Flood zone data
```

---

## Adding to Vercel

### Using CLI (Recommended)
```bash
# Add single variable
vercel env add VARIABLE_NAME production

# Or use the configuration script
./scripts/configure_secrets.sh
```

### Using Dashboard
1. Go to https://vercel.com/dashboard
2. Select your project
3. Go to Settings → Environment Variables
4. Add each variable for "Production" environment

---

## Security Best Practices

1. **Never commit secrets to git**
   - Use `.env.example` for templates only
   - Add `.env` to `.gitignore`

2. **Rotate keys regularly**
   - API keys: Every 90 days
   - Encryption key: Every 90 days
   - Webhook secrets: Every 180 days

3. **Use least privilege**
   - Only grant necessary permissions
   - Use read-only keys where possible

4. **Monitor usage**
   - Set up billing alerts
   - Track API usage
   - Review access logs

5. **Store securely**
   - Use password manager for encryption key
   - Use Vercel secrets for all production keys
   - Never share keys via email or chat

---

## Troubleshooting

### Invalid API Key
- Verify key is copied correctly (no extra spaces)
- Check key hasn't expired
- Verify key has correct permissions

### Rate Limit Errors
- Check API usage in provider dashboard
- Upgrade to paid tier if needed
- Implement caching to reduce calls

### Connection Errors
- Verify URL format is correct
- Check firewall/network settings
- Test connection locally first

### Missing Environment Variable
- Run `vercel env ls` to check configured variables
- Redeploy after adding new variables
- Check variable is set for "production" environment

---

## Cost Estimation

### Free Tier (Development)
- Supabase: Free
- Upstash: Free (10k commands/day)
- RentCast: Free (500 requests/month)
- Docusign: Free (sandbox)
- Apify: $5 credit/month
- Google Calendar: Free
- OpenAI: $5 credit (new accounts)
- SendGrid: Free (100 emails/day)

**Total**: ~$0-10/month

### Production (Moderate Usage)
- Supabase Pro: $25/month
- Upstash: $10/month
- RentCast: $49/month
- Docusign: ~$50/month (100 envelopes)
- Apify: $49/month
- Google Calendar: Free
- OpenAI: ~$5/month
- SendGrid: $15/month

**Total**: ~$200-250/month

---

## Support Contacts

- **RentCast**: support@rentcast.io
- **Docusign**: https://support.docusign.com/
- **Apify**: support@apify.com
- **Supabase**: https://supabase.com/support
- **Upstash**: support@upstash.com
- **SendGrid**: https://support.sendgrid.com/

---

**Last Updated**: November 2025
