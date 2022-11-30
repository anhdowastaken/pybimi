from .bimi import *

class HttpOptions:
    def __init__(self, httpTimeout: int=30, httpUserAgent: str='') -> None:
        self.httpTimeout = httpTimeout
        self.httpUserAgent = httpUserAgent

class LookupOptions:
    def __init__(self, selector: str=DEFAULT_SELECTOR) -> None:
        self.selector = selector

class IndicatorOptions:
    def __init__(self, maxSizeInBytes=0, httpOpts=HttpOptions()) -> None:
       self.maxSizeInBytes = maxSizeInBytes
       self.httpOtps = httpOpts

class VmcOptions:
    def __init__(self, maxSizeInBytes=0,
                       verifyDNSName=True,
                       revocationCheckAndOscpCheck=False,
                       httpOtps=HttpOptions(),
                       indicatorOpts=IndicatorOptions()) -> None:
        self.maxSizeInBytes = maxSizeInBytes
        self.verifyDNSName = verifyDNSName
        self.revocationCheckAndOscpCheck = revocationCheckAndOscpCheck
        self.httpOtps = httpOtps
        self.indicatorOtps = indicatorOpts
