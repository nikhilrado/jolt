"""
Flask-based Strava Activity Scheduler
Handles periodic checking for new Strava activities using Flask-APScheduler
"""

from flask_apscheduler import APScheduler
from datetime import datetime
import os
import logging

class StravaActivityScheduler:
    def __init__(self, app, strava_activity_monitor):
        self.app = app
        self.strava_activity_monitor = strava_activity_monitor
        self.scheduler = APScheduler()
        
        # Set up logging first
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Configure scheduler
        self._configure_scheduler()
        
        # Initialize scheduler with app
        self.scheduler.init_app(app)
    
    def _configure_scheduler(self):
        """Configure the scheduler settings"""
        
        # Enable scheduler in production
        enable_scheduler = os.getenv('ENABLE_STRAVA_SCHEDULER', 'true').lower() == 'true'
        
        self.app.config.update({
            'SCHEDULER_API_ENABLED': True,  # Enable API endpoints for scheduler management
            'SCHEDULER_TIMEZONE': 'UTC',    # Use UTC for consistency
            'SCHEDULER_JOB_DEFAULTS': {
                'coalesce': True,           # Combine multiple pending executions
                'max_instances': 1,         # Only one instance of each job at a time
                'misfire_grace_time': 300   # 5 minutes grace period for missed jobs
            }
        })
        
        # Only start if enabled (useful for development)
        if enable_scheduler:
            self.scheduler.start()
            self.logger.info("Strava Activity Scheduler started")
        else:
            self.logger.info("Strava Activity Scheduler disabled via environment variable")
    
    def start_monitoring(self):
        """Start the scheduled monitoring jobs"""
        if not self.strava_activity_monitor:
            self.logger.error("Strava activity monitor not available")
            return False
        
        try:
            # Check for new activities every 15 minutes
            self.scheduler.add_job(
                id='check_strava_activities',
                func=self._check_activities_job,
                trigger='interval',
                minutes=15,
                name='Check Strava Activities',
                replace_existing=True
            )
            
            # Send notifications every 5 minutes (offset from activity check)
            self.scheduler.add_job(
                id='send_strava_notifications',
                func=self._send_notifications_job,
                trigger='interval',
                minutes=5,
                name='Send Strava Notifications',
                replace_existing=True
            )
            
            # Health check every hour
            self.scheduler.add_job(
                id='strava_health_check',
                func=self._health_check_job,
                trigger='interval',
                hours=1,
                name='Strava Health Check',
                replace_existing=True
            )
            
            self.logger.info("Scheduled jobs added successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring: {e}")
            return False
    
    def _check_activities_job(self):
        """Job function to check for new activities"""
        try:
            with self.app.app_context():
                self.logger.info("Starting scheduled activity check...")
                
                notifications = self.strava_activity_monitor.check_all_users()
                
                self.logger.info(f"Activity check completed. Found {len(notifications)} new activities")
                
                for notification in notifications:
                    self.logger.info(
                        f"New activity: {notification['activity_type']} - "
                        f"{notification['activity_name']} (User: {notification['user_id']})"
                    )
                
                return {
                    'success': True,
                    'new_activities': len(notifications),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Activity check job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _send_notifications_job(self):
        """Job function to send pending notifications"""
        try:
            with self.app.app_context():
                self.logger.info("Starting notification sending...")
                
                pending_notifications = self.strava_activity_monitor.get_pending_notifications()
                
                sent_count = 0
                for notification in pending_notifications:
                    # Here you can implement actual notification sending
                    # For now, we'll just mark them as sent
                    if self.strava_activity_monitor.mark_notification_sent(notification['id']):
                        sent_count += 1
                        self.logger.info(f"Notification sent for activity {notification['strava_activity_id']}")
                
                self.logger.info(f"Notification job completed. Sent {sent_count} notifications")
                
                return {
                    'success': True,
                    'sent_count': sent_count,
                    'total_pending': len(pending_notifications),
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Notification sending job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def _health_check_job(self):
        """Job function for health checks"""
        try:
            with self.app.app_context():
                # Get connection status
                if hasattr(self.strava_activity_monitor, 'token_manager'):
                    active_users = self.strava_activity_monitor.token_manager.get_all_active_users()
                    user_count = len(active_users)
                else:
                    user_count = 0
                
                self.logger.info(f"Health check: {user_count} users with active Strava connections")
                
                return {
                    'success': True,
                    'active_users': user_count,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            self.logger.error(f"Health check job failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def stop_monitoring(self):
        """Stop all scheduled jobs"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown()
                self.logger.info("Strava scheduler stopped")
                return True
        except Exception as e:
            self.logger.error(f"Failed to stop scheduler: {e}")
            return False
    
    def get_job_status(self):
        """Get status of all scheduled jobs"""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        return jobs
    
    def trigger_job_manually(self, job_id):
        """Manually trigger a specific job"""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.now())
                self.logger.info(f"Manually triggered job: {job_id}")
                return True
            else:
                self.logger.error(f"Job not found: {job_id}")
                return False
        except Exception as e:
            self.logger.error(f"Failed to trigger job {job_id}: {e}")
            return False
