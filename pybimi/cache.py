from threading import Lock
from typing import Any, Tuple
from cachetools import TTLCache

class Cache:
    """
    Thread-safe cache wrapper with TTL (Time To Live) functionality.

    This cache provides thread-safe access to a time-based cache with
    automatic expiration of entries after a specified time period.

    Attributes:
        cache: TTLCache instance for storing cached data
        lock: Threading lock for thread-safe operations
    """

    def __init__(self, maxsize: int = 100, ttl: int = 1800) -> None:
        """
        Initialize cache with specified capacity and TTL.

        Args:
            maxsize: Maximum number of entries to store
            ttl: Time to live in seconds (default: 30 minutes)
        """
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = Lock()

    def set(self, key: str, value: Any) -> None:
        """
        Store a key-value pair in the cache.

        Args:
            key: Cache key identifier
            value: Value to store (any serializable object)
        """

        with self.lock:
            self.cache[key] = value

    def get(self, key: str) -> Tuple[bool, Any]:
        """
        Retrieve a value from the cache.

        Args:
            key: Cache key identifier

        Returns:
            Tuple of (exists, value) where exists is True if key found,
            and value is the stored data or None if not found
        """

        if key in self.cache:
            with self.lock:
                if key in self.cache:  # Double-check after acquiring lock
                    return (True, self.cache[key])

        return (False, None)
