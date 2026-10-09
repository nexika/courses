"""How many of the four results in the "Try it" code are errors (is_error set)."""
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "exercise" / "tests"
reply = json.loads((TESTS / "sample_four_calls.json").read_text(encoding="utf-8"))
calls = [b for b in reply["content"] if b["type"] == "tool_use"]
assert len(calls) == 4
errors = 0
for block in calls:
    if block["name"] != "lookup_order":
        errors += 1  # unknown tool
    elif set(block["input"]) != {"order_id"}:
        errors += 1  # input does not fit lookup_order(order_id)
    elif block["input"]["order_id"] != "A-1042":
        errors += 1  # no such order
print(json.dumps(errors))
