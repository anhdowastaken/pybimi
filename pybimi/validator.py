from .options import *
from .lookup_validator import LookupValidator
from .indicator_validator import IndicatorValidator
from .vmc_validator import VmcValidator
from .cache import Cache

class Validator():
    def __init__(self, domain: str,
                       lookupOpts: LookupOptions=LookupOptions(),
                       indicatorOpts: IndicatorOptions=IndicatorOptions(),
                       vmcOpts: VmcOptions=VmcOptions(),
                       httpOpts: HttpOptions=HttpOptions(),
                       cache: Cache=None) -> None:
        self.domain = domain
        self.lookupOpts = lookupOpts
        self.indicatorOpts = indicatorOpts
        self.vmcOpts = vmcOpts
        self.httpOpts = httpOpts
        self.cache = cache

    def validate(self, validateIndicator: bool=True, validateVmc: bool=True):
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
