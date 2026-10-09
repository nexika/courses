"""What four people pay in all after the change, against the bill with its tip."""
import json
import runpy
from pathlib import Path

v = runpy.run_path(str(Path(__file__).with_name("versions.py")))
print(json.dumps(round(4 * v["split_after"](100, 10, 4), 2)))
