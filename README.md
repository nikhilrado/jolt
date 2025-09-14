# Jolt - Strava Integration App

## Setup Instructions

### Prerequisites
- Python 3.8 or higher
- A Supabase account and project
- A Strava API application

### Installation

1. **Clone or download this project**

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   - Copy `.env.example` to `.env`
   - Fill in your configuration values:

   ```bash
   cp .env.example .env
   ```

   Edit `.env` with your actual values:
   ```
   FLASK_SECRET_KEY=your-random-secret-key
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your-supabase-anon-key
   STRAVA_CLIENT_ID=your-strava-client-id
   STRAVA_CLIENT_SECRET=your-strava-client-secret
   ```

### Configuration Setup

#### Supabase Setup
1. Create a new project at [supabase.com](https://supabase.com)
2. Go to Settings > API to find your URL and anon key
3. Go to Authentication > Settings and disable "Enable email confirmations" for easier signup
4. The app uses Supabase Auth for user management

#### Strava API Setup
1. Create a Strava API application at [developers.strava.com](https://developers.strava.com)
2. Set the authorization callback domain to: `localhost`
3. Note your Client ID and Client Secret

### Running the Application

```bash
python app.py
```

The app will be available at `http://localhost:5000`

### Features

- **User Authentication**: Sign up and sign in with Supabase
- **Strava Integration**: Connect your Strava account via OAuth
- **Activity Viewing**: View your recent Strava activities
- **Responsive Design**: Works on desktop and mobile devices

### Usage

1. Sign up for a new account or sign in
2. Connect your Strava account from the home page
3. View your activities and running data

### Project Structure

```
jolt/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── templates/            # HTML templates
│   ├── base.html         # Base template
│   ├── login.html        # Login page
│   ├── signup.html       # Sign up page
│   ├── home.html         # Home page
│   └── activities.html   # Activities page
└── static/               # Static files
    └── css/
        └── style.css     # Custom CSS styles
```

### API Endpoints

- `/` - Landing page (redirects to login or home)
- `/login` - User login
- `/signup` - User registration
- `/logout` - User logout
- `/home` - Home dashboard
- `/strava/connect` - Initiate Strava OAuth
- `/strava/callback` - Strava OAuth callback
- `/strava/activities` - View Strava activities
- `/strava/disconnect` - Disconnect Strava account

### Troubleshooting

- Make sure all environment variables are set correctly
- Check that your Supabase project is active
- Verify your Strava API credentials
- Ensure the Strava redirect URI matches your configuration

### Contributing

Feel free to submit issues and enhancement requests!
