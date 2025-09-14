"""
Advanced Training Analytics Engine for Jolt
Implements sports science metrics for training analysis and recommendations
"""

import requests
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import math


@dataclass
class TrainingLoad:
    """Training load metrics"""
    atl: float  # Acute Training Load (7-day)
    ctl: float  # Chronic Training Load (42-day)
    tsb: float  # Training Stress Balance
    acwr: float  # Acute:Chronic Workload Ratio
    monotony: float
    strain: float


@dataclass
class IntensityZones:
    """Heart rate or pace zones"""
    zone_1_time: float  # Easy
    zone_2_time: float  # Aerobic
    zone_3_time: float  # Tempo
    zone_4_time: float  # Threshold
    zone_5_time: float  # VO2 Max
    total_time: float


@dataclass
class PerformanceCurve:
    """Best pace/power at different durations"""
    one_min: float
    five_min: float
    ten_min: float
    twenty_min: float
    sixty_min: float


@dataclass
class WellnessMetrics:
    """Subjective wellness data"""
    mood: Optional[int] = None  # 1-5
    stress: Optional[int] = None  # 1-5
    motivation: Optional[int] = None  # 1-5
    sleep_quality: Optional[int] = None  # 1-5
    soreness: Optional[int] = None  # 1-5
    perceived_effort: Optional[int] = None  # 1-10


@dataclass
class TrainingInsights:
    """Comprehensive training insights"""
    training_load: TrainingLoad
    intensity_distribution: IntensityZones
    performance_curve: PerformanceCurve
    volume_trends: Dict
    consistency_metrics: Dict
    terrain_analysis: Dict
    cadence_analysis: Dict
    wellness_score: Optional[float] = None
    readiness_score: Optional[float] = None
    recommendations: List[str] = None


