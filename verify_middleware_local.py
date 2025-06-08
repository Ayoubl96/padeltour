#!/usr/bin/env python3
"""
Local verification script for middleware logging
This script checks if your middleware is configured correctly
"""

import os
import json
import logging
from datetime import datetime
import sys

# Add the app directory to the path
sys.path.insert(0, './app')

def check_environment_variables():
    """Check if Grafana environment variables are set"""
    print("🔧 ENVIRONMENT VARIABLES CHECK")
    print("=" * 50)
    
    required_vars = [
        "GRAFANA_LOKI_URL",
        "GRAFANA_LOKI_USERNAME", 
        "GRAFANA_LOKI_PASSWORD"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # Mask sensitive values
            if "PASSWORD" in var or "KEY" in var:
                display_value = f"{value[:8]}..." if len(value) > 8 else "***"
            else:
                display_value = value
            print(f"✅ {var}: {display_value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
        print("   Logs will only go to console, not Grafana")
    else:
        print("\n✅ All Grafana variables configured")
    
    return len(missing_vars) == 0

def test_logging_configuration():
    """Test the logging configuration"""
    print("\n📝 LOGGING CONFIGURATION TEST")
    print("=" * 50)
    
    try:
        # Import logging components
        from core.logging_config import setup_logging, get_logger, JSONFormatter
        
        print("✅ Successfully imported logging components")
        
        # Setup logging
        setup_logging()
        print("✅ Logging setup completed")
        
        # Get middleware logger
        logger = get_logger("padeltour.middleware")
        print("✅ Got middleware logger")
        
        # Test JSON formatter
        formatter = JSONFormatter()
        
        # Create a mock log record
        record = logging.LogRecord(
            name="padeltour.middleware",
            level=logging.INFO,
            pathname="middleware.py",
            lineno=85,
            msg="Test log message",
            args=(),
            exc_info=None,
            func="dispatch"
        )
        
        # Add middleware-specific fields
        record.request_id = "test-123-456"
        record.method = "GET"
        record.endpoint = "/api/v1/test"
        record.status_code = 200
        record.duration_ms = 125.45
        record.event_type = "request_complete"
        
        # Format the record
        formatted = formatter.format(record)
        log_data = json.loads(formatted)
        
        print("✅ JSON formatting works")
        print(f"   Sample formatted log: {formatted[:100]}...")
        
        # Check required fields
        required_fields = ["status_code", "duration_ms", "event_type", "request_id"]
        missing_fields = [field for field in required_fields if field not in log_data]
        
        if missing_fields:
            print(f"⚠️  Missing fields in formatted log: {missing_fields}")
        else:
            print("✅ All required fields present in formatted log")
        
        return True, log_data
        
    except Exception as e:
        print(f"❌ Logging configuration error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False, None

def test_middleware_import():
    """Test importing the middleware"""
    print("\n🔧 MIDDLEWARE IMPORT TEST")
    print("=" * 50)
    
    try:
        from core.middleware import LoggingMiddleware
        print("✅ Successfully imported LoggingMiddleware")
        
        # Try to instantiate (won't work without ASGI app, but import should work)
        print("✅ Middleware class available")
        return True
        
    except Exception as e:
        print(f"❌ Middleware import error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def check_grafana_connection():
    """Test connection to Grafana if configured"""
    print("\n🌐 GRAFANA CONNECTION TEST")
    print("=" * 50)
    
    try:
        from core.grafana_config import grafana_logger
        
        if not grafana_logger.enabled:
            print("❌ Grafana logger not enabled (missing env vars)")
            return False
        
        print("✅ Grafana logger enabled")
        print(f"   URL: {grafana_logger.loki_url}")
        print(f"   Username: {grafana_logger.loki_username}")
        print(f"   Batch size: {grafana_logger.batch_size}")
        print(f"   Flush interval: {grafana_logger.flush_interval}s")
        
        # Test sending a log
        grafana_logger.send_log(
            level="INFO",
            message="Test log from verification script",
            labels={
                "test": "verification",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        
        print("✅ Test log sent to Grafana")
        return True
        
    except Exception as e:
        print(f"❌ Grafana connection error: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

def main():
    """Run all verification tests"""
    print("🔍 MIDDLEWARE LOGGING VERIFICATION")
    print("=" * 60)
    print(f"Timestamp: {datetime.utcnow().isoformat()}Z")
    
    # Run tests
    tests = [
        ("Environment Variables", check_environment_variables),
        ("Logging Configuration", test_logging_configuration),
        ("Middleware Import", test_middleware_import),
        ("Grafana Connection", check_grafana_connection),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            if test_name == "Logging Configuration":
                success, data = test_func()
                results[test_name] = success
            else:
                results[test_name] = test_func()
        except Exception as e:
            print(f"\n❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n{'='*60}")
    print("📋 VERIFICATION SUMMARY")
    print(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Middleware should be working correctly.")
        print("\n📝 Next steps:")
        print("   1. Deploy your changes to Heroku")
        print("   2. Run the test_middleware_logging.py script")
        print("   3. Check your Grafana dashboard after 2-3 minutes")
    else:
        print("⚠️  Some tests failed. Please fix the issues above.")
        print("\n🔧 Common fixes:")
        print("   1. Set missing environment variables")
        print("   2. Check import paths")
        print("   3. Verify Grafana credentials")

if __name__ == "__main__":
    main() 