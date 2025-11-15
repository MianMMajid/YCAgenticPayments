#!/usr/bin/env python3
"""
Load demo data for Counter AI Real Estate Broker.

This script:
1. Creates a test user with preferences
2. Loads 10 sample Baltimore properties into Redis cache
3. Prepares the system for demo/testing
"""
import sys
import os
import json
import hashlib
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.database import engine, BaseModel
from models.user import User
from services.cache_client import cache_client
from config.settings import settings


# Sample Baltimore properties for demo
DEMO_PROPERTIES = [
    {
        "property_id": "demo_prop_001",
        "address": "123 Monument Street, Baltimore, MD 21201",
        "price": 385000,
        "beds": 3,
        "baths": 2,
        "sqft": 1850,
        "property_type": "single-family",
        "listing_url": "https://www.zillow.com/homedetails/123-Monument-St-Baltimore-MD-21201/demo001",
        "summary": "Charming 3-bed Federal Hill rowhome with renovated kitchen and rooftop deck",
        "lat": 39.2847,
        "lon": -76.6205,
        "year_built": 1920,
        "lot_size": 1200,
        "status": "Active",
        "days_on_market": 12,
        "estimated_value": 375000,
        "tax_assessment": 320000
    },
    {
        "property_id": "demo_prop_002",
        "address": "456 Charles Street, Baltimore, MD 21218",
        "price": 425000,
        "beds": 4,
        "baths": 2.5,
        "sqft": 2200,
        "property_type": "single-family",
        "listing_url": "https://www.zillow.com/homedetails/456-Charles-St-Baltimore-MD-21218/demo002",
        "summary": "Spacious 4-bed Victorian in Charles Village with original hardwood floors",
        "lat": 39.3260,
        "lon": -76.6177,
        "year_built": 1895,
        "lot_size": 1800,
        "status": "Active",
        "days_on_market": 8,
        "estimated_value": 410000,
        "tax_assessment": 350000
    },
    {
        "property_id": "demo_prop_003",
        "address": "789 Fort Avenue, Baltimore, MD 21230",
        "price": 350000,
        "beds": 2,
        "baths": 2,
        "sqft": 1400,
        "property_type": "condo",
        "listing_url": "https://www.zillow.com/homedetails/789-Fort-Ave-Baltimore-MD-21230/demo003",
        "summary": "Modern 2-bed waterfront condo in Locust Point with harbor views",
        "lat": 39.2667,
        "lon": -76.5986,
        "year_built": 2015,
        "lot_size": 0,
        "status": "Active",
        "days_on_market": 5,
        "estimated_value": 355000,
        "tax_assessment": 340000
    },
    {
        "property_id": "demo_prop_004",
        "address": "234 Aliceanna Street, Baltimore, MD 21231",
        "price": 475000,
        "beds": 3,
        "baths": 3,
        "sqft": 2000,
        "property_type": "townhouse",
        "listing_url": "https://www.zillow.com/homedetails/234-Aliceanna-St-Baltimore-MD-21231/demo004",
        "summary": "Contemporary 3-bed Fells Point townhouse with garage and private patio",
        "lat": 39.2833,
        "lon": -76.5933,
        "year_built": 2018,
        "lot_size": 1000,
        "status": "Active",
        "days_on_market": 15,
        "estimated_value": 465000,
        "tax_assessment": 450000
    },
    {
        "property_id": "demo_prop_005",
        "address": "567 Guilford Avenue, Baltimore, MD 21202",
        "price": 395000,
        "beds": 3,
        "baths": 2,
        "sqft": 1750,
        "property_type": "single-family",
        "listing_url": "https://www.zillow.com/homedetails/567-Guilford-Ave-Baltimore-MD-21202/demo005",
        "summary": "Updated 3-bed Mount Vernon rowhome near cultural district",
        "lat": 39.2976,
        "lon": -76.6147,
        "year_built": 1910,
        "lot_size": 1100,
        "status": "Active",
        "days_on_market": 20,
        "estimated_value": 380000,
        "tax_assessment": 310000
    },
    {
        "property_id": "demo_prop_006",
        "address": "890 Light Street, Baltimore, MD 21230",
        "price": 525000,
        "beds": 4,
        "baths": 3.5,
        "sqft": 2600,
        "property_type": "single-family",
        "listing_url": "https://www.zillow.com/homedetails/890-Light-St-Baltimore-MD-21230/demo006",
        "summary": "Luxury 4-bed Federal Hill home with finished basement and parking",
        "lat": 39.2789,
        "lon": -76.6119,
        "year_built": 2005,
        "lot_size": 2000,
        "status": "Active",
        "days_on_market": 10,
        "estimated_value": 510000,
        "tax_assessment": 480000
    },
    {
        "property_id": "demo_prop_007",
        "address": "321 Eastern Avenue, Baltimore, MD 21224",
        "price": 299000,
        "beds": 2,
        "baths": 1.5,
        "sqft": 1200,
        "property_type": "single-family",
        "listing_url": "https://www.zillow.com/homedetails/321-Eastern-Ave-Baltimore-MD-21224/demo007",
        "summary": "Cozy 2-bed Canton rowhome with exposed brick and backyard",
        "lat": 39.2833,
        "lon": -76.5767,
        "year_built": 1925,
        "lot_size": 900,
        "status": "Active",
        "days_on_market": 7,
        "estimated_value": 310000,
        "tax_assessment": 280000
    },
    {
        "property_id": "demo_prop_008",
        "address": "654 Park Avenue, Baltimore, MD 21201",
        "price": 410000,
        "beds": 3,
        "baths": 2.5,
        "sqft": 1900,
        "property_type": "single-family",
        "listing_url": "https://www.zillow.com/homedetails/654-Park-Ave-Baltimore-MD-21201/demo008",
        "summary": "Elegant 3-bed Bolton Hill brownstone with original details",
        "lat": 39.3067,
        "lon": -76.6258,
        "year_built": 1885,
        "lot_size": 1500,
        "status": "Active",
        "days_on_market": 18,
        "estimated_value": 400000,
        "tax_assessment": 360000
    },
    {
        "property_id": "demo_prop_009",
        "address": "987 South Charles Street, Baltimore, MD 21230",
        "price": 365000,
        "beds": 3,
        "baths": 2,
        "sqft": 1650,
        "property_type": "single-family",
        "listing_url": "https://www.zillow.com/homedetails/987-S-Charles-St-Baltimore-MD-21230/demo009",
        "summary": "Renovated 3-bed Riverside rowhome with modern finishes",
        "lat": 39.2722,
        "lon": -76.6089,
        "year_built": 1915,
        "lot_size": 1000,
        "status": "Active",
        "days_on_market": 14,
        "estimated_value": 370000,
        "tax_assessment": 330000
    },
    {
        "property_id": "demo_prop_010",
        "address": "432 West Pratt Street, Baltimore, MD 21201",
        "price": 450000,
        "beds": 3,
        "baths": 3,
        "sqft": 2100,
        "property_type": "condo",
        "listing_url": "https://www.zillow.com/homedetails/432-W-Pratt-St-Baltimore-MD-21201/demo010",
        "summary": "Penthouse 3-bed condo in Inner Harbor with skyline views and amenities",
        "lat": 39.2864,
        "lon": -76.6228,
        "year_built": 2012,
        "lot_size": 0,
        "status": "Active",
        "days_on_market": 6,
        "estimated_value": 445000,
        "tax_assessment": 430000
    }
]


