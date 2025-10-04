from flask import Blueprint, render_template, jsonify
import os
import random
from datetime import datetime

from app.Database.encrypter import Cryptography
from app.API.SMTP import MAIL_SERVER
from app.Database.database import get_recent_events, add_event
from app.Analytics.traffic_analytics import TrafficAnalytics

# Blueprint initialization
dashboard_bp = Blueprint('dashboard', __name__, template_folder='templates')

# Initialize components
cryptographer = Cryptography()
mail_server = MAIL_SERVER()
analytics = TrafficAnalytics()

# Global variable to store socketio instance (will be set from manage.py)
socketio_instance = None

def set_socketio(socketio):
    """Set the SocketIO instance for real-time updates."""
    global socketio_instance
    socketio_instance = socketio

@dashboard_bp.route('/')
def index():
    events = get_recent_events(limit=20)
    # Get current analytics
    current_analysis = analytics.analyze_current_conditions(limit=50)
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY", "")
    return render_template("index.html", 
                            events=events,
                            analysis=current_analysis,
                            google_maps_api_key=google_maps_api_key
                            )

@dashboard_bp.route('/api/analytics')
def get_analytics():
    """Get current traffic analytics."""
    analysis = analytics.analyze_current_conditions(limit=100)
    return jsonify(analysis)

@dashboard_bp.route('/api/intersection/<intersection_id>/patterns')
def get_intersection_patterns(intersection_id):
    """Get traffic patterns for a specific intersection."""
    patterns = analytics.get_intersection_patterns(intersection_id)
    return jsonify(patterns)

@dashboard_bp.route('/api/demo/generate')
def generate_demo_data():
    """Generate demo traffic data for testing."""
    # Generate sample data for different intersections (Punjab NH44 corridor)
    intersections = ['INT001', 'INT002', 'INT003', 'INT004', 'INT005']
    # Approximate coordinates along NH44 in Punjab
    nh44_coords = {
        'INT001': {"lat": 31.3260, "lng": 75.5762, "city": "Jalandhar"},
        'INT002': {"lat": 30.900965, "lng": 75.857277, "city": "Ludhiana"},
        'INT003': {"lat": 31.2240, "lng": 75.7695, "city": "Phagwara"},
        'INT004': {"lat": 32.2643, "lng": 75.6421, "city": "Pathankot"},
        'INT005': {"lat": 30.7046, "lng": 76.2230, "city": "Khanna"},
    }
    
    for intersection_id in intersections:
        # Generate realistic traffic data
        base_vehicles = random.randint(5, 20)
        base_speed = random.randint(25, 55)
        base_queue = random.randint(0, 12)
        
        # Add some congestion scenarios
        if random.random() < 0.3:  # 30% chance of congestion
            base_vehicles = random.randint(15, 25)
            base_speed = random.randint(10, 25)
            base_queue = random.randint(8, 15)
        
        meta_extra = nh44_coords.get(intersection_id, {})
        event = {
            "intersection_id": intersection_id,
            "timestamp": datetime.now().isoformat(),
            "vehicle_count": base_vehicles,
            "avg_speed": base_speed,
            "queue_len": base_queue,
            "meta": {
                "source": "demo_generator",
                "highway": "NH44",
                "region": "Punjab",
                "city": meta_extra.get("city"),
                "lat": meta_extra.get("lat"),
                "lng": meta_extra.get("lng")
            }
        }
        
        add_event(event)
    
    return jsonify({"status": "ok", "message": f"Generated demo data for {len(intersections)} intersections"})

@dashboard_bp.route('/api/highway/<highway_id>/summary')
def highway_summary(highway_id):
    """Return summary analytics for a specific highway corridor (e.g., NH44)."""
    # Pull a reasonable window
    events = get_recent_events(limit=200)
    # Filter by highway tag in meta
    corridor_events = [e for e in events if isinstance(e.get('meta'), dict) and e['meta'].get('highway') == highway_id]
    if not corridor_events:
        return jsonify({
            "status": "no_data",
            "highway": highway_id,
            "intersections": {},
            "overall": {}
        })

    # Group by intersection
    by_intersection = {}
    for e in corridor_events:
        iid = e['intersection_id']
        by_intersection.setdefault(iid, []).append(e)

    def congestion_level(vc, spd, ql):
        score = 0
        if vc >= 15: score += 2
        elif vc >= 11: score += 1
        if spd <= 20: score += 2
        elif spd <= 30: score += 1
        if ql >= 8: score += 2
        elif ql >= 5: score += 1
        return 'high' if score >= 4 else ('moderate' if score >= 2 else 'low')

    summary = {"intersections": {}, "alerts": []}
    congested = 0
    for iid, lst in by_intersection.items():
        latest = lst[0]
        lvl = congestion_level(latest['vehicle_count'], latest['avg_speed'], latest['queue_len'])
        if lvl == 'high':
            congested += 1
        summary["intersections"][iid] = {
            "latest": latest,
            "congestion_level": lvl,
            "city": (latest.get('meta') or {}).get('city')
        }

    total = len(by_intersection)
    overall = {
        "total_intersections": total,
        "congested": congested,
        "congestion_rate": (congested / total) if total else 0,
        "timestamp": datetime.now().isoformat(),
        "highway": highway_id
    }

    return jsonify({"status": "ok", "highway": highway_id, "summary": summary, "overall": overall})

# WebSocket event handlers will be registered separately
