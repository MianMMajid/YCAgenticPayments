# Create VAPI Tools via API - Direct Commands

**Send your tools to VAPI programmatically using the `/tool` endpoint**

---

## Quick Command (All 4 Tools)

### Option 1: Using the Script (Easiest)

```bash
cd /Users/omarramadan/Desktop/code/realtorAgent
bash scripts/create_vapi_tools_direct.sh
```

This will create all 4 tools automatically.

---

### Option 2: Individual curl Commands

#### Tool 1: search_properties

```bash
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer 13c20c0e-acd5-4ccc-a617-0bcf1e95a6de" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "search_properties",
      "description": "Search for properties matching the user'\''s criteria. Use this when the user wants to find homes, see listings, or browse properties in a specific area.",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {"type": "string", "description": "City and state (e.g., '\''Baltimore, MD'\'', '\''Arlington, VA'\'')"},
          "max_price": {"type": "integer", "description": "Maximum purchase price in dollars"},
          "min_beds": {"type": "integer", "description": "Minimum number of bedrooms"},
          "min_baths": {"type": "number", "description": "Minimum number of bathrooms (can be decimal like 1.5)"},
          "property_type": {"type": "string", "enum": ["single-family", "condo", "townhouse", "multi-family"], "description": "Type of property"},
          "user_id": {"type": "string", "description": "User identifier from the conversation context"}
        },
        "required": ["location", "max_price", "user_id"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/search",
      "method": "POST",
      "headers": {"Content-Type": "application/json"}
    }
  }'
```

#### Tool 2: analyze_risk

```bash
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer 13c20c0e-acd5-4ccc-a617-0bcf1e95a6de" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "analyze_risk",
      "description": "Analyze a property for potential red flags including overpricing, flood risk, crime, and tax issues. Use this when the user asks about problems, risks, or wants to check if a property is a good deal.",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {"type": "string", "description": "Unique identifier for the property from search results"},
          "address": {"type": "string", "description": "Full property address"},
          "list_price": {"type": "integer", "description": "Listed price of the property in dollars"},
          "user_id": {"type": "string", "description": "User identifier from the conversation context"}
        },
        "required": ["property_id", "address", "list_price", "user_id"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/analyze-risk",
      "method": "POST",
      "headers": {"Content-Type": "application/json"}
    }
  }'
```

#### Tool 3: schedule_viewing

```bash
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer 13c20c0e-acd5-4ccc-a617-0bcf1e95a6de" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "schedule_viewing",
      "description": "Schedule a property viewing by contacting the listing agent. Use this when the user wants to see a property, book a showing, or arrange a tour.",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {"type": "string", "description": "Unique identifier for the property"},
          "listing_url": {"type": "string", "description": "URL of the property listing (typically from Zillow)"},
          "requested_time": {"type": "string", "format": "date-time", "description": "Requested viewing time in ISO 8601 format (e.g., '\''2025-11-15T14:00:00Z'\'')"},
          "user_id": {"type": "string", "description": "User identifier from the conversation context"},
          "user_name": {"type": "string", "description": "User'\''s full name"},
          "user_email": {"type": "string", "description": "User'\''s email address"}
        },
        "required": ["property_id", "listing_url", "requested_time", "user_id", "user_name", "user_email"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/schedule",
      "method": "POST",
      "headers": {"Content-Type": "application/json"}
    }
  }'
```

#### Tool 4: draft_offer

```bash
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer 13c20c0e-acd5-4ccc-a617-0bcf1e95a6de" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "draft_offer",
      "description": "Generate a purchase offer document for the user to sign. Use this when the user wants to make an offer, submit a bid, or purchase a property.",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {"type": "string", "description": "Unique identifier for the property"},
          "address": {"type": "string", "description": "Full property address"},
          "offer_price": {"type": "integer", "description": "Offer amount in dollars"},
          "closing_days": {"type": "integer", "description": "Number of days until closing (typically 14, 30, or 45)"},
          "financing_type": {"type": "string", "enum": ["cash", "conventional", "fha", "va"], "description": "Type of financing"},
          "contingencies": {"type": "array", "items": {"type": "string", "enum": ["inspection", "appraisal", "financing", "sale-of-home"]}, "description": "List of contingencies to include in the offer"},
          "user_id": {"type": "string", "description": "User identifier from the conversation context"},
          "user_email": {"type": "string", "description": "User'\''s email address for receiving the signing link"}
        },
        "required": ["property_id", "address", "offer_price", "closing_days", "financing_type", "user_id", "user_email"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/draft-offer",
      "method": "POST",
      "headers": {"Content-Type": "application/json"}
    }
  }'
```

---

## Option 3: Using JSON File

You can also send each tool from the JSON file:

```bash
# Extract and send each tool individually
# (The JSON file has a "tools" array, so you need to extract each one)

# For example, using jq to extract first tool:
curl -X POST https://api.vapi.ai/tool \
  -H "Authorization: Bearer 13c20c0e-acd5-4ccc-a617-0bcf1e95a6de" \
  -H "Content-Type: application/json" \
  -d "$(jq '.tools[0]' vapi_tools_config.json)"
```

---

## Expected Response

Each tool creation should return:

```json
{
  "id": "tool_abc123...",
  "name": "search_properties",
  "type": "function",
  "server": {
    "url": "https://ycnov15vapivoice.ngrok.app/tools/search",
    ...
  },
  "createdAt": "2024-11-14T...",
  "updatedAt": "2024-11-14T..."
}
```

---

## Verify Tools Created

After running the commands, verify in VAPI dashboard:

1. Go to https://dashboard.vapi.ai
2. Open your assistant
3. Go to Functions/Tools section
4. You should see all 4 tools listed:
   - ✅ search_properties
   - ✅ analyze_risk
   - ✅ schedule_viewing
   - ✅ draft_offer

---

## Quick Test

Test that your backend is accessible:

```bash
curl https://ycnov15vapivoice.ngrok.app/health
```

Should return: `{"status": "healthy"}`

---

**Last Updated**: November 2024

