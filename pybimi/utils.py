import requests
import hashlib
from cachetools import TTLCache

from .exception import BimiFail

def download(uri: str,
             timeout: int=30,
             userAgent: str='',
             maxSizeInBytes: int=0,
             cache: TTLCache=None) -> bytes:
    h = hashlib.new('md5')
    h.update(uri.encode())
    key = 'bimi_downloaded_data_{}'.format(h.hexdigest())
    if cache is not None and \
       key in cache and \
       cache[key]:
        print('Found {} in cache'.format(key))
        return cache[key]

    headers = {'User-Agent': userAgent}
    resp = requests.get(uri,
                        stream=True,
                        timeout=timeout,
                        headers=headers)

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
        cache[key] = data

    return data
