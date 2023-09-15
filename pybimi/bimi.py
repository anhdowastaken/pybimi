SELECTOR_FIELD_NAME     = 'BIMI-Selector'
LOCATION_FIELD_NAME     = 'BIMI-Location'
INDICATOR_FIELD_NAME    = 'BIMI-Indicator'
CURRENT_VERSION         = 'BIMI1'
DEFAULT_SELECTOR        = 'default'

class BimiRecord:
    """
    A class used to represent an BIMI record

    Attributes
    ----------
    domain: str
        The domain that the BIMI record belongs to
    selector: str
        The selector which is used to query the BIMI DNS record
    location: str
        Value of the "l=" tag
    authorityEvidenceLocation: str
        Value of the "a=" tag
    """

    def __init__(self) -> None:
        self.domain = None
        self.selector = DEFAULT_SELECTOR
        self.location = None
        self.authorityEvidenceLocation = None

    def __repr__(self) -> str:
        return 'd: {}, s: {}, l: {}, a: {}' \
            .format(self.domain, self.selector, self.location, self.authorityEvidenceLocation)