class AdvancedAnalyticsEngine:
    """
    Advanced analytics engine for comprehensive training analysis
    """
    
    def __init__(self, headers):
        self.headers = headers
        self.user_zones = None
        self._load_user_zones()
    
    def _load_user_zones(self):
        """Load user's heart rate zones from Strava"""
        try:
            print("🔍 Fetching athlete zones from Strava API...")
            response = requests.get(
                'https://www.strava.com/api/v3/athlete/zones',
                headers=self.headers
            )
            if response.status_code == 200:
                self.user_zones = response.json()
                print(f"✅ Loaded user zones: {self.user_zones}")
            else:
                print(f"⚠️ Could not load zones (status {response.status_code}): {response.text}")
                self.user_zones = None
        except Exception as e:
            print(f"❌ Could not load user zones: {e}")
            self.user_zones = None
    
    def calculate_training_load(self, days: int = 90) -> TrainingLoad:
        """
        Calculate ATL, CTL, TSB, ACWR, Monotony, and Strain
        """
        print(f"📊 Calculating training load for last {days} days...")
        
        # Get activities for the specified period
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())
        
        print(f"🔍 Fetching activities from Strava API (after {start_date.strftime('%Y-%m-%d')})...")
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=self.headers,
            params={
                'after': start_timestamp,
                'per_page': 200
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch activities: {response.status_code} - {response.text}")
            return TrainingLoad(0, 0, 0, 0, 0, 0)
        
        activities = response.json()
        print(f"✅ Fetched {len(activities)} activities from Strava API")
        
        if not activities:
            return TrainingLoad(0, 0, 0, 0, 0, 0)
        
        # Calculate daily training loads (TRIMP-based)
        daily_loads = self._calculate_daily_trimp_loads(activities)
        print(f"📈 Calculated {len(daily_loads)} days of training load data")
        
        # Calculate ATL (7-day rolling average)
        atl = self._calculate_rolling_average(daily_loads, 7)
        print(f"🔥 ATL (7-day): {round(atl, 2)}")
        
        # Calculate CTL (42-day rolling average)
        ctl = self._calculate_rolling_average(daily_loads, 42)
        print(f"📊 CTL (42-day): {round(ctl, 2)}")
        
        # Calculate TSB (CTL - ATL)
        tsb = ctl - atl
        print(f"⚖️ TSB (Balance): {round(tsb, 2)}")
        
        # Calculate ACWR (7-day load / 28-day load)
        weekly_load_7d = sum(daily_loads[-7:]) if len(daily_loads) >= 7 else 0
        weekly_load_28d = sum(daily_loads[-28:]) if len(daily_loads) >= 28 else 0
        acwr = weekly_load_7d / (weekly_load_28d / 4) if weekly_load_28d > 0 else 0
        print(f"📊 ACWR (7d/28d ratio): {round(acwr, 2)}")
        
        # Calculate Monotony and Strain
        monotony = self._calculate_monotony(daily_loads)
        strain = weekly_load_7d * monotony if monotony > 0 else weekly_load_7d
        print(f"🔄 Monotony: {round(monotony, 2)}, Strain: {round(strain, 2)}")
        
        return TrainingLoad(
            atl=round(atl, 2),
            ctl=round(ctl, 2),
            tsb=round(tsb, 2),
            acwr=round(acwr, 2),
            monotony=round(monotony, 2),
            strain=round(strain, 2)
        )
    
    def _calculate_daily_trimp_loads(self, activities: List[Dict]) -> List[float]:
        """Calculate daily TRIMP loads from activities"""
        daily_loads = {}
        
        for activity in activities:
            date = datetime.fromisoformat(
                activity['start_date_local'].replace('Z', '+00:00')
            ).date()
            
            # Base load from duration and type
            base_load = activity.get('moving_time', 0) / 3600  # hours
            
            # Adjust for intensity if HR data available
            if activity.get('average_heartrate'):
                hr_load = self._calculate_hr_trimp(
                    activity['average_heartrate'], 
                    activity['moving_time']
                )
                base_load = hr_load
            
            daily_loads[date] = daily_loads.get(date, 0) + base_load
        
        # Convert to sorted list of daily loads
        sorted_dates = sorted(daily_loads.keys())
        return [daily_loads[date] for date in sorted_dates]
    
    def _calculate_hr_trimp(self, avg_hr: float, duration: int) -> float:
        """Calculate TRIMP from average heart rate"""
        # Simple TRIMP calculation (can be enhanced with zones)
        if not self.user_zones or 'heart_rate' not in self.user_zones:
            # Use basic calculation
            return (avg_hr / 100) * (duration / 3600)
        
        # Use actual zones if available
        hr_zones = self.user_zones['heart_rate']
        max_hr = hr_zones.get('max', 200)  # Default max HR
        
        # Calculate intensity factor
        intensity = (avg_hr - 60) / (max_hr - 60)  # Normalized intensity
        intensity = max(0, min(1, intensity))  # Clamp between 0 and 1
        
        return intensity * (duration / 3600)  # TRIMP = intensity × duration
    
    def _calculate_rolling_average(self, daily_loads: List[float], window: int) -> float:
        """Calculate rolling average training load"""
        if len(daily_loads) < window:
            return sum(daily_loads) / len(daily_loads) if daily_loads else 0
        
        return sum(daily_loads[-window:]) / window
    
    def _calculate_monotony(self, daily_loads: List[float]) -> float:
        """Calculate training monotony (mean / std dev)"""
        if len(daily_loads) < 7:
            return 1.0
        
        mean_load = statistics.mean(daily_loads[-28:])  # Last 28 days
        std_load = statistics.stdev(daily_loads[-28:]) if len(daily_loads) >= 28 else 1.0
        
        return mean_load / std_load if std_load > 0 else 1.0
    
    def analyze_intensity_distribution(self, days: int = 28) -> IntensityZones:
        """
        Analyze time spent in different intensity zones
        """
        print(f"🎯 Analyzing intensity distribution for last {days} days...")
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())
        
        print(f"🔍 Fetching activities for intensity analysis...")
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=self.headers,
            params={
                'after': start_timestamp,
                'per_page': 200
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch activities for intensity: {response.status_code}")
            return IntensityZones(0, 0, 0, 0, 0, 0)
        
        activities = response.json()
        print(f"✅ Fetched {len(activities)} activities for intensity analysis")
        
        zone_times = [0.0, 0.0, 0.0, 0.0, 0.0]  # Z1-Z5
        total_time = 0.0
        
        for activity in activities:
            duration = activity.get('moving_time', 0) / 3600  # hours
            total_time += duration
            
            # Try to get detailed zone data
            try:
                print(f"🔍 Fetching detailed data for activity {activity['id']}...")
                detail_response = requests.get(
                    f'https://www.strava.com/api/v3/activities/{activity["id"]}',
                    headers=self.headers
                )
                
                if detail_response.status_code == 200:
                    activity_detail = detail_response.json()
                    if 'laps' in activity_detail:
                        print(f"📊 Found {len(activity_detail['laps'])} laps for detailed zone analysis")
                        for lap in activity_detail['laps']:
                            if 'average_heartrate' in lap and lap['average_heartrate']:
                                zone = self._determine_hr_zone(lap['average_heartrate'])
                                zone_times[zone] += lap['moving_time'] / 3600
                    else:
                        # Fallback: estimate from average HR
                        if activity.get('average_heartrate'):
                            zone = self._determine_hr_zone(activity['average_heartrate'])
                            zone_times[zone] += duration
                else:
                    print(f"⚠️ Could not fetch activity detail (status {detail_response.status_code})")
            except Exception as e:
                print(f"❌ Could not analyze zones for activity {activity['id']}: {e}")
        
        print(f"🎯 Intensity Zone Distribution:")
        print(f"   Zone 1 (Easy): {zone_times[0]:.1f}h ({zone_times[0]/total_time*100:.1f}%)")
        print(f"   Zone 2 (Aerobic): {zone_times[1]:.1f}h ({zone_times[1]/total_time*100:.1f}%)")
        print(f"   Zone 3 (Tempo): {zone_times[2]:.1f}h ({zone_times[2]/total_time*100:.1f}%)")
        print(f"   Zone 4 (Threshold): {zone_times[3]:.1f}h ({zone_times[3]/total_time*100:.1f}%)")
        print(f"   Zone 5 (VO2 Max): {zone_times[4]:.1f}h ({zone_times[4]/total_time*100:.1f}%)")
        
        return IntensityZones(
            zone_1_time=zone_times[0],
            zone_2_time=zone_times[1],
            zone_3_time=zone_times[2],
            zone_4_time=zone_times[3],
            zone_5_time=zone_times[4],
            total_time=total_time
        )
    
    def _determine_hr_zone(self, avg_hr: float) -> int:
        """Determine heart rate zone (1-5)"""
        if not self.user_zones or 'heart_rate' not in self.user_zones:
            # Use basic estimation
            if avg_hr < 120:
                return 0  # Zone 1
            elif avg_hr < 140:
                return 1  # Zone 2
            elif avg_hr < 160:
                return 2  # Zone 3
            elif avg_hr < 180:
                return 3  # Zone 4
            else:
                return 4  # Zone 5
        
        # Use actual zones
        hr_zones = self.user_zones['heart_rate']
        zones = hr_zones.get('zones', [])
        
        for i, zone in enumerate(zones):
            if avg_hr <= zone['max']:
                return i
        
        return 4  # Default to zone 5
    
    def calculate_performance_curve(self, days: int = 90) -> PerformanceCurve:
        """
        Calculate best pace/power at different durations
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())
        
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=self.headers,
            params={
                'after': start_timestamp,
                'per_page': 200
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch activities: {response.status_code}")
            return []
        
        activities = response.json()
        
        best_times = {
            1: float('inf'),    # 1 minute
            5: float('inf'),    # 5 minutes
            10: float('inf'),   # 10 minutes
            20: float('inf'),   # 20 minutes
            60: float('inf')    # 60 minutes
        }
        
        for activity in activities:
            if activity.get('type') != 'Run':
                continue
                
            duration = activity.get('moving_time', 0) / 60  # minutes
            
            # Check if this activity sets a new best for any duration
            for target_duration in best_times:
                if duration >= target_duration:
                    # Calculate average pace for this duration
                    distance_km = activity.get('distance', 0) / 1000
                    if distance_km > 0:
                        pace_per_km = duration / distance_km
                        if pace_per_km < best_times[target_duration]:
                            best_times[target_duration] = pace_per_km
        
        # Convert to actual pace values (replace inf with None)
        return PerformanceCurve(
            one_min=best_times[1] if best_times[1] != float('inf') else None,
            five_min=best_times[5] if best_times[5] != float('inf') else None,
            ten_min=best_times[10] if best_times[10] != float('inf') else None,
            twenty_min=best_times[20] if best_times[20] != float('inf') else None,
            sixty_min=best_times[60] if best_times[60] != float('inf') else None
        )
    
    def analyze_volume_trends(self, days: int = 90) -> Dict:
        """
        Analyze training volume trends over time
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())
        
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=self.headers,
            params={
                'after': start_timestamp,
                'per_page': 200
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch activities: {response.status_code}")
            return []
        
        activities = response.json()
        
        # Calculate weekly volumes
        weekly_volumes = {}
        for activity in activities:
            date = datetime.fromisoformat(
                activity['start_date_local'].replace('Z', '+00:00')
            )
            week_start = date - timedelta(days=date.weekday())
            week_key = week_start.strftime('%Y-%W')
            
            if week_key not in weekly_volumes:
                weekly_volumes[week_key] = {
                    'distance': 0,
                    'time': 0,
                    'activities': 0
                }
            
            weekly_volumes[week_key]['distance'] += activity.get('distance', 0) / 1000  # km
            weekly_volumes[week_key]['time'] += activity.get('moving_time', 0) / 3600  # hours
            weekly_volumes[week_key]['activities'] += 1
        
        # Calculate trends
        weeks = sorted(weekly_volumes.keys())
        if len(weeks) >= 4:
            recent_weeks = weeks[-4:]
            older_weeks = weeks[-8:-4] if len(weeks) >= 8 else weeks[:-4]
            
            recent_avg_distance = sum(weekly_volumes[w]['distance'] for w in recent_weeks) / len(recent_weeks)
            older_avg_distance = sum(weekly_volumes[w]['distance'] for w in older_weeks) / len(older_weeks) if older_weeks else recent_avg_distance
            
            distance_trend = ((recent_avg_distance - older_avg_distance) / older_avg_distance * 100) if older_avg_distance > 0 else 0
        else:
            distance_trend = 0
        
        return {
            'weekly_volumes': weekly_volumes,
            'distance_trend_pct': round(distance_trend, 1),
            'total_distance_km': sum(w['distance'] for w in weekly_volumes.values()),
            'total_time_hours': sum(w['time'] for w in weekly_volumes.values()),
            'avg_sessions_per_week': sum(w['activities'] for w in weekly_volumes.values()) / len(weeks) if weeks else 0
        }
    
    def analyze_consistency(self, days: int = 90) -> Dict:
        """
        Analyze training consistency metrics
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())
        
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=self.headers,
            params={
                'after': start_timestamp,
                'per_page': 200
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch activities: {response.status_code}")
            return []
        
        activities = response.json()
        
        # Calculate days between activities
        activity_dates = []
        for activity in activities:
            date = datetime.fromisoformat(
                activity['start_date_local'].replace('Z', '+00:00')
            ).date()
            activity_dates.append(date)
        
        activity_dates.sort()
        
        if len(activity_dates) < 2:
            return {
                'consistency_score': 0,
                'avg_gap_days': 0,
                'longest_streak': 0,
                'current_streak': 0
            }
        
        # Calculate gaps between activities
        gaps = []
        for i in range(1, len(activity_dates)):
            gap = (activity_dates[i] - activity_dates[i-1]).days
            gaps.append(gap)
        
        # Calculate consistency score (lower std dev = more consistent)
        avg_gap = statistics.mean(gaps)
        gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 0
        consistency_score = max(0, 100 - (gap_std * 5))  # Penalty for high variability
        
        # Calculate streaks
        current_streak = 1
        longest_streak = 1
        temp_streak = 1
        
        for i in range(1, len(gaps)):
            if gaps[i] <= 3:  # Within 3 days
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1
        
        # Check current streak
        if gaps and gaps[-1] <= 3:
            current_streak = temp_streak
        
        return {
            'consistency_score': round(consistency_score, 1),
            'avg_gap_days': round(avg_gap, 1),
            'longest_streak': longest_streak,
            'current_streak': current_streak
        }
    
    def analyze_terrain(self, days: int = 90) -> Dict:
        """
        Analyze terrain and elevation patterns
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())
        
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=self.headers,
            params={
                'after': start_timestamp,
                'per_page': 200
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch activities: {response.status_code}")
            return []
        
        activities = response.json()
        
        elevation_data = []
        flat_runs = 0
        hilly_runs = 0
        
        for activity in activities:
            elevation_gain = activity.get('total_elevation_gain', 0)
            distance = activity.get('distance', 0) / 1000  # km
            
            if distance > 0:
                elevation_per_km = elevation_gain / distance
                elevation_data.append(elevation_per_km)
                
                if elevation_per_km < 20:  # Less than 20m per km
                    flat_runs += 1
                elif elevation_per_km > 50:  # More than 50m per km
                    hilly_runs += 1
        
        avg_elevation_per_km = statistics.mean(elevation_data) if elevation_data else 0
        
        return {
            'avg_elevation_per_km': round(avg_elevation_per_km, 1),
            'total_elevation_gain': sum(a.get('total_elevation_gain', 0) for a in activities),
            'flat_runs_pct': round((flat_runs / len(activities) * 100), 1) if activities else 0,
            'hilly_runs_pct': round((hilly_runs / len(activities) * 100), 1) if activities else 0,
            'terrain_variety_score': round(100 - abs(flat_runs - hilly_runs) / len(activities) * 100, 1) if activities else 0
        }
    
    def analyze_cadence(self, days: int = 90) -> Dict:
        """
        Analyze cadence patterns and consistency
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        start_timestamp = int(start_date.timestamp())
        
        response = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            headers=self.headers,
            params={
                'after': start_timestamp,
                'per_page': 200
            }
        )
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch activities: {response.status_code}")
            return []
        
        activities = response.json()
        
        cadence_data = []
        for activity in activities:
            if activity.get('type') == 'Run' and activity.get('average_cadence'):
                cadence_data.append(activity['average_cadence'])
        
        if not cadence_data:
            return {
                'avg_cadence': None,
                'cadence_consistency': 0,
                'cadence_trend': 0
            }
        
        avg_cadence = statistics.mean(cadence_data)
        cadence_std = statistics.stdev(cadence_data) if len(cadence_data) > 1 else 0
        cadence_consistency = max(0, 100 - (cadence_std * 2))  # Penalty for high variability
        
        # Calculate trend
        if len(cadence_data) >= 4:
            recent_avg = statistics.mean(cadence_data[-4:])
            older_avg = statistics.mean(cadence_data[:-4])
            cadence_trend = recent_avg - older_avg
        else:
            cadence_trend = 0
        
        return {
            'avg_cadence': round(avg_cadence, 1),
            'cadence_consistency': round(cadence_consistency, 1),
            'cadence_trend': round(cadence_trend, 1)
        }
    
    def calculate_wellness_score(self, wellness_data: WellnessMetrics, training_load: TrainingLoad) -> float:
        """
        Calculate overall wellness score from subjective and objective data
        """
        if not wellness_data.mood:
            return None
        
        # Weight the components
        mood_score = (wellness_data.mood / 5) * 30
        stress_score = ((6 - wellness_data.stress) / 5) * 20 if wellness_data.stress else 15
        motivation_score = (wellness_data.motivation / 5) * 20 if wellness_data.motivation else 15
        sleep_score = (wellness_data.sleep_quality / 5) * 20 if wellness_data.sleep_quality else 15
        soreness_score = ((11 - wellness_data.soreness) / 10) * 10 if wellness_data.soreness else 5
        
        wellness_score = mood_score + stress_score + motivation_score + sleep_score + soreness_score
        
        # Adjust for training load (high load + poor wellness = lower score)
        if training_load.tsb < -10:  # Very fatigued
            wellness_score *= 0.9
        elif training_load.tsb > 10:  # Very fresh
            wellness_score *= 1.1
        
        return min(100, max(0, round(wellness_score, 1)))
    
    def calculate_readiness_score(self, wellness_score: float, training_load: TrainingLoad) -> float:
        """
        Calculate training readiness score
        """
        if wellness_score is None:
            return None
        
        # Base readiness from wellness
        readiness = wellness_score * 0.6
        
        # Adjust for training load
        if training_load.tsb > 5:  # Fresh
            readiness += 20
        elif training_load.tsb < -15:  # Very fatigued
            readiness -= 20
        elif training_load.tsb < -5:  # Fatigued
            readiness -= 10
        
        # Adjust for ACWR
        if 0.8 <= training_load.acwr <= 1.3:  # Optimal load
            readiness += 10
        elif training_load.acwr > 1.5:  # Too much load
            readiness -= 15
        
        return min(100, max(0, round(readiness, 1)))
    
    def generate_recommendations(self, insights: TrainingInsights) -> List[str]:
        """
        Generate actionable training recommendations
        """
        recommendations = []
        
        # Training load recommendations
        if insights.training_load.tsb < -15:
            recommendations.append("🚨 High fatigue detected. Consider a recovery week with easy sessions only.")
        elif insights.training_load.tsb > 10:
            recommendations.append("💪 You're well-rested! Great time for a hard training block.")
        
        if insights.training_load.acwr > 1.5:
            recommendations.append("⚠️ Training load spike detected. Reduce volume this week to prevent injury.")
        elif insights.training_load.acwr < 0.8:
            recommendations.append("📈 You can safely increase training load this week.")
        
        # Intensity distribution recommendations
        total_time = insights.intensity_distribution.total_time
        if total_time > 0:
            easy_pct = insights.intensity_distribution.zone_1_time / total_time
            hard_pct = (insights.intensity_distribution.zone_4_time + insights.intensity_distribution.zone_5_time) / total_time
            
            if easy_pct < 0.7:
                recommendations.append("🏃‍♂️ Increase easy training time to 70-80% of total volume.")
            elif hard_pct > 0.3:
                recommendations.append("🔥 Reduce high-intensity training to 20-30% of total volume.")
        
        # Consistency recommendations
        if insights.consistency_metrics['consistency_score'] < 70:
            recommendations.append("📅 Improve training consistency. Aim for 3-4 sessions per week.")
        
        # Cadence recommendations
        if insights.cadence_analysis['avg_cadence'] and insights.cadence_analysis['avg_cadence'] < 160:
            recommendations.append("👟 Focus on increasing cadence to 170-180 steps per minute.")
        
        # Terrain recommendations
        if insights.terrain_analysis['hilly_runs_pct'] < 20:
            recommendations.append("⛰️ Add more hill training to improve strength and power.")
        
        return recommendations
    
    def get_comprehensive_insights(self, days: int = 90, wellness_data: Optional[WellnessMetrics] = None) -> TrainingInsights:
        """
        Get comprehensive training insights combining all metrics
        """
        print(f"\n🚀 === COMPREHENSIVE ANALYTICS FOR LAST {days} DAYS ===")
        print(f"📅 Analysis Period: {datetime.now() - timedelta(days=days)} to {datetime.now()}")
        
        print(f"\n1️⃣ TRAINING LOAD ANALYSIS")
        training_load = self.calculate_training_load(days)
        
        print(f"\n2️⃣ INTENSITY DISTRIBUTION ANALYSIS")
        intensity_distribution = self.analyze_intensity_distribution(days)
        
        print(f"\n3️⃣ PERFORMANCE CURVE ANALYSIS")
        performance_curve = self.calculate_performance_curve(days)
        
        print(f"\n4️⃣ VOLUME TRENDS ANALYSIS")
        volume_trends = self.analyze_volume_trends(days)
        
        print(f"\n5️⃣ CONSISTENCY ANALYSIS")
        consistency_metrics = self.analyze_consistency(days)
        
        print(f"\n6️⃣ TERRAIN ANALYSIS")
        terrain_analysis = self.analyze_terrain(days)
        
        print(f"\n7️⃣ CADENCE ANALYSIS")
        cadence_analysis = self.analyze_cadence(days)
        
        wellness_score = None
        readiness_score = None
        
        if wellness_data:
            print(f"\n8️⃣ WELLNESS ANALYSIS")
            wellness_score = self.calculate_wellness_score(wellness_data, training_load)
            readiness_score = self.calculate_readiness_score(wellness_score, training_load)
            print(f"💚 Wellness Score: {wellness_score}/100")
            print(f"🎯 Readiness Score: {readiness_score}/100")
        else:
            print(f"\n8️⃣ WELLNESS ANALYSIS - No wellness data provided")
        
        print(f"\n9️⃣ GENERATING RECOMMENDATIONS")
        insights = TrainingInsights(
            training_load=training_load,
            intensity_distribution=intensity_distribution,
            performance_curve=performance_curve,
            volume_trends=volume_trends,
            consistency_metrics=consistency_metrics,
            terrain_analysis=terrain_analysis,
            cadence_analysis=cadence_analysis,
            wellness_score=wellness_score,
            readiness_score=readiness_score
        )
        
        insights.recommendations = self.generate_recommendations(insights)
        print(f"💡 Generated {len(insights.recommendations)} recommendations")
        
        print(f"\n✅ === ANALYTICS COMPLETE ===")
        return insights
