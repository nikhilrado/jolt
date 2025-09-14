#!/usr/bin/env python3
"""
Debug script to check why Poke messages aren't being sent
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

def main():
    print("🔍 DEBUGGING POKE MESSAGE FLOW")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # 1. Check environment variables
    print("1️⃣ CHECKING ENVIRONMENT VARIABLES:")
    strava_client_id = os.getenv('STRAVA_CLIENT_ID')
    strava_webhook_token = os.getenv('STRAVA_WEBHOOK_VERIFY_TOKEN')
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    
    print(f"   STRAVA_CLIENT_ID: {'✅' if strava_client_id else '❌'} {strava_client_id}")
    print(f"   STRAVA_WEBHOOK_VERIFY_TOKEN: {'✅' if strava_webhook_token else '❌'} {strava_webhook_token}")
    print(f"   SUPABASE_URL: {'✅' if supabase_url else '❌'}")
    print(f"   SUPABASE_SERVICE_KEY: {'✅' if supabase_service_key else '❌'}")
    
    if not all([strava_client_id, strava_webhook_token, supabase_url, supabase_service_key]):
        print("❌ Missing required environment variables!")
        return
    
    # 2. Check Supabase connection
    print("\n2️⃣ CHECKING SUPABASE CONNECTION:")
    try:
        supabase = create_client(supabase_url, supabase_service_key)
        print("   ✅ Supabase connection successful")
    except Exception as e:
        print(f"   ❌ Supabase connection failed: {e}")
        return
    
    # 3. Check for Strava credentials in database
    print("\n3️⃣ CHECKING STRAVA CREDENTIALS:")
    try:
        strava_creds = supabase.table('strava_credentials').select('*').eq('is_active', True).execute()
        if strava_creds.data:
            print(f"   ✅ Found {len(strava_creds.data)} active Strava connection(s)")
            for cred in strava_creds.data:
                print(f"      User: {cred['user_id']}, Athlete: {cred['athlete_id']}")
        else:
            print("   ❌ No active Strava credentials found!")
            print("   💡 Make sure you've connected your Strava account at /strava/auth")
    except Exception as e:
        print(f"   ❌ Error checking Strava credentials: {e}")
    
    # 4. Check for Poke credentials
    print("\n4️⃣ CHECKING POKE CREDENTIALS:")
    try:
        poke_creds = supabase.table('poke_credentials').select('*').eq('is_active', True).execute()
        if poke_creds.data:
            print(f"   ✅ Found {len(poke_creds.data)} active Poke credential(s)")
            for cred in poke_creds.data:
                print(f"      User: {cred['user_id']}, Last used: {cred.get('last_used_at', 'Never')}")
        else:
            print("   ❌ No active Poke credentials found!")
            print("   💡 Make sure you've configured your Poke API key at /poke/settings")
    except Exception as e:
        print(f"   ❌ Error checking Poke credentials: {e}")
    
    # 5. Check recent webhook events
    print("\n5️⃣ CHECKING RECENT WEBHOOK EVENTS:")
    try:
        # Look for webhook events in activity_notifications
        webhooks = supabase.table('activity_notifications').select('*').ilike('activity_type', 'WEBHOOK_%').order('created_at', desc=True).limit(10).execute()
        if webhooks.data:
            print(f"   ✅ Found {len(webhooks.data)} recent webhook event(s)")
            for webhook in webhooks.data:
                print(f"      {webhook['created_at']}: {webhook['activity_type']} - Object: {webhook['strava_activity_id']}")
        else:
            print("   ❌ No webhook events found!")
            print("   💡 This means webhooks aren't being received")
    except Exception as e:
        print(f"   ❌ Error checking webhook events: {e}")
    
    # 6. Check recent activity notifications
    print("\n6️⃣ CHECKING RECENT ACTIVITY NOTIFICATIONS:")
    try:
        activities = supabase.table('activity_notifications').select('*').not_.ilike('activity_type', 'WEBHOOK_%').order('created_at', desc=True).limit(5).execute()
        if activities.data:
            print(f"   ✅ Found {len(activities.data)} recent activity notification(s)")
            for activity in activities.data:
                print(f"      {activity['created_at']}: {activity['activity_type']} - {activity['activity_name']}")
        else:
            print("   ⚠️ No recent activity notifications found")
    except Exception as e:
        print(f"   ❌ Error checking activity notifications: {e}")
    
    # 7. Check Poke messages
    print("\n7️⃣ CHECKING POKE MESSAGES:")
    try:
        poke_messages = supabase.table('poke_messages').select('*').order('sent_at', desc=True).limit(5).execute()
        if poke_messages.data:
            print(f"   ✅ Found {len(poke_messages.data)} Poke message(s)")
            for msg in poke_messages.data:
                print(f"      {msg['sent_at']}: {msg['activity_name']} - Success: {msg['poke_response'].get('success', False)}")
        else:
            print("   ❌ No Poke messages found!")
            print("   💡 This means the Poke integration isn't being triggered")
    except Exception as e:
        print(f"   ❌ Error checking Poke messages: {e}")
    
    print("\n" + "=" * 50)
    print("🔧 NEXT STEPS:")
    print("1. If no webhook events found: Check if webhook subscription is active")
    print("2. If no Poke credentials: Set up Poke API key at /poke/settings")  
    print("3. If no Strava credentials: Connect Strava at /strava/auth")
    print("4. If webhook events but no Poke messages: Check app logs for errors")

if __name__ == "__main__":
    main()
