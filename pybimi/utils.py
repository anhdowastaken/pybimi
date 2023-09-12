import requests
import hashlib
from urllib.parse import urlparse

from .exception import BimiFail, BimiTempfail
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

        BimiTempfail

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
    resp = requests.get(uri,
                        stream=True,
                        timeout=timeout,
                        headers=headers)

    if resp.status_code != 200:
        raise BimiTempfail('{} {}'.format(resp.status_code, resp.reason))

    data = None
    if maxSizeInBytes > 0:
        if int(resp.headers.get('Content-Length', 0)) > maxSizeInBytes:
            raise BimiFail('downloaded data is bigger than {} bytes'.format(maxSizeInBytes))

        body = []
        length = 0
        for chunk in resp.iter_content(1024):
            body.append(chunk)
            length += len(chunk)
            if length > maxSizeInBytes:
                raise BimiFail('downloaded data is bigger than {} bytes'.format(maxSizeInBytes))

        data = b''.join(body)

    else:
        data = resp.content

    # Cache
    if cache is not None:
        cache.set(key, data)

    return data

def getData(uri: str,
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

        BimiTempfail

    """

    url = urlparse(uri)
    if url is None:
        return None

    local_file = False
    if url.scheme == '':
        local_file = True

    elif url.scheme in ('http', 'https'):
        pass

    else:
        return None

    if local_file:
        try:
            with open(uri, 'rb') as f:
                return f.read()
        except Exception as e:
            raise BimiTempfail(e)

    return download(uri, timeout, userAgent, maxSizeInBytes, cache)
