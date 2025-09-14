# Jolt API Documentation

## Overview
The Jolt API allows third-party applications to access user data securely using Personal Access Tokens (PATs).

## Authentication
All API endpoints require authentication using a Personal Access Token in the Authorization header:

```
# Jolt API Documentation

This document describes the Jolt API endpoints for accessing user data and managing personal access tokens.

## Authentication

The API uses two types of authentication:

1. **Session Authentication**: For token management endpoints (requires login via web interface)
2. **Token Authentication**: For data access endpoints (requires personal access token)

### Personal Access Token Authentication

Include your token in the `Authorization` header:

```
Authorization: Bearer your_personal_access_token_here
```

## Token Management Endpoints

These endpoints require session authentication (user must be logged in via web interface).

### Get Token Status

Get information about your current personal access token.

```
GET /api/v1/token
```

**Headers:**
- Requires valid session (login via web interface)

**Response:**
```json
{
  "has_token": true,
  "token_info": {
    "id": "uuid",
    "created_at": "2024-01-01T00:00:00Z",
    "expires_at": "2025-01-01T00:00:00Z",
    "last_used_at": "2024-12-01T12:00:00Z",
    "is_active": true
  }
}
```

### Generate/Regenerate Token

Create a new personal access token or regenerate an existing one.

```
POST /api/v1/token
```

**Headers:**
- Requires valid session (login via web interface)

**Response:**
```json
{
  "success": true,
  "token": "jolt_pat_abcd1234efgh5678ijkl9012mnop3456",
  "message": "Token generated successfully",
  "expires_at": "2025-01-01T00:00:00Z",
  "warning": "This is the only time you will see this token. Store it securely!"
}
```

⚠️ **Important**: The token is only shown once. Store it securely!

### Revoke Token

Deactivate your current personal access token.

```
DELETE /api/v1/token
```

**Headers:**
- Requires valid session (login via web interface)

**Response:**
```json
{
  "success": true,
  "message": "Token revoked successfully"
}
```

## Data Access Endpoints

These endpoints require token authentication using your personal access token.

### Get User Profile

Retrieve your user profile information.

```
GET /api/v1/profile
```

**Headers:**
```
Authorization: Bearer your_personal_access_token_here
```

**Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### Get Activities

Retrieve your Strava activities (requires Strava connection).

```
GET /api/v1/activities
```

**Headers:**
```
Authorization: Bearer your_personal_access_token_here
```

**Response:**
```json
{
  "message": "Activities endpoint - integration with stored Strava tokens needed",
  "user_id": "user-uuid",
  "activities": []
}
```

### Get Running Statistics

Retrieve your running statistics and metrics.

```
GET /api/v1/stats
```

**Headers:**
```
Authorization: Bearer your_personal_access_token_here
```

**Response:**
```json
{
  "total_runs": 0,
  "total_distance": 0,
  "total_time": 0,
  "average_pace": 0,
  "user_id": "user-uuid"
}
```

### Get Email Address

Retrieve just your email address.

```
GET /api/v1/email
```

**Headers:**
```
Authorization: Bearer your_personal_access_token_here
```

**Response:**
```json
{
  "email": "user@example.com"
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "error": "Error message description"
}
```

Common HTTP status codes:
- `400`: Bad Request
- `401`: Unauthorized (invalid or missing token/session)
- `404`: Not Found
- `500`: Internal Server Error

## Usage Examples

### Using curl

1. **Generate a token** (after logging in via web interface):
```bash
curl -X POST https://your-app.onrender.com/api/v1/token 
  -H "Cookie: session=your_session_cookie"
```

2. **Get your profile**:
```bash
curl -X GET https://your-app.onrender.com/api/v1/profile 
  -H "Authorization: Bearer jolt_pat_abcd1234efgh5678ijkl9012mnop3456"
```

3. **Check token status**:
```bash
curl -X GET https://your-app.onrender.com/api/v1/token 
  -H "Cookie: session=your_session_cookie"
```

### Using Python

```python
import requests

# After generating token via web interface
API_BASE = "https://your-app.onrender.com"
TOKEN = "jolt_pat_abcd1234efgh5678ijkl9012mnop3456"

headers = {
    "Authorization": f"Bearer {TOKEN}"
}

# Get profile
response = requests.get(f"{API_BASE}/api/v1/profile", headers=headers)
profile = response.json()
print(profile)

# Get stats
response = requests.get(f"{API_BASE}/api/v1/stats", headers=headers)
stats = response.json()
print(stats)
```

### Using JavaScript

```javascript
const API_BASE = 'https://your-app.onrender.com';
const TOKEN = 'jolt_pat_abcd1234efgh5678ijkl9012mnop3456';

const headers = {
    'Authorization': `Bearer ${TOKEN}`,
    'Content-Type': 'application/json'
};

// Get profile
fetch(`${API_BASE}/api/v1/profile`, { headers })
    .then(response => response.json())
    .then(data => console.log(data));

// Get activities  
fetch(`${API_BASE}/api/v1/activities`, { headers })
    .then(response => response.json())
    .then(data => console.log(data));
```

## Rate Limiting

Currently, there are no rate limits implemented, but this may change in the future. Please use the API responsibly.

## Support

For API support or questions, please contact the development team or create an issue in the project repository.
```

## Getting a Token
1. Log into your Jolt account
2. Go to Home → API Token
3. Click "Generate API Token"
4. Copy and store the token securely (you'll only see it once)

## Base URL
- **Production:** `https://your-app.onrender.com`
- **Local Development:** `http://localhost:5000`

## Endpoints

### Get User Profile
**GET** `/api/v1/profile`

Returns the authenticated user's profile information.

**Example Request:**
```bash
curl -H "Authorization: Bearer jolt_pat_..." \
     https://your-app.onrender.com/api/v1/profile
```

**Example Response:**
```json
{
  "id": "user-uuid",
  "email": "user@example.com",
  "created_at": "2025-09-13T20:00:00Z"
}
```

### Get User Activities
**GET** `/api/v1/activities`

Returns the user's Strava activities (requires Strava connection).

**Example Request:**
```bash
curl -H "Authorization: Bearer jolt_pat_..." \
     https://your-app.onrender.com/api/v1/activities
```

**Example Response:**
```json
{
  "message": "Activities endpoint - integration with stored Strava tokens needed",
  "user_id": "user-uuid",
  "activities": []
}
```

### Get User Statistics
**GET** `/api/v1/stats`

Returns running statistics for the user.

**Example Request:**
```bash
curl -H "Authorization: Bearer jolt_pat_..." \
     https://your-app.onrender.com/api/v1/stats
```

**Example Response:**
```json
{
  "total_runs": 0,
  "total_distance": 0,
  "total_time": 0,
  "average_pace": 0,
  "user_id": "user-uuid"
}
```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Missing or invalid authorization header"
}
```

### 401 Token Invalid
```json
{
  "error": "Invalid token format"
}
```

### 401 Token Expired
```json
{
  "error": "Token has expired"
}
```

### 500 Internal Server Error
```json
{
  "error": "Error message"
}
```

## Rate Limiting
Currently no rate limiting is implemented, but may be added in the future.

## Token Management
- Each user can have only one active token at a time
- Tokens expire after 1 year
- Generating a new token invalidates the previous one
- Tokens can be revoked at any time through the web interface

## Security Best Practices
1. Store tokens securely (environment variables, secure vaults)
2. Never expose tokens in client-side code
3. Use HTTPS for all API requests
4. Regenerate tokens if they may have been compromised
5. Revoke tokens when no longer needed
