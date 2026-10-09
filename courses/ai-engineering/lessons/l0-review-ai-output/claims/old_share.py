"""What each of four people pays on a bill of 100 with a 10% tip, before the change."""
import json
import runpy
from pathlib import Path

v = runpy.run_path(str(Path(__file__).with_name("versions.py")))
print(json.dumps(v["split_before"](100, 10, 4)))
