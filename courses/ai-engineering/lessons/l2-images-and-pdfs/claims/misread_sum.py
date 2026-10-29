"""What the lines of the misread sample invoice add up to, as the "Try it" code prints it."""
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "exercise" / "tests"
invoice = json.loads((TESTS / "sample_extracted_misread.json").read_text(encoding="utf-8"))
print(json.dumps(sum(line["amount"] for line in invoice["lines"])))
