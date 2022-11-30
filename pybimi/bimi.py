SELECTOR_FIELD_NAME     = 'BIMI-Selector'
LOCATION_FIELD_NAME     = 'BIMI-Location'
INDICATOR_FIELD_NAME    = 'BIMI-Indicator'
CURRENT_VERSION         = 'BIMI1'
DEFAULT_SELECTOR        = 'default'

class BimiRecord:
    def __init__(self) -> None:
        self.domain = ''
        self.selector = DEFAULT_SELECTOR
        self.location = ''
        self.authorityEvidenceLocation = ''

    def __repr__(self) -> str:
        return 'd: {}, s: {}, l: {}, a: {}' \
            .format(self.domain, self.selector, self.location, self.authorityEvidenceLocation)
