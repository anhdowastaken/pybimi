import dns.resolver
from tld import get_fld

from .bimi import *
from .exception import *
from .options import *

class LookupValidator:
    """
    A class used to validate a BIMI DNS record

    Attributes
    ----------
    domain: str
        A domain
    opts: LookupOptions
        DNS lookup options
    actualDomain: str
        Actual domain
    actualSelector: str
        Actual selector
    bimiFailErrors: list
        List of BIMI fail errors collected when parsing the DNS TXT record

    Methods
    -------
    validate()
        Validate the BIMI DNS record
    parse(txt)
        Parse a BIMI DNS TXT record to a BimiRecord object
    """

    def __init__(self, domain: str, opts=LookupOptions()) -> None:
        self.domain = domain
        self.opts = opts
        # Actual
        self.actualDomain = self.domain
        if self.opts and self.opts.selector and self.opts.selector.strip():
            self.actualSelector = self.opts.selector.strip()
        else:
            self.actualSelector = DEFAULT_SELECTOR
        self.bimiFailErrors = [] # Only errors when parsing
        self.txt = ''

    def validate(self, collectAllBimiFail=False) -> BimiRecord:
        """
        Validate the BIMI DNS record. The record is fetched from the DNS server
        with some lookup options. If the record is fetched successfully, its
        syntax will be checked. Adn it will be parsed to a BimiRecord object.

        Parameters
        ----------
        collectAllBimiFail: bool
            If set, instead of raising a BimiFail exception, save it to the attribute bimiFailErrors

        Returns
        -------
        BimiRecord

        Raises
        ------
        BimiNoPolicy

        BimiDeclined

        BimiFail

        BimiTemfailCannotAccess
        """

        # https://datatracker.ietf.org/doc/html/draft-blank-ietf-bimi-02#appendix-B
        # Lookup selector._bimi.foo.example.com for the BIMI DNS record.
        # If it did not exist, it would fall back to the lookup selector._bimi.example.com.

        # The first try
        # Use input domain and input selector (if it exists)
        if not (self.domain and self.domain.strip()):
            raise BimiFail('empty domain')

        self.actualDomain = self.domain.strip()
        try:
            self.txt = self._lookup()
        except (BimiNoPolicy, BimiFail):
            fld = get_fld(self.domain, fix_protocol=True, fail_silently=True)
            if fld and fld.strip() and fld != self.domain:
                self.actualDomain = fld
                # The second try with the effective top level domain
                # Keep using input selector if it exists
                self.txt = self._lookup()

        rec = self.parse(self.txt, collectAllBimiFail=collectAllBimiFail)
        return rec

    def _lookup(self) -> str:
        qname = '{}._bimi.{}'.format(self.actualSelector, self.actualDomain)
        try:
            answers = dns.resolver.resolve(qname, 'TXT')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as e:
            raise BimiNoPolicy(e)
        except (dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers) as e:
            raise BimiTemfailCannotAccess(e)
        except dns.resolver.YXDOMAIN as e:
            raise BimiFail(e)

        if len(answers) == 0:
            raise BimiNoPolicy

        # Long keys are split in multiple parts
        txt = ''
        for rdata in answers:
            # FIXME: https://github.com/rthalley/dnspython/blob/32ce73ab3fca0cfd7e5bf0af3b6443a6124b166a/dns/rdtypes/txtbase.py#L66
            txt += rdata.to_text().strip('"').replace('" "', '')

        return txt

    def parse(self, txt: str, collectAllBimiFail=False) -> BimiRecord:
        """
        Parse a DNS TXT record to a BimiRecord object

        Parameters
        ----------
        txt: str
            A DNS TXT record
        collectAllBimiFail: bool
            If set, instead of raising a BimiFail exception, save it to the attribute bimiFailErrors

        Returns
        -------
        BimiRecord
            A BimiRecord object

        Raises
        ------
        BimiNoPolicy

        BimiDeclined

        BimiFailInvalidFormat
        """

        params = self._parse(txt, collectAllBimiFail=collectAllBimiFail)

        # Find unknown tags
        expectedKeys = ['v', 'l', 'a']
        foundUnexpectedKey = False
        for actualKey in params:
            matchExpectedKeys = False
            for key in expectedKeys:
                if actualKey.strip().lower() == key.strip().lower():
                    matchExpectedKeys = True
                    break

            if not matchExpectedKeys:
                foundUnexpectedKey = True
                break

        if foundUnexpectedKey:
            e = BimiFailInvalidFormat('unknown tag found')
            if collectAllBimiFail:
                self.bimiFailErrors.append(e)
            else:
                raise e

        requiredKeys = ['v', 'l']
        for key in requiredKeys:
            if key not in params:
                e = BimiFailInvalidFormat('{}= tag not found'.format(key))
                if collectAllBimiFail:
                    self.bimiFailErrors.append(e)
                else:
                    raise e

        if list(params.keys())[0] != 'v':
            e = BimiFailInvalidFormat('v= tag is not the first tag')
            if collectAllBimiFail:
                self.bimiFailErrors.append(e)
            else:
                raise e

        if params['v'] != CURRENT_VERSION:
            e = BimiFailInvalidFormat('unsupported version')
            if collectAllBimiFail:
                self.bimiFailErrors.append(e)
            else:
                raise e

        rec = BimiRecord()
        if 'l' in params:
            rec.location = params['l'].strip()
        if 'a' in params:
            rec.authorityEvidenceLocation = params['a'].strip()

        if ('l' in params and not params['l'].strip()) \
            and ('a' in params and not params['a'].strip()):
            raise BimiDeclined

        rec.domain = self.actualDomain
        rec.selector = self.actualSelector

        return rec

    def _parse(self, txt: str, collectAllBimiFail=False) -> dict:
        if not txt:
            raise BimiNoPolicy

        pairs = txt.split(';')
        params = dict()
        for s in pairs:
            if not s.strip():
                continue

            kv = s.split('=', 1)
            if len(kv) != 2:
                e = BimiFailInvalidFormat('invalid tag')
                if collectAllBimiFail:
                    self.bimiFailErrors.append(e)
                    continue
                else:
                    raise e
            params[kv[0].strip()] = kv[1].strip()

        return params
