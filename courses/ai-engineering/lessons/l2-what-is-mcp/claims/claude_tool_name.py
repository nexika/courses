"""The tool name Claude sees in the "Try it" code: the host puts the server's name in front of the MCP name."""
import json

listing = {"jsonrpc": "2.0", "id": 1, "result": {"resultType": "complete", "tools": [{
    "name": "lookup_order",
    "description": "Look up a customer's order by its order number and return its status.",
    "inputSchema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}]}}
tools = [{"name": "shop__" + tool["name"], "description": tool["description"],
          "input_schema": tool["inputSchema"]} for tool in listing["result"]["tools"]]
assert len(tools) == 1
print(json.dumps(tools[0]["name"]))
