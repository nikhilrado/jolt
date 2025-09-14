#!/usr/bin/env python3
"""
Check for recent webhook events in the database
"""

import os
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timedelta

def check_recent_webhooks():
    print("🔍 CHECKING RECENT WEBHOOK ACTIVITY")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Set up Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase = create_client(supabase_url, supabase_service_key)
    
    # Check for webhook events in the last 24 hours
    print("📡 RECENT WEBHOOK EVENTS (last 24 hours):")
    try:
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        webhooks = supabase.table('activity_notifications').select('*').ilike(
            'activity_type', 'WEBHOOK_%'
        ).gte('created_at', yesterday.isoformat()).order(
            'created_at', desc=True
        ).execute()
        
        if webhooks.data:
            print(f"   ✅ Found {len(webhooks.data)} webhook event(s)")
            for webhook in webhooks.data:
                event_data = webhook.get('activity_data', {}).get('webhook_event', {})
                print(f"   📅 {webhook['created_at']}")
                print(f"      🏃 {webhook['activity_type']}")
                print(f"      📊 Object: {event_data.get('object_id', 'N/A')}, Athlete: {event_data.get('owner_id', 'N/A')}")
                print(f"      👤 User: {webhook.get('user_id', 'Not found')}")
                print()
        else:
            print("   ❌ No webhook events found in the last 24 hours!")
            print("   💡 This means Strava is not sending webhook events")
            
    except Exception as e:
        print(f"   ❌ Error checking webhooks: {e}")
    
    # Check for any activity notifications (including non-webhook)
    print("🏃 ALL RECENT ACTIVITY NOTIFICATIONS (last 24 hours):")
    try:
        activities = supabase.table('activity_notifications').select('*').gte(
            'created_at', yesterday.isoformat()
        ).order('created_at', desc=True).limit(10).execute()
        
        if activities.data:
            print(f"   ✅ Found {len(activities.data)} activity notification(s)")
            for activity in activities.data:
                print(f"   📅 {activity['created_at']}")
                print(f"      🏃 {activity['activity_type']}")
                print(f"      📝 {activity['activity_name']}")
                print(f"      👤 User: {activity.get('user_id', 'N/A')}")
                print()
        else:
            print("   ⚠️ No activity notifications found")
    except Exception as e:
        print(f"   ❌ Error checking activities: {e}")
    
    # Check recent Poke messages
    print("📱 RECENT POKE MESSAGES (last 24 hours):")
    try:
        poke_messages = supabase.table('poke_messages').select('*').gte(
            'sent_at', yesterday.isoformat()
        ).order('sent_at', desc=True).limit(5).execute()
        
        if poke_messages.data:
            print(f"   ✅ Found {len(poke_messages.data)} Poke message(s)")
            for msg in poke_messages.data:
                success = msg['poke_response'].get('success', False)
                print(f"   📅 {msg['sent_at']}")
                print(f"      📱 {msg['message_text']}")
                print(f"      ✅ Success: {success}")
                if success:
                    phone = msg['poke_response'].get('response', {}).get('phoneNumber', 'N/A')
                    print(f"      📞 Phone: {phone}")
                print()
        else:
            print("   ⚠️ No Poke messages found")
    except Exception as e:
        print(f"   ❌ Error checking Poke messages: {e}")
    
    print("=" * 50)
    print("🔧 TROUBLESHOOTING TIPS:")
    print("1. If no webhook events: Strava isn't sending them")
    print("2. If webhook events but no processing: Check production app logs")
    print("3. If processing but no Poke: Check Poke API key and credentials")
    print("4. Check Render.com logs for real-time debugging")

if __name__ == "__main__":
    check_recent_webhooks()
