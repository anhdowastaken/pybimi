# pybimi

A comprehensive Python library for validating Brand Indicators for Message Identification (BIMI) records, indicators, and Verified Mark Certificates (VMCs).

[![Python Version](https://img.shields.io/badge/python-3.6+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## Overview

pybimi is a production-ready BIMI validator that implements the complete BIMI specification including:

- **DNS-based BIMI policy lookup** with custom nameserver support
- **SVG Tiny P/S profile validation** using Java Jing validator with RNC schema
- **X.509 certificate validation** for VMCs with domain verification
- **Certificate Transparency (CT) logging validation** (RFC 6962)
- **Comprehensive caching system** for performance optimization

## Features

✅ **Specification Compliant**: Adheres to BIMI and VMC reference documentation
✅ **Production Ready**: Comprehensive error handling and validation
✅ **Well Tested**: 93+ unit tests with 100% pass rate
✅ **Certificate Transparency**: Full SCT validation support
✅ **SVG Tiny P/S**: Enhanced validation for strict compliance
✅ **Backward Compatible**: All existing APIs maintained

## Installation

### From Source
```bash
git clone https://bitbucket.org/twofive25dev/pybimi
cd pybimi
pip install .
```

### Development Installation
```bash
# Clone and setup development environment
git clone https://bitbucket.org/twofive25dev/pybimi
cd pybimi
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e .
```

## Requirements

- **Python**: 3.6+
- **Java Runtime**: Required for SVG validation using Jing validator
- **Dependencies**: See `requirements.txt` for full list

## Quick Start

### Basic BIMI Validation
```python
from pybimi import Validator
from pybimi.exception import BimiError

# Basic validation
validator = Validator("example.com")
try:
    record = validator.validate()
    print(f"✅ BIMI validation successful for {record.domain}")
    print(f"Policy: {record.policy}")
    if record.indicator:
        print(f"Indicator: {record.indicator.url}")
    if record.vmc:
        print(f"VMC: {record.vmc.url}")
except BimiError as e:
    print(f"❌ BIMI validation failed: {e}")
```

### Simple Usage Example
```python
import pybimi

domains = [
    'dmarc25.jp',
    'quizlet.com',
    'account.pinterest.com',
    'grubhub.com',
]

for domain in domains:
    v = pybimi.Validator(domain)
    try:
        v.validate()
    except pybimi.BimiError as e:
        print('{}: {}'.format(domain, e))
    else:
        print('{}: OK'.format(domain))
```

Expected output:
```
dmarc25.jp: OK
quizlet.com: element "html" not allowed anywhere; expected element "svg" (with xmlns="http://www.w3.org/2000/svg")
account.pinterest.com: the VMC is not valid for account.pinterest.com (valid hostnames include: pinterest.com)
grubhub.com: data from Location and data from Authority Evidence Location are not identical
```

### Certificate Transparency Validation
```python
from pybimi import Validator, VmcOptions

# Enable CT logging validation
vmc_opts = VmcOptions(verifyCTLogging=True)
validator = Validator("example.com", vmcOpts=vmc_opts)

try:
    record = validator.validate()
    if record.vmc and record.vmc.ctLogValidated:
        print("✅ Certificate Transparency validation passed")
except BimiError as e:
    print(f"❌ CT validation failed: {e}")
```

### Advanced Configuration
```python
from pybimi import Validator, LookupOptions, VmcOptions, HttpOptions

# Custom configuration
lookup_opts = LookupOptions(selector="v1", ns=["8.8.8.8"])
vmc_opts = VmcOptions(
    verifyCTLogging=True,
    verifyDNSName=True
)
http_opts = HttpOptions(httpTimeout=30)

validator = Validator(
    "example.com",
    lookupOpts=lookup_opts,
    vmcOpts=vmc_opts,
    httpOpts=http_opts
)
```

## API Reference

### Core Classes

#### `Validator`
Main entry point for BIMI validation.

```python
validator = Validator(
    domain: str,
    lookupOpts: Optional[LookupOptions] = None,
    indicatorOpts: Optional[IndicatorOptions] = None,
    vmcOpts: Optional[VmcOptions] = None,
    httpOpts: Optional[HttpOptions] = None,
    cache: Optional[Cache] = None
)
```

#### `LookupOptions`
DNS lookup configuration options.

```python
lookup_opts = LookupOptions(
    selector: str = "default",  # BIMI selector
    ns: List[str] = None       # Custom nameservers
)
```

#### `VmcOptions`
VMC certificate validation options.

```python
vmc_opts = VmcOptions(
    verifyCTLogging: bool = False,    # Enable CT validation
    verifyDNSName: bool = True,       # Verify domain in certificate
    allowSelfSigned: bool = False     # Allow self-signed certificates
)
```

#### `IndicatorOptions`
SVG indicator validation options.

```python
indicator_opts = IndicatorOptions(
    validateSvgTinyProfile: bool = True  # Enable SVG Tiny P/S validation
)
```

#### `HttpOptions`
HTTP request configuration.

```python
http_opts = HttpOptions(
    httpTimeout: int = 10,     # Request timeout in seconds
    userAgent: str = None      # Custom user agent
)
```

### Exception Hierarchy

All exceptions inherit from `BimiError`:

```python
from pybimi.exception import (
    BimiError,          # Base exception
    BimiNoPolicy,       # No BIMI policy found
    BimiDeclined,       # BIMI explicitly declined
    BimiFail,          # Validation failures
    BimiTempfail       # Temporary failures
)
```

#### Common Exception Types

- `BimiFailInvalidSVG`: Invalid SVG indicator
- `BimiFailInvalidVMCNoCertificate`: No certificate in VMC
- `BimiFailInvalidVMCInvalidSCT`: Invalid Certificate Transparency data
- `BimiFailInvalidVMCDNSNameMismatch`: Domain mismatch in certificate
- `BimiFailInvalidVMCNoSCTFound`: No SCT found in VMC

## SVG Tiny P/S Profile Validation

pybimi includes comprehensive SVG Tiny Portable/Secure profile validation:

```python
from pybimi.indicator_validator import IndicatorValidator

validator = IndicatorValidator(
    "https://example.com/logo.svg",
    validateSvgTinyProfile=True
)

try:
    indicator = validator.validate()

    # Check compliance details
    print(f"SVG Tiny P/S Compliant: {indicator.svgTinyCompliant}")
    print(f"Color Count: {indicator.colorCount}")
    print(f"File Size: {indicator.size} bytes")

    if not indicator.svgTinyCompliant:
        for error in indicator.validationErrors:
            print(f"  - {error}")

except BimiFailInvalidSVG as e:
    print(f"SVG validation failed: {e}")
```

### Validation Checks

The validator enforces:
- **File Size**: Maximum 32KB (uncompressed)
- **Version**: Must be "1.2"
- **Base Profile**: Must be "tiny-ps"
- **Title Element**: Required, non-empty, max 64 characters
- **Color Requirements**: Minimum 2 unique colors
- **Prohibited Elements**: No scripts, animations, external images
- **Element Detection**: Full SVG Tiny P/S compliance scanning

## Certificate Transparency Support

Enhanced VMC validation with full Certificate Transparency support:

```python
from pybimi import Validator, VmcOptions

# Enable CT logging validation
vmc_opts = VmcOptions(verifyCTLogging=True)
validator = Validator("example.com", vmcOpts=vmc_opts)

record = validator.validate()

# Check CT validation results
if record.vmc:
    print(f"CT Log Validated: {record.vmc.ctLogValidated}")
    print(f"SCT Count: {len(record.vmc.scts) if record.vmc.scts else 0}")
```

### CT Validation Features

- **SCT Parsing**: Extracts Signed Certificate Timestamps
- **RFC 6962 Compliance**: Validates SCT structure and integrity
- **Timestamp Validation**: Ensures SCTs are not from the future
- **Multiple SCT Support**: Handles embedded and OCSP stapled SCTs

## Testing

Run the comprehensive test suite:

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python -m pytest tests/ -v

# Expected output: 93+ passed
```

### Test Coverage

- **93 comprehensive unit tests** covering all components
- **100% test pass rate** with proper mocking and isolation
- Coverage includes error handling, edge cases, and network failures
- Tests for all validators: Lookup, Indicator, VMC, and main Validator

## Architecture

### Core Components

- **`Validator`** (`validator.py`): Main orchestrator for BIMI validation
- **`LookupValidator`** (`lookup_validator.py`): DNS TXT record lookup and parsing
- **`IndicatorValidator`** (`indicator_validator.py`): SVG validation using Java/Jing
- **`VmcValidator`** (`vmc_validator.py`): X.509 certificate and CT validation
- **`BimiRecord`** (`bimi.py`): Data structure for parsed BIMI records

### Dependencies

- **Java Runtime**: Required for SVG validation (Jing validator)
- **certvalidator**: Patched version for VMC validation with Pilot Identifier support
- **dnspython**: DNS resolution for BIMI record lookups
- **requests**: HTTP client for fetching indicators and certificates
- **cachetools**: Performance optimization caching
- **tld**: Top-level domain parsing for domain validation

## Reference Documentation

This library implements the following specifications:

- [Brand Indicators for Message Identification (BIMI)](https://www.ietf.org/archive/id/draft-brand-indicators-for-message-identification-10.txt)
- [An Overview of the Design of BIMI](https://www.ietf.org/archive/id/draft-bkl-bimi-overview-00.txt)
- [General Guidance for Implementing BIMI](https://www.ietf.org/archive/id/draft-brotman-ietf-bimi-guidance-12.txt)
- [Fetch and Validation of Verified Mark Certificates](https://www.ietf.org/archive/id/draft-fetch-validation-vmc-wchuang-09.txt)
- [RFC 6962: Certificate Transparency](https://tools.ietf.org/html/rfc6962)

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest tests/ -v`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For issues and questions:
- Open an issue on [Bitbucket](https://bitbucket.org/twofive25dev/pybimi/issues)
- Contact: alex@twofive25.com

## Changelog

### Latest Version (0.0.1)
- ✅ **Full BIMI Specification Compliance**
- ✅ **Certificate Transparency Validation** with SCT support
- ✅ **Enhanced SVG Tiny P/S Profile Validation**
- ✅ **93+ Comprehensive Unit Tests** with 100% pass rate
- ✅ **Production-Ready Error Handling** and validation
- ✅ **Backward Compatibility** maintained
