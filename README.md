# Counter AI Real Estate Broker

Voice-first AI buyer's agent system that enables self-represented home buyers to search properties, schedule viewings, analyze risks, and draft purchase offers.

## Project Structure

```
counter-ai-broker/
├── api/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   └── tools/               # Tool endpoints
│       ├── __init__.py
│       ├── search.py        # Property search endpoint
│       ├── analyze_risk.py  # Risk analysis endpoint
│       ├── schedule.py      # Viewing scheduler endpoint
│       └── draft_offer.py   # Offer generator endpoint
├── models/
│   ├── __init__.py
│   └── database.py          # SQLAlchemy models
├── services/
│   ├── __init__.py
│   ├── rentcast.py          # RentCast API client
│   ├── fema.py              # FEMA API client
│   ├── apify.py             # Apify scraper client
│   ├── docusign.py          # Docusign API client
│   └── calendar.py          # Google Calendar client
├── config/
│   ├── __init__.py
│   └── settings.py          # Application settings
├── requirements.txt         # Python dependencies
├── vercel.json             # Vercel deployment config
├── .env.example            # Environment variables template
└── README.md
```

## Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd counter-ai-broker
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

5. **Run the development server**
   ```bash
   python api/main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn api.main:app --reload
   ```

## API Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health check
- `POST /tools/search` - Search for properties
- `POST /tools/analyze-risk` - Analyze property risks
- `POST /tools/schedule` - Schedule property viewing
- `POST /tools/draft-offer` - Generate purchase offer

## Deployment

### Production Deployment

For complete production deployment instructions, see:
- **[Deployment Guide](docs/deployment_guide.md)** - Comprehensive deployment walkthrough
- **[Production Checklist](PRODUCTION_CHECKLIST.md)** - Step-by-step checklist

### Quick Deploy

1. **Install Vercel CLI**:
   ```bash
   npm i -g vercel
   ```

2. **Run deployment script**:
   ```bash
   ./scripts/deploy.sh
   ```
   
   Or manually:
   ```bash
   vercel --prod
   ```

3. **Configure environment variables**:
   ```bash
   # Generate encryption key
   python scripts/generate_encryption_key.py
   
   # Add environment variables
   vercel env add DATABASE_URL production
   vercel env add REDIS_URL production
   vercel env add RENTCAST_API_KEY production
   # ... (see deployment guide for complete list)
   ```

4. **Update Vapi with production URLs**:
   ```bash
   python scripts/update_vapi_config.py https://your-domain.vercel.app
   ```

### Deployment Components

- **Hosting**: Vercel (serverless functions)
- **Database**: Supabase PostgreSQL with connection pooling
- **Cache**: Upstash Redis or Redis Cloud
- **Voice**: Vapi.ai with Twilio integration

### Post-Deployment

- Monitor logs: `vercel logs --follow`
- View dashboard: https://vercel.com/dashboard
- Test endpoints: See deployment guide
- Update Vapi tool URLs with production domain

## Demo Setup

For testing and demonstrations, use the demo data loader:

```bash
# Quick start - generate demo files only
python3 scripts/load_demo_data.py --files-only

# With Redis - load properties to cache
python3 scripts/load_demo_data.py --cache-only

# Full setup - database + cache + files
python3 scripts/load_demo_data.py
```

This creates:
- **Test user** with preferences (Demo User, +14105551234)
- **10 sample Baltimore properties** ($299k-$525k)
- **Demo script** with voice interaction flows
- **Properties JSON** for reference

### Demo Documentation

- **[Quick Start Guide](DEMO_QUICK_START.md)** - 5-minute setup
- **[Demo Data README](DEMO_DATA_README.md)** - Detailed setup instructions
- **[Demo Script](DEMO_SCRIPT.md)** - Voice interaction flows (generated)
- **[Secondary Phone Setup](docs/secondary_phone_setup.md)** - Agent simulation

### Demo Flow

1. **Property Search**: "Find me a house in Baltimore under $400,000"
2. **Risk Analysis**: "Check for red flags on 123 Monument Street"
3. **Schedule Viewing**: "Schedule a viewing for Saturday at 2pm"
4. **Make Offer**: "Make an offer for $370,000"

See `DEMO_QUICK_START.md` for complete demo instructions.

## Requirements

- Python 3.11+
- PostgreSQL (for production)
- Redis (for caching)

## External Services

- **RentCast API** - Property listings and data
- **FEMA API** - Flood zone information
- **Apify** - Zillow agent scraper
- **Docusign** - Contract generation and e-signature
- **Google Calendar** - Appointment scheduling
- **OpenAI** - Property summaries
- **SendGrid/Gmail** - Email notifications
- **CrimeoMeter** - Crime statistics

## Vapi Voice Interface Setup

The Counter system uses Vapi for voice interaction. Configuration files are provided:

- `vapi_complete_config.json` - Complete assistant configuration (import into Vapi)
- `docs/vapi_setup_guide.md` - Detailed setup instructions

### Quick Setup

1. Create a Vapi account at https://vapi.ai
2. Import `vapi_complete_config.json` or manually configure assistant
3. Update tool URLs with your deployment URL
4. Connect a Twilio phone number
5. Test by calling the number

See `docs/vapi_setup_guide.md` for detailed instructions.

## License

MIT
