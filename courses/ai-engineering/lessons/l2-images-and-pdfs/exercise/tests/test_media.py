import base64
import json
import struct
import unittest
import zlib
from pathlib import Path

from media import MAX_IMAGE_BASE64, check_invoice, content_block, media_type, png_size, visual_tokens

HERE = Path(__file__).resolve().parent
SOURCE = (HERE / "invoice_source.txt").read_text(encoding="utf-8")


def sample(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def png(width, height):
    """A real, valid grey PNG of the given size, made with the standard library."""
    def chunk(kind, body):
        return struct.pack(">I", len(body)) + kind + body + struct.pack(">I", zlib.crc32(kind + body))
    rows = b"".join(b"\x00" + b"\x80" * width for _ in range(height))
    header = struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows))
            + chunk(b"IEND", b""))


JPEG = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00" + b"\x00" * 20
GIF = b"GIF89a" + b"\x01\x00\x01\x00" + b"\x00" * 20
WEBP = b"RIFF" + struct.pack("<I", 30) + b"WEBPVP8 " + b"\x00" * 20
PDF = b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n1 0 obj\n<< /Type /Catalog >>\nendobj\n"


class MediaType(unittest.TestCase):
    def test_each_kind(self):
        self.assertEqual(media_type(png(2, 2)), "image/png")
        self.assertEqual(media_type(JPEG), "image/jpeg")
        self.assertEqual(media_type(GIF), "image/gif")
        self.assertEqual(media_type(b"GIF87a" + b"\x00" * 10), "image/gif")
        self.assertEqual(media_type(WEBP), "image/webp")
        self.assertEqual(media_type(PDF), "application/pdf")

    def test_other_files_are_refused(self):
        for data in (b"", b"hello", b"RIFF\x00\x00\x00\x00WAVE", b"BM" + b"\x00" * 30, b"PK\x03\x04docx"):
            with self.assertRaises(ValueError):
                media_type(data)


class ContentBlock(unittest.TestCase):
    def test_an_image(self):
        data = png(3, 2)
        block = content_block(data)
        self.assertEqual(block["type"], "image")
        self.assertEqual(block["source"]["type"], "base64")
        self.assertEqual(block["source"]["media_type"], "image/png")
        self.assertEqual(base64.b64decode(block["source"]["data"]), data)
        self.assertIsInstance(block["source"]["data"], str)

    def test_a_pdf_is_a_document(self):
        block = content_block(PDF)
        self.assertEqual(block["type"], "document")
        self.assertEqual(block["source"]["media_type"], "application/pdf")
        self.assertEqual(base64.b64decode(block["source"]["data"]), PDF)

    def test_an_image_too_large(self):
        big = JPEG + b"\x00" * (MAX_IMAGE_BASE64 // 4 * 3)
        with self.assertRaises(ValueError):
            content_block(big)
        fits = JPEG + b"\x00" * (MAX_IMAGE_BASE64 // 4 * 3 - len(JPEG) - 3)
        self.assertEqual(content_block(fits)["type"], "image")

    def test_an_unknown_file(self):
        with self.assertRaises(ValueError):
            content_block(b"just text")


class PngSize(unittest.TestCase):
    def test_sizes(self):
        self.assertEqual(png_size(png(1, 1)), (1, 1))
        self.assertEqual(png_size(png(300, 7)), (300, 7))

    def test_not_a_png(self):
        with self.assertRaises(ValueError):
            png_size(JPEG)


class VisualTokens(unittest.TestCase):
    def test_the_documented_examples(self):
        self.assertEqual(visual_tokens(200, 200), 64)
        self.assertEqual(visual_tokens(1000, 1000), 1296)
        self.assertEqual(visual_tokens(1920, 1080), 2691)

    def test_a_partial_patch_counts_as_a_whole_one(self):
        self.assertEqual(visual_tokens(1, 1), 1)
        self.assertEqual(visual_tokens(28, 28), 1)
        self.assertEqual(visual_tokens(29, 28), 2)

    def test_images_the_api_would_downscale(self):
        for width, height in ((2577, 100), (100, 2577), (3840, 2160), (2576, 2576)):
            with self.assertRaises(ValueError):
                visual_tokens(width, height)
        self.assertEqual(visual_tokens(2576, 28), 92)
        self.assertEqual(visual_tokens(2000, 1500), 3888)

    def test_no_pixels(self):
        with self.assertRaises(ValueError):
            visual_tokens(0, 10)


class CheckInvoice(unittest.TestCase):
    def test_a_good_extraction(self):
        self.assertEqual(check_invoice(sample("sample_extracted_ok.json"), SOURCE), [])

    def test_a_misread_amount(self):
        problems = check_invoice(sample("sample_extracted_misread.json"), SOURCE)
        self.assertIn(("sum", None), problems)
        self.assertIn(("not-in-source", "130.00"), problems)
        self.assertEqual(len(problems), 2)

    def test_missing_fields(self):
        self.assertEqual(check_invoice({"total": 1.0}, SOURCE), [("missing", "invoice_number"), ("missing", "lines")])

    def test_a_wrong_invoice_number(self):
        extracted = sample("sample_extracted_ok.json")
        extracted["invoice_number"] = "INV-2026-0471"
        self.assertEqual(check_invoice(extracted, SOURCE), [("not-in-source", "INV-2026-0471")])

    def test_a_total_that_adds_up_but_is_not_on_the_invoice(self):
        extracted = {"invoice_number": "INV-2026-0417", "total": 1430.0,
                     "lines": [{"item": "Website design", "amount": 1250.0},
                               {"item": "Hosting, 12 months", "amount": 180.0}]}
        self.assertEqual(check_invoice(extracted, SOURCE), [("not-in-source", "1430.00")])

    def test_a_number_inside_another_does_not_count(self):
        extracted = {"invoice_number": "INV-2026-0417", "total": 250.0,
                     "lines": [{"item": "Website design", "amount": 250.0}]}
        self.assertEqual(check_invoice(extracted, SOURCE), [("not-in-source", "250.00"), ("not-in-source", "250.00")])

    def test_an_invoice_number_inside_another_does_not_count(self):
        extracted = sample("sample_extracted_ok.json")
        extracted["invoice_number"] = "INV-2026-04"
        self.assertEqual(check_invoice(extracted, SOURCE), [("not-in-source", "INV-2026-04")])

    def test_rounding(self):
        extracted = {"invoice_number": "A-1", "total": 0.3,
                     "lines": [{"item": "x", "amount": 0.1}, {"item": "y", "amount": 0.2}]}
        self.assertEqual(check_invoice(extracted, "A-1 0.10 0.20 0.30"), [])


if __name__ == "__main__":
    unittest.main()
