"""Send images and PDFs to Claude, and check what it extracts before you use it.

Write media_type(), content_block(), png_size(), visual_tokens() and check_invoice(). Run the tests from
this folder with:
    python3 -m unittest discover -s ../tests
"""
import base64  # noqa: F401  (content_block needs it)
import math  # noqa: F401  (visual_tokens needs it)
import re  # noqa: F401  (check_invoice can use it)
import struct  # noqa: F401  (png_size needs it)

# The first bytes of each kind of file Claude accepts, and the media type the API expects for it.
SIGNATURES = [
    (b"\x89PNG\r\n\x1a\n", "image/png"),
    (b"\xff\xd8\xff", "image/jpeg"),
    (b"GIF87a", "image/gif"),
    (b"GIF89a", "image/gif"),
    (b"%PDF-", "application/pdf"),
]
MAX_IMAGE_BASE64 = 10_000_000  # 10 MB of base64 text per image on the Claude API (read as 10 million, to be safe)
PATCH = 28  # Claude sees an image as 28 x 28 pixel patches; each patch is one visual token
MAX_LONG_EDGE = 2576  # on Claude 4.7 and later models, such as Claude Opus 5.5: larger images are made smaller
MAX_VISUAL_TOKENS = 4784


def media_type(data):
    """Return the media type of a file from its first bytes, not from its name.

    WebP files start with b"RIFF", four bytes of size, then b"WEBP". Raise ValueError for anything else.
    """
    raise NotImplementedError


def content_block(data):
    """Return the content block that sends these bytes to Claude, encoded in base64.

    An image becomes {"type": "image", "source": {"type": "base64", "media_type": ..., "data": ...}};
    a PDF becomes the same with "type": "document". Raise ValueError for an image whose base64 text is
    longer than MAX_IMAGE_BASE64.
    """
    raise NotImplementedError


def png_size(data):
    """Return (width, height) of a PNG, read from its IHDR chunk. Raise ValueError if data is not a PNG.

    After the 8-byte signature comes the first chunk: 4 bytes of length, the 4 bytes b"IHDR", then the
    width and the height, each 4 bytes, big-endian: the first byte counts most, as the first digit of a
    written number counts most. struct.unpack(">II", ...) reads two such numbers.
    """
    raise NotImplementedError


def visual_tokens(width, height):
    """Return the visual tokens an image costs: ceil(width / 28) * ceil(height / 28).

    Raise ValueError if the width or the height is under 1.
    Raise ValueError if the image is larger than MAX_LONG_EDGE on its long edge or would cost more than
    MAX_VISUAL_TOKENS: the API would make it smaller, so resize it yourself and count again.
    """
    raise NotImplementedError


def check_invoice(extracted, source_text):
    """Check what Claude extracted from an invoice. Return a list of problems; an empty list means usable.

    extracted should hold "invoice_number" (a string), "total" (a number) and "lines" (a list of
    {"item": string, "amount": number}). source_text is text you got another way, such as from the
    system that issued the invoice. Report:
    - ("missing", field) for each of the three fields that is absent
    - ("sum", None) when the line amounts do not add up to the total (allow 0.005: numbers with decimals
      are not exact in Python, and 0.1 + 0.2 gives 0.30000000000000004)
    - ("not-in-source", value) for the invoice number and each amount or total, written with two
      decimals ("1250.00"), that does not appear in source_text once commas are removed, as a complete
      number, not as part of a longer one: "250.00" inside "1250.00" does not count. The invoice number
      must also appear on its own: "INV-1" inside "INV-12" does not count.
    """
    raise NotImplementedError
