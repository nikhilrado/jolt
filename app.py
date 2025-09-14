import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from supabase import create_client, Client
import requests
from dotenv import load_dotenv
import json
import statistics
from analytics_engine import AdvancedAnalyticsEngine, WellnessMetrics, TrainingInsights
from performance_psychology import PerformancePsychologyEngine
from strava_token_manager import StravaTokenManager
from strava_webhook_manager import StravaWebhookManager
import hashlib
import secrets
from functools import wraps
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# CalorieNinjas API configuration
CALORIE_NINJAS_API_URL = os.getenv('CALORIE_NINJAS_API_URL', 'https://api.calorieninjas.com/v1/nutrition')
CALORIE_NINJAS_API_KEY = os.getenv('CALORIE_NINJAS_API_KEY')  # Fallback to your key

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')

# Initialize supabase client only if credentials are provided
supabase = None
supabase_admin = None
strava_token_manager = None
strava_webhook_manager = None

if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Create admin client with service role key for bypassing RLS
        if SUPABASE_SERVICE_KEY:
            supabase_admin: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
        else:
            supabase_admin = supabase  # Fallback to regular client
        
        # Initialize Strava managers
        strava_token_manager = StravaTokenManager(supabase, supabase_admin)
        strava_webhook_manager = StravaWebhookManager(supabase, supabase_admin, strava_token_manager)
        
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

def get_user_strava_token(user_id):
    """Helper function to get valid Strava access token for a user"""
    if not strava_token_manager:
        return None
    
    access_token = strava_token_manager.get_valid_access_token(user_id)
    return access_token

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
    user_id = session['user']['id']
    strava_connected = strava_token_manager.is_connected(user_id) if strava_token_manager else False
    
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
    
    # Generate a state parameter for security (CSRF protection)
    state = secrets.token_urlsafe(32)
    session['strava_oauth_state'] = state
    
    # Build Strava OAuth URL following best practices
    strava_auth_url = (
        f"https://www.strava.com/oauth/authorize?"
        f"client_id={STRAVA_CLIENT_ID}&"
        f"response_type=code&"
        f"redirect_uri={STRAVA_REDIRECT_URI}&"
        f"approval_prompt=auto&"  # Use 'auto' instead of 'force' for better UX
        f"scope=read,activity:read_all&"  # Request minimal required scopes
        f"state={state}"  # Add state for CSRF protection
    )
    
    return redirect(strava_auth_url)

