import unittest
from unittest.mock import Mock, patch

from pybimi.indicator_validator import IndicatorValidator, Indicator
from pybimi.exception import (
    BimiFailInvalidURI, BimiTemfailCannotAccess, BimiTemfailJingError, BimiFailInvalidSVG
)
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
        """Test successful indicator validation with SVG Tiny validation disabled"""
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

        # Disable SVG Tiny validation for this test
        validator = IndicatorValidator(self.uri, validateSvgTinyProfile=False)

        # Mock SVG extraction
        with patch('pybimi.indicator_validator.IndicatorValidator._extractSVG') as mock_extract:
            mock_extract.return_value = Indicator("Test", 100, "1.1", "tiny")

            result = validator.validate()

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

        # Disable SVG Tiny validation for this test
        validator = IndicatorValidator(self.uri, validateSvgTinyProfile=False)

        with patch('pybimi.indicator_validator.IndicatorValidator._extractSVG') as mock_extract:
            mock_extract.return_value = Indicator("Test", 100, "1.1", "tiny")
            result = validator.validate()
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

    # New SVG Tiny P/S Profile Validation Tests
    def test_indicator_with_svg_tiny_attributes(self):
        """Test Indicator class with SVG Tiny P/S attributes"""
        errors = ["Test error"]
        indicator = Indicator("Test", 100, "1.2", "tiny-ps", 3, True, errors)

        self.assertEqual(indicator.colorCount, 3)
        self.assertTrue(indicator.svgTinyCompliant)
        self.assertEqual(indicator.validationErrors, errors)

    def test_svg_tiny_validation_disabled(self):
        """Test validator with SVG Tiny profile validation disabled"""
        validator = IndicatorValidator(self.uri, validateSvgTinyProfile=False)
        self.assertFalse(validator.validateSvgTinyProfile)

    @patch('subprocess.run')
    @patch('pybimi.indicator_validator.getData')
    @patch('tempfile.mkstemp')
    @patch('os.fdopen')
    @patch('os.remove')
    def test_svg_tiny_validation_success(self, mock_remove, mock_fdopen, mock_mkstemp, mock_get_data, mock_subprocess):
        """Test successful SVG Tiny P/S validation"""
        # Create valid SVG Tiny P/S content
        svg_content = b'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" version="1.2" baseProfile="tiny-ps">
    <title>Valid Logo</title>
    <rect fill="#ff0000" width="100" height="100"/>
    <circle fill="#00ff00" cx="50" cy="50" r="20"/>
