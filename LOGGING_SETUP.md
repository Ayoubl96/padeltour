# PadelTour Logging System Setup Guide

## Overview

This guide explains how to set up and use the comprehensive logging system for the PadelTour API, including integration with Grafana Cloud for centralized log management and monitoring.

## Step 1: Basic Logging Implementation ✅

The basic logging system has been implemented with the following features:

### Features Implemented

1. **Structured JSON Logging** - All logs are formatted as JSON for easy parsing
2. **Request/Response Middleware** - Automatic logging of all HTTP requests
3. **Environment-aware Formatting** - JSON in production (Heroku), plain text in development
4. **Request ID Tracking** - Each request gets a unique ID for tracing
5. **Performance Monitoring** - Request duration tracking
6. **Error Handling** - Comprehensive error logging with stack traces

### Files Created/Modified

- `app/core/logging_config.py` - Main logging configuration
- `app/core/middleware.py` - HTTP request/response logging middleware
- `app/utils/logging_utils.py` - Helper functions for consistent logging
- `app/main.py` - Updated to integrate logging system
- `app/api/v1/endpoints/auth.py` - Example of logging integration in routes

### Environment Variables

Set these environment variables to control logging behavior:

```bash
# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
export LOG_LEVEL=INFO

# In Heroku, the DYNO environment variable automatically enables JSON formatting
```

### How to Use in Your Code

#### 1. Import the logger

```python
from app.core.logging_config import get_logger
from app.utils.logging_utils import log_user_action, log_error, log_business_event

logger = get_logger("your_module_name")
```

#### 2. Basic logging

```python
logger.info("User registration completed", extra={
    "user_id": user.id,
    "event_type": "user_registration",
    "email": user.email
})
```

#### 3. Use helper functions for consistent logging

```python
# Log user actions
log_user_action(
    "padeltour.tournaments",
    "tournament_created",
    user_id=user.id,
    request=request,
    extra_data={"tournament_id": tournament.id}
)

# Log business events
log_business_event(
    "padeltour.tournaments",
    "player_registered",
    details={"tournament_id": tournament.id, "player_id": player.id},
    user_id=user.id,
    request=request
)

# Log errors
log_error(
    "padeltour.payments",
    "Payment processing failed",
    error_type="payment_error",
    user_id=user.id,
    request=request,
    exception=e
)
```

### Log Format Example

```json
{
  "timestamp": "2024-01-15T10:30:45Z",
  "level": "INFO",
  "logger": "padeltour.auth",
  "message": "User action: login_success",
  "module": "auth",
  "function": "login",
  "line": 45,
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": 123,
  "endpoint": "/api/v1/login",
  "method": "POST",
  "event_type": "user_action",
  "action": "login_success",
  "username": "company@example.com"
}
```

## Step 2: Grafana Cloud Integration 🚀

### Prerequisites

