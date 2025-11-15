# Counter AI - Deployment Summary

This document provides a quick overview of the deployment process and all available resources.

## 🚀 Quick Start Deployment

### 1. Prerequisites
- [ ] Vercel account and CLI installed
- [ ] Supabase account (PostgreSQL database)
- [ ] Upstash or Redis Cloud account
- [ ] All required API keys (see API Keys Reference)

### 2. One-Command Deployment

```bash
# Run the automated deployment script
./scripts/deploy.sh
```

This script will guide you through:
- Verifying environment variables
- Confirming database migrations
- Checking Redis setup
- Deploying to Vercel
- Testing the deployment

### 3. Manual Deployment Steps

If you prefer manual deployment:

```bash
# 1. Generate encryption key
python scripts/generate_encryption_key.py

# 2. Configure secrets
./scripts/configure_secrets.sh

# 3. Set up database
export DATABASE_URL='your-supabase-url'
./scripts/setup_database.sh

# 4. Set up Redis
export REDIS_URL='your-redis-url'
./scripts/setup_redis.sh

# 5. Deploy to Vercel
vercel --prod

# 6. Update Vapi configuration
python scripts/update_vapi_config.py https://your-domain.vercel.app

# 7. Test production
./scripts/test_production.sh https://your-domain.vercel.app
```

## 📚 Documentation

### Core Guides
- **[Deployment Guide](docs/deployment_guide.md)** - Complete deployment walkthrough
- **[Production Checklist](PRODUCTION_CHECKLIST.md)** - Step-by-step checklist
- **[API Keys Reference](docs/api_keys_reference.md)** - How to obtain all API keys
- **[Vapi Production Setup](docs/vapi_production_setup.md)** - Voice interface configuration

### Technical Documentation
- **[Database Setup](docs/database_setup.md)** - Database schema and migrations
- **[Error Handling](docs/error_handling_monitoring.md)** - Error handling and monitoring
- **[Vapi Setup Guide](docs/vapi_setup_guide.md)** - Voice interface setup

## 🛠️ Deployment Scripts

All scripts are located in the `scripts/` directory:

| Script | Purpose |
|--------|---------|
| `deploy.sh` | Automated deployment workflow |
| `configure_secrets.sh` | Configure all environment variables |
| `setup_database.sh` | Set up and migrate database |
| `setup_redis.sh` | Set up Redis cache |
| `generate_encryption_key.py` | Generate PII encryption key |
| `update_vapi_config.py` | Generate Vapi configuration |
| `test_production.sh` | Test all production endpoints |
| `verify_database.py` | Verify database setup |
| `verify_redis.py` | Verify Redis connection |

## 🔧 Configuration Files

| File | Purpose |
|------|---------|
| `vercel.json` | Vercel deployment configuration |
| `.env.example` | Environment variables template |
| `alembic.ini` | Database migration configuration |
| `vapi_complete_config.json` | Complete Vapi assistant config |
| `vapi_tools_config.json` | Vapi tool definitions |

## 📋 Deployment Checklist

### Phase 1: Pre-Deployment
- [ ] Vercel CLI installed and logged in
- [ ] Supabase project created
- [ ] Redis instance created
- [ ] All API keys obtained
- [ ] Encryption key generated

### Phase 2: Configuration
- [ ] DATABASE_URL configured in Vercel
- [ ] REDIS_URL configured in Vercel
- [ ] All API keys added to Vercel
- [ ] Environment variables verified

### Phase 3: Database Setup
- [ ] Database migrations run
- [ ] Tables created and verified
- [ ] Indexes created
- [ ] Connection pooling tested

### Phase 4: Deployment
- [ ] Code deployed to Vercel
- [ ] Health endpoint accessible
- [ ] All tool endpoints tested
- [ ] Response times verified

### Phase 5: Vapi Configuration
- [ ] Tool URLs updated with production domain
- [ ] Vapi assistant configuration saved
- [ ] Twilio phone number connected
- [ ] End-to-end voice flow tested

### Phase 6: Monitoring
- [ ] Vercel logs accessible
- [ ] Error tracking configured
- [ ] Performance metrics baseline established
- [ ] Alerts configured

## 🧪 Testing

### Automated Testing

```bash
# Test all production endpoints
./scripts/test_production.sh https://your-domain.vercel.app

# Verify database
export DATABASE_URL='your-supabase-url'
python scripts/verify_database.py

# Verify Redis
export REDIS_URL='your-redis-url'
python scripts/verify_redis.py
```

### Manual Testing

```bash
# Test health endpoint
curl https://your-domain.vercel.app/api/health

# Test property search
curl -X POST https://your-domain.vercel.app/api/tools/search \
  -H "Content-Type: application/json" \
  -d '{"location":"Baltimore, MD","max_price":400000,"user_id":"test"}'
```

### Voice Flow Testing

1. Call your Vapi phone number
2. Test each scenario:
   - Property search
   - Risk analysis
   - Viewing scheduler
   - Offer generator

