"""
Poke API Integration Service
Handles sending messages to users via Poke API
"""

import requests
import logging
from typing import Dict, Optional, Any
from datetime import datetime

class PokeService:
    """Service for sending messages via Poke API"""
    
    def __init__(self):
        self.base_url = "https://poke.com/api/v1/inbound-sms/webhook"
        self.logger = logging.getLogger(__name__)
        
    def send_message(self, api_key: str, message: str) -> Dict[str, Any]:
        """
        Send a message via Poke API
        
        Args:
            api_key: User's Poke API key
            message: Message text to send
            
        Returns:
            Dict containing success status and response data
        """
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'message': message
            }
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=10
            )
            
            response_data = response.json() if response.content else {}
            
            if response.status_code == 200:
                self.logger.info(f"✅ Poke message sent successfully")
                return {
                    'success': True,
                    'status_code': response.status_code,
                    'response': response_data,
                    'sent_at': datetime.utcnow().isoformat()
                }
            else:
                self.logger.error(f"❌ Poke API error: {response.status_code} - {response_data}")
                return {
                    'success': False,
                    'status_code': response.status_code,
                    'error': response_data,
                    'sent_at': datetime.utcnow().isoformat()
                }
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"❌ Poke API request failed: {e}")
            return {
                'success': False,
                'error': f'Request failed: {str(e)}',
                'sent_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            self.logger.error(f"❌ Unexpected error sending Poke message: {e}")
            return {
                'success': False,
                'error': f'Unexpected error: {str(e)}',
                'sent_at': datetime.utcnow().isoformat()
            }
    
    def send_run_completion_message(self, api_key: str, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a post-run message asking how the run went
        
        Args:
            api_key: User's Poke API key
            activity_data: Strava activity data
            
        Returns:
            Dict containing success status and response data
        """
        # Extract activity details
        activity_name = activity_data.get('name', 'Your run')
        activity_type = activity_data.get('type', 'Run')
        distance_meters = activity_data.get('distance', 0)
        distance_km = round(distance_meters / 1000, 2) if distance_meters else 0
        moving_time = activity_data.get('moving_time', 0)
        
        # Format duration
        if moving_time:
            minutes = moving_time // 60
            seconds = moving_time % 60
            duration_str = f"{minutes}:{seconds:02d}"
        else:
            duration_str = "unknown time"
        
        # Create personalized message
        if distance_km > 0:
            message = f"🏃‍♂️ Great job on your {distance_km}km {activity_type.lower()} in {duration_str}! How did it feel? Any thoughts on your performance today?"
        else:
            message = f"🏃‍♂️ Nice work on '{activity_name}'! How did your {activity_type.lower()} go today? How are you feeling?"
        
        return self.send_message(api_key, message)
    
    def test_api_key(self, api_key: str) -> Dict[str, Any]:
        """
        Test if a Poke API key is valid by sending a test message
        
        Args:
            api_key: Poke API key to test
            
        Returns:
            Dict containing validation results
        """
        test_message = "🔧 Testing your Poke API key from Jolt - this confirms your integration is working!"
        
        result = self.send_message(api_key, test_message)
        
        if result['success']:
            return {
                'valid': True,
                'message': 'API key is valid! Test message sent successfully.',
                'test_result': result
            }
        else:
            return {
                'valid': False,
                'message': 'API key validation failed. Please check your key.',
                'error': result.get('error', 'Unknown error'),
                'test_result': result
            }

# Global instance
poke_service = PokeService()
