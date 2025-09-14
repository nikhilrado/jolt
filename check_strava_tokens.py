#!/usr/bin/env python3
"""
Check Strava token status and validity
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime
import requests

def check_strava_tokens():
    print("🔍 CHECKING STRAVA TOKEN STATUS")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Set up Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase = create_client(supabase_url, supabase_service_key)
    
    print("🔐 STRAVA CREDENTIALS STATUS:")
    try:
        creds = supabase.table('strava_credentials').select('*').eq('is_active', True).execute()
        
        for cred in creds.data:
            user_id = cred['user_id']
            athlete_id = cred['athlete_id']
            access_token = cred.get('access_token', '')
            refresh_token = cred.get('refresh_token', '')
            expires_at = cred.get('expires_at')
            
            print(f"\n👤 User: {user_id}")
            print(f"🏃 Athlete ID: {athlete_id}")
            print(f"🔑 Access Token: {'✅ Present' if access_token else '❌ Missing'}")
            print(f"🔄 Refresh Token: {'✅ Present' if refresh_token else '❌ Missing'}")
            
            if expires_at:
                try:
                    # Parse expires_at timestamp
                    if isinstance(expires_at, str):
                        expires_dt = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
                    else:
                        expires_dt = datetime.fromtimestamp(expires_at)
                    
                    now = datetime.utcnow().replace(tzinfo=expires_dt.tzinfo)
                    time_until_expiry = expires_dt - now
                    
                    if time_until_expiry.total_seconds() > 0:
                        hours_left = time_until_expiry.total_seconds() / 3600
                        print(f"⏰ Token Expires: {expires_dt} ({hours_left:.1f} hours from now)")
                        print(f"🟢 Status: Valid")
                    else:
                        hours_ago = -time_until_expiry.total_seconds() / 3600
                        print(f"⏰ Token Expired: {expires_dt} ({hours_ago:.1f} hours ago)")
                        print(f"🔴 Status: EXPIRED")
                        
                except Exception as e:
                    print(f"❌ Error parsing expiry time: {e}")
                    print(f"Raw expires_at: {expires_at}")
            else:
                print(f"⏰ Expires At: Not set")
            
            # Test the access token
            if access_token:
                print(f"🧪 Testing access token...")
                try:
                    headers = {'Authorization': f'Bearer {access_token}'}
                    response = requests.get(
                        'https://www.strava.com/api/v3/athlete',
                        headers=headers,
                        timeout=5
                    )
                    
                    if response.status_code == 200:
                        athlete_data = response.json()
                        print(f"✅ Token is valid! Athlete: {athlete_data.get('firstname', '')} {athlete_data.get('lastname', '')}")
                    elif response.status_code == 401:
                        print(f"❌ Token is invalid/expired (401 Unauthorized)")
                        print(f"Response: {response.text}")
                    else:
                        print(f"⚠️ Unexpected response: {response.status_code}")
                        print(f"Response: {response.text}")
                        
                except Exception as e:
                    print(f"❌ Error testing token: {e}")
            
    except Exception as e:
        print(f"❌ Error checking credentials: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 NEXT STEPS:")
    print("1. If token expired: User needs to reconnect Strava at /strava/auth")
    print("2. If token valid but webhooks fail: Check production environment variables")
    print("3. If no credentials: User needs to connect Strava account")

if __name__ == "__main__":
    check_strava_tokens()
