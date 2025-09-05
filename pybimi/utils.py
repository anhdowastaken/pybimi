import os
from typing import Optional, Tuple
import requests
import hashlib
from urllib.parse import urlparse

from .exception import (
    BimiFail, BimiFailSizeLimitExceeded, BimiTemfailCannotAccess
)
from .cache import Cache

def download(uri: str,
             timeout: int = 30,
             userAgent: str = '',
             maxSizeInBytes: int = 0,
             cache: Optional[Cache] = None) -> bytes:
    """
    Download content from a URI with size limits and caching support.

    Args:
        uri: URL to download from
        timeout: HTTP request timeout in seconds
        userAgent: HTTP User-Agent header value
        maxSizeInBytes: Maximum allowed content size (0 = unlimited)
        cache: Optional cache instance for performance

    Returns:
        Downloaded content as bytes

    Raises:
        BimiFail: Invalid URI or other download failure
        BimiFailSizeLimitExceeded: Content exceeds size limit
        BimiTemfailCannotAccess: Network/HTTP error
    """

    # Generate cache key from URI hash
    uri_hash = hashlib.md5(uri.encode('utf-8')).hexdigest()
    cache_key = f'bimi_downloaded_data_{uri_hash}'
    # Check cache for existing download
    if cache is not None:
        found, cached_data = cache.get(cache_key)
        if found:
            return cached_data

    headers = {'User-Agent': userAgent}
    try:
        resp = requests.get(uri,
                            stream=True,
                            timeout=timeout,
                            headers=headers)
        resp.raise_for_status()

        # Handle size-limited downloads
        if maxSizeInBytes > 0:
            # Check Content-Length header first
            content_length = int(resp.headers.get('Content-Length', 0))
            if content_length > maxSizeInBytes:
                raise BimiFailSizeLimitExceeded(
                    f'Content size {content_length} exceeds limit {maxSizeInBytes} bytes'
                )

            # Stream download with size checking
            chunks = []
            total_size = 0
            chunk_size = min(1024, maxSizeInBytes)  # Adaptive chunk size

            for chunk in resp.iter_content(chunk_size):
                chunks.append(chunk)
                total_size += len(chunk)
                if total_size > maxSizeInBytes:
                    raise BimiFailSizeLimitExceeded(
                        f'Downloaded data size {total_size} exceeds limit {maxSizeInBytes} bytes'
                    )

            data = b''.join(chunks)
        else:
            data = resp.content

        # Store in cache for future requests
        if cache is not None:
            cache.set(cache_key, data)

        return data

    except requests.exceptions.RequestException as e:
        raise BimiTemfailCannotAccess(str(e))

def getData(uri: str,
            localFile: bool = False,
            timeout: int = 30,
            userAgent: str = '',
            maxSizeInBytes: int = 0,
            cache: Optional[Cache] = None) -> bytes:
    """
    Retrieve content from either a local file or remote URL.

    Args:
        uri: File path or URL to retrieve
        localFile: Whether uri is a local file path
        timeout: HTTP request timeout in seconds
        userAgent: HTTP User-Agent header value
        maxSizeInBytes: Maximum allowed content size (0 = unlimited)
        cache: Optional cache instance

    Returns:
        Content as bytes

    Raises:
        BimiFail: Invalid URI or file access error
        BimiFailSizeLimitExceeded: Content exceeds size limit
        BimiTemfailCannotAccess: File/network access error
    """

    if localFile:
        try:
            # Check file size before reading
            if maxSizeInBytes > 0:
                file_size = os.stat(uri).st_size
                if file_size > maxSizeInBytes:
                    raise BimiFailSizeLimitExceeded(
                        f'File size {file_size} exceeds limit {maxSizeInBytes} bytes'
                    )

            with open(uri, 'rb') as f:
                return f.read()
        except OSError as e:
            raise BimiTemfailCannotAccess(f'File access error: {e}')
        except Exception as e:
            raise BimiTemfailCannotAccess(f'Unexpected error: {e}')

    # Handle remote URLs
    parsed_url = urlparse(uri)
    if not parsed_url.scheme or parsed_url.scheme not in ('http', 'https'):
        raise BimiFail(f'Invalid or unsupported URI scheme: {uri}')

    return download(uri, timeout, userAgent, maxSizeInBytes, cache)
