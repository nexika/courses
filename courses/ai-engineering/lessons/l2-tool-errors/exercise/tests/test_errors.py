import json
import unittest
from pathlib import Path

from errors import ToolError, check_input, run_one, tool_results

HERE = Path(__file__).resolve().parent
LOOKUP = {"name": "lookup_order", "description": "Look up an order by its number.",
          "input_schema": {"type": "object",
                           "properties": {"order_id": {"type": "string"}, "detail": {"type": "boolean"}},
                           "required": ["order_id"]}}
STOCK = {"name": "count_stock", "description": "Count the items left in stock.",
         "input_schema": {"type": "object", "properties": {"sku": {"type": "string"}}, "required": ["sku"]}}
TOOLS = [LOOKUP, STOCK]
SECRET = "password=hunter2 at db.internal:5432"


def lookup_order(order_id, detail=False):
    if order_id == "A-1042":
        return {"order_id": order_id, "status": "shipped"}
    if order_id == "C-1":
        raise ConnectionError(SECRET)
    raise ToolError(f"No order {order_id}. Ask the user to check the number: it looks like A-1042.")


FUNCTIONS = {"lookup_order": lookup_order, "count_stock": lambda sku: "12"}


def call(name, args, cid="toolu_t1"):
    return {"id": cid, "name": name, "input": args}


class CheckInput(unittest.TestCase):
    def test_good_input(self):
        self.assertEqual(check_input(LOOKUP, {"order_id": "A-1042"}), [])
        self.assertEqual(check_input(LOOKUP, {"order_id": "A-1042", "detail": True}), [])

    def test_a_missing_required_field(self):
        problems = check_input(LOOKUP, {})
        self.assertEqual(len(problems), 1)
        self.assertIn("order_id", problems[0])

    def test_an_unknown_field(self):
        problems = check_input(LOOKUP, {"order_id": "A-1042", "order": "B-7"})
        self.assertEqual(len(problems), 1)
        self.assertIn("order", problems[0])

    def test_a_wrong_type(self):
        self.assertIn("order_id", check_input(LOOKUP, {"order_id": 1042})[0])
        self.assertTrue(check_input(LOOKUP, {"order_id": "A-1042", "detail": "yes"}))

    def test_every_problem_is_reported(self):
        self.assertEqual(len(check_input(LOOKUP, {"order": "B-7", "detail": 1})), 3)


class RunOne(unittest.TestCase):
    def test_success_has_no_error_flag(self):
        block = run_one(call("lookup_order", {"order_id": "A-1042"}), TOOLS, FUNCTIONS)
        self.assertEqual(block["type"], "tool_result")
        self.assertEqual(block["tool_use_id"], "toolu_t1")
        self.assertEqual(json.loads(block["content"])["status"], "shipped")
        self.assertFalse(block.get("is_error", False))

    def test_an_unknown_tool_lists_the_real_ones(self):
        block = run_one(call("track_parcel", {"order_id": "A-1042"}), TOOLS, FUNCTIONS)
        self.assertIs(block["is_error"], True)
        self.assertEqual(block["tool_use_id"], "toolu_t1")
        self.assertIn("track_parcel", block["content"])
        self.assertIn("lookup_order", block["content"])
        self.assertIn("count_stock", block["content"])

    def test_bad_input_is_reported_and_the_tool_is_not_run(self):
        ran = []
        functions = {"lookup_order": lambda **kw: ran.append(kw) or "ran", "count_stock": FUNCTIONS["count_stock"]}
        block = run_one(call("lookup_order", {"order": "B-7"}), TOOLS, functions)
        self.assertIs(block["is_error"], True)
        self.assertIn("order_id", block["content"])
        self.assertEqual(ran, [])

    def test_a_tool_error_passes_its_message_to_claude(self):
        block = run_one(call("lookup_order", {"order_id": "A-999"}), TOOLS, FUNCTIONS)
        self.assertIs(block["is_error"], True)
        self.assertEqual(block["content"], "No order A-999. Ask the user to check the number: it looks like A-1042.")

    def test_an_unexpected_failure_is_reported_without_its_details(self):
        block = run_one(call("lookup_order", {"order_id": "C-1"}), TOOLS, FUNCTIONS)
        self.assertIs(block["is_error"], True)
        self.assertIn("lookup_order", block["content"])
        self.assertIn("ConnectionError", block["content"])
        self.assertNotIn("hunter2", block["content"])
        self.assertNotIn("db.internal", block["content"])


class ToolResults(unittest.TestCase):
    def test_every_call_gets_a_result_in_order_even_when_most_fail(self):
        response = json.loads((HERE / "sample_four_calls.json").read_text(encoding="utf-8"))
        message = tool_results(response, TOOLS, FUNCTIONS)
        self.assertEqual(message["role"], "user")
        self.assertEqual([b["tool_use_id"] for b in message["content"]],
                         ["toolu_sample_01", "toolu_sample_02", "toolu_sample_03", "toolu_sample_04"])
        self.assertEqual([b.get("is_error", False) for b in message["content"]], [False, True, True, True])
        self.assertTrue(all(b["type"] == "tool_result" for b in message["content"]))

    def test_a_reply_without_calls_gives_no_results(self):
        response = {"content": [{"type": "text", "text": "Hello."}], "stop_reason": "end_turn"}
        self.assertEqual(tool_results(response, TOOLS, FUNCTIONS), {"role": "user", "content": []})


if __name__ == "__main__":
    unittest.main()
