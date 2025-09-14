import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client, Client
import requests
from dotenv import load_dotenv
import json
import hashlib
import secrets
from functools import wraps
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Initialize supabase client only if credentials are provided
supabase = None
supabase_admin = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Create admin client with service role key for bypassing RLS
        if SUPABASE_SERVICE_KEY:
            supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        else:
            supabase_admin = supabase  # Fallback to regular client
    except Exception as e:
        print(f"Warning: Failed to initialize Supabase client: {e}")
        print("Please check your SUPABASE_URL and SUPABASE_KEY in .env file")
else:
    print("Warning: SUPABASE_URL and SUPABASE_KEY not configured")
    print("Please set these values in your .env file")

# Strava configuration
STRAVA_CLIENT_ID = os.getenv('STRAVA_CLIENT_ID')
STRAVA_CLIENT_SECRET = os.getenv('STRAVA_CLIENT_SECRET')
STRAVA_REDIRECT_URI = os.getenv('STRAVA_REDIRECT_URI', 'http://localhost:5000/strava/callback')

# Personal Access Token utilities
def generate_pat():
    """Generate a new personal access token"""
    return f"jolt_pat_{secrets.token_hex(28)}"  # 64 chars total

def hash_token(token):
    """Create SHA-256 hash of token for database storage"""
    return hashlib.sha256(token.encode()).hexdigest()

def verify_token(token, token_hash):
    """Verify a token against its hash"""
    return hashlib.sha256(token.encode()).hexdigest() == token_hash

def require_auth(f):
    """Decorator to require session authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def require_api_auth(f):
    """Decorator to require API token authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid authorization header'}), 401
        
        token = auth_header.split(' ')[1]
        if not token.startswith('jolt_pat_'):
            return jsonify({'error': 'Invalid token format'}), 401
        
        # Verify token in database
        token_hash = hash_token(token)
        try:
            result = supabase.table('personal_access_tokens').select('*').eq('token_hash', token_hash).eq('is_active', True).execute()
            
            if not result.data:
                return jsonify({'error': 'Invalid or expired token'}), 401
            
            token_record = result.data[0]
            
            # Check if token is expired
            if token_record.get('expires_at'):
                expires_at = datetime.fromisoformat(token_record['expires_at'].replace('Z', '+00:00'))
                if expires_at < datetime.now(expires_at.tzinfo):
                    return jsonify({'error': 'Token has expired'}), 401
            
            # Update last_used_at
            supabase.table('personal_access_tokens').update({
                'last_used_at': datetime.utcnow().isoformat()
            }).eq('id', token_record['id']).execute()
            
            # Add user info to request context
            request.current_user_id = token_record['user_id']
            
            return f(*args, **kwargs)
            
        except Exception as e:
            return jsonify({'error': 'Token validation failed'}), 401
    
    return decorated_function

