"""
Simple thread-safe Singleton metaclass to ensure a class has only one instance.
"""
from threading import Lock
from typing import Type, Dict, Any


class Singleton(type):
    _instances: Dict[Type, Any] = {}
    _lock: Lock = Lock()

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            with cls._lock:
                if cls not in cls._instances:
                    cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
