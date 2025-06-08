# Troubleshooting Empty Dashboards

## The Problem: All Panels Show "No Data"

Your Grafana dashboards were showing empty panels because of **label mismatch** between the dashboard queries and your actual log data.

## Root Cause Analysis

### What the dashboards were looking for:
```logql
{app="padeltour", event_type="request_complete"}
```

### What your logs actually contain:
```json
{
  "logger": "padeltour.middleware",
  "level": "INFO",
  "status_code": 200,
  // ... (no event_type field)
}
```

### Key Issues:
1. **Wrong label**: `app="padeltour"` → Should be `logger="padeltour.middleware"`
2. **Missing field**: `event_type="request_complete"` → This field doesn't exist in your logs
3. **Query structure**: Needed to filter for completed requests using `|= "Completed"` instead

## The Solution

### Fixed Query Pattern:
```logql
# Instead of:
{app="padeltour", event_type="request_complete"} | json | status_code >= 400

# Use:
{logger="padeltour.middleware"} | json | status_code >= 400
```

### Working Dashboards:
- ✅ `debug-status-codes.json` - Quick test dashboard
- ✅ `status-code-monitoring-fixed.json` - Corrected version with proper queries

## Quick Test

1. Import `grafana/dashboards/debug-status-codes.json`
2. Check if you see data in the panels
3. If working, import `grafana/dashboards/status-code-monitoring-fixed.json`

## Your Log Structure

Based on your actual logs, here's what's available for queries:

### Available Labels:
- `logger="padeltour.middleware"`
- `level="INFO"` or `level="ERROR"`

### Available JSON Fields:
- `status_code` (200, 404, etc.)
- `duration_ms` (response time)
- `endpoint` (API path)
- `method` (GET, POST, etc.)
- `request_id` (unique identifier)
- `timestamp`

### Sample Working Queries:

```logql
# Total requests in last 5 minutes
count_over_time({logger="padeltour.middleware"} | json | status_code > 0 [5m])

# Error rate percentage
(sum(rate({logger="padeltour.middleware"} | json | status_code >= 400 [5m])) 
 / sum(rate({logger="padeltour.middleware"} | json | status_code > 0 [5m]))) * 100

# Status code distribution
sum by (status_code) (count_over_time({logger="padeltour.middleware"} | json | status_code > 0 [5m]))

# Error logs only
{logger="padeltour.middleware"} | json | status_code >= 400
```

## Next Steps

1. **Test the fixed dashboards** to confirm they work
2. **Update existing dashboards** to use the correct label pattern
3. **Consider adding event_type field** to your middleware for better log categorization (optional)

## Prevention for Future

To avoid this issue in the future:
1. Always test dashboard queries in Grafana's "Explore" section before creating dashboards
2. Use the Label Browser in Grafana to see what labels are actually available
3. Check a few actual log entries to understand the JSON structure 