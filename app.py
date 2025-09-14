import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client, Client
import requests
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Initialize supabase client only if credentials are provided
supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
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
def home():
    """Home page - requires authentication"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
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

if __name__ == '__main__':
    app.run(debug=True, port=5000)
