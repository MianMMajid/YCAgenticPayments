#!/usr/bin/env python3
"""Verification script to check project setup."""
import sys
import os

def check_directories():
    """Check if all required directories exist."""
    required_dirs = [
        'api',
        'api/tools',
        'models',
        'services',
        'config'
    ]
    
    print("Checking directories...")
    for dir_path in required_dirs:
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            print(f"  ✓ {dir_path}")
        else:
            print(f"  ✗ {dir_path} - MISSING")
            return False
    return True

def check_files():
    """Check if all required files exist."""
    required_files = [
        'requirements.txt',
        'vercel.json',
        '.env.example',
        '.gitignore',
        'README.md',
        'api/main.py',
        'config/settings.py'
    ]
    
    print("\nChecking files...")
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - MISSING")
            return False
    return True

def check_imports():
    """Check if core modules can be imported."""
    print("\nChecking imports...")
    try:
        from api.main import app
        print("  ✓ FastAPI app")
    except Exception as e:
        print(f"  ✗ FastAPI app - {e}")
        return False
    
    try:
        from config.settings import settings
        print("  ✓ Settings")
    except Exception as e:
        print(f"  ✗ Settings - {e}")
        return False
    
    return True

def main():
    """Run all verification checks."""
    print("=" * 50)
    print("Counter AI Real Estate Broker - Setup Verification")
    print("=" * 50)
    
    checks = [
        check_directories(),
        check_files(),
        check_imports()
    ]
    
    print("\n" + "=" * 50)
    if all(checks):
        print("✓ All checks passed! Setup is complete.")
        print("=" * 50)
        return 0
    else:
        print("✗ Some checks failed. Please review the output above.")
        print("=" * 50)
        return 1

if __name__ == "__main__":
    sys.exit(main())
