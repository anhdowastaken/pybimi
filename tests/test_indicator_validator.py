import unittest
from unittest.mock import Mock, patch, mock_open
import tempfile
import os

from pybimi.indicator_validator import IndicatorValidator, Indicator
from pybimi.exception import *
from pybimi.options import IndicatorOptions, HttpOptions


class TestIndicatorValidator(unittest.TestCase):

    def setUp(self):
        self.uri = "https://example.com/logo.svg"
        self.validator = IndicatorValidator(self.uri)

    def test_init_with_defaults(self):
        """Test initialization with default options"""
        validator = IndicatorValidator("https://example.com/logo.svg")
        self.assertEqual(validator.uri, "https://example.com/logo.svg")
        self.assertFalse(validator.localFile)
        self.assertIsInstance(validator.opts, IndicatorOptions)
        self.assertIsInstance(validator.httpOpts, HttpOptions)

    def test_init_with_local_file(self):
        """Test initialization with local file"""
        validator = IndicatorValidator("/path/to/logo.svg", localFile=True)
        self.assertTrue(validator.localFile)

    @patch('subprocess.run')
    @patch('pybimi.indicator_validator.getData')
    @patch('tempfile.mkstemp')
    @patch('os.fdopen')
    @patch('os.remove')
    def test_validate_success(self, mock_remove, mock_fdopen, mock_mkstemp, mock_get_data, mock_subprocess):
        """Test successful indicator validation"""
        mock_svg_data = b'<svg version="1.1" baseProfile="tiny"><title>Test</title></svg>'
        mock_get_data.return_value = mock_svg_data

        # Mock temp file creation
        mock_fd = 3
        mock_path = '/tmp/test.svg'
        mock_mkstemp.return_value = (mock_fd, mock_path)

        # Mock file operations
        mock_file = Mock()
        mock_fdopen.return_value.__enter__.return_value = mock_file

        # Mock subprocess success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        # Mock SVG extraction
        with patch('pybimi.indicator_validator.IndicatorValidator._extractSVG') as mock_extract:
            mock_extract.return_value = Indicator("Test", 100, "1.1", "tiny")

            result = self.validator.validate()

            self.assertIsInstance(result, Indicator)
            mock_get_data.assert_called_once()
            mock_subprocess.assert_called_once()
            mock_extract.assert_called_once()

    def test_validate_empty_uri_returns_none(self):
        """Test that empty URI returns None"""
        validator = IndicatorValidator("")
        result = validator.validate()
        self.assertIsNone(result)

    def test_validate_none_uri_returns_none(self):
        """Test that None URI returns None"""
        validator = IndicatorValidator(None)
        result = validator.validate()
        self.assertIsNone(result)

    @patch('pybimi.indicator_validator.getData')
    def test_validate_http_uri_raises_error(self, mock_get_data):
        """Test that HTTP URI raises error"""
        validator = IndicatorValidator("http://example.com/logo.svg")
        mock_get_data.side_effect = BimiFailInvalidURI("HTTP not allowed")

        with self.assertRaises(BimiFailInvalidURI):
            validator.validate()

    @patch('pybimi.indicator_validator.getData')
    def test_validate_network_error_raises_tempfail(self, mock_get_data):
        """Test that network errors raise BimiTempfail"""
        mock_get_data.side_effect = BimiTemfailCannotAccess("Network error")

        with self.assertRaises(BimiTemfailCannotAccess):
            self.validator.validate()

    @patch('subprocess.run')
    @patch('pybimi.indicator_validator.getData')
    @patch('tempfile.mkstemp')
    @patch('os.fdopen')
    @patch('os.remove')
    def test_validate_jing_error_raises_tempfail(self, mock_remove, mock_fdopen, mock_mkstemp, mock_get_data, mock_subprocess):
        """Test that Jing validation errors raise BimiTempfail"""
        mock_get_data.return_value = b'<svg>test</svg>'
        mock_mkstemp.return_value = (3, '/tmp/test.svg')
        mock_fdopen.return_value.__enter__.return_value = Mock()
        mock_subprocess.side_effect = Exception("Java error")

        with self.assertRaises(BimiTemfailJingError):
            self.validator.validate()

    @patch('subprocess.run')
    @patch('pybimi.indicator_validator.getData')
    @patch('tempfile.mkstemp')
    @patch('os.fdopen')
    @patch('os.remove')
    def test_validate_subprocess_success(self, mock_remove, mock_fdopen, mock_mkstemp, mock_get_data, mock_subprocess):
        """Test successful subprocess validation"""
        mock_get_data.return_value = b'<svg>test</svg>'
        mock_mkstemp.return_value = (3, '/tmp/test.svg')
        mock_fdopen.return_value.__enter__.return_value = Mock()

        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        with patch('pybimi.indicator_validator.IndicatorValidator._extractSVG') as mock_extract:
            mock_extract.return_value = Indicator("Test", 100, "1.1", "tiny")
            result = self.validator.validate()
            self.assertIsInstance(result, Indicator)

    @patch('subprocess.run')
    @patch('pybimi.indicator_validator.getData')
    @patch('tempfile.mkstemp')
    @patch('os.fdopen')
    @patch('os.remove')
    def test_validate_subprocess_validation_error(self, mock_remove, mock_fdopen, mock_mkstemp, mock_get_data, mock_subprocess):
        """Test subprocess validation error"""
        mock_get_data.return_value = b'<svg>invalid</svg>'
        mock_mkstemp.return_value = (3, '/tmp/test.svg')
        mock_fdopen.return_value.__enter__.return_value = Mock()

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = b''
        mock_result.stderr = b'/tmp/test.svg:1:1: error: validation failed'
        mock_subprocess.return_value = mock_result

        with self.assertRaises(BimiFailInvalidSVG):
            self.validator.validate()

    @patch('subprocess.run')
    @patch('pybimi.indicator_validator.getData')
    @patch('tempfile.mkstemp')
    @patch('os.fdopen')
    @patch('os.remove')
    def test_validate_subprocess_process_error(self, mock_remove, mock_fdopen, mock_mkstemp, mock_get_data, mock_subprocess):
        """Test process error in subprocess validation"""
        mock_get_data.return_value = b'<svg>test</svg>'
        mock_mkstemp.return_value = (3, '/tmp/test.svg')
        mock_fdopen.return_value.__enter__.return_value = Mock()
        mock_subprocess.side_effect = Exception("Process failed")

        with self.assertRaises(BimiTemfailJingError):
            self.validator.validate()

    @patch('xml.dom.minidom.parse')
    @patch('os.path.getsize')
    def test_extract_svg_success(self, mock_getsize, mock_parse):
        """Test successful SVG info extraction"""
        mock_doc = Mock()
        mock_svg_element = Mock()
        mock_svg_element.attributes.items.return_value = [('version', '1.1'), ('baseProfile', 'tiny')]
        mock_title_element = Mock()
        mock_title_element.firstChild.nodeValue = "Test Logo"
        mock_doc.getElementsByTagName.side_effect = lambda tag: {
            'svg': [mock_svg_element],
            'title': [mock_title_element]
        }.get(tag, [])
        mock_parse.return_value = mock_doc
        mock_getsize.return_value = 100

        result = self.validator._extractSVG('/tmp/test.svg')

        self.assertIsInstance(result, Indicator)
        self.assertEqual(result.title, "Test Logo")
        self.assertEqual(result.version, "1.1")
        self.assertEqual(result.baseProfile, "tiny")
        self.assertEqual(result.size, 100)

    @patch('xml.dom.minidom.parse')
    def test_extract_svg_parse_error(self, mock_parse):
        """Test SVG parsing error"""
        mock_parse.side_effect = Exception("Parse error")

        result = self.validator._extractSVG('/tmp/invalid.svg')
        self.assertIsNone(result)

    @patch('xml.dom.minidom.parse')
    def test_extract_svg_no_svg_element(self, mock_parse):
        """Test SVG with no svg element"""
        mock_doc = Mock()
        mock_doc.getElementsByTagName.side_effect = lambda tag: {
            'svg': [],  # No SVG elements
            'title': []
        }.get(tag, [])
        mock_parse.return_value = mock_doc

        result = self.validator._extractSVG('/tmp/invalid.svg')
        self.assertIsNone(result)

    def test_validate_with_cache_hit(self):
        """Test validation with cache hit"""
        from pybimi.cache import Cache
        cache = Cache()

        # Mock cache to return a cached result
        with patch.object(cache, 'get') as mock_get:
            mock_get.return_value = (True, None)  # Cache hit, no error

            validator = IndicatorValidator(self.uri, cache=cache)
            result = validator.validate()

            self.assertIsNone(result)  # Cached result

    def test_validate_with_cache_error(self):
        """Test validation with cached error"""
        from pybimi.cache import Cache
        cache = Cache()

        # Mock cache to return a cached error
        cached_error = BimiFailInvalidSVG("Cached error")
        with patch.object(cache, 'get') as mock_get:
            mock_get.return_value = (True, cached_error)

            validator = IndicatorValidator(self.uri, cache=cache)

            with self.assertRaises(BimiFailInvalidSVG):
                validator.validate()


if __name__ == '__main__':
    unittest.main()
