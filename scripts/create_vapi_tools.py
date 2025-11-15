#!/usr/bin/env python3
"""
Create VAPI tools programmatically using the VAPI API.

This script sends the tool configurations to VAPI to create/update tools.

Usage:
    python3 scripts/create_vapi_tools.py
"""
import json
import sys
import os
from pathlib import Path

# Add parent directory to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))

from config.settings import settings
import httpx

def load_tools_config():
    """Load tools configuration from JSON file."""
    config_path = Path(__file__).parent.parent / "vapi_tools_config.json"
    
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    return config["tools"]

def create_tool_via_api(tool_config, api_key, assistant_id=None):
    """
    Create a tool via VAPI API.
    
    Args:
        tool_config: Tool configuration dict
        api_key: VAPI API key
        assistant_id: Optional assistant ID (if creating for specific assistant)
    
    Returns:
        Response from API
    """
    url = "https://api.vapi.ai/tool"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Prepare payload
    payload = tool_config
    
    # If assistant_id provided, add it to payload
    if assistant_id:
        payload["assistantId"] = assistant_id
    
    print(f"Creating tool: {tool_config['function']['name']}...")
    print(f"  URL: {tool_config['server']['url']}")
    
    try:
        response = httpx.post(url, json=payload, headers=headers, timeout=30.0)
        response.raise_for_status()
        
        result = response.json()
        print(f"  ✅ Success! Tool ID: {result.get('id', 'N/A')}")
        return result
        
    except httpx.HTTPStatusError as e:
        print(f"  ❌ Error: {e.response.status_code}")
        print(f"  Response: {e.response.text}")
        return None
    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return None

def main():
    """Main function to create all tools."""
    print("=" * 80)
    print("VAPI TOOLS CREATION")
    print("=" * 80)
    print()
    
    # Get VAPI API key from environment
    api_key = os.getenv("VAPI_API_KEY") or settings.get("vapi_private_key", "")
    
    if not api_key:
        print("❌ Error: VAPI_API_KEY not found in environment")
        print()
        print("Set it with:")
        print("  export VAPI_API_KEY=your_vapi_private_key")
        print()
        print("Or add to .env file:")
        print("  VAPI_API_KEY=your_vapi_private_key")
        sys.exit(1)
    
    # Get assistant ID (optional)
    assistant_id = os.getenv("VAPI_ASSISTANT_ID", "")
    
    # Load tools configuration
    print("Loading tools configuration...")
    tools = load_tools_config()
    print(f"Found {len(tools)} tools to create")
    print()
    
    # Create each tool
    results = []
    for tool in tools:
        result = create_tool_via_api(tool, api_key, assistant_id if assistant_id else None)
        results.append(result)
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()
    
    successful = [r for r in results if r is not None]
    failed = [r for r in results if r is None]
    
    print(f"✅ Successfully created: {len(successful)}/{len(tools)}")
    print(f"❌ Failed: {len(failed)}/{len(tools)}")
    print()
    
    if successful:
        print("Created tools:")
        for tool, result in zip(tools, results):
            if result:
                print(f"  ✅ {tool['function']['name']} - ID: {result.get('id', 'N/A')}")
    
    if failed:
        print("Failed tools:")
        for tool, result in zip(tools, results):
            if not result:
                print(f"  ❌ {tool['function']['name']}")
    
    print()
    print("=" * 80)
    print()
    print("Next steps:")
    print("  1. Go to https://dashboard.vapi.ai")
    print("  2. Open your assistant")
    print("  3. Go to Functions/Tools section")
    print("  4. Verify all tools are listed")
    print("  5. Test with a phone call")
    print()

if __name__ == "__main__":
    main()

