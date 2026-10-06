"""Output tokens in the sample reply that stopped with stop_reason max_tokens."""
import json
from pathlib import Path

LESSON = Path(__file__).resolve().parent.parent
reply = json.loads((LESSON / "exercise" / "tests" / "sample_cut_off.json").read_text(encoding="utf-8"))
assert reply["stop_reason"] == "max_tokens"
print(json.dumps(reply["usage"]["output_tokens"]))
