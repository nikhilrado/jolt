# Strava Activity Monitoring System

This system automatically monitors connected Strava accounts for new activities and can trigger notifications or actions when new runs, rides, or other activities are detected.

## Features

- **Database-stored credentials**: Strava OAuth tokens are securely stored in Supabase instead of session storage
- **Automatic token refresh**: Expired tokens are automatically refreshed using refresh tokens
- **Cron job monitoring**: Check for new activities every 15 minutes
- **Activity notifications**: Generate motivational messages for new activities
- **API endpoints**: RESTful endpoints for monitoring and management

## Database Schema

The system adds two new tables to your Supabase database:

### `strava_credentials`
Stores OAuth tokens and athlete information for each user.

### `activity_notifications`
Tracks detected activities and notification status.

## Setup Instructions

### 1. Database Migration

Run the database migration to create the required tables:

```sql
-- Apply the migration from database/migration_002_strava_credentials.sql
```

### 2. Environment Variables

Ensure these environment variables are set:

```bash
STRAVA_CLIENT_ID=your_strava_app_client_id
STRAVA_CLIENT_SECRET=your_strava_app_client_secret
STRAVA_REDIRECT_URI=http://localhost:5000/strava/callback
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_anon_key
SUPABASE_SERVICE_KEY=your_supabase_service_role_key
```

### 3. Generate API Token

To use the cron job endpoints, you'll need a Personal Access Token:

1. Log into your Jolt account
2. Go to `/api-token`
3. Generate a new token
4. Save the token securely

### 4. Cron Job Setup

#### Option A: GitHub Actions (Recommended)

1. Set up repository secrets in GitHub:
   - `JOLT_API_URL`: Your deployed app URL (e.g., `https://your-app.render.com`)
   - `JOLT_API_TOKEN`: Your generated API token

2. The workflow in `.github/workflows/strava_monitor.yml` will automatically:
   - Check for new activities every 15 minutes
   - Send notifications for detected activities
   - Provide status updates

#### Option B: External Cron Service

Use services like:
- **EasyCron**: Web-based cron service
- **Cronhub**: Reliable cron monitoring
- **Your own server**: Traditional cron setup

Example cron commands:
```bash
# Check for new activities every 15 minutes
*/15 * * * * python3 /path/to/cron_strava.py check

# Send notifications every 15 minutes (offset by 5 minutes)
5,20,35,50 * * * * python3 /path/to/cron_strava.py notify
```

#### Option C: Local Development

For testing locally:
```bash
# Check activities
python3 cron_strava.py check

# Send notifications
python3 cron_strava.py notify

# Get status
python3 cron_strava.py status
```

## API Endpoints

### Cron Job Endpoints (Require API Token)

- `POST /cron/check-activities`: Check for new activities across all users
- `POST /cron/send-notifications`: Send pending notifications
- `GET /api/strava/status`: Get connection status for all users

### User Endpoints (Require Login)

- `GET /api/user/strava/notifications`: Get activity notifications for current user
- `GET /strava/connect`: Connect Strava account
- `GET /strava/activities`: View Strava activities

## How It Works

1. **User Connects Strava**: OAuth flow stores access/refresh tokens in database
2. **Cron Job Runs**: Every 15 minutes, checks for new activities
3. **Activity Detection**: Compares with last known activity ID for each user
4. **Notification Generation**: Creates motivational messages based on activity type
5. **Notification Sending**: Marks notifications as sent (extend for actual delivery)

## Activity Message Examples

The system generates contextual messages based on activity type and metrics:

- **Running**: "🏃‍♂️ Incredible! You just completed a 21.2km run! That's marathon-level dedication! 💪"
- **Cycling**: "🚴‍♂️ Epic century ride! 102.5km - you're absolutely crushing it! 🔥"
- **Swimming**: "🏊‍♂️ Awesome swim session! Water time is the best time! 🌊"

## Extending the System

### Custom Notifications

To implement actual notifications (email, SMS, push, etc.), modify the `cron_send_notifications()` function in `app.py`.

### Webhook Integration

Add webhook endpoints to integrate with services like:
- Slack/Discord for team notifications
- Email services (SendGrid, Mailgun)
- Push notification services
- Custom analytics platforms

### Activity Analysis

The system stores full activity data, enabling:
- Performance trend analysis
- Goal tracking
- Social features
- Integration with other fitness apps

## Security Considerations

- API tokens have expiration dates and usage tracking
- Strava tokens are automatically refreshed
- Row Level Security (RLS) ensures users only see their own data
- Service role key used only for system operations

## Troubleshooting

### Common Issues

1. **"Strava connection expired"**: User needs to reconnect their account
2. **Cron job failures**: Check API token validity and network connectivity
3. **Missing activities**: Verify token scopes include `activity:read_all`

### Monitoring

Use the status endpoint to monitor system health:
```bash
curl -H "Authorization: Bearer YOUR_API_TOKEN" \
     https://your-app.com/api/strava/status
```

## Development Notes

- Uses `strava_token_manager.py` for credential management
- Uses `strava_activity_monitor.py` for activity checking
- All Strava API calls automatically handle token refresh
- Database operations use admin client to bypass RLS when needed
