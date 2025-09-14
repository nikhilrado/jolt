# 🚀 Jolt API Complete Reference

This document provides a comprehensive list of all API endpoints in the Jolt application, organized by category and authentication type.

## 📋 Authentication Types

- **🔑 Token-based**: Requires `Authorization: Bearer <token>` header (Primary authentication method)
- **🍪 Session-based**: Requires browser login session (Legacy - for web UI only)
- **🌐 Public**: No authentication required

---

## 🔑 Token-Based API Endpoints (v1 API)

### User Profile & Management
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/profile` | Get user profile information | Token |
| `GET` | `/api/v1/email` | Get user email address | Token |
| `GET` | `/api/v1/activities` | Get user's Strava activities | Token |
| `GET` | `/api/v1/stats` | Get user's running statistics | Token |

### Token Management
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/v1/token` | Get user's API tokens | Token |
| `POST` | `/api/v1/token` | Generate new API token | Token |
| `DELETE` | `/api/v1/token` | Revoke API token | Token |

---

## 🔑 Token-Based API Endpoints (All Data Access)

### Strava Integration
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/strava/activities` | Get Strava activities with detailed data | Token |
| `GET` | `/api/strava/status` | Get Strava connection status | Token |
| `GET` | `/strava/activities` | Get Strava activities (Legacy session-based) | Session |

### Webhook Management
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET/POST` | `/webhooks/strava` | Handle Strava webhook events | Public |
| `POST` | `/admin/webhooks/create` | Create webhook subscription | Token |
| `GET` | `/admin/webhooks/status` | Get webhook subscription status | Token |
| `DELETE` | `/admin/webhooks/delete/<id>` | Delete webhook subscription | Token |
| `POST` | `/admin/webhooks/test` | Test webhook processing | Token |

### Analytics & Performance
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/analytics/comprehensive` | Comprehensive training analytics | Token |
| `GET` | `/api/analytics/summary` | Training summary statistics | Token |
| `GET` | `/api/analytics/performance-trends` | Performance trends over time | Token |

### Psychology Analysis
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/psychology/analysis` | Performance psychology analysis | Token |
| `GET` | `/api/psychology/performance-events` | Performance events with context | Token |
| `GET` | `/api/psychology/split-analysis/<activity_id>` | Detailed split analysis | Token |
| `GET` | `/api/psychology/insights` | Psychology insights and recommendations | Token |
| `POST` | `/api/psychology/submit-wellness` | Submit wellness/feeling data | Token |
| `POST` | `/api/psychology/analyze-feelings` | Analyze feelings and get personalized insights | Token |

### Nutrition Tracking
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/nutrition/dashboard` | Nutrition dashboard data | Token |
| `GET` | `/api/nutrition/insights` | Nutrition insights and analysis | Token |
| `POST` | `/api/nutrition/log-meal` | Log a new meal | Token |
| `GET` | `/api/nutrition/daily-summary` | Daily nutrition summary | Token |
| `GET` | `/api/nutrition/trends` | Nutrition trends over time | Token |
| `GET` | `/api/nutrition/patterns` | Nutrition patterns and habits | Token |

### User Notifications
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/user/strava/notifications` | Get user's Strava notifications | Token |

## 🍪 Session-Based Endpoints (Legacy - Web UI Only)

### Web Interface
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/home` | Home page | Session |
| `GET` | `/api-token` | Token management page | Session |
| `POST` | `/api-token/generate` | Generate token (UI) | Session |
| `POST` | `/api-token/revoke` | Revoke token (UI) | Session |

---

## 🌐 Public API Endpoints (MCP/CalorieNinjas)

### Nutrition Analysis
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/mcp/nutrition/analyze` | Analyze meal nutrition | Public |
| `POST` | `/api/mcp/nutrition/analyze-and-save` | Analyze and save meal | Session |
| `POST` | `/api/mcp/nutrition/batch-analyze` | Analyze multiple meals | Public |
| `POST` | `/api/mcp/nutrition/health-recommendations` | Get health recommendations | Public |

---

## 🔧 Administrative & Cron Endpoints

### Cron Jobs (Background Tasks)
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/cron/check-activities` | Check for new Strava activities | Token |
| `POST` | `/cron/send-notifications` | Send pending notifications | Token |

### Scheduler Management
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/admin/scheduler/status` | Get scheduler status | Token |
| `POST` | `/admin/scheduler/start` | Start scheduler | Token |
| `POST` | `/admin/scheduler/stop` | Stop scheduler | Token |
| `POST` | `/admin/scheduler/trigger/<job_id>` | Trigger specific job | Token |
| `GET` | `/admin/scheduler` | Scheduler admin interface | Session |

---

## 🎯 Web Interface Endpoints