## 📊 Monitoring

### Dashboards
- **Vercel**: https://vercel.com/dashboard
- **Supabase**: https://app.supabase.com
- **Upstash**: https://console.upstash.com
- **Vapi**: https://dashboard.vapi.ai

### Key Metrics
- Response time: < 1 second (p95)
- Error rate: < 1%
- Cache hit rate: > 50%
- Database connections: < 80% of pool

### Logs

```bash
# Real-time logs
vercel logs --follow

# Last 100 lines
vercel logs -n 100

# Filter by function
vercel logs --filter="api/tools/search"
```

## 🔐 Security

### Best Practices
- ✅ All secrets stored in Vercel environment variables
- ✅ PII encrypted in database
- ✅ API keys rotated every 90 days
- ✅ Rate limiting enabled
- ✅ HTTPS enforced
- ✅ Webhook signatures validated

### Security Checklist
- [ ] No secrets committed to git
- [ ] Encryption key stored in password manager
- [ ] API keys have minimum required permissions
- [ ] Database uses connection pooling
- [ ] Redis uses TLS (if applicable)
- [ ] Error messages don't expose sensitive data

## 💰 Cost Estimation

### Free Tier (Development)
- Vercel: Free
- Supabase: Free (500MB)
- Upstash: Free (10k commands/day)
- RentCast: Free (500 requests/month)
- Total: **$0-10/month**

### Production (Moderate Usage)
- Vercel Pro: $20/month
- Supabase Pro: $25/month
- Upstash: $10/month
- RentCast: $49/month
- Docusign: $50/month
- Apify: $49/month
- SendGrid: $15/month
- OpenAI: $5/month
- Total: **~$200-250/month**

## 🆘 Troubleshooting

### Common Issues

**Deployment fails**
- Check Vercel logs: `vercel logs -n 100`
- Verify all environment variables are set
- Check for syntax errors in code

**Database connection errors**
- Verify DATABASE_URL uses pooler (port 6543)
- Check Supabase project is active
- Test connection locally first

**Redis connection errors**
- Verify REDIS_URL format is correct
- Check TLS is enabled (for Upstash)
- Test with `python scripts/verify_redis.py`

**Slow response times**
- Check external API latency
- Verify caching is working
- Review Vercel function execution time

**Tool not executing in Vapi**
- Verify tool URLs are correct
- Check endpoint is accessible with curl
- Review Vapi logs for errors

### Rollback Procedure

```bash
# List deployments
vercel ls

# Rollback to previous
vercel rollback [deployment-url]
```

## 📞 Support

### Documentation
- Vercel: https://vercel.com/docs
- Supabase: https://supabase.com/docs
- Vapi: https://docs.vapi.ai

### Support Contacts
- Vercel: https://vercel.com/support
- Supabase: https://supabase.com/support
- Vapi: https://vapi.ai/support

## 🎯 Next Steps After Deployment

1. **Monitor Performance**
   - Watch Vercel dashboard for errors
   - Check response times
   - Review cache hit rates

2. **Test Thoroughly**
   - Make test calls to Vapi number
   - Verify all tools work correctly
   - Check database records are created

3. **Optimize**
   - Tune cache TTLs based on usage
   - Adjust rate limits if needed
   - Optimize slow queries

4. **Scale**
   - Monitor API usage and costs
   - Upgrade tiers as needed
   - Add more caching layers

5. **Maintain**
   - Rotate API keys every 90 days
   - Review error logs weekly
   - Update dependencies monthly

## 📝 Deployment Log Template

Keep a record of your deployments:

```
Deployment Date: _______________
Deployed By: _______________
Deployment URL: _______________
Vercel Deployment ID: _______________

Environment Variables Configured:
- [ ] DATABASE_URL
- [ ] REDIS_URL
- [ ] RENTCAST_API_KEY
- [ ] DOCUSIGN_INTEGRATION_KEY
- [ ] DOCUSIGN_SECRET_KEY
- [ ] DOCUSIGN_ACCOUNT_ID
- [ ] APIFY_API_TOKEN
- [ ] GOOGLE_CALENDAR_CLIENT_ID
- [ ] GOOGLE_CALENDAR_CLIENT_SECRET
- [ ] ENCRYPTION_KEY
- [ ] OPENAI_API_KEY
- [ ] SENDGRID_API_KEY

Tests Passed:
- [ ] Health check
- [ ] Property search
- [ ] Risk analysis
- [ ] Viewing scheduler
- [ ] Offer generator
- [ ] Voice flow

Notes:
_______________________________________________
_______________________________________________
```

---

## Quick Reference Commands

```bash
# Deploy
vercel --prod

# View logs
vercel logs --follow

# Check env vars
vercel env ls

# Test production
./scripts/test_production.sh https://your-domain.vercel.app

# Rollback
vercel rollback [deployment-url]

# Generate Vapi config
python scripts/update_vapi_config.py https://your-domain.vercel.app
```

---

**Last Updated**: November 2025
**Version**: 1.0.0
