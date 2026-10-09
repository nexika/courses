"""How many servers in the sample .mcp.json run a command on your computer (local, stdio servers)."""
import json
from pathlib import Path

TESTS = Path(__file__).resolve().parent.parent / "exercise" / "tests"
config = json.loads((TESTS / "sample_mcp.json").read_text(encoding="utf-8"))
servers = config["mcpServers"]
assert len(servers) == 5
print(json.dumps(sum(1 for entry in servers.values() if "command" in entry)))
