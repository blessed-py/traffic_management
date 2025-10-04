from typing import List, Dict, Tuple, Optional
from datetime import datetime, timedelta
from collections import defaultdict
import statistics
from app.Database.database import get_recent_events


class TrafficAnalytics:
    """Analytics engine for traffic pattern detection and congestion alerts."""
    
    def __init__(self):
        self.congestion_threshold = 15  # vehicles per intersection
        self.slow_speed_threshold = 20  # km/h
        self.queue_threshold = 8  # vehicles in queue
        
    def analyze_current_conditions(self, limit: int = 100) -> Dict:
        """Analyze current traffic conditions across all intersections."""
        events = get_recent_events(limit)
        if not events:
            return {"status": "no_data", "intersections": {}}
            
        # Group by intersection
        intersection_data = defaultdict(list)
        for event in events:
            intersection_data[event["intersection_id"]].append(event)
        
        analysis = {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "intersections": {},
            "alerts": [],
            "overall_stats": {}
        }
        
        congested_count = 0
        total_intersections = len(intersection_data)
        
        for intersection_id, intersection_events in intersection_data.items():
            if not intersection_events:
                continue
                
            latest_event = intersection_events[0]  # Most recent event
            intersection_analysis = self._analyze_intersection(intersection_id, intersection_events)
            
            analysis["intersections"][intersection_id] = intersection_analysis
            
            # Generate alerts
            if intersection_analysis["congestion_level"] == "high":
                congested_count += 1
                analysis["alerts"].append({
                    "type": "congestion",
                    "intersection_id": intersection_id,
                    "severity": "high",
                    "message": f"High congestion detected at intersection {intersection_id}",
                    "details": {
                        "vehicle_count": latest_event["vehicle_count"],
                        "queue_length": latest_event["queue_len"],
                        "avg_speed": latest_event["avg_speed"]
                    }
                })
            elif intersection_analysis["congestion_level"] == "moderate":
                analysis["alerts"].append({
                    "type": "congestion",
                    "intersection_id": intersection_id,
                    "severity": "moderate", 
                    "message": f"Moderate congestion at intersection {intersection_id}",
                    "details": {
                        "vehicle_count": latest_event["vehicle_count"],
                        "queue_length": latest_event["queue_len"],
                        "avg_speed": latest_event["avg_speed"]
                    }
                })
        
        # Overall statistics
        analysis["overall_stats"] = {
            "total_intersections": total_intersections,
            "congested_intersections": congested_count,
            "congestion_rate": congested_count / total_intersections if total_intersections > 0 else 0,
            "network_status": self._determine_network_status(congested_count, total_intersections)
        }
        
        return analysis
    
    def _analyze_intersection(self, intersection_id: str, events: List[Dict]) -> Dict:
        """Analyze individual intersection traffic patterns."""
        if not events:
            return {"status": "no_data"}
            
        latest = events[0]
        
        # Calculate averages for trend analysis
        vehicle_counts = [e["vehicle_count"] for e in events[:10]]  # Last 10 readings
        speeds = [e["avg_speed"] for e in events[:10]]
        queue_lengths = [e["queue_len"] for e in events[:10]]
        
        avg_vehicles = statistics.mean(vehicle_counts)
        avg_speed = statistics.mean(speeds)
        avg_queue = statistics.mean(queue_lengths)
        
        # Determine congestion level
        congestion_level = self._calculate_congestion_level(
            latest["vehicle_count"], 
            latest["avg_speed"], 
            latest["queue_len"]
        )
        
        # Traffic flow efficiency (higher is better)
        efficiency = self._calculate_traffic_efficiency(avg_speed, avg_queue, avg_vehicles)
        
        # Detect trends
        trend = self._detect_trend(vehicle_counts)
        
        return {
            "intersection_id": intersection_id,
            "current_stats": {
                "vehicle_count": latest["vehicle_count"],
                "avg_speed": latest["avg_speed"],
                "queue_length": latest["queue_len"],
                "timestamp": latest["timestamp"]
            },
            "averages": {
                "vehicle_count": round(avg_vehicles, 1),
                "speed": round(avg_speed, 1),
                "queue_length": round(avg_queue, 1)
            },
            "congestion_level": congestion_level,
            "efficiency_score": efficiency,
            "trend": trend,
            "recommendations": self._generate_recommendations(congestion_level, trend, latest)
        }
    
    def _calculate_congestion_level(self, vehicle_count: int, avg_speed: float, queue_len: int) -> str:
        """Calculate congestion level based on multiple factors."""
        congestion_score = 0
        
        # Vehicle count factor
        if vehicle_count >= self.congestion_threshold:
            congestion_score += 2
        elif vehicle_count >= self.congestion_threshold * 0.7:
            congestion_score += 1
            
        # Speed factor
        if avg_speed <= self.slow_speed_threshold:
            congestion_score += 2
        elif avg_speed <= self.slow_speed_threshold * 1.5:
            congestion_score += 1
            
        # Queue length factor
        if queue_len >= self.queue_threshold:
            congestion_score += 2
        elif queue_len >= self.queue_threshold * 0.7:
            congestion_score += 1
        
        if congestion_score >= 4:
            return "high"
        elif congestion_score >= 2:
            return "moderate"
        else:
            return "low"
    
    def _calculate_traffic_efficiency(self, avg_speed: float, avg_queue: float, avg_vehicles: float) -> float:
        """Calculate traffic flow efficiency score (0-100)."""
        speed_score = min(avg_speed / 60 * 100, 100)  # Normalize to 60 km/h max
        queue_score = max(100 - (avg_queue / 15 * 100), 0)  # Lower queue is better
        throughput_score = min(avg_vehicles / 20 * 100, 100)  # Normalize to 20 vehicles
        
        # Weighted average
        efficiency = (speed_score * 0.4 + queue_score * 0.4 + throughput_score * 0.2)
        return round(efficiency, 1)
    
    def _detect_trend(self, values: List[float]) -> str:
        """Detect if traffic is increasing, decreasing, or stable."""
        if len(values) < 4:
            return "stable"
            
        recent_avg = statistics.mean(values[:3])  # Last 3 readings
        older_values = values[3:6] if len(values) >= 6 else values[3:]
        
        if not older_values:  # No older data to compare
            return "stable"
            
        older_avg = statistics.mean(older_values)
        
        change_threshold = 2  # vehicles
        if recent_avg > older_avg + change_threshold:
            return "increasing"
        elif recent_avg < older_avg - change_threshold:
            return "decreasing"
        else:
            return "stable"
    
    def _generate_recommendations(self, congestion_level: str, trend: str, latest_event: Dict) -> List[str]:
        """Generate traffic management recommendations."""
        recommendations = []
        
        if congestion_level == "high":
            recommendations.append("🚦 Consider extending green light duration")
            recommendations.append("📱 Send congestion alerts to approaching vehicles")
            
            if latest_event["queue_len"] > 10:
                recommendations.append("🚧 Deploy traffic management personnel")
                
        elif congestion_level == "moderate":
            recommendations.append("⚠️  Monitor closely for congestion escalation")
            
        if trend == "increasing":
            recommendations.append("📈 Traffic volume is rising - prepare for peak conditions")
        elif trend == "decreasing":
            recommendations.append("📉 Traffic is clearing - consider optimizing signal timing")
            
        if latest_event["avg_speed"] < 15:
            recommendations.append("🐌 Very slow speeds detected - check for incidents")
            
        if not recommendations:
            recommendations.append("✅ Traffic flowing normally")
            
        return recommendations
    
    def _determine_network_status(self, congested_count: int, total_count: int) -> str:
        """Determine overall network traffic status."""
        if total_count == 0:
            return "unknown"
            
        congestion_rate = congested_count / total_count
        
        if congestion_rate >= 0.6:
            return "heavy"
        elif congestion_rate >= 0.3:
            return "moderate"
        else:
            return "light"
    
    def get_intersection_patterns(self, intersection_id: str, hours: int = 24) -> Dict:
        """Analyze traffic patterns for a specific intersection over time."""
        # This would typically query historical data
        # For now, we'll use recent events as a demo
        events = get_recent_events(100)
        intersection_events = [e for e in events if e["intersection_id"] == intersection_id]
        
        if not intersection_events:
            return {"status": "no_data", "intersection_id": intersection_id}
        
        # Group by hour for pattern analysis
        hourly_data = defaultdict(list)
        for event in intersection_events:
            try:
                event_time = datetime.fromisoformat(event["timestamp"])
                hour = event_time.hour
                hourly_data[hour].append(event)
            except:
                continue
        
        patterns = {
            "intersection_id": intersection_id,
            "analysis_period_hours": hours,
            "hourly_averages": {},
            "peak_hours": [],
            "off_peak_hours": []
        }
        
        # Calculate hourly averages
        hour_averages = {}
        for hour, hour_events in hourly_data.items():
            if hour_events:
                avg_vehicles = statistics.mean([e["vehicle_count"] for e in hour_events])
                avg_speed = statistics.mean([e["avg_speed"] for e in hour_events])
                avg_queue = statistics.mean([e["queue_len"] for e in hour_events])
                
                hour_averages[hour] = {
                    "vehicle_count": round(avg_vehicles, 1),
                    "avg_speed": round(avg_speed, 1),
                    "queue_length": round(avg_queue, 1),
                    "sample_count": len(hour_events)
                }
        
        patterns["hourly_averages"] = hour_averages
        
        # Identify peak and off-peak hours
        if hour_averages:
            sorted_hours = sorted(hour_averages.items(), key=lambda x: x[1]["vehicle_count"], reverse=True)
            total_hours = len(sorted_hours)
            peak_count = max(1, total_hours // 3)  # Top third are peak hours
            
            patterns["peak_hours"] = [hour for hour, data in sorted_hours[:peak_count]]
            patterns["off_peak_hours"] = [hour for hour, data in sorted_hours[-peak_count:]]
        
        return patterns