from threading import Lock
from typing import List, Dict

_EVENTS: List[Dict] = []
_LOCK = Lock()
_NEXT_ID = 1


def add_event(event: Dict) -> Dict:
    """Add an event to the in-memory store and return the stored event with id."""
    global _NEXT_ID
    with _LOCK:
        event_with_id = dict(event)
        event_with_id["id"] = _NEXT_ID
        _NEXT_ID += 1
        _EVENTS.append(event_with_id)
        return event_with_id


def get_recent_events(limit: int = 20) -> List[Dict]:
    """Return the most recent events up to limit, newest first."""
    with _LOCK:
        return list(reversed(_EVENTS))[: max(0, int(limit))]


def clear_events():
    """Utility to clear all events (useful for tests)."""
    global _EVENTS, _NEXT_ID
    with _LOCK:
        _EVENTS = []
        _NEXT_ID = 1
