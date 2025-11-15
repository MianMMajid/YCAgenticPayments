#!/usr/bin/env python3
"""
Update .env file with Locus agent credentials.

This script updates the agent IDs and keys for Title and Inspection agents.
"""
import os
import re
from pathlib import Path

# Agent credentials provided
AGENT_CREDENTIALS = {
    # Title Search Agent (LandAmerica)
    "LOCUS_AGENT_TITLE_ID": "ooeju0aot520uv7dd77nr7d5r",
    "LOCUS_AGENT_TITLE_KEY": "locus_dev_o4LU_j8-VWgDiOm_MFiA1u4M97rC0KIp",  # Updated 2025-01-16
    
    # Inspection Agent
    "LOCUS_AGENT_INSPECTION_ID": "2ss8gjcf4q8g05hueor4ftnuu7",
    "LOCUS_AGENT_INSPECTION_KEY": "locus_dev_NeMbZAgJFwpWXIrGaiZQTWm-Fhnpsxfd",
    
    # Appraisal Agent
    "LOCUS_AGENT_APPRAISAL_ID": "7qictfjj57f973mfp0i4ku209k",
    "LOCUS_AGENT_APPRAISAL_KEY": "locus_dev_y7wmTdasNBO4gCsFxWJnQ8bo0IROSOKk",
    
    # Underwriting Agent
    "LOCUS_AGENT_UNDERWRITING_ID": "27fqhc1mtsd97q63bddaqoutmv",
    "LOCUS_AGENT_UNDERWRITING_KEY": "locus_dev_cRKUMxRuSSjqaQzRgdbdhm5Jz2-szqVl",
}

# Service Recipient Wallet Addresses
SERVICE_RECIPIENTS = {
    "SERVICE_RECIPIENT_LANDAMERICA": "0x86752df5821648a76c3f9e15766cca3d5226903a",  # Updated from Locus dashboard
    "SERVICE_RECIPIENT_AMERISPEC": "0x0c8115aac3551a4d5282b9dc0aa8721b80f341bc",  # Updated from Locus dashboard
    "SERVICE_RECIPIENT_CORELOGIC": "0xbf951bed631ddd22f2461c67539708861050c060",  # Updated from Locus dashboard
    "SERVICE_RECIPIENT_FANNIEMAE": "0x5a9a151475b9e7fe2a74b4f8b5277de4e8030953",  # Updated from Locus dashboard
}


def update_env_file(env_path: Path):
    """Update .env file with agent credentials."""
    env_content = ""
    existing_vars = {}
    
    # Read existing .env if it exists
    if env_path.exists():
        with open(env_path, 'r') as f:
            env_content = f.read()
            # Extract existing variables
            for line in env_content.split('\n'):
                if '=' in line and not line.strip().startswith('#'):
                    parts = line.split('=', 1)
                    if len(parts) == 2:
                        var_name = parts[0].strip()
                        var_value = parts[1].strip()
                        existing_vars[var_name] = var_value
    
    # Update or add agent credentials
    lines = env_content.split('\n')
    new_lines = []
    updated_vars = set()
    
    for line in lines:
        # Check if this line contains an agent credential we need to update
        should_skip = False
        for var_name in AGENT_CREDENTIALS.keys():
            if line.startswith(f"{var_name}="):
                # Update this line
                new_lines.append(f"{var_name}={AGENT_CREDENTIALS[var_name]}")
                updated_vars.add(var_name)
                should_skip = True
                break
        
        if not should_skip:
            new_lines.append(line)
    
    # Add any missing agent credentials
    for var_name, var_value in AGENT_CREDENTIALS.items():
        if var_name not in updated_vars:
            # Find the right place to insert (after other agent vars or in agent section)
            inserted = False
            for i, line in enumerate(new_lines):
                if "LOCUS_AGENT" in line or "# Agent" in line:
                    # Insert after this line
                    new_lines.insert(i + 1, f"{var_name}={var_value}")
                    inserted = True
                    break
            
            if not inserted:
                # Add at the end
                new_lines.append(f"{var_name}={var_value}")
    
    # Update or add service recipient addresses
    for line in lines:
        should_skip = False
        for var_name in SERVICE_RECIPIENTS.keys():
            if line.startswith(f"{var_name}="):
                should_skip = True
                break
        if not should_skip:
            new_lines.append(line)
    
    # Add service recipient addresses if not present
    recipient_vars_written = set()
    for line in new_lines:
        for var_name in SERVICE_RECIPIENTS.keys():
            if line.startswith(f"{var_name}="):
                recipient_vars_written.add(var_name)
                break
    
    # Add missing recipient addresses
    if SERVICE_RECIPIENTS:
        # Find where to insert (after service URLs or at end)
        inserted = False
        for i, line in enumerate(new_lines):
            if "SERVICE_RECIPIENT" in line or ("FANNIEMAE_SERVICE" in line and "SERVICE_RECIPIENT" not in '\n'.join(new_lines[:i+10])):
                # Insert after service URLs
                new_lines.insert(i + 1, "\n# Service Recipient Wallet Addresses")
                for var_name, var_value in SERVICE_RECIPIENTS.items():
                    if var_name not in recipient_vars_written:
                        new_lines.insert(i + 2, f"{var_name}={var_value}")
                inserted = True
                break
        
        if not inserted:
            # Add at the end
            new_lines.append("\n# Service Recipient Wallet Addresses")
            for var_name, var_value in SERVICE_RECIPIENTS.items():
                if var_name not in recipient_vars_written:
                    new_lines.append(f"{var_name}={var_value}")
    
    # Write updated content
    with open(env_path, 'w') as f:
        f.write('\n'.join(new_lines))
    
    print(f"✅ Updated {env_path}")
    print("\nUpdated Agent Credentials:")
    for var_name, var_value in AGENT_CREDENTIALS.items():
        print(f"  {var_name}={var_value[:20]}..." if len(var_value) > 20 else f"  {var_name}={var_value}")
    
    print("\nUpdated Service Recipient Wallets:")
    for var_name, var_value in SERVICE_RECIPIENTS.items():
        print(f"  {var_name}={var_value}")


def main():
    """Main function."""
    project_root = Path(__file__).parent.parent
    env_path = project_root / ".env"
    
    print("=" * 70)
    print("UPDATING LOCUS AGENT CREDENTIALS")
    print("=" * 70)
    print(f"\nUpdating: {env_path}")
    
    if not env_path.exists():
        print(f"⚠️  .env file not found. Creating new one...")
        env_path.touch()
    
    update_env_file(env_path)
    
    print("\n" + "=" * 70)
    print("✅ Update complete!")
    print("=" * 70)
    print("\nUpdated credentials:")
    print("  ✓ Title Search Agent ID and Key")
    print("  ✓ Inspection Agent ID and Key")
    print("  ✓ Appraisal Agent ID and Key")
    print("  ✓ Underwriting Agent ID and Key")
    print("  ✓ LandAmerica Recipient Wallet")
    print("  ✓ AmeriSpec Recipient Wallet")
    print("  ✓ CoreLogic Recipient Wallet")
    print("  ✓ Fannie Mae Recipient Wallet")
    print("\nNote: You still need to add:")
    print("  - Policy Group IDs (from Locus Dashboard)")


if __name__ == "__main__":
    main()

