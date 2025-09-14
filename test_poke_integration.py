#!/usr/bin/env python3
"""
Test script to simulate a Strava webhook event and trigger Poke message
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client

def simulate_strava_activity():
    """Simulate a Strava activity webhook event"""
    print("🧪 SIMULATING STRAVA WEBHOOK EVENT")
    print("=" * 50)
    
    # Load environment
    load_dotenv()
    
    # Set up Supabase
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_service_key = os.getenv('SUPABASE_SERVICE_KEY')
    supabase = create_client(supabase_url, supabase_service_key)
    
    # Get user with both Strava and Poke credentials
    print("1️⃣ Finding user with Strava and Poke credentials...")
    
    # Find user with Strava credentials
    strava_creds = supabase.table('strava_credentials').select('*').eq('is_active', True).execute()
    if not strava_creds.data:
        print("❌ No Strava credentials found!")
        return
    
    user_id = strava_creds.data[0]['user_id']
    athlete_id = strava_creds.data[0]['athlete_id']
    print(f"   ✅ Found Strava user: {user_id} (athlete: {athlete_id})")
    
    # Check if user has Poke credentials
    poke_creds = supabase.table('poke_credentials').select('*').eq('user_id', user_id).eq('is_active', True).execute()
    if not poke_creds.data:
        print(f"❌ User {user_id} doesn't have Poke credentials!")
        return
    
    print(f"   ✅ User has Poke API key")
    
    # 2. Create fake webhook event
    print("\n2️⃣ Creating simulated webhook event...")
    fake_webhook_event = {
        'object_type': 'activity',
        'aspect_type': 'create',
        'object_id': 9999999999,  # Fake activity ID
        'owner_id': athlete_id,
        'subscription_id': 303815,
        'event_time': 1726320000
    }
    
    # 3. Import and test webhook manager
    print("\n3️⃣ Testing webhook manager...")
    try:
        from strava_webhook_manager import StravaWebhookManager
        from strava_token_manager import StravaTokenManager
        
        # Create managers
        supabase_client = create_client(supabase_url, os.getenv('SUPABASE_KEY'))
        token_manager = StravaTokenManager(supabase_client, supabase)
        webhook_manager = StravaWebhookManager(supabase_client, supabase, token_manager)
        
        print("   ✅ Webhook manager created")
        
        # 4. Log the webhook event
        print("\n4️⃣ Logging webhook event...")
        webhook_manager._log_webhook_event(fake_webhook_event)
        print("   ✅ Webhook event logged to activity_notifications")
        
        # 5. Test activity processing (with fake data since we can't fetch real activity)
        print("\n5️⃣ Testing activity processing...")
        fake_activity_data = {
            'id': 9999999999,
            'name': 'Test Morning Run',
            'type': 'Run',
            'distance': 5200,  # 5.2km in meters
            'moving_time': 1800,  # 30 minutes
            'start_date': '2025-09-14T06:00:00Z',
            'achievement_count': 2,
            'kudos_count': 5
        }
        
        # Test run_complete (which includes Poke message sending)
        result = webhook_manager.run_complete(user_id, fake_activity_data)
        print(f"   📊 Run complete result: {result}")
        
        if 'poke_message' in result:
            print("   ✅ Poke message was sent!")
            print(f"   📱 Message result: {result['poke_message']}")
        else:
            print("   ❌ No Poke message in result")
        
        print("\n6️⃣ Checking database for Poke message...")
        poke_messages = supabase.table('poke_messages').select('*').eq('user_id', user_id).order('sent_at', desc=True).limit(1).execute()
        if poke_messages.data:
            msg = poke_messages.data[0]
            print(f"   ✅ Found Poke message: {msg['message_text']}")
            print(f"   📊 Success: {msg['poke_response'].get('success', False)}")
        else:
            print("   ❌ No Poke message found in database")
            
    except Exception as e:
        print(f"   ❌ Error testing webhook manager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate_strava_activity()
