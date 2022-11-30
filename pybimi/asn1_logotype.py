from asn1crypto import core
from .exception import BimiFail

oidLogotype              = '1.3.6.1.5.5.7.1.12'
oidDigestAlgorithmMD5    = '1.2.840.113549.2.5'
oidDigestAlgorithmSHA1   = '1.3.14.3.2.26'
oidDigestAlgorithmSHA256 = '2.16.840.1.101.3.4.2.1'
oidDigestAlgorithmSHA384 = '2.16.840.1.101.3.4.2.2'
oidDigestAlgorithmSHA512 = '2.16.840.1.101.3.4.2.3'

# AlgorithmIdentifier  ::=  SEQUENCE  {
#   algorithm   OBJECT IDENTIFIER,
#   parameters  ANY DEFINED BY algorithm OPTIONAL  }
class ASN1AlgorithmIdentifier(core.Sequence):
    _fields = [
        ('algorithm', core.ObjectIdentifier),
        ('parameters', core.Any, {'optional': True}),
    ]

# HashAlgAndValue ::= SEQUENCE {
#   hashAlg     AlgorithmIdentifier,
#   hashValue   OCTET STRING }
class ASN1HashAlgAndValue(core.Sequence):
    _fields = [
        ('hashAlg', ASN1AlgorithmIdentifier),
        ('hashValue', core.OctetString),
    ]

class SequenceOfASN1HashAlgAndValue(core.SequenceOf):
    _child_spec = ASN1HashAlgAndValue

class SequenceOfIA5String(core.SequenceOf):
    _child_spec = core.IA5String

# LogotypeDetails ::= SEQUENCE {
#   mediaType       IA5String, -- MIME media type name and optional
#                              -- parameters
#   logotypeHash    SEQUENCE SIZE (1..MAX) OF HashAlgAndValue,
#   logotypeURI     SEQUENCE SIZE (1..MAX) OF IA5String }
class ASN1LogotypeDetails(core.Sequence):
    _fields = [
        ('mediaType', core.IA5String),
        ('logotypeHash', SequenceOfASN1HashAlgAndValue),
        ('logotypeURI', SequenceOfIA5String),
    ]

# LogotypeImageType ::= INTEGER { grayScale(0), color(1) }

# LogotypeImageResolution ::= CHOICE {
#   numBits     [1] INTEGER,   -- Resolution in bits
#   tableSize   [2] INTEGER }  -- Number of colors or grey tones
class ASN1LogotypeImageResolution(core.Choice):
    _alternatives = [
        ('numBits', core.Integer, {'implicit': 1}),
        ('tableSize', core.Integer, {'implicit': 2}),
    ]

# LogotypeImageInfo ::= SEQUENCE {
#   type        [0] LogotypeImageType DEFAULT color,
#   fileSize    INTEGER,  -- In octets
#   xSize       INTEGER,  -- Horizontal size in pixels
#   ySize       INTEGER,  -- Vertical size in pixels
#   resolution  LogotypeImageResolution OPTIONAL,
#   language    [4] IA5String OPTIONAL }  -- RFC 3066 Language Tag
class ASN1LogotypeImageInfo(core.Sequence):
    _fields = [
        ('type', core.Integer, {'implicit': 0, 'default': 1}),
        ('fileSize', core.Integer),
        ('xSize', core.Integer),
        ('ySize', core.Integer),
        ('resolution', ASN1LogotypeImageResolution, {'optional': True}),
        ('language', core.IA5String, {'implicit': 4, 'optional': True}),
    ]

# LogotypeAudioInfo ::= SEQUENCE {
#   fileSize    INTEGER,  -- In octets
#   playTime    INTEGER,  -- In milliseconds
#   channels    INTEGER,  -- 1=mono, 2=stereo, 4=quad
#   sampleRate  [3] INTEGER OPTIONAL,  -- Samples per second
#   language    [4] IA5String OPTIONAL }  -- RFC 3066 Language Tag
class ASN1LogotypeAudioInfo(core.Sequence):
    _fields = [
        ('fileSize', core.Integer),
        ('playTime', core.Integer),
        ('channels', core.Integer),
        ('sampleRate', core.Integer, {'implicit': 3, 'optional': True}),
        ('language', core.IA5String, {'implicit': 4, 'optional': True}),
    ]

#  LogotypeImage ::= SEQUENCE {
#   imageDetails    LogotypeDetails,
#   imageInfo       LogotypeImageInfo OPTIONAL }
class ASN1LogotypeImage(core.Sequence):
    _fields = [
        ('imageDetails', ASN1LogotypeDetails),
        ('imageInfo', ASN1LogotypeImageInfo, {'optional': True}),
    ]

