"""How many text pieces (text_delta events) the sample stream sends, and that they rebuild the sample reply."""
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "exercise" / "tests"
events = json.loads((TESTS / "sample_stream.json").read_text(encoding="utf-8"))
reply = json.loads((TESTS / "sample_reply.json").read_text(encoding="utf-8"))
pieces = [e["delta"]["text"] for e in events
          if e["type"] == "content_block_delta" and e["delta"]["type"] == "text_delta"]
assert "".join(pieces) == reply["content"][0]["text"]
print(json.dumps(len(pieces)))
