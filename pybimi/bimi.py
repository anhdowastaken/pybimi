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
        """
        Return string representation of the BIMI record.

        Returns:
            Formatted string with domain, selector, location, and authority info
        """
        return (f'd: {self.domain}, s: {self.selector}, '
                f'l: {self.location}, a: {self.authorityEvidenceLocation}')

    def has_indicator(self) -> bool:
        """
        Check if this record has a valid indicator location.

        Returns:
            True if location field is not empty
        """
        return bool(self.location and self.location.strip())

    def has_authority_evidence(self) -> bool:
        """
        Check if this record has authority evidence (VMC).

        Returns:
            True if authority evidence location is not empty
        """
        return bool(self.authorityEvidenceLocation and
                   self.authorityEvidenceLocation.strip())
