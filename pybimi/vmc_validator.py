import os
from urllib.parse import urlparse
from asn1crypto import pem, x509
from certvalidator import ValidationContext, CertificateValidator
import hashlib
from tld import get_tld

from .bimi import *
from .exception import *
from .utils import *
from .asn1_logotype import *
from .options import *
from .cache import *

HERE = os.path.split(__file__)[0]
CACERT = os.path.join(HERE, 'cacert.pem')

oidExtKeyUsageBrandIndicatorForMessageIdentification = '1.3.6.1.5.5.7.3.31'

class VmcValidator:
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

    def validate(self):
        if not self.vmcUri:
            return

        h = hashlib.new('md5')
        h.update(self.vmcUri.encode())
        key = 'bimi_vmc_validation_result_{}'.format(h.hexdigest())
        # Find validation result in cache
        if self.cache is not None:
            found, e = self.cache.get(key)
            if found:
                # print('Found {} in cache'.format(key))
                if e is None:
                    return
                else:
                    raise e

        url = urlparse(self.vmcUri)
        if url is None:
            e = BimiFail('invalid Location URI')
            self._saveValidationResultToCache(key, e)
            raise e

        if url.scheme != 'https':
            e = BimiFail('the Authority Evidence Location URI is not served by HTTPS')
            self._saveValidationResultToCache(key, e)
            raise e

        try:
            vmcData = download(self.vmcUri,
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

            if self.opts.verifyDNSName:
                if not vmc.is_valid_domain_ip(self.domain):
                    e = BimiFail('the VMC is not valid for {} (valid hostnames include: {})'.format(self.domain, ', '.join(vmc.valid_domains)))
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
            tld = get_tld(self.domain, fix_protocol=True, fail_silently=True)
            for r in selectorSet:
                if '{}._bimi.{}'.format(self.lookupOpts.selector, self.domain) == r or \
                   '{}._bimi.{}'.format(self.lookupOpts.selector, tld) == r:
                    sanMatch = True
                    break
            for r in domainSet:
                if self.domain == r or tld == r:
                    sanMatch = True
                    break

            if not sanMatch:
                e = BimiFail('domain does not match SAN')
                self._saveValidationResultToCache(key, e)
                raise e

            # Validation of VMC Evidence Document
            hashArr = []
            for ext in vmc['tbs_certificate']['extensions']:
                if ext['extn_id'].native == oidLogotype:
                    if ext['critical'].native:
                        e = BimiFail('the logotype extension is CRITICAL')
                        self._saveValidationResultToCache(key, e)
                        raise e

                    hashArr += extractHashArray(ext['extn_value'].native)

            if len(hashArr) == 0:
                e = BimiFail('no hash found')
                self._saveValidationResultToCache(key, e)
                raise e

            try:
                indicatorData = download(self.indicatorUri,
                                         self.httpOpts.httpTimeout,
                                         self.httpOpts.httpUserAgent,
                                         self.indicatorOpts.maxSizeInBytes)
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
                e = BimiFail('data from Location and data from Authority Evidence Location are not identical')
                self._saveValidationResultToCache(key, e)
                raise e

        except Exception as e:
            e = BimiFail(e)
            self._saveValidationResultToCache(key, e)
            raise e

        self._saveValidationResultToCache(key, None)
