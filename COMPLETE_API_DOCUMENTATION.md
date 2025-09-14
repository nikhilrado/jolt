# Complete API Documentation for MCP Integration

## Overview
This document describes all JSON API endpoints available for MCP (Master Control Program) integration. All endpoints return JSON responses that can be directly consumed by your MCP and Poke.

## Base URL
```
http://localhost:5001/api/
```

## Authentication
- Most endpoints require user session authentication
- Use Flask session cookies for authentication
- Some endpoints work without authentication for analysis-only operations

---

## Strava Integration Endpoints

### 1. Get Strava Activities
**Endpoint:** `GET /api/strava/activities`

**Description:** Get detailed Strava activities with enhanced data including splits, heart rate zones, and performance metrics.

**Authentication:** Required (user session + Strava connected)

**Response:**
```json
{
    "success": true,
    "total_activities": 20,
    "activities": [
        {
            "id": 123456789,
            "name": "Morning Run",
            "type": "Run",
            "distance": 5000,
            "moving_time": 1800,
            "elapsed_time": 1900,
            "total_elevation_gain": 50,
            "start_date": "2024-01-15T06:00:00Z",
            "average_speed": 2.78,
            "max_speed": 4.5,
            "average_cadence": 180,
            "average_heartrate": 150,
            "max_heartrate": 175,
            "average_watts": 200,
            "max_watts": 300,
            "calories": 400,
            "suffer_score": 5,
            "kudos_count": 15,
            "comment_count": 3,
            "gear": {
                "id": "g123456",
                "name": "Nike Air Zoom"
            },
            "mile_splits": [
                {"mile": 1, "time": 360, "pace": "6:00"},
                {"mile": 2, "time": 365, "pace": "6:05"}
            ],
            "heart_rate_zones": {
                "zone_1": 120,
                "zone_2": 300,
                "zone_3": 600,
                "zone_4": 300,
                "zone_5": 180
            }
        }
    ]
}
```

---

## Analytics Endpoints

### 2. Comprehensive Training Analytics
**Endpoint:** `GET /api/analytics/comprehensive?days=90`

**Description:** Get comprehensive sports science analytics including training load, performance curves, and recommendations.

**Authentication:** Required (user session + Strava connected)

**Query Parameters:**
- `days`: Time period (7, 14, 30, 60, 90, 180, 365) - default: 90

**Response:**
```json
{
    "success": true,
    "analysis_period": "90 days",
    "training_load": {
        "atl": 45.2,
        "ctl": 52.8,
        "tsb": 7.6,
        "acwr": 0.86,
        "monotony": 1.2,
        "strain": 54.2
    },
    "intensity_zones": {
        "zone_1_percentage": 25.5,
        "zone_2_percentage": 35.2,
        "zone_3_percentage": 22.1,
        "zone_4_percentage": 12.8,
        "zone_5_percentage": 4.4
    },
    "performance_curves": {
        "best_5k": "18:45",
        "best_10k": "39:20",
        "best_half_marathon": "1:28:15",
        "best_marathon": "3:05:30"
    },
    "volume_trends": {
        "weekly_volume": 45.2,
        "monthly_volume": 180.8,
        "volume_trend": "increasing"
    },
    "consistency": {
        "training_frequency": 4.2,
        "consistency_score": 85.5,
        "longest_gap": 3
    },
    "terrain_analysis": {
        "avg_elevation_gain": 125.5,
        "hill_percentage": 15.2,
        "flat_percentage": 65.8
    },
    "cadence_analysis": {
        "avg_cadence": 175.2,
        "cadence_consistency": 78.5,
        "optimal_cadence_range": "170-180"
    },
    "wellness_score": 78.5,
    "readiness_score": 82.3,
    "recommendations": [
        "Increase training volume by 10% for next 4 weeks",
        "Focus on Zone 2 training for aerobic base building",
        "Add strength training 2x per week"
    ]
}
```

---

## Psychology Analysis Endpoints

### 3. Performance Psychology Analysis
**Endpoint:** `GET /api/psychology/analysis?days=30`

**Description:** Get performance psychology analysis including mental patterns, performance events, and psychological recommendations.

**Authentication:** Required (user session + Strava connected)

**Query Parameters:**
- `days`: Time period (7, 14, 30, 60, 90, 180) - default: 30

