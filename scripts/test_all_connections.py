#!/usr/bin/env python3
"""Test all API connections and services."""
import asyncio
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from models.database import get_db
from services.cache_client import CacheClient
from services.rentcast_client import RentCastClient
from services.docusign_client import DocusignClient
from services.email_client import EmailClient
import httpx
import openai

# Test results
results = {
    "database": {"status": "pending", "message": ""},
    "redis": {"status": "pending", "message": ""},
    "rentcast": {"status": "pending", "message": ""},
    "docusign": {"status": "pending", "message": ""},
    "apify": {"status": "pending", "message": ""},
    "openai": {"status": "pending", "message": ""},
    "sendgrid": {"status": "pending", "message": ""},
    "google_calendar": {"status": "pending", "message": ""},
}


def test_database():
    """Test database connection."""
    try:
        from sqlalchemy import text
        db = next(get_db())
        # Try a simple query
        result = db.execute(text("SELECT 1"))
        result.fetchone()
        results["database"]["status"] = "✅ PASS"
        results["database"]["message"] = "Database connection successful"
        db.close()
    except Exception as e:
        results["database"]["status"] = "❌ FAIL"
        results["database"]["message"] = f"Database error: {str(e)}"


def test_redis():
    """Test Redis connection."""
    try:
        cache = CacheClient()
        if cache.client is None:
            results["redis"]["status"] = "❌ FAIL"
            results["redis"]["message"] = "Redis client not initialized"
            return
        # Test set and get
        cache.set("test_key", "test_value", ttl=10)
        value = cache.get("test_key")
        if value == "test_value":
            cache.delete("test_key")  # Cleanup
            results["redis"]["status"] = "✅ PASS"
            results["redis"]["message"] = "Redis connection successful"
        else:
            results["redis"]["status"] = "❌ FAIL"
            results["redis"]["message"] = "Redis test failed: value mismatch"
    except Exception as e:
        results["redis"]["status"] = "❌ FAIL"
        results["redis"]["message"] = f"Redis error: {str(e)}"


async def test_rentcast():
    """Test RentCast API."""
    try:
        client = RentCastClient(api_key=settings.rentcast_api_key)
        # Test with a simple search (Baltimore)
        response = await client.search_listings(
            city="Baltimore",
            state="MD",
            max_price=500000,
            limit=1
        )
        if response and isinstance(response, list):
            # Verify it's real data, not placeholder
            if len(response) > 0:
                prop = response[0]
                # RentCast uses 'formattedAddress' or 'addressLine1', not 'address'
                address = prop.get('formattedAddress') or prop.get('addressLine1') or 'N/A'
                has_real_data = any(key in prop for key in ['formattedAddress', 'addressLine1', 'city', 'listPrice', 'price'])
                if has_real_data and address != 'N/A':
                    results["rentcast"]["status"] = "✅ PASS"
                    results["rentcast"]["message"] = f"RentCast API working (found {len(response)} properties, sample: {address[:40]}...)"
                else:
                    results["rentcast"]["status"] = "⚠️  WARN"
                    results["rentcast"]["message"] = "RentCast returned data but structure unexpected"
            else:
                results["rentcast"]["status"] = "⚠️  WARN"
                results["rentcast"]["message"] = "RentCast API responded but no properties found"
        else:
            results["rentcast"]["status"] = "⚠️  WARN"
            results["rentcast"]["message"] = "RentCast API responded but no properties found"
    except Exception as e:
        results["rentcast"]["status"] = "❌ FAIL"
        results["rentcast"]["message"] = f"RentCast error: {str(e)}"


async def test_docusign():
    """Test DocuSign API authentication."""
    try:
        client = DocusignClient(
            integration_key=settings.docusign_integration_key,
            secret_key=settings.docusign_secret_key,
            account_id=settings.docusign_account_id
        )
        # Try to get an access token
        token = await client._get_access_token()
        if token and len(token) > 50:  # Real tokens are long
            # Verify token format (JWT tokens are base64 encoded)
            token_preview = token[:20] + "..." if len(token) > 20 else token
            results["docusign"]["status"] = "✅ PASS"
            results["docusign"]["message"] = f"DocuSign authentication successful (token: {token_preview})"
        else:
            results["docusign"]["status"] = "❌ FAIL"
            results["docusign"]["message"] = "DocuSign authentication failed - invalid token"
    except Exception as e:
        results["docusign"]["status"] = "❌ FAIL"
        results["docusign"]["message"] = f"DocuSign error: {str(e)}"


