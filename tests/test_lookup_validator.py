import unittest
from unittest.mock import Mock, patch
import dns.resolver

from pybimi.lookup_validator import LookupValidator
from pybimi.bimi import BimiRecord, DEFAULT_SELECTOR
from pybimi.exception import (
    BimiNoPolicy, BimiDeclined, BimiFailInvalidFormat, BimiFail, BimiTemfailCannotAccess
)
from pybimi.options import LookupOptions


class TestLookupValidator(unittest.TestCase):

    def setUp(self):
        self.domain = "example.com"
        self.validator = LookupValidator(self.domain)

    def test_init_with_default_selector(self):
        """Test initialization with default selector"""
        validator = LookupValidator("example.com")
        self.assertEqual(validator.domain, "example.com")
        self.assertEqual(validator.actualSelector, DEFAULT_SELECTOR)

    def test_init_with_custom_selector(self):
        """Test initialization with custom selector"""
        opts = LookupOptions(selector="test")
        validator = LookupValidator("example.com", opts)
        self.assertEqual(validator.actualSelector, "test")

    def test_parse_valid_bimi_record(self):
        """Test parsing a valid BIMI DNS record"""
        txt = "v=BIMI1; l=https://example.com/logo.svg; a=https://example.com/vmc.pem"
        record = self.validator.parse(txt)

        self.assertIsInstance(record, BimiRecord)
        self.assertEqual(record.location, "https://example.com/logo.svg")
        self.assertEqual(record.authorityEvidenceLocation, "https://example.com/vmc.pem")
        self.assertEqual(record.domain, self.domain)
        self.assertEqual(record.selector, DEFAULT_SELECTOR)

    def test_parse_minimal_bimi_record(self):
        """Test parsing minimal BIMI record with only required tags"""
        txt = "v=BIMI1; l=https://example.com/logo.svg"
        record = self.validator.parse(txt)

        self.assertEqual(record.location, "https://example.com/logo.svg")
        self.assertIsNone(record.authorityEvidenceLocation)

    def test_parse_empty_record_raises_no_policy(self):
        """Test that empty record raises BimiNoPolicy"""
        with self.assertRaises(BimiNoPolicy):
            self.validator.parse("")

    def test_parse_declined_record(self):
        """Test that record with empty l and a tags raises BimiDeclined"""
        txt = "v=BIMI1; l=; a="
        with self.assertRaises(BimiDeclined):
            self.validator.parse(txt)

    def test_parse_invalid_version_raises_error(self):
        """Test that invalid version raises BimiFailInvalidFormat"""
        txt = "v=BIMI2; l=https://example.com/logo.svg"
        with self.assertRaises(BimiFailInvalidFormat):
            self.validator.parse(txt)

    def test_parse_missing_version_raises_error(self):
        """Test that missing version tag raises error"""
        txt = "l=https://example.com/logo.svg"
        with self.assertRaises(BimiFailInvalidFormat):
            self.validator.parse(txt)

    def test_parse_missing_location_raises_error(self):
        """Test that missing location tag raises error"""
        txt = "v=BIMI1; a=https://example.com/vmc.pem"
        with self.assertRaises(BimiFailInvalidFormat):
            self.validator.parse(txt)

    def test_parse_version_not_first_raises_error(self):
        """Test that version tag not being first raises error"""
        txt = "l=https://example.com/logo.svg; v=BIMI1"
        with self.assertRaises(BimiFailInvalidFormat):
            self.validator.parse(txt)

    def test_parse_unknown_tag_raises_error(self):
        """Test that unknown tags raise error"""
        txt = "v=BIMI1; l=https://example.com/logo.svg; unknown=value"
        with self.assertRaises(BimiFailInvalidFormat):
            self.validator.parse(txt)

    def test_parse_invalid_tag_format_raises_error(self):
        """Test that invalid tag format raises error"""
        txt = "v=BIMI1; invalid_tag; l=https://example.com/logo.svg"
        with self.assertRaises(BimiFailInvalidFormat):
            self.validator.parse(txt)

    def test_parse_collect_all_errors(self):
        """Test parsing with collectAllBimiFail option"""
        txt = "unknown=value; v=BIMI1; l=https://example.com/logo.svg; extra=tag"
        self.validator.parse(txt, collectAllBimiFail=True)
        self.assertTrue(len(self.validator.bimiFailErrors) > 0)

    @patch('dns.resolver.Resolver.resolve')
    def test_lookup_success(self, mock_resolve):
        """Test successful DNS lookup"""
        mock_answer = Mock()
        mock_answer.to_text.return_value = '"v=BIMI1; l=https://example.com/logo.svg"'
        mock_resolve.return_value = [mock_answer]

        result = self.validator._lookup()
        self.assertEqual(result, "v=BIMI1; l=https://example.com/logo.svg")

    @patch('dns.resolver.Resolver.resolve')
    def test_lookup_nxdomain_raises_no_policy(self, mock_resolve):
        """Test that NXDOMAIN raises BimiNoPolicy"""
        mock_resolve.side_effect = dns.resolver.NXDOMAIN()

        with self.assertRaises(BimiNoPolicy):
            self.validator._lookup()

    @patch('dns.resolver.Resolver.resolve')
    def test_lookup_timeout_raises_tempfail(self, mock_resolve):
        """Test that timeout raises BimiTempfail"""
        mock_resolve.side_effect = dns.resolver.LifetimeTimeout()

        with self.assertRaises(BimiTemfailCannotAccess):
            self.validator._lookup()

    @patch('dns.resolver.Resolver.resolve')
    def test_lookup_with_custom_nameserver(self, mock_resolve):
        """Test DNS lookup with custom nameserver"""
        mock_answer = Mock()
        mock_answer.to_text.return_value = '"v=BIMI1; l=https://example.com/logo.svg"'
        mock_resolve.return_value = [mock_answer]

        opts = LookupOptions(ns=["8.8.8.8"])
        validator = LookupValidator("example.com", opts)
        result = validator._lookup()

        self.assertEqual(result, "v=BIMI1; l=https://example.com/logo.svg")

    def test_empty_domain_raises_error(self):
        """Test that empty domain raises BimiFail"""
        validator = LookupValidator("")
        with self.assertRaises(BimiFail):
            validator.validate()

    @patch('pybimi.lookup_validator.get_fld')
    @patch.object(LookupValidator, '_lookup')
    def test_fallback_to_fld_on_failure(self, mock_lookup, mock_get_fld):
        """Test fallback to effective top-level domain on lookup failure"""
        mock_get_fld.return_value = "example.com"
        mock_lookup.side_effect = [BimiNoPolicy(), "v=BIMI1; l=https://example.com/logo.svg"]

        validator = LookupValidator("subdomain.example.com")
        record = validator.validate()

        self.assertEqual(validator.actualDomain, "example.com")
        self.assertIsInstance(record, BimiRecord)
        self.assertEqual(mock_lookup.call_count, 2)


if __name__ == '__main__':
    unittest.main()
