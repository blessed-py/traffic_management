from flask import Flask
from flask_socketio import SocketIO
from app.Blueprints.Dashboard.dashboard import dashboard_bp
from app.Blueprints.Ingestion.ingestion import ingestion_bp
from app.WebSocket.events import init_websocket_events, simulate_live_traffic

#from app.Database.database import DatabaseManager

# Initialize the database
#db_manager = DatabaseManager()
#db_manager.initialize()

app = Flask(__name__, static_folder='app/static/')
app.config['SECRET_KEY'] = 'JKKEBJKBJRBKJR,BLKJRCBLKJCRL4Y4479272949474JBCKEHCEV'

# Initialize SocketIO for real-time features
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize WebSocket event handlers
init_websocket_events(socketio)


# Blueprint registration

app.register_blueprint(dashboard_bp)
app.register_blueprint(ingestion_bp)




# Main route
if __name__ == '__main__':
    # Start live traffic simulation for demo
    simulate_live_traffic()
    socketio.run(app, debug=True, host='0.0.0.0', port=1122)
