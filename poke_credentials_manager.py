"""
Poke Credentials Manager
Handles storage and retrieval of user Poke API keys
"""

from typing import Optional, Dict, Any
from datetime import datetime
import logging

class PokeCredentialsManager:
    """Manages Poke API credentials for users"""
    
    def __init__(self, supabase_client, supabase_admin_client):
        self.supabase = supabase_client
        self.supabase_admin = supabase_admin_client
        self.logger = logging.getLogger(__name__)
    
    def store_api_key(self, user_id: str, api_key: str) -> Dict[str, Any]:
        """
        Store or update a user's Poke API key
        
        Args:
            user_id: User's UUID
            api_key: Poke API key
            
        Returns:
            Dict with success status and data
        """
        try:
            # Check if user already has credentials
            existing = self.get_credentials(user_id)
            
            if existing:
                # Update existing credentials
                result = self.supabase.table('poke_credentials').update({
                    'api_key': api_key,
                    'updated_at': datetime.utcnow().isoformat(),
                    'is_active': True
                }).eq('user_id', user_id).execute()
                
                action = 'updated'
            else:
                # Create new credentials
                result = self.supabase.table('poke_credentials').insert({
                    'user_id': user_id,
                    'api_key': api_key,
                    'is_active': True,
                    'created_at': datetime.utcnow().isoformat()
                }).execute()
                
                action = 'created'
            
            if result.data:
                self.logger.info(f"✅ Poke API key {action} for user {user_id}")
                return {
                    'success': True,
                    'action': action,
                    'data': result.data[0]
                }
            else:
                return {'success': False, 'error': 'Failed to store API key'}
                
        except Exception as e:
            self.logger.error(f"Error storing Poke API key for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user's active Poke credentials
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict with credentials or None if not found
        """
        try:
            result = self.supabase.table('poke_credentials').select('*').eq(
                'user_id', user_id
            ).eq('is_active', True).single().execute()
            
            if result.data:
                return result.data
            return None
            
        except Exception as e:
            # No credentials found (normal case)
            return None
    
    def get_api_key(self, user_id: str) -> Optional[str]:
        """
        Get user's Poke API key
        
        Args:
            user_id: User's UUID
            
        Returns:
            API key string or None if not found
        """
        credentials = self.get_credentials(user_id)
        return credentials['api_key'] if credentials else None
    
    def remove_credentials(self, user_id: str) -> Dict[str, Any]:
        """
        Remove user's Poke credentials (deactivate)
        
        Args:
            user_id: User's UUID
            
        Returns:
            Dict with success status
        """
        try:
            result = self.supabase.table('poke_credentials').update({
                'is_active': False,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
            
            if result.data:
                self.logger.info(f"✅ Poke credentials removed for user {user_id}")
                return {'success': True, 'message': 'Credentials removed successfully'}
            else:
                return {'success': False, 'error': 'No credentials found to remove'}
                
        except Exception as e:
            self.logger.error(f"Error removing Poke credentials for user {user_id}: {e}")
            return {'success': False, 'error': str(e)}
    
    def update_last_used(self, user_id: str) -> None:
        """
        Update the last_used_at timestamp for user's credentials
        
        Args:
            user_id: User's UUID
        """
        try:
            self.supabase_admin.table('poke_credentials').update({
                'last_used_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).eq('is_active', True).execute()
            
        except Exception as e:
            self.logger.error(f"Error updating last used timestamp: {e}")
    
    def mark_test_message_sent(self, user_id: str) -> None:
        """
        Mark that a test message has been sent for this user
        
        Args:
            user_id: User's UUID
        """
        try:
            self.supabase_admin.table('poke_credentials').update({
                'test_message_sent': True,
                'updated_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).eq('is_active', True).execute()
            
        except Exception as e:
            self.logger.error(f"Error marking test message sent: {e}")
    
    def get_all_active_users(self) -> list:
        """
        Get all users with active Poke credentials
        
        Returns:
            List of user credentials
        """
        try:
            result = self.supabase_admin.table('poke_credentials').select('*').eq(
                'is_active', True
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            self.logger.error(f"Error getting active Poke users: {e}")
            return []
    
    def has_credentials(self, user_id: str) -> bool:
        """
        Check if user has active Poke credentials
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if user has active credentials
        """
        return self.get_credentials(user_id) is not None
