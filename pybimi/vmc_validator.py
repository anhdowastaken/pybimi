import os
from datetime import datetime
import re
import struct
import time
from urllib.parse import urlparse
from asn1crypto import pem, x509
from certvalidator import ValidationContext, CertificateValidator
import hashlib
from tld import get_fld

from .exception import (
    BimiFail, BimiFailInvalidURI, BimiFailInvalidVMCNotPEM, BimiFailInvalidVMCNoLeafFound,
    BimiFailInvalidVMCMultiLeafs, BimiFailInvalidVMCUnmatchedDomain,
    BimiFailInvalidVMCUnmatchedSAN, BimiFailInvalidVMCCriticalLogotype,
    BimiFailInvalidVMCNoHashFound, BimiFailInvalidVMCUnmatchedSVG,
    BimiFailInvalidVMCUnsupportedAlgorithm, BimiFailInvalidVMCCannotVerify,
    BimiFailInvalidVMCNotValidBefore, BimiFailInvalidVMCExpiredAfter,
    BimiFailInvalidVMCNoRevocationFound, BimiFailInvalidVMCCheckRevocationFailed,
    BimiFailInvalidVMCIssuerNotMatch, BimiFailInvalidVMCAnyPolicyFound,
    BimiFailInvalidVMCNotCA, BimiFailInvalidVMCExceedMaximumPathLength,
    BimiFailInvalidVMCNotAllowToSign, BimiFailInvalidVMCUnsupportedCriticalExtensionFound,
    BimiFailInvalidVMCNoValidPolicySetFound, BimiFailInvalidVMCNoMatchingIssuerFound,
    BimiFailInvalidVMCNoSCTFound, BimiFailInvalidVMCInvalidSCT, BimiFailInvalidVMCSCTFutureTimestamp,
    BimiTempfail
)
from .utils import getData
from .asn1_logotype import extractHashArray, oidLogotype
from .options import VmcOptions, LookupOptions, IndicatorOptions, HttpOptions
from .cache import Cache

HERE = os.path.split(__file__)[0]
CACERT = os.path.join(HERE, 'cacert.pem')

