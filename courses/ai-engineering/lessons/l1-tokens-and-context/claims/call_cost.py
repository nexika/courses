"""One call on Claude Sonnet 5.5: 2000 input tokens, 500 output tokens, in dollars."""
import json
import sys
from pathlib import Path

# Use the exercise solution and its price table, so the text, the claims and the exercise agree.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "exercise" / "solution"))
from cost import call_cost, load_prices  # noqa: E402

usage = {"input_tokens": 2000, "output_tokens": 500}
print(json.dumps(round(call_cost(usage, load_prices()["claude-sonnet-5-5"]), 6)))
