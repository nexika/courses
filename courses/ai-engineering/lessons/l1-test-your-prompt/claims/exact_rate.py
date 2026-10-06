"""The pass rate, in percent, of the lesson's example with the exact-match grader."""
import json
import runpy
from pathlib import Path

example = runpy.run_path(str(Path(__file__).with_name("example.py")))
rate, _ = example["run_eval"](example["CASES"], example["stand_in_model"], example["exact_match"])
print(json.dumps(round(rate * 100)))