# LogotypeAudio ::= SEQUENCE {
#   audioDetails    LogotypeDetails,
#   audioInfo       LogotypeAudioInfo OPTIONAL }
class ASN1LogotypeAudio(core.Sequence):
    _fields = [
        ('audioDetails', ASN1LogotypeDetails),
        ('audioInfo', ASN1LogotypeAudioInfo, {'optional': True}),
    ]

class SequenceOfASN1LogotypeImage(core.SequenceOf):
    _child_spec = ASN1LogotypeImage

class SequenceOfASN1LogotypeAudio(core.SequenceOf):
    _child_spec = ASN1LogotypeAudio

# LogotypeData ::= SEQUENCE {
#   image   SEQUENCE OF LogotypeImage OPTIONAL,
#   audio   [1] SEQUENCE OF LogotypeAudio OPTIONAL }
class ASN1LogotypeData(core.Sequence):
    _fields = [
        ('image', SequenceOfASN1LogotypeImage, {'optional': True}),
        ('audio', SequenceOfASN1LogotypeAudio, {'implicit': 1, 'optional': True}),
    ]

#  LogotypeReference ::= SEQUENCE {
#   refStructHash   SEQUENCE SIZE (1..MAX) OF HashAlgAndValue,
#   refStructURI    SEQUENCE SIZE (1..MAX) OF IA5String }
#                   -- Places to get the same "LTD" file
class ASN1LogotypeReference(core.Sequence):
    _fields = [
        ('refStructHash', SequenceOfASN1HashAlgAndValue),
        ('refStructURI', SequenceOfIA5String),
    ]

# LogotypeInfo ::= CHOICE {
#   direct      [0] LogotypeData,
#   indirect    [1] LogotypeReference }
class ASN1LogotypeInfo(core.Choice):
    _alternatives = [
        ('direct', ASN1LogotypeData, {'implicit': 0}),
        ('indirect', ASN1LogotypeReference, {'implicit': 1}),
    ]

# OtherLogotypeInfo ::= SEQUENCE {
#   logotypeType    OBJECT IDENTIFIER,
#   info            LogotypeInfo }
class ASN1OtherLogotypeInfo(core.Sequence):
    _fields = [
        ('logotypeType', core.ObjectIdentifier),
        ('info', ASN1LogotypeInfo),
    ]

class SequenceOfASN1LogotypeInfo(core.SequenceOf):
    _child_spec = ASN1LogotypeInfo

class SequenceOfASN1OtherLogotypeInfo(core.SequenceOf):
    _child_spec = ASN1OtherLogotypeInfo

# LogotypeExtn ::= SEQUENCE {
#   communityLogos  [0] EXPLICIT SEQUENCE OF LogotypeInfo OPTIONAL,
#   issuerLogo      [1] EXPLICIT LogotypeInfo OPTIONAL,
#   subjectLogo     [2] EXPLICIT LogotypeInfo OPTIONAL,
#   otherLogos      [3] EXPLICIT SEQUENCE OF OtherLogotypeInfo OPTIONAL }
class ASN1LogotypeExtn(core.Sequence):
    _fields = [
        ('communityLogos', SequenceOfASN1LogotypeInfo, {'explicit': 0, 'optional': True}),
        ('issuerLogo', ASN1LogotypeInfo, {'explicit': 1, 'optional': True}),
        ('subjectLogo', ASN1LogotypeInfo, {'explicit': 2, 'optional': True}),
        ('otherLogos', SequenceOfASN1OtherLogotypeInfo, {'explicit': 3, 'optional': True}),
    ]

class LogotypeHash():
    def __init__(self, algorithm, value) -> None:
        if algorithm == oidDigestAlgorithmMD5:
            self.algorithm = 'md5'
        elif algorithm == oidDigestAlgorithmSHA1:
            self.algorithm = 'sha1'
        elif algorithm == oidDigestAlgorithmSHA256:
            self.algorithm = 'sha256'
        elif algorithm == oidDigestAlgorithmSHA384:
            self.algorithm = 'sha384'
        elif algorithm == oidDigestAlgorithmSHA512:
            self.algorithm = 'sha512'
        else:
            self.algorithm = None

        self.value = value

def extractHashArray(data) -> list:
    parsed = ASN1LogotypeExtn.load(data)

    if 'subjectLogo' not in parsed:
        raise BimiFail('no supported image found')

    if 'image' not in parsed['subjectLogo'].chosen:
        raise BimiFail('no image found')

    hashArr = []
    for image in parsed['subjectLogo'].chosen['image']:
        if 'imageDetails' in image and \
           'logotypeHash' in image['imageDetails']:
            for hash in image['imageDetails']['logotypeHash']:
                if 'hashAlg' in hash and \
                   'algorithm' in hash['hashAlg'] and \
                   'hashValue' in hash:
                    hashArr.append(LogotypeHash(hash['hashAlg']['algorithm'].native,
                                                hash['hashValue'].native))

    return hashArr
