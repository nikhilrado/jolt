"""
Production WSGI entry point for Jolt app with webhook-based Strava integration
"""

import os
from app import app

print("✅ Jolt app initialized with webhook-based Strava integration")
print("🎯 Real-time activity processing - no polling needed!")

if __name__ == "__main__":
    app.run()
