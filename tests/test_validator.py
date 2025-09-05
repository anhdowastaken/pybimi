import unittest
from unittest.mock import Mock, patch

from pybimi.validator import Validator
from pybimi.bimi import BimiRecord
from pybimi.exception import *
from pybimi.options import LookupOptions, IndicatorOptions, VmcOptions, HttpOptions
from pybimi.cache import Cache


class TestValidator(unittest.TestCase):

    def setUp(self):
        self.domain = "example.com"
        self.validator = Validator(self.domain)

    def test_init_with_defaults(self):
        """Test initialization with default options"""
        validator = Validator("example.com")
        self.assertEqual(validator.domain, "example.com")
        self.assertIsInstance(validator.lookupOpts, LookupOptions)
        self.assertIsInstance(validator.indicatorOpts, IndicatorOptions)
        self.assertIsInstance(validator.vmcOpts, VmcOptions)
        self.assertIsInstance(validator.httpOpts, HttpOptions)
        self.assertIsNone(validator.cache)

    def test_init_with_custom_options(self):
        """Test initialization with custom options"""
        lookup_opts = LookupOptions(selector="test")
        indicator_opts = IndicatorOptions(maxSizeInBytes=2048)
        vmc_opts = VmcOptions(verifyDNSName=False)
        http_opts = HttpOptions(httpTimeout=30)
        cache = Cache()

        validator = Validator(
            "example.com",
            lookupOpts=lookup_opts,
            indicatorOpts=indicator_opts,
            vmcOpts=vmc_opts,
            httpOpts=http_opts,
            cache=cache
        )

        self.assertEqual(validator.lookupOpts.selector, "test")
        self.assertEqual(validator.indicatorOpts.maxSizeInBytes, 2048)
        self.assertFalse(validator.vmcOpts.verifyDNSName)
        self.assertEqual(validator.httpOpts.httpTimeout, 30)
        self.assertIsNotNone(validator.cache)

    @patch('pybimi.validator.VmcValidator')
    @patch('pybimi.validator.IndicatorValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_full_success(self, mock_lookup, mock_indicator, mock_vmc):
        """Test successful full validation"""
        # Mock BIMI record
        mock_record = BimiRecord()
        mock_record.domain = "example.com"
        mock_record.location = "https://example.com/logo.svg"
        mock_record.authorityEvidenceLocation = "https://example.com/vmc.pem"

        # Mock validators
        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        mock_indicator_instance = Mock()
        mock_indicator_instance.validate.return_value = None
        mock_indicator.return_value = mock_indicator_instance

        mock_vmc_instance = Mock()
        mock_vmc_instance.validate.return_value = None
        mock_vmc.return_value = mock_vmc_instance

        result = self.validator.validate()

        self.assertEqual(result, mock_record)
        mock_lookup.assert_called_once()
        mock_indicator.assert_called_once()
        mock_vmc.assert_called_once()

    @patch('pybimi.validator.VmcValidator')
    @patch('pybimi.validator.IndicatorValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_skip_indicator(self, mock_lookup, mock_indicator, mock_vmc):
        """Test validation with indicator validation skipped"""
        # Mock BIMI record
        mock_record = BimiRecord()
        mock_record.domain = "example.com"
        mock_record.location = "https://example.com/logo.svg"
        mock_record.authorityEvidenceLocation = "https://example.com/vmc.pem"

        # Mock lookup validator
        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        # Mock VMC validator
        mock_vmc_instance = Mock()
        mock_vmc_instance.validate.return_value = None
        mock_vmc.return_value = mock_vmc_instance

        result = self.validator.validate(validateIndicator=False)

        self.assertEqual(result, mock_record)
        mock_lookup.assert_called_once()
        mock_indicator.assert_not_called()
        mock_vmc.assert_called_once()

    @patch('pybimi.validator.VmcValidator')
    @patch('pybimi.validator.IndicatorValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_skip_vmc(self, mock_lookup, mock_indicator, mock_vmc):
        """Test validation with VMC validation skipped"""
        # Mock BIMI record
        mock_record = BimiRecord()
        mock_record.domain = "example.com"
        mock_record.location = "https://example.com/logo.svg"
        mock_record.authorityEvidenceLocation = "https://example.com/vmc.pem"

        # Mock lookup validator
        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        # Mock indicator validator
        mock_indicator_instance = Mock()
        mock_indicator_instance.validate.return_value = None
        mock_indicator.return_value = mock_indicator_instance

        result = self.validator.validate(validateVmc=False)

        self.assertEqual(result, mock_record)
        mock_lookup.assert_called_once()
        mock_indicator.assert_called_once()
        mock_vmc.assert_not_called()

    @patch('pybimi.validator.LookupValidator')
    def test_validate_lookup_failure_propagated(self, mock_lookup):
        """Test that lookup validation failures are propagated"""
        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.side_effect = BimiNoPolicy("No policy found")
        mock_lookup.return_value = mock_lookup_instance

        with self.assertRaises(BimiNoPolicy):
            self.validator.validate()

    @patch('pybimi.validator.IndicatorValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_indicator_failure_propagated(self, mock_lookup, mock_indicator):
        """Test that indicator validation failures are propagated"""
        # Mock successful lookup
        mock_record = BimiRecord()
        mock_record.location = "https://example.com/logo.svg"
        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        # Mock indicator validation failure
        mock_indicator_instance = Mock()
        mock_indicator_instance.validate.side_effect = BimiFailInvalidSVG("Invalid SVG")
        mock_indicator.return_value = mock_indicator_instance

        with self.assertRaises(BimiFailInvalidSVG):
            self.validator.validate()

    @patch('pybimi.validator.VmcValidator')
    @patch('pybimi.validator.IndicatorValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_vmc_failure_propagated(self, mock_lookup, mock_indicator, mock_vmc):
        """Test that VMC validation failures are propagated"""
        # Mock successful lookup and indicator validation
        mock_record = BimiRecord()
        mock_record.location = "https://example.com/logo.svg"
        mock_record.authorityEvidenceLocation = "https://example.com/vmc.pem"

        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        mock_indicator_instance = Mock()
        mock_indicator_instance.validate.return_value = None
        mock_indicator.return_value = mock_indicator_instance

        # Mock VMC validation failure
        mock_vmc_instance = Mock()
        mock_vmc_instance.validate.side_effect = BimiFailInvalidVMC("Invalid VMC")
        mock_vmc.return_value = mock_vmc_instance

        with self.assertRaises(BimiFailInvalidVMC):
            self.validator.validate()

    @patch('pybimi.validator.IndicatorValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_with_cache(self, mock_lookup, mock_indicator):
        """Test validation with cache"""
        cache = Cache()
        validator = Validator("example.com", cache=cache)

        # Mock successful lookup
        mock_record = BimiRecord()
        mock_record.location = "https://example.com/logo.svg"
        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        # Mock indicator validator to verify cache is passed
        mock_indicator_instance = Mock()
        mock_indicator_instance.validate.return_value = None
        mock_indicator.return_value = mock_indicator_instance

        result = validator.validate(validateVmc=False)

        # Verify cache was passed to indicator validator
        mock_indicator.assert_called_once()
        args, kwargs = mock_indicator.call_args
        self.assertEqual(kwargs.get('cache'), cache)

    @patch('pybimi.validator.VmcValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_vmc_constructor_params(self, mock_lookup, mock_vmc):
        """Test VMC validator receives correct constructor parameters"""
        # Mock successful lookup
        mock_record = BimiRecord()
        mock_record.domain = "example.com"
        mock_record.location = "https://example.com/logo.svg"
        mock_record.authorityEvidenceLocation = "https://example.com/vmc.pem"

        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        mock_vmc_instance = Mock()
        mock_vmc_instance.validate.return_value = None
        mock_vmc.return_value = mock_vmc_instance

        self.validator.validate(validateIndicator=False)

        # Verify VMC validator constructor parameters
        mock_vmc.assert_called_once_with(
            vmcUri="https://example.com/vmc.pem",
            indicatorUri="https://example.com/logo.svg",
            domain="example.com",
            opts=self.validator.vmcOpts,
            lookupOpts=self.validator.lookupOpts,
            indicatorOpts=self.validator.indicatorOpts,
            httpOpts=self.validator.httpOpts,
            cache=self.validator.cache
        )

    @patch('pybimi.validator.IndicatorValidator')
    @patch('pybimi.validator.LookupValidator')
    def test_validate_indicator_constructor_params(self, mock_lookup, mock_indicator):
        """Test indicator validator receives correct constructor parameters"""
        # Mock successful lookup
        mock_record = BimiRecord()
        mock_record.location = "https://example.com/logo.svg"

        mock_lookup_instance = Mock()
        mock_lookup_instance.validate.return_value = mock_record
        mock_lookup.return_value = mock_lookup_instance

        mock_indicator_instance = Mock()
        mock_indicator_instance.validate.return_value = None
        mock_indicator.return_value = mock_indicator_instance

        self.validator.validate(validateVmc=False)

        # Verify indicator validator constructor parameters
        mock_indicator.assert_called_once_with(
            uri="https://example.com/logo.svg",
            opts=self.validator.indicatorOpts,
            httpOpts=self.validator.httpOpts,
            cache=self.validator.cache
        )


if __name__ == '__main__':
    unittest.main()
