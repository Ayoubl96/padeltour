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
- **Beginner**: `simple.json` - Basic request/error monitoring
- **Standard**: `standard.json` - Comprehensive API monitoring  
- **Advanced**: `advanced.json` - Full performance analytics
- **🆕 Status Codes**: `status-code-monitoring.json` - HTTP status analysis

**💡 Recommended**: Import `status-code-monitoring.json` - it works with your current setup and provides essential API health metrics!

### 3. Import Process
1. Copy the **entire JSON content** from your chosen dashboard file
2. In Grafana: **Dashboards → New → Import**
3. **Paste JSON** and click **"Load"** then **"Import"**
4. No data source selection needed (pre-configured for "grafanacloud-logs")

## 📊 Dashboard Features

### Debug Dashboard (`debug.json`)
- ✅ Basic connection test
- ✅ Log count verification
- ✅ Error detection

### Simple Dashboard (`simple.json`)
- Request volume tracking
- Error monitoring
- Application health status
- Log level distribution
- Recent error logs

### Standard Dashboard (`standard.json`)
- Request rate analysis
- HTTP status code tracking
- Top endpoints identification
- Error rate monitoring
- Response time basics

### Advanced Dashboard (`advanced.json`)
- Response time percentiles (P50, P95, P99)
- Performance analysis by endpoint
- Slow request detection
- Status code categorization
- Comprehensive error analysis

### Status Code Monitoring Dashboard (`status-code-monitoring.json`) 🆕
- **Error rate percentages** (overall, server errors, client errors)
- **Success rate tracking** for SLA monitoring
- **Status code distribution** (200, 404, 500, etc.)
- **Status class breakdown** (2xx, 4xx, 5xx)
- **Error trends over time**
- **Error rate by endpoint**
- **Recent HTTP error logs**

## 🔧 Enhanced Middleware (Optional)

For the **Advanced Dashboard** to work fully, implement the enhanced middleware:

```python
# In your main.py
from grafana.enhanced_middleware import EnhancedLoggingMiddleware

app.add_middleware(EnhancedLoggingMiddleware)
```

## 📚 Documentation

- **Setup Guide**: `docs/setup-guide.md` - Complete installation instructions
- **Troubleshooting**: `docs/troubleshooting.md` - Fix common issues

## 🆘 Need Help?

1. **Empty Dashboard**: Check `docs/troubleshooting.md`
2. **Connection Issues**: Use `dashboards/debug.json` first
3. **Query Errors**: Verify your log labels match `app="padeltour"`

## ✅ What Works

All files in this folder are **tested and working** with Grafana Cloud. The old broken files have been removed. 