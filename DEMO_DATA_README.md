# Demo Data Setup Guide

## Overview

This guide helps you set up demo data for Counter AI Real Estate Broker, including:
- Test user with preferences
- 10 sample Baltimore properties
- Demo script for voice interactions
- Secondary phone number for agent simulation

## Quick Start

### Option 1: With Database (Production-like)

If you have PostgreSQL and Redis running:

```bash
# Load demo data into database and cache
python3 scripts/load_demo_data.py
```

This will:
- ✅ Create test user in database
- ✅ Load 10 properties into Redis cache
- ✅ Generate DEMO_SCRIPT.md
- ✅ Generate demo_properties.json

### Option 2: Without Database (Cache Only)

If you only have Redis running:

```bash
# Load properties to cache only (no database)
python3 scripts/load_demo_data.py --cache-only
```

### Option 3: Files Only (No Services)

If you don't have PostgreSQL or Redis:

```bash
# Just generate the demo files
python3 scripts/load_demo_data.py --files-only
```

This creates:
- `DEMO_SCRIPT.md` - Voice interaction flows
- `demo_properties.json` - Sample property data
- You'll need to manually create the test user when services are available

## Test User Details

The demo script creates a test user with these details:

```json
{
  "name": "Demo User",
  "phone": "+14105551234",
  "email": "demo@counter.app",
  "preferred_locations": ["Baltimore, MD", "Towson, MD"],
  "max_budget": 450000,
  "min_beds": 3,
  "min_baths": 2,
  "property_types": ["single-family", "townhouse"],
  "pre_approved": true,
  "pre_approval_amount": 500000
}
```

## Sample Properties

10 Baltimore properties are included, ranging from $299k to $525k:

1. **123 Monument Street** - $385k (3/2) - Federal Hill rowhome
2. **456 Charles Street** - $425k (4/2.5) - Victorian in Charles Village
3. **789 Fort Avenue** - $350k (2/2) - Waterfront condo
4. **234 Aliceanna Street** - $475k (3/3) - Fells Point townhouse
5. **567 Guilford Avenue** - $395k (3/2) - Mount Vernon rowhome
6. **890 Light Street** - $525k (4/3.5) - Luxury Federal Hill
7. **321 Eastern Avenue** - $299k (2/1.5) - Canton rowhome
8. **654 Park Avenue** - $410k (3/2.5) - Bolton Hill brownstone
9. **987 South Charles Street** - $365k (3/2) - Riverside rowhome
10. **432 West Pratt Street** - $450k (3/3) - Inner Harbor penthouse

All properties include:
- Full address and coordinates
- Price, beds, baths, sqft
- Property type and year built
- Estimated value and tax assessment (for risk analysis)
- Listing URL (for agent scraping)
- AI-generated summary

## Demo Script

After running the loader, review `DEMO_SCRIPT.md` for:

### Voice Interaction Flows
- Property search examples
- Risk analysis scenarios
- Viewing scheduling
- Offer generation

### Test Scenarios
- First-time buyer (budget-conscious)
- Competitive market (quick decisions)
- Risk-averse buyer (detailed analysis)

### Troubleshooting Tips
- What to do if search returns no results
- How to handle API failures
- Voice interaction debugging

## Secondary Phone Number Setup

For the viewing scheduler demo, you need a phone number to receive agent calls.

See `docs/secondary_phone_setup.md` for detailed instructions on:

### Quick Options
1. **Google Voice** (Free, 5 min setup) - Recommended for quick demos
2. **Twilio** (~$1/month) - Professional, automated responses
3. **Vapi Agent** (~$10/month) - Most realistic, AI-to-AI conversation
4. **Manual** (Free) - Best for live presentations

### Recommended Setup
For a hackathon or quick demo:
```bash
# 1. Get a Google Voice number (free)
# 2. Set to "Do not disturb" (all calls → voicemail)
# 3. Enable email notifications
# 4. Update demo script with the number
```

## Verifying the Setup

### Check Database
```bash
# Verify test user was created
python3 scripts/verify_database.py
```