async def test_apify():
    """Test Apify API."""
    try:
        # Test API token by checking account info
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                "https://api.apify.com/v2/users/me",
                headers={"Authorization": f"Bearer {settings.apify_api_token}"},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                # Verify it's real account data
                username = data.get('username') or data.get('data', {}).get('username')
                if username and username != 'unknown':
                    results["apify"]["status"] = "✅ PASS"
                    results["apify"]["message"] = f"Apify API working (user: {username}, plan: {data.get('data', {}).get('plan', 'N/A')})"
                else:
                    results["apify"]["status"] = "⚠️  WARN"
                    results["apify"]["message"] = f"Apify API responded but user data incomplete: {data}"
            else:
                results["apify"]["status"] = "❌ FAIL"
                results["apify"]["message"] = f"Apify API error: {response.status_code} - {response.text[:100]}"
    except Exception as e:
        results["apify"]["status"] = "❌ FAIL"
        results["apify"]["message"] = f"Apify error: {str(e)}"


async def test_openai():
    """Test OpenAI API."""
    try:
        client = openai.OpenAI(api_key=settings.openai_api_key)
        # Test with a simple completion
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say only the word 'test' and nothing else"}],
            max_tokens=5
        )
        if response.choices and len(response.choices) > 0:
            content = response.choices[0].message.content
            # Verify we got a real response
            if content and len(content.strip()) > 0:
                results["openai"]["status"] = "✅ PASS"
                results["openai"]["message"] = f"OpenAI API working (response: '{content.strip()}', tokens: {response.usage.total_tokens if response.usage else 'N/A'})"
            else:
                results["openai"]["status"] = "❌ FAIL"
                results["openai"]["message"] = "OpenAI API returned empty response"
        else:
            results["openai"]["status"] = "❌ FAIL"
            results["openai"]["message"] = "OpenAI API returned no choices"
    except Exception as e:
        results["openai"]["status"] = "❌ FAIL"
        results["openai"]["message"] = f"OpenAI error: {str(e)}"


async def test_sendgrid():
    """Test SendGrid API."""
    try:
        # Test API key by checking account info
        async with httpx.AsyncClient() as http_client:
            response = await http_client.get(
                "https://api.sendgrid.com/v3/user/profile",
                headers={"Authorization": f"Bearer {settings.sendgrid_api_key}"},
                timeout=10.0
            )
            if response.status_code == 200:
                data = response.json()
                # SendGrid /v3/user/profile only returns type and userid, not email
                # This is normal - the API key is valid if we get 200
                userid = data.get('userid')
                if userid:
                    results["sendgrid"]["status"] = "✅ PASS"
                    results["sendgrid"]["message"] = f"SendGrid API working (userid: {userid}, type: {data.get('type', 'N/A')})"
                else:
                    results["sendgrid"]["status"] = "⚠️  WARN"
                    results["sendgrid"]["message"] = f"SendGrid API responded but userid missing: {data}"
            else:
                error_text = response.text[:200] if response.text else "No error message"
                results["sendgrid"]["status"] = "❌ FAIL"
                results["sendgrid"]["message"] = f"SendGrid API error: {response.status_code} - {error_text}"
    except Exception as e:
        results["sendgrid"]["status"] = "❌ FAIL"
        results["sendgrid"]["message"] = f"SendGrid error: {str(e)}"


def test_google_calendar():
    """Test Google Calendar credentials format."""
    try:
        if settings.google_calendar_client_id and settings.google_calendar_client_secret:
            # Just verify the format is correct
            if "apps.googleusercontent.com" in settings.google_calendar_client_id:
                results["google_calendar"]["status"] = "✅ PASS"
                results["google_calendar"]["message"] = "Google Calendar credentials format valid (OAuth flow required for full test)"
            else:
                results["google_calendar"]["status"] = "⚠️  WARN"
                results["google_calendar"]["message"] = "Google Calendar client ID format may be incorrect"
        else:
            results["google_calendar"]["status"] = "❌ FAIL"
            results["google_calendar"]["message"] = "Google Calendar credentials not configured"
    except Exception as e:
        results["google_calendar"]["status"] = "❌ FAIL"
        results["google_calendar"]["message"] = f"Google Calendar error: {str(e)}"


async def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Testing All API Connections")
    print("=" * 60)
    print()
    
    # Run sync tests first
    test_database()
    test_redis()
    test_google_calendar()
    
    # Run async tests
    await asyncio.gather(
        test_rentcast(),
        test_docusign(),
        test_apify(),
        test_openai(),
        test_sendgrid(),
    )
    
    # Print results
    print("📊 Test Results:")
    print("-" * 60)
    for service, result in results.items():
        status = result["status"]
        message = result["message"]
        print(f"{status} {service.upper():<20} {message}")
    print("-" * 60)
    
    # Summary
    passed = sum(1 for r in results.values() if "✅" in r["status"])
    total = len(results)
    print(f"\n✅ Passed: {passed}/{total}")
    
    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed. Check the messages above.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)