# VMC-related OID constants as defined in BIMI specifications
OID_PILOT_IDENTIFIER = '1.3.6.1.4.1.53087.4.1'
OID_EXT_KEY_USAGE_BIMI = '1.3.6.1.5.5.7.3.31'
OID_TRADEMARK_REGISTRATION = '1.3.6.1.4.1.53087.1.4'
OID_SCT_LIST = '1.3.6.1.4.1.11129.2.4.2'

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
    localVMC: bool
        If set, it means the vmcUri is a local file path
    localIndicator: bool
        If set, it means the indicatorUri is a local file path
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
    svgImages: list
        List of SVG images extracted from the certificate when validating
    bimiFailErrors: list
        List of BIMI fail errors collected when parsing the DNS TXT record

    Methods
    -------
    validate()
        Validate the VMC
    """

    def __init__(self, vmcUri: str,
                       indicatorUri: str=None,
                       localVMC: bool=False,
                       localIndicator: bool=False,
                       domain: str=None,
                       opts: VmcOptions=VmcOptions(),
                       lookupOpts: LookupOptions=LookupOptions,
                       indicatorOpts: IndicatorOptions=IndicatorOptions(),
                       httpOpts: HttpOptions=HttpOptions(),
                       cache: Cache=None) -> None:
        self.vmcUri = vmcUri
        self.indicatorUri = indicatorUri
        self.localVMC = localVMC
        self.localIndicator = localIndicator
        self.domain = domain
        self.opts = opts
        self.lookupOpts = lookupOpts
        self.indicatorOpts = indicatorOpts
        self.httpOpts = httpOpts
        self.cache = cache
        self.svgImages = []
        self.bimiFailErrors = [] # Only errors when validating after VMC is found

    def _saveValidationResultToCache(self, key: str, value: Exception):
        if self.cache is not None:
            self.cache.set(key, value)

    def validate(self, extractSvg=False, collectAllBimiFail=False) -> Vmc:
        """
        Validate the VMC. The VMC is downloaded from the URI with some HTTP
        options. If the indicator is downloaded successfully, it will be
        validated by some validation options.

        Parameters
        ----------
        extractSvg: bool
            If set, try to find and extract corresponding SVG image, save it to the attribute svgImages
        collectAllBimiFail: bool
            If set, instead of raising a BimiFail exception, save it to the attribute bimiFailErrors

        Returns
        -------
        Vmc

        Raises
        ------
        BimiFail

        BimiFailInvalidURI

        BimiFailInvalidVMC

        BimiTempfail

        BimiTemfailCannotAccess
        """

        # Certificate information holder
        c = None

        if not (self.vmcUri and self.vmcUri.strip()):
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
            e = BimiFailInvalidURI('invalid VMC URI')
            self._saveValidationResultToCache(key, e)
            raise e

        if not self.localVMC and url.scheme != 'https':
            e = BimiFailInvalidURI('the VMC URI is not served by HTTPS')
            self._saveValidationResultToCache(key, e)
            raise e

        try:
            vmcData = getData(uri=self.vmcUri,
                              localFile=self.localVMC,
                              timeout=self.httpOpts.httpTimeout,
                              userAgent=self.httpOpts.httpUserAgent,
                              maxSizeInBytes=self.opts.maxSizeInBytes,
                              cache=self.cache)

        except BimiFail as e:
            self._saveValidationResultToCache(key, e)
            raise e

        except BimiTempfail as e:
            raise e

        except Exception as e:
            raise BimiTempfail(str(e))

        if not pem.detect(vmcData):
            e = BimiFailInvalidVMCNotPEM('PEM-encoded data not found')
            self._saveValidationResultToCache(key, e)
            raise e

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
                e = BimiFailInvalidVMCMultiLeafs('more than one VMC found')
                self._saveValidationResultToCache(key, e)
                raise e

            leaf = der_bytes
            vmc = cert

        # We exit the loop with no leaf certificate
        if vmc is None:
            e = BimiFailInvalidVMCNoLeafFound('no VMC found')
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

        # Patch certvalidator to support Pilot Identifier extension
        import certvalidator.validate
        import certvalidator.errors

        # Store original function if not already patched
        if not hasattr(certvalidator.validate, '_original_validate_path'):
            certvalidator.validate._original_validate_path = certvalidator.validate._validate_path

            def patched_validate_path(validation_context, path):
                orig_func = certvalidator.validate._original_validate_path

                # Try to catch the specific error and allow pilot identifier
                try:
                    return orig_func(validation_context, path)
                except certvalidator.errors.PathValidationError as e:
                    error_msg = str(e)
                    if 'unsupported critical extension' in error_msg and OID_PILOT_IDENTIFIER in error_msg:
                        # This is the pilot identifier - proceed without this check
                        # We'll temporarily modify the certificate objects
                        modified_path = []
                        for cert in path:
                            if OID_PILOT_IDENTIFIER in [str(ext) for ext in cert.critical_extensions]:
                                # Temporarily remove pilot identifier from critical extensions
                                original_critical = cert._critical_extensions
                                cert._critical_extensions = set(ext for ext in original_critical if str(ext) != OID_PILOT_IDENTIFIER)
                                modified_path.append((cert, original_critical))
                            else:
                                modified_path.append((cert, None))

                        try:
                            # Call original validation with the same path object but modified certificates
                            result = orig_func(validation_context, path)
                            return result
                        finally:
                            # Restore original critical extensions
                            for cert, original_critical in modified_path:
                                if original_critical is not None:
                                    cert._critical_extensions = original_critical
                    else:
                        raise e

            certvalidator.validate._validate_path = patched_validate_path

        context = ValidationContext(trust_roots=roots,
                                    allow_fetching=self.opts.revocationCheckAndOscpCheck)
        validator = CertificateValidator(leaf,
                                            intermediate_certs=intermediates,
                                            validation_context=context)

        try:
            validator.validate_usage(
                # Any key usage
                key_usage=set([]),
                # 5.1.5. Verify that the end-entity certificate is a Verified Mark Certificate
                extended_key_usage=set([OID_EXT_KEY_USAGE_BIMI])
            )
        except Exception as e:
            string = str(e)
            exception_pattern_map = self._get_exception_certvalidator_pattern_map()
            found_pattern = False
            for exception, pattern in exception_pattern_map.items():
                if re.search(pattern=pattern, string=string):
                    found_pattern = True
                    e = exception(string)
                    if collectAllBimiFail:
                        self.bimiFailErrors.append(e)
                    else:
                        self._saveValidationResultToCache(key, e)
                        raise e
                    break

            if not found_pattern:
                e = BimiFail(string)
                if collectAllBimiFail:
                    self.bimiFailErrors.append(e)
                else:
                    self._saveValidationResultToCache(key, e)
                    raise e

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
                    e = BimiFailInvalidVMCUnmatchedDomain('the VMC is not valid for {} (valid domains include: {})'.format(hostname, ', '.join(vmc.valid_domains)))
                    if collectAllBimiFail:
                        self.bimiFailErrors.append(e)
                    else:
                        self._saveValidationResultToCache(key, e)
                        raise e

        # 5.1.4. Validate the proof of CT logging (if enabled)
        if self.opts.verifyCTLogging:
            self._validateCTLogging(vmc, collectAllBimiFail)

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
            e = BimiFailInvalidVMCUnmatchedSAN('domain does not match SAN in VMC')
            if collectAllBimiFail:
                self.bimiFailErrors.append(e)
            else:
                self._saveValidationResultToCache(key, e)
                raise e

        # Validation of VMC Evidence Document
        hashArr = []
        for ext in vmc['tbs_certificate']['extensions']:
            if ext['extn_id'].native == oidLogotype:
                if ext['critical'].native:
                    e = BimiFailInvalidVMCCriticalLogotype('the logotype extension in VMC is CRITICAL')
                    if collectAllBimiFail:
                        self.bimiFailErrors.append(e)
                    else:
                        self._saveValidationResultToCache(key, e)
                        raise e

                hashArr += extractHashArray(ext['extn_value'].native, extractSvg=extractSvg)

        if len(hashArr) == 0:
            e = BimiFailInvalidVMCNoHashFound('no hash found in VMC')
            if collectAllBimiFail:
                self.bimiFailErrors.append(e)
            else:
                self._saveValidationResultToCache(key, e)
                raise e

        if extractSvg:
            for hash in hashArr:
                self.svgImages.append(hash[1])

        if self.indicatorUri and self.opts.verifySVGImage:
            try:
                indicatorData = getData(uri=self.indicatorUri,
                                        localFile=self.localIndicator,
                                        timeout=self.httpOpts.httpTimeout,
                                        userAgent=self.httpOpts.httpUserAgent,
                                        maxSizeInBytes=self.indicatorOpts.maxSizeInBytes,
                                        cache=self.cache)

            except Exception:
                e = BimiFail('cannot get SVG logo file to compare with the image embedded in VMC certificate')
                if collectAllBimiFail:
                    self.bimiFailErrors.append(e)
                else:
                    self._saveValidationResultToCache(key, e)
                    raise e

            else:
                if indicatorData:
                    hashMatch = False
                    for hash in hashArr:
                        h = hashlib.new(hash[0].algorithm)
                        h.update(indicatorData)
                        if h.digest() == hash[0].value:
                            hashMatch = True
                            break

                    if not hashMatch:
                        e = BimiFailInvalidVMCUnmatchedSVG('SVG logo file is not binary equal to the image embedded in VMC certificate')
                        if collectAllBimiFail:
                            self.bimiFailErrors.append(e)
                        else:
                            self._saveValidationResultToCache(key, e)
                            raise e

                else:
                    e = BimiFail('SVG logo file is not valid to compare with the image embedded in VMC certificate')
                    if collectAllBimiFail:
                        self.bimiFailErrors.append(e)
                    else:
                        self._saveValidationResultToCache(key, e)
                        raise e

        self._saveValidationResultToCache(key, None)
        return c

    def _validateCTLogging(self, vmc, collectAllBimiFail=False):
        """
        Validate Certificate Transparency (CT) logging according to RFC 6962.
        The receiver must find one or more SCTs and validate they are signed
        by a recognized CT log.
        """
        sct_list = self._extractSCTList(vmc)

        if not sct_list:
            e = BimiFailInvalidVMCNoSCTFound('no SCT (Signed Certificate Timestamp) found in VMC')
            if collectAllBimiFail:
                self.bimiFailErrors.append(e)
            else:
                raise e
            return

        # Validate each SCT
        valid_sct_found = False
        for sct in sct_list:
            try:
                if self._validateSCT(sct, vmc):
                    valid_sct_found = True
                    break
            except Exception:
                # Continue trying other SCTs if one fails
                continue

        if not valid_sct_found:
            e = BimiFailInvalidVMCInvalidSCT('no valid SCT found - SCT validation failed')
            if collectAllBimiFail:
                self.bimiFailErrors.append(e)
            else:
                raise e

    def _extractSCTList(self, vmc):
        """
        Extract SCT list from certificate extensions.
        SCTs are embedded in the certificate as an X.509v3 extension.
        """
        for ext in vmc['tbs_certificate']['extensions']:
            if ext['extn_id'].native == OID_SCT_LIST:
                # SCT list is encoded as an ASN.1 OCTET STRING
                sct_list_data = ext['extn_value'].native
                return self._parseSCTList(sct_list_data)
        return []

    def _parseSCTList(self, sct_list_data):
        """
        Parse SCT list according to RFC 6962 Section 3.3.
        The SCT list is a length-prefixed list of individual SCTs.
        """
        if len(sct_list_data) < 2:
            return []

        # First 2 bytes are the length of the entire list
        list_length = struct.unpack('>H', sct_list_data[:2])[0]
        if list_length != len(sct_list_data) - 2:
            return []

        scts = []
        offset = 2

        while offset < len(sct_list_data):
            if offset + 2 > len(sct_list_data):
                break

            # Each SCT is length-prefixed with 2 bytes
            sct_length = struct.unpack('>H', sct_list_data[offset:offset+2])[0]
            offset += 2

            if offset + sct_length > len(sct_list_data):
                break

            sct_data = sct_list_data[offset:offset+sct_length]
            if len(sct_data) >= 43:  # Minimum SCT size
                scts.append(self._parseSCT(sct_data))

            offset += sct_length

        return scts

    def _parseSCT(self, sct_data):
        """
        Parse individual SCT according to RFC 6962 Section 3.2.
        SCT structure:
        - Version (1 byte)
        - Log ID (32 bytes)
        - Timestamp (8 bytes)
        - Extensions length (2 bytes)
        - Extensions (variable)
        - Signature (variable)
        """
        if len(sct_data) < 43:
            return None

        offset = 0

        # Version
        version = sct_data[offset]
        offset += 1

        # Log ID (32 bytes)
        log_id = sct_data[offset:offset+32]
        offset += 32

        # Timestamp (8 bytes, big endian)
        timestamp = struct.unpack('>Q', sct_data[offset:offset+8])[0]
        offset += 8

        # Extensions length
        ext_length = struct.unpack('>H', sct_data[offset:offset+2])[0]
        offset += 2

        # Extensions
        extensions = sct_data[offset:offset+ext_length]
        offset += ext_length

        # Signature
        signature = sct_data[offset:]

        return {
            'version': version,
            'log_id': log_id,
            'timestamp': timestamp,
            'extensions': extensions,
            'signature': signature
        }

    def _validateSCT(self, sct, vmc):
        """
        Validate SCT according to RFC 6962 requirements:
        1. Check timestamp is not in the future
        2. Verify signature (simplified check)

        Note: vmc parameter is kept for potential future signature verification
        """
        if not sct:
            return False

        # Check timestamp is not in the future (RFC 6962)
        current_time_ms = int(time.time() * 1000)
        if sct['timestamp'] > current_time_ms:
            raise BimiFailInvalidVMCSCTFutureTimestamp('SCT timestamp is in the future')

        # For production use, you would verify the signature using the CT log's public key
        # This requires maintaining a list of trusted CT logs and their public keys
        # For now, we perform basic structural validation

        # Basic validation: check required fields are present
        required_fields = ['version', 'log_id', 'timestamp', 'signature']
        for field in required_fields:
            if field not in sct or sct[field] is None:
                return False

        # Check version is supported (currently only version 0)
        if sct['version'] != 0:
            return False

        # Check log_id is correct length (32 bytes)
        if len(sct['log_id']) != 32:
            return False

        # Check signature is present and reasonable length
        if len(sct['signature']) < 64:  # Minimum signature length
            return False

        return True

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
                      trademarkRegistration=c['subject'][OID_TRADEMARK_REGISTRATION],
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

        except Exception:
            return None

    def _get_exception_certvalidator_pattern_map(self):
        # TODO: Update map if upgrade certvalidator
        return {
            BimiFailInvalidVMCUnsupportedAlgorithm: '^The path could not be validated because the signature of .+ uses the unsupported algorithm .+$',
            BimiFailInvalidVMCCannotVerify: '^The path could not be validated because the signature of .+ could not be verified$',
            BimiFailInvalidVMCNotValidBefore: '^The path could not be validated because .+ is not valid until .+$',
            BimiFailInvalidVMCExpiredAfter: '^The path could not be validated because .+ expired .+$',
            BimiFailInvalidVMCNoRevocationFound: '^The path could not be validated because no revocation information could be found for .+$',
            BimiFailInvalidVMCCheckRevocationFailed: '^The path could not be validated because the .+ revocation checks failed: .+$',
            BimiFailInvalidVMCIssuerNotMatch: '^The path could not be validated because the .+ issuer name could not be matched$',
            BimiFailInvalidVMCAnyPolicyFound: '^The path could not be validated because .+ contains a policy mapping for the "any policy"$',
            BimiFailInvalidVMCNotCA: '^The path could not be validated because .+ is not a CA$',
            BimiFailInvalidVMCExceedMaximumPathLength: '^The path could not be validated because it exceeds the maximum path length$',
            BimiFailInvalidVMCNotAllowToSign: '^The path could not be validated because + is not allowed to sign certificates$',
            BimiFailInvalidVMCUnsupportedCriticalExtensionFound: '^The path could not be validated because .+ contains the following unsupported critical extension.*: .+$',
            BimiFailInvalidVMCNoValidPolicySetFound: '^The path could not be validated because there is no valid set of policies for .+$',
            BimiFailInvalidVMCNoMatchingIssuerFound: '^Unable to build a validation path for the certificate .+ - no issuer matching .+ was found$',
            BimiFailInvalidVMCNoSCTFound: r'^no SCT \(Signed Certificate Timestamp\) found in VMC$',
            BimiFailInvalidVMCInvalidSCT: '^no valid SCT found - SCT validation failed$',
            BimiFailInvalidVMCSCTFutureTimestamp: '^SCT timestamp is in the future$',
        }
