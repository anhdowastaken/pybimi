from asn1crypto import core
from .exception import BimiFail

oidLogotype              = '1.3.6.1.5.5.7.1.12'
oidDigestAlgorithmMD5    = '1.2.840.113549.2.5'
oidDigestAlgorithmSHA1   = '1.3.14.3.2.26'
oidDigestAlgorithmSHA256 = '2.16.840.1.101.3.4.2.1'
oidDigestAlgorithmSHA384 = '2.16.840.1.101.3.4.2.2'
oidDigestAlgorithmSHA512 = '2.16.840.1.101.3.4.2.3'

class ASN1AlgorithmIdentifier(core.Sequence):
    """
    AlgorithmIdentifier  ::=  SEQUENCE  {
      algorithm   OBJECT IDENTIFIER,
      parameters  ANY DEFINED BY algorithm OPTIONAL  }
    """

    _fields = [
        ('algorithm', core.ObjectIdentifier),
        ('parameters', core.Any, {'optional': True}),
    ]

class ASN1HashAlgAndValue(core.Sequence):
    """
    HashAlgAndValue ::= SEQUENCE {
      hashAlg     AlgorithmIdentifier,
      hashValue   OCTET STRING }
    """

    _fields = [
        ('hashAlg', ASN1AlgorithmIdentifier),
        ('hashValue', core.OctetString),
    ]

class SequenceOfASN1HashAlgAndValue(core.SequenceOf):
    _child_spec = ASN1HashAlgAndValue

class SequenceOfIA5String(core.SequenceOf):
    _child_spec = core.IA5String

class ASN1LogotypeDetails(core.Sequence):
    """
    LogotypeDetails ::= SEQUENCE {
      mediaType       IA5String, -- MIME media type name and optional
                                 -- parameters
      logotypeHash    SEQUENCE SIZE (1..MAX) OF HashAlgAndValue,
      logotypeURI     SEQUENCE SIZE (1..MAX) OF IA5String }
    """

    _fields = [
        ('mediaType', core.IA5String),
        ('logotypeHash', SequenceOfASN1HashAlgAndValue),
        ('logotypeURI', SequenceOfIA5String),
    ]

# LogotypeImageType ::= INTEGER { grayScale(0), color(1) }

class ASN1LogotypeImageResolution(core.Choice):
    """
    LogotypeImageResolution ::= CHOICE {
      numBits     [1] INTEGER,   -- Resolution in bits
      tableSize   [2] INTEGER }  -- Number of colors or grey tones
    """

    _alternatives = [
        ('numBits', core.Integer, {'implicit': 1}),
        ('tableSize', core.Integer, {'implicit': 2}),
    ]

class ASN1LogotypeImageInfo(core.Sequence):
    """
    LogotypeImageInfo ::= SEQUENCE {
      type        [0] LogotypeImageType DEFAULT color,
      fileSize    INTEGER,  -- In octets
      xSize       INTEGER,  -- Horizontal size in pixels
      ySize       INTEGER,  -- Vertical size in pixels
      resolution  LogotypeImageResolution OPTIONAL,
      language    [4] IA5String OPTIONAL }  -- RFC 3066 Language Tag
    """

    _fields = [
        ('type', core.Integer, {'implicit': 0, 'default': 1}),
        ('fileSize', core.Integer),
        ('xSize', core.Integer),
        ('ySize', core.Integer),
        ('resolution', ASN1LogotypeImageResolution, {'optional': True}),
        ('language', core.IA5String, {'implicit': 4, 'optional': True}),
    ]

class ASN1LogotypeAudioInfo(core.Sequence):
    """
    LogotypeAudioInfo ::= SEQUENCE {
      fileSize    INTEGER,  -- In octets
      playTime    INTEGER,  -- In milliseconds
      channels    INTEGER,  -- 1=mono, 2=stereo, 4=quad
      sampleRate  [3] INTEGER OPTIONAL,  -- Samples per second
      language    [4] IA5String OPTIONAL }  -- RFC 3066 Language Tag
    """

    _fields = [
        ('fileSize', core.Integer),
        ('playTime', core.Integer),
        ('channels', core.Integer),
        ('sampleRate', core.Integer, {'implicit': 3, 'optional': True}),
        ('language', core.IA5String, {'implicit': 4, 'optional': True}),
    ]

class ASN1LogotypeImage(core.Sequence):
    """
    LogotypeImage ::= SEQUENCE {
      imageDetails    LogotypeDetails,
      imageInfo       LogotypeImageInfo OPTIONAL }
    """

    _fields = [
        ('imageDetails', ASN1LogotypeDetails),
        ('imageInfo', ASN1LogotypeImageInfo, {'optional': True}),
    ]

