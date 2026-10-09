import copy
import json
import unittest
from pathlib import Path

from tools import define_tool, run_tool_loop, tool_calls, tool_results

HERE = Path(__file__).resolve().parent
ORDERS = {"A-1042": "shipped", "B-7": "packing"}


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def lookup_order(order_id):
    return {"order_id": order_id, "status": ORDERS[order_id]}


FUNCTIONS = {"lookup_order": lookup_order}
LOOKUP = {"order_id": {"type": "string", "description": "The order number, such as A-1042."}}


def final(text):
    return {"content": [{"type": "text", "text": text}], "stop_reason": "end_turn"}


def calls(*pairs, prefix="toolu_t"):
    return {"content": [{"type": "tool_use", "id": f"{prefix}{i}", "name": name, "input": args}
                        for i, (name, args) in enumerate(pairs)], "stop_reason": "tool_use"}


class Recorder:
    """A stand-in for the API: returns the replies in order and keeps a copy of each request."""

    def __init__(self, *replies):
        self.replies, self.requests = list(replies), []

    def __call__(self, messages, tools):
        self.requests.append(copy.deepcopy(messages))
        return self.replies[len(self.requests) - 1]


class DefineTool(unittest.TestCase):
    def test_a_definition_has_name_description_and_input_schema(self):
        tool = define_tool("lookup_order", "Look up an order by its number.", LOOKUP, ["order_id"])
        self.assertEqual(tool, {
            "name": "lookup_order", "description": "Look up an order by its number.",
            "input_schema": {"type": "object", "properties": LOOKUP, "required": ["order_id"]}})
        self.assertEqual(json.loads(json.dumps(tool)), tool)

    def test_no_required_fields(self):
        tool = define_tool("list_orders", "List the latest orders.", {})
        self.assertEqual(tool["input_schema"]["required"], [])

    def test_bad_definitions_are_refused(self):
        for name in ("look up", "", "x" * 129, "order.lookup"):
            with self.assertRaises(ValueError):
                define_tool(name, "Look up an order.", LOOKUP, ["order_id"])
        with self.assertRaises(ValueError):
            define_tool("lookup_order", "  ", LOOKUP, ["order_id"])
        with self.assertRaises(ValueError):
            define_tool("lookup_order", "Look up an order.", LOOKUP, ["order_number"])


class ToolCalls(unittest.TestCase):
    def test_text_blocks_are_not_calls(self):
        self.assertEqual(tool_calls(load("sample_tool_call.json")),
                         [{"id": "toolu_sample_01", "name": "lookup_order", "input": {"order_id": "A-1042"}}])

    def test_several_calls_keep_their_order(self):
        self.assertEqual([c["id"] for c in tool_calls(load("sample_two_calls.json"))],
                         ["toolu_sample_02", "toolu_sample_03"])

    def test_a_final_answer_has_no_calls(self):
        self.assertEqual(tool_calls(load("sample_final_answer.json")), [])


class ToolResults(unittest.TestCase):
    def test_one_result_answers_the_call_by_its_id(self):
        message = tool_results(load("sample_tool_call.json"), FUNCTIONS)
        self.assertEqual(message["role"], "user")
        self.assertEqual(len(message["content"]), 1)
        block = message["content"][0]
        self.assertEqual((block["type"], block["tool_use_id"]), ("tool_result", "toolu_sample_01"))
        self.assertEqual(json.loads(block["content"]), {"order_id": "A-1042", "status": "shipped"})

    def test_every_call_gets_a_result_in_order(self):
        message = tool_results(load("sample_two_calls.json"), FUNCTIONS)
        self.assertEqual([b["tool_use_id"] for b in message["content"]], ["toolu_sample_02", "toolu_sample_03"])
        self.assertEqual(json.loads(message["content"][1]["content"])["status"], "packing")

    def test_a_string_result_is_sent_as_it_is(self):
        message = tool_results(calls(("echo", {"text": "hi"})), {"echo": lambda text: text})
        self.assertEqual(message["content"][0]["content"], "hi")

    def test_the_function_gets_the_input_as_keyword_arguments(self):
        seen = {}

        def add(a, b):
            seen.update(a=a, b=b)
            return a + b
        message = tool_results(calls(("add", {"b": 2, "a": 40})), {"add": add})
        self.assertEqual(seen, {"a": 40, "b": 2})
        self.assertEqual(message["content"][0]["content"], "42")


class RunToolLoop(unittest.TestCase):
    TOOLS = [{"name": "lookup_order", "description": "Look up an order by its number.",
              "input_schema": {"type": "object", "properties": LOOKUP, "required": ["order_id"]}}]

    def test_no_tool_needed(self):
        ask = Recorder(final("Hello!"))
        text, messages = run_tool_loop(ask, "Hi", self.TOOLS, FUNCTIONS)
        self.assertEqual(text, "Hello!")
        self.assertEqual([m["role"] for m in messages], ["user", "assistant"])

    def test_one_round_of_the_tool_exchange(self):
        ask = Recorder(load("sample_tool_call.json"), load("sample_final_answer.json"))
        text, messages = run_tool_loop(ask, "Where is order A-1042?", self.TOOLS, FUNCTIONS)
        self.assertTrue(text.startswith("Order A-1042 has shipped."))
        second = ask.requests[1]
        self.assertEqual([m["role"] for m in second], ["user", "assistant", "user"])
        self.assertEqual(second[0], {"role": "user", "content": "Where is order A-1042?"})
        self.assertEqual(second[1]["content"], load("sample_tool_call.json")["content"])
        self.assertEqual(second[2]["content"][0]["type"], "tool_result")
        self.assertEqual(second[2]["content"][0]["tool_use_id"], "toolu_sample_01")
        self.assertEqual(len(messages), 4)

    def test_two_rounds(self):
        ask = Recorder(calls(("lookup_order", {"order_id": "A-1042"}), prefix="a"),
                       calls(("lookup_order", {"order_id": "B-7"}), prefix="b"), final("Both found."))
        text, messages = run_tool_loop(ask, "Check A-1042, then B-7.", self.TOOLS, FUNCTIONS)
        self.assertEqual(text, "Both found.")
        self.assertEqual(len(ask.requests), 3)
        self.assertEqual(len(messages), 6)

    def test_the_loop_stops_after_max_rounds(self):
        ask = Recorder(*[calls(("lookup_order", {"order_id": "A-1042"}))] * 10)
        with self.assertRaises(RuntimeError):
            run_tool_loop(ask, "Loop forever", self.TOOLS, FUNCTIONS, max_rounds=3)
        self.assertEqual(len(ask.requests), 4)

    def test_another_stop_reason_ends_the_loop(self):
        cut = {"content": [{"type": "text", "text": "Order A-1042 has"}], "stop_reason": "max_tokens"}
        text, _ = run_tool_loop(Recorder(cut), "Where is A-1042?", self.TOOLS, FUNCTIONS)
        self.assertEqual(text, "Order A-1042 has")


if __name__ == "__main__":
    unittest.main()
