"""How many messages the second request of the "Try it" round sends, rebuilt from the sample reply."""
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "exercise" / "tests"
reply = json.loads((TESTS / "sample_tool_call.json").read_text(encoding="utf-8"))
assert reply["stop_reason"] == "tool_use"
messages = [{"role": "user", "content": "Where is order A-1042?"}]
messages.append({"role": "assistant", "content": reply["content"]})
results = [{"type": "tool_result", "tool_use_id": b["id"], "content": "{}"}
           for b in reply["content"] if b["type"] == "tool_use"]
assert len(results) == 1
messages.append({"role": "user", "content": results})
assert [m["role"] for m in messages] == ["user", "assistant", "user"]
print(json.dumps(len(messages)))
