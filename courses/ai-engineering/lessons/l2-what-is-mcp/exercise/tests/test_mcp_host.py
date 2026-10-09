import copy
import json
import unittest
from pathlib import Path

from mcp_host import call_request, claude_tools, request, tool_result

HERE = Path(__file__).resolve().parent


def sample(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


LISTING = sample("sample_tools_list.json")


def listing_of(*names):
    return {"jsonrpc": "2.0", "id": 1, "result": {"resultType": "complete", "tools": [
        {"name": n, "description": "A tool.", "inputSchema": {"type": "object"}} for n in names]}}


class Request(unittest.TestCase):
    def test_a_json_rpc_request(self):
        self.assertEqual(request(7, "tools/list", {}),
                         {"jsonrpc": "2.0", "id": 7, "method": "tools/list", "params": {}})

    def test_params_are_kept(self):
        sent = request("a", "tools/call", {"name": "x", "arguments": {"n": 1}})
        self.assertEqual(sent["params"], {"name": "x", "arguments": {"n": 1}})
        self.assertEqual(sent["id"], "a")


class ClaudeTools(unittest.TestCase):
    def test_tools_become_claude_tool_definitions(self):
        tools, routes = claude_tools("shop", LISTING)
        self.assertEqual(len(tools), 2)
        first = tools[0]
        self.assertEqual(first["name"], "shop__lookup_order")
        self.assertEqual(first["description"], LISTING["result"]["tools"][0]["description"])
        self.assertEqual(first["input_schema"], LISTING["result"]["tools"][0]["inputSchema"])
        self.assertNotIn("inputSchema", first)

    def test_names_the_api_refuses_are_made_safe(self):
        tools, routes = claude_tools("shop", LISTING)
        self.assertEqual(tools[1]["name"], "shop__stock_count")
        self.assertEqual(routes["shop__stock_count"], ("shop", "stock.count"))
        tools, _ = claude_tools("my shop", listing_of("a/b"))
        self.assertEqual(tools[0]["name"], "my_shop__a_b")

    def test_two_servers_with_the_same_tool_name(self):
        routes = {}
        claude_tools("docs", listing_of("search"), routes)
        claude_tools("tickets", listing_of("search"), routes)
        self.assertEqual(routes["docs__search"], ("docs", "search"))
        self.assertEqual(routes["tickets__search"], ("tickets", "search"))

    def test_a_name_taken_twice_is_refused(self):
        with self.assertRaises(ValueError):
            claude_tools("shop", listing_of("stock.count", "stock_count"))

    def test_a_name_too_long_is_refused(self):
        tools, _ = claude_tools("s", listing_of("x" * 125))
        self.assertEqual(len(tools[0]["name"]), 128)
        with self.assertRaises(ValueError):
            claude_tools("s", listing_of("x" * 126))

    def test_an_error_response_is_refused(self):
        with self.assertRaises(ValueError):
            claude_tools("shop", sample("sample_call_protocol_error.json"))

    def test_the_listing_is_not_changed(self):
        before = copy.deepcopy(LISTING)
        claude_tools("shop", LISTING)
        self.assertEqual(LISTING, before)


class CallRequest(unittest.TestCase):
    def test_a_call_goes_to_the_server_that_owns_the_tool(self):
        routes = {}
        claude_tools("shop", LISTING, routes)
        claude_tools("docs", listing_of("search"), routes)
        use = {"type": "tool_use", "id": "toolu_1", "name": "shop__stock_count", "input": {"sku": "K-7"}}
        server, sent = call_request(5, use, routes)
        self.assertEqual(server, "shop")
        self.assertEqual(sent, {"jsonrpc": "2.0", "id": 5, "method": "tools/call",
                                "params": {"name": "stock.count", "arguments": {"sku": "K-7"}}})

    def test_an_unknown_tool(self):
        with self.assertRaises(KeyError):
            call_request(5, {"type": "tool_use", "id": "toolu_1", "name": "shop__nope", "input": {}}, {})


class ToolResult(unittest.TestCase):
    def sent(self, request_id):
        return request(request_id, "tools/call", {"name": "lookup_order", "arguments": {}})

    def test_a_result(self):
        block = tool_result("toolu_1", self.sent(2), sample("sample_call_ok.json"))
        self.assertEqual(block["type"], "tool_result")
        self.assertEqual(block["tool_use_id"], "toolu_1")
        self.assertEqual(block["content"], "Order A-1042: shipped.\nExpected delivery in 2 days.")
        self.assertFalse(block.get("is_error", False))

    def test_a_tool_execution_error_keeps_its_message(self):
        response = sample("sample_call_tool_error.json")
        block = tool_result("toolu_2", self.sent(3), response)
        self.assertIs(block["is_error"], True)
        self.assertEqual(block["content"], response["result"]["content"][0]["text"])

    def test_a_protocol_error(self):
        block = tool_result("toolu_3", self.sent(4), sample("sample_call_protocol_error.json"))
        self.assertIs(block["is_error"], True)
        self.assertIn("-32602", block["content"])
        self.assertIn("Unknown tool: track_parcel", block["content"])

    def test_items_that_are_not_text(self):
        response = {"jsonrpc": "2.0", "id": 9, "result": {"content": [
            {"type": "text", "text": "Chart below."},
            {"type": "image", "data": "iVBORw0KGgo=", "mimeType": "image/png"}]}}
        block = tool_result("toolu_4", self.sent(9), response)
        self.assertEqual(block["content"], "Chart below.\n[image not shown]")
        self.assertNotIn("iVBORw0KGgo=", block["content"])

    def test_a_response_to_another_request_is_refused(self):
        with self.assertRaises(ValueError):
            tool_result("toolu_1", self.sent(99), sample("sample_call_ok.json"))


if __name__ == "__main__":
    unittest.main()
