# Grafana Dashboard Troubleshooting Guide

## Problem: Empty Dashboard After Import

If your dashboard appears empty after importing, follow these steps to diagnose and fix the issue.

## Step 1: Verify Loki Data Source

1. **Check Data Source Connection**:
   - Go to **Configuration** → **Data Sources** in Grafana
   - Find your Loki data source
   - Click **Test** to ensure it's connected
   - The URL should look like: `https://logs-prod-us-central1.grafana.net`

2. **Verify Authentication**:
   - Username should be your Grafana Cloud username
   - Password should be your Grafana Cloud API key (not your login password)

## Step 2: Test Basic Queries in Explore

1. **Go to Explore Tab**:
   - Click the **Explore** icon (compass) in the left sidebar
   - Select your Loki data source

2. **Test Basic Query**:
   ```logql
   {app="padeltour"}
   ```
   
   **Expected Result**: You should see your logs
   
   **If No Results**: Your logs don't have the `app="padeltour"` label

3. **Find Your Actual Labels**:
   If the basic query returns no results, try:
   ```logql
   {job="your-app-name"}
   ```
   Or just browse available labels in the Label Browser

## Step 3: Check Your Log Labels

Based on your log examples, your logs should have these labels:
- `app="padeltour"`
- `level="INFO"` (or ERROR, WARNING)
- `event_type="request_start"` (or request_complete, etc.)

**Test Each Label**:
```logql
# Test app label
{app="padeltour"}

# Test level label  
{level="INFO"}

# Test event_type label
{event_type="request_start"}
```

## Step 4: Fix Common Label Issues

### Issue A: Wrong App Label
If your logs use a different app name, update the dashboard queries.

**Find and Replace in Dashboard JSON**:
- Find: `app="padeltour"`
- Replace with: `app="your-actual-app-name"`

### Issue B: Missing Labels
If some labels are missing, use this simplified query:
```logql
# Just get all logs for your app
{app="padeltour"}
```

## Step 5: Create a Minimal Test Dashboard

Create this simple panel to test:

1. **Create New Dashboard**
2. **Add Panel**
3. **Set Query**:
   ```logql
   {app="padeltour"}
   ```
4. **Set Visualization**: Logs
5. **Save and Test**

## Step 6: Fix Time Range Issues

1. **Check Time Range**: Make sure you're looking at a period when your app was running
2. **Try "Last 24 hours" or "Last 7 days"**
3. **Check Log Timestamps**: Ensure they're recent and in the correct timezone

## Step 7: Import Dashboard Correctly

1. **Copy the ENTIRE JSON content** (including outer braces)
2. **In Grafana**: Dashboards → New → Import
3. **Paste JSON** (don't upload file)
4. **Click Load**
5. **Select your Loki data source** from dropdown
6. **Click Import**

## Step 8: Common LogQL Query Fixes

If you see specific errors, here are corrected queries:

### For Request Count:
```logql
# Simple count
count_over_time({app="padeltour", event_type="request_start"} [1m])

# Rate-based (more complex)
rate({app="padeltour", event_type="request_start"} [1m])
```

### For Error Count:
```logql
# Simple error count
count_over_time({app="padeltour", level="ERROR"} [1m])
```

### For All Logs:
```logql
# Just show all logs
{app="padeltour"}
```

## Quick Debug Queries

Copy these into Grafana Explore to test:

```logql
# 1. Check if any logs exist
{app="padeltour"}

# 2. Check recent logs (last hour)
{app="padeltour"} |= ""

# 3. Check specific log levels
{app="padeltour", level="INFO"}

# 4. Check request events
{app="padeltour", event_type="request_start"}

# 5. Count logs per minute
count_over_time({app="padeltour"} [1m])
```

## Still Having Issues?

### Check These Common Problems:

1. **Wrong Data Source Selected**: Each panel needs the correct Loki data source
2. **Case Sensitivity**: Labels are case-sensitive (`INFO` vs `info`)
3. **Label Values**: Check exact values in your logs vs dashboard queries
4. **Time Zone**: Grafana time vs your log timestamps
5. **No Recent Data**: App might not be sending logs currently

### Get Your Actual Log Structure:

Run this in Explore to see your log structure:
```logql
{app="padeltour"} | json | limit 10
```

This will show you the exact fields and values in your logs.

## Need to Modify Dashboard?

If you need to change the queries in your dashboard:

1. **Edit Panel**: Click panel title → Edit
2. **Update Query**: Change the LogQL expression
3. **Test**: Use the query inspector to test
4. **Save**: Apply and save changes

## Contact for Help

If you're still stuck, share:
1. Screenshot of empty dashboard
2. Result of `{app="padeltour"}` query in Explore
3. Sample of your actual log entry
4. Any error messages you see 