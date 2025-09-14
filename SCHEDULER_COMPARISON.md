# Strava Activity Monitoring: Flask Scheduler vs GitHub Actions

## TL;DR: Flask Scheduler is Better! 🎯

We've switched from GitHub Actions to Flask-APScheduler for these compelling reasons:

## 📊 **Comparison Table**

| Feature | Flask Scheduler | GitHub Actions |
|---------|----------------|----------------|
| **Setup Complexity** | ✅ Simple | ❌ Complex (secrets, YAML) |
| **Minimum Interval** | ✅ Any (seconds) | ❌ 5 minutes minimum |
| **Resource Usage** | ✅ Runs in your app | ❌ Uses GitHub compute |
| **State Persistence** | ✅ Warm starts | ❌ Cold starts |
| **Development** | ✅ Works locally | ❌ GitHub-only |
| **Error Handling** | ✅ Excellent | ❌ Limited |
| **Monitoring** | ✅ Built-in APIs | ❌ External monitoring |
| **Cost** | ✅ Free with your app | ❌ Uses GitHub minutes |

## 🚀 **Flask Scheduler Implementation**

### Installation
```bash
pip install Flask-APScheduler
```

### Features
- **15-minute activity checks** (vs 5-minute minimum in GitHub Actions)
- **5-minute notification processing**
- **Hourly health checks**
- **Built-in web API for management**
- **Automatic error recovery**
- **Development/production modes**

### Configuration
```python
# Environment variables
ENABLE_STRAVA_SCHEDULER=true  # Set to false for development
STRAVA_CHECK_INTERVAL=15      # Minutes between activity checks
NOTIFICATION_SEND_INTERVAL=5   # Minutes between notification sends
```

### Management Endpoints
```bash
# Check scheduler status
GET /admin/scheduler/status

# Start/stop scheduler
POST /admin/scheduler/start
POST /admin/scheduler/stop

# Manually trigger jobs
POST /admin/scheduler/trigger/check_strava_activities
POST /admin/scheduler/trigger/send_strava_notifications
```

## 🎛️ **How It Works**

### 1. **Automatic Startup**
```python
# In production (wsgi.py)
if strava_scheduler and os.getenv('ENABLE_STRAVA_SCHEDULER') == 'true':
    strava_scheduler.start_monitoring()
```

### 2. **Scheduled Jobs**
- **Activity Check**: Every 15 minutes
  - Fetches new activities for all users
  - Refreshes expired tokens automatically
  - Stores notifications for processing

- **Notification Send**: Every 5 minutes  
  - Processes pending notifications
  - Marks notifications as sent
  - Handles delivery failures

- **Health Check**: Every hour
  - Reports active user count
  - Monitors system health
  - Logs status information

### 3. **Error Handling**
```python
# Automatic recovery features
'coalesce': True,           # Combine missed executions
'max_instances': 1,         # Prevent job overlap
'misfire_grace_time': 300   # 5-minute grace period
```

## 🔧 **Usage Examples**

### Local Development
```bash
# Disable scheduler for development
echo "ENABLE_STRAVA_SCHEDULER=false" >> .env

# Or run with scheduler enabled
python app.py
```

### Production Deployment
```bash
# Render.com / Heroku / etc.
gunicorn wsgi:app

# The scheduler starts automatically
```

### Manual Job Triggers
```bash
# Using your API token
curl -X POST \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  https://yourapp.com/admin/scheduler/trigger/check_strava_activities
```

## 📈 **Benefits Over GitHub Actions**

### 1. **Better Performance**
- No cold starts
- Persistent database connections
- Shared memory between jobs

### 2. **Simpler Architecture**
```
GitHub Actions Approach:
GitHub Cron → External API Call → Your App → Database

Flask Scheduler Approach:
Your App → Internal Function → Database
```

### 3. **Enhanced Monitoring**
```python
# Real-time job status
{
  "scheduler_running": true,
  "jobs": [
    {
      "id": "check_strava_activities",
      "name": "Check Strava Activities", 
      "next_run": "2025-09-14T15:30:00",
      "trigger": "interval[0:15:00]"
    }
  ]
}
```

### 4. **Development Friendly**
- Works in local development
- Easy debugging with breakpoints
- Immediate testing of changes

## 🚨 **Migration from GitHub Actions**

### What to Remove
```bash
# Delete these files
rm .github/workflows/strava_monitor.yml
rm cron_strava.py
```

### What to Update
```yaml
# render.yaml - Change start command
startCommand: gunicorn wsgi:app  # Instead of app:app
```

### Environment Variables
```bash
# Add to your deployment
ENABLE_STRAVA_SCHEDULER=true
SUPABASE_SERVICE_KEY=your_service_key  # If not already set
```

## 🛡️ **Production Considerations**

### 1. **Memory Usage**
- Scheduler runs in same process as Flask app
- Minimal memory overhead
- Monitor with your existing app monitoring

### 2. **Scaling**
- Works with single instance deployments
- For multi-instance: use external job queue (Celery/RQ)
- Current implementation perfect for most use cases

### 3. **Reliability**
- Jobs continue across app restarts
- Automatic recovery from failures
- Configurable retry logic

## 🎯 **Conclusion**

**Flask Scheduler wins because:**
- ✅ **Simpler**: No external dependencies
- ✅ **Faster**: No cold starts or API calls
- ✅ **Flexible**: Any interval, better control
- ✅ **Cheaper**: No external compute costs
- ✅ **Debuggable**: Works in development
- ✅ **Maintainable**: All code in one place

The only scenario where GitHub Actions might be better is if you need the scheduler to run even when your app is down - but that's rarely the case since the app needs to be up to process the API calls anyway!

**Recommendation**: Use Flask scheduler for this use case. It's the right tool for the job! 🚀
