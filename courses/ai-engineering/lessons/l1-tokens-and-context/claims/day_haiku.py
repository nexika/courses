"""The same 10,000 calls a day on Claude Haiku 4.5, in dollars."""
import json
import sys
from pathlib import Path

# Use the exercise solution and its price table, so the text, the claims and the exercise agree.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "exercise" / "solution"))
from cost import load_prices, workload_cost  # noqa: E402

usage = {"input_tokens": 2000, "output_tokens": 500}
print(json.dumps(round(workload_cost(usage, load_prices()["claude-haiku-4-5"], 10_000), 2)))
