from threading import Lock
from cachetools import TTLCache

class Cache():
    """
    A class used to wrap cachetools.TTLCache

    Attributes
    ----------
    cache: cachetools.TTLCache
        cachetools.TTLCache object
    lock: threading.Lock
        A lock
    """

    def __init__(self, maxsize: int=100, ttl: int=1800) -> None:
        self.cache = TTLCache(maxsize=maxsize, ttl=ttl)
        self.lock = Lock()

    def set(self, key: str, value: any):
        """
        Save to cache

        Parameters
        ----------
        key: str
            A key
        value: any
            A value
        """

        if self.cache is not None:
            with self.lock:
                self.cache[key] = value

    def get(self, key: str):
        """
        Get from cache

        Parameters
        ----------
        key: str
            A key

        Returns
        -------
        existing: bool
            Whether the key exists in cache
        value: any
            Corresponding value in cache of the key
        """

        if self.cache is not None and \
           key in self.cache:
            with self.lock:
                return (True, self.cache[key])

        return (False, None)
