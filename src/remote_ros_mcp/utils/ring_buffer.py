"""Thread-safe ring buffer for caching recent ROS2 topic messages."""

import collections
import threading
import time
from typing import Any, Dict, List, Optional


class TopicRingBuffer:
    """Fixed-capacity buffer storing the latest N messages of a topic."""

    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self._buffer: collections.deque[Dict[str, Any]] = collections.deque(maxlen=capacity)
        self._lock = threading.Lock()
        self._last_received_time: float = 0.0

    def add(self, message: Dict[str, Any]):
        with self._lock:
            ts = float(time.time())
            entry = {
                "timestamp": ts,
                "data": message,
            }
            self._buffer.append(entry)
            self._last_received_time = ts

    def get_latest(self) -> Optional[Dict[str, Any]]:
        with self._lock:
            if not self._buffer:
                return None
            return self._buffer[-1]

    def get_all(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._buffer)

    def count(self) -> int:
        with self._lock:
            return len(self._buffer)

    def last_received_time(self) -> float:
        with self._lock:
            return self._last_received_time

    def clear(self):
        with self._lock:
            self._buffer.clear()
            self._last_received_time = 0.0
