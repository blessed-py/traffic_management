from flask import Blueprint, request, jsonify
from datetime import datetime

from app.Database.database import add_event, get_recent_events
from app.WebSocket.events import broadcast_new_event

ingestion_bp = Blueprint("ingestion", __name__)


def _validate_event(payload: dict):
    required = ["intersection_id", "timestamp", "vehicle_count", "avg_speed", "queue_len"]
    missing = [k for k in required if k not in payload]
    if missing:
        return False, f"Missing fields: {', '.join(missing)}"
    try:
        # basic type/format checks
        datetime.fromisoformat(str(payload["timestamp"]))
        int(payload["vehicle_count"])  # will raise if not int-like
        float(payload["avg_speed"])    # will raise if not float-like
        int(payload["queue_len"])      # will raise if not int-like
    except Exception as e:
        return False, f"Invalid field types/format: {e}"
    return True, None


@ingestion_bp.route("/api/ingest", methods=["POST"])
def ingest():
    data = request.get_json(silent=True) or {}
    ok, err = _validate_event(data)
    if not ok:
        return jsonify({"status": "error", "error": err}), 400

    event = {
        "intersection_id": str(data["intersection_id"]),
        "timestamp": str(data["timestamp"]),  # store as ISO string
        "vehicle_count": int(data["vehicle_count"]),
        "avg_speed": float(data["avg_speed"]),
        "queue_len": int(data["queue_len"]),
        "meta": data.get("meta", {}),
    }
    stored = add_event(event)
    
    # Broadcast the new event to connected WebSocket clients
    broadcast_new_event(stored)
    
    return jsonify({"status": "ok", "id": stored["id"]}), 201


@ingestion_bp.route("/api/events", methods=["GET"])
def list_events():
    limit = request.args.get("limit", default=20, type=int)
    return jsonify({"events": get_recent_events(limit=limit)})
