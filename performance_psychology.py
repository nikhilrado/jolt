"""
Performance Psychology Engine for Jolt
Correlates objective performance metrics with subjective wellness data
to provide psychological insights and recommendations.
"""

import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import statistics
import json


@dataclass
class PerformanceEvent:
    """A significant performance event that needs psychological analysis"""
    event_type: str  # 'split_degradation', 'pace_positive_split', 'heart_rate_drift', 'early_fatigue', 'breakthrough'
    activity_id: int
    activity_name: str
    timestamp: datetime
    objective_data: Dict  # The actual performance data
    severity: float  # 0-1 scale of how significant this event is
    psychological_context: Optional[str] = None


@dataclass
class PsychologicalInsight:
    """Psychological insight based on performance patterns"""
    insight_type: str
    title: str
    description: str
    evidence: List[str]
    recommendations: List[str]
    confidence: float  # 0-1 scale
    related_events: List[PerformanceEvent]


@dataclass
class WellnessTrend:
    """Wellness data trend analysis"""
    metric: str
    trend_direction: str  # 'improving', 'declining', 'stable'
    trend_strength: float  # 0-1 scale
    recent_values: List[float]
    correlation_with_performance: Optional[float] = None


class PerformancePsychologyEngine:
    """
    Engine for analyzing performance psychology by correlating
    objective Strava data with subjective wellness metrics
    """
    
    def __init__(self, headers):
        self.headers = headers
        self.wellness_history = []  # Store historical wellness data
    
    def analyze_performance_psychology(self, days: int = 30) -> Dict:
        """
        Comprehensive performance psychology analysis
        """
        print(f"\n🧠 === PERFORMANCE PSYCHOLOGY ANALYSIS ===")
        print(f"📅 Analyzing last {days} days for psychological patterns")
        
        # Get recent activities
        activities = self._get_recent_activities(days)
        print(f"🔍 Found {len(activities)} activities to analyze")
        
        # Detect performance events
        performance_events = self._detect_performance_events(activities)
        print(f"🎯 Detected {len(performance_events)} significant performance events")
        
        # Analyze wellness trends
        wellness_trends = self._analyze_wellness_trends()
        print(f"💚 Analyzed {len(wellness_trends)} wellness trends")
        
        # Correlate performance with wellness
        correlations = self._correlate_performance_wellness(activities, wellness_trends)
        print(f"🔗 Found {len(correlations)} performance-wellness correlations")
        
        # Generate psychological insights
        insights = self._generate_psychological_insights(performance_events, wellness_trends, correlations)
        print(f"💡 Generated {len(insights)} psychological insights")
        
        # Generate performance psychology recommendations
        recommendations = self._generate_psychology_recommendations(insights, wellness_trends)
        print(f"🎯 Generated {len(recommendations)} psychology recommendations")
        
        return {
            'performance_events': performance_events,
            'wellness_trends': wellness_trends,
            'correlations': correlations,
            'psychological_insights': insights,
            'recommendations': recommendations,
            'analysis_period': f"{days} days"
        }
    
    def _get_recent_activities(self, days: int) -> List[Dict]:
        """Get recent activities with detailed data"""
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
        
        # Enhance activities with detailed data
        enhanced_activities = []
        for activity in activities:
            if activity.get('type') == 'Run':  # Focus on running for psychology analysis
                enhanced_activity = self._enhance_activity_for_psychology(activity)
                enhanced_activities.append(enhanced_activity)
        
        return enhanced_activities
    
    def _enhance_activity_for_psychology(self, activity: Dict) -> Dict:
        """Enhance activity with data needed for psychological analysis"""
        activity_id = activity['id']
        
        try:
            # Get detailed activity data
            detail_response = requests.get(
                f'https://www.strava.com/api/v3/activities/{activity_id}',
                headers=self.headers
            )
            
            if detail_response.status_code == 200:
                detailed_activity = detail_response.json()
                activity.update({
                    'splits_metric': detailed_activity.get('splits_metric', []),
                    'laps': detailed_activity.get('laps', []),
                    'best_efforts': detailed_activity.get('best_efforts', []),
                    'average_heartrate': detailed_activity.get('average_heartrate'),
                    'max_heartrate': detailed_activity.get('max_heartrate'),
                    'suffer_score': detailed_activity.get('suffer_score'),
                    'description': detailed_activity.get('description', '')
                })
            
            # Try to get streams for detailed analysis
            try:
                streams_response = requests.get(
                    f'https://www.strava.com/api/v3/activities/{activity_id}/streams',
                    headers=self.headers,
                    params={
                        'keys': 'time,distance,heartrate,velocity_smooth,altitude',
                        'key_by_type': 'true'
                    }
                )
                
                if streams_response.status_code == 200:
                    streams_data = streams_response.json()
                    activity['streams'] = streams_data
                    
                    # Analyze pace consistency
                    if 'velocity_smooth' in streams_data:
                        velocities = streams_data['velocity_smooth']['data']
                        activity['pace_consistency'] = self._analyze_pace_consistency(velocities)
                    
                    # Analyze heart rate drift
                    if 'heartrate' in streams_data:
                        hr_data = streams_data['heartrate']['data']
                        activity['hr_drift'] = self._analyze_hr_drift(hr_data)
                        
            except Exception as e:
                print(f"⚠️ Could not fetch streams for activity {activity_id}: {e}")
                
        except Exception as e:
            print(f"⚠️ Could not enhance activity {activity_id}: {e}")
        
        return activity
    
    def _analyze_pace_consistency(self, velocities: List[float]) -> Dict:
        """Analyze pace consistency throughout the run"""
        if not velocities or len(velocities) < 10:
            return {'consistency_score': 0, 'variation_pct': 0}
        
        # Calculate coefficient of variation (CV = std/mean)
        mean_velocity = statistics.mean(velocities)
        std_velocity = statistics.stdev(velocities) if len(velocities) > 1 else 0
        
        cv = std_velocity / mean_velocity if mean_velocity > 0 else 0
        consistency_score = max(0, 1 - cv)  # Higher is more consistent
        
        return {
            'consistency_score': round(consistency_score, 3),
            'variation_pct': round(cv * 100, 1),
            'mean_pace': round(mean_velocity * 3.6, 2),  # km/h
            'pace_range': round((max(velocities) - min(velocities)) * 3.6, 2)
        }
    
    def _analyze_hr_drift(self, hr_data: List[float]) -> Dict:
        """Analyze heart rate drift (indicator of fatigue)"""
        if not hr_data or len(hr_data) < 20:
            return {'drift_pct': 0, 'fatigue_indicator': 'none'}
        
        # Split into first and second half
        mid_point = len(hr_data) // 2
        first_half = hr_data[:mid_point]
        second_half = hr_data[mid_point:]
        
        first_half_avg = statistics.mean(first_half)
        second_half_avg = statistics.mean(second_half)
        
        drift_pct = ((second_half_avg - first_half_avg) / first_half_avg) * 100 if first_half_avg > 0 else 0
        
        # Categorize fatigue level
        if drift_pct > 10:
            fatigue_indicator = 'high'
        elif drift_pct > 5:
            fatigue_indicator = 'moderate'
        elif drift_pct > 2:
            fatigue_indicator = 'slight'
        else:
            fatigue_indicator = 'none'
        
        return {
            'drift_pct': round(drift_pct, 1),
            'fatigue_indicator': fatigue_indicator,
            'first_half_avg': round(first_half_avg, 1),
            'second_half_avg': round(second_half_avg, 1)
        }
    
    def _detect_performance_events(self, activities: List[Dict]) -> List[PerformanceEvent]:
        """Detect significant performance events that need psychological analysis"""
        events = []
        
        for activity in activities:
            # 1. Split degradation analysis
            if 'splits_metric' in activity and activity['splits_metric']:
                split_events = self._detect_split_degradation(activity)
                events.extend(split_events)
            
            # 2. Pace consistency analysis
            if 'pace_consistency' in activity:
                pace_events = self._detect_pace_issues(activity)
                events.extend(pace_events)
            
            # 3. Heart rate drift analysis
            if 'hr_drift' in activity:
                hr_events = self._detect_hr_issues(activity)
                events.extend(hr_events)
            
            # 4. Performance breakthroughs
            breakthrough_events = self._detect_performance_breakthroughs(activity, activities)
            events.extend(breakthrough_events)
        
        return events
    
    def _detect_split_degradation(self, activity: Dict) -> List[PerformanceEvent]:
        """Detect significant split degradation (hitting the wall)"""
        events = []
        splits = activity['splits_metric']
        
        if len(splits) < 3:
            return events
        
        # Analyze split progression
        split_times = [split['moving_time'] for split in splits]
        
        # Check for significant degradation in later splits
        for i in range(2, len(split_times)):
            early_avg = statistics.mean(split_times[:i//2])
            recent_split = split_times[i]
            
            degradation_pct = ((recent_split - early_avg) / early_avg) * 100
            
            if degradation_pct > 15:  # More than 15% slower
                severity = min(1.0, degradation_pct / 30)  # Normalize to 0-1
                
                event = PerformanceEvent(
                    event_type='split_degradation',
                    activity_id=activity['id'],
                    activity_name=activity['name'],
                    timestamp=datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00')),
                    objective_data={
                        'degradation_pct': degradation_pct,
                        'split_number': i + 1,
                        'early_avg_time': early_avg,
                        'degraded_split_time': recent_split,
                        'total_splits': len(splits)
                    },
                    severity=severity
                )
                events.append(event)
        
        return events
    
    def _detect_pace_issues(self, activity: Dict) -> List[PerformanceEvent]:
        """Detect pace consistency issues"""
        events = []
        pace_data = activity['pace_consistency']
        
        if pace_data['consistency_score'] < 0.7:  # Low consistency
            severity = 1 - pace_data['consistency_score']
            
            event = PerformanceEvent(
                event_type='pace_inconsistency',
                activity_id=activity['id'],
                activity_name=activity['name'],
                timestamp=datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00')),
                objective_data=pace_data,
                severity=severity
            )
            events.append(event)
        
        return events
    
    def _detect_hr_issues(self, activity: Dict) -> List[PerformanceEvent]:
        """Detect heart rate drift issues"""
        events = []
        hr_data = activity['hr_drift']
        
        if hr_data['fatigue_indicator'] in ['moderate', 'high']:
            severity = 0.5 if hr_data['fatigue_indicator'] == 'moderate' else 0.8
            
            event = PerformanceEvent(
                event_type='heart_rate_drift',
                activity_id=activity['id'],
                activity_name=activity['name'],
                timestamp=datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00')),
                objective_data=hr_data,
                severity=severity
            )
            events.append(event)
        
        return events
    
    def _detect_performance_breakthroughs(self, activity: Dict, all_activities: List[Dict]) -> List[PerformanceEvent]:
        """Detect performance breakthroughs (PRs, best efforts)"""
        events = []
        
        # Check if this activity has any best efforts (PRs)
        if 'best_efforts' in activity and activity['best_efforts']:
            for effort in activity['best_efforts']:
                if effort.get('is_kom', False) or effort.get('pr_rank', 0) == 1:
                    event = PerformanceEvent(
                        event_type='performance_breakthrough',
                        activity_id=activity['id'],
                        activity_name=activity['name'],
                        timestamp=datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00')),
                        objective_data={
                            'effort_name': effort['name'],
                            'effort_time': effort['moving_time'],
                            'effort_distance': effort.get('distance', 0),
                            'is_kom': effort.get('is_kom', False),
                            'pr_rank': effort.get('pr_rank', 0)
                        },
                        severity=0.9  # High significance
                    )
                    events.append(event)
        
        return events
    
    def _analyze_wellness_trends(self) -> List[WellnessTrend]:
        """Analyze wellness data trends"""
        trends = []
        
        if not self.wellness_history:
            print("⚠️ No wellness history available for trend analysis")
            return trends
        
        # Analyze trends for each wellness metric
        wellness_metrics = ['mood', 'stress', 'motivation', 'sleep_quality', 'soreness', 'perceived_effort']
        
        for metric in wellness_metrics:
            values = [entry.get(metric) for entry in self.wellness_history if entry.get(metric) is not None]
            
            if len(values) < 3:
                continue
            
            # Calculate trend
            recent_avg = statistics.mean(values[-3:]) if len(values) >= 3 else statistics.mean(values)
            older_avg = statistics.mean(values[:-3]) if len(values) > 3 else recent_avg
            
            trend_direction = 'stable'
            trend_strength = 0
            
            if recent_avg > older_avg * 1.1:  # 10% improvement
                trend_direction = 'improving'
                trend_strength = (recent_avg - older_avg) / older_avg
            elif recent_avg < older_avg * 0.9:  # 10% decline
                trend_direction = 'declining'
                trend_strength = (older_avg - recent_avg) / older_avg
            
            trend = WellnessTrend(
                metric=metric,
                trend_direction=trend_direction,
                trend_strength=round(trend_strength, 3),
                recent_values=values[-7:]  # Last 7 entries
            )
            trends.append(trend)
        
        return trends
    
    def _correlate_performance_wellness(self, activities: List[Dict], wellness_trends: List[WellnessTrend]) -> List[Dict]:
        """Correlate performance metrics with wellness data"""
        correlations = []
        
        if not wellness_trends:
            return correlations
        
        # Analyze correlations between performance and wellness
        for activity in activities:
            activity_date = datetime.fromisoformat(activity['start_date_local'].replace('Z', '+00:00')).date()
            
            # Find wellness data closest to this activity
            closest_wellness = self._find_closest_wellness_data(activity_date)
            
            if closest_wellness:
                correlation_data = {
                    'activity_id': activity['id'],
                    'activity_date': activity_date,
                    'wellness_data': closest_wellness,
                    'performance_metrics': {
                        'average_pace': activity.get('average_speed', 0) * 3.6,  # km/h
                        'suffer_score': activity.get('suffer_score', 0),
                        'consistency_score': activity.get('pace_consistency', {}).get('consistency_score', 0),
                        'hr_drift': activity.get('hr_drift', {}).get('drift_pct', 0)
                    }
                }
                correlations.append(correlation_data)
        
        return correlations
    
    def _find_closest_wellness_data(self, activity_date: datetime.date) -> Optional[Dict]:
        """Find wellness data closest to the activity date"""
        if not self.wellness_history:
            return None
        
        closest_entry = None
        min_days_diff = float('inf')
        
        for entry in self.wellness_history:
            entry_date = datetime.fromisoformat(entry['date']).date()
            days_diff = abs((activity_date - entry_date).days)
            
            if days_diff < min_days_diff and days_diff <= 3:  # Within 3 days
                min_days_diff = days_diff
                closest_entry = entry
        
        return closest_entry
    
    def _generate_psychological_insights(self, events: List[PerformanceEvent], 
                                       wellness_trends: List[WellnessTrend],
                                       correlations: List[Dict]) -> List[PsychologicalInsight]:
        """Generate psychological insights from the analysis"""
        insights = []
        
        # 1. Split degradation insights
        split_events = [e for e in events if e.event_type == 'split_degradation']
        if split_events:
            insight = self._create_split_degradation_insight(split_events, wellness_trends)
            insights.append(insight)
        
        # 2. Mental toughness insights
        breakthrough_events = [e for e in events if e.event_type == 'performance_breakthrough']
        if breakthrough_events:
            insight = self._create_mental_toughness_insight(breakthrough_events, wellness_trends)
            insights.append(insight)
        
        # 3. Consistency insights
        pace_events = [e for e in events if e.event_type == 'pace_inconsistency']
        if pace_events:
            insight = self._create_consistency_insight(pace_events, wellness_trends)
            insights.append(insight)
        
        return insights
    
    def _create_split_degradation_insight(self, events: List[PerformanceEvent], 
                                        wellness_trends: List[WellnessTrend]) -> PsychologicalInsight:
        """Create insight about split degradation (hitting the wall)"""
        avg_degradation = statistics.mean([e.objective_data['degradation_pct'] for e in events])
        
        # Check wellness context
        stress_trend = next((t for t in wellness_trends if t.metric == 'stress'), None)
        motivation_trend = next((t for t in wellness_trends if t.metric == 'motivation'), None)
        
        evidence = [
            f"Average split degradation: {avg_degradation:.1f}%",
            f"Occurred in {len(events)} recent activities",
            f"Most severe degradation: {max(e.objective_data['degradation_pct'] for e in events):.1f}%"
        ]
        
        recommendations = []
        
        # Psychological recommendations based on context
        if stress_trend and stress_trend.trend_direction == 'declining':
            recommendations.extend([
                "🧠 Practice mental toughness techniques like positive self-talk",
                "🎯 Break long runs into smaller, manageable segments",
                "💪 Build confidence with shorter, successful runs first"
            ])
        else:
            recommendations.extend([
                "⏱️ Practice negative splitting (start slower, finish stronger)",
                "🏃‍♂️ Increase weekly volume gradually to build endurance",
                "🧘‍♀️ Practice mindfulness during challenging moments"
            ])
        
        return PsychologicalInsight(
            insight_type='split_degradation',
            title='Mental Toughness During Fatigue',
            description=f"You're experiencing significant pace degradation in the latter parts of runs, averaging {avg_degradation:.1f}% slower. This suggests either physical fatigue or mental challenges when the going gets tough.",
            evidence=evidence,
            recommendations=recommendations,
            confidence=0.8,
            related_events=events
        )
    
    def _create_mental_toughness_insight(self, events: List[PerformanceEvent], 
                                       wellness_trends: List[WellnessTrend]) -> PsychologicalInsight:
        """Create insight about mental toughness and breakthroughs"""
        evidence = [
            f"Achieved {len(events)} performance breakthroughs recently",
            f"Breakthrough types: {', '.join(set(e.objective_data['effort_name'] for e in events))}"
        ]
        
        recommendations = [
            "🔥 You're in a breakthrough phase - maintain this momentum!",
            "🎯 Set slightly more ambitious goals for your next training cycle",
            "💪 Your mental toughness is strong - use this confidence for challenging workouts"
        ]
        
        return PsychologicalInsight(
            insight_type='mental_toughness',
            title='Performance Breakthrough Momentum',
            description="You've been achieving significant performance breakthroughs recently, indicating strong mental toughness and physical adaptation.",
            evidence=evidence,
            recommendations=recommendations,
            confidence=0.9,
            related_events=events
        )
    
    def _create_consistency_insight(self, events: List[PerformanceEvent], 
                                  wellness_trends: List[WellnessTrend]) -> PsychologicalInsight:
        """Create insight about pace consistency"""
        avg_consistency = statistics.mean([e.objective_data['consistency_score'] for e in events])
        
        evidence = [
            f"Average pace consistency score: {avg_consistency:.2f}",
            f"Pace variation: {statistics.mean([e.objective_data['variation_pct'] for e in events]):.1f}%"
        ]
        
        recommendations = [
            "🎯 Practice pacing strategies with tempo runs",
            "⏱️ Use a metronome or GPS watch to maintain steady pace",
            "🧠 Focus on mental discipline during the first half of runs"
        ]
        
        return PsychologicalInsight(
            insight_type='pace_consistency',
            title='Pace Discipline and Mental Focus',
            description="Your pace consistency could improve, suggesting opportunities to develop better pacing discipline and mental focus during runs.",
            evidence=evidence,
            recommendations=recommendations,
            confidence=0.7,
            related_events=events
        )
    
    def _generate_psychology_recommendations(self, insights: List[PsychologicalInsight], 
                                           wellness_trends: List[WellnessTrend]) -> List[str]:
        """Generate actionable psychology recommendations"""
        recommendations = []
        
        # General recommendations based on insights
        for insight in insights:
            recommendations.extend(insight.recommendations)
        
        # Wellness-based recommendations
        stress_trend = next((t for t in wellness_trends if t.metric == 'stress'), None)
        if stress_trend and stress_trend.trend_direction == 'declining':
            recommendations.extend([
                "🧘‍♀️ Consider meditation or breathing exercises before challenging runs",
                "😴 Prioritize sleep - stress and poor sleep affect performance psychology",
                "🎵 Use music or podcasts to distract from negative thoughts during tough miles"
            ])
        
        motivation_trend = next((t for t in wellness_trends if t.metric == 'motivation'), None)
        if motivation_trend and motivation_trend.trend_direction == 'declining':
            recommendations.extend([
                "🎯 Set smaller, achievable goals to rebuild motivation",
                "🏃‍♂️ Join a running group or find a training partner",
                "📱 Use running apps to track progress and celebrate achievements"
            ])
        
        return list(set(recommendations))  # Remove duplicates
    
    def submit_wellness_data(self, wellness_data: Dict) -> bool:
        """Submit wellness data for psychology analysis"""
        try:
            wellness_entry = {
                'date': datetime.now().isoformat(),
                'mood': wellness_data.get('mood'),
                'stress': wellness_data.get('stress'),
                'motivation': wellness_data.get('motivation'),
                'sleep_quality': wellness_data.get('sleep_quality'),
                'soreness': wellness_data.get('soreness'),
                'perceived_effort': wellness_data.get('perceived_effort')
            }
            
            self.wellness_history.append(wellness_entry)
            print(f"✅ Wellness data submitted: {wellness_entry}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to submit wellness data: {e}")
            return False
    
    def get_psychology_summary(self, days: int = 30) -> Dict:
        """Get a summary of performance psychology analysis"""
        analysis = self.analyze_performance_psychology(days)
        
        return {
            'summary': {
                'total_events': len(analysis['performance_events']),
                'insights_count': len(analysis['psychological_insights']),
                'recommendations_count': len(analysis['recommendations']),
                'analysis_period': analysis['analysis_period']
            },
            'key_findings': [
                insight.title for insight in analysis['psychological_insights']
            ],
            'top_recommendations': analysis['recommendations'][:5],
            'wellness_status': self._get_wellness_status(analysis['wellness_trends'])
        }
    
    def _get_wellness_status(self, wellness_trends: List[WellnessTrend]) -> Dict:
        """Get overall wellness status"""
        if not wellness_trends:
            return {'status': 'no_data', 'message': 'No wellness data available'}
        
        improving_count = sum(1 for t in wellness_trends if t.trend_direction == 'improving')
        declining_count = sum(1 for t in wellness_trends if t.trend_direction == 'declining')
        
        if improving_count > declining_count:
            return {'status': 'positive', 'message': 'Wellness trends are generally improving'}
        elif declining_count > improving_count:
            return {'status': 'concern', 'message': 'Some wellness metrics are declining'}
        else:
            return {'status': 'stable', 'message': 'Wellness metrics are stable'}
