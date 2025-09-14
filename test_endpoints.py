#!/usr/bin/env python3
"""
Test script for Jolt API endpoints
Run this after starting your Flask app and authenticating in the browser
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
SESSION_COOKIE = "your_session_cookie_here"  # Replace with actual session cookie

def test_endpoint(endpoint, method="GET", data=None):
    """Test a single endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Cookie": f"session={SESSION_COOKIE}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"Success: {data.get('success', 'N/A')}")
                
                # Print key information based on endpoint
                if 'activities' in endpoint:
                    activities = data.get('activities', [])
                    print(f"Total Activities: {len(activities)}")
                    if activities:
                        print(f"First Activity: {activities[0].get('name', 'N/A')}")
                        print(f"Activity Type: {activities[0].get('type', 'N/A')}")
                        print(f"Distance: {activities[0].get('distance', 'N/A')} meters")
                
                elif 'analytics' in endpoint:
                    analytics = data
                    print(f"Analysis Period: {analytics.get('analysis_period', 'N/A')}")
                    training_load = analytics.get('training_load', {})
                    if training_load:
                        print(f"ATL: {training_load.get('atl', 'N/A')}")
                        print(f"CTL: {training_load.get('ctl', 'N/A')}")
                        print(f"TSB: {training_load.get('tsb', 'N/A')}")
                
                elif 'psychology' in endpoint:
                    psychology = data
                    print(f"Analysis Period: {psychology.get('analysis_period', 'N/A')}")
                    events = psychology.get('performance_events', [])
                    print(f"Performance Events: {len(events)}")
                
                elif 'nutrition' in endpoint:
                    nutrition = data
                    print(f"Analysis Period: {nutrition.get('analysis_period', 'N/A')}")
                    if 'insights' in endpoint:
                        insights = nutrition.get('insights', {})
                        summary = insights.get('summary', {})
                        print(f"Total Meals: {summary.get('total_meals_logged', 'N/A')}")
                        print(f"Avg Daily Calories: {summary.get('avg_daily_calories', 'N/A')}")
                    elif 'dashboard' in endpoint:
                        summary = nutrition.get('summary', {})
                        print(f"Total Days: {summary.get('total_days', 'N/A')}")
                        print(f"Total Meals: {summary.get('total_meals', 'N/A')}")
                
                elif 'mcp' in endpoint:
                    mcp_data = data
                    print(f"Success: {mcp_data.get('success', 'N/A')}")
                    if 'analysis' in mcp_data:
                        analysis = mcp_data['analysis']
                        print(f"Meal Name: {analysis.get('name', 'N/A')}")
                        print(f"Calories: {analysis.get('calories', 'N/A')}")
                        print(f"Protein: {analysis.get('protein', 'N/A')}g")
                        print(f"Health Recommendations: {len(analysis.get('health_recommendations', []))}")
                
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")

def main():
    """Run all endpoint tests"""
    print("Jolt API Endpoint Tester")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    
    if SESSION_COOKIE == "your_session_cookie_here":
        print("\n⚠️  WARNING: Please update SESSION_COOKIE with your actual session cookie!")
        print("1. Start your Flask app: python app.py")
        print("2. Open browser and go to http://localhost:5001")
        print("3. Login and connect Strava")
        print("4. Open browser dev tools (F12)")
        print("5. Go to Application/Storage tab")
        print("6. Copy the 'session' cookie value")
        print("7. Replace SESSION_COOKIE in this script")
        return
    
    # Test all endpoints
    endpoints = [
        # Strava endpoints
        ("/api/strava/activities", "GET"),
        
        # Analytics endpoints
        ("/api/analytics/comprehensive?days=30", "GET"),
        
        # Psychology endpoints
        ("/api/psychology/analysis?days=30", "GET"),
        
        # Nutrition endpoints
        ("/api/nutrition/dashboard?days=7", "GET"),
        ("/api/nutrition/insights?days=30", "GET"),
        
        # CalorieNinjas endpoints (no auth required)
        ("/api/mcp/nutrition/analyze", "POST", {
            "meal_description": "grilled chicken breast with brown rice and steamed broccoli"
        }),
        ("/api/mcp/nutrition/health-recommendations", "POST", {
            "calories": 420,
            "carbs": 45,
            "fats": 12,
            "protein": 35,
            "sodium": 450,
            "fiber": 8,
            "sugar": 2
        })
    ]
    
    for endpoint, method, *data in endpoints:
        test_endpoint(endpoint, method, data[0] if data else None)
    
    print(f"\n{'='*60}")
    print("Testing complete!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
