#!/usr/bin/env python3
"""
Switch to Production Mode

This script updates .env to switch from demo mode to production mode.
"""
import os
import re
from pathlib import Path

def update_env_for_production():
    """Update .env file for production mode."""
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print("❌ .env file not found!")
        return False
    
    # Read current .env
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Update USE_MOCK_SERVICES
    content = re.sub(
        r'^USE_MOCK_SERVICES=.*$',
        'USE_MOCK_SERVICES=false',
        content,
        flags=re.MULTILINE
    )
    
    # Update DEMO_MODE
    content = re.sub(
        r'^DEMO_MODE=.*$',
        'DEMO_MODE=false',
        content,
        flags=re.MULTILINE
    )
    
    # If not found, add them
    if 'USE_MOCK_SERVICES=' not in content:
        content += '\nUSE_MOCK_SERVICES=false\n'
    if 'DEMO_MODE=' not in content:
        content += '\nDEMO_MODE=false\n'
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write(content)
    
    print("✅ Updated .env for production mode:")
    print("   USE_MOCK_SERVICES=false")
    print("   DEMO_MODE=false")
    print()
    print("⚠️  Remember to:")
    print("   1. Find Locus API endpoint URL (via browser DevTools)")
    print("   2. Update LOCUS_API_BASE_URL in .env")
    print("   3. Update service URLs to real endpoints (when available)")
    print("   4. Test with: python3 scripts/test_locus_a2a_payment.py")
    
    return True

if __name__ == "__main__":
    print("=" * 70)
    print("SWITCHING TO PRODUCTION MODE")
    print("=" * 70)
    print()
    update_env_for_production()