@app.route('/strava/callback')
def strava_callback():
    """Handle Strava OAuth callback"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    code = request.args.get('code')
    state = request.args.get('state')
    error = request.args.get('error')
    
    # Check for authorization errors
    if error:
        flash(f'Strava authorization error: {error}', 'error')
        return redirect(url_for('home'))
    
    if not code:
        flash('Strava authorization failed - no code received', 'error')
        return redirect(url_for('home'))
    
    # Verify state parameter for CSRF protection
    if not state or state != session.get('strava_oauth_state'):
        flash('Strava authorization failed - invalid state parameter', 'error')
        return redirect(url_for('home'))
    
    # Clear the state from session
    session.pop('strava_oauth_state', None)
    
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
        
        if response.status_code == 200 and 'access_token' in token_response:
            # Store credentials in database instead of session
            user_id = session['user']['id']
            if strava_token_manager and strava_token_manager.store_credentials(user_id, token_response):
                # Check what scopes were actually granted
                granted_scopes = token_response.get('scope', '').split(',')
                required_scopes = ['read', 'activity:read_all']
                
                missing_scopes = [scope for scope in required_scopes if scope not in granted_scopes]
                if missing_scopes:
                    flash(f'Warning: Some permissions were not granted: {", ".join(missing_scopes)}', 'warning')
                
                flash('Strava connected successfully!', 'success')
            else:
                flash('Failed to store Strava credentials', 'error')
        else:
            error_description = token_response.get('message', 'Unknown error')
            flash(f'Failed to connect to Strava: {error_description}', 'error')
            
    except Exception as e:
        flash(f'Strava connection error: {str(e)}', 'error')
    
    return redirect(url_for('home'))

@app.route('/strava/disconnect', methods=['POST'])
@require_auth
def strava_disconnect():
    """Disconnect Strava account"""
    if not strava_token_manager:
        flash('Strava token manager not available', 'error')
        return redirect(url_for('home'))
    
    user_id = session['user']['id']
    
    try:
        # Get current access token
        access_token = strava_token_manager.get_valid_access_token(user_id)
        
        if access_token:
            # Deauthorize on Strava's side
            deauth_url = "https://www.strava.com/oauth/deauthorize"
            deauth_data = {'access_token': access_token}
            
            response = requests.post(deauth_url, data=deauth_data)
            
            if response.status_code != 200:
                print(f"Failed to deauthorize on Strava: {response.status_code} - {response.text}")
        
        # Invalidate credentials in our database regardless of Strava's response
        if strava_token_manager.invalidate_credentials(user_id):
            flash('Strava account disconnected successfully', 'success')
        else:
            flash('Failed to disconnect Strava account', 'error')
            
    except Exception as e:
        flash(f'Error disconnecting Strava: {str(e)}', 'error')
    
    return redirect(url_for('home'))

# ============================================================================
# STRAVA WEBHOOK ENDPOINTS
# ============================================================================

@app.route('/webhooks/strava', methods=['GET', 'POST'])
def strava_webhook():
    """
    Handle Strava webhook events
    GET: Webhook subscription validation
    POST: Actual webhook events
    """
    if not strava_webhook_manager:
        return jsonify({'error': 'Webhook manager not initialized'}), 500
    
    if request.method == 'GET':
        # Handle subscription validation
        result = strava_webhook_manager.handle_subscription_validation(request.args)
        
        if 'error' in result:
            return jsonify(result), 400
        
        return jsonify(result), 200
    
    elif request.method == 'POST':
        # Handle webhook event
        try:
            event_data = request.get_json()
            
            if not event_data:
                return jsonify({'error': 'No JSON data received'}), 400
            
            # Process the webhook event
            result = strava_webhook_manager.handle_webhook_event(event_data)
            
            # Always return 200 OK to acknowledge receipt (required by Strava)
            return jsonify(result), 200
            
        except Exception as e:
            # Still return 200 to acknowledge receipt, but log the error
            print(f"Error processing webhook: {e}")
            return jsonify({'status': 'error', 'message': str(e)}), 200

# ============================================================================
# WEBHOOK MANAGEMENT ENDPOINTS (API TOKEN REQUIRED)
# ============================================================================

@app.route('/admin/webhooks/create', methods=['POST'])
@require_api_auth
def create_webhook_subscription():
    """Create a Strava webhook subscription"""
    if not strava_webhook_manager:
        return jsonify({'error': 'Webhook manager not initialized'}), 500
    
    try:
        # Get the callback URL
        callback_url = request.json.get('callback_url')
        
        if not callback_url:
            # Auto-generate callback URL based on request
            base_url = request.url_root.rstrip('/')
            callback_url = f"{base_url}/webhooks/strava"
        
        result = strava_webhook_manager.create_webhook_subscription(callback_url)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/webhooks/status', methods=['GET'])
@require_api_auth
def get_webhook_status():
    """Get current webhook subscription status"""
    if not strava_webhook_manager:
        return jsonify({'error': 'Webhook manager not initialized'}), 500
    
    try:
        result = strava_webhook_manager.get_webhook_subscription()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/webhooks/delete/<int:subscription_id>', methods=['DELETE'])
@require_api_auth
def delete_webhook_subscription(subscription_id):
    """Delete a webhook subscription"""
    if not strava_webhook_manager:
        return jsonify({'error': 'Webhook manager not initialized'}), 500
    
    try:
        result = strava_webhook_manager.delete_webhook_subscription(subscription_id)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/webhooks/test', methods=['POST'])
@require_api_auth
def test_webhook():
    """Test webhook processing with sample data"""
    if not strava_webhook_manager:
        return jsonify({'error': 'Webhook manager not initialized'}), 500
    
    try:
        # Sample webhook event for testing
        test_event = {
            "object_type": "activity",
            "object_id": 12345678,
            "aspect_type": "create",
            "owner_id": 98765432,
            "subscription_id": 1,
            "event_time": 1672531200
        }
        
        result = strava_webhook_manager.handle_webhook_event(test_event)
        return jsonify({
            'test_event': test_event,
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/strava/activities')
def strava_activities():
    """Get Strava activities as JSON"""
    if 'user' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava account not connected'}), 400
    
    try:
        # Get valid access token
        access_token = strava_token_manager.get_valid_access_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        # Fetch activities from Strava
        headers = {'Authorization': f'Bearer {access_token}'}
        activities_url = 'https://www.strava.com/api/v3/athlete/activities'
        
        response = requests.get(activities_url, headers=headers, params={'per_page': 20})
        activities = response.json()
        
        if response.status_code == 200:
            # Enhance each activity with detailed data
            enhanced_activities = []
            for activity in activities:
                enhanced_activity = enhance_activity_data(activity, headers)
                enhanced_activities.append(enhanced_activity)
            
            return jsonify({
                'success': True,
                'total_activities': len(enhanced_activities),
                'activities': enhanced_activities
            })
        else:
            return jsonify({'error': 'Failed to fetch activities from Strava'}), 500
            
    except Exception as e:
        return jsonify({'error': f'Error fetching activities: {str(e)}'}), 500

def enhance_activity_data(activity, headers):
    """Enhance activity with additional detailed data"""
    activity_id = activity['id']
    
    try:
        # Get detailed activity data
        detail_url = f'https://www.strava.com/api/v3/activities/{activity_id}'
        detail_response = requests.get(detail_url, headers=headers)
        
        if detail_response.status_code == 200:
            detailed_activity = detail_response.json()
            
            # Merge detailed data with basic activity data
            activity.update({
                'detailed': detailed_activity,
                'has_heartrate': bool(detailed_activity.get('has_heartrate', False)),
                'has_kudoed': detailed_activity.get('has_kudoed', False),
                'kudos_count': detailed_activity.get('kudos_count', 0),
                'comment_count': detailed_activity.get('comment_count', 0),
                'athlete_count': detailed_activity.get('athlete_count', 1),
                'average_watts': detailed_activity.get('average_watts'),
                'max_watts': detailed_activity.get('max_watts'),
                'weighted_avg_watts': detailed_activity.get('weighted_avg_watts'),
                'kilojoules': detailed_activity.get('kilojoules'),
                'average_cadence': detailed_activity.get('average_cadence'),
                'average_temp': detailed_activity.get('average_temp'),
                'average_heartrate': detailed_activity.get('average_heartrate'),
                'max_heartrate': detailed_activity.get('max_heartrate'),
                'suffer_score': detailed_activity.get('suffer_score'),
                'calories': detailed_activity.get('calories'),
                'description': detailed_activity.get('description', ''),
                'gear': detailed_activity.get('gear', {}),
                'splits_metric': detailed_activity.get('splits_metric', []),
                'laps': detailed_activity.get('laps', [])
            })
        
        # Try to get activity streams (mile splits, heart rate data, etc.)
        try:
            streams_url = f'https://www.strava.com/api/v3/activities/{activity_id}/streams'
            streams_response = requests.get(streams_url, headers=headers, params={
                'keys': 'time,distance,latlng,altitude,heartrate,temp,moving,grade_smooth,velocity_smooth,cadence,watts',
                'key_by_type': 'true'
            })
            
            if streams_response.status_code == 200:
                streams_data = streams_response.json()
                activity['streams'] = streams_data
                
                # Process splits data if available
                if 'distance' in streams_data and 'time' in streams_data:
                    activity['mile_splits'] = calculate_mile_splits(
                        streams_data['distance']['data'], 
                        streams_data['time']['data']
                    )
                    
                # Process heart rate data if available
                if 'heartrate' in streams_data:
                    hr_data = streams_data['heartrate']['data']
                    activity['hr_stats'] = {
                        'avg_hr': sum(hr_data) / len(hr_data) if hr_data else None,
                        'max_hr': max(hr_data) if hr_data else None,
                        'min_hr': min(hr_data) if hr_data else None,
                        'hr_zones': calculate_hr_zones(hr_data) if hr_data else None
                    }
                    
        except Exception as e:
            print(f"Could not fetch streams for activity {activity_id}: {e}")
            activity['streams'] = None
            
    except Exception as e:
        print(f"Could not enhance activity {activity_id}: {e}")
    
    return activity

def calculate_mile_splits(distance_data, time_data):
    """Calculate mile splits from distance and time streams"""
    if not distance_data or not time_data:
        return []
    
    splits = []
    mile_meters = 1609.34  # 1 mile in meters
    
    for i, distance in enumerate(distance_data):
        if distance > 0 and distance % mile_meters < 100:  # Within 100m of a mile
            mile_number = int(distance / mile_meters)
            if mile_number > 0 and mile_number > len(splits):
                time_at_mile = time_data[i] if i < len(time_data) else time_data[-1]
                splits.append({
                    'mile': mile_number,
                    'time': time_at_mile,
                    'pace': time_at_mile / mile_number if mile_number > 0 else 0
                })
    
    return splits

def calculate_hr_zones(hr_data):
    """Calculate heart rate zones (simplified)"""
    if not hr_data:
        return None
    
    avg_hr = sum(hr_data) / len(hr_data)
    max_hr = max(hr_data)
    
    # Simple HR zone calculation (you might want to use actual max HR)
    zones = {
        'zone_1': sum(1 for hr in hr_data if hr < avg_hr * 0.7),
        'zone_2': sum(1 for hr in hr_data if avg_hr * 0.7 <= hr < avg_hr * 0.8),
        'zone_3': sum(1 for hr in hr_data if avg_hr * 0.8 <= hr < avg_hr * 0.9),
        'zone_4': sum(1 for hr in hr_data if avg_hr * 0.9 <= hr < max_hr * 0.95),
        'zone_5': sum(1 for hr in hr_data if hr >= max_hr * 0.95)
    }
    
    return zones

# CalorieNinjas Integration Functions
def analyze_meal_with_calorie_ninjas(meal_description):
    """Analyze meal description using CalorieNinjas API"""
    if not CALORIE_NINJAS_API_KEY:
        print(f"DEBUG: CALORIE_NINJAS_API_KEY is: {CALORIE_NINJAS_API_KEY}")
        print(f"DEBUG: Environment variable CALORIE_NINJAS_API_KEY: {os.getenv('CALORIE_NINJAS_API_KEY')}")
        raise ValueError("CalorieNinjas API key not configured")
    
    headers = {
        'X-Api-Key': CALORIE_NINJAS_API_KEY
    }
    
    try:
        # URL encode the query
        import urllib.parse
        encoded_query = urllib.parse.quote(meal_description)
        url = f"{CALORIE_NINJAS_API_URL}?query={encoded_query}"
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        result = response.json()
        
        if 'items' in result and result['items']:
            # Aggregate all items into a single meal
            total_calories = sum(item.get('calories', 0) for item in result['items'])
            total_carbs = sum(item.get('carbohydrates_total_g', 0) for item in result['items'])
            total_fats = sum(item.get('fat_total_g', 0) for item in result['items'])
            total_protein = sum(item.get('protein_g', 0) for item in result['items'])
            total_sodium = sum(item.get('sodium_mg', 0) for item in result['items'])
            total_fiber = sum(item.get('fiber_g', 0) for item in result['items'])
            total_sugar = sum(item.get('sugar_g', 0) for item in result['items'])
            
            # Create meal name from first few items
            item_names = [item.get('name', 'Unknown') for item in result['items'][:3]]
            meal_name = ', '.join(item_names)
            if len(result['items']) > 3:
                meal_name += f" and {len(result['items']) - 3} more items"
            
            return {
                'name': meal_name,
                'calories': round(total_calories, 1),
                'carbs': round(total_carbs, 1),
                'fats': round(total_fats, 1),
                'protein': round(total_protein, 1),
                'sodium': round(total_sodium, 1),
                'fiber': round(total_fiber, 1),
                'sugar': round(total_sugar, 1),
                'ingredients': result['items'],
                'health_recommendations': generate_health_recommendations(
                    total_calories, total_carbs, total_fats, total_protein, 
                    total_sodium, total_fiber, total_sugar
                )
            }
        else:
            raise ValueError("No nutritional data found for the meal description")
            
    except requests.exceptions.RequestException as e:
        raise ValueError(f"Failed to call CalorieNinjas API: {str(e)}")

def generate_health_recommendations(calories, carbs, fats, protein, sodium, fiber, sugar):
    """Generate health recommendations based on nutritional data"""
    recommendations = []
    
    # Calorie recommendations
    if calories > 800:
        recommendations.append("Consider reducing portion size - this meal is quite high in calories")
    elif calories < 200:
        recommendations.append("This meal is quite low in calories - consider adding more nutrient-dense foods")
    
    # Protein recommendations
    if protein < 15:
        recommendations.append("Add more protein sources like lean meat, fish, beans, or Greek yogurt")
    elif protein > 50:
        recommendations.append("High protein content - great for muscle building and satiety!")
    
    # Fat recommendations
    if fats > 30:
        recommendations.append("Consider reducing saturated fats and opting for healthier fats like olive oil or avocado")
    elif fats < 5:
        recommendations.append("Add healthy fats like nuts, seeds, or olive oil for better nutrient absorption")
    
    # Carbohydrate recommendations
    if carbs > 80:
        recommendations.append("High carb content - consider balancing with more protein and vegetables")
    elif carbs < 20:
        recommendations.append("Low carb content - add some whole grains or fruits for energy")
    
    # Fiber recommendations
    if fiber < 5:
        recommendations.append("Add more fiber-rich foods like vegetables, fruits, or whole grains")
    elif fiber > 15:
        recommendations.append("Excellent fiber content - great for digestive health!")
    
    # Sodium recommendations
    if sodium > 1000:
        recommendations.append("High sodium content - consider reducing salt and processed foods")
    elif sodium < 200:
        recommendations.append("Low sodium content - good for heart health")
    
    # Sugar recommendations
    if sugar > 25:
        recommendations.append("High sugar content - consider reducing added sugars and processed foods")
    elif sugar < 5:
        recommendations.append("Low sugar content - great choice for stable energy")
    
    # Macro balance recommendations
    protein_percentage = (protein * 4 / calories * 100) if calories > 0 else 0
    carb_percentage = (carbs * 4 / calories * 100) if calories > 0 else 0
    fat_percentage = (fats * 9 / calories * 100) if calories > 0 else 0
    
    if protein_percentage < 15:
        recommendations.append("Increase protein to 15-25% of total calories for better muscle health")
    if carb_percentage > 70:
        recommendations.append("Consider reducing carbs and increasing protein and healthy fats")
    if fat_percentage < 20:
        recommendations.append("Add healthy fats to reach 20-35% of total calories")
    
    return recommendations

def save_meal_to_supabase(meal_data, user_id):
    """Save analyzed meal data to Supabase meals table"""
    try:
        # Prepare the meal data for Supabase (simplified schema)
        # Convert decimal values to integers for bigint fields
        meal_record = {
            'user_id': user_id,
            'carbs': int(round(meal_data.get('carbs', 0))),
            'fats': int(round(meal_data.get('fats', 0))),
            'protein': int(round(meal_data.get('protein', 0))),
            'calories': int(round(meal_data.get('calories', 0))),
            'name': meal_data.get('name', 'Unknown Meal')
        }
        
        # Insert into Supabase
        result = supabase.table('meals').insert(meal_record).execute()
        return result.data[0] if result.data else None
        
    except Exception as e:
        raise ValueError(f"Failed to save meal to database: {str(e)}")

def get_daily_nutrition_summary(user_id, date=None):
    """Get daily nutrition summary for a user"""
    if not date:
        date = datetime.now().date()
    
    try:
        # Get meals for the specified date
        start_date = datetime.combine(date, datetime.min.time())
        end_date = datetime.combine(date, datetime.max.time())
        
        result = supabase.table('meals').select('*').eq('user_id', user_id).gte('created_at', start_date.isoformat()).lte('created_at', end_date.isoformat()).execute()
        
        meals = result.data if result.data else []
        
        # Calculate totals
        total_calories = sum(meal.get('calories', 0) for meal in meals)
        total_carbs = sum(meal.get('carbs', 0) for meal in meals)
        total_fats = sum(meal.get('fats', 0) for meal in meals)
        total_protein = sum(meal.get('protein', 0) for meal in meals)
        
        # Calculate macro percentages
        total_macros = total_carbs + total_fats + total_protein
        if total_macros > 0:
            carb_percentage = (total_carbs * 4 / total_calories * 100) if total_calories > 0 else 0
            fat_percentage = (total_fats * 9 / total_calories * 100) if total_calories > 0 else 0
            protein_percentage = (total_protein * 4 / total_calories * 100) if total_calories > 0 else 0
        else:
            carb_percentage = fat_percentage = protein_percentage = 0
        
        return {
            'date': date.isoformat(),
            'total_meals': len(meals),
            'total_calories': total_calories,
            'total_carbs': total_carbs,
            'total_fats': total_fats,
            'total_protein': total_protein,
            'macro_breakdown': {
                'carbs_percentage': round(carb_percentage, 1),
                'fats_percentage': round(fat_percentage, 1),
                'protein_percentage': round(protein_percentage, 1)
            },
            'meals': meals
        }
        
    except Exception as e:
        raise ValueError(f"Failed to get nutrition summary: {str(e)}")

def get_nutrition_trends(user_id, days=7):
    """Get nutrition trends over specified days"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        trends = []
        for i in range(days):
            current_date = start_date + timedelta(days=i)
            daily_summary = get_daily_nutrition_summary(user_id, current_date)
            trends.append(daily_summary)
        
        return trends
        
    except Exception as e:
        raise ValueError(f"Failed to get nutrition trends: {str(e)}")

