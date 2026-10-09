"""The priority in the sample reply that is valid JSON but out of range."""
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "exercise" / "tests"
reply = json.loads((TESTS / "sample_out_of_range.json").read_text(encoding="utf-8"))
assert reply["stop_reason"] == "end_turn"
ticket = json.loads(reply["content"][0]["text"])
assert set(ticket) == {"category", "priority", "summary"}
print(json.dumps(ticket["priority"]))
