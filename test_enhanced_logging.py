#!/usr/bin/env python3
"""
Test script to verify enhanced middleware v2 is working correctly.
Run this after starting your FastAPI server to generate sample logs.
"""

import requests
import time
import json

# Base URL for your API
BASE_URL = "http://localhost:8000"

def test_endpoints():
    """Test various endpoints to generate logs for Grafana dashboards"""
    
    print("🚀 Testing Enhanced Middleware v2 Logging...")
    print("=" * 50)
    
    # Test 1: Root endpoint (should be fast)
    print("1. Testing root endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   ✅ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 2: Non-existent endpoint (404 error)
    print("2. Testing 404 endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/non-existent")
        print(f"   ✅ Status: {response.status_code} (expected 404)")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 3: API endpoints
    print("3. Testing API endpoints...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/docs")
        print(f"   ✅ Status: {response.status_code}")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    # Test 4: Multiple rapid requests (for volume testing)
    print("4. Testing request volume...")
    for i in range(5):
        try:
            response = requests.get(f"{BASE_URL}/")
            print(f"   Request {i+1}: {response.status_code}")
            time.sleep(0.1)  # Small delay
        except Exception as e:
            print(f"   ❌ Request {i+1} Error: {e}")
    
    # Test 5: Slow request simulation (if you have any endpoints that might be slow)
    print("5. Testing potential slow endpoint...")
    try:
        # This might be slow or return 404, both are useful for testing
        response = requests.get(f"{BASE_URL}/api/v1/some-endpoint", timeout=5)
        print(f"   ✅ Status: {response.status_code}")
    except requests.exceptions.Timeout:
        print("   ⏰ Request timed out (good for slow request testing)")
    except Exception as e:
        print(f"   ℹ️  Expected error: {e}")
    
    print("=" * 50)
    print("✅ Test completed!")
    print("\nNow check your Grafana dashboards:")
    print("1. Debug Dashboard - Should show recent logs")
    print("2. Simple Dashboard - Should show request volume")
    print("3. API Monitoring Dashboard - Should show request patterns")
    print("4. Advanced Dashboard - Should show performance metrics")
    print("\nLook for:")
    print("- Request counts increasing")
    print("- Different status codes (200, 404)")
    print("- Response time metrics")
    print("- Event types: request_start, request_complete, success, client_error")

def test_with_different_methods():
    """Test different HTTP methods"""
    print("\n🔧 Testing different HTTP methods...")
    
    # GET request
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"GET /: {response.status_code}")
    except Exception as e:
        print(f"GET error: {e}")
    
    # POST request (might return 404 or 405, both useful)
    try:
        response = requests.post(f"{BASE_URL}/", json={"test": "data"})
        print(f"POST /: {response.status_code}")
    except Exception as e:
        print(f"POST info: {e}")

if __name__ == "__main__":
    print("Enhanced Middleware v2 Test Script")
    print("Make sure your FastAPI server is running on localhost:8000")
    
    input("Press Enter to start testing...")
    
    test_endpoints()
    test_with_different_methods()
    
    print("\n🎯 Next Steps:")
    print("1. Check your application logs for structured JSON output")
    print("2. Import the Grafana dashboards if you haven't already")
    print("3. Look for the enhanced fields in Advanced Dashboard:")
    print("   - is_slow, is_error, status_category")
    print("   - P50, P95, P99 response times")
    print("   - success, client_error, server_error events") 