def analyze_meal_patterns(user_id, days=30):
    """Analyze meal patterns and provide insights over time"""
    try:
        trends = get_nutrition_trends(user_id, days)
        
        if not trends:
            return {
                'insights': [],
                'patterns': {},
                'recommendations': ['Start logging meals to get personalized insights!']
            }
        
        # Calculate averages and trends
        total_days = len(trends)
        avg_calories = sum(day['total_calories'] for day in trends) / total_days
        avg_protein = sum(day['total_protein'] for day in trends) / total_days
        avg_carbs = sum(day['total_carbs'] for day in trends) / total_days
        avg_fats = sum(day['total_fats'] for day in trends) / total_days
        
        # Calculate consistency metrics
        calorie_variance = statistics.variance([day['total_calories'] for day in trends]) if total_days > 1 else 0
        protein_variance = statistics.variance([day['total_protein'] for day in trends]) if total_days > 1 else 0
        
        # Analyze patterns
        insights = []
        patterns = {}
        recommendations = []
        
        # Calorie analysis
        if avg_calories > 2500:
            insights.append(f"High average daily calories ({avg_calories:.0f}) - consider portion control")
            recommendations.append("Focus on nutrient-dense, lower-calorie foods")
        elif avg_calories < 1200:
            insights.append(f"Low average daily calories ({avg_calories:.0f}) - ensure adequate nutrition")
            recommendations.append("Add healthy snacks and increase portion sizes")
        else:
            insights.append(f"Good calorie range ({avg_calories:.0f} daily average)")
        
        # Protein analysis
        protein_percentage = (avg_protein * 4 / avg_calories * 100) if avg_calories > 0 else 0
        if protein_percentage < 15:
            insights.append(f"Low protein intake ({protein_percentage:.1f}% of calories)")
            recommendations.append("Increase protein sources: lean meats, fish, beans, Greek yogurt")
        elif protein_percentage > 35:
            insights.append(f"Very high protein intake ({protein_percentage:.1f}% of calories)")
            recommendations.append("Consider balancing with more vegetables and healthy carbs")
        else:
            insights.append(f"Good protein balance ({protein_percentage:.1f}% of calories)")
        
        # Consistency analysis
        if calorie_variance > 100000:  # High variance
            insights.append("High day-to-day calorie variation - aim for more consistency")
            recommendations.append("Plan meals ahead and maintain regular eating patterns")
        else:
            insights.append("Good consistency in daily calorie intake")
        
        # Meal frequency analysis
        total_meals = sum(day['total_meals'] for day in trends)
        avg_meals_per_day = total_meals / total_days
        
        if avg_meals_per_day < 2:
            insights.append(f"Low meal frequency ({avg_meals_per_day:.1f} meals/day)")
            recommendations.append("Consider adding healthy snacks between meals")
        elif avg_meals_per_day > 5:
            insights.append(f"High meal frequency ({avg_meals_per_day:.1f} meals/day)")
            recommendations.append("Consider consolidating into fewer, larger meals")
        else:
            insights.append(f"Good meal frequency ({avg_meals_per_day:.1f} meals/day)")
        
        # Macro balance analysis
        carb_percentage = (avg_carbs * 4 / avg_calories * 100) if avg_calories > 0 else 0
        fat_percentage = (avg_fats * 9 / avg_calories * 100) if avg_calories > 0 else 0
        
        if carb_percentage > 70:
            insights.append(f"High carb intake ({carb_percentage:.1f}% of calories)")
            recommendations.append("Balance carbs with more protein and healthy fats")
        elif carb_percentage < 30:
            insights.append(f"Low carb intake ({carb_percentage:.1f}% of calories)")
            recommendations.append("Add more whole grains, fruits, and vegetables")
        
        if fat_percentage < 20:
            insights.append(f"Low fat intake ({fat_percentage:.1f}% of calories)")
            recommendations.append("Add healthy fats: nuts, seeds, olive oil, avocado")
        elif fat_percentage > 40:
            insights.append(f"High fat intake ({fat_percentage:.1f}% of calories)")
            recommendations.append("Focus on lean proteins and reduce saturated fats")
        
        # Store patterns
        patterns = {
            'avg_calories': round(avg_calories, 1),
            'avg_protein': round(avg_protein, 1),
            'avg_carbs': round(avg_carbs, 1),
            'avg_fats': round(avg_fats, 1),
            'avg_meals_per_day': round(avg_meals_per_day, 1),
            'calorie_consistency': 'high' if calorie_variance < 50000 else 'medium' if calorie_variance < 100000 else 'low',
            'protein_consistency': 'high' if protein_variance < 100 else 'medium' if protein_variance < 300 else 'low',
            'macro_balance': {
                'protein_pct': round(protein_percentage, 1),
                'carb_pct': round(carb_percentage, 1),
                'fat_pct': round(fat_percentage, 1)
            }
        }
        
        return {
            'insights': insights,
            'patterns': patterns,
            'recommendations': recommendations,
            'analysis_period': f'{days} days'
        }
        
    except Exception as e:
        raise ValueError(f"Failed to analyze meal patterns: {str(e)}")

