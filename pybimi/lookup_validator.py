from typing import List, Optional
import dns.resolver
from tld import get_fld

from .bimi import BimiRecord, DEFAULT_SELECTOR, CURRENT_VERSION
from .exception import (
    BimiError, BimiNoPolicy, BimiDeclined, BimiFail,
    BimiFailInvalidFormat, BimiTemfailCannotAccess
)
from .options import LookupOptions

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

    def __init__(self, domain: str, opts: Optional[LookupOptions] = None) -> None:
        """
        Initialize DNS lookup validator.

        Args:
            domain: Target domain for BIMI record lookup
            opts: DNS lookup configuration options
        """
        if not domain or not isinstance(domain, str):
            raise ValueError("Domain must be a non-empty string")

        self.domain = domain.strip().lower()
        self.opts = opts or LookupOptions()
        # Actual domain and selector used for lookup
        self.actualDomain = self.domain
        if self.opts.selector and self.opts.selector.strip():
            self.actualSelector = self.opts.selector.strip()
        else:
            self.actualSelector = DEFAULT_SELECTOR
        self.bimiFailErrors: List[BimiError] = []  # Collect parsing errors
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

        # BIMI DNS lookup with fallback mechanism per specification:
        # https://datatracker.ietf.org/doc/html/draft-blank-ietf-bimi-02#appendix-B
        # 1. Try: selector._bimi.foo.example.com
        # 2. Fallback: selector._bimi.example.com (effective TLD)

        # The first try
        # Use input domain and input selector (if it exists)
        if not (self.domain and self.domain.strip()):
            raise BimiFail('empty domain')

        self.actualDomain = self.domain.strip()
        try:
            self.txt = self._lookup()
        except (BimiNoPolicy, BimiFail) as initial_error:
            # Attempt fallback to effective top-level domain
            fld = get_fld(self.domain, fix_protocol=True, fail_silently=True)
            if fld and fld.strip() and fld.lower() != self.domain.lower():
                self.actualDomain = fld.lower()
                try:
                    self.txt = self._lookup()
                except Exception:
                    # If fallback fails, raise the original error
                    raise initial_error
            else:
                raise initial_error

        rec = self.parse(self.txt, collectAllBimiFail=collectAllBimiFail)
        return rec

    def _lookup(self) -> str:
        """
        Perform DNS TXT record lookup for BIMI policy.

        Returns:
            Raw TXT record content

        Raises:
            BimiNoPolicy: No BIMI record found
            BimiTemfailCannotAccess: DNS query failed
            BimiFail: DNS query error
        """
        qname = f'{self.actualSelector}._bimi.{self.actualDomain}'
        try:
            resolver = dns.resolver.Resolver()
            if self.opts.ns and isinstance(self.opts.ns, list):
                resolver.nameservers = self.opts.ns
            answers = resolver.resolve(qname, 'TXT')
        except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer) as e:
            raise BimiNoPolicy(e)
        except (dns.resolver.LifetimeTimeout, dns.resolver.NoNameservers) as e:
            raise BimiTemfailCannotAccess(e)
        except dns.resolver.YXDOMAIN as e:
            raise BimiFail(e)

        if len(answers) == 0:
            raise BimiNoPolicy

        # Concatenate multiple TXT record parts (RFC compliant)
        txt_parts = []
        for rdata in answers:
            # Remove quotes and concatenate split strings
            # FIXME: Consider using rdata.strings for better handling
            part = rdata.to_text().strip('"').replace('" "', '')
            txt_parts.append(part)

        txt = ''.join(txt_parts)

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

        # Validate against expected BIMI tags
        expected_keys = {'v', 'l', 'a'}  # version, location, authority
        actual_keys = {key.lower() for key in params.keys()}
        unexpected_keys = actual_keys - expected_keys

        if unexpected_keys:
            error = BimiFailInvalidFormat(f'Unknown tags found: {", ".join(unexpected_keys)}')
            if collectAllBimiFail:
                self.bimiFailErrors.append(error)
            else:
                raise error

        # Check for required tags
        required_keys = ['v', 'l']  # version and location are mandatory
        for key in required_keys:
            if key not in params:
                error = BimiFailInvalidFormat(f'Required tag "{key}=" not found')
                if collectAllBimiFail:
                    self.bimiFailErrors.append(error)
                else:
                    raise error

        if len(list(params.keys())) > 0 and list(params.keys())[0] != 'v':
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

    def _parse(self, txt: str, collectAllBimiFail: bool = False) -> dict:
        """
        Parse BIMI DNS TXT record into key-value pairs.

        Args:
            txt: Raw TXT record content
            collectAllBimiFail: Whether to collect all errors instead of raising

        Returns:
            Dictionary of parsed tag-value pairs

        Raises:
            BimiNoPolicy: Empty record
            BimiFailInvalidFormat: Invalid record format
        """
        if not txt:
            raise BimiNoPolicy

        if not txt.strip():
            raise BimiNoPolicy("Empty BIMI record")

        # Split on semicolon and parse key=value pairs
        pairs = [pair.strip() for pair in txt.split(';') if pair.strip()]
        params = {}

        for pair in pairs:
            if '=' not in pair:
                error = BimiFailInvalidFormat(f'Invalid tag format: {pair}')
                if collectAllBimiFail:
                    self.bimiFailErrors.append(error)
                    continue
                else:
                    raise error

            key, value = pair.split('=', 1)
            params[key.strip()] = value.strip()

        return params
