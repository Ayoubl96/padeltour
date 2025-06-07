# HTTP Status Code Monitoring Guide

## 🎯 Why Status Code Monitoring is Essential

HTTP status codes are **crucial indicators** of your API's health and user experience. They tell you:

- **2xx Success**: Everything is working correctly
- **4xx Client Errors**: User/client problems (bad requests, auth issues)
- **5xx Server Errors**: Your API has problems (bugs, outages, dependencies)

## 📊 What You Already Have

Good news! Your current middleware **already logs status codes** as structured fields:

```json
{
  "status_code": 200,
  "duration": 145.2,
  "event_type": "request_complete"
}
```

## 🚀 Enhanced Status Code Tracking

### Current vs Enhanced Logging

**Current (You have this):**
```json
{
  "status_code": 404,
  "event_type": "request_complete"
}
```

**Enhanced (Recommended upgrade):**
```json
{
  "status_code": 404,
  "status_category": "client_error",
  "status_class": "4xx",
  "is_success": false,
  "is_client_error": true,
  "is_server_error": false,
  "event_type": "request_complete"
}
```

## 📈 Dashboard Capabilities

### With Current Setup
✅ **Status code distribution**  
✅ **Basic error rate calculation**  
✅ **Filter logs by status code**  

### With Enhanced Setup
✅ **All of the above, plus:**  
✅ **Status code categories (2xx, 4xx, 5xx)**  
✅ **Success rate percentages**  
✅ **Error rate by endpoint**  
✅ **Detailed error classification**  

## 🎯 Key Metrics to Monitor

### 1. **Error Rate Percentage**
```logql
(sum(rate({app="padeltour", event_type="request_complete"} 
| json | status_code >= 400 [5m])) 
/ sum(rate({app="padeltour", event_type="request_complete"} [5m]))) * 100
```

### 2. **Success Rate (SLA)**
```logql
(sum(rate({app="padeltour", event_type="request_complete"} 
| json | status_code < 400 [5m])) 
/ sum(rate({app="padeltour", event_type="request_complete"} [5m]))) * 100
```

### 3. **Server Error Rate**
```logql
(sum(rate({app="padeltour", event_type="request_complete"} 
| json | status_code >= 500 [5m])) 
/ sum(rate({app="padeltour", event_type="request_complete"} [5m]))) * 100
```

## 📊 Available Dashboards

### 1. **Status Code Monitoring Dashboard** (`status-code-monitoring.json`)
Specialized dashboard focusing on HTTP status codes:
- Error rate percentages
- Status code distribution
- Success rate tracking
- Error trends over time
- Error rate by endpoint
- Recent HTTP errors

### 2. **Enhanced Dashboards** (If using enhanced middleware)
- More detailed categorization
- Better endpoint grouping
- Advanced error classification

## 🔧 Implementation Options

### Option A: Use Current Setup (Immediate)
Import the **Status Code Monitoring Dashboard** right now. It works with your existing logs.

### Option B: Upgrade to Enhanced (Recommended)
1. Replace your middleware with `enhanced_middleware_v2.py`
2. Get better categorization and metrics
3. More detailed dashboards

## 🚨 Alerting Recommendations

Set up alerts for:

1. **Overall Error Rate > 5%** for 5 minutes
2. **Server Error Rate > 1%** for 2 minutes  
3. **Success Rate < 95%** for 5 minutes
4. **Any endpoint with > 20% error rate**

## 📋 Status Code Reference

### Success Codes (2xx)
- **200 OK**: Normal successful request
- **201 Created**: Resource successfully created
- **204 No Content**: Successful request, no response body

### Client Error Codes (4xx)
- **400 Bad Request**: Invalid request format
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Access denied
- **404 Not Found**: Resource doesn't exist
- **422 Unprocessable Entity**: Validation errors

### Server Error Codes (5xx)
- **500 Internal Server Error**: Generic server error
- **502 Bad Gateway**: Upstream server error
- **503 Service Unavailable**: Server overloaded
- **504 Gateway Timeout**: Upstream timeout

## 🎯 Quick Start

1. **Import** `dashboards/status-code-monitoring.json`
2. **Check** your current error rates
3. **Set up alerts** on key metrics
4. **Monitor trends** over time
5. **Investigate** any spikes in error rates

## 💡 Pro Tips

- **4xx errors** often indicate API documentation or client issues
- **5xx errors** are always your responsibility to fix
- **Monitor error rates by endpoint** to find problematic areas
- **Track success rate as your primary SLA metric**
- **Set up alerting** before you need it 