1. **Grafana Cloud Account** - Sign up at [https://grafana.com/](https://grafana.com/)
2. **Loki Instance** - Available in your Grafana Cloud dashboard

### Setup Instructions

#### 1. Get Grafana Cloud Credentials

1. Log into your Grafana Cloud account
2. Go to "My Account" → "API Keys"
3. Create a new API key with "MetricsPublisher" role
4. Note down your Loki URL, username, and API key

Your Loki URL will look like:
```
https://logs-prod-us-central1.grafana.net/loki/api/v1/push
```

#### 2. Configure Environment Variables

Set these environment variables in your Heroku app:

```bash
# Grafana Cloud Loki Configuration
export GRAFANA_LOKI_URL="https://logs-prod-us-central1.grafana.net/loki/api/v1/push"
export GRAFANA_LOKI_USERNAME="your-grafana-username"
export GRAFANA_LOKI_PASSWORD="your-grafana-api-key"

# Optional: Configure batching (defaults shown)
export LOKI_BATCH_SIZE=10
export LOKI_FLUSH_INTERVAL=5

# Environment label for log categorization
export ENVIRONMENT=production
```

#### 3. Deploy to Heroku

The Grafana integration will automatically activate when the environment variables are set.

```bash
git add .
git commit -m "Add comprehensive logging system with Grafana Cloud integration"
git push heroku main
```

#### 4. Verify Logs in Grafana

1. Go to your Grafana Cloud dashboard
2. Navigate to "Explore"
3. Select your Loki data source
4. Query your logs using LogQL:

```logql
{app="padeltour"}
```

### Grafana Query Examples

#### Filter by log level
```logql
{app="padeltour", level="ERROR"}
```

#### Filter by event type
```logql
{app="padeltour", event_type="user_action"}
```

#### Filter by endpoint
```logql
{app="padeltour", endpoint="/api/v1/login"}
```

#### Search for specific text
```logql
{app="padeltour"} |= "login_success"
```

#### Rate of errors per minute
```logql
rate({app="padeltour", level="ERROR"}[1m])
```

### Dashboard Creation

Create dashboards in Grafana to monitor:

1. **Request Rate** - Number of requests per minute
2. **Error Rate** - Percentage of failed requests
3. **Response Time** - Average response time trends
4. **User Activity** - Login attempts, registrations, etc.
5. **Business Metrics** - Tournament creations, player registrations

### Alerts Setup

Set up alerts for:

1. **High Error Rate** - When error rate exceeds threshold
2. **Slow Response Times** - When average response time is too high
3. **Failed Logins** - Multiple failed login attempts
4. **System Errors** - Critical application errors

## Advanced Usage

### Custom Log Labels

Add custom labels for better filtering:

```python
logger.info("Custom event", extra={
    "event_type": "custom_business_event",
    "tournament_id": tournament.id,
    "player_count": len(tournament.players),
    "custom_label": "important_metric"
})
```

### Performance Monitoring

```python
import time

start_time = time.time()
# ... your code ...
duration = (time.time() - start_time) * 1000

logger.info("Operation completed", extra={
    "event_type": "performance",
    "operation": "tournament_calculation",
    "duration_ms": duration,
    "tournament_id": tournament.id
})
```

### Correlation IDs

The system automatically adds request IDs, but you can add custom correlation IDs:

```python
logger.info("Processing tournament", extra={
    "correlation_id": "tournament_processing_" + str(tournament.id),
    "tournament_id": tournament.id
})
```

## Troubleshooting

### Common Issues

1. **Logs not appearing in Grafana**
   - Check environment variables are set correctly
   - Verify Grafana credentials
   - Check Heroku logs for connection errors

2. **Performance impact**
   - Logs are batched and sent asynchronously
   - Adjust `LOKI_BATCH_SIZE` and `LOKI_FLUSH_INTERVAL` if needed

3. **Missing request IDs**
   - Ensure the LoggingMiddleware is added first in main.py
   - Request parameter must be passed to logging functions

### Testing Locally

To test Grafana integration locally:

1. Set the environment variables in your `.env` file
2. Run the application locally
3. Check your Grafana dashboard for incoming logs

### Log Volume Management

Monitor your Grafana Cloud usage to avoid overage charges:

1. Use appropriate log levels (avoid DEBUG in production)
2. Consider sampling for high-volume endpoints
3. Set up log retention policies in Grafana

## Security Considerations

1. **Never log sensitive data** - passwords, tokens, personal information
2. **Use environment variables** - never hardcode credentials
3. **Rotate API keys** - regularly update Grafana API keys
4. **Monitor access** - review who has access to your logs

## Best Practices

1. **Consistent naming** - Use consistent event types and logger names
2. **Structured data** - Always use the `extra` parameter for structured data
3. **Meaningful messages** - Write descriptive log messages
4. **Request context** - Always pass the request object when available
5. **Error handling** - Log errors with appropriate context and stack traces

## Monitoring Your Application

With this logging system, you can now monitor:

- **Application Performance** - Response times, throughput
- **User Behavior** - Login patterns, feature usage
- **Business Metrics** - Tournament activity, registrations
- **System Health** - Error rates, system resources
- **Security Events** - Failed logins, suspicious activity

Your PadelTour API now has enterprise-grade logging and monitoring capabilities! 🎉 