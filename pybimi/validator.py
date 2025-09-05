from typing import Optional
from .options import LookupOptions, IndicatorOptions, VmcOptions, HttpOptions
from .lookup_validator import LookupValidator
from .indicator_validator import IndicatorValidator
from .vmc_validator import VmcValidator
from .cache import Cache
from .bimi import BimiRecord

class Validator:
    """
    A class used to validate BIMI of a domain

    Attributes
    ----------
    domain: str
        A domain
    lookupOpts: LookupOptions
        DNS lookup options
    indicatorOpts: IndicatorOptions
        BIMI indicator validation options
    vmcOpts: VmcOptions
        VMC validation options
    httpOpts: HttpOptions
        HTTP options
    cache: Cache=None
        Cache

    Methods
    -------
    validate()
        Validate BIMI
    """

    def __init__(self, domain: str,
                       lookupOpts: Optional[LookupOptions] = None,
                       indicatorOpts: Optional[IndicatorOptions] = None,
                       vmcOpts: Optional[VmcOptions] = None,
                       httpOpts: Optional[HttpOptions] = None,
                       cache: Optional[Cache] = None) -> None:
        """
        Initialize the BIMI validator.

        Args:
            domain: Target domain to validate BIMI for
            lookupOpts: DNS lookup configuration options
            indicatorOpts: SVG indicator validation options
            vmcOpts: VMC certificate validation options
            httpOpts: HTTP request configuration options
            cache: Optional cache instance for performance optimization
        """
        if not domain or not isinstance(domain, str):
            raise ValueError("Domain must be a non-empty string")

        self.domain = domain.strip().lower()
        self.lookupOpts = lookupOpts or LookupOptions()
        self.indicatorOpts = indicatorOpts or IndicatorOptions()
        self.vmcOpts = vmcOpts or VmcOptions()
        self.httpOpts = httpOpts or HttpOptions()
        self.cache = cache

    def validate(self, validateIndicator: bool = True, validateVmc: bool = True) -> BimiRecord:
        """
        Validate BIMI record, indicator, and VMC certificate for the domain.

        This method performs a complete BIMI validation workflow:
        1. DNS record lookup and parsing
        2. SVG indicator validation (if requested)
        3. VMC certificate validation (if requested)

        Args:
            validateIndicator: Whether to validate the SVG indicator
            validateVmc: Whether to validate the VMC certificate

        Returns:
            BimiRecord: Validated BIMI record with all relevant information

        Raises:
            BimiNoPolicy: No BIMI policy found for domain
            BimiDeclined: BIMI explicitly declined by domain
            BimiFail: Validation failure (various subtypes)
            BimiTempfail: Temporary failure (network, etc.)
        """

        lv = LookupValidator(domain=self.domain, opts=self.lookupOpts)
        rec = lv.validate()

        if validateIndicator:
            iv = IndicatorValidator(uri=rec.location,
                                    opts=self.indicatorOpts,
                                    httpOpts=self.httpOpts,
                                    cache=self.cache)
            iv.validate()

        if validateVmc:
            vv = VmcValidator(vmcUri=rec.authorityEvidenceLocation,
                              indicatorUri=rec.location,
                              domain=rec.domain,
                              opts=self.vmcOpts,
                              lookupOpts=self.lookupOpts,
                              indicatorOpts=self.indicatorOpts,
                              httpOpts=self.httpOpts,
                              cache=self.cache)
            vv.validate()

        return rec
