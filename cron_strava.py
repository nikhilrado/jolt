#!/usr/bin/env python3
"""
Cron job script for checking Strava activities
This script can be run by external cron services or GitHub Actions
"""

import os
import requests
import sys
from datetime import datetime

# Configuration
API_BASE_URL = os.getenv('JOLT_API_URL', 'http://localhost:5000')
API_TOKEN = os.getenv('JOLT_API_TOKEN')

def check_activities():
    """Check for new Strava activities"""
    if not API_TOKEN:
        print("ERROR: JOLT_API_TOKEN environment variable not set")
        return False
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"[{datetime.now().isoformat()}] Checking for new Strava activities...")
        
        response = requests.post(
            f"{API_BASE_URL}/cron/check-activities",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Found {data.get('new_activities_found', 0)} new activities")
            
            for notification in data.get('notifications', []):
                print(f"  📱 {notification['activity_type']}: {notification['activity_name']} (User: {notification['user_id']})")
            
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def send_notifications():
    """Send pending notifications"""
    if not API_TOKEN:
        print("ERROR: JOLT_API_TOKEN environment variable not set")
        return False
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"[{datetime.now().isoformat()}] Sending pending notifications...")
        
        response = requests.post(
            f"{API_BASE_URL}/cron/send-notifications",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success: Sent {data.get('sent_count', 0)} notifications")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def get_status():
    """Get Strava connection status"""
    if not API_TOKEN:
        print("ERROR: JOLT_API_TOKEN environment variable not set")
        return False
    
    headers = {
        'Authorization': f'Bearer {API_TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/strava/status",
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"📊 Status: {data.get('total_connected_users', 0)} users connected to Strava")
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except requests.RequestException as e:
        print(f"❌ Request failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python3 cron_strava.py [check|notify|status]")
        print("  check  - Check for new activities")
        print("  notify - Send pending notifications")
        print("  status - Get connection status")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "check":
        success = check_activities()
    elif command == "notify":
        success = send_notifications()
    elif command == "status":
        success = get_status()
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
