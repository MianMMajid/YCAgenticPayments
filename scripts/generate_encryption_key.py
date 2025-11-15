#!/usr/bin/env python3
"""
Generate encryption key for PII fields

This script generates a Fernet encryption key that should be stored
as the ENCRYPTION_KEY environment variable in Vercel.

Usage:
    python scripts/generate_encryption_key.py
"""

from cryptography.fernet import Fernet

def main():
    key = Fernet.generate_key()
    key_str = key.decode()
    
    print("=" * 60)
    print("ENCRYPTION KEY GENERATED")
    print("=" * 60)
    print()
    print("Copy this key and add it to Vercel:")
    print()
    print(f"  {key_str}")
    print()
    print("Command to add to Vercel:")
    print()
    print(f"  vercel env add ENCRYPTION_KEY production")
    print()
    print("⚠️  IMPORTANT:")
    print("  - Store this key securely (password manager)")
    print("  - Never commit this key to git")
    print("  - If lost, encrypted data cannot be recovered")
    print("  - Rotate this key every 90 days")
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()
