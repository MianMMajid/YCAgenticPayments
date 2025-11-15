#!/bin/bash
# Create VAPI tools using curl commands
# 
# Usage:
#   export VAPI_API_KEY=your_vapi_private_key
#   bash scripts/create_vapi_tools_curl.sh

set -e

VAPI_API_KEY="${VAPI_API_KEY:-}"
VAPI_BASE_URL="https://api.vapi.ai"

if [ -z "$VAPI_API_KEY" ]; then
    echo "❌ Error: VAPI_API_KEY environment variable not set"
    echo ""
    echo "Set it with:"
    echo "  export VAPI_API_KEY=your_vapi_private_key"
    exit 1
fi

echo "============================================================"
echo "VAPI TOOLS CREATION (via curl)"
echo "============================================================"
echo ""

# Tool 1: search_properties
echo "Creating tool: search_properties..."
curl -X POST "$VAPI_BASE_URL/tool" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "search_properties",
      "description": "Search for properties matching the user'\''s criteria. Use this when the user wants to find homes, see listings, or browse properties in a specific area.",
      "parameters": {
        "type": "object",
        "properties": {
          "location": {
            "type": "string",
            "description": "City and state (e.g., '\''Baltimore, MD'\'', '\''Arlington, VA'\'')"
          },
          "max_price": {
            "type": "integer",
            "description": "Maximum purchase price in dollars"
          },
          "min_beds": {
            "type": "integer",
            "description": "Minimum number of bedrooms"
          },
          "min_baths": {
            "type": "number",
            "description": "Minimum number of bathrooms (can be decimal like 1.5)"
          },
          "property_type": {
            "type": "string",
            "enum": ["single-family", "condo", "townhouse", "multi-family"],
            "description": "Type of property"
          },
          "user_id": {
            "type": "string",
            "description": "User identifier from the conversation context"
          }
        },
        "required": ["location", "max_price", "user_id"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/search",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }'
echo ""
echo ""

# Tool 2: analyze_risk
echo "Creating tool: analyze_risk..."
curl -X POST "$VAPI_BASE_URL/tool" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "analyze_risk",
      "description": "Analyze a property for potential red flags including overpricing, flood risk, crime, and tax issues. Use this when the user asks about problems, risks, or wants to check if a property is a good deal.",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {
            "type": "string",
            "description": "Unique identifier for the property from search results"
          },
          "address": {
            "type": "string",
            "description": "Full property address"
          },
          "list_price": {
            "type": "integer",
            "description": "Listed price of the property in dollars"
          },
          "user_id": {
            "type": "string",
            "description": "User identifier from the conversation context"
          }
        },
        "required": ["property_id", "address", "list_price", "user_id"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/analyze-risk",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }'
echo ""
echo ""

# Tool 3: schedule_viewing
echo "Creating tool: schedule_viewing..."
curl -X POST "$VAPI_BASE_URL/tool" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "schedule_viewing",
      "description": "Schedule a property viewing by contacting the listing agent. Use this when the user wants to see a property, book a showing, or arrange a tour.",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {
            "type": "string",
            "description": "Unique identifier for the property"
          },
          "listing_url": {
            "type": "string",
            "description": "URL of the property listing (typically from Zillow)"
          },
          "requested_time": {
            "type": "string",
            "format": "date-time",
            "description": "Requested viewing time in ISO 8601 format (e.g., '\''2025-11-15T14:00:00Z'\'')"
          },
          "user_id": {
            "type": "string",
            "description": "User identifier from the conversation context"
          },
          "user_name": {
            "type": "string",
            "description": "User'\''s full name"
          },
          "user_email": {
            "type": "string",
            "description": "User'\''s email address"
          }
        },
        "required": ["property_id", "listing_url", "requested_time", "user_id", "user_name", "user_email"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/schedule",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }'
echo ""
echo ""

# Tool 4: draft_offer
echo "Creating tool: draft_offer..."
curl -X POST "$VAPI_BASE_URL/tool" \
  -H "Authorization: Bearer $VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "type": "function",
    "function": {
      "name": "draft_offer",
      "description": "Generate a purchase offer document for the user to sign. Use this when the user wants to make an offer, submit a bid, or purchase a property.",
      "parameters": {
        "type": "object",
        "properties": {
          "property_id": {
            "type": "string",
            "description": "Unique identifier for the property"
          },
          "address": {
            "type": "string",
            "description": "Full property address"
          },
          "offer_price": {
            "type": "integer",
            "description": "Offer amount in dollars"
          },
          "closing_days": {
            "type": "integer",
            "description": "Number of days until closing (typically 14, 30, or 45)"
          },
          "financing_type": {
            "type": "string",
            "enum": ["cash", "conventional", "fha", "va"],
            "description": "Type of financing"
          },
          "contingencies": {
            "type": "array",
            "items": {
              "type": "string",
              "enum": ["inspection", "appraisal", "financing", "sale-of-home"]
            },
            "description": "List of contingencies to include in the offer"
          },
          "user_id": {
            "type": "string",
            "description": "User identifier from the conversation context"
          },
          "user_email": {
            "type": "string",
            "description": "User'\''s email address for receiving the signing link"
          }
        },
        "required": ["property_id", "address", "offer_price", "closing_days", "financing_type", "user_id", "user_email"]
      }
    },
    "server": {
      "url": "https://ycnov15vapivoice.ngrok.app/tools/draft-offer",
      "method": "POST",
      "headers": {
        "Content-Type": "application/json"
      }
    }
  }'
echo ""
echo ""

echo "============================================================"
echo "✅ All tools created!"
echo "============================================================"
echo ""
echo "Next steps:"
echo "  1. Go to https://dashboard.vapi.ai"
echo "  2. Open your assistant"
echo "  3. Go to Functions/Tools section"
echo "  4. Verify all 4 tools are listed"
echo "  5. Test with a phone call"
echo ""

