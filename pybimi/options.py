import os
from .bimi import *

HERE = os.path.split(__file__)[0]
JAVA = 'java'
JING_JAR = os.path.join(HERE, 'jing.jar')
RNC_SCHEMA = os.path.join(HERE, 'SVG_PS-latest.rnc')

class HttpOptions:
    """
    A class to represent HTTP options

    Attributes
    ----------
    httpTimeout: int=30
        HTTP timeout
    httpUserAgent: str=''
        HTTP User Agent
    """

    def __init__(self, httpTimeout: int=30, httpUserAgent: str='') -> None:
        self.httpTimeout = httpTimeout
        self.httpUserAgent = httpUserAgent

class LookupOptions:
    """
    A class to represent BIMI DNS lookup options

    Attributes
    ----------
    selector: str='default'
        A selector to fetch BIMI DNS TXT record
    """

    def __init__(self, selector: str=DEFAULT_SELECTOR) -> None:
        self.selector = selector

class IndicatorOptions:
    """
    A class to represent BIMI indicator validation options

    Attributes
    ----------
    maxSizeInBytes: int=0
        Maximum size in bytes of an BIMI indicator
    httpOpts: HttpOptions=HttpOptions()
        HTTP options
    javaPath: str='java'
        Path of JAVA binary
    jingJarPath: str='jing.jar'
        Path of Jing jar file
    rncSchemaPath: str='SVG_PS-latest.rnc'
        Path of RNC schema file
    """

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
    """
    A class to represent Verified Mark Certificates validation options

    Attributes
    ----------
    maxSizeInBytes: int=0
        Maximum size in bytes of a certificate
    verifyDNSName: bool=True
        Ensure the certificate is valid for input domain
    verifyDNSNameAcceptSubdomain: bool=False
        If the certificate is valid for the TLD, accept any its subdomain
    revocationCheckAndOscpCheck: bool=False
        Ensure the certificate was not revoked and passed OSCP check
    verifySVGImage: bool=True
        Ensure the external SVG logo image and the one embedded in the certificate are the same
    httpOpts=HttpOptions()
        HTTP options
    indicatorOpts=IndicatorOptions()
        BIMI indicator validation options
    """

    def __init__(self, maxSizeInBytes: int=0,
                       verifyDNSName: bool=True,
                       verifyDNSNameAcceptSubdomain: bool=False,
                       revocationCheckAndOscpCheck: bool=False,
                       verifySVGImage: bool=True,
                       httpOpts=HttpOptions(),
                       indicatorOpts=IndicatorOptions()) -> None:
        self.maxSizeInBytes = maxSizeInBytes
        self.verifyDNSName = verifyDNSName
        self.verifyDNSNameAcceptSubdomain = verifyDNSNameAcceptSubdomain
        self.revocationCheckAndOscpCheck = revocationCheckAndOscpCheck
        self.verifySVGImage = verifySVGImage
        self.httpOpts = httpOpts
        self.indicatorOpts = indicatorOpts
