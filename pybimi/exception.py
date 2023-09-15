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