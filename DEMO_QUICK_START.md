# Counter AI - Demo Quick Start

## 🚀 5-Minute Setup

### Step 1: Load Demo Data (30 seconds)
```bash
python3 scripts/load_demo_data.py --files-only
```

This creates:
- ✅ `DEMO_SCRIPT.md` - Voice interaction flows
- ✅ `demo_properties.json` - 10 Baltimore properties
- ✅ Test user configuration

### Step 2: Review Demo Script (2 minutes)
```bash
open DEMO_SCRIPT.md
# or
cat DEMO_SCRIPT.md
```

Key sections:
- **Demo Flow**: 4 main scenarios (search, risk, schedule, offer)
- **Sample Properties**: 10 properties from $299k-$525k
- **Testing Scenarios**: First-time buyer, competitive market, risk-averse

### Step 3: Set Up Secondary Phone (2 minutes)

**Quick Option - Google Voice** (Recommended):
1. Go to [voice.google.com](https://voice.google.com)
2. Get a free number (choose Baltimore area code: 410/443/667)
3. Set to "Do not disturb" → all calls go to voicemail
4. Enable email notifications
5. Done! ✅

**Alternative Options**:
- See `docs/secondary_phone_setup.md` for Twilio, Vapi Agent, or Manual options

### Step 4: Test the Demo (30 seconds)

Call Counter and say:
```
"Find me a house in Baltimore under $400,000"
```

Expected: 3 properties returned in < 1 second

---

## 📋 Demo Flow Cheat Sheet

### 1️⃣ Property Search
**Say**: "Find me a house in Baltimore under $400,000"
**Returns**: 3 properties (Monument St, Fort Ave, Guilford Ave)

### 2️⃣ Risk Analysis
**Say**: "Check for red flags on 123 Monument Street"
**Returns**: Pricing, flood zone, tax, crime analysis

### 3️⃣ Schedule Viewing
**Say**: "Schedule a viewing at 456 Charles Street for Saturday at 2pm"
**Returns**: Agent contacted, calendar event created

### 4️⃣ Make Offer
**Say**: "Make an offer on 123 Monument Street for $370,000"
**Returns**: Docusign contract sent to email

---

## 🏠 Sample Properties (Quick Reference)

| Address | Price | Beds/Baths | Type | Neighborhood |
|---------|-------|------------|------|--------------|
| 123 Monument St | $385k | 3/2 | Rowhome | Federal Hill |
| 456 Charles St | $425k | 4/2.5 | Victorian | Charles Village |
| 789 Fort Ave | $350k | 2/2 | Condo | Locust Point |
| 234 Aliceanna St | $475k | 3/3 | Townhouse | Fells Point |
| 567 Guilford Ave | $395k | 3/2 | Rowhome | Mount Vernon |
| 890 Light St | $525k | 4/3.5 | Luxury | Federal Hill |
| 321 Eastern Ave | $299k | 2/1.5 | Rowhome | Canton |
| 654 Park Ave | $410k | 3/2.5 | Brownstone | Bolton Hill |
| 987 S Charles St | $365k | 3/2 | Rowhome | Riverside |
| 432 W Pratt St | $450k | 3/3 | Penthouse | Inner Harbor |

---

## 👤 Test User Details

```
Name: Demo User
Phone: +1 (410) 555-1234
Email: demo@counter.app
Budget: $450,000
Preferences: 3+ beds, 2+ baths in Baltimore
Pre-approval: $500,000 (conventional or cash)
```

---

## 🎯 Success Checklist

Before your demo, verify:

- [ ] Demo files created (`DEMO_SCRIPT.md`, `demo_properties.json`)
- [ ] Secondary phone number set up and tested
- [ ] Reviewed demo flow (4 main scenarios)
- [ ] Practiced voice commands
- [ ] Tested at least one end-to-end flow
- [ ] Backup plan ready (manual testing if APIs fail)

---

## 🐛 Quick Troubleshooting

### "No properties found"
```bash
# Reload demo data
python3 scripts/load_demo_data.py --cache-only
```

### "User not found"
```bash
# Create test user
python3 scripts/load_demo_data.py
```

### Voice is slow (>2 seconds)
- Check Redis: `redis-cli ping`
- Verify cache loaded: `redis-cli KEYS "search:*"`
- Check API logs for timeouts

### Docusign fails
- Verify template ID in `.env`
- Check integration key is valid
- Ensure account has API access

---

## 📚 Full Documentation

- **Demo Data Setup**: `DEMO_DATA_README.md`
- **Demo Script**: `DEMO_SCRIPT.md`
- **Phone Setup**: `docs/secondary_phone_setup.md`
- **General Setup**: `README.md`
- **API Reference**: `VAPI_QUICK_REFERENCE.md`

---

## 🎬 Demo Tips

1. **Start Simple**: Begin with property search, then add complexity
2. **Use Natural Language**: Counter understands conversational queries
3. **Show Interruptions**: Interrupt Counter mid-sentence to show responsiveness
4. **Highlight Speed**: Point out sub-1-second response times
5. **Explain Context**: Show how Counter remembers "that property" from earlier
6. **Demo Risk Analysis**: This is a unique feature that impresses buyers
7. **Show Offer Generation**: End-to-end from search to signed contract

---

## 🚀 Ready to Demo!

You're all set! Key points to remember:

- ✅ 10 sample properties loaded
- ✅ Test user configured
- ✅ Demo script ready
- ✅ Secondary phone set up
- ✅ Voice flows practiced

**Good luck with your demo! 🎉**

---

## 📞 Support

Questions? Check:
1. `DEMO_SCRIPT.md` - Detailed scenarios and troubleshooting
2. `DEMO_DATA_README.md` - Setup instructions
3. `docs/secondary_phone_setup.md` - Phone configuration
4. Project `README.md` - General documentation
