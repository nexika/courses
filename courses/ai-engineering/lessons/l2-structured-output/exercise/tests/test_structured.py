import copy
import json
import unittest
from pathlib import Path

from structured import ReplyError, ask_until_valid, parse_reply, validate

HERE = Path(__file__).resolve().parent
SCHEMA = json.loads((HERE / "ticket_schema.json").read_text(encoding="utf-8"))


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def reply(text, stop_reason="end_turn"):
    return {"content": [{"type": "text", "text": text}], "stop_reason": stop_reason,
            "usage": {"input_tokens": 10, "output_tokens": 10}}


GOOD = {"category": "bug", "priority": 2, "summary": "Crash on start."}


class Validate(unittest.TestCase):
    def test_a_valid_ticket_has_no_problems(self):
        self.assertEqual(validate(GOOD, SCHEMA), [])

    def test_a_missing_required_field(self):
        problems = validate({"category": "bug", "priority": 2}, SCHEMA)
        self.assertEqual(len(problems), 1)
        self.assertIn("summary", problems[0])

    def test_a_field_the_schema_does_not_allow(self):
        problems = validate({**GOOD, "reasoning": "I think it is a bug."}, SCHEMA)
        self.assertEqual(len(problems), 1)
        self.assertIn("reasoning", problems[0])

    def test_wrong_types(self):
        self.assertTrue(validate({**GOOD, "priority": "2"}, SCHEMA))
        self.assertTrue(validate({**GOOD, "priority": 2.5}, SCHEMA))
        self.assertTrue(validate({**GOOD, "summary": None}, SCHEMA))
        self.assertTrue(validate(["bug", 2, "Crash"], SCHEMA))

    def test_true_is_not_a_number(self):
        self.assertTrue(validate(True, {"type": "integer"}))
        self.assertTrue(validate(False, {"type": "number"}))
        self.assertEqual(validate(3, {"type": "number"}), [])
        self.assertEqual(validate(True, {"type": "boolean"}), [])

    def test_minimum_and_maximum(self):
        self.assertIn("priority", validate({**GOOD, "priority": 5}, SCHEMA)[0])
        self.assertTrue(validate({**GOOD, "priority": 0}, SCHEMA))
        self.assertEqual(validate({**GOOD, "priority": 3}, SCHEMA), [])

    def test_enum_ignores_case_but_not_other_words(self):
        self.assertEqual(validate({**GOOD, "category": "Bug"}, SCHEMA), [])
        self.assertTrue(validate({**GOOD, "category": "feature"}, SCHEMA))

    def test_every_problem_is_reported(self):
        problems = validate({"category": "feature", "priority": 9, "extra": 1}, SCHEMA)
        self.assertEqual(len(problems), 4)

    def test_arrays_check_each_item(self):
        schema = {"type": "array", "items": SCHEMA}
        self.assertEqual(validate([GOOD, GOOD], schema), [])
        problems = validate([GOOD, {**GOOD, "priority": 7}], schema)
        self.assertEqual(len(problems), 1)
        self.assertIn("[1]", problems[0])


class ParseReply(unittest.TestCase):
    def reason(self, response):
        with self.assertRaises(ReplyError) as caught:
            parse_reply(response, SCHEMA)
        return caught.exception.reason

    def test_a_good_reply(self):
        self.assertEqual(parse_reply(load("sample_ok.json"), SCHEMA),
                         {"category": "bug", "priority": 2, "summary": "The export button does nothing in Safari."})

    def test_enum_values_come_back_in_the_schema_spelling(self):
        self.assertEqual(parse_reply(load("sample_enum_case.json"), SCHEMA)["category"], "billing")

    def test_each_kind_of_bad_reply(self):
        self.assertEqual(self.reason(load("sample_out_of_range.json")), "invalid")
        self.assertEqual(self.reason(load("sample_cut_off.json")), "cut_off")
        self.assertEqual(self.reason(load("sample_refusal.json")), "refusal")
        self.assertEqual(self.reason(load("sample_not_json.json")), "not_json")

    def test_only_text_blocks_are_read(self):
        response = reply(json.dumps(GOOD))
        response["content"].insert(0, {"type": "thinking", "thinking": "{not json"})
        self.assertEqual(parse_reply(response, SCHEMA), GOOD)

    def test_the_response_is_not_changed(self):
        response = load("sample_enum_case.json")
        before = copy.deepcopy(response)
        parse_reply(response, SCHEMA)
        self.assertEqual(response, before)


class AskUntilValid(unittest.TestCase):
    def script(self, *responses):
        calls = []

        def ask(max_tokens):
            calls.append(max_tokens)
            return responses[len(calls) - 1]
        return ask, calls

    def test_a_good_first_reply_is_asked_once(self):
        ask, calls = self.script(reply(json.dumps(GOOD)))
        self.assertEqual(ask_until_valid(ask, SCHEMA), GOOD)
        self.assertEqual(calls, [1024])

    def test_an_invalid_reply_is_asked_again(self):
        ask, calls = self.script(reply('{"category": "bug"}'), reply("not json"), reply(json.dumps(GOOD)))
        self.assertEqual(ask_until_valid(ask, SCHEMA), GOOD)
        self.assertEqual(calls, [1024, 1024, 1024])

    def test_a_cut_off_reply_is_asked_again_with_more_tokens(self):
        ask, calls = self.script(reply('{"category": "bu', "max_tokens"), reply(json.dumps(GOOD)))
        self.assertEqual(ask_until_valid(ask, SCHEMA, max_tokens=100), GOOD)
        self.assertEqual(calls, [100, 200])

    def test_a_refusal_is_not_retried(self):
        ask, calls = self.script(load("sample_refusal.json"), reply(json.dumps(GOOD)))
        with self.assertRaises(ReplyError) as caught:
            ask_until_valid(ask, SCHEMA)
        self.assertEqual(caught.exception.reason, "refusal")
        self.assertEqual(len(calls), 1)

    def test_it_gives_up_after_the_last_attempt(self):
        ask, calls = self.script(*[reply('{"category": "feature"}')] * 5)
        with self.assertRaises(ReplyError) as caught:
            ask_until_valid(ask, SCHEMA, attempts=2)
        self.assertEqual(caught.exception.reason, "gave_up")
        self.assertEqual(len(calls), 2)


if __name__ == "__main__":
    unittest.main()
