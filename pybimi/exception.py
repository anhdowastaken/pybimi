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