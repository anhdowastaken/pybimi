import os
import tempfile
from urllib.parse import urlparse
import subprocess
import re
from xml.dom import minidom

from .bimi import *
from .exception import *
from .utils import *
from .options import *
from .cache import *

class Indicator:
    """
    A class used to represent a SVG

    Attributes
    ----------
    title: str
    size: int
        Size in bytes
    version: str
    baseProfile: str
    """

    def __init__(self, title: str,
                       size: int,
                       version: str,
                       baseProfile: str) -> None:
        self.title = title
        self.size = size
        self.version = version
        self.baseProfile = baseProfile

    def __repr__(self) -> str:
        return str(self.__dict__)

class IndicatorValidator:
    """
    A class used to validate a BIMI indicator

    Attributes
    ----------
    uri: str
        URI of the BIMI indicator
    opts: IndicatorOptions
        Indicator validation options
    httpOpts: HttpOptions
        HTTP options
    cache: Cache
        Cache

    Methods
    -------
    validate()
        Validate the BIMI indicator
    """

    def __init__(self, uri: str,
                       opts: IndicatorOptions=IndicatorOptions(),
                       httpOpts: HttpOptions=HttpOptions(),
                       cache: Cache=None) -> None:
        self.uri = uri
        self.opts = opts
        self.httpOpts = httpOpts
        self.cache = cache

    def _saveValidationResultToCache(self, key: str, value: Exception):
        """
        Save validation result to cache

        Parameters
        ----------
        key: str
            A key
        value: Exception
            An exception
        """

        if self.cache is not None:
            self.cache.set(key, value)

    def validate(self) -> Indicator:
        """
        Validate the BIMI indicator. The indicator is downloaded from the URI
        with some HTTP options. If the indicator is downloaded successfully, it
        will be validated by some validation options.

        Returns
        -------
        Indicator

        Raises
        ------
        BimiFail

        BimiTempfail
        """

        # SVG information holder
        i = None

        h = hashlib.new('md5')
        h.update(self.uri.encode())
        key = 'bimi_indicator_validation_result_{}'.format(h.hexdigest())
        # Find validation result in cache
        if self.cache is not None:
            found, e = self.cache.get(key)
            if found:
                # print('Found {} in cache'.format(key))
                if e is None:
                    return i
                else:
                    raise e

        url = urlparse(self.uri)
        if url is None:
            e = BimiFail('invalid SVG URI')
            self._saveValidationResultToCache(key, e)
            raise e

        if url.scheme != '' and url.scheme != 'https':
            e = BimiFail('the SVG URI is not served by HTTPS')
            self._saveValidationResultToCache(key, e)
            raise e

        fd, path = tempfile.mkstemp(prefix='pybimi', suffix='.svg')
        try:
            with os.fdopen(fd, 'wb') as f:
                indicatorData = getData(self.uri,
                                        self.httpOpts.httpTimeout,
                                        self.httpOpts.httpUserAgent,
                                        self.opts.maxSizeInBytes,
                                        self.cache)
                f.write(indicatorData)

        except BimiFail as e:
            os.remove(path)
            self._saveValidationResultToCache(key, e)
            raise e

        except Exception as e:
            os.remove(path)
            raise BimiTempfail(e)

        i = self._extractSVG(path)

        try:
            cmd = [self.opts.javaPath, '-jar', self.opts.jingJarPath, '-c', self.opts.rncSchemaPath, path]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            os.remove(path)
            raise BimiTempfail(e)

        if proc.returncode != 0:
            out = proc.stdout.decode() + proc.stderr.decode()
            lines = out.split('\n')
            if len(lines) > 0:
                line = lines[0]
                pattern = '.+:\d+:\d+:\s+(error|fatal):\s+(.+)'
                matches = re.findall(pattern, line)
                if len(matches) > 0:
                    os.remove(path)
                    e = BimiFail(matches[0][1])
                    self._saveValidationResultToCache(key, e)
                    raise e

                else:
                    os.remove(path)
                    e = BimiFail(line)
                    self._saveValidationResultToCache(key, e)
                    raise e

            else:
                os.remove(path)
                e = BimiFail(out)
                self._saveValidationResultToCache(key, e)
                raise e

        os.remove(path)

        self._saveValidationResultToCache(key, None)
        return i

    def _extractSVG(self, path: str) -> Indicator:
        """
        Extract SVG information from the indicator downloaded from internet

        Parameters
        ----------
        path: str
            Local path of the downloaded indicator

        Returns
        -------
        Indicator
        """

        try:
            doc = minidom.parse(path)
            svg = doc.getElementsByTagName('svg')[0].attributes.items()
            title = doc.getElementsByTagName('title')[0].firstChild.nodeValue
            i = Indicator(title=title,
                          size=os.path.getsize(path),
                          version='',
                          baseProfile='')
            for item in svg:
                if item[0] == 'version':
                    i.version = item[1]
                elif item[0] == 'baseProfile':
                    i.baseProfile = item[1]

            return i

        except:
            return None

