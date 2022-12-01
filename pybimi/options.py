import os
from .bimi import *

HERE = os.path.split(__file__)[0]
JAVA = 'java'
JING_JAR = os.path.join(HERE, 'jing.jar')
RNC_SCHEMA = os.path.join(HERE, 'SVG_PS-latest.rnc')

class HttpOptions:
    def __init__(self, httpTimeout: int=30, httpUserAgent: str='') -> None:
        self.httpTimeout = httpTimeout
        self.httpUserAgent = httpUserAgent

class LookupOptions:
    def __init__(self, selector: str=DEFAULT_SELECTOR) -> None:
        self.selector = selector

class IndicatorOptions:
    def __init__(self, maxSizeInBytes: int=0,
                       httpOpts: HttpOptions=HttpOptions(),
                       javaPath: str=JAVA,
                       jingJarPath: str=JING_JAR,
                       rncSchemaPath: str=RNC_SCHEMA) -> None:
       self.maxSizeInBytes = maxSizeInBytes
       self.httpOpts = httpOpts
       self.javaPath = javaPath
       self.jingJarPath = jingJarPath
       self.rncSchemaPath = rncSchemaPath

class VmcOptions:
    def __init__(self, maxSizeInBytes: int=0,
                       verifyDNSName: bool=True,
                       revocationCheckAndOscpCheck: bool=False,
                       httpOpts=HttpOptions(),
                       indicatorOpts=IndicatorOptions()) -> None:
        self.maxSizeInBytes = maxSizeInBytes
        self.verifyDNSName = verifyDNSName
        self.revocationCheckAndOscpCheck = revocationCheckAndOscpCheck
        self.httpOpts = httpOpts
        self.indicatorOpts = indicatorOpts
