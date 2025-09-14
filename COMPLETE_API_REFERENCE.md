# 🚀 Jolt API Complete Reference

This document provides a comprehensive list of all API endpoints in the Jolt application, organized by category and authentication type.

## 📋 Authentication Types

- **🔑 Token-based**: Requires `Authorization: Bearer <token>` header
- **🍪 Session-based**: Requires browser login session
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

## 🍪 Session-Based API Endpoints

### Strava Integration
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/strava/activities` | Get Strava activities with detailed data | Session |
| `GET` | `/api/strava/status` | Get Strava connection status | Session |

### Analytics & Performance
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/analytics/comprehensive` | Comprehensive training analytics | Session |
| `GET` | `/api/analytics/summary` | Training summary statistics | Session |
| `GET` | `/api/analytics/performance-trends` | Performance trends over time | Session |

### Psychology Analysis
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/psychology/analysis` | Performance psychology analysis | Session |
| `GET` | `/api/psychology/performance-events` | Performance events with context | Session |
| `GET` | `/api/psychology/split-analysis/<activity_id>` | Detailed split analysis | Session |
| `GET` | `/api/psychology/insights` | Psychology insights and recommendations | Session |

### Nutrition Tracking
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/nutrition/dashboard` | Nutrition dashboard data | Session |
| `GET` | `/api/nutrition/insights` | Nutrition insights and analysis | Session |
| `POST` | `/api/nutrition/log-meal` | Log a new meal | Session |
| `GET` | `/api/nutrition/daily-summary` | Daily nutrition summary | Session |
| `GET` | `/api/nutrition/trends` | Nutrition trends over time | Session |
| `GET` | `/api/nutrition/patterns` | Nutrition patterns and habits | Session |

### User Notifications
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `GET` | `/api/user/strava/notifications` | Get user's Strava notifications | Session |

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

### **Total: 36 API Endpoints**

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
