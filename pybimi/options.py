import os
from typing import Optional
from .bimi import DEFAULT_SELECTOR

HERE = os.path.split(__file__)[0]
JAVA = 'java'
JING_JAR = os.path.join(HERE, 'jing.jar')
RNC_SCHEMA = os.path.join(HERE, 'SVG_PS-latest.rnc')

class HttpOptions:
    """
    Configuration options for HTTP requests.

    These options control how HTTP requests are made when fetching
    BIMI indicators and VMC certificates from remote URLs.

    Attributes:
        httpTimeout: Request timeout in seconds
        httpUserAgent: User-Agent header value for requests
    """

    def __init__(self, httpTimeout: int = 30, httpUserAgent: str = '') -> None:
        """
        Initialize HTTP options.

        Args:
            httpTimeout: Timeout for HTTP requests in seconds
            httpUserAgent: User-Agent string for HTTP requests
        """
        self.httpTimeout = httpTimeout
        self.httpUserAgent = httpUserAgent

class LookupOptions:
    """
    Configuration options for BIMI DNS record lookups.

    These options control how BIMI DNS TXT records are queried,
    including selector choice and custom DNS servers.

    Attributes:
        selector: BIMI selector for DNS queries (default: 'default')
        ns: Custom DNS nameservers to use for queries
    """

    def __init__(self, selector: str = DEFAULT_SELECTOR, ns: Optional[list] = None) -> None:
        """
        Initialize DNS lookup options.

        Args:
            selector: BIMI selector for DNS record queries
            ns: List of custom DNS nameserver IPs to use
        """
        self.selector = selector
        self.ns = ns

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
    verifyCTLogging: bool=False
        Validate Certificate Transparency (CT) logging according to RFC 6962
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
                       verifyCTLogging: bool=False,
                       httpOpts=HttpOptions(),
                       indicatorOpts=IndicatorOptions()) -> None:
        self.maxSizeInBytes = maxSizeInBytes
        self.verifyDNSName = verifyDNSName
        self.verifyDNSNameAcceptSubdomain = verifyDNSNameAcceptSubdomain
        self.revocationCheckAndOscpCheck = revocationCheckAndOscpCheck
        self.verifySVGImage = verifySVGImage
        self.verifyCTLogging = verifyCTLogging
        self.httpOpts = httpOpts
        self.indicatorOpts = indicatorOpts
