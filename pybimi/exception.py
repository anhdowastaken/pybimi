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

class BimiFail(BimiError):
    """Raised when any critical error is found"""
