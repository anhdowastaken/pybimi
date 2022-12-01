import dns.resolver
from tld import get_fld

from .bimi import *
from .exception import *
from .options import *

class LookupValidator:
    def __init__(self, domain: str, opts=LookupOptions()) -> None:
        self.domain = domain
        self.opts = opts
        # Actual
        self.actualDomain = self.domain
        if self.opts and self.opts.selector and self.opts.selector.strip():
            self.actualSelector = self.opts.selector.strip()
        else:
            self.actualSelector = DEFAULT_SELECTOR

    def validate(self) -> BimiRecord:
        # https://datatracker.ietf.org/doc/html/draft-blank-ietf-bimi-02#appendix-B
        # Lookup selector._bimi.foo.example.com for the BIMI DNS record.
        # If it did not exist, it would fall back to the lookup selector._bimi.example.com.

        # The first try
        # Use input domain and input selector (if it exists)
        if not (self.domain and self.domain.strip()):
            raise BimiFail('empty domain')

        self.actualDomain = self.domain.strip()
        txt = ''
        try:
            txt = self._lookup()
        except (BimiNoPolicy, BimiFail):
            fld = get_fld(self.domain, fix_protocol=True, fail_silently=True)
            if fld and fld.strip() and fld != self.domain:
                self.actualDomain = fld
                # The second try with the effective top level domain
                # Keep using input selector if it exists
                txt = self._lookup()

        rec = self.parse(txt)
        return rec

    def _lookup(self) -> str:
        qname = '{}._bimi.{}'.format(self.actualSelector, self.actualDomain)
        try:
            answers = dns.resolver.resolve(qname, 'TXT')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as e:
            raise BimiNoPolicy(e)
        except (dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers) as e:
            raise BimiTempfail(e)
        except dns.resolver.YXDOMAIN as e:
            raise BimiFail(e)

        if len(answers) == 0:
            raise BimiNoPolicy

        # Long keys are split in multiple parts
        txt = ''
        for rdata in answers:
            txt += rdata.to_text().strip('"')

        return txt

    def parse(self, txt: str) -> BimiRecord:
        params = self._parse(txt)

        # Find unknown tags
        expectedKeys = ['v', 'l', 'a']
        foundUnexpectedKey = False
        for actualKey in params:
            found = False
            for key in expectedKeys:
                if actualKey.strip().lower() == key.strip().lower():
                    found = True
                    break

            if not found:
                foundUnexpectedKey = True
                break

        if foundUnexpectedKey:
            raise BimiFail('unknown tag found')

        if params['v'] != CURRENT_VERSION:
            raise BimiFail('unsupported version')

        rec = BimiRecord()
        if 'l' in params:
            rec.location = params['l'].strip()
        if 'a' in params:
            rec.authorityEvidenceLocation = params['a'].strip()

        if 'l' in params and not params['l'].strip() \
            and 'a' in params and not params['l'].strip():
            raise BimiDeclined

        rec.domain = self.actualDomain
        rec.selector = self.actualSelector

        return rec

    def _parse(self, txt: str) -> dict:
        if not txt:
            raise BimiNoPolicy

        pairs = txt.split(';')
        params = dict()
        for s in pairs:
            if not s.strip():
                continue

            kv = s.split('=', 1)
            if len(kv) != 2:
                raise BimiFail('malformed params')
            params[kv[0].strip()] = kv[1].strip()

        return params
