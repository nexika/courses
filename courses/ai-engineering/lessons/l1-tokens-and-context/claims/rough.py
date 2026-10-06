"""The rough guess for 7,000 characters of English text, at 3.5 characters per token."""
import json
import sys
from pathlib import Path

# Use the exercise solution and its price table, so the text, the claims and the exercise agree.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "exercise" / "solution"))
from cost import rough_tokens  # noqa: E402

print(json.dumps(rough_tokens("x" * 7000)))
