#!/usr/bin/env python3
"""
Generate Vapi configuration with production URLs

This script generates the Vapi tool configuration with your production domain.

Usage:
    python scripts/update_vapi_config.py https://your-domain.vercel.app
"""

import sys
import json

def generate_vapi_config(base_url: str) -> dict:
    """Generate Vapi tool configuration with production URLs"""
    
    # Remove trailing slash if present
    base_url = base_url.rstrip('/')
    
    config = {
        "functions": [
            {
                "name": "search_properties",
                "url": f"{base_url}/api/tools/search",
                "description": "Search for homes matching criteria including location, price range, bedrooms, and bathrooms",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string",
                            "description": "City and state (e.g., 'Baltimore, MD')"
                        },
                        "max_price": {
                            "type": "integer",
                            "description": "Maximum price in dollars"
                        },
                        "min_beds": {
                            "type": "integer",
                            "description": "Minimum number of bedrooms"
                        },
                        "min_baths": {
                            "type": "number",
                            "description": "Minimum number of bathrooms"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier from session"
                        }
                    },
                    "required": ["location", "max_price", "user_id"]
                }
            },
            {
                "name": "analyze_risk",
                "url": f"{base_url}/api/tools/analyze-risk",
                "description": "Analyze a property for potential red flags including overpricing, flood risk, tax issues, and crime",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "string",
                            "description": "Unique property identifier"
                        },
                        "address": {
                            "type": "string",
                            "description": "Full property address"
                        },
                        "list_price": {
                            "type": "integer",
                            "description": "Listed price in dollars"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier from session"
                        }
                    },
                    "required": ["property_id", "address", "list_price", "user_id"]
                }
            },
            {
                "name": "schedule_viewing",
                "url": f"{base_url}/api/tools/schedule",
                "description": "Schedule a property viewing by contacting the listing agent and creating a calendar event",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "string",
                            "description": "Unique property identifier"
                        },
                        "listing_url": {
                            "type": "string",
                            "description": "Zillow listing URL"
                        },
                        "requested_time": {
                            "type": "string",
                            "description": "ISO 8601 datetime string (e.g., '2025-11-15T14:00:00')"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier from session"
                        },
                        "user_name": {
                            "type": "string",
                            "description": "User's full name"
                        },
                        "user_email": {
                            "type": "string",
                            "description": "User's email address"
                        }
                    },
                    "required": ["property_id", "listing_url", "requested_time", "user_id", "user_name", "user_email"]
                }
            },
            {
                "name": "draft_offer",
                "url": f"{base_url}/api/tools/draft-offer",
                "description": "Generate a purchase agreement with specified terms and send for e-signature via Docusign",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "property_id": {
                            "type": "string",
                            "description": "Unique property identifier"
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
                            "description": "Number of days until closing (e.g., 14, 30, 45)"
                        },
                        "financing_type": {
                            "type": "string",
                            "description": "Type of financing: 'cash', 'conventional', or 'fha'",
                            "enum": ["cash", "conventional", "fha"]
                        },
                        "contingencies": {
                            "type": "array",
                            "items": {
                                "type": "string",
                                "enum": ["inspection", "appraisal", "financing"]
                            },
                            "description": "List of contingencies to include"
                        },
                        "user_id": {
                            "type": "string",
                            "description": "User identifier from session"
                        },
                        "user_email": {
                            "type": "string",
                            "description": "User's email address for Docusign"
                        }
                    },
                    "required": ["property_id", "address", "offer_price", "closing_days", "financing_type", "user_id", "user_email"]
                }
            }
        ]
    }
    
    return config

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/update_vapi_config.py https://your-domain.vercel.app")
        print()
        print("Example:")
        print("  python scripts/update_vapi_config.py https://counter-ai.vercel.app")
        sys.exit(1)
    
    base_url = sys.argv[1]
    
    # Validate URL format
    if not base_url.startswith('http'):
        print("❌ Error: URL must start with http:// or https://")
        sys.exit(1)
    
    config = generate_vapi_config(base_url)
    
    print("=" * 80)
    print("VAPI TOOL CONFIGURATION")
    print("=" * 80)
    print()
    print("Copy this configuration to your Vapi assistant:")
    print()
    print(json.dumps(config, indent=2))
    print()
    print("=" * 80)
    print()
    print("Steps to update Vapi:")
    print("  1. Go to https://dashboard.vapi.ai")
    print("  2. Navigate to your Counter AI assistant")
    print("  3. Go to the 'Functions' or 'Tools' section")
    print("  4. Replace the existing configuration with the above JSON")
    print("  5. Save the assistant")
    print()
    print("Tool URLs:")
    for func in config["functions"]:
        print(f"  - {func['name']}: {func['url']}")
    print()
    print("=" * 80)

if __name__ == "__main__":
    main()
