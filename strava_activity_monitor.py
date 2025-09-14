"""
Strava Activity Monitoring Service
Handles checking for new activities and sending notifications
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import os
from strava_token_manager import StravaTokenManager

class StravaActivityMonitor:
    def __init__(self, supabase_client, supabase_admin_client=None):
        self.supabase = supabase_client
        self.supabase_admin = supabase_admin_client or supabase_client
        self.token_manager = StravaTokenManager(supabase_client, supabase_admin_client)
    
    def check_new_activities_for_user(self, user_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check for new activities for a specific user"""
        user_id = user_data['user_id']
        last_activity_id = user_data.get('last_activity_id')
        
        # Get valid access token
        access_token = self.token_manager.get_valid_access_token(user_id)
        if not access_token:
            print(f"No valid access token for user {user_id}")
            return []
        
        try:
            # Fetch recent activities from Strava
            headers = {'Authorization': f'Bearer {access_token}'}
            activities_url = 'https://www.strava.com/api/v3/athlete/activities'
            
            # Get activities from the last 24 hours to ensure we don't miss any
            since = int((datetime.utcnow() - timedelta(hours=24)).timestamp())
            params = {
                'after': since,
                'per_page': 30  # Should be enough for most users
            }
            
            response = requests.get(activities_url, headers=headers, params=params)
            
            if response.status_code != 200:
                print(f"Failed to fetch activities for user {user_id}: {response.status_code}")
                return []
            
            activities = response.json()
            
            # Filter for new activities
            new_activities = []
            latest_activity_id = last_activity_id
            
            for activity in activities:
                activity_id = activity['id']
                
                # If we have a last_activity_id, only include activities newer than that
                if last_activity_id is None or activity_id > last_activity_id:
                    new_activities.append(activity)
                    
                    # Track the latest activity ID
                    if latest_activity_id is None or activity_id > latest_activity_id:
                        latest_activity_id = activity_id
            
            # Update the last activity check
            if latest_activity_id != last_activity_id:
                self.token_manager.update_last_activity_check(user_id, latest_activity_id)
            else:
                self.token_manager.update_last_activity_check(user_id)
            
            return new_activities
            
        except Exception as e:
            print(f"Error checking activities for user {user_id}: {e}")
            return []
    
    def store_activity_notification(self, user_id: str, activity: Dict[str, Any]) -> bool:
        """Store a new activity notification in the database"""
        try:
            notification_data = {
                'user_id': user_id,
                'strava_activity_id': activity['id'],
                'activity_type': activity.get('type', 'Unknown'),
                'activity_name': activity.get('name', 'Untitled Activity'),
                'activity_data': activity,
                'notification_sent': False
            }
            
            result = self.supabase_admin.table('activity_notifications').insert(
                notification_data
            ).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error storing activity notification: {e}")
            return False
    
    def process_new_activity(self, user_id: str, activity: Dict[str, Any]) -> Dict[str, Any]:
        """Process a new activity and determine what action to take"""
        activity_type = activity.get('type', '').lower()
        activity_name = activity.get('name', 'Untitled Activity')
        distance = activity.get('distance', 0) / 1000  # Convert to km
        duration = activity.get('moving_time', 0) / 60  # Convert to minutes
        
        # Store the notification
        self.store_activity_notification(user_id, activity)
        
        # Determine the message/action based on activity type
        message = self.generate_activity_message(activity_type, activity_name, distance, duration, activity)
        
        return {
            'user_id': user_id,
            'activity_id': activity['id'],
            'activity_type': activity_type,
            'activity_name': activity_name,
            'message': message,
            'should_notify': True,  # You can add logic here to determine when to notify
            'activity_data': activity
        }
    
    def generate_activity_message(self, activity_type: str, activity_name: str, distance_km: float, duration_min: float, activity: Dict[str, Any]) -> str:
        """Generate a motivational or congratulatory message for the activity"""
        
        if 'run' in activity_type:
            if distance_km >= 21:  # Half marathon or more
                return f"🏃‍♂️ Incredible! You just completed a {distance_km:.1f}km run ({activity_name})! That's marathon-level dedication! 💪"
            elif distance_km >= 10:
                return f"🏃‍♂️ Great job on your {distance_km:.1f}km run ({activity_name})! You're crushing those distance goals! 🎯"
            elif distance_km >= 5:
                return f"🏃‍♂️ Nice {distance_km:.1f}km run ({activity_name})! Keep up the consistent training! ✨"
            else:
                return f"🏃‍♂️ Every step counts! Great {distance_km:.1f}km run ({activity_name})! 👟"
        
        elif 'ride' in activity_type or 'cycling' in activity_type:
            if distance_km >= 100:
                return f"🚴‍♂️ Epic century ride! {distance_km:.1f}km ({activity_name}) - you're absolutely crushing it! 🔥"
            elif distance_km >= 50:
                return f"🚴‍♂️ Fantastic {distance_km:.1f}km ride ({activity_name})! Those legs are getting stronger! 💪"
            else:
                return f"🚴‍♂️ Great ride! {distance_km:.1f}km ({activity_name}) - keep those wheels spinning! 🌟"
        
        elif 'swim' in activity_type:
            return f"🏊‍♂️ Awesome swim session ({activity_name})! Water time is the best time! 🌊"
        
        elif 'workout' in activity_type or 'strength' in activity_type:
            return f"💪 Solid workout session ({activity_name})! Building that strength one rep at a time! 🏋️‍♂️"
        
        elif 'walk' in activity_type or 'hike' in activity_type:
            return f"🚶‍♂️ Great {activity_name}! Movement is medicine - keep it up! 🌿"
        
        else:
            return f"🎯 Awesome {activity_type} session ({activity_name})! Every activity counts towards your goals! ⭐"
    
    def check_all_users(self) -> List[Dict[str, Any]]:
        """Check for new activities across all users with Strava connected"""
        all_notifications = []
        
        # Get all users with active Strava credentials
        active_users = self.token_manager.get_all_active_users()
        print(f"Checking {len(active_users)} users for new activities...")
        
        for user_data in active_users:
            try:
                new_activities = self.check_new_activities_for_user(user_data)
                
                for activity in new_activities:
                    notification = self.process_new_activity(user_data['user_id'], activity)
                    all_notifications.append(notification)
                    print(f"New activity found for user {user_data['user_id']}: {activity.get('name', 'Untitled')}")
                
            except Exception as e:
                print(f"Error processing user {user_data['user_id']}: {e}")
                continue
        
        return all_notifications
    
    def get_pending_notifications(self, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get pending notifications that haven't been sent yet"""
        try:
            query = self.supabase_admin.table('activity_notifications').select('*').eq('notification_sent', False)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            result = query.execute()
            return result.data
            
        except Exception as e:
            print(f"Error getting pending notifications: {e}")
            return []
    
    def mark_notification_sent(self, notification_id: str) -> bool:
        """Mark a notification as sent"""
        try:
            result = self.supabase_admin.table('activity_notifications').update({
                'notification_sent': True,
                'notification_sent_at': datetime.utcnow().isoformat()
            }).eq('id', notification_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error marking notification as sent: {e}")
            return False
