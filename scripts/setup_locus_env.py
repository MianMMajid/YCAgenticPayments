#!/usr/bin/env python3
"""
Setup script to add Locus credentials to .env file.

This script will:
1. Check if .env exists
2. Add/update Locus configuration
3. Preserve existing settings
"""
import os
import re
from pathlib import Path

# Locus Configuration
LOCUS_CONFIG = {
    # Main Wallet
    "LOCUS_WALLET_ADDRESS": "0x45B876546953Fe28C66022b48310dFbc1c2Fec47",
    "LOCUS_WALLET_PRIVATE_KEY": "0xfd7875c20892f146272f8733a5d037d24da4ceffe8b59d90dc30709aea2bb0e1",
    "LOCUS_CHAIN_ID": "8453",
    "LOCUS_WALLET_NAME": "Yc-MakeEmPay",
    
    # Locus API Key
    "LOCUS_API_KEY": "locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG",
    
    # Agent API Keys
    "LOCUS_AGENT_TITLE_KEY": "locus_dev_exC56yN_i7sWO7HURNBrYC_KqE7KHEaG",
    "LOCUS_AGENT_INSPECTION_KEY": "locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd",
    "LOCUS_AGENT_APPRAISAL_KEY": "locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk",
    "LOCUS_AGENT_UNDERWRITING_KEY": "locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl",
    
    # Budgets
    "AGENT_TITLE_BUDGET": "0.03",
    "AGENT_INSPECTION_BUDGET": "0.012",
    "AGENT_APPRAISAL_BUDGET": "0.010",
    "AGENT_UNDERWRITING_BUDGET": "0.019",
    
    # Mock Services
    "LANDAMERICA_SERVICE": "http://localhost:5001/landamerica/title-search",
    "AMERISPEC_SERVICE": "http://localhost:5001/amerispec/inspection",
    "CORELOGIC_SERVICE": "http://localhost:5001/corelogic/valuation",
    "FANNIEMAE_SERVICE": "http://localhost:5001/fanniemae/verify",
    
    # Mode
    "DEMO_MODE": "true",
    "USE_MOCK_SERVICES": "true",
}

# Note: No Policy Groups needed - just Agent IDs and wallets
# Agent IDs are already configured in update_agent_credentials.py


def update_env_file(env_path: Path):
    """Update .env file with Locus configuration."""
    env_content = ""
    existing_vars = set()
    
    # Read existing .env if it exists
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
            # Extract existing variable names
            for line in env_content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    var_name = line.split('=')[0].strip()
                    existing_vars.add(var_name)
    
    # Add Locus section header if not present
    if "# LOCUS" not in env_content:
        env_content += "\n\n# ============================================\n"
        env_content += "# LOCUS PAYMENT INFRASTRUCTURE\n"
        env_content += "# ============================================\n\n"
    
    # Update or add Locus variables
    lines = env_content.split('\n')
    new_lines = []
    in_locus_section = False
    locus_vars_written = set()
    
    for line in lines:
        # Check if we're in Locus section
        if "# LOCUS" in line or "LOCUS_" in line or "AGENT_" in line or "LANDAMERICA_SERVICE" in line:
            in_locus_section = True
        
        # Skip existing Locus variables (we'll add them fresh)
        if in_locus_section and '=' in line and not line.strip().startswith('#'):
            var_name = line.split('=')[0].strip()
            # Remove Policy Group IDs (not needed)
            if var_name.startswith(('LOCUS_POLICY_', 'locus_policy_')):
                continue  # Skip Policy Group IDs
            if var_name.startswith(('LOCUS_', 'AGENT_', 'LANDAMERICA_', 'AMERISPEC_', 'CORELOGIC_', 'FANNIEMAE_', 'DEMO_MODE', 'USE_MOCK_SERVICES')):
                continue  # Skip, we'll add it fresh
        
        new_lines.append(line)
    
    # Add all Locus configuration
    new_lines.append("\n# Main Wallet")
    for key, value in LOCUS_CONFIG.items():
        if key.startswith(('LOCUS_WALLET', 'LOCUS_CHAIN', 'LOCUS_API')):
            new_lines.append(f"{key}={value}")
    
    # Note: No Policy Groups needed - just Agent IDs and wallets
    new_lines.append("\n# Agent IDs & Keys (already configured)")
    
    for key, value in LOCUS_CONFIG.items():
        if 'AGENT' in key and 'KEY' in key:
            new_lines.append(f"{key}={value}")
    
    new_lines.append("\n# Budgets")
    for key, value in LOCUS_CONFIG.items():
        if 'BUDGET' in key:
            new_lines.append(f"{key}={value}")
    
    new_lines.append("\n# Mock Services")
    for key, value in LOCUS_CONFIG.items():
        if 'SERVICE' in key:
            new_lines.append(f"{key}={value}")
    
    new_lines.append("\n# Mode")
    for key, value in LOCUS_CONFIG.items():
        if 'MODE' in key:
            new_lines.append(f"{key}={value}")
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print(f"✅ Updated {env_path}")
    print("\n⚠️  REMEMBER: You still need to add Policy IDs and Agent IDs from Locus Dashboard!")
    print("   See docs/LOCUS_CREDENTIALS_SETUP.md for details")


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    
    print("=" * 60)
    print("LOCUS ENVIRONMENT SETUP")
    print("=" * 60)
    print(f"\nUpdating: {env_path}")
    
    if not env_path.exists():
        print(f"⚠️  .env file not found. Creating new one...")
        env_path.touch()
    
    update_env_file(env_path)
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Get Policy IDs from Locus Dashboard")
    print("2. Get Agent IDs from Locus Dashboard")
    print("3. Update .env file with those IDs")
    print("4. Set USE_MOCK_SERVICES=false when ready for production")


if __name__ == "__main__":
    main()

