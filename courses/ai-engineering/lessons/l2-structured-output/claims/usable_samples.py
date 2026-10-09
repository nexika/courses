"""How many of the six sample replies pass the checks of the "Try it" code."""
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "exercise" / "tests"
CATEGORIES = ("bug", "billing", "question")
paths = sorted(TESTS.glob("sample_*.json"))
assert len(paths) == 6
usable = 0
for path in paths:
    reply = json.loads(path.read_text(encoding="utf-8"))
    if reply["stop_reason"] != "end_turn":
        continue
    text = "".join(block["text"] for block in reply["content"] if block["type"] == "text")
    try:
        ticket = json.loads(text)
    except json.JSONDecodeError:
        continue
    priority = ticket.get("priority")
    if (str(ticket.get("category")).lower() in CATEGORIES and type(priority) is int and 1 <= priority <= 3
            and isinstance(ticket.get("summary"), str)):
        usable += 1
print(json.dumps(usable))
