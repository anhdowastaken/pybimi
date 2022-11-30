from threading import Lock
from cachetools import TTLCache

class Cache():
    def __init__(self, maxsize: int=100, ttl: int=1800) -> None:
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = Lock()

    def set(self, key: str, value: any):
        if self.cache is not None:
            with self.lock:
                self.cache[key] = value

    def get(self, key: str):
        if self.cache is not None and \
           key in self.cache:
            with self.lock:
                return (True, self.cache[key])

        return (False, None)
