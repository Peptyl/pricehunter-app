#!/usr/bin/env python3
"""
PriceHunter Backend - End-to-End Test Script
Tests the full flow: Auth → Subscription → Deals Access
"""

import requests
import json
import sys

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"

def test_endpoint(name, method, path, expected_status=200, headers=None, data=None):
    """Test an API endpoint"""
    url = f"{BASE_URL}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=data, timeout=10)
        else:
            return False, f"Unknown method: {method}"
        
        success = resp.status_code == expected_status
        return success, f"{resp.status_code} - {resp.text[:100] if resp.text else 'OK'}"
    except Exception as e:
        return False, str(e)

def main():
    print("=" * 60)
    print("PriceHunter Backend - E2E Test Suite")
    print("=" * 60)
    print(f"Testing: {BASE_URL}")
    print()
    
    tests = [
        ("Health Check", "GET", "/health", 200),
        ("API Root", "GET", "/", 200),
        ("Get Perfumes (Public)", "GET", "/api/perfumes", 200),
        ("Get Deals (No Auth - 401)", "GET", "/api/deals", 401),
        ("Get Alerts (No Auth - 401)", "GET", "/api/alerts", 401),
        ("Subscription Status (No Auth - 401)", "GET", "/api/subscriptions/status", 401),
    ]
    
    passed = 0
    failed = 0
    
    for name, method, path, expected in tests:
        success, result = test_endpoint(name, method, path, expected)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} | {name}: {result}")
        if success:
            passed += 1
        else:
            failed += 1
    
    print()
    print("=" * 60)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    # Auth-protected flow test
    print()
    print("⚠️  Skipping authenticated tests (requires Clerk JWT)")
    print("To test authenticated endpoints:")
    print("  1. Get Clerk JWT token from your mobile app")
    print("  2. Run: curl -H 'Authorization: Bearer TOKEN' {BASE_URL}/api/deals")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())