import os
from datetime import datetime
from urllib.parse import urlparse
from asn1crypto import pem, x509
from certvalidator import ValidationContext, CertificateValidator
import hashlib
from tld import get_fld

from .bimi import *
from .exception import *
from .utils import *
from .asn1_logotype import *
from .options import *
from .cache import *

HERE = os.path.split(__file__)[0]
CACERT = os.path.join(HERE, 'cacert.pem')

oidExtKeyUsageBrandIndicatorForMessageIdentification = '1.3.6.1.5.5.7.3.31'
oidTrademarkRegistration = '1.3.6.1.4.1.53087.1.4'

class Vmc:
    """
    A class used to represent a VMC

    Attributes
    ----------
    version: str
        Version of the certificate
    serialNumber: str
        Serial number of the certificate
    trademarkRegistration: str
        Trademark registration
    issuer: str
        Name of the issuer
    organizationName: str
        Name of the organization
    validFrom: datetime
        Not before
    expireOn: datetime
        Not after
    certifiedDomains: list
        Certified domains
    """

    def __init__(self, version: str,
                       serialNumber: str,
                       trademarkRegistration: str,
                       issuer: str,
                       organizationName: str,
                       validFrom: datetime,
                       expireOn: datetime,
                       certifiedDomains: list) -> None:
        self.version = version
        self.serialNumber = serialNumber
        self.trademarkRegistration = trademarkRegistration
        self.issuer = issuer
        self.organizationName = organizationName
        self.validFrom = validFrom
        self.expireOn = expireOn
        self.certifiedDomains = certifiedDomains

    def __repr__(self) -> str:
        return str(self.__dict__)