class ASN1LogotypeAudio(core.Sequence):
    """
    LogotypeAudio ::= SEQUENCE {
      audioDetails    LogotypeDetails,
      audioInfo       LogotypeAudioInfo OPTIONAL }
    """

    _fields = [
        ('audioDetails', ASN1LogotypeDetails),
        ('audioInfo', ASN1LogotypeAudioInfo, {'optional': True}),
    ]

class SequenceOfASN1LogotypeImage(core.SequenceOf):
    _child_spec = ASN1LogotypeImage

class SequenceOfASN1LogotypeAudio(core.SequenceOf):
    _child_spec = ASN1LogotypeAudio

class ASN1LogotypeData(core.Sequence):
    """
    LogotypeData ::= SEQUENCE {
      image   SEQUENCE OF LogotypeImage OPTIONAL,
      audio   [1] SEQUENCE OF LogotypeAudio OPTIONAL }
    """

    _fields = [
        ('image', SequenceOfASN1LogotypeImage, {'optional': True}),
        ('audio', SequenceOfASN1LogotypeAudio, {'implicit': 1, 'optional': True}),
    ]

class ASN1LogotypeReference(core.Sequence):
    """
    LogotypeReference ::= SEQUENCE {
      refStructHash   SEQUENCE SIZE (1..MAX) OF HashAlgAndValue,
      refStructURI    SEQUENCE SIZE (1..MAX) OF IA5String }
                      -- Places to get the same "LTD" file
    """

    _fields = [
        ('refStructHash', SequenceOfASN1HashAlgAndValue),
        ('refStructURI', SequenceOfIA5String),
    ]

class ASN1LogotypeInfo(core.Choice):
    """
    LogotypeInfo ::= CHOICE {
      direct      [0] LogotypeData,
      indirect    [1] LogotypeReference }
    """

    _alternatives = [
        ('direct', ASN1LogotypeData, {'implicit': 0}),
        ('indirect', ASN1LogotypeReference, {'implicit': 1}),
    ]

class ASN1OtherLogotypeInfo(core.Sequence):
    """
    OtherLogotypeInfo ::= SEQUENCE {
      logotypeType    OBJECT IDENTIFIER,
      info            LogotypeInfo }
    """

    _fields = [
        ('logotypeType', core.ObjectIdentifier),
        ('info', ASN1LogotypeInfo),
    ]

class SequenceOfASN1LogotypeInfo(core.SequenceOf):
    _child_spec = ASN1LogotypeInfo

class SequenceOfASN1OtherLogotypeInfo(core.SequenceOf):
    _child_spec = ASN1OtherLogotypeInfo

class ASN1LogotypeExtn(core.Sequence):
    """
    LogotypeExtn ::= SEQUENCE {
      communityLogos  [0] EXPLICIT SEQUENCE OF LogotypeInfo OPTIONAL,
      issuerLogo      [1] EXPLICIT LogotypeInfo OPTIONAL,
      subjectLogo     [2] EXPLICIT LogotypeInfo OPTIONAL,
      otherLogos      [3] EXPLICIT SEQUENCE OF OtherLogotypeInfo OPTIONAL }
    """

    _fields = [
        ('communityLogos', SequenceOfASN1LogotypeInfo, {'explicit': 0, 'optional': True}),
        ('issuerLogo', ASN1LogotypeInfo, {'explicit': 1, 'optional': True}),
        ('subjectLogo', ASN1LogotypeInfo, {'explicit': 2, 'optional': True}),
        ('otherLogos', SequenceOfASN1OtherLogotypeInfo, {'explicit': 3, 'optional': True}),
    ]

class LogotypeHash():
    """
    The class used to represent hash of a logo type

    Attributes
    ----------
    algorithm: str
        Hash algorithm
    value: str
        Hash value
    """

    def __init__(self, algorithm, value) -> None:
        """
        Parameters
        ----------
        algorithm: str
            OID hash algorithm
            Supported algorithms:
            - MD5   : 1.2.840.113549.2.5
            - SHA1  : 1.3.14.3.2.26
            - SHA256: 2.16.840.1.101.3.4.2.1
            - SHA384: 2.16.840.1.101.3.4.2.2
            - SHA512: 2.16.840.1.101.3.4.2.3
        value: str
            Hash value
        """

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
    """
    Extract hash array from ASN1 logo type extension data

    Parameters
    ----------
    data: any
        A byte string of BER or DER-encoded data

    Returns
    -------
    list
        A list of LogotypeHash
    """

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
