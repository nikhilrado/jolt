#!/usr/bin/env python3
"""
Sleep Analysis Engine
Comprehensive sleep tracking, sleep debt monitoring, and circadian rhythm analysis
"""

import statistics
from datetime import datetime, timedelta, time
from typing import Dict, List, Optional, Tuple
import math

class SleepEngine:
    """Advanced sleep analysis and monitoring engine"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        
        # Sleep recommendations based on age groups
        self.sleep_recommendations = {
            'adult': {'min': 7, 'optimal': 8, 'max': 9},
            'young_adult': {'min': 7, 'optimal': 8.5, 'max': 9.5},
            'teen': {'min': 8, 'optimal': 9, 'max': 10},
            'child': {'min': 9, 'optimal': 10, 'max': 11}
        }
        
        # Circadian rhythm analysis parameters
        self.circadian_parameters = {
            'optimal_bedtime_range': (22, 23),  # 10-11 PM
            'optimal_wake_range': (6, 8),       # 6-8 AM
            'consistency_threshold': 1.0,       # hours of variation
            'social_jetlag_threshold': 2.0      # hours difference between weekdays/weekends
        }
    
    def log_sleep(self, user_id: str, sleep_data: Dict) -> Dict:
        """Log sleep data for a user"""
        try:
            # Validate required fields
            required_fields = ['sleep_duration', 'tiredness', 'time_going_to_bed', 'time_waking_up']
            for field in required_fields:
                if field not in sleep_data:
                    return {'success': False, 'error': f'Missing required field: {field}'}
            
            # Prepare data for insertion
            sleep_record = {
                'user_id': user_id,
                'sleep_duration': float(sleep_data['sleep_duration']),
                'tiredness': int(sleep_data['tiredness']),
                'time_going_to_bed': sleep_data['time_going_to_bed'],
                'time_waking_up': sleep_data['time_waking_up'],
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Insert into Supabase
            result = self.supabase.table('sleep').insert(sleep_record).execute()
            
            if result.data:
                return {
                    'success': True,
                    'sleep_record': result.data[0],
                    'message': 'Sleep data logged successfully'
                }
            else:
                return {'success': False, 'error': 'Failed to insert sleep data'}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_sleep_data(self, user_id: str, days: int = 30) -> List[Dict]:
        """Get sleep data for a user over specified period"""
        try:
            # Calculate date range
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            
            # Query sleep data
            result = self.supabase.table('sleep').select('*').eq(
                'user_id', user_id
            ).gte('created_at', start_date.isoformat()).order(
                'created_at', desc=True
            ).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            print(f"Error fetching sleep data: {e}")
            return []
    
    def calculate_sleep_debt(self, user_id: str, days: int = 14) -> Dict:
        """Calculate sleep debt over specified period"""
        try:
            sleep_data = self.get_sleep_data(user_id, days)
            
            if not sleep_data:
                return {
                    'total_debt': 0,
                    'average_debt_per_night': 0,
                    'debt_trend': 'insufficient_data',
                    'recommendation': 'Start logging sleep data to track sleep debt'
                }
            
            # Calculate sleep debt (assuming 8 hours optimal sleep)
            optimal_sleep = 8.0
            total_debt = 0
            sleep_durations = []
            
            for record in sleep_data:
                actual_sleep = record['sleep_duration']
                sleep_durations.append(actual_sleep)
                debt = max(0, optimal_sleep - actual_sleep)
                total_debt += debt
            
            average_debt_per_night = total_debt / len(sleep_data) if sleep_durations else 0
            
            # Determine debt trend
            if len(sleep_durations) >= 7:
                recent_avg = statistics.mean(sleep_durations[-7:])
                older_avg = statistics.mean(sleep_durations[:-7]) if len(sleep_durations) > 7 else recent_avg
                
                if recent_avg > older_avg + 0.5:
                    debt_trend = 'improving'
                elif recent_avg < older_avg - 0.5:
                    debt_trend = 'worsening'
                else:
                    debt_trend = 'stable'
            else:
                debt_trend = 'insufficient_data'
            
            # Generate recommendation
            if total_debt > 20:
                recommendation = "High sleep debt detected. Consider taking a recovery nap and going to bed 1-2 hours earlier."
            elif total_debt > 10:
                recommendation = "Moderate sleep debt. Try to get 30-60 minutes extra sleep per night."
            elif total_debt > 5:
                recommendation = "Minor sleep debt. Maintain consistent sleep schedule."
            else:
                recommendation = "Great sleep habits! Keep maintaining your current routine."
            
            return {
                'total_debt': round(total_debt, 1),
                'average_debt_per_night': round(average_debt_per_night, 1),
                'debt_trend': debt_trend,
                'recommendation': recommendation,
                'total_nights_analyzed': len(sleep_data),
                'average_sleep_duration': round(statistics.mean(sleep_durations), 1) if sleep_durations else 0
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def analyze_circadian_rhythm(self, user_id: str, days: int = 14) -> Dict:
        """Analyze circadian rhythm patterns and disruptions"""
        try:
            sleep_data = self.get_sleep_data(user_id, days)
            
            if len(sleep_data) < 3:
                return {
                    'rhythm_quality': 'insufficient_data',
                    'consistency_score': 0,
                    'social_jetlag': 0,
                    'recommendations': ['Log at least 3 nights of sleep data for circadian analysis']
                }
            
            # Extract bedtimes and wake times
            bedtimes = []
            wake_times = []
            
            for record in sleep_data:
                bedtime = datetime.fromisoformat(record['time_going_to_bed'].replace('Z', '+00:00'))
                wake_time = datetime.fromisoformat(record['time_waking_up'].replace('Z', '+00:00'))
                
                bedtimes.append(bedtime.time())
                wake_times.append(wake_time.time())
            
            # Calculate consistency metrics
            bedtime_consistency = self._calculate_time_consistency(bedtimes)
            wake_time_consistency = self._calculate_time_consistency(wake_times)
            
            # Calculate social jetlag (difference between weekday and weekend patterns)
            social_jetlag = self._calculate_social_jetlag(sleep_data)
            
            # Determine rhythm quality
            consistency_score = (bedtime_consistency + wake_time_consistency) / 2
            
            if consistency_score > 0.8:
                rhythm_quality = 'excellent'
            elif consistency_score > 0.6:
                rhythm_quality = 'good'
            elif consistency_score > 0.4:
                rhythm_quality = 'fair'
            else:
                rhythm_quality = 'poor'
            
            # Generate recommendations
            recommendations = self._generate_circadian_recommendations(
                rhythm_quality, consistency_score, social_jetlag, bedtimes, wake_times
            )
            
            return {
                'rhythm_quality': rhythm_quality,
                'consistency_score': round(consistency_score, 2),
                'bedtime_consistency': round(bedtime_consistency, 2),
                'wake_time_consistency': round(wake_time_consistency, 2),
                'social_jetlag': round(social_jetlag, 1),
                'average_bedtime': self._format_time(statistics.mean([t.hour + t.minute/60 for t in bedtimes])),
                'average_wake_time': self._format_time(statistics.mean([t.hour + t.minute/60 for t in wake_times])),
                'recommendations': recommendations
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_time_consistency(self, times: List[time]) -> float:
        """Calculate consistency score for a list of times (0-1 scale)"""
        if len(times) < 2:
            return 1.0
        
        # Convert times to hours since midnight
        hours = [t.hour + t.minute/60 for t in times]
        
        # Calculate standard deviation
        mean_hour = statistics.mean(hours)
        variance = statistics.variance(hours) if len(hours) > 1 else 0
        std_dev = math.sqrt(variance)
        
        # Convert to consistency score (lower std dev = higher consistency)
        # 1 hour std dev = 0.5 score, 2 hours = 0.25, etc.
        consistency = max(0, 1 - (std_dev / 2))
        return consistency
    
    def _calculate_social_jetlag(self, sleep_data: List[Dict]) -> float:
        """Calculate social jetlag (difference between weekday and weekend sleep patterns)"""
        if len(sleep_data) < 7:
            return 0.0
        
        weekday_bedtimes = []
        weekend_bedtimes = []
        
        for record in sleep_data:
            bedtime = datetime.fromisoformat(record['time_going_to_bed'].replace('Z', '+00:00'))
            weekday = bedtime.weekday() < 5  # Monday = 0, Friday = 4
            
            bedtime_hour = bedtime.hour + bedtime.minute/60
            
            if weekday:
                weekday_bedtimes.append(bedtime_hour)
            else:
                weekend_bedtimes.append(bedtime_hour)
        
        if not weekday_bedtimes or not weekend_bedtimes:
            return 0.0
        
        weekday_avg = statistics.mean(weekday_bedtimes)
        weekend_avg = statistics.mean(weekend_bedtimes)
        
        return abs(weekend_avg - weekday_avg)
    
    def _format_time(self, hour_float: float) -> str:
        """Convert hour float to readable time string"""
        hours = int(hour_float)
        minutes = int((hour_float - hours) * 60)
        return f"{hours:02d}:{minutes:02d}"
    
    def _generate_circadian_recommendations(self, rhythm_quality: str, consistency_score: float, 
                                          social_jetlag: float, bedtimes: List[time], 
                                          wake_times: List[time]) -> List[str]:
        """Generate personalized circadian rhythm recommendations"""
        recommendations = []
        
        if rhythm_quality == 'poor':
            recommendations.append("Your sleep schedule is very inconsistent. Try to go to bed and wake up at the same time every day, even on weekends.")
        
        if consistency_score < 0.6:
            recommendations.append("Focus on maintaining a consistent bedtime within a 30-minute window.")
        
        if social_jetlag > 2.0:
            recommendations.append("You have significant social jetlag. Try to keep your weekend schedule within 1 hour of your weekday schedule.")
        
        # Check for late bedtimes
        avg_bedtime_hour = statistics.mean([t.hour + t.minute/60 for t in bedtimes])
        if avg_bedtime_hour > 23.5:  # After 11:30 PM
            recommendations.append("Consider going to bed earlier. Late bedtimes can disrupt your circadian rhythm.")
        
        # Check for early wake times
        avg_wake_hour = statistics.mean([t.hour + t.minute/60 for t in wake_times])
        if avg_wake_hour < 6.0:  # Before 6 AM
            recommendations.append("Very early wake times may indicate insufficient sleep. Consider going to bed earlier.")
        
        if not recommendations:
            recommendations.append("Your circadian rhythm looks healthy! Keep maintaining your consistent sleep schedule.")
        
        return recommendations
    
    def get_sleep_insights(self, user_id: str, days: int = 30) -> Dict:
        """Get comprehensive sleep insights and recommendations"""
        try:
            sleep_data = self.get_sleep_data(user_id, days)
            sleep_debt = self.calculate_sleep_debt(user_id, days)
            circadian_analysis = self.analyze_circadian_rhythm(user_id, days)
            
            if not sleep_data:
                return {
                    'status': 'no_data',
                    'message': 'No sleep data available. Start logging your sleep to get insights.',
                    'recommendations': ['Log your first sleep session to begin tracking']
                }
            
            # Calculate additional metrics
            sleep_durations = [record['sleep_duration'] for record in sleep_data]
            tiredness_scores = [record['tiredness'] for record in sleep_data]
            
            avg_sleep_duration = statistics.mean(sleep_durations)
            avg_tiredness = statistics.mean(tiredness_scores)
            
            # Determine overall sleep quality
            if avg_sleep_duration >= 7.5 and avg_tiredness <= 3 and sleep_debt.get('total_debt', 0) < 5:
                overall_quality = 'excellent'
            elif avg_sleep_duration >= 7 and avg_tiredness <= 4 and sleep_debt.get('total_debt', 0) < 10:
                overall_quality = 'good'
            elif avg_sleep_duration >= 6.5 and avg_tiredness <= 5:
                overall_quality = 'fair'
            else:
                overall_quality = 'poor'
            
            # Generate personalized recommendations
            recommendations = self._generate_sleep_recommendations(
                overall_quality, avg_sleep_duration, avg_tiredness, sleep_debt, circadian_analysis
            )
            
            return {
                'status': 'success',
                'analysis_period_days': days,
                'total_sleep_sessions': len(sleep_data),
                'overall_sleep_quality': overall_quality,
                'average_sleep_duration': round(avg_sleep_duration, 1),
                'average_tiredness_score': round(avg_tiredness, 1),
                'sleep_debt_analysis': sleep_debt,
                'circadian_rhythm_analysis': circadian_analysis,
                'recommendations': recommendations,
                'trends': self._analyze_sleep_trends(sleep_data)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _generate_sleep_recommendations(self, quality: str, avg_duration: float, 
                                      avg_tiredness: float, sleep_debt: Dict, 
                                      circadian: Dict) -> List[str]:
        """Generate comprehensive sleep recommendations"""
        recommendations = []
        
        # Duration-based recommendations
        if avg_duration < 7:
            recommendations.append("You're getting less than 7 hours of sleep. Aim for 7-9 hours for optimal health.")
        elif avg_duration > 9:
            recommendations.append("You're sleeping more than 9 hours regularly. This might indicate underlying health issues.")
        
        # Tiredness-based recommendations
        if avg_tiredness > 6:
            recommendations.append("High tiredness scores suggest poor sleep quality. Consider sleep hygiene improvements.")
        elif avg_tiredness < 3:
            recommendations.append("Great energy levels! Your sleep quality appears to be excellent.")
        
        # Add sleep debt recommendations
        if sleep_debt.get('total_debt', 0) > 10:
            recommendations.append(sleep_debt.get('recommendation', ''))
        
        # Add circadian recommendations
        if circadian.get('rhythm_quality') == 'poor':
            recommendations.extend(circadian.get('recommendations', []))
        
        # General recommendations
        if quality == 'poor':
            recommendations.extend([
                "Consider establishing a relaxing bedtime routine",
                "Avoid screens 1 hour before bed",
                "Keep your bedroom cool, dark, and quiet",
                "Limit caffeine after 2 PM"
            ])
        
        return recommendations[:5]  # Limit to top 5 recommendations
    
    def _analyze_sleep_trends(self, sleep_data: List[Dict]) -> Dict:
        """Analyze sleep trends over time"""
        if len(sleep_data) < 7:
            return {'trend': 'insufficient_data'}
        
        # Analyze last 7 days vs previous period
        recent_data = sleep_data[:7]
        older_data = sleep_data[7:14] if len(sleep_data) > 7 else []
        
        recent_avg_duration = statistics.mean([r['sleep_duration'] for r in recent_data])
        recent_avg_tiredness = statistics.mean([r['tiredness'] for r in recent_data])
        
        if older_data:
            older_avg_duration = statistics.mean([r['sleep_duration'] for r in older_data])
            older_avg_tiredness = statistics.mean([r['tiredness'] for r in older_data])
            
            duration_trend = 'improving' if recent_avg_duration > older_avg_duration + 0.3 else \
                           'declining' if recent_avg_duration < older_avg_duration - 0.3 else 'stable'
            
            tiredness_trend = 'improving' if recent_avg_tiredness < older_avg_tiredness - 0.5 else \
                            'declining' if recent_avg_tiredness > older_avg_tiredness + 0.5 else 'stable'
        else:
            duration_trend = 'stable'
            tiredness_trend = 'stable'
        
        return {
            'duration_trend': duration_trend,
            'tiredness_trend': tiredness_trend,
            'recent_avg_duration': round(recent_avg_duration, 1),
            'recent_avg_tiredness': round(recent_avg_tiredness, 1)
        }

