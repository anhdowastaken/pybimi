from .options import *
from .lookup_validator import LookupValidator
from .indicator_validator import IndicatorValidator
from .vmc_validator import VmcValidator

class Validator():
    def __init__(self, domain: str,
                       lookupOpts: LookupOptions=LookupOptions(),
                       indicatorOpts: IndicatorOptions=IndicatorOptions(),
                       vmcOpts: VmcOptions=VmcOptions(),
                       httpOpts: HttpOptions=HttpOptions()) -> None:
        self.domain = domain
        self.lookupOpts = lookupOpts
        self.indicatorOpts = indicatorOpts
        self.vmcOpts = vmcOpts
        self.httpOpts = httpOpts

    def validate(self, validateIndicator: bool=True, validateVmc: bool=True):
        lv = LookupValidator(self.domain, self.lookupOpts)
        rec = lv.validate()

        if validateIndicator:
            iv = IndicatorValidator(rec.location, self.indicatorOpts, self.httpOpts)
            iv.validate()

        if validateVmc:
            vv = VmcValidator(rec.authorityEvidenceLocation,
                              rec.location,
                              self.domain,
                              self.vmcOpts,
                              self.httpOpts,
                              self.indicatorOpts)
            vv.validate()
