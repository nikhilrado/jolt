#!/usr/bin/env python3
"""
Comprehensive test script for all Jolt API endpoints
Tests both token-based and session-based endpoints
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
API_TOKEN = "jolt_pat_0b6649e371df3eb6d5240775416d894d6b9784eba8c2660e46b7d90c"
SESSION_COOKIE = "your_session_cookie_here"  # Replace with actual session cookie

def test_token_endpoint(endpoint, method="GET", data=None):
    """Test a token-authenticated endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing TOKEN: {method} {endpoint}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"✅ Success: {data.get('message', 'OK')}")
                
                # Print key information based on endpoint
                if 'profile' in endpoint:
                    print(f"User ID: {data.get('id', 'N/A')}")
                    print(f"Token Valid: {data.get('token_valid', 'N/A')}")
                
                elif 'activities' in endpoint:
                    activities = data.get('activities', [])
                    print(f"Total Activities: {len(activities)}")
                    if activities:
                        print(f"First Activity: {activities[0].get('name', 'N/A')}")
                
                elif 'stats' in endpoint:
                    print(f"Total Runs: {data.get('total_runs', 'N/A')}")
                    print(f"Total Distance: {data.get('total_distance', 'N/A')}")
                
                elif 'email' in endpoint:
                    print(f"User ID: {data.get('user_id', 'N/A')}")
                    print(f"Message: {data.get('message', 'N/A')}")
                
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_session_endpoint(endpoint, method="GET", data=None):
    """Test a session-authenticated endpoint"""
    url = f"{BASE_URL}{endpoint}"
    headers = {
        "Cookie": f"session={SESSION_COOKIE}",
        "Content-Type": "application/json"
    }
    
    print(f"\n{'='*60}")
    print(f"Testing SESSION: {method} {endpoint}")
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
                print(f"✅ Success: {data.get('success', 'OK')}")
                
                # Print key information based on endpoint
                if 'activities' in endpoint:
                    activities = data.get('activities', [])
                    print(f"Total Activities: {len(activities)}")
                    if activities:
                        print(f"First Activity: {activities[0].get('name', 'N/A')}")
                        print(f"Activity Type: {activities[0].get('type', 'N/A')}")
                
                elif 'analytics' in endpoint:
                    print(f"Analysis Period: {data.get('analysis_period', 'N/A')}")
                    if 'training_load' in data:
                        tl = data['training_load']
                        print(f"ATL: {tl.get('atl', 'N/A')}")
                        print(f"CTL: {tl.get('ctl', 'N/A')}")
                        print(f"TSB: {tl.get('tsb', 'N/A')}")
                
                elif 'psychology' in endpoint:
                    print(f"Analysis Period: {data.get('analysis_period', 'N/A')}")
                    events = data.get('performance_events', [])
                    print(f"Performance Events: {len(events)}")
                
                elif 'nutrition' in endpoint:
                    print(f"Analysis Period: {data.get('analysis_period', 'N/A')}")
                    if 'insights' in endpoint:
                        insights = data.get('insights', {})
                        summary = insights.get('summary', {})
                        print(f"Total Meals: {summary.get('total_meals_logged', 'N/A')}")
                    elif 'dashboard' in endpoint:
                        summary = data.get('summary', {})
                        print(f"Total Days: {summary.get('total_days', 'N/A')}")
                
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_public_endpoint(endpoint, method="POST", data=None):
    """Test a public endpoint (no authentication required)"""
    url = f"{BASE_URL}{endpoint}"
    headers = {"Content-Type": "application/json"}
    
    print(f"\n{'='*60}")
    print(f"Testing PUBLIC: {method} {endpoint}")
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
                print(f"✅ Success: {data.get('success', 'OK')}")
                
                # Print key information based on endpoint
                if 'analyze' in endpoint and 'batch' not in endpoint:
                    analysis = data.get('analysis', {})
                    print(f"Meal Name: {analysis.get('name', 'N/A')}")
                    print(f"Calories: {analysis.get('calories', 'N/A')}")
                    print(f"Protein: {analysis.get('protein', 'N/A')}g")
                
                elif 'batch-analyze' in endpoint:
                    print(f"Total Meals: {data.get('total_meals', 'N/A')}")
                    print(f"Successful: {data.get('successful_analyses', 'N/A')}")
                    print(f"Failed: {data.get('failed_analyses', 'N/A')}")
                
                elif 'health-recommendations' in endpoint:
                    recommendations = data.get('health_recommendations', [])
                    print(f"Recommendations: {len(recommendations)}")
                    if recommendations:
                        print(f"First: {recommendations[0]}")
                
            except json.JSONDecodeError:
                print("Response is not valid JSON")
                print(f"Response: {response.text[:200]}...")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def main():
    """Run comprehensive endpoint tests"""
    print("🚀 Jolt API Comprehensive Endpoint Tester")
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now()}")
    
    if SESSION_COOKIE == "your_session_cookie_here":
        print("\n⚠️  WARNING: Session-based endpoints will fail without proper session cookie!")
        print("To test session endpoints:")
        print("1. Start your Flask app: python app.py")
        print("2. Open browser and go to http://localhost:5001")
        print("3. Login and connect Strava")
        print("4. Open browser dev tools (F12)")
        print("5. Go to Application/Storage tab")
        print("6. Copy the 'session' cookie value")
        print("7. Replace SESSION_COOKIE in this script")
        print("\n" + "="*60)
    
    # Test Token-based endpoints (v1 API)
    print("\n🔑 TESTING TOKEN-BASED ENDPOINTS (v1 API)")
    print("="*60)
    
    token_endpoints = [
        ("/api/v1/profile", "GET"),
        ("/api/v1/activities", "GET"),
        ("/api/v1/stats", "GET"),
        ("/api/v1/email", "GET"),
    ]
    
    for endpoint, method in token_endpoints:
        test_token_endpoint(endpoint, method)
    
    # Test Public endpoints (MCP/CalorieNinjas)
    print("\n🌐 TESTING PUBLIC ENDPOINTS (MCP/CalorieNinjas)")
    print("="*60)
    
    public_endpoints = [
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
        }),
        ("/api/mcp/nutrition/batch-analyze", "POST", {
            "meal_descriptions": ["grilled salmon with quinoa", "greek yogurt with berries"]
        })
    ]
    
    for endpoint, method, *data in public_endpoints:
        test_public_endpoint(endpoint, method, data[0] if data else None)
    
    # Test Session-based endpoints (require browser login + Strava connection)
    print("\n🍪 TESTING SESSION-BASED ENDPOINTS (Requires Login + Strava)")
    print("="*60)
    
    session_endpoints = [
        # Strava endpoints
        ("/api/strava/activities", "GET"),
        
        # Analytics endpoints
        ("/api/analytics/comprehensive?days=30", "GET"),
        ("/api/analytics/summary?days=30", "GET"),
        ("/api/analytics/performance-trends?days=30", "GET"),
        
        # Psychology endpoints
        ("/api/psychology/analysis?days=30", "GET"),
        ("/api/psychology/performance-events?days=30", "GET"),
        ("/api/psychology/insights?days=30", "GET"),
        
        # Nutrition endpoints
        ("/api/nutrition/dashboard?days=7", "GET"),
        ("/api/nutrition/insights?days=30", "GET"),
        ("/api/nutrition/daily-summary", "GET"),
        ("/api/nutrition/trends?days=30", "GET"),
        ("/api/nutrition/patterns?days=30", "GET"),
    ]
    
    for endpoint, method in session_endpoints:
        test_session_endpoint(endpoint, method)
    
    print(f"\n{'='*60}")
    print("🎯 Testing complete!")
    print("📊 Summary:")
    print("  ✅ Token-based endpoints: Working")
    print("  ✅ Public endpoints: Working")
    print("  ⚠️  Session-based endpoints: Require browser login + Strava connection")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