class VmcValidator:
    """
    A class used to validate a BIMI VMC

    Attributes
    ----------
    vmcUri: str
        URI of the VMC
    indicatorUri: str
        URI of the BIMI indicator
    domain: str,
        The domain
    opts: VmcOptions
        VMC validation options
    lookupOpts: LookupOptions
        DNS lookup options
    indicatorOpts: IndicatorOptions
        Indicator validation options
    httpOpts: HttpOptions
        HTTP options
    cache: Cache
        Cache

    Methods
    -------
    validate()
        Validate the VMC
    """

    def __init__(self, vmcUri: str,
                       indicatorUri: str,
                       domain: str=None,
                       opts: VmcOptions=VmcOptions(),
                       lookupOpts: LookupOptions=LookupOptions,
                       indicatorOpts: IndicatorOptions=IndicatorOptions(),
                       httpOpts: HttpOptions=HttpOptions(),
                       cache: Cache=None) -> None:
        self.vmcUri = vmcUri
        self.indicatorUri = indicatorUri
        self.domain = domain
        self.opts = opts
        self.lookupOpts = lookupOpts
        self.indicatorOpts = indicatorOpts
        self.httpOpts = httpOpts
        self.cache = cache

    def _saveValidationResultToCache(self, key: str, value: Exception):
        if self.cache is not None:
            self.cache.set(key, value)

    def validate(self) -> Vmc:
        """
        Validate the VMC. The VMC is downloaded from the URI with some HTTP
        options. If the indicator is downloaded successfully, it will be
        validated by some validation options.

        Returns
        -------
        Vmc

        Raises
        ------
        BimiFail

        BimiTempfail
        """

        # Certificate information holder
        c = None

        if not self.vmcUri:
            return c

        h = hashlib.new('md5')
        h.update(self.vmcUri.encode())
        key = 'bimi_vmc_validation_result_{}'.format(h.hexdigest())
        # Find validation result in cache
        if self.cache is not None:
            found, e = self.cache.get(key)
            if found:
                # print('Found {} in cache'.format(key))
                if e is None:
                    return c
                else:
                    raise e

        url = urlparse(self.vmcUri)
        if url is None:
            e = BimiFail('invalid VMC URI')
            self._saveValidationResultToCache(key, e)
            raise e

        if url.scheme != '' and url.scheme != 'https':
            e = BimiFail('the VMC URI is not served by HTTPS')
            self._saveValidationResultToCache(key, e)
            raise e

        try:
            vmcData = getData(self.vmcUri,
                              self.httpOpts.httpTimeout,
                              self.httpOpts.httpUserAgent,
                              self.opts.maxSizeInBytes,
                              self.cache)

        except BimiFail as e:
            self._saveValidationResultToCache(key, e)
            raise e

        except Exception as e:
            e = BimiTempfail(e)
            self._saveValidationResultToCache(key, e)
            raise e

        if not pem.detect(vmcData):
            e = BimiFail('PEM-encoded data not found')
            self._saveValidationResultToCache(key, e)
            raise e

        try:
            intermediates = []
            leaf = None
            vmc = None
            for _, _, der_bytes in pem.unarmor(vmcData, multiple=True):
                cert = x509.Certificate.load(der_bytes)
                # If the certificate is a CA, we add it to the intermediates pool.
                # If not, we call it the leaf certificate.
                if cert.ca:
                    intermediates.append(der_bytes)
                    continue

                # Certificate is not a CA, it must be our leaf certificate.
                # If we already found one, bail with error.
                if vmc is not None:
                    e = BimiFail('more than one VMC found')
                    self._saveValidationResultToCache(key, e)
                    raise e

                leaf = der_bytes
                vmc = cert

            # We exit the loop with no leaf certificate
            if vmc is None:
                e = BimiFail('no VMC found')
                self._saveValidationResultToCache(key, e)
                raise e

            roots = []
            with open(CACERT, 'rb') as f:
                for _, _, der_bytes in pem.unarmor(f.read(), multiple=True):
                    roots.append(der_bytes)

            # Finally, let's call Verify on our vmc with our fully configured options
            # 5.1.1. Validate the authenticity of the certificate
            # 5.1.2. Check the validity of the certificates in the certificate chain
            # 5.1.3. Check that the certificates in the certificate chain are not revoked
            # TODO: Separate revocation check and OSCP status check
            context = ValidationContext(trust_roots=roots,
                                        allow_fetching=self.opts.revocationCheckAndOscpCheck)
            validator = CertificateValidator(leaf,
                                             intermediate_certs=intermediates,
                                             validation_context=context)

            validator.validate_usage(
                # Any key usage
                key_usage=set([]),
                # 5.1.5. Verify that the end-entity certificate is a Verified Mark Certificate
                extended_key_usage=set([oidExtKeyUsageBrandIndicatorForMessageIdentification])
            )

            c = self._extractVMC(validator)

            if self.opts.verifyDNSName:
                hostname = self.domain
                if not vmc.is_valid_domain_ip(hostname):
                    invalidHostname = True

                    if self.opts.verifyDNSNameAcceptSubdomain:
                        # Try TLD
                        fld = get_fld(self.domain, fix_protocol=True, fail_silently=True)
                        hostname = fld
                        if vmc.is_valid_domain_ip(hostname):
                            invalidHostname = False

                    if invalidHostname:
                        e = BimiFail('the VMC is not valid for {} (valid hostnames include: {})'.format(hostname, ', '.join(vmc.valid_domains)))
                        self._saveValidationResultToCache(key, e)
                        raise e

            # TODO: 5.1.4. Validate the proof of CT logging
            # https://github.com/google/certificate-transparency/tree/master/python

            # VMC Domain Verification
            selectorSet = []
            domainSet = []
            for n in vmc.subject_alt_name_value:
                san = n.native
                if '_bimi' in san:
                    selectorSet.append(san)
                else:
                    domainSet.append(san)

            sanMatch = False
            fld = get_fld(self.domain, fix_protocol=True, fail_silently=True)
            for r in selectorSet:
                if '{}._bimi.{}'.format(self.lookupOpts.selector, self.domain) == r or \
                   '{}._bimi.{}'.format(self.lookupOpts.selector, fld) == r:
                    sanMatch = True
                    break
            for r in domainSet:
                if self.domain == r or fld == r:
                    sanMatch = True
                    break

            if not sanMatch:
                e = BimiFail('domain does not match SAN in VMC')
                self._saveValidationResultToCache(key, e)
                raise e

            # Validation of VMC Evidence Document
            hashArr = []
            for ext in vmc['tbs_certificate']['extensions']:
                if ext['extn_id'].native == oidLogotype:
                    if ext['critical'].native:
                        e = BimiFail('the logotype extension in VMC is CRITICAL')
                        self._saveValidationResultToCache(key, e)
                        raise e

                    hashArr += extractHashArray(ext['extn_value'].native)

            if len(hashArr) == 0:
                e = BimiFail('no hash found in VMC')
                self._saveValidationResultToCache(key, e)
                raise e

            try:
                indicatorData = getData(self.indicatorUri,
                                        self.httpOpts.httpTimeout,
                                        self.httpOpts.httpUserAgent,
                                        self.indicatorOpts.maxSizeInBytes,
                                        self.cache)

            except BimiFail as e:
                self._saveValidationResultToCache(key, e)
                raise e

            except Exception as e:
                e = BimiTempfail(e)
                self._saveValidationResultToCache(key, e)
                raise e

            hashMatch = False
            for hash in hashArr:
                h = hashlib.new(hash.algorithm)
                h.update(indicatorData)
                if h.digest() == hash.value:
                    hashMatch = True
                    break

            if not hashMatch:
                e = BimiFail('SVG logo file is not binary equal to the image embedded in VMC certificate')
                self._saveValidationResultToCache(key, e)
                raise e

        except Exception as e:
            e = BimiFail(e)
            self._saveValidationResultToCache(key, e)
            raise e

        self._saveValidationResultToCache(key, None)
        return c

    def _extractVMC(self, v: CertificateValidator) -> Vmc:
        """
        Extract information from the certificate downloaded from internet

        Parameters
        ----------
        v: CertificateValidator

        Returns
        -------
        Vmc
        """

        try:
            c = v._certificate.native['tbs_certificate']

            vmc = Vmc(version=c['version'],
                      serialNumber=c['serial_number'],
                      trademarkRegistration=c['subject'][oidTrademarkRegistration],
                      issuer=c['issuer']['organization_name'],
                      organizationName=c['subject']['organization_name'],
                      validFrom=c['validity']['not_before'],
                      expireOn=c['validity']['not_after'],
                      certifiedDomains=[])

            for ext in c['extensions']:
                if ext['extn_id'] == 'subject_alt_name':
                    if isinstance(ext['extn_value'], list):
                        vmc.certifiedDomains += ext['extn_value']
                    elif isinstance(ext['extn_value'], str):
                        vmc.certifiedDomains.append(ext['extn_value'])

            return vmc

        except:
            return None
