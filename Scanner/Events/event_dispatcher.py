"""
Simple Observer / EventDispatcher implementation.
Subscriptions are (event_name -> list of callables).
Thread-safe and lightweight.
"""
from threading import Lock
from typing import Callable, Any, Dict, List


class EventDispatcher:
    def __init__(self):
        self._listeners: Dict[str, List[Callable[..., None]]] = {}
        self._lock = Lock()

    def subscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        with self._lock:
            self._listeners.setdefault(event_name, []).append(callback)

    def unsubscribe(self, event_name: str, callback: Callable[..., None]) -> None:
        with self._lock:
            if event_name in self._listeners:
                try:
                    self._listeners[event_name].remove(callback)
                except ValueError:
                    pass

    def dispatch(self, event_name: str, *args, **kwargs) -> None:
        listeners = []
        with self._lock:
            listeners = list(self._listeners.get(event_name, []))
        for listener in listeners:
            try:
                listener(*args, **kwargs)
            except Exception:
                # Best-effort: listeners should handle their own errors
                continue