def get_meal_insights(user_id, days=30):
    """Get comprehensive meal insights and recommendations"""
    try:
        # Get basic trends
        trends = get_nutrition_trends(user_id, days)
        
        # Get pattern analysis
        pattern_analysis = analyze_meal_patterns(user_id, days)
        
        # Calculate weekly patterns
        weekly_patterns = {}
        if len(trends) >= 7:
            recent_week = trends[-7:]
            weekly_patterns = {
                'avg_calories': sum(day['total_calories'] for day in recent_week) / 7,
                'avg_protein': sum(day['total_protein'] for day in recent_week) / 7,
                'avg_carbs': sum(day['total_carbs'] for day in recent_week) / 7,
                'avg_fats': sum(day['total_fats'] for day in recent_week) / 7,
                'total_meals': sum(day['total_meals'] for day in recent_week)
            }
        
        return {
            'trends': trends,
            'pattern_analysis': pattern_analysis,
            'weekly_patterns': weekly_patterns,
            'summary': {
                'total_days_analyzed': len(trends),
                'total_meals_logged': sum(day['total_meals'] for day in trends),
                'avg_daily_calories': round(sum(day['total_calories'] for day in trends) / len(trends), 1) if trends else 0
            }
        }
        
    except Exception as e:
        raise ValueError(f"Failed to get meal insights: {str(e)}")

@app.route('/api/analytics/comprehensive')
def comprehensive_analytics():
    """Get comprehensive training analytics as JSON"""
    if 'user' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava account not connected'}), 400
    
    try:
        # Get time period from query parameter (default to 90 days)
        days = request.args.get('days', 90, type=int)
        valid_periods = [7, 14, 30, 60, 90, 180, 365]
        
        if days not in valid_periods:
            days = 90  # Default fallback
        
        # Create Strava client
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Create analytics engine
        analytics = AdvancedAnalyticsEngine(headers)
        
        # Get comprehensive insights for the specified period
        insights = analytics.get_comprehensive_insights(days=days)
        
        # Convert insights to JSON-serializable format
        analytics_data = {
            'success': True,
            'analysis_period': f'{days} days',
            'training_load': insights.training_load.__dict__ if insights.training_load else {},
            'intensity_zones': insights.intensity_zones.__dict__ if insights.intensity_zones else {},
            'performance_curves': insights.performance_curves.__dict__ if insights.performance_curves else {},
            'volume_trends': insights.volume_trends.__dict__ if insights.volume_trends else {},
            'consistency': insights.consistency.__dict__ if insights.consistency else {},
            'terrain_analysis': insights.terrain_analysis.__dict__ if insights.terrain_analysis else {},
            'cadence_analysis': insights.cadence_analysis.__dict__ if insights.cadence_analysis else {},
            'wellness_score': insights.wellness_score,
            'readiness_score': insights.readiness_score,
            'recommendations': insights.recommendations
        }
        
        return jsonify(analytics_data)
        
    except Exception as e:
        return jsonify({'error': f'Error generating analytics: {str(e)}'}), 500

