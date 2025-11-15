# Counter AI Demo Script

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