**Response:**
```json
{
    "success": true,
    "analysis_period": "30 days",
    "performance_events": [
        {
            "event_type": "split_degradation",
            "activity_id": 123456789,
            "description": "Pace slowed significantly in final 2 miles",
            "severity": "moderate",
            "objective_data": {
                "mile_1_pace": "6:00",
                "mile_2_pace": "6:05",
                "mile_3_pace": "6:45",
                "mile_4_pace": "7:15"
            }
        }
    ],
    "wellness_insights": {
        "stress_level": "moderate",
        "motivation_trend": "increasing",
        "sleep_quality": "good",
        "recovery_status": "adequate"
    },
    "psychological_patterns": {
        "mental_toughness_score": 78.5,
        "consistency_mindset": "strong",
        "goal_adherence": 85.2,
        "pressure_handling": "good"
    },
    "recommendations": [
        "Practice positive self-talk during challenging moments",
        "Implement pre-race visualization techniques",
        "Focus on process goals rather than outcome goals"
    ],
    "summary": {
        "total_events": 3,
        "mental_trend": "improving",
        "key_strengths": ["Consistency", "Goal Setting"],
        "areas_for_improvement": ["Race Day Nerves", "Mid-Race Focus"]
    }
}
```

---

## Nutrition Endpoints

### 4. Nutrition Dashboard
**Endpoint:** `GET /api/nutrition/dashboard?days=7`

**Description:** Get nutrition dashboard data with trends and averages.

**Authentication:** Required (user session)

**Query Parameters:**
- `days`: Time period (1, 3, 7, 14, 30) - default: 7

**Response:**
```json
{
    "success": true,
    "analysis_period": "7 days",
    "trends": [
        {
            "date": "2024-01-15",
            "total_meals": 3,
            "total_calories": 1850,
            "total_carbs": 185,
            "total_fats": 68,
            "total_protein": 95,
            "macro_breakdown": {
                "carbs_percentage": 40.0,
                "fats_percentage": 33.1,
                "protein_percentage": 20.5
            }
        }
    ],
    "averages": {
        "calories": 1850.3,
        "carbs": 185.7,
        "fats": 68.4,
        "protein": 95.2
    },
    "summary": {
        "total_days": 7,
        "total_meals": 21,
        "avg_daily_calories": 1850.3
    }
}
```

### 5. Nutrition Insights
**Endpoint:** `GET /api/nutrition/insights?days=30`

**Description:** Get comprehensive nutrition insights and pattern analysis.

**Authentication:** Required (user session)

**Query Parameters:**
- `days`: Time period (7, 14, 30, 60, 90) - default: 30

**Response:**
```json
{
    "success": true,
    "analysis_period": "30 days",
    "insights": {
        "trends": [...],
        "pattern_analysis": {
            "insights": [
                "Good calorie range (1850 daily average)",
                "Good protein balance (22.3% of calories)",
                "Good consistency in daily calorie intake"
            ],
            "patterns": {
                "avg_calories": 1850.3,
                "avg_protein": 95.2,
                "avg_carbs": 185.7,
                "avg_fats": 68.4,
                "avg_meals_per_day": 3.2,
                "calorie_consistency": "high",
                "protein_consistency": "medium",
                "macro_balance": {
                    "protein_pct": 22.3,
                    "carb_pct": 40.1,
                    "fat_pct": 33.2
                }
            },
            "recommendations": [
                "Add healthy fats: nuts, seeds, olive oil, avocado",
                "Consider adding healthy snacks between meals"
            ]
        },
        "weekly_patterns": {
            "avg_calories": 1850.3,
            "avg_protein": 95.2,
            "avg_carbs": 185.7,
            "avg_fats": 68.4,
            "total_meals": 21
        },
        "summary": {
            "total_days_analyzed": 30,
            "total_meals_logged": 96,
            "avg_daily_calories": 1850.3
        }
    }
}
```

---

## CalorieNinjas Integration Endpoints

### 6. Analyze Meal (No Save)
**Endpoint:** `POST /api/mcp/nutrition/analyze`

**Description:** Analyze meal description using CalorieNinjas API without saving to database.

**Authentication:** None required

**Request Body:**
```json
{
    "meal_description": "grilled chicken breast with brown rice and steamed broccoli"
}
```

**Response:**
```json
{
    "success": true,
    "meal_description": "grilled chicken breast with brown rice and steamed broccoli",
    "analysis": {
        "name": "chicken breast, brown rice, broccoli",
        "calories": 420,
        "carbs": 45,
        "fats": 12,
        "protein": 35,
        "sodium": 450,
        "fiber": 8,
        "sugar": 2,
        "ingredients": [
            {
                "name": "chicken breast",
                "calories": 165,
                "protein_g": 31,
                "fat_total_g": 3.6,
                "carbohydrates_total_g": 0,
                "fiber_g": 0,
                "sodium_mg": 74
            }
        ],
        "health_recommendations": [
            "High protein content - great for muscle building and satiety!",
            "Excellent fiber content - great for digestive health!"
        ]
    }
}
```

### 7. Analyze and Save Meal
**Endpoint:** `POST /api/mcp/nutrition/analyze-and-save`

**Description:** Analyze meal and save to user's nutrition log.

**Authentication:** Required (user session)

