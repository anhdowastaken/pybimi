import unittest

from pybimi.exception import *


class TestExceptions(unittest.TestCase):

    def test_base_exception(self):
        """Test BimiError base exception"""
        with self.assertRaises(BimiError):
            raise BimiError("Test error")

    def test_no_policy_exception(self):
        """Test BimiNoPolicy exception"""
        with self.assertRaises(BimiNoPolicy):
            raise BimiNoPolicy("No BIMI policy found")

        with self.assertRaises(BimiError):
            raise BimiNoPolicy("Should inherit from BimiError")

    def test_declined_exception(self):
        """Test BimiDeclined exception"""
        with self.assertRaises(BimiDeclined):
            raise BimiDeclined("BIMI declined")

        with self.assertRaises(BimiError):
            raise BimiDeclined("Should inherit from BimiError")

    def test_tempfail_exception(self):
        """Test BimiTempfail exception"""
        with self.assertRaises(BimiTempfail):
            raise BimiTempfail("Temporary failure")

        with self.assertRaises(BimiError):
            raise BimiTempfail("Should inherit from BimiError")

    def test_tempfail_cannot_access_exception(self):
        """Test BimiTemfailCannotAccess exception"""
        with self.assertRaises(BimiTemfailCannotAccess):
            raise BimiTemfailCannotAccess("Cannot access resource")

        with self.assertRaises(BimiTempfail):
            raise BimiTemfailCannotAccess("Should inherit from BimiTempfail")

    def test_tempfail_jing_error_exception(self):
        """Test BimiTemfailJingError exception"""
        with self.assertRaises(BimiTemfailJingError):
            raise BimiTemfailJingError("Jing validation error")

        with self.assertRaises(BimiTempfail):
            raise BimiTemfailJingError("Should inherit from BimiTempfail")

    def test_fail_exception(self):
        """Test BimiFail exception"""
        with self.assertRaises(BimiFail):
            raise BimiFail("Validation failed")

        with self.assertRaises(BimiError):
            raise BimiFail("Should inherit from BimiError")

    def test_fail_size_limit_exceeded_exception(self):
        """Test BimiFailSizeLimitExceeded exception"""
        with self.assertRaises(BimiFailSizeLimitExceeded):
            raise BimiFailSizeLimitExceeded("Size limit exceeded")

        with self.assertRaises(BimiFail):
            raise BimiFailSizeLimitExceeded("Should inherit from BimiFail")

    def test_fail_invalid_uri_exception(self):
        """Test BimiFailInvalidURI exception"""
        with self.assertRaises(BimiFailInvalidURI):
            raise BimiFailInvalidURI("Invalid URI")

        with self.assertRaises(BimiFail):
            raise BimiFailInvalidURI("Should inherit from BimiFail")

    def test_fail_invalid_format_exception(self):
        """Test BimiFailInvalidFormat exception"""
        with self.assertRaises(BimiFailInvalidFormat):
            raise BimiFailInvalidFormat("Invalid format")

        with self.assertRaises(BimiFail):
            raise BimiFailInvalidFormat("Should inherit from BimiFail")

    def test_fail_invalid_svg_exception(self):
        """Test BimiFailInvalidSVG exception"""
        with self.assertRaises(BimiFailInvalidSVG):
            raise BimiFailInvalidSVG("Invalid SVG")

        with self.assertRaises(BimiFail):
            raise BimiFailInvalidSVG("Should inherit from BimiFail")

    def test_fail_invalid_vmc_exception(self):
        """Test BimiFailInvalidVMC exception"""
        with self.assertRaises(BimiFailInvalidVMC):
            raise BimiFailInvalidVMC("Invalid VMC")

        with self.assertRaises(BimiFail):
            raise BimiFailInvalidVMC("Should inherit from BimiFail")

    def test_vmc_specific_exceptions(self):
        """Test VMC-specific exception inheritance"""
        vmc_exceptions = [
            BimiFailInvalidVMCNotPEM,
            BimiFailInvalidVMCNoLeafFound,
            BimiFailInvalidVMCMultiLeafs,
            BimiFailInvalidVMCUnmatchedDomain,
            BimiFailInvalidVMCUnmatchedSAN,
            BimiFailInvalidVMCCriticalLogotype,
            BimiFailInvalidVMCNoHashFound,
            BimiFailInvalidVMCUnmatchedSVG,
            BimiFailInvalidVMCUnsupportedAlgorithm,
            BimiFailInvalidVMCCannotVerify,
            BimiFailInvalidVMCNotValidBefore,
            BimiFailInvalidVMCExpiredAfter,
            BimiFailInvalidVMCNoRevocationFound,
            BimiFailInvalidVMCCheckRevocationFailed,
            BimiFailInvalidVMCIssuerNotMatch,
            BimiFailInvalidVMCAnyPolicyFound,
            BimiFailInvalidVMCNotCA,
            BimiFailInvalidVMCExceedMaximumPathLength,
            BimiFailInvalidVMCNotAllowToSign,
            BimiFailInvalidVMCUnsupportedCriticalExtensionFound,
            BimiFailInvalidVMCNoValidPolicySetFound,
            BimiFailInvalidVMCNoMatchingIssuerFound,
            BimiFailInvalidVMCNoSCTFound,
            BimiFailInvalidVMCInvalidSCT,
            BimiFailInvalidVMCSCTFutureTimestamp,
        ]

        for exception_class in vmc_exceptions:
            with self.subTest(exception=exception_class.__name__):
                with self.assertRaises(BimiFailInvalidVMC):
                    raise exception_class("Test error")

                with self.assertRaises(BimiFail):
                    raise exception_class("Should inherit from BimiFail")

                with self.assertRaises(BimiError):
                    raise exception_class("Should inherit from BimiError")

    def test_exception_messages(self):
        """Test that exceptions preserve error messages"""
        message = "Custom error message"

        try:
            raise BimiFailInvalidVMC(message)
        except BimiFailInvalidVMC as e:
            self.assertEqual(str(e), message)

    def test_exception_inheritance_chain(self):
        """Test complete inheritance chain"""
        # Test that VMC-specific exceptions inherit properly
        exception = BimiFailInvalidVMCNotPEM("test")

        self.assertIsInstance(exception, BimiFailInvalidVMCNotPEM)
        self.assertIsInstance(exception, BimiFailInvalidVMC)
        self.assertIsInstance(exception, BimiFail)
        self.assertIsInstance(exception, BimiError)
        self.assertIsInstance(exception, Exception)


if __name__ == '__main__':
    unittest.main()
