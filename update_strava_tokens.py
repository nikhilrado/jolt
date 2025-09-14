#!/usr/bin/env python3
"""
Script to update Strava access token usage in app.py
This will replace session-based token access with database-based token access
"""

import re

def update_strava_functions():
    # Read the current app.py file
    with open('/Users/nikhil/Desktop/jolt/app.py', 'r') as f:
        content = f.read()
    
    # Pattern 1: Replace session check
    content = re.sub(
        r"if 'strava_access_token' not in session:",
        r"user_id = session['user']['id']\n    if not strava_token_manager or not strava_token_manager.is_connected(user_id):",
        content
    )
    
    # Pattern 2: Replace flash message for disconnected
    content = re.sub(
        r"flash\('Please connect your Strava account first', 'error'\)",
        r"flash('Please connect your Strava account first', 'error')",
        content
    )
    
    # Pattern 3: Replace header creation with token
    content = re.sub(
        r"headers = \{'Authorization': f'Bearer \{session\[\"strava_access_token\"\]\}'\}",
        r"access_token = get_user_strava_token(user_id)\n        if not access_token:\n            flash('Strava connection expired. Please reconnect your account.', 'error')\n            return redirect(url_for('home'))\n        \n        headers = {'Authorization': f'Bearer {access_token}'}",
        content
    )
    
    return content

if __name__ == "__main__":
    updated_content = update_strava_functions()
    
    # Write back to file
    with open('/Users/nikhil/Desktop/jolt/app.py', 'w') as f:
        f.write(updated_content)
    
    print("Updated app.py with new Strava token management")
