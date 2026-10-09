"""The bill of 100 with its 10% tip: what the four people should pay in all."""
import json
import runpy
from pathlib import Path

v = runpy.run_path(str(Path(__file__).with_name("versions.py")))
print(json.dumps(100 + v["tip"](100, 10)))
