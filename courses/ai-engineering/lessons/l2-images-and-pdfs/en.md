# Images and PDFs

## What you will be able to do

- Send an image or a PDF to Claude in a request, as a content block, and know the formats and limits.
- Estimate what an image costs in tokens before you send it.
- Check what Claude extracts from an image or a PDF before you use it, and know when a person must look.

## The idea

So far you sent Claude text. Claude can also understand and analyze images[^v-what]. And you can ask it
about the text, pictures, charts and tables in a PDF[^p-what]. One use is
to turn a document into structured data, such as the fields of an invoice[^p-what].

**An image is a content block**

In the lesson "Your first API call", a user turn's `content` was a string, and a reply's `content` was a
list of blocks. A user turn's `content` can also be a list of content blocks, and an image is one of
them[^v-sources]. The API takes an image in one of three ways: the image's
bytes in the request, encoded in `base64`; a URL where the image is online; or a `file_id` from the Files
API, where you upload a file once and refer to it many times[^v-sources]. Here is the first way:

```json
{"role": "user", "content": [
  {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": "iVBORw0KGgo..."}},
  {"type": "text", "text": "What does this receipt say?"}
]}
```

`base64` turns any bytes into plain letters, digits and a few signs, so that a file can travel inside JSON. In
Python, a file's raw content is a `bytes` value, written like `b"GIF89a"`; inside it, `\x89` is one
byte, written in hexadecimal (see below). `.decode("ascii")` turns the `base64` bytes into an
ordinary string, which JSON needs; ASCII is the basic set of English letters, digits and signs. The
*media type* is a label that says what kind of file it is, such as `image/png`. Claude accepts JPEG,
PNG, GIF and WebP images; for an animated image, it uses only the first frame[^v-formats]. Put the image
before your question: Claude works best that way, though other orders still work[^v-order].

Do not trust a file's name to tell you its type. Look at its first bytes: every PNG file starts with the
same eight bytes, `89 50 4E 47 0D 0A 1A 0A` in hexadecimal[^png-sig], and the other formats have their
own signatures, listed in the exercise. (Bytes are usually written in hexadecimal, a way of writing
numbers that also uses the letters A to F.)

**A PDF is a document block**

A PDF goes in a block of type `document`, with the media type `application/pdf`[^p-type]. Like images, it can be
sent as a URL, in `base64`, or by `file_id`[^p-ways]. The API turns each page into an image and also
extracts each page's text, and Claude reads both. That is how it can answer questions about charts and
diagrams, not only the text[^p-how].

**What it costs, and the limits**

Claude sees an image as patches of 28 × 28 pixels; each patch is one *visual token*[^v-cost]. An image costs
⌈width / 28⌉ × ⌈height / 28⌉ visual tokens, where ⌈ ⌉ means "round up"[^v-cost]. A 1000 × 1000 image
costs 36 × 36 = 1296 visual tokens[^v-table]. Images larger than a model's limits are made smaller before Claude sees
them[^v-downscale]. On Claude 4.7 and later models, the limit is 2576 pixels on the long edge and 4784
visual tokens[^v-tiers]. Claude Opus 5.5, the model this course uses, is one of these later models, so
these limits apply to it[^v-tiers].
On that model, a 1920 × 1080 image costs 2691 visual tokens, without being resized[^v-table-hd]. Send an image only as large as the task needs.

A PDF page costs tokens twice. Each page's text typically uses 1,500 to 3,000 tokens, and each page's image is
counted like any other image[^p-cost]. Dense PDFs, with small fonts, complex tables or heavy graphics, can
fill the context window before the page limit[^p-dense].

The main limits on the Claude API. Claude is also offered through other cloud services, such as Amazon
Bedrock and Google Cloud, and some limits are lower there[^v-size]:

- An image may be at most 8000 × 8000 pixels[^v-dims] (or, to be safe on every service, 2000 × 2000
  when a request holds more than 20 images[^v-many]), and at most 10 MB once encoded in `base64`[^v-size].
- A request may hold up to 600 images, or 100 on models with a 200k-token context window[^v-count].
- A PDF request may hold up to 600 pages, or 100 when the context window is under 1M tokens; the whole
  request may be at most 32 MB on the Claude API (other services differ), and the PDF may not have a password or be encrypted[^p-limits].

**Check what Claude extracts**

Claude can be wrong about what it sees. It may make mistakes on images that are low in quality, rotated or very
small (under 200 pixels), its counts of many small objects are approximate, and it cannot tell whether an
image was made by AI[^v-limits]. It does not see an image's metadata, such as the date stored in a
photo[^v-meta]. PDFs have the same limits, since Claude reads their pages as images[^p-vision].
Anthropic's guide asks you to review and verify what Claude says about images, and not to use it for
tasks that need perfect precision without a person checking[^v-verify].

So treat an extraction like any other model output, as in the lesson on JSON output: check it before you
use it. Three checks help:

1) **Shape:** the JSON has the fields you need, with the right types (your `validate` from that lesson).
2) **Sums:** the numbers agree with each other. On an invoice, the lines add up to the total.
3) **Source:** the values appear in something you got another way, such as the record of the system
   that issued the invoice.

When a check fails, do not guess: send the document to a person.

## Try it

### Without a key: build a request and check an extraction

This script reads a tiny PNG, the example image from Anthropic's vision guide[^v-example], written as `base64`
text. It checks the file's first bytes, reads its size, counts visual tokens, and builds the request.
Then it checks two sample extractions of an invoice: one correct, one where an amount was misread. Save
it as `look_and_check.py` in the lesson folder and run `python3 look_and_check.py` from that folder:

