#!/usr/bin/env python3
"""
Helper script to guide you in getting Locus Policy Group IDs and Agent IDs.

This script provides step-by-step instructions for finding the IDs you need
from the Locus Dashboard.
"""
import os
from pathlib import Path

def print_instructions():
    """Print step-by-step instructions for getting Locus IDs."""
    
    print("=" * 70)
    print("HOW TO GET LOCUS POLICY GROUP IDs AND AGENT IDs")
    print("=" * 70)
    print()
    
    print("📍 STEP 1: Get Policy Group IDs")
    print("-" * 70)
    print("1. Go to: https://app.paywithlocus.com/dashboard/agents")
    print("2. Look for 'Policy Groups' section or navigate to Policies")
    print("3. Find each of these policy groups:")
    print()
    print("   a) LandAmerica Title Verification Policy")
    print("      → Copy the Policy Group ID (format: policy_xxxxx)")
    print("      → Add to .env as: LOCUS_POLICY_TITLE_ID=policy_xxxxx")
    print()
    print("   b) AmeriSpec Home Inspection Policy")
    print("      → Copy the Policy Group ID")
    print("      → Add to .env as: LOCUS_POLICY_INSPECTION_ID=policy_xxxxx")
    print()
    print("   c) CoreLogic Property Valuation Policy")
    print("      → Copy the Policy Group ID")
    print("      → Add to .env as: LOCUS_POLICY_APPRAISAL_ID=policy_xxxxx")
    print()
    print("   d) Fannie Mae Loan Verification Policy")
    print("      → Copy the Policy Group ID")
    print("      → Add to .env as: LOCUS_POLICY_UNDERWRITING_ID=policy_xxxxx")
    print()
    
    print("📍 STEP 2: Get Agent IDs")
    print("-" * 70)
    print("1. Go to: https://app.paywithlocus.com/dashboard/agents")
    print("2. Find each of these agents:")
    print()
    print("   a) Title Search Agent")
    print("      → Copy the Agent ID (format: agent_xxxxx)")
    print("      → Add to .env as: LOCUS_AGENT_TITLE_ID=agent_xxxxx")
    print()
    print("   b) Inspection Agent")
    print("      → Copy the Agent ID")
    print("      → Add to .env as: LOCUS_AGENT_INSPECTION_ID=agent_xxxxx")
    print()
    print("   c) Appraisal Agent")
    print("      → Copy the Agent ID")
    print("      → Add to .env as: LOCUS_AGENT_APPRAISAL_ID=agent_xxxxx")
    print()
    print("   d) Underwriting Agent")
    print("      → Copy the Agent ID")
    print("      → Add to .env as: LOCUS_AGENT_UNDERWRITING_ID=agent_xxxxx")
    print()
    
    print("📍 STEP 3: Update .env File")
    print("-" * 70)
    env_path = Path(__file__).parent.parent / ".env"
    print(f"1. Open: {env_path}")
    print("2. Find the placeholder values (ending with [get_from_locus])")
    print("3. Replace with the actual IDs you copied")
    print("4. Save the file")
    print()
    
    print("📍 STEP 4: Verify Configuration")
    print("-" * 70)
    print("Run this command to verify your .env has all required values:")
    print()
    print("  python3 scripts/verify_locus_config.py")
    print()
    
    print("=" * 70)
    print("✅ Once you have all IDs, your Locus integration will be complete!")
    print("=" * 70)
    print()


def check_current_env():
    """Check what's currently in .env file."""
    env_path = Path(__file__).parent.parent / ".env"
    
    if not env_path.exists():
        print("⚠️  .env file not found. Run setup_locus_env.py first.")
        return
    
    print("\n📋 Current .env Status:")
    print("-" * 70)
    
    with open(env_path, 'r') as f:
        content = f.read()
    
    # Check for placeholders
    placeholders = [
        "LOCUS_POLICY_TITLE_ID",
        "LOCUS_POLICY_INSPECTION_ID",
        "LOCUS_POLICY_APPRAISAL_ID",
        "LOCUS_POLICY_UNDERWRITING_ID",
        "LOCUS_AGENT_TITLE_ID",
        "LOCUS_AGENT_INSPECTION_ID",
        "LOCUS_AGENT_APPRAISAL_ID",
        "LOCUS_AGENT_UNDERWRITING_ID"
    ]
    
    missing = []
    found = []
    
    for placeholder in placeholders:
        if placeholder in content:
            # Check if it's a placeholder or real value
            lines = content.split('\n')
            for line in lines:
                if line.startswith(placeholder):
                    if '[get_from_locus]' in line or '[' in line:
                        missing.append(placeholder)
                    else:
                        found.append(placeholder)
                    break
    
    if found:
        print("✅ Found IDs:")
        for item in found:
            print(f"   ✓ {item}")
    
    if missing:
        print("\n⚠️  Still need:")
        for item in missing:
            print(f"   ✗ {item}")
    
    print()


if __name__ == "__main__":
    print_instructions()
    check_current_env()

