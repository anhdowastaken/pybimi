SELECTOR_FIELD_NAME     = 'BIMI-Selector'
LOCATION_FIELD_NAME     = 'BIMI-Location'
INDICATOR_FIELD_NAME    = 'BIMI-Indicator'
CURRENT_VERSION         = 'BIMI1'
DEFAULT_SELECTOR        = 'default'

oidExtKeyUsageBrandIndicatorForMessageIdentification = '1.3.6.1.5.5.7.3.31'

class BimiRecord:
    def __init__(self) -> None:
        self.domain = ''
        self.selector = DEFAULT_SELECTOR
        self.location = ''
        self.authorityEvidenceLocation = ''

    def __repr__(self) -> str:
        return 'd: {}, s: {}, l: {}, a: {}' \
            .format(self.domain, self.selector, self.location, self.authorityEvidenceLocation)