@app.route('/')
def index():
    """Landing page - redirect to login if not authenticated"""
    if 'user' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if not supabase:
        flash('Supabase is not configured. Please check your environment variables.', 'error')
        return render_template('login.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        try:
            # Authenticate with Supabase
            response = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            if response.user:
                session['user'] = {
                    'id': response.user.id,
                    'email': response.user.email
                }
                flash('Login successful!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Invalid credentials', 'error')
                
        except Exception as e:
            flash(f'Login failed: {str(e)}', 'error')
    
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """Signup page"""
    if not supabase:
        flash('Supabase is not configured. Please check your environment variables.', 'error')
        return render_template('signup.html')
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        if password != confirm_password:
            flash('Passwords do not match', 'error')
            return render_template('signup.html')
        
        try:
            # Sign up with Supabase
            response = supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if response.user:
                # Automatically sign in the user after successful signup
                session['user'] = {
                    'id': response.user.id,
                    'email': response.user.email
                }
                flash('Account created successfully! Welcome to Jolt!', 'success')
                return redirect(url_for('home'))
            else:
                flash('Signup failed', 'error')
                
        except Exception as e:
            flash(f'Signup failed: {str(e)}', 'error')
    
    return render_template('signup.html')

@app.route('/logout')
def logout():
    """Logout user"""
    try:
        if supabase:
            supabase.auth.sign_out()
        session.clear()
        flash('Logged out successfully', 'success')
    except Exception as e:
        flash(f'Logout error: {str(e)}', 'error')
    
    return redirect(url_for('login'))

@app.route('/home')
@require_auth
def home():
    """Home page - requires authentication"""
    # Check if user has connected Strava
    strava_connected = 'strava_access_token' in session
    
    return render_template('home.html', 
                         user=session['user'], 
                         strava_connected=strava_connected)

@app.route('/strava/connect')
def strava_connect():
    """Redirect to Strava OAuth"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if not STRAVA_CLIENT_ID:
        flash('Strava client ID not configured', 'error')
        return redirect(url_for('home'))
    
    # Build Strava OAuth URL
    strava_auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={STRAVA_CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={STRAVA_REDIRECT_URI}&"
        f"approval_prompt=force&"
        f"scope=read,activity:read_all"
    )
    
    return redirect(strava_auth_url)

@app.route('/strava/callback')
def strava_callback():
    """Handle Strava OAuth callback"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    code = request.args.get('code')
    if not code:
        flash('Strava authorization failed', 'error')
        return redirect(url_for('home'))
    
    try:
        # Exchange code for access token
        token_url = "https://www.strava.com/oauth/token"
        token_data = {
            'client_id': STRAVA_CLIENT_ID,
            'client_secret': STRAVA_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code'
        }
        
        response = requests.post(token_url, data=token_data)
        token_response = response.json()
        
        if 'access_token' in token_response:
            session['strava_access_token'] = token_response['access_token']
            session['strava_athlete'] = token_response['athlete']
            flash('Strava connected successfully!', 'success')
        else:
            flash('Failed to connect to Strava', 'error')
            
    except Exception as e:
        flash(f'Strava connection error: {str(e)}', 'error')
    
    return redirect(url_for('home'))

@app.route('/strava/activities')
def strava_activities():
    """Display Strava activities"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if 'strava_access_token' not in session:
        flash('Please connect your Strava account first', 'error')
        return redirect(url_for('home'))
    
    try:
        # Fetch activities from Strava
        headers = {'Authorization': f'Bearer {session["strava_access_token"]}'}
        activities_url = 'https://www.strava.com/api/v3/athlete/activities'
        
        response = requests.get(activities_url, headers=headers, params={'per_page': 10})
        activities = response.json()
        
        if response.status_code == 200:
            return render_template('activities.html', activities=activities)
        else:
            flash('Failed to fetch activities from Strava', 'error')
            return redirect(url_for('home'))
            
    except Exception as e:
        flash(f'Error fetching activities: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/strava/disconnect')
def strava_disconnect():
    """Disconnect Strava account"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    # Remove Strava data from session
    session.pop('strava_access_token', None)
    session.pop('strava_athlete', None)
    
    flash('Strava account disconnected', 'success')
    return redirect(url_for('home'))

# Personal Access Token Management Routes
@app.route('/api-token')
@require_auth
def api_token():
    """Display user's personal access token"""
    try:
        result = supabase.table('personal_access_tokens').select('id, last_used_at, expires_at, created_at, is_active').eq('user_id', session['user']['id']).single().execute()
        
        token_data = result.data if result.data else None
        return render_template('api_token.html', token=token_data)
        
    except Exception as e:
        # No token exists yet
        return render_template('api_token.html', token=None)

@app.route('/api-token/generate', methods=['POST'])
@require_auth
def generate_api_token():
    """Generate or regenerate user's personal access token"""
    try:
        # Generate new token
        token = generate_pat()
        token_hash = hash_token(token)
        
        # Calculate expiration (1 year from now)
        expires_at = datetime.utcnow() + timedelta(days=365)
        
        # Check if user already has a token
        existing_result = supabase.table('personal_access_tokens').select('id').eq('user_id', session['user']['id']).execute()
        
        if existing_result.data:
            # Update existing token
            result = supabase.table('personal_access_tokens').update({
                'token_hash': token_hash,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'last_used_at': None,
                'is_active': True
            }).eq('user_id', session['user']['id']).execute()
        else:
            # Create new token
            result = supabase.table('personal_access_tokens').insert({
                'user_id': session['user']['id'],
                'token_hash': token_hash,
                'expires_at': expires_at.isoformat()
            }).execute()
        
        if result.data:
            # Show token to user (only time they'll see it)
            return render_template('token_generated.html', token=token)
        else:
            flash('Failed to generate token', 'error')
            
    except Exception as e:
        flash(f'Error generating token: {str(e)}', 'error')
    
    return redirect(url_for('api_token'))

@app.route('/api-token/revoke', methods=['POST'])
@require_auth
def revoke_api_token():
    """Revoke user's personal access token"""
    try:
        result = supabase.table('personal_access_tokens').update({
            'is_active': False
        }).eq('user_id', session['user']['id']).execute()
        
        if result.data:
            flash('API token revoked successfully', 'success')
        else:
            flash('No active token found', 'error')
            
    except Exception as e:
        flash(f'Error revoking token: {str(e)}', 'error')
    
    return redirect(url_for('api_token'))

# API Routes (Token authenticated)
@app.route('/api/v1/profile')
@require_api_auth
def api_profile():
    """Get user profile via API"""
    try:
        # Get user data from Supabase
        result = supabase.auth.admin.get_user(request.current_user_id)
        user = result.user
        
        return jsonify({
            'id': user.id,
            'email': user.email,
            'created_at': user.created_at
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/activities')
@require_api_auth
def api_activities():
    """Get user's Strava activities via API"""
    try:
        # This would need to fetch the user's Strava token from database
        # For now, return a placeholder
        return jsonify({
            'message': 'Activities endpoint - integration with stored Strava tokens needed',
            'user_id': request.current_user_id,
            'activities': []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/stats')
@require_api_auth  
def api_stats():
    """Get user's running statistics via API"""
    try:
        # Placeholder for stats calculation
        return jsonify({
            'total_runs': 0,
            'total_distance': 0,
            'total_time': 0,
            'average_pace': 0,
            'user_id': request.current_user_id
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/email')
@require_api_auth
def api_email():
    """Get user's email address via API"""
    try:
        # For now, we'll need to get the email from the personal_access_tokens table
        # by looking up the user who owns this token, then get their email from the session data
        # Since we don't have direct access to user email from just the user_id,
        # let's create a temporary solution that gets the email from login records
        
        # Simple approach: return the user_id for now and we'll enhance this
        # In a real app, you'd want to store email in the tokens table or use proper user management
        return jsonify({
            'user_id': request.current_user_id,
            'message': 'Email retrieval not fully implemented yet. User ID provided instead.'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Session-based API endpoints for token management
@app.route('/api/v1/token', methods=['GET'])
@require_auth
def api_get_token():
    """Get current token status via API (requires session auth)"""
    try:
        result = supabase.table('personal_access_tokens').select('id, last_used_at, expires_at, created_at, is_active').eq('user_id', session['user']['id']).single().execute()
        
        if result.data:
            token_data = result.data
            return jsonify({
                'has_token': True,
                'token_info': {
                    'id': token_data['id'],
                    'created_at': token_data['created_at'],
                    'expires_at': token_data['expires_at'],
                    'last_used_at': token_data['last_used_at'],
                    'is_active': token_data['is_active']
                }
            })
        else:
            return jsonify({
                'has_token': False,
                'token_info': None
            })
            
    except Exception as e:
        return jsonify({
            'has_token': False,
            'token_info': None,
            'message': 'No token found'
        })

@app.route('/api/v1/token', methods=['POST'])
@require_auth
def api_generate_token():
    """Generate or regenerate token via API (requires session auth)"""
    try:
        # Generate new token
        token = generate_pat()
        token_hash = hash_token(token)
        
        # Calculate expiration (1 year from now)
        expires_at = datetime.utcnow() + timedelta(days=365)
        
        # Check if user already has a token
        existing_result = supabase.table('personal_access_tokens').select('id').eq('user_id', session['user']['id']).execute()
        
        if existing_result.data:
            # Update existing token
            result = supabase.table('personal_access_tokens').update({
                'token_hash': token_hash,
                'expires_at': expires_at.isoformat(),
                'created_at': datetime.utcnow().isoformat(),
                'last_used_at': None,
                'is_active': True
            }).eq('user_id', session['user']['id']).execute()
        else:
            # Create new token
            result = supabase.table('personal_access_tokens').insert({
                'user_id': session['user']['id'],
                'token_hash': token_hash,
                'expires_at': expires_at.isoformat()
            }).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'token': token,
                'message': 'Token generated successfully',
                'expires_at': expires_at.isoformat(),
                'warning': 'This is the only time you will see this token. Store it securely!'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to generate token'
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/v1/token', methods=['DELETE'])
@require_auth
def api_revoke_token():
    """Revoke token via API (requires session auth)"""
    try:
        result = supabase.table('personal_access_tokens').update({
            'is_active': False
        }).eq('user_id', session['user']['id']).execute()
        
        if result.data:
            return jsonify({
                'success': True,
                'message': 'Token revoked successfully'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'No active token found'
            }), 404
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    # For local development only
    app.run(debug=True, port=5001)