Expected output:
```
✅ Database connection successful
✅ Found 1 users
✅ Test user exists: Demo User (demo@counter.app)
```

### Check Redis Cache
```bash
# Verify properties were cached
redis-cli KEYS "search:*"
redis-cli KEYS "property:*"
```

Expected output:
```
1) "search:test_user_id:abc123:400000"
2) "search:test_user_id:abc123:500000"
...
11) "property:demo_prop_001"
12) "property:demo_prop_002"
...
```

### Check Files
```bash
ls -la | grep -E "(DEMO_SCRIPT|demo_properties)"
```

Expected output:
```
-rw-r--r--  1 user  staff  15234 Nov 13 10:30 DEMO_SCRIPT.md
-rw-r--r--  1 user  staff   8192 Nov 13 10:30 demo_properties.json
```

## Testing the Demo

### 1. Test Property Search

Call Counter and say:
```
"Find me a house in Baltimore under $400,000"
```

Expected response:
- Counter returns 3 properties
- Includes 123 Monument Street ($385k)
- Includes 789 Fort Avenue ($350k)
- Includes 567 Guilford Avenue ($395k)

### 2. Test Risk Analysis

Say:
```
"Check for red flags on 123 Monument Street"
```

Expected response:
- Pricing analysis (slightly overpriced by 2.7%)
- Flood zone check
- Tax assessment warning (potential increase)
- Crime data (if available)

### 3. Test Viewing Scheduler

Say:
```
"Schedule a viewing at 456 Charles Street for Saturday at 2pm"
```

Expected response:
- Counter checks your calendar
- Sends email to listing agent
- Creates pending calendar event
- Calls secondary phone number (if configured)

### 4. Test Offer Generation

Say:
```
"I want to make an offer on 123 Monument Street for $370,000"
```

Counter will ask:
- Closing timeline? (say "30 days")
- Financing type? (say "conventional")
- Contingencies? (say "inspection and appraisal")

Expected response:
- Docusign envelope created
- Signing link sent to demo@counter.app
- Offer saved in database

## Troubleshooting

### "No properties found"
**Cause**: Cache not loaded or expired
**Fix**: 
```bash
python3 scripts/load_demo_data.py
# Or check Redis: redis-cli KEYS "search:*"
```

### "User not found"
**Cause**: Database not populated
**Fix**:
```bash
python3 scripts/load_demo_data.py
# Or manually create user via API
```

### "Agent contact not found"
**Cause**: Apify scraper can't access demo URLs
**Fix**: Demo properties use fake URLs. For real demos:
1. Use actual Zillow listings
2. Or mock the Apify response in code

### "Docusign template not found"
**Cause**: Template ID not configured for Maryland
**Fix**: 
1. Upload MD purchase agreement to Docusign
2. Create template with text fields
3. Update `DOCUSIGN_MD_TEMPLATE_ID` in .env

### Voice is slow (>2 seconds)
**Cause**: Cache misses, API timeouts
**Fix**:
1. Verify Redis is running: `redis-cli ping`
2. Check cache hit rate in logs
3. Pre-warm cache with demo data

## Production Deployment

When deploying to production:

1. **Don't use demo data** - It's for testing only
2. **Update phone numbers** - Use real contact info
3. **Configure real APIs** - RentCast, FEMA, Docusign
4. **Set up monitoring** - Sentry, Datadog, etc.
5. **Enable rate limiting** - Protect against abuse
6. **Use production database** - Supabase, AWS RDS, etc.

## Next Steps

1. ✅ Run `python3 scripts/load_demo_data.py`
2. ✅ Review `DEMO_SCRIPT.md`
3. ✅ Set up secondary phone number (see `docs/secondary_phone_setup.md`)
4. ✅ Test each demo scenario
5. ✅ Practice the voice interaction flow
6. 🚀 Ready to demo!

## Support

For issues or questions:
- Check `DEMO_SCRIPT.md` for troubleshooting tips
- Review `docs/secondary_phone_setup.md` for phone setup
- See `README.md` for general setup instructions
- Check logs in `logs/` directory for errors

---

**Happy demoing! 🎉**