**Request Body:**
```json
{
    "meal_description": "grilled chicken breast with brown rice and steamed broccoli"
}
```

**Response:**
```json
{
    "success": true,
    "meal_description": "grilled chicken breast with brown rice and steamed broccoli",
    "saved_meal_id": 123,
    "analysis": {
        "name": "chicken breast, brown rice, broccoli",
        "calories": 420,
        "carbs": 45,
        "fats": 12,
        "protein": 35,
        "sodium": 450,
        "fiber": 8,
        "sugar": 2,
        "ingredients": [...],
        "health_recommendations": [...]
    }
}
```

### 8. Batch Analyze Meals
**Endpoint:** `POST /api/mcp/nutrition/batch-analyze`

**Description:** Analyze multiple meal descriptions in batch (max 10 meals).

**Authentication:** None required

**Request Body:**
```json
{
    "meal_descriptions": [
        "grilled chicken breast with brown rice",
        "Greek yogurt with berries and granola",
        "salmon with quinoa and asparagus"
    ]
}
```

**Response:**
```json
{
    "success": true,
    "total_meals": 3,
    "successful_analyses": 3,
    "failed_analyses": 0,
    "results": [
        {
            "index": 0,
            "meal_description": "grilled chicken breast with brown rice",
            "success": true,
            "analysis": {
                "name": "chicken breast, brown rice",
                "calories": 350,
                "carbs": 35,
                "fats": 8,
                "protein": 28,
                "sodium": 320,
                "fiber": 3,
                "sugar": 1,
                "ingredients": [...],
                "health_recommendations": [...]
            }
        }
    ]
}
```

### 9. Health Recommendations
**Endpoint:** `POST /api/mcp/nutrition/health-recommendations`

**Description:** Get health recommendations for nutritional data.

**Authentication:** None required

**Request Body:**
```json
{
    "calories": 420,
    "carbs": 45,
    "fats": 12,
    "protein": 35,
    "sodium": 450,
    "fiber": 8,
    "sugar": 2
}
```

**Response:**
```json
{
    "success": true,
    "nutritional_data": {
        "calories": 420,
        "carbs": 45,
        "fats": 12,
        "protein": 35,
        "sodium": 450,
        "fiber": 8,
        "sugar": 2
    },
    "macro_breakdown": {
        "protein_percentage": 33.3,
        "carb_percentage": 42.9,
        "fat_percentage": 25.7
    },
    "health_recommendations": [
        "High protein content - great for muscle building and satiety!",
        "Excellent fiber content - great for digestive health!",
        "Low sodium content - good for heart health"
    ]
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
    "error": "Error message description"
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request (missing or invalid data)
- `401` - Unauthorized (authentication required)
- `500` - Internal Server Error

---

## Usage Examples

### Python Example - Get All Data
```python
import requests

# Get Strava activities
activities = requests.get('http://localhost:5001/api/strava/activities')
print(f"Activities: {activities.json()}")

# Get comprehensive analytics
analytics = requests.get('http://localhost:5001/api/analytics/comprehensive?days=30')
print(f"Analytics: {analytics.json()}")

# Get psychology analysis
psychology = requests.get('http://localhost:5001/api/psychology/analysis?days=30')
print(f"Psychology: {psychology.json()}")

# Get nutrition insights
nutrition = requests.get('http://localhost:5001/api/nutrition/insights?days=30')
print(f"Nutrition: {nutrition.json()}")

# Analyze a meal
meal_analysis = requests.post('http://localhost:5001/api/mcp/nutrition/analyze', 
                             json={'meal_description': 'grilled chicken with rice'})
print(f"Meal Analysis: {meal_analysis.json()}")
```

### JavaScript Example
```javascript
// Get all user data
async function getAllUserData() {
    const [activities, analytics, psychology, nutrition] = await Promise.all([
        fetch('http://localhost:5001/api/strava/activities').then(r => r.json()),
        fetch('http://localhost:5001/api/analytics/comprehensive?days=30').then(r => r.json()),
        fetch('http://localhost:5001/api/psychology/analysis?days=30').then(r => r.json()),
        fetch('http://localhost:5001/api/nutrition/insights?days=30').then(r => r.json())
    ]);
    
    return {
        activities,
        analytics,
        psychology,
        nutrition
    };
}
```

---

## Integration Notes

1. **Session Management:** Use Flask session cookies for authentication
2. **Rate Limiting:** CalorieNinjas API has rate limits; batch requests limited to 10 meals
3. **Data Types:** All nutritional values are integers (rounded from decimals)
4. **Error Handling:** Always check the `success` field in responses
5. **Time Periods:** Use valid period values as specified in each endpoint
6. **Performance:** Large datasets are limited (e.g., 20 activities max)

This API provides complete access to all fitness, nutrition, and psychology data for comprehensive MCP integration! 🚀📊🤖
