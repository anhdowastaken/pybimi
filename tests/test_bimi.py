import unittest

from pybimi.bimi import BimiRecord, DEFAULT_SELECTOR, CURRENT_VERSION
from pybimi.bimi import SELECTOR_FIELD_NAME, LOCATION_FIELD_NAME, INDICATOR_FIELD_NAME


class TestBimiRecord(unittest.TestCase):

    def test_init_defaults(self):
        """Test BimiRecord initialization with defaults"""
        record = BimiRecord()

        self.assertIsNone(record.domain)
        self.assertEqual(record.selector, DEFAULT_SELECTOR)
        self.assertIsNone(record.location)
        self.assertIsNone(record.authorityEvidenceLocation)

    def test_init_all_fields(self):
        """Test BimiRecord with all fields set"""
        record = BimiRecord()
        record.domain = "example.com"
        record.selector = "test"
        record.location = "https://example.com/logo.svg"
        record.authorityEvidenceLocation = "https://example.com/vmc.pem"

        self.assertEqual(record.domain, "example.com")
        self.assertEqual(record.selector, "test")
        self.assertEqual(record.location, "https://example.com/logo.svg")
        self.assertEqual(record.authorityEvidenceLocation, "https://example.com/vmc.pem")

    def test_repr(self):
        """Test string representation of BimiRecord"""
        record = BimiRecord()
        record.domain = "example.com"
        record.selector = "default"
        record.location = "https://example.com/logo.svg"
        record.authorityEvidenceLocation = "https://example.com/vmc.pem"

        expected = "d: example.com, s: default, l: https://example.com/logo.svg, a: https://example.com/vmc.pem"
        self.assertEqual(repr(record), expected)

    def test_repr_with_none_values(self):
        """Test string representation with None values"""
        record = BimiRecord()

        expected = "d: None, s: default, l: None, a: None"
        self.assertEqual(repr(record), expected)

    def test_constants(self):
        """Test BIMI constants are properly defined"""
        self.assertEqual(SELECTOR_FIELD_NAME, 'BIMI-Selector')
        self.assertEqual(LOCATION_FIELD_NAME, 'BIMI-Location')
        self.assertEqual(INDICATOR_FIELD_NAME, 'BIMI-Indicator')
        self.assertEqual(CURRENT_VERSION, 'BIMI1')
        self.assertEqual(DEFAULT_SELECTOR, 'default')


if __name__ == '__main__':
    unittest.main()
