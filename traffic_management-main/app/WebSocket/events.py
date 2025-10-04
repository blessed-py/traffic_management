from flask_socketio import emit, join_room, leave_room
from flask import request
from threading import Timer
import random
from datetime import datetime

from app.Database.database import get_recent_events, add_event
from app.Analytics.traffic_analytics import TrafficAnalytics

# Global variables for managing real-time updates
socketio_instance = None
update_timers = {}
analytics = TrafficAnalytics()

def init_websocket_events(socketio):
    """Initialize WebSocket event handlers."""
    global socketio_instance
    socketio_instance = socketio
    
    @socketio.on('connect')
    def on_connect():
        """Handle client connection."""
        print(f"Client connected: {request.sid}")
        # Send initial data
        events = get_recent_events(limit=20)
        analysis = analytics.analyze_current_conditions(limit=50)
        
        emit('initial_data', {
            'events': events,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        })
    
    @socketio.on('disconnect')
    def on_disconnect():
        """Handle client disconnection."""
        print(f"Client disconnected: {request.sid}")
        # Clean up any timers for this client
        if request.sid in update_timers:
            update_timers[request.sid].cancel()
            del update_timers[request.sid]
    
    @socketio.on('subscribe_updates')
    def on_subscribe_updates(data=None):
        """Subscribe client to real-time traffic updates."""
        print(f"Client {request.sid} subscribed to updates")
        join_room('traffic_updates')
        
        # Start sending periodic updates
        start_periodic_updates()
        
        emit('subscription_confirmed', {
            'status': 'subscribed',
            'update_interval': 10  # seconds
        })
    
    @socketio.on('unsubscribe_updates') 
    def on_unsubscribe_updates():
        """Unsubscribe client from updates."""
        print(f"Client {request.sid} unsubscribed from updates")
        leave_room('traffic_updates')
        
        emit('subscription_confirmed', {
            'status': 'unsubscribed'
        })
    
    @socketio.on('request_intersection_details')
    def on_request_intersection_details(data):
        """Send detailed information for a specific intersection."""
        intersection_id = data.get('intersection_id')
        if not intersection_id:
            emit('error', {'message': 'Missing intersection_id'})
            return
            
        patterns = analytics.get_intersection_patterns(intersection_id)
        recent_events = [e for e in get_recent_events(50) if e['intersection_id'] == intersection_id]
        
        emit('intersection_details', {
            'intersection_id': intersection_id,
            'patterns': patterns,
            'recent_events': recent_events[:10],
            'timestamp': datetime.now().isoformat()
        })
    
    @socketio.on('generate_test_event')
    def on_generate_test_event(data):
        """Generate a test traffic event for demonstration."""
        intersection_id = data.get('intersection_id', 'TEST001')
        
        # Generate realistic test data
        test_event = {
            "intersection_id": intersection_id,
            "timestamp": datetime.now().isoformat(),
            "vehicle_count": random.randint(5, 25),
            "avg_speed": random.randint(15, 60),
            "queue_len": random.randint(0, 15),
            "meta": {"source": "websocket_test"}
        }
        
        # Add to database
        stored_event = add_event(test_event)
        
        # Broadcast to all subscribers
        socketio.emit('traffic_update', {
            'type': 'new_event',
            'event': stored_event,
            'timestamp': datetime.now().isoformat()
        }, room='traffic_updates')
        
        # Send confirmation to requester
        emit('test_event_created', {
            'event': stored_event,
            'message': 'Test event generated successfully'
        })

def start_periodic_updates():
    """Start periodic traffic updates broadcast."""
    def send_update():
        if socketio_instance:
            # Get latest analytics
            analysis = analytics.analyze_current_conditions(limit=100)
            recent_events = get_recent_events(limit=10)
            
            # Broadcast to all subscribed clients
            socketio_instance.emit('traffic_update', {
                'type': 'periodic_update',
                'analysis': analysis,
                'recent_events': recent_events,
                'timestamp': datetime.now().isoformat()
            }, room='traffic_updates')
            
            # Check for critical alerts
            if analysis.get('alerts'):
                critical_alerts = [alert for alert in analysis['alerts'] if alert['severity'] == 'high']
                if critical_alerts:
                    socketio_instance.emit('critical_alert', {
                        'alerts': critical_alerts,
                        'timestamp': datetime.now().isoformat()
                    }, room='traffic_updates')
        
        # Schedule next update
        Timer(10.0, send_update).start()  # Update every 10 seconds
    
    # Start the update cycle
    send_update()

def broadcast_new_event(event):
    """Broadcast a new traffic event to all connected clients."""
    if socketio_instance:
        # Get updated analytics after new event
        analysis = analytics.analyze_current_conditions(limit=50)
        
        socketio_instance.emit('traffic_update', {
            'type': 'new_event',
            'event': event,
            'analysis': analysis,
            'timestamp': datetime.now().isoformat()
        }, room='traffic_updates')

def simulate_live_traffic():
    """Simulate live traffic data for demonstration."""
    intersections = ['INT001', 'INT002', 'INT003', 'INT004', 'INT005']
    
    def generate_random_event():
        intersection_id = random.choice(intersections)
        
        # Generate realistic data with some variation
        current_hour = datetime.now().hour
        is_peak_hour = current_hour in [7, 8, 9, 17, 18, 19]  # Rush hours
        
        if is_peak_hour:
            base_vehicles = random.randint(12, 25)
            base_speed = random.randint(15, 35)
            base_queue = random.randint(5, 15)
        else:
            base_vehicles = random.randint(3, 15)
            base_speed = random.randint(30, 60)
            base_queue = random.randint(0, 8)
        
        # Add random incidents (5% chance)
        if random.random() < 0.05:
            base_vehicles = random.randint(20, 30)
            base_speed = random.randint(5, 15)
            base_queue = random.randint(10, 20)
        
        event = {
            "intersection_id": intersection_id,
            "timestamp": datetime.now().isoformat(),
            "vehicle_count": base_vehicles,
            "avg_speed": base_speed,
            "queue_len": base_queue,
            "meta": {"source": "live_simulation"}
        }
        
        # Add to database
        stored_event = add_event(event)
        
        # Broadcast to connected clients
        broadcast_new_event(stored_event)
        
        # Schedule next event (15-45 seconds)
        Timer(random.uniform(15, 45), generate_random_event).start()
    
    # Start simulation
    generate_random_event()