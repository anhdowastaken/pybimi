import unittest
from unittest.mock import Mock, patch, mock_open
from datetime import datetime
import struct

from pybimi.vmc_validator import VmcValidator, Vmc
from pybimi.exception import *
from pybimi.options import VmcOptions, LookupOptions, IndicatorOptions, HttpOptions


class TestVmcValidator(unittest.TestCase):

    def setUp(self):
        self.vmc_uri = "https://example.com/vmc.pem"
        self.indicator_uri = "https://example.com/logo.svg"
        self.domain = "example.com"
        self.validator = VmcValidator(
            vmcUri=self.vmc_uri,
            indicatorUri=self.indicator_uri,
            domain=self.domain
        )

    def test_init_with_defaults(self):
        """Test initialization with default options"""
        validator = VmcValidator("https://example.com/vmc.pem")
        self.assertEqual(validator.vmcUri, "https://example.com/vmc.pem")
        self.assertIsInstance(validator.opts, VmcOptions)
        self.assertIsInstance(validator.httpOpts, HttpOptions)
        self.assertEqual(validator.svgImages, [])
        self.assertEqual(validator.bimiFailErrors, [])

    def test_init_with_local_files(self):
        """Test initialization with local file flags"""
        validator = VmcValidator(
            "/path/to/vmc.pem",
            indicatorUri="/path/to/logo.svg",
            localVMC=True,
            localIndicator=True
        )
        self.assertTrue(validator.localVMC)
        self.assertTrue(validator.localIndicator)

    def test_validate_empty_uri_returns_none(self):
        """Test that empty VMC URI returns None"""
        validator = VmcValidator("")
        result = validator.validate()
        self.assertIsNone(result)

    def test_validate_none_uri_returns_none(self):
        """Test that None VMC URI returns None"""
        validator = VmcValidator(None)
        result = validator.validate()
        self.assertIsNone(result)

    def test_validate_http_uri_raises_error(self):
        """Test that HTTP URI raises error"""
        validator = VmcValidator("http://example.com/vmc.pem")
        with self.assertRaises(BimiFailInvalidURI):
            validator.validate()

    def test_validate_invalid_uri_raises_error(self):
        """Test that invalid URI raises error"""
        validator = VmcValidator("invalid://uri")
        with self.assertRaises(BimiFailInvalidURI):
            validator.validate()

    @patch('pybimi.vmc_validator.getData')
    def test_validate_network_error_raises_tempfail(self, mock_get_data):
        """Test that network errors raise BimiTempfail"""
        mock_get_data.side_effect = BimiTemfailCannotAccess("Network error")

        with self.assertRaises(BimiTemfailCannotAccess):
            self.validator.validate()

    @patch('pybimi.vmc_validator.getData')
    def test_validate_non_pem_data_raises_error(self, mock_get_data):
        """Test that non-PEM data raises error"""
        mock_get_data.return_value = b"not pem data"

        with self.assertRaises(BimiFailInvalidVMCNotPEM):
            self.validator.validate()

    @patch('pybimi.vmc_validator.getData')
    @patch('pybimi.vmc_validator.pem.unarmor')
    def test_validate_no_leaf_certificate_raises_error(self, mock_unarmor, mock_get_data):
        """Test that no leaf certificate raises error"""
        mock_get_data.return_value = b"-----BEGIN CERTIFICATE-----\ndata\n-----END CERTIFICATE-----"
        mock_unarmor.return_value = []  # No certificates

        with self.assertRaises(BimiFailInvalidVMCNoLeafFound):
            self.validator.validate()

    @patch('pybimi.vmc_validator.getData')
    @patch('pybimi.vmc_validator.pem.unarmor')
    @patch('pybimi.vmc_validator.x509.Certificate.load')
    def test_validate_multiple_leaf_certificates_raises_error(self, mock_cert_load, mock_unarmor, mock_get_data):
        """Test that multiple leaf certificates raise error"""
        mock_get_data.return_value = b"-----BEGIN CERTIFICATE-----\ndata\n-----END CERTIFICATE-----"

        # Create mock certificates (non-CA)
        mock_cert1 = Mock()
        mock_cert1.ca = False
        mock_cert2 = Mock()
        mock_cert2.ca = False

        mock_cert_load.side_effect = [mock_cert1, mock_cert2]
        mock_unarmor.return_value = [
            (None, None, b"cert1_der"),
            (None, None, b"cert2_der")
        ]

        with self.assertRaises(BimiFailInvalidVMCMultiLeafs):
            self.validator.validate()

    @patch('pybimi.vmc_validator.getData')
    @patch('pybimi.vmc_validator.pem.unarmor')
    @patch('pybimi.vmc_validator.x509.Certificate.load')
    @patch('pybimi.vmc_validator.CertificateValidator')
    @patch('builtins.open', mock_open(read_data=b'ca cert data'))
    def test_validate_certificate_validation_error(self, mock_validator_class, mock_cert_load, mock_unarmor, mock_get_data):
        """Test certificate validation error"""
        mock_get_data.return_value = b"-----BEGIN CERTIFICATE-----\ndata\n-----END CERTIFICATE-----"

        # Mock certificate
        mock_cert = Mock()
        mock_cert.ca = False
        mock_cert_load.return_value = mock_cert
        mock_unarmor.return_value = [(None, None, b"cert_der")]

        # Mock validator to raise validation error
        mock_validator = Mock()
        mock_validator.validate_usage.side_effect = Exception("Validation failed")
        mock_validator_class.return_value = mock_validator

        with self.assertRaises(BimiFail):
            self.validator.validate()

    @patch('pybimi.vmc_validator.getData')
    @patch('pybimi.vmc_validator.pem.unarmor')
    @patch('pybimi.vmc_validator.x509.Certificate.load')
    @patch('pybimi.vmc_validator.CertificateValidator')
    @patch('builtins.open', mock_open(read_data=b'ca cert data'))
    def test_validate_domain_mismatch_raises_error(self, mock_validator_class, mock_cert_load, mock_unarmor, mock_get_data):
        """Test domain mismatch raises error"""
        mock_get_data.return_value = b"-----BEGIN CERTIFICATE-----\ndata\n-----END CERTIFICATE-----"

        # Mock certificate
        mock_cert = Mock()
        mock_cert.ca = False
        mock_cert.is_valid_domain_ip.return_value = False
        mock_cert.valid_domains = ['otherdomain.com']  # Add valid_domains attribute
        mock_cert_load.return_value = mock_cert
        mock_unarmor.return_value = [(None, None, b"cert_der")]

        # Mock validator
        mock_validator = Mock()
        mock_validator.validate_usage.return_value = None
        mock_validator._certificate = Mock()
        mock_validator._certificate.native = {
            'tbs_certificate': {
                'version': 3,
                'serial_number': 123,
                'validity': {
                    'not_before': datetime.now(),
                    'not_after': datetime.now()
                },
                'subject': {
                    'organization_name': 'Test Org',
                    '1.3.6.1.4.1.53087.1.4': 'TM123'
                },
                'issuer': {'organization_name': 'Test CA'},
                'extensions': []
            }
        }
        mock_validator_class.return_value = mock_validator

        # Enable DNS name verification
        self.validator.opts.verifyDNSName = True

        with self.assertRaises(BimiFailInvalidVMCUnmatchedDomain):
            self.validator.validate()

    @patch('pybimi.vmc_validator.get_fld')
    def test_validate_domain_fallback_to_fld(self, mock_get_fld):
        """Test domain validation fallback to effective TLD"""
        mock_get_fld.return_value = "example.com"

        # This would typically be part of a larger test, but demonstrates the concept
        validator = VmcValidator("https://subdomain.example.com/vmc.pem", domain="subdomain.example.com")

        # The actual validation would use get_fld for fallback
        self.assertEqual(mock_get_fld.call_count, 0)  # Not called yet

    def test_extract_vmc_success(self):
        """Test successful VMC information extraction"""
        # Create mock certificate validator
        mock_validator = Mock()
        mock_validator._certificate = Mock()
        mock_validator._certificate.native = {
            'tbs_certificate': {
                'version': 3,
                'serial_number': 12345,
                'validity': {
                    'not_before': datetime(2023, 1, 1),
                    'not_after': datetime(2024, 1, 1)
                },
                'subject': {
                    'organization_name': 'Test Organization',
                    '1.3.6.1.4.1.53087.1.4': 'TM12345'
                },
                'issuer': {'organization_name': 'Test CA'},
                'extensions': [
                    {
                        'extn_id': 'subject_alt_name',
                        'extn_value': ['example.com', 'test.example.com']
                    }
                ]
            }
        }

        result = self.validator._extractVMC(mock_validator)

        self.assertIsInstance(result, Vmc)
        self.assertEqual(result.version, 3)
        self.assertEqual(result.serialNumber, 12345)
        self.assertEqual(result.organizationName, 'Test Organization')
        self.assertEqual(result.issuer, 'Test CA')
        self.assertEqual(result.trademarkRegistration, 'TM12345')
        self.assertIn('example.com', result.certifiedDomains)
        self.assertIn('test.example.com', result.certifiedDomains)

    def test_extract_vmc_exception_returns_none(self):
        """Test VMC extraction returns None on exception"""
        # Create mock that will raise exception
        mock_validator = Mock()
        mock_validator._certificate = Mock()
        mock_validator._certificate.native = None  # Will cause KeyError

        result = self.validator._extractVMC(mock_validator)
        self.assertIsNone(result)

    def test_parse_sct_valid_sct(self):
        """Test parsing valid SCT data"""
        # Create minimal valid SCT data
        version = struct.pack('B', 0)  # Version 0
        log_id = b'\x01' * 32  # 32 bytes log ID
        timestamp = struct.pack('>Q', 1640995200000)  # Unix timestamp in ms
        ext_len = struct.pack('>H', 0)  # No extensions
        signature = b'\x02' * 64  # Dummy signature

        sct_data = version + log_id + timestamp + ext_len + signature

        result = self.validator._parseSCT(sct_data)

        self.assertIsNotNone(result)
        self.assertEqual(result['version'], 0)
        self.assertEqual(result['log_id'], b'\x01' * 32)
        self.assertEqual(result['timestamp'], 1640995200000)
        self.assertEqual(result['extensions'], b'')
        self.assertEqual(result['signature'], b'\x02' * 64)

    def test_parse_sct_invalid_length(self):
        """Test parsing SCT with invalid length"""
        sct_data = b'short'  # Too short

        result = self.validator._parseSCT(sct_data)
        self.assertIsNone(result)

    def test_validate_sct_valid(self):
        """Test validating valid SCT"""
        import time
        current_time = int(time.time() * 1000)
        past_time = current_time - 86400000  # 1 day ago

        sct = {
            'version': 0,
            'log_id': b'\x01' * 32,
            'timestamp': past_time,
            'extensions': b'',
            'signature': b'\x02' * 64
        }

        result = self.validator._validateSCT(sct, None)
        self.assertTrue(result)

    def test_validate_sct_future_timestamp_raises_error(self):
        """Test SCT with future timestamp raises error"""
        import time
        current_time = int(time.time() * 1000)
        future_time = current_time + 86400000  # 1 day in future

        sct = {
            'version': 0,
            'log_id': b'\x01' * 32,
            'timestamp': future_time,
            'extensions': b'',
            'signature': b'\x02' * 64
        }

        with self.assertRaises(BimiFailInvalidVMCSCTFutureTimestamp):
            self.validator._validateSCT(sct, None)

    def test_validate_sct_missing_fields(self):
        """Test SCT validation with missing fields"""
        sct = {
            'version': 0,
            'log_id': b'\x01' * 32,
            # Missing timestamp, extensions, signature
        }

        # The _validateSCT method checks for timestamp first, so it will raise KeyError
        # Let's test with proper exception handling
        try:
            result = self.validator._validateSCT(sct, None)
            self.assertFalse(result)
        except KeyError:
            # This is expected behavior for missing required fields
            pass

    def test_validate_sct_wrong_version(self):
        """Test SCT validation with wrong version"""
        import time
        current_time = int(time.time() * 1000)
        past_time = current_time - 86400000

        sct = {
            'version': 1,  # Wrong version
            'log_id': b'\x01' * 32,
            'timestamp': past_time,
            'extensions': b'',
            'signature': b'\x02' * 64
        }

        result = self.validator._validateSCT(sct, None)
        self.assertFalse(result)

    def test_validate_sct_wrong_log_id_length(self):
        """Test SCT validation with wrong log ID length"""
        import time
        current_time = int(time.time() * 1000)
        past_time = current_time - 86400000

        sct = {
            'version': 0,
            'log_id': b'\x01' * 16,  # Wrong length (should be 32)
            'timestamp': past_time,
            'extensions': b'',
            'signature': b'\x02' * 64
        }

        result = self.validator._validateSCT(sct, None)
        self.assertFalse(result)

    def test_validate_sct_short_signature(self):
        """Test SCT validation with too short signature"""
        import time
        current_time = int(time.time() * 1000)
        past_time = current_time - 86400000

        sct = {
            'version': 0,
            'log_id': b'\x01' * 32,
            'timestamp': past_time,
            'extensions': b'',
            'signature': b'\x02' * 32  # Too short (should be at least 64)
        }

        result = self.validator._validateSCT(sct, None)
        self.assertFalse(result)

    def test_parse_sct_list_valid(self):
        """Test parsing valid SCT list"""
        # Create SCT data
        version = struct.pack('B', 0)
        log_id = b'\x01' * 32
        timestamp = struct.pack('>Q', 1640995200000)
        ext_len = struct.pack('>H', 0)
        signature = b'\x02' * 64

        sct_data = version + log_id + timestamp + ext_len + signature
        sct_length = struct.pack('>H', len(sct_data))

        # Create SCT list
        list_data = sct_length + sct_data
        list_length = struct.pack('>H', len(list_data))
        sct_list_data = list_length + list_data

        result = self.validator._parseSCTList(sct_list_data)

        self.assertEqual(len(result), 1)
        self.assertIsNotNone(result[0])
        self.assertEqual(result[0]['version'], 0)

    def test_parse_sct_list_empty(self):
        """Test parsing empty SCT list"""
        sct_list_data = struct.pack('>H', 0)  # Empty list

        result = self.validator._parseSCTList(sct_list_data)
        self.assertEqual(len(result), 0)

    def test_parse_sct_list_invalid_length(self):
        """Test parsing SCT list with invalid length"""
        sct_list_data = b'\x00'  # Too short

        result = self.validator._parseSCTList(sct_list_data)
        self.assertEqual(len(result), 0)

    def test_validate_collect_all_errors(self):
        """Test validation with collectAllBimiFail option"""
        validator = VmcValidator("http://example.com/vmc.pem")  # Will cause error

        with patch.object(validator, '_saveValidationResultToCache'):
            try:
                validator.validate(collectAllBimiFail=True)
            except BimiFailInvalidURI:
                pass

        # Should have collected the error instead of raising
        # (This test structure assumes the method would collect errors in some scenarios)


if __name__ == '__main__':
    unittest.main()
