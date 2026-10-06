import copy
import json
import unittest
from pathlib import Path

from first_call import build_request, join_stream, read_reply

HERE = Path(__file__).resolve().parent


def start(input_tokens):
    return {"type": "message_start",
            "message": {"content": [], "usage": {"input_tokens": input_tokens, "output_tokens": 1}}}


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


class BuildRequest(unittest.TestCase):
    def test_a_single_question(self):
        body = build_request("claude-opus-5-5", 300, [("user", "What is a token?")])
        self.assertEqual(body, {"model": "claude-opus-5-5", "max_tokens": 300,
                                "messages": [{"role": "user", "content": "What is a token?"}]})

    def test_the_system_prompt_is_a_top_level_field(self):
        body = build_request("m", 100, [("user", "Hi")], system="Answer in French.")
        self.assertEqual(body["system"], "Answer in French.")
        self.assertTrue(all(m["role"] != "system" for m in body["messages"]))

    def test_no_system_field_without_a_system_prompt(self):
        self.assertNotIn("system", build_request("m", 100, [("user", "Hi")]))
        self.assertNotIn("system", build_request("m", 100, [("user", "Hi")], system=""))

    def test_a_conversation_keeps_every_turn_in_order(self):
        turns = [("user", "What is a token?"), ("assistant", "A small piece of text."),
                 ("user", "And a context window?")]
        body = build_request("m", 200, turns)
        self.assertEqual([(m["role"], m["content"]) for m in body["messages"]], turns)

    def test_the_body_can_be_sent_as_json(self):
        body = build_request("m", 50, [("user", "Hi")], system="Be brief.")
        self.assertEqual(json.loads(json.dumps(body)), body)

    def test_bad_requests_are_refused(self):
        with self.assertRaises(ValueError):
            build_request("m", 0, [("user", "Hi")])
        with self.assertRaises(ValueError):
            build_request("m", "300", [("user", "Hi")])
        with self.assertRaises(ValueError):
            build_request("m", True, [("user", "Hi")])
        with self.assertRaises(ValueError):
            build_request("m", 100, [])
        with self.assertRaises(ValueError):
            build_request("m", 100, [("system", "Be brief."), ("user", "Hi")])
        with self.assertRaises(ValueError):
            build_request("m", 100, [("user", "Hi"), ("assistant", "Hello")])


class ReadReply(unittest.TestCase):
    def test_a_finished_reply(self):
        reply = read_reply(load("sample_reply.json"))
        self.assertTrue(reply["text"].startswith("A token is a small piece of text"))
        self.assertEqual(reply["stop_reason"], "end_turn")
        self.assertEqual((reply["input_tokens"], reply["output_tokens"]), (41, 28))
        self.assertFalse(reply["cut_off"])

    def test_a_reply_cut_off_by_max_tokens(self):
        reply = read_reply(load("sample_cut_off.json"))
        self.assertEqual(reply["stop_reason"], "max_tokens")
        self.assertTrue(reply["cut_off"])
        self.assertEqual(reply["output_tokens"], 16)
        self.assertTrue(reply["text"].endswith("that a model can"))

    def test_only_text_blocks_make_the_answer(self):
        response = {"content": [{"type": "thinking", "thinking": "The user wants a short answer."},
                                {"type": "text", "text": "Hello"}, {"type": "text", "text": ", world."}],
                    "stop_reason": "end_turn", "usage": {"input_tokens": 9, "output_tokens": 7}}
        self.assertEqual(read_reply(response)["text"], "Hello, world.")

    def test_a_cut_off_reply_with_several_text_blocks(self):
        response = {"content": [{"type": "text", "text": "First part. "}, {"type": "text", "text": "Second, cut"}],
                    "stop_reason": "max_tokens", "usage": {"input_tokens": 12, "output_tokens": 8}}
        reply = read_reply(response)
        self.assertEqual(reply["text"], "First part. Second, cut")
        self.assertTrue(reply["cut_off"])
        self.assertEqual((reply["input_tokens"], reply["output_tokens"]), (12, 8))

    def test_the_response_is_not_changed(self):
        response = load("sample_reply.json")
        before = copy.deepcopy(response)
        read_reply(response)
        self.assertEqual(response, before)


class JoinStream(unittest.TestCase):
    def test_a_stream_gives_the_same_reply_as_the_whole_message(self):
        self.assertEqual(join_stream(load("sample_stream.json")), read_reply(load("sample_reply.json")))

    def test_output_tokens_are_running_totals_not_added_up(self):
        events = [start(5),
                  {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Hi"}},
                  {"type": "message_delta", "delta": {"stop_reason": None}, "usage": {"output_tokens": 10}},
                  {"type": "message_delta", "delta": {"stop_reason": "max_tokens"}, "usage": {"output_tokens": 12}},
                  {"type": "message_stop"}]
        reply = join_stream(events)
        self.assertEqual((reply["input_tokens"], reply["output_tokens"]), (5, 12))
        self.assertEqual(reply["stop_reason"], "max_tokens")
        self.assertTrue(reply["cut_off"])

    def test_pings_and_unknown_events_are_ignored(self):
        events = [start(3),
                  {"type": "ping"},
                  {"type": "some_future_event", "data": "x"},
                  {"type": "content_block_delta", "index": 0, "delta": {"type": "text_delta", "text": "Yes."}},
                  {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 2}},
                  {"type": "message_stop"}]
        self.assertEqual(join_stream(events)["text"], "Yes.")

    def test_thinking_before_the_text_is_not_part_of_the_answer(self):
        events = [start(4),
                  {"type": "content_block_start", "index": 0, "content_block": {"type": "thinking", "thinking": ""}},
                  {"type": "content_block_delta", "index": 0,
                   "delta": {"type": "thinking_delta", "thinking": "A short answer will do."}},
                  {"type": "content_block_stop", "index": 0},
                  {"type": "content_block_start", "index": 1, "content_block": {"type": "text", "text": ""}},
                  {"type": "content_block_delta", "index": 1, "delta": {"type": "text_delta", "text": "Hello."}},
                  {"type": "content_block_stop", "index": 1},
                  {"type": "message_delta", "delta": {"stop_reason": "end_turn"}, "usage": {"output_tokens": 9}},
                  {"type": "message_stop"}]
        reply = join_stream(events)
        self.assertEqual(reply["text"], "Hello.")
        self.assertEqual((reply["stop_reason"], reply["output_tokens"]), ("end_turn", 9))


if __name__ == "__main__":
    unittest.main()