def create_test_user(session: Session) -> User:
    """Create a test user with preferences."""
    print("\n📝 Creating test user...")
    
    # Check if test user already exists
    existing_user = session.query(User).filter_by(name="Demo User").first()
    if existing_user:
        print(f"✅ Test user already exists: {existing_user.id}")
        return existing_user
    
    user = User(
        phone_number="+14105551234",
        email="demo@counter.app",
        name="Demo User",
        preferred_locations=["Baltimore, MD", "Towson, MD"],
        max_budget=450000,
        min_beds=3,
        min_baths=2,
        property_types=["single-family", "townhouse"],
        pre_approved=True,
        pre_approval_amount=500000,
        last_active=datetime.now(timezone.utc).isoformat()
    )
    
    session.add(user)
    session.commit()
    session.refresh(user)
    
    print(f"✅ Created test user: {user.id}")
    print(f"   Name: {user.name}")
    print(f"   Phone: {user.phone_number}")
    print(f"   Email: {user.email}")
    print(f"   Budget: ${user.max_budget:,}")
    print(f"   Preferences: {user.min_beds}+ beds, {user.min_baths}+ baths")
    print(f"   Pre-approved: ${user.pre_approval_amount:,}")
    
    return user


def load_properties_to_cache(user_id: str):
    """Load sample properties into Redis cache."""
    print("\n🏠 Loading sample properties to cache...")
    
    if not cache_client.client:
        print("⚠️  Redis not available. Skipping cache loading.")
        print("   Properties will still be available in the demo script.")
        return
    
    # Create search result cache entries for different queries
    search_queries = [
        {
            "location": "Baltimore, MD",
            "max_price": 400000,
            "min_beds": 3,
            "properties": [p for p in DEMO_PROPERTIES if p["price"] <= 400000 and p["beds"] >= 3][:3]
        },
        {
            "location": "Baltimore, MD",
            "max_price": 500000,
            "min_beds": 2,
            "properties": DEMO_PROPERTIES[:3]
        },
        {
            "location": "Baltimore, MD",
            "max_price": 450000,
            "min_beds": 3,
            "properties": [p for p in DEMO_PROPERTIES if p["price"] <= 450000 and p["beds"] >= 3][:3]
        }
    ]
    
    cached_count = 0
    for query in search_queries:
        # Create cache key matching the search tool format
        location_hash = hashlib.md5(query["location"].encode()).hexdigest()[:8]
        cache_key = f"search:{user_id}:{location_hash}:{query['max_price']}"
        
        cache_data = {
            "properties": query["properties"],
            "total_found": len(query["properties"]),
            "cached_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Cache for 24 hours
        if cache_client.set(cache_key, cache_data, ttl=86400):
            cached_count += 1
            print(f"✅ Cached search: {query['location']} under ${query['max_price']:,} ({len(query['properties'])} properties)")
    
    # Cache individual property details
    for prop in DEMO_PROPERTIES:
        cache_key = f"property:{prop['property_id']}"
        if cache_client.set(cache_key, prop, ttl=86400):
            cached_count += 1
    
    print(f"✅ Loaded {cached_count} cache entries")
    print(f"   - {len(search_queries)} search result sets")
    print(f"   - {len(DEMO_PROPERTIES)} individual properties")


def save_demo_script():
    """Save demo script for voice interaction."""
    print("\n📋 Creating demo script...")
    
    demo_script = """# Counter AI Demo Script

## Test User Information
- **Name**: Demo User
- **Phone**: +1 (410) 555-1234
- **Email**: demo@counter.app
- **Budget**: $450,000
- **Preferences**: 3+ beds, 2+ baths in Baltimore
- **Pre-approval**: $500,000 (cash or conventional)

## Demo Flow

### 1. Property Search
**User**: "Counter, find me a house in Baltimore under $400,000"

**Expected Response**: Counter will search and return 3 properties:
- 123 Monument Street - $385k (3 bed, 2 bath)
- 789 Fort Avenue - $350k (2 bed, 2 bath condo)
- 567 Guilford Avenue - $395k (3 bed, 2 bath)

**Follow-up**: "Tell me more about the Monument Street property"

---

### 2. Risk Analysis
**User**: "Check for red flags on 123 Monument Street"

**Expected Response**: Counter will analyze:
- Pricing: Slightly overpriced by 2.7% (list $385k vs estimated $375k)
- Flood zone: Check FEMA data
- Tax assessment: $320k (potential for increase)
- Crime: Check neighborhood safety

**Follow-up**: "What about the Charles Street property?"

---

### 3. Schedule Viewing
**User**: "Schedule a viewing at 456 Charles Street for Saturday at 2pm"

**Expected Response**: Counter will:
- Extract agent contact from Zillow listing
- Check your calendar for conflicts
- Send email to listing agent
- Create pending calendar event
- Confirm appointment request

**Note**: For demo, agent email will go to a test inbox

---

### 4. Make an Offer
**User**: "I want to make an offer on 123 Monument Street for $370,000"

**Expected Response**: Counter will ask for details:
- Closing timeline (14, 30, or 45 days)
- Financing type (cash, conventional, FHA)
- Contingencies (inspection, appraisal, financing)

**User**: "30 days, conventional financing, with inspection and appraisal contingencies"

**Expected Response**: Counter will:
- Generate Maryland purchase agreement via Docusign
- Populate all fields with offer terms
- Send signing link to demo@counter.app
- Confirm document sent

---

## Sample Properties Available

1. **123 Monument Street** - $385k (3/2, 1850 sqft) - Federal Hill rowhome
2. **456 Charles Street** - $425k (4/2.5, 2200 sqft) - Victorian in Charles Village
3. **789 Fort Avenue** - $350k (2/2, 1400 sqft) - Waterfront condo
4. **234 Aliceanna Street** - $475k (3/3, 2000 sqft) - Fells Point townhouse
5. **567 Guilford Avenue** - $395k (3/2, 1750 sqft) - Mount Vernon rowhome
6. **890 Light Street** - $525k (4/3.5, 2600 sqft) - Luxury Federal Hill
7. **321 Eastern Avenue** - $299k (2/1.5, 1200 sqft) - Canton rowhome
8. **654 Park Avenue** - $410k (3/2.5, 1900 sqft) - Bolton Hill brownstone
9. **987 South Charles Street** - $365k (3/2, 1650 sqft) - Riverside rowhome
10. **432 West Pratt Street** - $450k (3/3, 2100 sqft) - Inner Harbor penthouse

---

## Testing Scenarios

### Scenario A: First-Time Buyer
- Budget-conscious search under $350k
- Needs education on flood insurance and tax implications
- Wants to see multiple properties before deciding

### Scenario B: Competitive Market
- Search in popular neighborhood (Federal Hill, Fells Point)
- Quick decision needed (properties moving fast)
- Cash offer to be competitive

### Scenario C: Risk-Averse Buyer
- Detailed risk analysis on multiple properties
- Concerned about overpricing and hidden costs
- Wants inspection and appraisal contingencies

---

## Voice Interaction Tips

1. **Natural Language**: Speak naturally, Counter understands conversational queries
2. **Interruptions**: You can interrupt Counter at any time with new questions
3. **Context**: Counter remembers the conversation, so you can say "that property" or "the first one"
4. **Clarifications**: If Counter needs more info, it will ask follow-up questions
5. **Filler Phrases**: During API calls, Counter will say things like "Let me check the records..."

---

## Secondary Phone Number Setup

For simulated agent calls (viewing confirmations), set up:

**Option 1: Voicemail**
- Use a Google Voice number
- Set to go straight to voicemail
- Counter will leave viewing request message

**Option 2: Second Vapi Agent**
- Create a simple "Listing Agent" Vapi assistant
- Responds to viewing requests with confirmation
- Can simulate back-and-forth scheduling

**Option 3: Manual Testing**
- Have a team member answer the secondary number
- Follow a script to confirm viewings
- Most realistic for demo purposes

---

## Troubleshooting

### If search returns no results:
- Check Redis connection: `redis-cli ping`
- Verify cache was loaded: `redis-cli KEYS "search:*"`
- Check API logs for RentCast errors

### If risk analysis fails:
- Verify FEMA API is accessible
- Check RentCast API key is valid
- Review error logs in Sentry

### If Docusign fails:
- Verify integration key and secret
- Check template IDs are correct for MD
- Ensure account has API access enabled

### If voice is slow:
- Check Vercel function logs for timeouts
- Verify Redis cache is being used
- Monitor external API latency

---

## Success Metrics

- ✅ Search responds in < 1 second
- ✅ Risk analysis completes in < 2 seconds
- ✅ Viewing request sent successfully
- ✅ Docusign envelope created and sent
- ✅ Voice interruptions handled smoothly
- ✅ No errors in conversation flow

"""
    
    with open("DEMO_SCRIPT.md", "w") as f:
        f.write(demo_script)
    
    print("✅ Created DEMO_SCRIPT.md")
    print("   Contains: Voice interaction flows, test scenarios, troubleshooting")


def save_properties_json():
    """Save properties as JSON for reference."""
    print("\n💾 Saving properties JSON...")
    
    with open("demo_properties.json", "w") as f:
        json.dump(DEMO_PROPERTIES, f, indent=2)
    
    print("✅ Created demo_properties.json")
    print(f"   Contains: {len(DEMO_PROPERTIES)} Baltimore properties")


def main():
    """Main execution function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Load demo data for Counter AI")
    parser.add_argument("--cache-only", action="store_true", 
                       help="Only load cache, skip database")
    parser.add_argument("--files-only", action="store_true",
                       help="Only generate files, skip database and cache")
    args = parser.parse_args()
    
    print("=" * 60)
    print("Counter AI - Demo Data Loader")
    print("=" * 60)
    
    user_id = "demo_user_12345"  # Default user ID for cache-only mode
    
    # Files-only mode
    if args.files_only:
        print("\n📄 Running in FILES-ONLY mode")
        print("   (Skipping database and cache)")
        
        save_demo_script()
        save_properties_json()
        
        print("\n" + "=" * 60)
        print("✅ Demo files created successfully!")
        print("=" * 60)
        print("\n📋 Created Files:")
        print("   - DEMO_SCRIPT.md")
        print("   - demo_properties.json")
        print("\n⚠️  Note: Run with database connection to create test user")
        print("🚀 Review DEMO_SCRIPT.md to get started!")
        return
    
    # Cache-only mode
    if args.cache_only:
        print("\n💾 Running in CACHE-ONLY mode")
        print("   (Skipping database)")
        
        load_properties_to_cache(user_id)
        save_demo_script()
        save_properties_json()
        
        print("\n" + "=" * 60)
        print("✅ Demo data loaded to cache!")
        print("=" * 60)
        print(f"\n📱 Using default User ID: {user_id}")
        print("\n⚠️  Note: Run without --cache-only to create test user in database")
        print("🚀 Ready for demo!")
        return
    
    # Full mode (database + cache + files)
    print("\n🗄️  Running in FULL mode")
    print("   (Database + Cache + Files)")
    
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    
    try:
        # 1. Create test user
        user = create_test_user(session)
        user_id = user.id
        
        # 2. Load properties to cache
        load_properties_to_cache(user_id)
        
        # 3. Save demo script
        save_demo_script()
        
        # 4. Save properties JSON
        save_properties_json()
        
        print("\n" + "=" * 60)
        print("✅ Demo data loaded successfully!")
        print("=" * 60)
        print(f"\n📱 Test User ID: {user_id}")
        print(f"📞 Test Phone: +1 (410) 555-1234")
        print(f"📧 Test Email: demo@counter.app")
        print(f"\n📋 Next Steps:")
        print("   1. Review DEMO_SCRIPT.md for voice interaction flows")
        print("   2. Test search: 'Find me a house in Baltimore under $400k'")
        print("   3. Test risk analysis on any property")
        print("   4. Set up secondary phone number for agent simulation")
        print("\n🚀 Ready for demo!")
        
    except Exception as e:
        print(f"\n❌ Error loading demo data: {e}")
        print("\n💡 Try running with --cache-only or --files-only if services aren't available")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        session.close()


if __name__ == "__main__":
    main()
