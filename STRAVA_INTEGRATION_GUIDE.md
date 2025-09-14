# Strava Integration - Best Practices Compliance

This document outlines how our Strava integration follows the official Strava API authentication best practices.

## ✅ **What We Implement Correctly**

### 1. **Proper OAuth 2.0 Flow**
- ✅ Using the correct 3-legged OAuth flow
- ✅ Proper authorization endpoint: `https://www.strava.com/oauth/authorize`
- ✅ Correct token exchange endpoint: `https://www.strava.com/oauth/token`
- ✅ Proper refresh token endpoint: `https://www.strava.com/oauth/token`

### 2. **Security Best Practices**
- ✅ **State Parameter**: We generate and verify a CSRF protection state parameter
- ✅ **Secure Storage**: Tokens stored in Supabase with RLS policies
- ✅ **Client Secret Protection**: Never exposed to frontend
- ✅ **Proper Error Handling**: Handle authorization errors gracefully

### 3. **Token Management**
- ✅ **Refresh Logic**: Automatically refresh tokens that expire within 1 hour (per Strava guidelines)
- ✅ **Refresh Token Updates**: Always use the most recent refresh token returned
- ✅ **Token Invalidation**: Proper cleanup when refresh fails
- ✅ **Expiration Tracking**: Store and check `expires_at` timestamps

### 4. **Scope Management**
- ✅ **Minimal Scopes**: Request only required scopes (`read,activity:read_all`)
- ✅ **Scope Storage**: Store granted scopes in database
- ✅ **Scope Verification**: Check which scopes were actually granted
- ✅ **Scope Validation**: Methods to verify required scopes are available

### 5. **Database Schema**
- ✅ **Separate Storage**: Tokens in dedicated `strava_credentials` table
- ✅ **User Isolation**: RLS policies ensure users only see their own tokens
- ✅ **Comprehensive Fields**: Store all necessary OAuth data
- ✅ **Activity Tracking**: Track last activity check for cron jobs

## 🔧 **Key Implementation Details**

### OAuth URL Construction
```
https://www.strava.com/oauth/authorize?
  client_id={CLIENT_ID}&
  response_type=code&
  redirect_uri={REDIRECT_URI}&
  approval_prompt=auto&           # Better UX than 'force'
  scope=read,activity:read_all&   # Minimal required scopes
  state={CSRF_TOKEN}              # CSRF protection
```

### Token Refresh Strategy
- Check if token expires within 1 hour (3600 seconds)
- If yes, refresh automatically
- Always use newest refresh token from response
- Handle 400/401 errors properly
- Mark credentials inactive if refresh fails

### Database Schema
```sql
CREATE TABLE strava_credentials (
    user_id UUID UNIQUE,
    access_token TEXT,
    refresh_token TEXT,
    expires_at TIMESTAMP,
    athlete_id BIGINT,
    athlete_data JSONB,
    scope TEXT,                    -- Store granted scopes
    last_activity_check TIMESTAMP, -- For cron jobs
    last_activity_id BIGINT,      -- Track latest seen activity
    is_active BOOLEAN
);
```

### Cron Job Architecture
- Use admin client to bypass RLS for system operations
- Track `last_activity_check` and `last_activity_id` per user
- Automatic token refresh during background checks
- Store activity notifications for later processing

## 🎯 **Advanced Features**

### 1. **Automated Activity Monitoring**
- Cron job checks for new activities every 15 minutes
- Uses stored tokens with automatic refresh
- Tracks latest activity ID to avoid duplicates
- Generates motivational messages based on activity type

### 2. **Proper Deauthorization**
- Call Strava's deauthorize endpoint
- Clean up local credentials
- Handle both success and failure cases

### 3. **Error Handling & Recovery**
- Graceful degradation when tokens expire
- Clear user feedback for authorization issues
- Automatic cleanup of invalid credentials
- Retry logic for temporary failures

### 4. **API Endpoints for Monitoring**
- `/cron/check-activities` - Check for new activities
- `/cron/send-notifications` - Process pending notifications
- `/api/strava/status` - Monitor connection status
- `/api/user/strava/notifications` - User notification history

## 🔐 **Security Considerations**

### Authentication
- All cron endpoints require API token authentication
- User-facing endpoints require session authentication
- Proper CSRF protection with state parameter

### Data Protection
- Row Level Security (RLS) on all tables
- Separate admin client for system operations
- No sensitive data in logs or error messages

### Token Security
- Tokens never stored in session (only in secure database)
- Automatic cleanup of expired credentials
- Proper token rotation following Strava guidelines

## 📚 **Strava Documentation Compliance**

Our implementation follows these specific Strava guidelines:

1. **Token Expiration**: "If the application's access tokens for the user are expired or will expire in one hour (3,600 seconds) or less, a new access token will be returned."

2. **Refresh Token Usage**: "Always use the most recent refresh token for subsequent requests to obtain a new access token."

3. **Scope Handling**: "Apps should check which scopes a user has accepted."

4. **Error Handling**: Proper handling of 400 (Bad Request) and 401 (Unauthorized) responses during token refresh.

5. **State Parameter**: Using state parameter for CSRF protection as recommended for security.

## 🚀 **Usage Examples**

### Setting up Cron Jobs
```bash
# Check for new activities every 15 minutes
*/15 * * * * curl -X POST -H "Authorization: Bearer YOUR_API_TOKEN" https://yourapp.com/cron/check-activities

# Send notifications every hour
0 * * * * curl -X POST -H "Authorization: Bearer YOUR_API_TOKEN" https://yourapp.com/cron/send-notifications
```

### Manual Activity Check
```python
# Get token manager instance
token_manager = StravaTokenManager(supabase, supabase_admin)

# Check if user has valid connection
if token_manager.is_connected(user_id):
    # Get valid access token (auto-refreshes if needed)
    access_token = token_manager.get_valid_access_token(user_id)
    
    # Use token for API calls
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get('https://www.strava.com/api/v3/athlete/activities', headers=headers)
```

This implementation provides a robust, secure, and Strava-compliant integration that handles all the edge cases and follows industry best practices.