@app.route('/analytics/wellness', methods=['GET', 'POST'])
def wellness_tracking():
    """Wellness tracking and insights"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        flash('Please connect your Strava account first', 'error')
        return redirect(url_for('home'))
    
    if request.method == 'POST':
        try:
            # Get wellness data from form
            wellness_data = WellnessMetrics(
                mood=int(request.form.get('mood', 3)),
                stress=int(request.form.get('stress', 3)),
                motivation=int(request.form.get('motivation', 3)),
                sleep_quality=int(request.form.get('sleep_quality', 3)),
                soreness=int(request.form.get('soreness', 3)),
                perceived_effort=int(request.form.get('perceived_effort', 5))
            )
            
            # Store in session for this analysis
            session['wellness_data'] = {
                'mood': wellness_data.mood,
                'stress': wellness_data.stress,
                'motivation': wellness_data.motivation,
                'sleep_quality': wellness_data.sleep_quality,
                'soreness': wellness_data.soreness,
                'perceived_effort': wellness_data.perceived_effort
            }
            
            flash('Wellness data recorded!', 'success')
            return redirect(url_for('wellness_insights'))
            
        except Exception as e:
            flash(f'Error recording wellness data: {str(e)}', 'error')
    
    return render_template('wellness_form.html')

@app.route('/analytics/wellness-insights')
def wellness_insights():
    """Display wellness insights with training data"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        flash('Please connect your Strava account first', 'error')
        return redirect(url_for('home'))
    
    try:
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        analytics = AdvancedAnalyticsEngine(headers)
        
        # Get wellness data from session
        wellness_dict = session.get('wellness_data', {})
        wellness_data = WellnessMetrics(
            mood=wellness_dict.get('mood'),
            stress=wellness_dict.get('stress'),
            motivation=wellness_dict.get('motivation'),
            sleep_quality=wellness_dict.get('sleep_quality'),
            soreness=wellness_dict.get('soreness'),
            perceived_effort=wellness_dict.get('perceived_effort')
        ) if wellness_dict else None
        
        # Get comprehensive insights with wellness data
        insights = analytics.get_comprehensive_insights(days=30, wellness_data=wellness_data)
        
        return render_template('wellness_insights.html', insights=insights, wellness_data=wellness_data)
        
    except Exception as e:
        flash(f'Error generating wellness insights: {str(e)}', 'error')
        return redirect(url_for('home'))

@app.route('/api/analytics/summary')
def api_analytics_summary():
    """API endpoint for analytics summary"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        # Get time period from query parameter (default to 90 days)
        days = request.args.get('days', 90, type=int)
        valid_periods = [7, 14, 30, 60, 90, 180, 365]
        
        if days not in valid_periods:
            days = 90  # Default fallback
        
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        analytics = AdvancedAnalyticsEngine(headers)
        
        # Get insights for the specified period
        insights = analytics.get_comprehensive_insights(days=days)
        
        # Convert to JSON-serializable format
        summary = {
            'training_load': {
                'atl': insights.training_load.atl,
                'ctl': insights.training_load.ctl,
                'tsb': insights.training_load.tsb,
                'acwr': insights.training_load.acwr,
                'monotony': insights.training_load.monotony,
                'strain': insights.training_load.strain
            },
            'volume_trends': insights.volume_trends,
            'consistency': insights.consistency_metrics,
            'terrain': insights.terrain_analysis,
            'cadence': insights.cadence_analysis,
            'recommendations': insights.recommendations
        }
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/analytics/performance-trends')
def api_performance_trends():
    """API endpoint for performance trends over time"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get activities for last 3 months
        end_date = datetime.now()
        start_date = end_date - timedelta(days=90)
        start_timestamp = int(start_date.timestamp())
        
        activities_url = 'https://www.strava.com/api/v3/athlete/activities'
        response = requests.get(activities_url, headers=headers, params={
            'after': start_timestamp,
            'per_page': 200
        })
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch activities'}), 500
        
        activities = response.json()
        
        # Process trends
        trends = {
            'pace_trend': [],
            'heart_rate_trend': [],
            'distance_trend': [],
            'elevation_trend': []
        }
        
        for activity in activities:
            if activity.get('type') == 'Run':
                date = activity['start_date_local'][:10]
                
                # Pace trend
                if activity.get('average_speed'):
                    pace_km_per_min = activity['average_speed'] * 3.6 / 60  # km/min
                    trends['pace_trend'].append({
                        'date': date,
                        'value': round(pace_km_per_min, 2)
                    })
                
                # Heart rate trend
                if activity.get('average_heartrate'):
                    trends['heart_rate_trend'].append({
                        'date': date,
                        'value': activity['average_heartrate']
                    })
                
                # Distance trend
                if activity.get('distance'):
                    trends['distance_trend'].append({
                        'date': date,
                        'value': round(activity['distance'] / 1000, 2)  # km
                    })
                
                # Elevation trend
                if activity.get('total_elevation_gain'):
                    trends['elevation_trend'].append({
                        'date': date,
                        'value': activity['total_elevation_gain']
                    })
        
        return jsonify(trends)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/psychology/analysis')
def psychology_analysis():
    """Get performance psychology analysis as JSON"""
    if 'user' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava account not connected'}), 400
    
    try:
        # Get time period from query parameter (default to 30 days)
        days = request.args.get('days', 30, type=int)
        valid_periods = [7, 14, 30, 60, 90, 180]
        
        if days not in valid_periods:
            days = 30  # Default fallback
        
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        psychology_engine = PerformancePsychologyEngine(headers)
        
        # Get comprehensive psychology analysis for the specified period
        analysis = psychology_engine.analyze_performance_psychology(days=days)
        
        # Convert analysis to JSON-serializable format
        psychology_data = {
            'success': True,
            'analysis_period': f'{days} days',
            'performance_events': [event.__dict__ for event in analysis.performance_events] if analysis.performance_events else [],
            'wellness_insights': analysis.wellness_insights,
            'psychological_patterns': analysis.psychological_patterns,
            'recommendations': analysis.recommendations,
            'summary': analysis.summary
        }
        
        return jsonify(psychology_data)
        
    except Exception as e:
        return jsonify({'error': f'Error generating psychology analysis: {str(e)}'}), 500