### Token Management UI
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api-token` | API token management page | Session |
| `POST` | `/api-token/generate` | Generate new token (UI) | Session |
| `POST` | `/api-token/revoke` | Revoke token (UI) | Session |

---

## 📊 Endpoint Summary

### By Authentication Type:
- **🔑 Token-based**: 7 endpoints
- **🍪 Session-based**: 15 endpoints  
- **🌐 Public**: 4 endpoints
- **🔧 Admin/Cron**: 7 endpoints
- **🎯 Web UI**: 3 endpoints

### **Total: 43 API Endpoints**

---

## 🚀 **MIGRATION COMPLETE: Session → Token Authentication**

### **✅ What Changed:**
- **All data access endpoints** now use token-based authentication
- **Session-based authentication** is now legacy (web UI only)
- **Enhanced security** with proper token validation
- **Better scalability** for mobile apps and third-party integrations

### **🔧 Technical Changes:**
- Added `@require_token_auth` decorator for enhanced token validation
- Updated all endpoints to use `request.current_user_id` instead of `session['user']['id']`
- Integrated webhook-based Strava monitoring (replacing polling system)
- Added comprehensive webhook management endpoints
- Maintained backward compatibility for web UI
- All existing functionality preserved

### **🆕 New Webhook Features:**
- **Real-time Strava activity monitoring** via webhooks
- **Webhook subscription management** with full CRUD operations
- **Automatic activity processing** without polling
- **Enhanced scalability** and reduced API rate limiting
- **Better reliability** with event-driven architecture

---

## 🧠 New Psychology Endpoints (User Input)

### **Submit Wellness Data**
**Endpoint:** `POST /api/psychology/submit-wellness`

**Description:** Submit your current feelings and wellness data for psychology analysis.

**Request Body:**
```json
{
  "mood": 7,           // 1-10 scale (1=very low, 10=excellent)
  "stress": 4,          // 1-10 scale (1=no stress, 10=extremely stressed)  
  "motivation": 8,      // 1-10 scale (1=no motivation, 10=highly motivated)
  "sleep_quality": 6,   // 1-10 scale (1=poor sleep, 10=excellent sleep)
  "soreness": 3,        // 1-10 scale (1=no soreness, 10=very sore)
  "perceived_effort": 5 // 1-10 scale (1=very easy, 10=maximum effort)
}
```

**Response:**
```json
{
  "success": true,
  "message": "Wellness data submitted successfully",
  "data": { /* submitted data */ }
}
```

### **Analyze Feelings**
**Endpoint:** `POST /api/psychology/analyze-feelings`

**Description:** Submit your feelings and get personalized psychological insights and recommendations.

**Request Body:** Same as submit-wellness endpoint

**Response:**
```json
{
  "success": true,
  "submitted_wellness_data": { /* your input */ },
  "personalized_insights": [
    {
      "type": "mood_support",
      "title": "Low Mood Detected", 
      "message": "Your mood is quite low today...",
      "recommendations": [
        "Try a gentle walk or easy run",
        "Focus on activities that bring you joy"
      ]
    }
  ],
  "performance_analysis": {
    "analysis_period": "7 days",
    "total_activities": 5,
    "psychological_insights": [ /* detailed insights */ ]
  },
  "recommendations": [ /* general recommendations */ ],
  "wellness_trends": [ /* trend analysis */ ]
}
```

### **Example Usage:**
```bash
# Submit how you're feeling
curl -X POST -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{
    "mood": 3,
    "stress": 8, 
    "motivation": 2,
    "sleep_quality": 4,
    "soreness": 6,
    "perceived_effort": 7
  }' \
  http://localhost:5001/api/psychology/analyze-feelings
```

### **Personalized Insights Types:**
- **`mood_support`**: When mood < 4, provides gentle exercise recommendations
- **`mood_positive`**: When mood > 7, suggests challenging workouts
- **`stress_management`**: When stress > 7, recommends stress-relieving activities
- **`motivation_boost`**: When motivation < 4, provides motivation-building tips

---

## 🧪 Testing Your Endpoints

### Token-Based Testing:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:5001/api/v1/profile
```

### Public Endpoint Testing:
```bash
curl -X POST -H "Content-Type: application/json" \
  -d '{"meal_description": "grilled chicken breast"}' \
  http://localhost:5001/api/mcp/nutrition/analyze
```

### Session-Based Testing:
1. Login via browser at `http://localhost:5001`
2. Connect Strava account
3. Use browser dev tools to get session cookie
4. Test endpoints with session cookie

---

## 🚀 New Features from Merge

Your friend's code added these new capabilities:

### **Strava Token Management:**
- Better token storage and refresh
- Automatic token validation
- Proper disconnection handling

### **Background Monitoring:**
- Automated Strava activity checking
- Scheduled notification sending
- Health monitoring and status checks

### **Admin Interface:**
- Scheduler management
- Job monitoring and control
- System status endpoints

### **Enhanced Security:**
- Proper token-based authentication
- Session management improvements
- Better error handling

---

## 📝 Notes

- All endpoints return JSON responses
- Error responses include descriptive error messages
- Session-based endpoints require Strava connection for full functionality
- Token-based endpoints work independently of browser sessions
- Public endpoints (MCP) provide nutrition analysis without authentication

Your Jolt API is now a comprehensive fitness and nutrition tracking platform! 🎉
