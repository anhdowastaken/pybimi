import os
import requests
import hashlib
from urllib.parse import urlparse

from .exception import *
from .cache import Cache

def download(uri: str,
             timeout: int=30,
             userAgent: str='',
             maxSizeInBytes: int=0,
             cache: Cache=None) -> bytes:
    """
    Download a thing from internet via its URI

    Parameters
    ----------
    uri: str
        An URI
    timeout: int=30
        HTTP timeout
    userAgent: str=''
        HTTP User Agent
    maxSizeInBytes: int=0
        Maximum size in bytes or BimiFail will be raised
    cache: Cache=None
        Cache

    Returns
    -------
    bytes:
        Data in bytes

    Raises
    ------
        BimiFail

        BimiTemfailCannotAccess

    """

    h = hashlib.new('md5')
    h.update(uri.encode())
    key = 'bimi_downloaded_data_{}'.format(h.hexdigest())
    # Find downloaded data in cache
    if cache is not None:
        # print('Found {} in cache'.format(key))
        found, data = cache.get(key)
        if found:
            return data

    headers = {'User-Agent': userAgent}
    try:
        resp = requests.get(uri,
                            stream=True,
                            timeout=timeout,
                            headers=headers)
        resp.raise_for_status()

        data = None
        if maxSizeInBytes > 0:
            if int(resp.headers.get('Content-Length', 0)) > maxSizeInBytes:
                raise BimiFailSizeLimitExceeded('downloaded data is bigger than {} bytes'.format(maxSizeInBytes))

            body = []
            length = 0
            for chunk in resp.iter_content(1024):
                body.append(chunk)
                length += len(chunk)
                if length > maxSizeInBytes:
                    raise BimiFailSizeLimitExceeded('downloaded data is bigger than {} bytes'.format(maxSizeInBytes))

            data = b''.join(body)

        else:
            data = resp.content

        # Cache
        if cache is not None:
            cache.set(key, data)

        return data

    except requests.exceptions.RequestException as e:
        raise BimiTemfailCannotAccess(str(e))

def getData(uri: str,
            localFile: bool=False,
            timeout: int=30,
            userAgent: str='',
            maxSizeInBytes: int=0,
            cache: Cache=None) -> bytes:
    """
    Get a thing via its URI. It can be a local file or an Internet thing.

    Parameters
    ----------
    uri: str
        An URI
    localFile: bool=False
        If set, it means the uri is a local file path
    timeout: int=30
        HTTP timeout
    userAgent: str=''
        HTTP User Agent
    maxSizeInBytes: int=0
        Maximum size in bytes or BimiFail will be raised
    cache: Cache=None
        Cache

    Returns
    -------
    bytes:
        Data in bytes

    Raises
    ------
        BimiFail

        BimiTemfailCannotAccess

    """

    if localFile:
        try:
            if maxSizeInBytes > 0 and os.stat(uri).st_size > maxSizeInBytes:
                raise BimiFailSizeLimitExceeded('data size is bigger than {} bytes'.format(maxSizeInBytes))

            with open(uri, 'rb') as f:
                return f.read()
        except Exception as e:
            raise BimiTemfailCannotAccess(str(e))

    else:
        url = urlparse(uri)
        if url is None:
            return None

        if url.scheme not in ('http', 'https'):
            return None

    return download(uri, timeout, userAgent, maxSizeInBytes, cache)
