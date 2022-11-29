import os
import tempfile
from urllib.parse import urlparse
import subprocess
import re

from .bimi import *
from .exception import *
from .utils import *

HERE = os.path.split(__file__)[0]
JING_JAR = os.path.join(HERE, 'jing.jar')
RNC_SCHEMA = os.path.join(HERE, 'SVG_PS-latest.rnc')

class SvgOptions:
    def __init__(self, httpTimeout=30, httpUserAgent='', maxSizeInBytes=0) -> None:
        self.httpTimeout = httpTimeout
        self.httpUserAgent = httpUserAgent
        self.maxSizeInBytes = maxSizeInBytes

class SvgValidator:
    def __init__(self, uri: str, opts: SvgOptions=SvgOptions()) -> None:
        self.uri = uri
        self.opts = opts

    def validate(self):
        url = urlparse(self.uri)
        if url is None:
            raise BimiFail('invalid Location URI')

        if url.scheme != 'https':
            raise BimiFail('the Location URI is not served by HTTPS')

        fd, path = tempfile.mkstemp(prefix='pybimi', suffix='.svg')
        try:
            with os.fdopen(fd, 'wb') as f:
                f.write(download(self.uri,
                                 self.opts.httpTimeout,
                                 self.opts.httpUserAgent,
                                 self.opts.maxSizeInBytes))
        except BimiFail as e:
            raise e
        except Exception as e:
            os.remove(path)
            raise BimiTempfail(e)

        try:
            cmd = ['java', '-jar', JING_JAR, '-c', RNC_SCHEMA, path]
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
                    raise BimiFail(matches[0][1])
                else:
                    raise BimiFail(line)
            else:
                raise BimiFail(out)

        os.remove(path)
