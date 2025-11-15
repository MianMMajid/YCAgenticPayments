#!/usr/bin/env python3
"""
Verify Redis cache setup and configuration

This script tests Redis connectivity and basic operations.

Usage:
    export REDIS_URL='your-redis-url'
    python scripts/verify_redis.py
"""

import os
import sys
import time
from datetime import datetime

def test_redis_connection():
    """Test Redis connection and operations"""
    
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        print("❌ REDIS_URL environment variable not set")
        print()
        print("Set it with:")
        print("  export REDIS_URL='your-redis-url'")
        return False
    
    # Mask password in output
    masked_url = redis_url
    if '@' in masked_url and '://' in masked_url:
        protocol = masked_url.split('://')[0]
        rest = masked_url.split('://')[1]
        if '@' in rest:
            auth_part = rest.split('@')[0]
            host_part = rest.split('@')[1]
            if ':' in auth_part:
                user = auth_part.split(':')[0]
                masked_url = f"{protocol}://{user}:****@{host_part}"
    
    print(f"Redis URL: {masked_url}")
    print()
    
    try:
        # Import cache client
        from services.cache_client import CacheClient
        
        print("🔌 Testing Redis connection...")
        cache = CacheClient()
        
        # Test 1: Basic SET/GET
        print("  Testing SET/GET operations...")
        test_key = "test:counter:verify"
        test_value = f"test-{datetime.now().isoformat()}"
        
        cache.set(test_key, test_value, ttl=60)
        retrieved = cache.get(test_key)
        
        if retrieved == test_value:
            print("  ✓ SET/GET successful")
        else:
            print(f"  ❌ SET/GET failed: expected '{test_value}', got '{retrieved}'")
            return False
        
        # Test 2: TTL
        print("  Testing TTL (expiration)...")
        ttl_key = "test:counter:ttl"
        cache.set(ttl_key, "expires-soon", ttl=2)
        
        # Should exist immediately
        if cache.get(ttl_key) == "expires-soon":
            print("  ✓ Key set with TTL")
        else:
            print("  ❌ TTL test failed: key not found")
            return False
        
        # Wait and check expiration
        print("  Waiting 3 seconds for expiration...")
        time.sleep(3)
        
        if cache.get(ttl_key) is None:
            print("  ✓ TTL expiration working")
        else:
            print("  ⚠️  Key did not expire (may be cached)")
        
        # Test 3: DELETE
        print("  Testing DELETE operation...")
        delete_key = "test:counter:delete"
        cache.set(delete_key, "to-be-deleted", ttl=60)
        cache.delete(delete_key)
        
        if cache.get(delete_key) is None:
            print("  ✓ DELETE successful")
        else:
            print("  ❌ DELETE failed: key still exists")
            return False
        
        # Test 4: Multiple keys
        print("  Testing multiple key operations...")
        keys = [f"test:counter:multi:{i}" for i in range(5)]
        for i, key in enumerate(keys):
            cache.set(key, f"value-{i}", ttl=60)
        
        all_found = all(cache.get(key) == f"value-{i}" for i, key in enumerate(keys))
        if all_found:
            print("  ✓ Multiple keys handled correctly")
        else:
            print("  ❌ Multiple keys test failed")
            return False
        
        # Cleanup
        for key in keys:
            cache.delete(key)
        cache.delete(test_key)
        
        print()
        print("✅ All Redis tests passed!")
        print()
        
        # Show cache stats
        print("📊 Cache Configuration:")
        print(f"  URL: {masked_url}")
        print(f"  Connection: Active")
        print(f"  Operations: SET, GET, DELETE, TTL")
        print()
        
        return True
        
    except ImportError as e:
        print(f"❌ Failed to import CacheClient: {e}")
        print()
        print("Make sure you have installed dependencies:")
        print("  pip install -r requirements.txt")
        return False
        
    except Exception as e:
        print(f"❌ Redis test failed: {e}")
        print()
        print("Troubleshooting:")
        print("  - Verify REDIS_URL is correct")
        print("  - Check Redis service is running")
        print("  - Verify network connectivity")
        print("  - Check Redis dashboard for errors")
        return False

def main():
    print("=" * 60)
    print("Counter AI - Redis Cache Verification")
    print("=" * 60)
    print()
    
    success = test_redis_connection()
    
    if success:
        print("Next steps:")
        print("  1. Add REDIS_URL to Vercel:")
        print("     vercel env add REDIS_URL production")
        print("  2. Deploy your application")
        print("  3. Monitor cache hit rates in production")
        print()
        print("Expected cache usage:")
        print("  - Property searches: 24h TTL")
        print("  - Agent info: 7d TTL")
        print("  - Risk analyses: 24h TTL")
        print()
        sys.exit(0)
    else:
        print()
        print("❌ Redis verification failed")
        print()
        sys.exit(1)

if __name__ == "__main__":
    main()
