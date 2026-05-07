import time
from typing import Any, Dict, Optional, Tuple


class TTLCache:
    def __init__(self) -> None:
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        if key not in self._store:
            return None
        expires_at, value = self._store[key]
        if expires_at < time.time():
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ttl_seconds: int) -> None:
        self._store[key] = (time.time() + ttl_seconds, value)


cache = TTLCache()
