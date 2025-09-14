# MCP Nutrition API Documentation

## Overview
This document describes the MCP (Master Control Program) API endpoints for nutrition analysis using CalorieNinjas integration.

## Environment Setup

Add these variables to your `.env` file:

```bash
# CalorieNinjas API Configuration
CALORIE_NINJAS_API_URL=https://api.calorieninjas.com/v1/nutrition
CALORIE_NINJAS_API_KEY=5Ynu/fNeNzAzsZNgLJBFNQ==wVr0G2WIEm9jCzhJ
```

## Base URL
```
http://localhost:5001/api/mcp/nutrition/
```

## Authentication
- Most endpoints require user session authentication
- Use Flask session cookies for authentication
- Some endpoints work without authentication for analysis-only operations

---

## API Endpoints

### 1. Analyze Meal (No Save)
**Endpoint:** `POST /api/mcp/nutrition/analyze`

**Description:** Analyze a meal description using CalorieNinjas API without saving to database.

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

---

### 2. Analyze and Save Meal
**Endpoint:** `POST /api/mcp/nutrition/analyze-and-save`

**Description:** Analyze a meal and save it to the user's nutrition log.

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

---

### 3. Batch Analyze Meals
**Endpoint:** `POST /api/mcp/nutrition/batch-analyze`

**Description:** Analyze multiple meal descriptions in a single request (max 10 meals).

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

---

### 4. Health Recommendations
**Endpoint:** `POST /api/mcp/nutrition/health-recommendations`

**Description:** Get personalized health recommendations based on nutritional data.

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

### Python Example
```python
import requests

# Analyze a meal
response = requests.post('http://localhost:5001/api/mcp/nutrition/analyze', 
                        json={'meal_description': 'grilled chicken with rice'})
data = response.json()

if data['success']:
    print(f"Calories: {data['analysis']['calories']}")
    print(f"Protein: {data['analysis']['protein']}g")
    for rec in data['analysis']['health_recommendations']:
        print(f"Recommendation: {rec}")
```

### JavaScript Example
```javascript
// Analyze a meal
const response = await fetch('http://localhost:5001/api/mcp/nutrition/analyze', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        meal_description: 'grilled chicken with rice'
    })
});

const data = await response.json();
if (data.success) {
    console.log(`Calories: ${data.analysis.calories}`);
    console.log(`Protein: ${data.analysis.protein}g`);
}
```

---

## Integration Notes

1. **Rate Limiting:** CalorieNinjas API has rate limits. Batch requests are limited to 10 meals per request.

2. **Data Types:** All nutritional values are returned as integers (rounded from decimals).

3. **Error Handling:** Always check the `success` field in responses and handle errors gracefully.

4. **Authentication:** For endpoints that save data, ensure user session is established.

5. **Meal Descriptions:** Be specific with meal descriptions for better accuracy:
   - Include portion sizes: "1 cup brown rice"
   - Mention cooking methods: "grilled chicken breast"
   - List all ingredients: "chicken, rice, broccoli, olive oil"

---

## Health Recommendation Logic

The system provides recommendations based on:

- **Calorie Ranges:** 1200-2500 calories optimal
- **Protein:** 15-25% of total calories
- **Carbs:** 30-70% of total calories  
- **Fats:** 20-35% of total calories
- **Fiber:** Minimum 5g per meal
- **Sodium:** Under 1000mg per meal
- **Sugar:** Under 25g per meal

Recommendations are personalized based on these nutritional guidelines and best practices.
