#!/usr/bin/env python3
"""
Test script to verify middleware logging functionality
Run this to check if your middleware is properly logging requests
"""

import requests
import time
import json
import sys
from urllib.parse import urljoin

# Your API base URL
BASE_URL = "https://api.tourn.me"  # Change this if needed

def test_endpoint(endpoint, method="GET", expected_status=None):
    """Test a single endpoint and print results"""
    url = urljoin(BASE_URL, endpoint)
    
    print(f"\n🔍 Testing {method} {endpoint}")
    print(f"   Full URL: {url}")
    
    try:
        if method == "GET":
            response = requests.get(url, timeout=10)
        elif method == "POST":
            response = requests.post(url, json={}, timeout=10)
        
        print(f"   ✅ Status: {response.status_code}")
        
        if expected_status and response.status_code != expected_status:
            print(f"   ⚠️  Expected {expected_status}, got {response.status_code}")
            
        return response.status_code
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Request failed: {e}")
        return None

def main():
    """Run middleware logging tests"""
    
    print("🧪 MIDDLEWARE LOGGING TEST")
    print("=" * 50)
    print(f"Testing API: {BASE_URL}")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
    
    # Test cases: (endpoint, method, expected_status)
    test_cases = [
        # Existing endpoints
        ("/", "GET", 200),
        ("/api/v1/staging/tournament/1/stage", "GET", None),
        ("/api/v1/staging/stage/1/group", "GET", None),
        
        # Test different status codes
        ("/nonexistent", "GET", 404),          # Should generate 404
        ("/api/v1/invalid", "GET", 404),       # Should generate 404
        
        # Security scanner paths (will generate 404s)
        ("/.env", "GET", 404),
        ("/admin", "GET", 404),
        ("/wp-admin", "GET", 404),
    ]
    
    results = []
    
    print(f"\n📊 Running {len(test_cases)} test requests...")
    
    for i, (endpoint, method, expected_status) in enumerate(test_cases, 1):
        print(f"\n[{i}/{len(test_cases)}]", end="")
        status = test_endpoint(endpoint, method, expected_status)
        results.append({
            "endpoint": endpoint,
            "method": method,
            "status": status,
            "expected": expected_status
        })
        
        # Small delay between requests
        time.sleep(0.5)
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 TEST SUMMARY")
    print(f"{'='*50}")
    
    successful = len([r for r in results if r["status"] is not None])
    status_codes = {}
    
    for result in results:
        if result["status"]:
            status_codes[result["status"]] = status_codes.get(result["status"], 0) + 1
    
    print(f"✅ Successful requests: {successful}/{len(test_cases)}")
    print(f"📊 Status code distribution:")
    for status, count in sorted(status_codes.items()):
        print(f"   {status}: {count} requests")
    
    print(f"\n🕐 Check your Grafana dashboard in 2-3 minutes")
    print(f"   Expected logs with event_type='request_complete'")
    print(f"   Should see status codes: {list(status_codes.keys())}")
    
    # Generate sample LogQL queries
    print(f"\n🔍 SAMPLE GRAFANA QUERIES TO TEST:")
    print(f"{'='*50}")
    print("1. Check total requests:")
    print('   {logger="padeltour.middleware"} | json | event_type="request_complete"')
    
    print("\n2. Check status code distribution:")
    print('   sum by (status_code) (count_over_time({logger="padeltour.middleware"} | json | event_type="request_complete" [5m]))')
    
    print("\n3. Check error rate:")
    print('   (sum(rate({logger="padeltour.middleware"} | json | event_type="request_complete" | status_code >= 400 [5m])) / sum(rate({logger="padeltour.middleware"} | json | event_type="request_complete" [5m]))) * 100')
    
    print("\n4. Check recent logs:")
    print('   {logger="padeltour.middleware"} | json | event_type="request_complete" | status_code > 0')

if __name__ == "__main__":
    main() 