```python
"""Build an image request and check an extraction, offline. No network, no key."""
import base64
import json
import math
import struct
from pathlib import Path

# 1. A tiny PNG (one pixel), written as base64 text. Real code reads a file: Path("photo.png").read_bytes()
data = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGP4z8AAAAMBAQDJ/pLvAAAAAElFTkSuQmCC")
print("starts like a PNG:", data.startswith(b"\x89PNG\r\n\x1a\n"))
width, height = struct.unpack(">II", data[16:24])
print("size:", width, "x", height)

# 2. What it costs: one visual token per 28 x 28 patch.
for w, h in ((width, height), (1000, 1000), (1920, 1080)):
    print(f"{w} x {h}:", math.ceil(w / 28) * math.ceil(h / 28), "visual tokens")

# 3. The request: the image first, then the question.
request = {"model": "claude-opus-5-5", "max_tokens": 1024, "messages": [{"role": "user", "content": [
    {"type": "image", "source": {"type": "base64", "media_type": "image/png",
                                 "data": base64.standard_b64encode(data).decode("ascii")}},
    {"type": "text", "text": "What colour is this pixel?"}]}]}
print(json.dumps(request)[:160], "...")

# 4. Check an extraction: do the line amounts add up to the total?
folder = Path("exercise/tests")
for name in ("sample_extracted_ok.json", "sample_extracted_misread.json"):
    invoice = json.loads((folder / name).read_text(encoding="utf-8"))
    lines = sum(line["amount"] for line in invoice["lines"])
    print(name, "lines add up to", lines, "total says", invoice["total"],
          "OK" if abs(lines - invoice["total"]) < 0.005 else "CHECK BY HAND")
```

`math.ceil` rounds up, like ⌈ ⌉ above. `struct.unpack(">II", ...)` reads two whole numbers of four bytes
each, the width and the height; `>` means big-endian, where the first byte counts most, as the first
digit of a written number counts most. A
PNG is made of *chunks*, labelled pieces of data, and the first chunk's data starts with the width and
the height[^png-ihdr]; in the file, they come right after the first sixteen bytes.

In the misread sample, the lines add up to 1404.5, less than the
total: one amount is wrong, and the sum check caught it without knowing which. The script allows a tiny
difference, because numbers with decimals are not exact in Python:
`0.1 + 0.2` gives `0.30000000000000004`.

The samples are shaped like real extractions but were written by hand; the invoice is made up.

### With your own key (optional)

This sends a real image, so it needs a key and its tokens are billed. Set up the key and the SDK as in
the lesson "Your first API call". Use a photo or a scan of a receipt of your own, saved as
`receipt.jpg`:

```python
import base64
from pathlib import Path

import anthropic

data = Path("receipt.jpg").read_bytes()
client = anthropic.Anthropic()
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": [
        {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg",
                                     "data": base64.standard_b64encode(data).decode("ascii")}},
        {"type": "text", "text": "List each item and its price as JSON, then the total."},
    ]}],
)
print("".join(block.text for block in message.content if block.type == "text"))
print("input tokens:", message.usage.input_tokens)
```

For a PDF, use `"type": "document"` and `"media_type": "application/pdf"`. Compare what comes back
with the receipt itself, line by line.

## Common mistakes

- **Trusting the extraction because it looks tidy.** Clean JSON can still hold a misread number. Check
  the shape, the sums and the source[^v-verify].
- **Guessing the type from the file name.** A file called `scan.png` may be a JPEG, and the media type
  you send must match the bytes. Read the first bytes[^png-sig].
- **Sending huge images.** They cost more tokens and are made smaller anyway[^v-downscale]. Resize them yourself to
  what the task needs.
- **Putting the question before the image.** It still works, but Claude works best with the image
  first[^v-order].
- **Asking Claude to count many small things or to name a person.** Counts are approximate, and Claude
  will not identify people in images[^v-limits].
- **Sending a Word or Excel file as a document.** Formats such as `.docx` and `.xlsx` are not accepted in
  document blocks; convert them to text or PDF first[^p-binary].

## Your exercise

### What to build

Open `exercise/starter/media.py`. It gives you the file signatures and the limits as constants. Write
five functions; they run offline, and the tests make their own small PNG files.

- `media_type(data)` returns the media type from the file's first bytes, or raises `ValueError`.
- `content_block(data)` returns the image or document block, with the bytes in `base64`. It refuses an
  image whose `base64` text is longer than the 10 MB limit[^v-size].
- `png_size(data)` returns a PNG's width and height, read from its first chunk (the starter explains
  where they are).
- `visual_tokens(width, height)` returns the cost in visual tokens, and raises `ValueError` for an image
  the API would make smaller, so that you resize it yourself first.
- `check_invoice(extracted, source_text)` returns the problems in an invoice that Claude extracted: missing
  fields, lines that do not add up to the total, and values that do not appear in the source text.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

The tests fail until your functions work. A solution is in `exercise/solution/`: try first, then compare.

## Check yourself

Take the quiz for this lesson. If a question is hard, read "What it costs, and the limits" and "Check what
Claude extracts" again.

[^v-what]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-what]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-sources]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-formats]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-order]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^png-sig]: Portable Network Graphics (PNG) Specification (Third Edition), <https://www.w3.org/TR/png-3/>
[^p-ways]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-how]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-cost]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-tiers]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-cost]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-dense]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-dims]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-size]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-count]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-limits]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-limits]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-meta]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-vision]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^v-verify]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-table]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^png-ihdr]: Portable Network Graphics (PNG) Specification (Third Edition), <https://www.w3.org/TR/png-3/>
[^v-downscale]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-table-hd]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-many]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^v-example]: Vision, <https://platform.claude.com/docs/en/build-with-claude/vision>
[^p-type]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
[^p-binary]: PDF support, <https://platform.claude.com/docs/en/build-with-claude/pdf-support>
