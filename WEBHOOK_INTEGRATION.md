# Strava Webhook Integration

## Overview
This app now uses **real-time webhooks** instead of polling to detect new Strava activities. This provides instant notifications when users complete runs, eliminating the need for 15-minute polling intervals.

## How It Works

### 1. Webhook Endpoint
- **URL**: `/webhooks/strava`
- **Methods**: GET (validation), POST (events)
- **Purpose**: Receives real-time notifications from Strava

### 2. Event Processing
When Strava sends a webhook for a new activity:
1. **Webhook received** → `/webhooks/strava` endpoint
2. **Event validated** → Strava signature verification
3. **Activity fetched** → Get full activity details from Strava API
4. **`run_complete()` called** → Main processing function
5. **Insights generated** → Activity analysis and metrics
6. **Database stored** → Notification saved for user

### 3. Key Components

#### StravaWebhookManager
- Handles webhook validation and event processing
- Manages Strava webhook subscriptions
- Calls `run_complete()` for new activities

#### run_complete() Function
- **Input**: user_id, activity_data
- **Output**: Processing results with insights
- **Purpose**: Main activity processing logic

## API Endpoints

### Webhook Endpoints
- `GET/POST /webhooks/strava` - Main webhook endpoint
- `POST /admin/webhooks/create` - Create webhook subscription
- `GET /admin/webhooks/status` - Check subscription status
- `DELETE /admin/webhooks/delete/<id>` - Delete subscription
- `POST /admin/webhooks/test` - Test with sample data

### Status Endpoints
- `GET /api/strava/status` - Get connection status across users

## Benefits vs Old Polling System

| Feature | Old Polling | New Webhooks |
|---------|-------------|--------------|
| **Latency** | 15 minutes | Instant |
| **API Calls** | Continuous | Only when needed |
| **Reliability** | Rate limit issues | Event-driven |
| **Scalability** | Poor | Excellent |
| **Real-time** | No | Yes |

## Setup Instructions

1. **Environment Variables**
   ```bash
   STRAVA_CLIENT_ID=your_client_id
   STRAVA_CLIENT_SECRET=your_client_secret
   STRAVA_WEBHOOK_VERIFY_TOKEN=your_verify_token
   ```

2. **Create Webhook Subscription**
   ```bash
   curl -X POST https://your-app.com/admin/webhooks/create \
     -H "Authorization: Bearer YOUR_API_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"callback_url": "https://your-app.com/webhooks/strava"}'
   ```

3. **Test the Integration**
   ```bash
   curl -X POST https://your-app.com/admin/webhooks/test \
     -H "Authorization: Bearer YOUR_API_TOKEN"
   ```

## Removed Components

The following polling-related files have been moved to `deprecated_polling/`:
- `strava_activity_monitor.py` - Old polling logic
- `strava_scheduler.py` - Flask-APScheduler integration  
- `STRAVA_MONITORING.md` - Old documentation

## Migration Notes

- ✅ **No data migration needed** - existing users work immediately
- ✅ **No UI changes** - same user experience
- ✅ **Better performance** - instant notifications
- ✅ **Cleaner codebase** - removed ~500 lines of polling code

## Troubleshooting

### Webhook Not Receiving Events
1. Check webhook subscription: `GET /admin/webhooks/status`
2. Verify callback URL is accessible from internet
3. Check Strava webhook verification token

### Events Not Processing
1. Check logs for `run_complete()` function
2. Verify user has valid Strava access token
3. Test with sample event: `POST /admin/webhooks/test`

---

🎉 **Real-time Strava integration is now live!** No more waiting for polls - activities are processed instantly when completed.