</svg>'''

        mock_get_data.return_value = svg_content
        mock_mkstemp.return_value = (3, '/tmp/test.svg')
        mock_fdopen.return_value.__enter__.return_value = Mock()

        # Mock subprocess success
        mock_result = Mock()
        mock_result.returncode = 0
        mock_subprocess.return_value = mock_result

        validator = IndicatorValidator(self.uri, validateSvgTinyProfile=True)

        # Mock the file operations for validation
        with patch('pybimi.indicator_validator.IndicatorValidator._extractSVG') as mock_extract, \
             patch('pybimi.indicator_validator.IndicatorValidator._validateSvgTinyProfile') as mock_validate:

            mock_indicator = Indicator("Valid Logo", 1000, "1.2", "tiny-ps", 2, True, [])
            mock_extract.return_value = mock_indicator

            result = validator.validate()

            mock_validate.assert_called_once()
            self.assertIsInstance(result, Indicator)

    def test_count_colors_mock_implementation(self):
        """Test color counting with patched implementation"""
        validator = IndicatorValidator(self.uri)

        # Test the normalize color functionality
        self.assertEqual(validator._normalizeColor('#f0c'), '#ff00cc')
        self.assertEqual(validator._normalizeColor('#ff0000'), '#ff0000')

        # Test extract colors from style
        colors = validator._extractColorsFromStyle('fill: #ff0000; stroke: #00ff00')
        self.assertEqual(len(colors), 2)

    def test_normalize_color_hex(self):
        """Test color normalization for hex colors"""
        validator = IndicatorValidator(self.uri)

        # Test 3-digit hex
        self.assertEqual(validator._normalizeColor('#f0c'), '#ff00cc')

        # Test 6-digit hex
        self.assertEqual(validator._normalizeColor('#FF00CC'), '#ff00cc')

    def test_normalize_color_rgb(self):
        """Test color normalization for RGB colors"""
        validator = IndicatorValidator(self.uri)

        rgb_color = 'rgb(255, 0, 128)'
        self.assertEqual(validator._normalizeColor(rgb_color), 'rgb(255, 0, 128)')

    def test_extract_colors_from_style(self):
        """Test color extraction from CSS style attribute"""
        validator = IndicatorValidator(self.uri)

        style = 'fill: #ff0000; stroke: #00ff00; opacity: 0.5'
        colors = validator._extractColorsFromStyle(style)

        self.assertEqual(len(colors), 2)
        self.assertIn('#ff0000', colors)
        self.assertIn('#00ff00', colors)

    @patch('xml.etree.ElementTree.parse')
    def test_check_prohibited_elements_found(self, mock_parse):
        """Test detection of prohibited elements"""
        mock_root = Mock()
        mock_tree = Mock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree

        # Mock elements including prohibited ones
        elements = [
            Mock(),
            Mock(),
            Mock()
        ]
        elements[0].tag = 'rect'
        elements[1].tag = 'image'  # Prohibited
        elements[2].tag = 'script'  # Prohibited

        mock_root.iter.return_value = elements

        validator = IndicatorValidator(self.uri)
        prohibited = validator._checkProhibitedElements('/tmp/test.svg')

        self.assertEqual(len(prohibited), 2)
        self.assertIn('image', prohibited)
        self.assertIn('script', prohibited)

    @patch('xml.etree.ElementTree.parse')
    def test_check_prohibited_elements_none_found(self, mock_parse):
        """Test when no prohibited elements are found"""
        mock_root = Mock()
        mock_tree = Mock()
        mock_tree.getroot.return_value = mock_root
        mock_parse.return_value = mock_tree

        # Mock elements with only allowed ones
        elements = [Mock(), Mock()]
        elements[0].tag = 'rect'
        elements[1].tag = 'circle'

        mock_root.iter.return_value = elements

        validator = IndicatorValidator(self.uri)
        prohibited = validator._checkProhibitedElements('/tmp/test.svg')

        self.assertEqual(len(prohibited), 0)

    def test_validate_svg_tiny_profile_file_size_error(self):
        """Test SVG Tiny validation fails on oversized file"""
        validator = IndicatorValidator(self.uri)

        # Create indicator with oversized file
        indicator = Indicator("Test", 40000, "1.2", "tiny-ps", 2, False, [])

        with self.assertRaises(BimiFailInvalidSVG) as context:
            validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        self.assertIn("File size", str(context.exception))

    def test_validate_svg_tiny_profile_version_error(self):
        """Test SVG Tiny validation fails on wrong version"""
        validator = IndicatorValidator(self.uri)

        # Create indicator with wrong version
        indicator = Indicator("Test", 1000, "1.1", "tiny-ps", 2, False, [])

        with self.assertRaises(BimiFailInvalidSVG) as context:
            validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        self.assertIn("Version must be '1.2'", str(context.exception))

    def test_validate_svg_tiny_profile_base_profile_error(self):
        """Test SVG Tiny validation fails on wrong baseProfile"""
        validator = IndicatorValidator(self.uri)

        # Create indicator with wrong baseProfile
        indicator = Indicator("Test", 1000, "1.2", "tiny", 2, False, [])

        with self.assertRaises(BimiFailInvalidSVG) as context:
            validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        self.assertIn("baseProfile must be 'tiny-ps'", str(context.exception))

    def test_validate_svg_tiny_profile_empty_title_error(self):
        """Test SVG Tiny validation fails on empty title"""
        validator = IndicatorValidator(self.uri)

        # Create indicator with empty title
        indicator = Indicator("", 1000, "1.2", "tiny-ps", 2, False, [])

        with self.assertRaises(BimiFailInvalidSVG) as context:
            validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        self.assertIn("Title element is required", str(context.exception))

    def test_validate_svg_tiny_profile_long_title_error(self):
        """Test SVG Tiny validation fails on overly long title"""
        validator = IndicatorValidator(self.uri)

        # Create indicator with long title
        long_title = "A" * 100  # Exceeds 64 character limit
        indicator = Indicator(long_title, 1000, "1.2", "tiny-ps", 2, False, [])

        with self.assertRaises(BimiFailInvalidSVG) as context:
            validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        self.assertIn("Title length", str(context.exception))

    def test_validate_svg_tiny_profile_insufficient_colors_error(self):
        """Test SVG Tiny validation fails on insufficient colors"""
        validator = IndicatorValidator(self.uri)

        # Create indicator with insufficient colors
        indicator = Indicator("Test", 1000, "1.2", "tiny-ps", 1, False, [])

        with self.assertRaises(BimiFailInvalidSVG) as context:
            validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        self.assertIn("must include at least 2 colors", str(context.exception))

    @patch('pybimi.indicator_validator.IndicatorValidator._checkProhibitedElements')
    def test_validate_svg_tiny_profile_prohibited_elements_error(self, mock_check):
        """Test SVG Tiny validation fails on prohibited elements"""
        validator = IndicatorValidator(self.uri)
        mock_check.return_value = ['image', 'script']

        # Create otherwise valid indicator
        indicator = Indicator("Test", 1000, "1.2", "tiny-ps", 2, False, [])

        with self.assertRaises(BimiFailInvalidSVG) as context:
            validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        self.assertIn("Prohibited elements found", str(context.exception))

    @patch('pybimi.indicator_validator.IndicatorValidator._checkProhibitedElements')
    def test_validate_svg_tiny_profile_success(self, mock_check):
        """Test successful SVG Tiny P/S validation"""
        validator = IndicatorValidator(self.uri)
        mock_check.return_value = []  # No prohibited elements

        # Create valid indicator
        indicator = Indicator("Valid Test Logo", 1000, "1.2", "tiny-ps", 3, False, [])

        # Should not raise an exception
        validator._validateSvgTinyProfile('/tmp/test.svg', indicator)

        # Check that indicator was updated
        self.assertTrue(indicator.svgTinyCompliant)
        self.assertEqual(len(indicator.validationErrors), 0)


if __name__ == '__main__':
    unittest.main()
