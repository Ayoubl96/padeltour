# Middleware Logging Issues & Fixes

## 🚨 Issues Found & Fixed

### 1. **Duration Field Mismatch** ✅ FIXED
**Problem**: `logging_config.py` looked for `duration` field, but middleware sent `duration_ms`
**Fix**: Updated JSON formatter to handle both field names
**Impact**: Response time data now appears in Grafana

### 2. **Missing Status Code in Exception Logs** ✅ FIXED  
**Problem**: When exceptions occurred, error logs didn't include `status_code`
**Fix**: Added `status_code: 500` to exception log entries
**Impact**: Better error tracking and debugging

### 3. **Inconsistent Log Levels** ✅ FIXED
**Problem**: Request completion logs used different levels (INFO/ERROR)
**Fix**: All `request_complete` events now use INFO level, with separate ERROR events for alerting
**Impact**: Consistent data in Grafana panels

### 4. **Missing Debug Information** ✅ FIXED
**Problem**: Hard to debug whether requests were processed correctly
**Fix**: Added debugging fields: `has_response`, `processing_time`, `had_exception`
**Impact**: Better troubleshooting capabilities

## 🔧 Testing Your Fixes

### Option 1: Local Verification (Before Deploy)
```bash
python verify_middleware_local.py
```
This checks:
- Environment variables
- Import configuration  
- Logging setup
- Grafana connection

### Option 2: Live API Testing (After Deploy)
```bash
python test_middleware_logging.py
```
This generates real requests to test:
- Different status codes (200, 404)
- Error scenarios
- Response time tracking
- Status code distribution

## 📊 Expected Results in Grafana

After deploying fixes, you should see:

### ✅ Status Code Distribution Panel
- **200** responses from valid endpoints
- **404** responses from invalid paths
- Correct percentages and counts

### ✅ Error Rate Panel  
- Non-zero percentage if 404s are present
- Accurate calculation based on status codes

### ✅ Response Time Panel
- Average response times (100-200ms typically)
- Time series data showing performance

### ✅ Request Rate Panel
- Requests per second
- Should show activity spikes during testing

## 🔍 Debugging Queries

If panels still show "No data", try these LogQL queries in Grafana Explore:

### 1. Basic Log Check
```logql
{logger="padeltour.middleware"}
```
Should show all middleware logs

### 2. Request Completion Check  
```logql
{logger="padeltour.middleware"} | json | event_type="request_complete"
```
Should show completed requests with status codes

### 3. Field Validation
```logql
{logger="padeltour.middleware"} | json | event_type="request_complete" | status_code > 0
```
Should show only logs with valid status codes

### 4. Recent Activity
```logql
{logger="padeltour.middleware"} | json | event_type="request_complete" | duration_ms > 0
```
Should show logs with response time data

## 🚨 If Still No Data

### Check Environment Variables
```bash
heroku config:get GRAFANA_LOKI_URL
heroku config:get GRAFANA_LOKI_USERNAME  
heroku config:get GRAFANA_LOKI_PASSWORD
```

### Check Heroku Logs
```bash
heroku logs --tail
```
Look for:
- "Grafana Cloud Logger initialized successfully"
- "Successfully sent X logs to Grafana"
- Any error messages

### Verify Dashboard Data Source
1. Go to Grafana Settings → Data Sources
2. Find your Loki data source
3. Copy the UID (e.g., "grafanacloud-logs")
4. Ensure dashboard JSON files use the same UID

## 📈 Enhanced Features Added

### New Log Fields
- `has_response`: Whether response object exists
- `processing_time`: Total processing time in seconds
- `had_exception`: Boolean flag for exception handling
- `event_type`: "request_complete" or "http_error"

### Dual Logging Strategy
- **INFO level**: All request completions (for metrics)
- **ERROR level**: Only errors (for alerting)

### Better Exception Handling
- Exceptions now include status_code
- Clearer error messages
- Full stack traces preserved

## 🎯 Next Steps

1. **Deploy** your changes to Heroku
2. **Run** `test_middleware_logging.py` to generate test data
3. **Wait** 2-3 minutes for logs to appear in Grafana
4. **Import** `status-code-current-middleware.json` dashboard
5. **Verify** data appears in all panels

If you still see "No data" after following these steps, the issue is likely with:
- Grafana environment variables
- Data source configuration  
- Log ingestion delays

Contact support with Heroku logs and Grafana data source details for further debugging. 