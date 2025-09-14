"""
Strava Webhook Handler
Handles real-time webhook events from Strava when activities are created/updated
"""

import os
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from flask import request, jsonify
import hashlib
import hmac
import logging

class StravaWebhookManager:
    def __init__(self, supabase_client, supabase_admin_client, token_manager=None):
        self.supabase = supabase_client
        self.supabase_admin = supabase_admin_client
        self.token_manager = token_manager
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.verify_token = os.getenv('STRAVA_WEBHOOK_VERIFY_TOKEN', 'JOLT_STRAVA_WEBHOOK')
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def handle_subscription_validation(self, args: Dict[str, str]) -> Dict[str, Any]:
        """
        Handle Strava webhook subscription validation
        Called when Strava validates our callback URL
        """
        hub_mode = args.get('hub.mode')
        hub_challenge = args.get('hub.challenge')
        hub_verify_token = args.get('hub.verify_token')
        
        self.logger.info(f"Webhook validation request: mode={hub_mode}, token={hub_verify_token}")
        
        if (hub_mode == 'subscribe' and 
            hub_verify_token == self.verify_token and 
            hub_challenge):
            
            self.logger.info("Webhook validation successful")
            return {"hub.challenge": hub_challenge}
        
        self.logger.error("Webhook validation failed")
        return {"error": "Validation failed"}
    
    def handle_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming webhook events from Strava
        """
        try:
            object_type = event_data.get('object_type')
            aspect_type = event_data.get('aspect_type')
            object_id = event_data.get('object_id')
            owner_id = event_data.get('owner_id')
            event_time = event_data.get('event_time')
            
            self.logger.info(f"Received webhook: {object_type}.{aspect_type} for object {object_id} by athlete {owner_id}")
            
            # 📝 LOG INCOMING WEBHOOK: Add webhook event to activity_notifications for debugging
            self._log_webhook_event(event_data)
            
            # We're mainly interested in activity events
            if object_type == 'activity':
                return self._handle_activity_event(
                    aspect_type, object_id, owner_id, event_time, event_data
                )
            elif object_type == 'athlete':
                return self._handle_athlete_event(
                    aspect_type, object_id, owner_id, event_time, event_data
                )
            else:
                self.logger.info(f"Ignoring event for object type: {object_type}")
                return {"status": "ignored", "reason": f"Unsupported object type: {object_type}"}
            
        except Exception as e:
            self.logger.error(f"Error handling webhook event: {e}")
            return {"error": str(e)}
    
    def _handle_activity_event(self, aspect_type: str, activity_id: int, athlete_id: int, 
                              event_time: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle activity-specific webhook events"""
        
        if aspect_type == 'create':
            return self._handle_activity_create(activity_id, athlete_id, event_time)
        elif aspect_type == 'update':
            return self._handle_activity_update(activity_id, athlete_id, event_time, event_data)
        elif aspect_type == 'delete':
            return self._handle_activity_delete(activity_id, athlete_id, event_time)
        else:
            return {"status": "ignored", "reason": f"Unsupported aspect type: {aspect_type}"}
    
    def _handle_activity_create(self, activity_id: int, athlete_id: int, event_time: int) -> Dict[str, Any]:
        """Handle new activity creation - this is the main event we care about!"""
        
        self.logger.info(f"🏃‍♂️ NEW ACTIVITY CREATED! ID: {activity_id}, Athlete: {athlete_id}")
        
        try:
            # Find the user in our database by athlete_id
            user_id = self._get_user_id_by_athlete_id(athlete_id)
            
            if not user_id:
                self.logger.warning(f"No user found for athlete ID: {athlete_id}")
                return {"status": "ignored", "reason": "User not found in our database"}
            
            # Get the user's access token
            if not self.token_manager:
                self.logger.error("Token manager not available")
                return {"error": "Token manager not available"}
            
            access_token = self.token_manager.get_valid_access_token(user_id)
            if not access_token:
                self.logger.warning(f"No valid access token for user {user_id}")
                return {"status": "ignored", "reason": "No valid access token"}
            
            # Fetch the activity details from Strava
            activity_data = self._fetch_activity_details(activity_id, access_token)
            
            if not activity_data:
                self.logger.error(f"Failed to fetch activity details for {activity_id}")
                return {"error": "Failed to fetch activity details"}
            
            # 🎯 MAIN PROCESSING: Call run_complete for the activity
            result = self.run_complete(user_id, activity_data)
            
            # Update the user's last activity ID
            if self.token_manager:
                self.token_manager.update_last_activity_check(
                    user_id, activity_id
                )
            
            # Log the success
            self.logger.info(f"✅ Processed new activity: {activity_data.get('name', 'Untitled')} "
                           f"({activity_data.get('type', 'Unknown')}) for user {user_id}")
            
            return {
                "status": "processed",
                "activity_name": activity_data.get('name'),
                "activity_type": activity_data.get('type'),
                "message": result.get('message', 'Activity processed'),
                "user_id": user_id,
                "run_complete_result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error processing activity creation: {e}")
            return {"error": str(e)}
    
    def _handle_activity_update(self, activity_id: int, athlete_id: int, 
                               event_time: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle activity updates (title, type, privacy changes)"""
        
        updates = event_data.get('updates', {})
        self.logger.info(f"Activity {activity_id} updated: {updates}")
        
        # For now, we'll just log updates
        # You could implement logic to handle title/type changes if needed
        return {
            "status": "acknowledged", 
            "updates": updates,
            "activity_id": activity_id
        }
    
    def _handle_activity_delete(self, activity_id: int, athlete_id: int, event_time: int) -> Dict[str, Any]:
        """Handle activity deletion"""
        
        self.logger.info(f"Activity {activity_id} deleted by athlete {athlete_id}")
        
        # You might want to clean up any stored notifications for this activity
        try:
            # Mark any notifications for this activity as obsolete
            self.supabase_admin.table('activity_notifications').update({
                'notification_sent': True,  # Mark as sent so they don't get processed
                'notification_sent_at': datetime.utcnow().isoformat()
            }).eq('strava_activity_id', activity_id).execute()
            
            return {"status": "cleaned_up", "activity_id": activity_id}
            
        except Exception as e:
            self.logger.error(f"Error cleaning up deleted activity: {e}")
            return {"error": str(e)}
    
    def _handle_athlete_event(self, aspect_type: str, athlete_id: int, 
                             owner_id: int, event_time: int, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle athlete events (mainly deauthorization)"""
        
        if aspect_type == 'update':
            updates = event_data.get('updates', {})
            
            # Check if this is a deauthorization event
            if updates.get('authorized') == 'false':
                self.logger.info(f"Athlete {athlete_id} deauthorized our app")
                
                # Invalidate the user's credentials
                user_id = self._get_user_id_by_athlete_id(athlete_id)
                if user_id and self.token_manager:
                    self.token_manager.invalidate_credentials(user_id)
                
                return {"status": "deauthorized", "athlete_id": athlete_id}
        
        return {"status": "ignored", "reason": "Non-deauth athlete event"}
    
    def run_complete(self, user_id: str, activity_data: dict) -> dict:
        """
        Handle completion of a run activity.
        This is the main function called when a new activity is detected.
        Now includes Poke integration for post-run messages.
        """
        try:
            # Extract basic activity metrics
            activity_type = activity_data.get('type', 'Run')
            activity_name = activity_data.get('name', 'Morning Run')
            distance = activity_data.get('distance', 0) / 1000  # Convert meters to km
            moving_time = activity_data.get('moving_time', 0)
            avg_speed = activity_data.get('average_speed', 0) * 3.6  # m/s to km/h
            
            # Create basic insights
            insights = {
                'activity_summary': f"Completed {distance:.2f}km {activity_type.lower()} in {moving_time//60}:{moving_time%60:02d}",
                'performance_notes': f"Average speed: {avg_speed:.2f} km/h",
                'completion_message': f"Great job on your {activity_type.lower()}! 🏃‍♂️",
                'metrics': {
                    'distance_km': round(distance, 2),
                    'duration_minutes': round(moving_time / 60, 1),
                    'avg_speed_kmh': round(avg_speed, 2)
                }
            }
            
            # Store notification in database
            notification_data = {
                'user_id': user_id,
                'strava_activity_id': activity_data.get('id'),
                'activity_type': activity_type,
                'activity_name': activity_name,
                'activity_data': {
                    'distance_meters': activity_data.get('distance', 0),
                    'moving_time_seconds': moving_time,
                    'activity_details': activity_data,
                    'insights': insights
                },
                'notification_sent': False,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Store in database
            response = self.supabase_admin.table('activity_notifications').insert(notification_data).execute()
            
            result = {
                'status': 'success',
                'message': insights['completion_message'],
                'insights': insights
            }
            
            if response.data:
                result['notification_id'] = response.data[0]['id']
                self.logger.info(f"🎯 Run complete processed for user {user_id}: {activity_name}")
            else:
                result['warning'] = 'Failed to store notification'
            
            # 🔥 NEW: Send Poke message if user has API key
            poke_result = self._send_poke_message(user_id, activity_data)
            if poke_result:
                result['poke_message'] = poke_result
            
            return result
                
        except Exception as e:
            self.logger.error(f"Error in run_complete: {e}")
            return {'status': 'error', 'message': f'Error processing run completion: {str(e)}'}
    
    def _send_poke_message(self, user_id: str, activity_data: dict) -> Optional[dict]:
        """
        Send a Poke message to the user asking about their run
        """
        try:
            # Import Poke credentials manager
            from poke_credentials_manager import PokeCredentialsManager
            
            # Get user's Poke API key
            poke_manager = PokeCredentialsManager(self.supabase, self.supabase_admin)
            poke_api_key = poke_manager.get_api_key(user_id)
            
            if not poke_api_key:
                self.logger.info(f"No Poke API key found for user {user_id}")
                return None
            
            # Import Poke service
            from poke_service import poke_service
            
            # Send message
            poke_result = poke_service.send_run_completion_message(poke_api_key, activity_data)
            
            # Update last used timestamp
            if poke_result['success']:
                poke_manager.update_last_used(user_id)
            
            # Store Poke message record
            poke_message_data = {
                'user_id': user_id,
                'strava_activity_id': activity_data.get('id'),
                'activity_type': activity_data.get('type', 'Run'),
                'activity_name': activity_data.get('name', 'Morning Run'),
                'message_text': self._generate_poke_message_text(activity_data),
                'poke_response': poke_result,
                'sent_at': datetime.utcnow().isoformat()
            }
            
            # Store in database
            self.supabase_admin.table('poke_messages').insert(poke_message_data).execute()
            
            if poke_result['success']:
                self.logger.info(f"✅ Poke message sent to user {user_id} about activity {activity_data.get('id')}")
                return {
                    'sent': True,
                    'message': 'Poke message sent successfully',
                    'poke_response': poke_result
                }
            else:
                self.logger.error(f"❌ Failed to send Poke message to user {user_id}: {poke_result.get('error')}")
                return {
                    'sent': False,
                    'error': poke_result.get('error'),
                    'poke_response': poke_result
                }
                
        except Exception as e:
            self.logger.error(f"Error sending Poke message: {e}")
            return {
                'sent': False,
                'error': f'Failed to send Poke message: {str(e)}'
            }
    
    def _generate_poke_message_text(self, activity_data: dict) -> str:
        """Generate the message text that will be sent via Poke"""
        activity_type = activity_data.get('type', 'Run')
        distance_meters = activity_data.get('distance', 0)
        distance_km = round(distance_meters / 1000, 2) if distance_meters else 0
        moving_time = activity_data.get('moving_time', 0)
        
        if moving_time:
            minutes = moving_time // 60
            seconds = moving_time % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "unknown time"
        
        if distance_km > 0:
            return f"🏃‍♂️ Great job on your {distance_km}km {activity_type.lower()} in {duration_str}! How did it feel? Any thoughts on your performance today?"
        else:
            activity_name = activity_data.get('name', 'Your run')
            return f"🏃‍♂️ Nice work on '{activity_name}'! How did your {activity_type.lower()} go today? How are you feeling?"
    
    def _get_user_id_by_athlete_id(self, athlete_id: int) -> Optional[str]:
        """Get our internal user ID from Strava athlete ID"""
        try:
            result = self.supabase_admin.table('strava_credentials').select('user_id').eq(
                'athlete_id', athlete_id
            ).eq('is_active', True).single().execute()
            
            if result.data:
                return result.data['user_id']
            return None
            
        except Exception as e:
            self.logger.error(f"Error looking up user by athlete ID {athlete_id}: {e}")
            return None
    
    def _fetch_activity_details(self, activity_id: int, access_token: str) -> Optional[Dict[str, Any]]:
        """Fetch full activity details from Strava API"""
        try:
            headers = {'Authorization': f'Bearer {access_token}'}
            url = f'https://www.strava.com/api/v3/activities/{activity_id}'
            
            response = requests.get(url, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"Failed to fetch activity {activity_id}: {response.status_code}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error fetching activity details: {e}")
            return None
    
    def create_webhook_subscription(self, callback_url: str) -> Dict[str, Any]:
        """Create a webhook subscription with Strava"""
        try:
            url = "https://www.strava.com/api/v3/push_subscriptions"
            data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'callback_url': callback_url,
                'verify_token': self.verify_token
            }
            
            response = requests.post(url, data=data, timeout=10)
            
            if response.status_code == 201:
                subscription_data = response.json()
                self.logger.info(f"Webhook subscription created: {subscription_data}")
                return {"success": True, "subscription": subscription_data}
            else:
                self.logger.error(f"Failed to create webhook subscription: {response.status_code} - {response.text}")
                return {"success": False, "error": response.text}
                
        except Exception as e:
            self.logger.error(f"Error creating webhook subscription: {e}")
            return {"success": False, "error": str(e)}
    
    def get_webhook_subscription(self) -> Dict[str, Any]:
        """Get current webhook subscription"""
        try:
            url = "https://www.strava.com/api/v3/push_subscriptions"
            params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                subscriptions = response.json()
                return {"success": True, "subscriptions": subscriptions}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def delete_webhook_subscription(self, subscription_id: int) -> Dict[str, Any]:
        """Delete a webhook subscription"""
        try:
            url = f"https://www.strava.com/api/v3/push_subscriptions/{subscription_id}"
            params = {
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            response = requests.delete(url, params=params, timeout=10)
            
            if response.status_code == 204:
                self.logger.info(f"Webhook subscription {subscription_id} deleted")
                return {"success": True}
            else:
                return {"success": False, "error": response.text}
                
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _log_webhook_event(self, event_data: Dict[str, Any]) -> None:
        """
        Log incoming webhook event to activity_notifications table for debugging
        """
        try:
            object_type = event_data.get('object_type', 'unknown')
            aspect_type = event_data.get('aspect_type', 'unknown') 
            object_id = event_data.get('object_id', 0)
            owner_id = event_data.get('owner_id')
            
            # Get our internal user ID from Strava athlete ID
            user_id = None
            if owner_id:
                user_id = self._get_user_id_by_athlete_id(owner_id)
            
            # Create a webhook log entry in activity_notifications
            webhook_log_data = {
                'user_id': user_id,  # May be None if user not found
                'strava_activity_id': object_id if object_type == 'activity' else 0,
                'activity_type': f"WEBHOOK_{object_type.upper()}_{aspect_type.upper()}",
                'activity_name': f"Webhook: {object_type}.{aspect_type}",
                'activity_data': {
                    'webhook_event': event_data,
                    'event_received_at': datetime.utcnow().isoformat(),
                    'object_type': object_type,
                    'aspect_type': aspect_type,
                    'object_id': object_id,
                    'owner_id': owner_id
                },
                'notification_sent': False,  # This is just a log entry
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Insert webhook log (always use admin client for webhook events to bypass RLS)
            self.supabase_admin.table('activity_notifications').insert(webhook_log_data).execute()
                
            self.logger.info(f"📝 Webhook event logged: {object_type}.{aspect_type} for object {object_id}")
            
        except Exception as e:
            self.logger.error(f"Error logging webhook event: {e}")
            # Don't fail the webhook processing if logging fails
