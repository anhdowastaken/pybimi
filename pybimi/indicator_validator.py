import os
import tempfile
from urllib.parse import urlparse
import subprocess
import re
from xml.dom import minidom
import xml.etree.ElementTree as ET

from .bimi import *
from .exception import *
from .utils import *
from .options import *
from .cache import *

class Indicator:
    """
    A class used to represent a SVG

    Attributes
    ----------
    title: str
    size: int
        Size in bytes
    version: str
    baseProfile: str
    colorCount: int
        Number of unique colors detected
    svgTinyCompliant: bool
        Whether SVG meets Tiny P/S profile requirements
    validationErrors: list
        List of validation issues found
    """

    def __init__(self, title: str,
                       size: int,
                       version: str,
                       baseProfile: str,
                       colorCount: int = 0,
                       svgTinyCompliant: bool = False,
                       validationErrors: list = None) -> None:
        self.title = title
        self.size = size
        self.version = version
        self.baseProfile = baseProfile
        self.colorCount = colorCount
        self.svgTinyCompliant = svgTinyCompliant
        self.validationErrors = validationErrors or []

    def __repr__(self) -> str:
        return str(self.__dict__)

class IndicatorValidator:
    """
    A class used to validate a BIMI indicator

    Attributes
    ----------
    uri: str
        URI of the BIMI indicator
    localFile: bool
        If set, it means the uri is a local file path
    opts: IndicatorOptions
        Indicator validation options
    httpOpts: HttpOptions
        HTTP options
    cache: Cache
        Cache
    bimiFailErrors: list
        List of BIMI fail errors collected when validating with Jing
    validateSvgTinyProfile: bool
        Whether to perform additional SVG Tiny P/S profile validation

    Methods
    -------
    validate()
        Validate the BIMI indicator
    _validateSvgTinyProfile()
        Perform SVG Tiny P/S profile validation
    """

    # SVG Tiny P/S profile constants
    SVG_TINY_PS_MAX_SIZE = 32 * 1024  # 32KB
    SVG_TINY_PS_TITLE_MAX_LENGTH = 64
    SVG_TINY_PS_MIN_COLORS = 2

    # Prohibited elements in SVG Tiny P/S
    PROHIBITED_ELEMENTS = {
        'image', 'switch', 'foreignObject', 'script', 'animation', 'animateColor',
        'animateMotion', 'animateTransform', 'set', 'cursor', 'view', 'marker',
        'mask', 'clipPath', 'pattern', 'filter', 'feBlend', 'feColorMatrix',
        'feComponentTransfer', 'feComposite', 'feConvolveMatrix', 'feDiffuseLighting',
        'feDisplacementMap', 'feFlood', 'feGaussianBlur', 'feImage', 'feMerge',
        'feMorphology', 'feOffset', 'feSpecularLighting', 'feTile', 'feTurbulence',
        'feDistantLight', 'fePointLight', 'feSpotLight', 'feFuncA', 'feFuncB',
        'feFuncG', 'feFuncR', 'feMergeNode'
    }

    def __init__(self, uri: str,
                       localFile: bool=False,
                       opts: IndicatorOptions=IndicatorOptions(),
                       httpOpts: HttpOptions=HttpOptions(),
                       cache: Cache=None,
                       validateSvgTinyProfile: bool=True) -> None:
        self.uri = uri
        self.localFile = localFile
        self.opts = opts
        self.httpOpts = httpOpts
        self.cache = cache
        self.bimiFailErrors = [] # Only errors when validating with Jing
        self.validateSvgTinyProfile = validateSvgTinyProfile

    def _saveValidationResultToCache(self, key: str, value: Exception):
        """
        Save validation result to cache

        Parameters
        ----------
        key: str
            A key
        value: Exception
            An exception
        """

        if self.cache is not None:
            self.cache.set(key, value)

    def validate(self, collectAllBimiFail=False) -> Indicator:
        """
        Validate the BIMI indicator. The indicator is downloaded from the URI
        with some HTTP options. If the indicator is downloaded successfully, it
        will be validated by some validation options.

        Parameters
        ----------
        collectAllBimiFail: bool
            If set, instead of raising a BimiFail exception, save it to the attribute bimiFailErrors

        Returns
        -------
        Indicator

        Raises
        ------
        BimiFail

        BimiFailInvalidURI

        BimiFailInvalidSVG

        BimiTempfail

        BimiTemfailCannotAccess

        BimiTemfailJingError
        """

        # SVG information holder
        i = None

        if not (self.uri and self.uri.strip()):
            return i

        h = hashlib.new('md5')
        h.update(self.uri.encode())
        key = 'bimi_indicator_validation_result_{}'.format(h.hexdigest())
        # Find validation result in cache
        if self.cache is not None:
            found, e = self.cache.get(key)
            if found:
                # print('Found {} in cache'.format(key))
                if e is None:
                    return i
                else:
                    raise e

        url = urlparse(self.uri)
        if url is None:
            e = BimiFailInvalidURI('invalid SVG URI')
            self._saveValidationResultToCache(key, e)
            raise e

        if not self.localFile and url.scheme != 'https':
            e = BimiFailInvalidURI('the SVG URI is not served by HTTPS')
            self._saveValidationResultToCache(key, e)
            raise e

        fd, path = tempfile.mkstemp(prefix='pybimi', suffix='.svg')
        try:
            with os.fdopen(fd, 'wb') as f:
                indicatorData = getData(uri=self.uri,
                                        localFile=self.localFile,
                                        timeout=self.httpOpts.httpTimeout,
                                        userAgent=self.httpOpts.httpUserAgent,
                                        maxSizeInBytes=self.opts.maxSizeInBytes,
                                        cache=self.cache)
                f.write(indicatorData)

        except BimiTempfail as e:
            os.remove(path)
            raise e

        except BimiFail as e:
            os.remove(path)
            self._saveValidationResultToCache(key, e)
            raise e

        except Exception as e:
            os.remove(path)
            raise BimiTempfail(str(e))

        i = self._extractSVG(path)

        try:
            cmd = [self.opts.javaPath, '-jar', self.opts.jingJarPath, '-c', self.opts.rncSchemaPath, path]
            proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        except Exception as e:
            os.remove(path)
            raise BimiTemfailJingError(str(e))

        if proc.returncode != 0:
            out = proc.stdout.decode() + proc.stderr.decode()
            lines = out.split('\n')
            if len(lines) > 0:
                line = lines[0]
                pattern = r'.+:\d+:\d+:\s+(error|fatal):\s+(.+)'
                matches = re.findall(pattern, line)
                if len(matches) > 0:
                    e = BimiFailInvalidSVG(matches[0][1])
                    if collectAllBimiFail:
                        self.bimiFailErrors.append(e)
                    else:
                        os.remove(path)
                        self._saveValidationResultToCache(key, e)
                        raise e

                else:
                    e = BimiFailInvalidSVG(line)
                    if collectAllBimiFail:
                        self.bimiFailErrors.append(e)
                    else:
                        os.remove(path)
                        self._saveValidationResultToCache(key, e)
                        raise e

            else:
                e = BimiFailInvalidSVG(out)
                if collectAllBimiFail:
                    self.bimiFailErrors.append(e)
                else:
                    os.remove(path)
                    self._saveValidationResultToCache(key, e)
                    raise e

        # Perform additional SVG Tiny P/S profile validation if enabled
        if self.validateSvgTinyProfile and i is not None:
            try:
                self._validateSvgTinyProfile(path, i)
            except BimiFail as e:
                os.remove(path)
                self._saveValidationResultToCache(key, e)
                raise e

        os.remove(path)

        self._saveValidationResultToCache(key, None)
        return i

    def _extractSVG(self, path: str) -> Indicator:
        """
        Extract SVG information from the indicator downloaded from internet

        Parameters
        ----------
        path: str
            Local path of the downloaded indicator

        Returns
        -------
        Indicator
        """

        try:
            doc = minidom.parse(path)
            svg_elements = doc.getElementsByTagName('svg')
            if not svg_elements:
                return None

            svg = svg_elements[0].attributes.items()

            # Extract title - handle cases where title might be missing
            title_elements = doc.getElementsByTagName('title')
            title = ''
            if title_elements and title_elements[0].firstChild:
                title = title_elements[0].firstChild.nodeValue or ''

            file_size = os.path.getsize(path)

            i = Indicator(title=title,
                          size=file_size,
                          version='',
                          baseProfile='')
            for item in svg:
                if item[0] == 'version':
                    i.version = item[1]
                elif item[0] == 'baseProfile':
                    i.baseProfile = item[1]

            # Extract additional SVG Tiny P/S validation info if enabled
            if self.validateSvgTinyProfile:
                color_count = self._countColors(path)
                i.colorCount = color_count

            return i

        except:
            return None

    def _validateSvgTinyProfile(self, path: str, indicator: Indicator) -> None:
        """
        Perform SVG Tiny P/S profile validation beyond basic Jing validation

        Parameters
        ----------
        path: str
            Local path to SVG file
        indicator: Indicator
            The indicator object to update with validation results

        Raises
        ------
        BimiFailInvalidSVG
            If SVG does not meet Tiny P/S profile requirements
        """
        errors = []

        # Check file size
        if indicator.size > self.SVG_TINY_PS_MAX_SIZE:
            errors.append(f"File size ({indicator.size} bytes) exceeds SVG Tiny P/S maximum of {self.SVG_TINY_PS_MAX_SIZE} bytes")

        # Check version
        if indicator.version != "1.2":
            errors.append(f"Version must be '1.2' for SVG Tiny P/S, found: '{indicator.version}'")

        # Check base profile
        if indicator.baseProfile != "tiny-ps":
            errors.append(f"baseProfile must be 'tiny-ps' for SVG Tiny P/S, found: '{indicator.baseProfile}'")

        # Check title requirements
        if not indicator.title or indicator.title.strip() == '':
            errors.append("Title element is required and must not be empty")
        elif len(indicator.title) > self.SVG_TINY_PS_TITLE_MAX_LENGTH:
            errors.append(f"Title length ({len(indicator.title)}) exceeds maximum of {self.SVG_TINY_PS_TITLE_MAX_LENGTH} characters")

        # Check color requirements
        if indicator.colorCount < self.SVG_TINY_PS_MIN_COLORS:
            errors.append(f"SVG must include at least {self.SVG_TINY_PS_MIN_COLORS} colors, found: {indicator.colorCount}")

        # Check for prohibited elements
        prohibited_found = self._checkProhibitedElements(path)
        if prohibited_found:
            errors.append(f"Prohibited elements found: {', '.join(prohibited_found)}")

        # Update indicator with validation results
        indicator.validationErrors = errors
        indicator.svgTinyCompliant = len(errors) == 0

        # Raise error if validation failed
        if errors:
            raise BimiFailInvalidSVG(f"SVG Tiny P/S validation failed: {'; '.join(errors[:3])}")

    def _countColors(self, path: str) -> int:
        """
        Count unique colors used in the SVG

        Parameters
        ----------
        path: str
            Local path to SVG file

        Returns
        -------
        int
            Number of unique colors found
        """
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            colors = set()

            # Look for color attributes throughout the SVG
            for elem in root.iter():
                # Check common color attributes
                for attr in ['fill', 'stroke', 'stop-color']:
                    color_value = elem.get(attr)
                    if color_value and color_value.lower() not in ['none', 'transparent']:
                        colors.add(self._normalizeColor(color_value))

                # Check style attribute for colors
                style = elem.get('style', '')
                if style:
                    colors.update(self._extractColorsFromStyle(style))

            return len(colors)

        except Exception:
            return 0

    def _normalizeColor(self, color: str) -> str:
        """
        Normalize color representation for counting

        Parameters
        ----------
        color: str
            Color value from SVG

        Returns
        -------
        str
            Normalized color representation
        """
        color = color.strip().lower()

        # Handle hex colors
        if color.startswith('#'):
            # Convert 3-digit hex to 6-digit
            if len(color) == 4:
                color = '#' + ''.join([c*2 for c in color[1:]])
            return color

        # Handle rgb() colors
        if color.startswith('rgb(') and color.endswith(')'):
            return color

        # Handle named colors (return as-is)
        return color

    def _extractColorsFromStyle(self, style: str) -> set:
        """
        Extract colors from CSS style attribute

        Parameters
        ----------
        style: str
            CSS style string

        Returns
        -------
        set
            Set of colors found in style
        """
        colors = set()

        # Split style into individual properties
        properties = [prop.strip() for prop in style.split(';') if ':' in prop]

        for prop in properties:
            key, value = prop.split(':', 1)
            key = key.strip()
            value = value.strip()

            if key in ['fill', 'stroke', 'stop-color'] and value.lower() not in ['none', 'transparent']:
                colors.add(self._normalizeColor(value))

        return colors

    def _checkProhibitedElements(self, path: str) -> list:
        """
        Check for prohibited elements in SVG Tiny P/S

        Parameters
        ----------
        path: str
            Local path to SVG file

        Returns
        -------
        list
            List of prohibited elements found
        """
        try:
            tree = ET.parse(path)
            root = tree.getroot()

            prohibited_found = []

            for elem in root.iter():
                # Remove namespace prefix for comparison
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag_name in self.PROHIBITED_ELEMENTS:
                    prohibited_found.append(tag_name)

            return list(set(prohibited_found))  # Remove duplicates

        except Exception:
            return []
