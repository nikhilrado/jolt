#!/usr/bin/env python3
"""
Test script for the new psychology endpoints that accept user feelings
"""

import requests
import json
from datetime import datetime

# Configuration
BASE_URL = "http://localhost:5001"
SESSION_COOKIE = "your_session_cookie_here"  # Replace with actual session cookie

def test_submit_wellness_data():
    """Test submitting wellness/feeling data"""
    url = f"{BASE_URL}/api/psychology/submit-wellness"
    headers = {
        "Cookie": f"session={SESSION_COOKIE}",
        "Content-Type": "application/json"
    }
    
    # Sample wellness data
    wellness_data = {
        "mood": 7,           # 1-10 scale (1=very low, 10=excellent)
        "stress": 4,          # 1-10 scale (1=no stress, 10=extremely stressed)
        "motivation": 8,      # 1-10 scale (1=no motivation, 10=highly motivated)
        "sleep_quality": 6,   # 1-10 scale (1=poor sleep, 10=excellent sleep)
        "soreness": 3,        # 1-10 scale (1=no soreness, 10=very sore)
        "perceived_effort": 5 # 1-10 scale (1=very easy, 10=maximum effort)
    }
    
    print(f"\n{'='*60}")
    print("Testing: POST /api/psychology/submit-wellness")
    print(f"{'='*60}")
    print(f"Submitting wellness data: {json.dumps(wellness_data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=wellness_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: {data.get('message', 'OK')}")
            print(f"Submitted data: {json.dumps(data.get('data', {}), indent=2)}")
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_analyze_feelings():
    """Test analyzing feelings and getting psychological insights"""
    url = f"{BASE_URL}/api/psychology/analyze-feelings"
    headers = {
        "Cookie": f"session={SESSION_COOKIE}",
        "Content-Type": "application/json"
    }
    
    # Sample wellness data for analysis
    wellness_data = {
        "mood": 3,           # Low mood - should trigger mood support insights
        "stress": 8,          # High stress - should trigger stress management insights
        "motivation": 2,      # Low motivation - should trigger motivation boost insights
        "sleep_quality": 4,   # Poor sleep
        "soreness": 6,        # Some soreness
        "perceived_effort": 7 # High perceived effort
    }
    
    print(f"\n{'='*60}")
    print("Testing: POST /api/psychology/analyze-feelings")
    print(f"{'='*60}")
    print(f"Analyzing feelings: {json.dumps(wellness_data, indent=2)}")
    
    try:
        response = requests.post(url, headers=headers, json=wellness_data)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Analysis completed")
            
            # Display personalized insights
            insights = data.get('personalized_insights', [])
            print(f"\n🎯 Personalized Insights ({len(insights)} found):")
            for i, insight in enumerate(insights, 1):
                print(f"\n{i}. {insight.get('title', 'N/A')}")
                print(f"   Type: {insight.get('type', 'N/A')}")
                print(f"   Message: {insight.get('message', 'N/A')}")
                print(f"   Recommendations:")
                for rec in insight.get('recommendations', []):
                    print(f"     • {rec}")
            
            # Display performance analysis summary
            perf_analysis = data.get('performance_analysis', {})
            print(f"\n📊 Performance Analysis:")
            print(f"   Analysis Period: {perf_analysis.get('analysis_period', 'N/A')}")
            print(f"   Total Activities: {perf_analysis.get('total_activities', 'N/A')}")
            print(f"   Performance Events: {perf_analysis.get('performance_events', 'N/A')}")
            
            # Display psychological insights
            psych_insights = perf_analysis.get('psychological_insights', [])
            if psych_insights:
                print(f"\n🧠 Psychological Insights ({len(psych_insights)} found):")
                for i, insight in enumerate(psych_insights, 1):
                    print(f"\n{i}. {insight.get('title', 'N/A')}")
                    print(f"   Description: {insight.get('description', 'N/A')}")
                    print(f"   Confidence: {insight.get('confidence', 'N/A')}")
            
            # Display wellness trends
            trends = data.get('wellness_trends', [])
            if trends:
                print(f"\n📈 Wellness Trends ({len(trends)} found):")
                for trend in trends:
                    print(f"   {trend.get('metric', 'N/A')}: {trend.get('trend_direction', 'N/A')} (strength: {trend.get('trend_strength', 'N/A')})")
            
        else:
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

def test_different_mood_scenarios():
    """Test different mood scenarios to see different insights"""
    scenarios = [
        {
            "name": "Great Day",
            "data": {"mood": 9, "stress": 2, "motivation": 9, "sleep_quality": 8, "soreness": 2, "perceived_effort": 6}
        },
        {
            "name": "Struggling Day", 
            "data": {"mood": 2, "stress": 9, "motivation": 1, "sleep_quality": 3, "soreness": 8, "perceived_effort": 9}
        },
        {
            "name": "Average Day",
            "data": {"mood": 5, "stress": 5, "motivation": 5, "sleep_quality": 5, "soreness": 5, "perceived_effort": 5}
        }
    ]
    
    print(f"\n{'='*60}")
    print("Testing Different Mood Scenarios")
    print(f"{'='*60}")
    
    for scenario in scenarios:
        print(f"\n🎭 Scenario: {scenario['name']}")
        print(f"Data: {json.dumps(scenario['data'], indent=2)}")
        
        # This would normally make the API call, but for demo purposes we'll just show the data
        print("(Would make API call to /api/psychology/analyze-feelings)")

def main():
    """Run all psychology endpoint tests"""
    print("🧠 Psychology Endpoints Tester")
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
    
    # Test the endpoints
    test_submit_wellness_data()
    test_analyze_feelings()
    test_different_mood_scenarios()
    
    print(f"\n{'='*60}")
    print("🎯 Testing complete!")
    print("📋 New Psychology Endpoints:")
    print("  ✅ POST /api/psychology/submit-wellness - Submit feeling data")
    print("  ✅ POST /api/psychology/analyze-feelings - Get personalized insights")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()
