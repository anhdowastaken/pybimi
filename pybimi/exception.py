class BimiError(Exception):
    """Base class for other errors"""

class BimiNoPolicy(BimiError):
    """Raised when the domain doesn't support BIMI"""

class BimiDeclined(BimiError):
    """Raised when the domain declines BIMI"""

class BimiTempfail(BimiError):
    """
    Raised when there is any problem in the environment.
    The problem can be resolved by retrying later.
    """

class BimiTemfailCannotAccess(BimiTempfail):
    """Raised when cannot access or cannot download the thing"""

class BimiTemfailJingError(BimiTempfail):
    """Raised when cannot use Java to run Jing"""

class BimiFail(BimiError):
    """Raised when any critical error is found"""

class BimiFailSizeLimitExceeded(BimiFail):
    """Raised when size limit exceeded"""

class BimiFailInvalidURI(BimiFail):
    """Raised when input URI is invalid"""

class BimiFailInvalidFormat(BimiFail):
    """Raised when format is invalid"""

class BimiFailInvalidSVG(BimiFail):
    """Raised when SVG logo image is invalid"""

class BimiFailInvalidVMC(BimiFail):
    """Raised when VMC certificate is invalid"""

class BimiFailInvalidVMCNotPEM(BimiFailInvalidVMC):
    """Raised when input data is not valid PEM-encoded data"""

class BimiFailInvalidVMCNoLeafFound(BimiFailInvalidVMC):
    """Raised when no VMC found"""

class BimiFailInvalidVMCMultiLeafs(BimiFailInvalidVMC):
    """Raised when more than one VMC found"""

class BimiFailInvalidVMCUnmatchedDomain(BimiFailInvalidVMC):
    """Raised when the VMC is not valid for input domain"""

class BimiFailInvalidVMCUnmatchedSAN(BimiFailInvalidVMC):
    """Raised when SAN in the VMC does not match input domain"""

class BimiFailInvalidVMCCriticalLogotype(BimiFailInvalidVMC):
    """Raised when the logotype extension in the VMC is CRITICAL"""

class BimiFailInvalidVMCNoHashFound(BimiFailInvalidVMC):
    """Raised when no hash found in the VMC"""

class BimiFailInvalidVMCUnmatchedSVG(BimiFailInvalidVMC):
    """Raised when input SVG logo file is not binary equal to the image embedded in the VMC"""

class BimiFailInvalidVMCUnsupportedAlgorithm(BimiFailInvalidVMC):
    """Raised when the signature uses the unsupported algorithm"""

class BimiFailInvalidVMCCannotVerify(BimiFailInvalidVMC):
    """Raised when the signature could not be verified"""

class BimiFailInvalidVMCNotValidBefore(BimiFailInvalidVMC):
    """Raised when the certificate is only valid after now"""

class BimiFailInvalidVMCExpiredAfter(BimiFailInvalidVMC):
    """Raised when the certificate was expired now"""

class BimiFailInvalidVMCNoRevocationFound(BimiFailInvalidVMC):
    """Raised when no revocation information could be found"""

class BimiFailInvalidVMCCheckRevocationFailed(BimiFailInvalidVMC):
    """Raised when check revocation failed"""

class BimiFailInvalidVMCIssuerNotMatch(BimiFailInvalidVMC):
    """Raised when the issuer does not match"""

class BimiFailInvalidVMCAnyPolicyFound(BimiFailInvalidVMC):
    """Raised when a policy mapping for the \"any policy\""""

class BimiFailInvalidVMCNotCA(BimiFailInvalidVMC):
    """Raised when the certificate is not CA"""

class BimiFailInvalidVMCExceedMaximumPathLength(BimiFailInvalidVMC):
    """Raised when maximum path length was exceeded"""
class BimiFailInvalidVMCNotAllowToSign(BimiFailInvalidVMC):
    """Raised when the certificate is not allowed to be signed"""

class BimiFailInvalidVMCUnsupportedCriticalExtensionFound(BimiFailInvalidVMC):
    """Raised when an unsupported critical extension found"""

class BimiFailInvalidVMCNoValidPolicySetFound(BimiFailInvalidVMC):
    """Raised when no valid policy set found"""

class BimiFailInvalidVMCNoMatchingIssuerFound(BimiFailInvalidVMC):
    """Raised when no matching issuer found"""

class BimiFailInvalidVMCNoSCTFound(BimiFailInvalidVMC):
    """Raised when no SCT (Signed Certificate Timestamp) found in VMC"""

class BimiFailInvalidVMCInvalidSCT(BimiFailInvalidVMC):
    """Raised when SCT validation fails"""

class BimiFailInvalidVMCSCTFutureTimestamp(BimiFailInvalidVMC):
    """Raised when SCT timestamp is in the future"""
