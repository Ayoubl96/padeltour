# PadelTour Grafana Monitoring

This folder contains everything needed to set up comprehensive monitoring for your PadelTour API using Grafana Cloud.

## 📁 Folder Structure

```
grafana/
├── README.md                         # This file
├── dashboards/                       # Ready-to-import dashboard files
│   ├── debug.json                   # Start here - tests basic connection
│   ├── simple.json                  # Basic monitoring dashboard
│   ├── standard.json                # Comprehensive monitoring 
│   ├── advanced.json                # Full observability (requires enhanced middleware)
│   └── status-code-monitoring.json  # 🆕 HTTP status code analysis
├── docs/                            # Documentation
│   ├── setup-guide.md               # Complete setup instructions
│   ├── troubleshooting.md           # Solutions for common issues
│   └── status-code-guide.md         # 🆕 Status code monitoring guide
├── enhanced_middleware.py           # Optional: Enhanced logging v1
└── enhanced_middleware_v2.py        # 🆕 Enhanced logging with status tracking
```

## 🚀 Quick Start

### 1. Test Your Connection First
Import `dashboards/debug.json` to verify your logs are accessible:
- Go to Grafana → Dashboards → New → Import
- Copy and paste the entire JSON content
- If you see logs → You're ready!
- If empty → Check the troubleshooting guide

### 2. Choose Your Dashboard Level
- **Debug**: `debug.json` - Connection testing and basic log verification
- **Simple**: `simple.json` - Basic request/error monitoring (perfect for beginners)
- **API Monitoring**: `api-monitoring.json` - Comprehensive API monitoring with performance metrics
- **Business Metrics**: `business-metrics.json` - User actions, business events, and database operations
- **Advanced**: `advanced.json` - Full performance analytics with percentiles and slow request detection

**💡 Recommended Start**: Import `simple.json` first, then `api-monitoring.json` for comprehensive monitoring!

### 3. Import Process
1. Copy the **entire JSON content** from your chosen dashboard file
2. In Grafana: **Dashboards → New → Import**
3. **Paste JSON** and click **"Load"** then **"Import"**
4. No data source selection needed (pre-configured for "grafanacloud-logs")

## 📊 Dashboard Features

### Debug Dashboard (`debug.json`)
- ✅ Basic connection test
- ✅ Log count verification
- ✅ Event type detection
- ✅ Log level distribution
- ✅ Sample log viewing

### Simple Dashboard (`simple.json`)
- Request volume tracking
- Error monitoring
- Application health status
- Average response time
- Log level distribution
- Recent error logs

### API Monitoring Dashboard (`api-monitoring.json`)
- Request rate and error rate metrics
- HTTP status code distribution
- Top API endpoints by traffic
- Response time trends (average & 95th percentile)
- Recent HTTP errors and user actions
- HTTP methods distribution

### Business Metrics Dashboard (`business-metrics.json`)
- User actions per hour
- Business events tracking
- Database operations monitoring
- User activity trends over time
- Database operations by table
- Recent user actions and business events

### Advanced Dashboard (`advanced.json`)
- **Success rate and error rate percentages**
- **Response time percentiles** (P50, P95, P99)
- **Slow request detection** (>1s automatically flagged)
- **Status code categorization** (2xx, 3xx, 4xx, 5xx)
- **Performance analysis by endpoint**
- **Request type classification** over time
- **Recent slow requests and server errors**

## 🔧 Enhanced Middleware (Optional)

For the **Advanced Dashboard** to work fully, implement the enhanced middleware v2:

```python
# In your main.py
from grafana.enhanced_middleware_v2 import EnhancedLoggingMiddleware

app.add_middleware(EnhancedLoggingMiddleware)
```

### Enhanced Middleware Features:
- **Detailed performance metrics** (P50, P95, P99 response times)
- **Automatic slow request detection** (>1s flagged)
- **Status code categorization** (2xx, 3xx, 4xx, 5xx)
- **Request size and response size tracking**
- **Enhanced error context** with error types
- **Business event logging helpers**
- **Performance metric logging functions**

## 📚 Documentation

- **Setup Guide**: `docs/setup-guide.md` - Complete installation instructions
- **Troubleshooting**: `docs/troubleshooting.md` - Fix common issues

## 🆘 Need Help?

1. **Empty Dashboard**: Check `docs/troubleshooting.md`
2. **Connection Issues**: Use `dashboards/debug.json` first
3. **Query Errors**: Verify your log labels match `app="padeltour"`

## ✅ What Works

All files in this folder are **tested and working** with Grafana Cloud. The old broken files have been removed. 