@app.route('/psychology/wellness-submit', methods=['POST'])
def submit_wellness_psychology():
    """Submit wellness data for psychology analysis"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_id = session['user']['id']
        wellness_data = request.get_json()
        
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        psychology_engine = PerformancePsychologyEngine(headers)
        
        success = psychology_engine.submit_wellness_data(wellness_data)
        
        if success:
            return jsonify({'status': 'success', 'message': 'Wellness data submitted for psychology analysis'})
        else:
            return jsonify({'status': 'error', 'message': 'Failed to submit wellness data'}), 500
            
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/psychology/performance-events')
def api_performance_events():
    """API endpoint for performance events that need psychological context"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        psychology_engine = PerformancePsychologyEngine(headers)
        
        # Get time period from query parameter (default to 7 days)
        days = request.args.get('days', 7, type=int)
        valid_periods = [3, 7, 14, 30, 60]
        
        if days not in valid_periods:
            days = 7  # Default fallback
        
        # Get recent activities and detect performance events
        activities = psychology_engine._get_recent_activities(days=days)
        events = psychology_engine._detect_performance_events(activities)
        
        # Convert events to JSON-serializable format
        events_data = []
        for event in events:
            events_data.append({
                'event_type': event.event_type,
                'activity_id': event.activity_id,
                'activity_name': event.activity_name,
                'timestamp': event.timestamp.isoformat(),
                'severity': event.severity,
                'objective_data': event.objective_data,
                'needs_psychological_context': True
            })
        
        return jsonify({
            'performance_events': events_data,
            'total_events': len(events_data),
            'analysis_period': f'{days} days'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/psychology/split-analysis/<int:activity_id>')
def api_split_analysis(activity_id):
    """API endpoint for detailed split analysis of a specific activity"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        
        # Get detailed activity data
        response = requests.get(
            f'https://www.strava.com/api/v3/activities/{activity_id}',
            headers=headers
        )
        
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch activity'}), 500
        
        activity = response.json()
        
        # Analyze splits
        splits_analysis = {}
        if 'splits_metric' in activity and activity['splits_metric']:
            splits = activity['splits_metric']
            split_times = [split['moving_time'] for split in splits]
            
            # Calculate split degradation
            degradation_analysis = []
            for i in range(2, len(split_times)):
                early_avg = statistics.mean(split_times[:i//2])
                current_split = split_times[i]
                degradation_pct = ((current_split - early_avg) / early_avg) * 100
                
                degradation_analysis.append({
                    'split_number': i + 1,
                    'split_time': current_split,
                    'degradation_pct': degradation_pct,
                    'psychological_impact': 'high' if degradation_pct > 15 else 'moderate' if degradation_pct > 8 else 'low'
                })
            
            splits_analysis = {
                'total_splits': len(splits),
                'average_split_time': statistics.mean(split_times),
                'split_consistency': 1 - (statistics.stdev(split_times) / statistics.mean(split_times)) if len(split_times) > 1 else 1,
                'degradation_analysis': degradation_analysis,
                'significant_degradation': any(d['degradation_pct'] > 15 for d in degradation_analysis)
            }
        
        return jsonify({
            'activity_id': activity_id,
            'activity_name': activity['name'],
            'activity_date': activity['start_date_local'],
            'splits_analysis': splits_analysis,
            'psychological_questions': [
                "How did you feel during the middle portion of this run?",
                "Did you experience any negative thoughts when your pace slowed?",
                "What mental strategies did you use to push through fatigue?",
                "How was your sleep quality the night before this run?",
                "Were you feeling stressed or motivated before starting?"
            ] if splits_analysis.get('significant_degradation') else []
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/psychology/insights')
def api_psychology_insights():
    """API endpoint for performance psychology insights"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        access_token = get_user_strava_token(user_id)
        if not access_token:
            flash('Strava connection expired. Please reconnect your account.', 'error')
            return redirect(url_for('home'))
        
        headers = {'Authorization': f'Bearer {access_token}'}
        psychology_engine = PerformancePsychologyEngine(headers)
        
        # Get time period from query parameter (default to 30 days)
        days = request.args.get('days', 30, type=int)
        valid_periods = [7, 14, 30, 60, 90, 180]
        
        if days not in valid_periods:
            days = 30  # Default fallback
        
        # Get psychology summary for the specified period
        summary = psychology_engine.get_psychology_summary(days=days)
        
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/psychology/submit-wellness', methods=['POST'])
def submit_wellness_data():
    """Submit wellness/feeling data for psychology analysis"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        # Get wellness data from request
        wellness_data = request.get_json()
        
        if not wellness_data:
            return jsonify({'error': 'No wellness data provided'}), 400
        
        # Validate required fields
        required_fields = ['mood', 'stress', 'motivation']
        for field in required_fields:
            if field not in wellness_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate field values (should be 1-10 scale)
        for field in ['mood', 'stress', 'motivation', 'sleep_quality', 'soreness', 'perceived_effort']:
            if field in wellness_data:
                value = wellness_data[field]
                if not isinstance(value, (int, float)) or value < 1 or value > 10:
                    return jsonify({'error': f'{field} must be a number between 1-10'}), 400
        
        access_token = get_user_strava_token(user_id)
        if not access_token:
            return jsonify({'error': 'Strava connection expired'}), 400
        
        headers = {'Authorization': f'Bearer {access_token}'}
        psychology_engine = PerformancePsychologyEngine(headers)
        
        # Submit wellness data
        success = psychology_engine.submit_wellness_data(wellness_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Wellness data submitted successfully',
                'data': wellness_data
            })
        else:
            return jsonify({'error': 'Failed to submit wellness data'}), 500
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/psychology/analyze-feelings', methods=['POST'])
def analyze_feelings():
    """Analyze user's feelings and provide psychological insights"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    user_id = session['user']['id']
    if not strava_token_manager or not strava_token_manager.is_connected(user_id):
        return jsonify({'error': 'Strava not connected'}), 400
    
    try:
        # Get wellness data from request
        wellness_data = request.get_json()
        
        if not wellness_data:
            return jsonify({'error': 'No wellness data provided'}), 400
        
        # Validate required fields
        required_fields = ['mood', 'stress', 'motivation']
        for field in required_fields:
            if field not in wellness_data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Validate field values (should be 1-10 scale)
        for field in ['mood', 'stress', 'motivation', 'sleep_quality', 'soreness', 'perceived_effort']:
            if field in wellness_data:
                value = wellness_data[field]
                if not isinstance(value, (int, float)) or value < 1 or value > 10:
                    return jsonify({'error': f'{field} must be a number between 1-10'}), 400
        
        access_token = get_user_strava_token(user_id)
        if not access_token:
            return jsonify({'error': 'Strava connection expired'}), 400
        
        headers = {'Authorization': f'Bearer {access_token}'}
        psychology_engine = PerformancePsychologyEngine(headers)
        
        # Submit wellness data first
        wellness_success = psychology_engine.submit_wellness_data(wellness_data)
        
        if not wellness_success:
            return jsonify({'error': 'Failed to submit wellness data'}), 500
        
        # Get time period from query parameter (default to 7 days for recent analysis)
        days = request.args.get('days', 7, type=int)
        valid_periods = [7, 14, 30, 60, 90]
        
        if days not in valid_periods:
            days = 7  # Default fallback
        
        # Get comprehensive psychology analysis
        analysis = psychology_engine.analyze_performance_psychology(days=days)
        
        # Create personalized insights based on current feelings
        current_mood = wellness_data.get('mood', 5)
        current_stress = wellness_data.get('stress', 5)
        current_motivation = wellness_data.get('motivation', 5)
        
        # Generate personalized recommendations
        personalized_insights = []
        
        if current_mood < 4:
            personalized_insights.append({
                'type': 'mood_support',
                'title': 'Low Mood Detected',
                'message': 'Your mood is quite low today. Consider light exercise or activities you enjoy.',
                'recommendations': [
                    'Try a gentle walk or easy run',
                    'Focus on activities that bring you joy',
                    'Consider talking to someone about how you feel'
                ]
            })
        elif current_mood > 7:
            personalized_insights.append({
                'type': 'mood_positive',
                'title': 'Great Mood!',
                'message': 'You\'re feeling great today! This is a perfect time for challenging workouts.',
                'recommendations': [
                    'Consider a challenging workout or new activity',
                    'Set new personal records or goals',
                    'Share your positive energy with others'
                ]
            })
        
        if current_stress > 7:
            personalized_insights.append({
                'type': 'stress_management',
                'title': 'High Stress Level',
                'message': 'You\'re experiencing high stress. Exercise can help, but don\'t overdo it.',
                'recommendations': [
                    'Try stress-relieving activities like yoga or meditation',
                    'Avoid high-intensity workouts if feeling overwhelmed',
                    'Focus on recovery and self-care'
                ]
            })
        
        if current_motivation < 4:
            personalized_insights.append({
                'type': 'motivation_boost',
                'title': 'Low Motivation',
                'message': 'Motivation is low today. Start small and build momentum.',
                'recommendations': [
                    'Set small, achievable goals for today',
                    'Try a different type of exercise or activity',
                    'Remember your long-term goals and why you started'
                ]
            })
        
        # Combine with existing analysis
        response = {
            'success': True,
            'submitted_wellness_data': wellness_data,
            'personalized_insights': personalized_insights,
            'performance_analysis': {
                'analysis_period': analysis['analysis_period'],
                'total_activities': len(analysis['activities']),
                'performance_events': len(analysis['performance_events']),
                'psychological_insights': [
                    {
                        'title': insight.title,
                        'description': insight.description,
                        'recommendations': insight.recommendations,
                        'confidence': insight.confidence
                    } for insight in analysis['psychological_insights']
                ]
            },
            'recommendations': analysis['recommendations'],
            'wellness_trends': [
                {
                    'metric': trend.metric,
                    'trend_direction': trend.trend_direction,
                    'trend_strength': trend.trend_strength,
                    'recent_values': trend.recent_values
                } for trend in analysis['wellness_trends']
            ]
        }
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        # For now, return basic user info from the token
        # In a production app, you'd want to store more user data in your own tables
        return jsonify({
            'id': request.current_user_id,
            'message': 'User profile retrieved successfully',
            'token_valid': True,
            'note': 'User details can be enhanced by storing additional profile data in your database'
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

# Nutrition and Meal Tracking Routes
@app.route('/nutrition/log-meal', methods=['GET', 'POST'])
def log_meal():
    """Log a meal using CalAI analysis"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            meal_description = request.form.get('meal_description', '').strip()
            if not meal_description:
                flash('Please provide a meal description', 'error')
                return render_template('log_meal.html')
            
            # Analyze meal with CalorieNinjas
            meal_data = analyze_meal_with_calorie_ninjas(meal_description)
            
            # Save to Supabase
            user_id = session['user']['id']
            saved_meal = save_meal_to_supabase(meal_data, user_id)
            
            if saved_meal:
                # Store analysis data in session to show on success page
                session['last_meal_analysis'] = meal_data
                flash('Meal logged successfully!', 'success')
                return redirect(url_for('meal_analysis_result'))
            else:
                flash('Failed to save meal', 'error')
                
        except Exception as e:
            flash(f'Error logging meal: {str(e)}', 'error')
    
    return render_template('log_meal.html')

@app.route('/nutrition/meal-analysis')
def meal_analysis_result():
    """Display meal analysis results"""
    if 'user' not in session:
        return redirect(url_for('login'))
    
    if 'last_meal_analysis' not in session:
        flash('No meal analysis found', 'error')
        return redirect(url_for('log_meal'))
    
    meal_data = session['last_meal_analysis']
    # Clear the session data after displaying
    session.pop('last_meal_analysis', None)
    
    return render_template('meal_analysis_result.html', meal_data=meal_data)

@app.route('/api/nutrition/dashboard')
def nutrition_dashboard():
    """Get nutrition dashboard data as JSON"""
    if 'user' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        user_id = session['user']['id']
        
        # Get time period from query parameter (default to 7 days)
        days = request.args.get('days', 7, type=int)
        valid_periods = [1, 3, 7, 14, 30]
        
        if days not in valid_periods:
            days = 7  # Default fallback
        
        # Get nutrition trends
        trends = get_nutrition_trends(user_id, days)
        
        # Calculate averages
        if trends:
            avg_calories = sum(day['total_calories'] for day in trends) / len(trends)
            avg_carbs = sum(day['total_carbs'] for day in trends) / len(trends)
            avg_fats = sum(day['total_fats'] for day in trends) / len(trends)
            avg_protein = sum(day['total_protein'] for day in trends) / len(trends)
        else:
            avg_calories = avg_carbs = avg_fats = avg_protein = 0
        
        return jsonify({
            'success': True,
            'analysis_period': f'{days} days',
            'trends': trends,
            'averages': {
                'calories': round(avg_calories, 1),
                'carbs': round(avg_carbs, 1),
                'fats': round(avg_fats, 1),
                'protein': round(avg_protein, 1)
            },
            'summary': {
                'total_days': len(trends),
                'total_meals': sum(day['total_meals'] for day in trends),
                'avg_daily_calories': round(avg_calories, 1)
            }
        })
        
    except Exception as e:
        return jsonify({'error': f'Error loading nutrition dashboard: {str(e)}'}), 500

@app.route('/api/nutrition/insights')
def nutrition_insights():
    """Get comprehensive nutrition insights as JSON"""
    if 'user' not in session:
        return jsonify({'error': 'User not authenticated'}), 401
    
    try:
        user_id = session['user']['id']
        
        # Get time period from query parameter (default to 30 days)
        days = request.args.get('days', 30, type=int)
        valid_periods = [7, 14, 30, 60, 90]
        
        if days not in valid_periods:
            days = 30  # Default fallback
        
        # Get comprehensive meal insights
        insights = get_meal_insights(user_id, days)
        
        return jsonify({
            'success': True,
            'analysis_period': f'{days} days',
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({'error': f'Error loading nutrition insights: {str(e)}'}), 500

# API Endpoints for Nutrition
@app.route('/api/nutrition/log-meal', methods=['POST'])
def api_log_meal():
    """API endpoint to log a meal"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        data = request.get_json()
        meal_description = data.get('meal_description', '').strip()
        
        if not meal_description:
            return jsonify({'error': 'Meal description is required'}), 400
        
        # Analyze meal with CalorieNinjas
        meal_data = analyze_meal_with_calorie_ninjas(meal_description)
        
        # Save to Supabase
        user_id = session['user']['id']
        saved_meal = save_meal_to_supabase(meal_data, user_id)
        
        if saved_meal:
            return jsonify({
                'success': True,
                'meal': saved_meal,
                'analysis': meal_data
            })
        else:
            return jsonify({'error': 'Failed to save meal'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/daily-summary')
def api_daily_nutrition():
    """API endpoint for daily nutrition summary"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_id = session['user']['id']
        date_str = request.args.get('date')
        
        if date_str:
            try:
                date = datetime.fromisoformat(date_str).date()
            except ValueError:
                return jsonify({'error': 'Invalid date format'}), 400
        else:
            date = None
        
        summary = get_daily_nutrition_summary(user_id, date)
        return jsonify(summary)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/trends')
def api_nutrition_trends():
    """API endpoint for nutrition trends"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_id = session['user']['id']
        days = request.args.get('days', 7, type=int)
        valid_periods = [1, 3, 7, 14, 30, 60, 90]
        
        if days not in valid_periods:
            days = 7  # Default fallback
        
        trends = get_nutrition_trends(user_id, days)
        return jsonify({
            'trends': trends,
            'analysis_period': f'{days} days'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/insights')
def api_nutrition_insights():
    """API endpoint for comprehensive nutrition insights"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_id = session['user']['id']
        days = request.args.get('days', 30, type=int)
        valid_periods = [7, 14, 30, 60, 90]
        
        if days not in valid_periods:
            days = 30  # Default fallback
        
        insights = get_meal_insights(user_id, days)
        return jsonify(insights)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/nutrition/patterns')
def api_meal_patterns():
    """API endpoint for meal pattern analysis"""
    if 'user' not in session:
        return jsonify({'error': 'Not authenticated'}), 401
    
    try:
        user_id = session['user']['id']
        days = request.args.get('days', 30, type=int)
        valid_periods = [7, 14, 30, 60, 90]
        
        if days not in valid_periods:
            days = 30  # Default fallback
        
        patterns = analyze_meal_patterns(user_id, days)
        return jsonify(patterns)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# MCP API Endpoints for CalorieNinjas Integration
@app.route('/api/mcp/nutrition/analyze', methods=['POST'])
def mcp_analyze_meal():
    """
    MCP Endpoint: Analyze meal description using CalorieNinjas API
    Returns comprehensive nutritional analysis without saving to database
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        meal_description = data.get('meal_description', '').strip()
        if not meal_description:
            return jsonify({'error': 'meal_description is required'}), 400
        
        # Analyze meal with CalorieNinjas
        meal_analysis = analyze_meal_with_calorie_ninjas(meal_description)
        
        # Return analysis without saving to database
        return jsonify({
            'success': True,
            'meal_description': meal_description,
            'analysis': {
                'name': meal_analysis['name'],
                'calories': meal_analysis['calories'],
                'carbs': meal_analysis['carbs'],
                'fats': meal_analysis['fats'],
                'protein': meal_analysis['protein'],
                'sodium': meal_analysis['sodium'],
                'fiber': meal_analysis['fiber'],
                'sugar': meal_analysis['sugar'],
                'ingredients': meal_analysis['ingredients'],
                'health_recommendations': meal_analysis['health_recommendations']
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/nutrition/analyze-and-save', methods=['POST'])
def mcp_analyze_and_save_meal():
    """
    MCP Endpoint: Analyze meal and save to user's nutrition log
    Requires user authentication via session or API token
    """
    if 'user' not in session:
        return jsonify({'error': 'User authentication required'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        meal_description = data.get('meal_description', '').strip()
        if not meal_description:
            return jsonify({'error': 'meal_description is required'}), 400
        
        # Analyze meal with CalorieNinjas
        meal_analysis = analyze_meal_with_calorie_ninjas(meal_description)
        
        # Save to user's nutrition log
        user_id = session['user']['id']
        saved_meal = save_meal_to_supabase(meal_analysis, user_id)
        
        if saved_meal:
            return jsonify({
                'success': True,
                'meal_description': meal_description,
                'saved_meal_id': saved_meal['id'],
                'analysis': {
                    'name': meal_analysis['name'],
                    'calories': meal_analysis['calories'],
                    'carbs': meal_analysis['carbs'],
                    'fats': meal_analysis['fats'],
                    'protein': meal_analysis['protein'],
                    'sodium': meal_analysis['sodium'],
                    'fiber': meal_analysis['fiber'],
                    'sugar': meal_analysis['sugar'],
                    'ingredients': meal_analysis['ingredients'],
                    'health_recommendations': meal_analysis['health_recommendations']
                }
            })
        else:
            return jsonify({'error': 'Failed to save meal to database'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/nutrition/batch-analyze', methods=['POST'])
def mcp_batch_analyze_meals():
    """
    MCP Endpoint: Analyze multiple meal descriptions in batch
    Returns analysis for all meals without saving to database
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        meal_descriptions = data.get('meal_descriptions', [])
        if not meal_descriptions or not isinstance(meal_descriptions, list):
            return jsonify({'error': 'meal_descriptions array is required'}), 400
        
        if len(meal_descriptions) > 10:
            return jsonify({'error': 'Maximum 10 meals per batch request'}), 400
        
        results = []
        for i, meal_description in enumerate(meal_descriptions):
            try:
                meal_analysis = analyze_meal_with_calorie_ninjas(meal_description.strip())
                results.append({
                    'index': i,
                    'meal_description': meal_description,
                    'success': True,
                    'analysis': {
                        'name': meal_analysis['name'],
                        'calories': meal_analysis['calories'],
                        'carbs': meal_analysis['carbs'],
                        'fats': meal_analysis['fats'],
                        'protein': meal_analysis['protein'],
                        'sodium': meal_analysis['sodium'],
                        'fiber': meal_analysis['fiber'],
                        'sugar': meal_analysis['sugar'],
                        'ingredients': meal_analysis['ingredients'],
                        'health_recommendations': meal_analysis['health_recommendations']
                    }
                })
            except Exception as e:
                results.append({
                    'index': i,
                    'meal_description': meal_description,
                    'success': False,
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'total_meals': len(meal_descriptions),
            'successful_analyses': len([r for r in results if r['success']]),
            'failed_analyses': len([r for r in results if not r['success']]),
            'results': results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mcp/nutrition/health-recommendations', methods=['POST'])
def mcp_get_health_recommendations():
    """
    MCP Endpoint: Get health recommendations for nutritional data
    Accepts nutritional values and returns personalized recommendations
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'JSON data required'}), 400
        
        # Extract nutritional values
        calories = data.get('calories', 0)
        carbs = data.get('carbs', 0)
        fats = data.get('fats', 0)
        protein = data.get('protein', 0)
        sodium = data.get('sodium', 0)
        fiber = data.get('fiber', 0)
        sugar = data.get('sugar', 0)
        
        # Generate health recommendations
        recommendations = generate_health_recommendations(
            calories, carbs, fats, protein, sodium, fiber, sugar
        )
        
        # Calculate macro percentages
        protein_percentage = (protein * 4 / calories * 100) if calories > 0 else 0
        carb_percentage = (carbs * 4 / calories * 100) if calories > 0 else 0
        fat_percentage = (fats * 9 / calories * 100) if calories > 0 else 0
        
        return jsonify({
            'success': True,
            'nutritional_data': {
                'calories': calories,
                'carbs': carbs,
                'fats': fats,
                'protein': protein,
                'sodium': sodium,
                'fiber': fiber,
                'sugar': sugar
            },
            'macro_breakdown': {
                'protein_percentage': round(protein_percentage, 1),
                'carb_percentage': round(carb_percentage, 1),
                'fat_percentage': round(fat_percentage, 1)
            },
            'health_recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================================================
# API STATUS ENDPOINTS
# ============================================================================

@app.route('/api/strava/status', methods=['GET'])
@require_api_auth
def api_strava_status():
    """
    Get Strava connection status across all users.
    Useful for monitoring and debugging.
    """
    if not strava_token_manager:
        return jsonify({'error': 'Strava token manager not initialized'}), 500
    
    try:
        active_users = strava_token_manager.get_all_active_users()
        
        return jsonify({
            'success': True,
            'total_connected_users': len(active_users),
            'users': [
                {
                    'user_id': user['user_id'],
                    'athlete_id': user['athlete_id'],
                    'last_activity_check': user.get('last_activity_check'),
                    'last_activity_id': user.get('last_activity_id')
                } for user in active_users
            ]
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get status: {str(e)}'}), 500

@app.route('/api/user/strava/notifications', methods=['GET'])
@require_auth
def get_user_notifications():
    """
    Get activity notifications for the current user.
    """
    if not strava_activity_monitor:
        return jsonify({'error': 'Strava activity monitor not initialized'}), 500
    
    user_id = session['user']['id']
    
    try:
        # Get all notifications for this user (both sent and unsent)
        all_notifications = strava_activity_monitor.get_pending_notifications(user_id)
        
        # Also get sent notifications from the last 7 days
        # (you might want to modify get_pending_notifications to include sent ones)
        
        return jsonify({
            'success': True,
            'notifications': [
                {
                    'id': n['id'],
                    'activity_id': n['strava_activity_id'],
                    'activity_type': n['activity_type'],
                    'activity_name': n['activity_name'],
                    'notification_sent': n['notification_sent'],
                    'created_at': n['created_at']
                } for n in all_notifications
            ]
        })
        
    except Exception as e:
        return jsonify({'error': f'Failed to get notifications: {str(e)}'}), 500

# ============================================================================

# ============================================================================





        return redirect(url_for('home'))

if __name__ == '__main__':
    # Debug: Check if CalorieNinjas API key is loaded
    print(f"DEBUG: CalorieNinjas API Key loaded: {'Yes' if CALORIE_NINJAS_API_KEY else 'No'}")
    if CALORIE_NINJAS_API_KEY:
        print(f"DEBUG: API Key starts with: {CALORIE_NINJAS_API_KEY[:10]}...")
    else:
        print("WARNING: CalorieNinjas API key not found in environment variables")
    
    print("🚀 Starting Jolt with webhook-based Strava integration")
    print("✅ No more polling - webhooks provide real-time notifications!")
    
    # Run the Flask app
    app.run(debug=True, port=5000)
