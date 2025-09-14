"""
Strava token management utilities
Handles storing, retrieving, and refreshing Strava OAuth tokens
"""

import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
import os

class StravaTokenManager:
    def __init__(self, supabase_client, supabase_admin_client=None):
        self.supabase = supabase_client
        self.supabase_admin = supabase_admin_client or supabase_client
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    def store_credentials(self, user_id: str, token_response: Dict[str, Any]) -> bool:
        """Store Strava credentials in database"""
        try:
            # Calculate expiration time using timezone-aware datetime
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=token_response.get('expires_in', 21600))
            
            credentials_data = {
                'user_id': user_id,
                'access_token': token_response['access_token'],
                'refresh_token': token_response['refresh_token'],
                'expires_at': expires_at.isoformat(),
                'athlete_id': token_response['athlete']['id'],
                'athlete_data': token_response['athlete'],
                'scope': token_response.get('scope', ''),  # Store granted scopes
                'updated_at': datetime.now(timezone.utc).isoformat()
            }
            
            # Use upsert to handle updates if credentials already exist
            result = self.supabase.table('strava_credentials').upsert(
                credentials_data,
                on_conflict='user_id'
            ).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error storing Strava credentials: {e}")
            return False
    
    def get_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get Strava credentials for a user"""
        try:
            result = self.supabase.table('strava_credentials').select('*').eq(
                'user_id', user_id
            ).eq('is_active', True).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            print(f"Error retrieving Strava credentials: {e}")
            return None
    
    def get_valid_access_token(self, user_id: str) -> Optional[str]:
        """Get a valid access token, refreshing if necessary"""
        credentials = self.get_credentials(user_id)
        if not credentials:
            return None
        
        # Check if token is expired or will expire within 1 hour (3600 seconds)
        # This follows Strava's recommendation to refresh tokens that expire in 1 hour or less
        expires_at = datetime.fromisoformat(credentials['expires_at'].replace('Z', '+00:00'))
        current_time = datetime.now(expires_at.tzinfo)  # Make sure both datetimes have the same timezone
        time_until_expiry = (expires_at - current_time).total_seconds()
        
        if time_until_expiry <= 3600:  # 1 hour = 3600 seconds
            # Token is expired or will expire within 1 hour, refresh it
            new_credentials = self.refresh_token(credentials['refresh_token'])
            if new_credentials:
                # Update stored credentials
                self.store_credentials(user_id, new_credentials)
                return new_credentials['access_token']
            else:
                # Refresh failed, credentials are invalid
                self.invalidate_credentials(user_id)
                return None
        
        return credentials['access_token']
    
    def refresh_token(self, refresh_token: str) -> Optional[Dict[str, Any]]:
        """Refresh an expired Strava access token"""
        try:
            refresh_url = "https://www.strava.com/oauth/token"
            refresh_data = {
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'refresh_token': refresh_token,
                'grant_type': 'refresh_token'
            }
            
            response = requests.post(refresh_url, data=refresh_data)
            response_data = response.json()
            
            if response.status_code == 200:
                # Always use the new refresh token from the response
                # According to Strava docs: "Always use the most recent refresh token"
                return response_data
            elif response.status_code == 400:
                error = response_data.get('message', 'Bad request')
                print(f"Token refresh failed - Bad request: {error}")
                return None
            elif response.status_code == 401:
                print("Token refresh failed - Unauthorized (refresh token invalid or expired)")
                return None
            else:
                print(f"Token refresh failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error refreshing Strava token: {e}")
            return None
    
    def invalidate_credentials(self, user_id: str) -> bool:
        """Mark credentials as inactive"""
        try:
            result = self.supabase.table('strava_credentials').update({
                'is_active': False,
                'updated_at': datetime.now(timezone.utc).isoformat()
            }).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error invalidating Strava credentials: {e}")
            return False
    
    def is_connected(self, user_id: str) -> bool:
        """Check if user has valid Strava credentials"""
        return self.get_valid_access_token(user_id) is not None
    
    def get_granted_scopes(self, user_id: str) -> List[str]:
        """Get the scopes that were granted by the user"""
        credentials = self.get_credentials(user_id)
        if not credentials or not credentials.get('scope'):
            return []
        return credentials['scope'].split(',')
    
    def has_required_scopes(self, user_id: str, required_scopes: List[str]) -> bool:
        """Check if user has granted all required scopes"""
        granted_scopes = self.get_granted_scopes(user_id)
        return all(scope in granted_scopes for scope in required_scopes)
    
    def get_all_active_users(self) -> list:
        """Get all users with active Strava credentials (for cron jobs)"""
        try:
            # Use admin client to bypass RLS for system operations
            result = self.supabase_admin.table('strava_credentials').select(
                'user_id, athlete_id, last_activity_check, last_activity_id'
            ).eq('is_active', True).execute()
            
            return result.data
            
        except Exception as e:
            print(f"Error getting active Strava users: {e}")
            return []
    
    def update_last_activity_check(self, user_id: str, last_activity_id: Optional[int] = None) -> bool:
        """Update the last activity check timestamp and optionally the last activity ID"""
        try:
            update_data = {
                'last_activity_check': datetime.now(timezone.utc).isoformat()
            }
            
            if last_activity_id is not None:
                update_data['last_activity_id'] = str(last_activity_id)
            
            result = self.supabase_admin.table('strava_credentials').update(
                update_data
            ).eq('user_id', user_id).execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            print(f"Error updating last activity check: {e}")
            return False
