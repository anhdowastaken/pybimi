import requests

from .exception import BimiFail

def download(uri: str, timeout: int=30, userAgent: str='', maxSizeInBytes: int=0) -> bytes:
    headers = {'User-Agent': userAgent}
    resp = requests.get(uri,
                        stream=True,
                        timeout=timeout,
                        headers=headers)

    if maxSizeInBytes > 0:
        if int(resp.headers.get('Content-Length', 0)) > maxSizeInBytes:
            raise BimiFail('downloaded data is bigger than {} bytes'.format(maxSizeInBytes))

        data = []
        length = 0
        for chunk in resp.iter_content(1024):
            data.append(chunk)
            length += len(chunk)
            if length > maxSizeInBytes:
                raise BimiFail('downloaded data is bigger than {} bytes'.format(maxSizeInBytes))

        return b''.join(data)

    else:
        return resp.content

    # TODO: Cache
