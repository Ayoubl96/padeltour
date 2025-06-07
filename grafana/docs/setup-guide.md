# PadelTour API Grafana Dashboard Setup

## Overview
This repository contains three levels of monitoring dashboards for your PadelTour API:

1. **Simple Dashboard** (`grafana_dashboard_simple.json`) - Basic monitoring with count-based metrics
2. **Standard Dashboard** (`grafana_dashboard.json`) - Comprehensive monitoring with rate-based metrics
3. **Advanced Dashboard** (`grafana_dashboard_advanced.json`) - Full observability with response time histograms and performance analysis

## Available Dashboards

### Simple Dashboard Features:
- Total requests per minute
- Error count monitoring
- Application health status
- Request volume over time
- Log level distribution
- Recent error logs
- Request endpoints table

### Standard Dashboard Features:
- Request rate (requests per second)
- Error rate monitoring
- HTTP status code distribution
- Application health monitoring
- Request volume trends
- Top endpoints by traffic
- Recent error logs

### Advanced Dashboard Features:
- Request rate with multiple percentiles
- Error rate percentage calculation
- Response time percentiles (P50, P95, P99)
- Slow request tracking (>1s)
- Status code categorization
- Performance analysis by endpoint
- Response size monitoring
- Method distribution analysis

## Setup Instructions

### 1. Choose Your Dashboard
Start with the **Simple Dashboard** if you're new to monitoring, then upgrade to Standard or Advanced as needed.

### 2. Import the Dashboard
1. Open your Grafana Cloud instance
2. Go to "Dashboards" → "New" → "Import"
3. Copy the contents of your chosen dashboard JSON file and paste it into the import dialog
4. Click "Load" and then "Import"

### 3. Verify Data Source
Make sure your Loki data source is configured and named "Loki" (or update the queries accordingly).

### 4. Optional: Enhanced Middleware for Advanced Metrics
For the **Advanced Dashboard** to work optimally, consider upgrading your middleware using the enhanced version in `enhanced_middleware.py`. This provides:

- Better endpoint normalization (groups `/users/123` as `/users/{id}`)
- Response time tracking with `duration_ms` field
- Status code categorization
- Response size tracking
- Slow request flagging

To implement:
```python
# In your main.py or app setup
from enhanced_middleware import EnhancedLoggingMiddleware

app.add_middleware(EnhancedLoggingMiddleware)
```

### 5. Dashboard Panels Explained

#### Top Row Stats:
- **Request Volume**: Shows requests per second
- **Error Rate**: Shows errors per second with color-coded thresholds
- **HTTP Status Codes**: Pie chart showing distribution of status codes
- **Application Status**: Shows if your app instances are running

#### Middle Row:
- **Requests Over Time**: Time series showing total requests vs errors
- **Top Endpoints**: Bar chart of most frequently accessed endpoints

#### Bottom Row:
- **Recent Error Logs**: Live feed of error logs
- **Request Duration**: Average response times (if available from logs)

## LogQL Query Examples

Here are some useful LogQL queries you can use:

### Basic Request Metrics
```logql
# Total request rate
sum(rate({app="padeltour", event_type="request_start"} [5m]))

# Error rate
sum(rate({app="padeltour", level="ERROR"} [5m]))

# Requests by endpoint
sum by (endpoint) (rate({app="padeltour", event_type="request_start"} [5m]))
```

### Status Code Extraction
```logql
# Extract status codes from completion messages
{app="padeltour", event_type="request_complete"} 
| json 
| line | regexp "- (?P<status_code>\\d{3})"
```

### Error Analysis
```logql
# Recent error logs
{app="padeltour", level="ERROR"}

# Errors by module
sum by (module) (rate({app="padeltour", level="ERROR"} [5m]))
```

## Customization Tips

1. **Adjust Time Ranges**: Change the default time range from "Last 1 hour" to your preference
2. **Add Alerting**: Set up alerts on the error rate panel
3. **Custom Labels**: Add more labels to your logging to get better filtering
4. **Thresholds**: Adjust the color thresholds based on your normal traffic patterns

## Troubleshooting

1. **No Data Showing**: 
   - Verify your Loki data source is working
   - Check that logs are being sent with the correct labels (`app="padeltour"`)

2. **Query Errors**:
   - Some queries might need adjustment based on your exact log format
   - Use the Explore feature in Grafana to test queries

3. **Performance Issues**:
   - Increase query time ranges if needed
   - Consider using recording rules for heavy queries

## Advanced Features

### Response Time Calculation
To get accurate response times, you might want to enhance your logging to include duration:

```python
# In your middleware
duration = time.time() - start_time
logger.info("Request completed", extra={
    "duration_ms": duration * 1000,
    "status_code": response.status_code
})
```

Then use LogQL:
```logql
avg_over_time({app="padeltour"} | json | unwrap duration_ms [5m])
```

### Custom Alerts
Set up alerts for:
- Error rate > 1% for 5 minutes
- Request volume drops below expected threshold
- Application restart events
- Average response time > 2 seconds for 5 minutes
- P95 response time > 5 seconds
- Zero requests for 2 minutes (service down)

## Quick Start Checklist

1. ✅ Verify Grafana Cloud Loki is receiving your logs
2. ✅ Import the Simple Dashboard first to validate basic functionality
3. ✅ Check that all panels are showing data (may take a few minutes)
4. ✅ If using Advanced Dashboard, implement enhanced middleware
5. ✅ Set up basic alerts on error rate and response time
6. ✅ Customize thresholds based on your traffic patterns
7. ✅ Add dashboard to favorites and set auto-refresh

## Need Help?

If you encounter issues:
1. Check the Grafana Explore tab to test LogQL queries manually
2. Verify your log labels match the dashboard expectations (`app="padeltour"`)
3. Check that log timestamps are recent (within your selected time range)
4. Review the enhanced middleware implementation if response time metrics aren't showing 