"""
Production WSGI entry point for Jolt app with Strava scheduler
"""

import os
from app import app, strava_scheduler

# Initialize scheduler for production
if strava_scheduler and os.getenv('ENABLE_STRAVA_SCHEDULER', 'true').lower() == 'true':
    print("Initializing Strava scheduler for production...")
    if strava_scheduler.start_monitoring():
        print("✅ Strava scheduler started successfully")
    else:
        print("❌ Failed to start Strava scheduler")

if __name__ == "__main__":
    app.run()
