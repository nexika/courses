"""Input tokens in the sample reply, which every language of the lesson shows in full."""
import json
import re
from pathlib import Path

LESSON = Path(__file__).resolve().parent.parent
reply = json.loads((LESSON / "exercise" / "tests" / "sample_reply.json").read_text(encoding="utf-8"))
for lang in ("en", "ar", "fr"):
    text = (LESSON / f"{lang}.md").read_text(encoding="utf-8")
    shown = [json.loads(block) for block in re.findall(r"```json\n(.*?)```", text, re.S)]
    assert reply in shown, f"{lang}.md does not show the sample reply as it is in exercise/tests"
print(json.dumps(reply["usage"]["input_tokens"]))
