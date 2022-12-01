import os
import tempfile
from urllib.parse import urlparse
import subprocess
import re

from .bimi import *
from .exception import *
from .utils import *
from .options import *
from .cache import *

class IndicatorValidator:
    def __init__(self, uri: str,
                       opts: IndicatorOptions=IndicatorOptions(),
                       httpOpts: HttpOptions=HttpOptions(),
                       cache: Cache=None) -> None:
        self.uri = uri
        self.opts = opts
        self.httpOpts = httpOpts
        self.cache = cache

    def _saveValidationResultToCache(self, key: str, value: Exception):
        if self.cache is not None:
            self.cache.set(key, value)

    def validate(self):
        h = hashlib.new('md5')
        h.update(self.uri.encode())
        key = 'bimi_indicator_validation_result_{}'.format(h.hexdigest())
        # Find validation result in cache
        if self.cache is not None:
            found, e = self.cache.get(key)
            if found:
                # print('Found {} in cache'.format(key))
                if e is None:
                    return
                else:
                    raise e

        url = urlparse(self.uri)
        if url is None:
            e = BimiFail('invalid Location URI')
            self._saveValidationResultToCache(key, e)
            raise e

        if url.scheme != 'https':
            e = BimiFail('the Location URI is not served by HTTPS')
            self._saveValidationResultToCache(key, e)
            raise e

        fd, path = tempfile.mkstemp(prefix='pybimi', suffix='.svg')
        try:
            with os.fdopen(fd, 'wb') as f:
                indicatorData = download(self.uri,
                                         self.httpOpts.httpTimeout,
                                         self.httpOpts.httpUserAgent,
                                         self.opts.maxSizeInBytes,
                                         self.cache)
                f.write(indicatorData)

        except BimiFail as e:
            self._saveValidationResultToCache(key, e)
            raise e

        except Exception as e:
            os.remove(path)
            e = BimiTempfail(e)
            self._saveValidationResultToCache(key, e)
            raise e

        try:
            cmd = [self.opts.javaPath, '-jar', self.opts.jingJarPath, '-c', self.opts.rncSchemaPath, path]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            os.remove(path)
            e = BimiTempfail(e)
            self._saveValidationResultToCache(key, e)
            raise e

        if proc.returncode != 0:
            out = proc.stdout.decode() + proc.stderr.decode()
            lines = out.split('\n')
            if len(lines) > 0:
                line = lines[0]
                pattern = '.+:\d+:\d+:\s+(error|fatal):\s+(.+)'
                matches = re.findall(pattern, line)
                if len(matches) > 0:
                    e = BimiFail(matches[0][1])
                    self._saveValidationResultToCache(key, e)
                    raise e

                else:
                    e = BimiFail(line)
                    self._saveValidationResultToCache(key, e)
                    raise e

            else:
                e = BimiFail(out)
                self._saveValidationResultToCache(key, e)
                raise e

        os.remove(path)

        self._saveValidationResultToCache(key, None)
