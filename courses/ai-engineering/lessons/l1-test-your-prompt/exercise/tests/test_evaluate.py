import unittest

from evaluate import exact_match, normalized_match, run_eval

CASES = [
    {"input": "a", "expected": "positive"},
    {"input": "b", "expected": "negative"},
    {"input": "c", "expected": "mixed"},
    {"input": "d", "expected": "positive"},
]


def model_from(answers):
    """A deterministic stand-in model that also records what it was asked."""
    asked = []

    def model(text):
        asked.append(text)
        return answers[text]

    return model, asked


class TestGraders(unittest.TestCase):
    def test_exact_match_is_strict(self):
        self.assertTrue(exact_match("mixed", "mixed"))
        self.assertFalse(exact_match("Mixed", "mixed"))
        self.assertFalse(exact_match("mixed.", "mixed"))
        self.assertFalse(exact_match(" mixed", "mixed"))

    def test_normalized_match_ignores_case_spaces_and_final_punctuation(self):
        self.assertTrue(normalized_match("Mixed", "mixed"))
        self.assertTrue(normalized_match(" POSITIVE \n", "positive"))
        self.assertTrue(normalized_match("negative.", "negative"))
        self.assertTrue(normalized_match("Positive!", "positive"))
        self.assertTrue(normalized_match("very   good", "Very good"))

    def test_normalized_match_still_rejects_other_answers(self):
        self.assertFalse(normalized_match("not positive", "positive"))
        self.assertFalse(normalized_match("The sentiment is mixed.", "mixed"))
        self.assertFalse(normalized_match("negative", "positive"))
        self.assertFalse(normalized_match("", "positive"))


class TestRunEval(unittest.TestCase):
    def test_pass_rate_and_failing_cases_in_order(self):
        model, _ = model_from({"a": "positive", "b": "positive", "c": "mixed", "d": "Positive"})
        rate, failures = run_eval(CASES, model, exact_match)
        self.assertAlmostEqual(rate, 0.5)
        self.assertEqual([f["input"] for f in failures], ["b", "d"])
        self.assertEqual(failures[0]["expected"], "negative")
        self.assertEqual(failures[0]["output"], "positive")
        self.assertEqual(failures[1]["output"], "Positive")
        self.assertIsNone(failures[0]["error"])

    def test_the_grader_decides(self):
        model, _ = model_from({"a": "positive", "b": "positive", "c": "mixed", "d": "Positive"})
        rate, failures = run_eval(CASES, model, normalized_match)
        self.assertAlmostEqual(rate, 0.75)
        self.assertEqual([f["input"] for f in failures], ["b"])
        rate, failures = run_eval(CASES, model, lambda output, expected: True)
        self.assertEqual((rate, failures), (1.0, []))

    def test_grader_gets_the_output_then_the_expected_answer(self):
        seen = []

        def grader(output, expected):
            seen.append((output, expected))
            return True

        model, _ = model_from({"a": "w", "b": "x", "c": "y", "d": "z"})
        run_eval(CASES, model, grader)
        self.assertEqual(seen, [("w", "positive"), ("x", "negative"), ("y", "mixed"), ("z", "positive")])

    def test_the_model_is_asked_once_per_case_in_order(self):
        model, asked = model_from({"a": "positive", "b": "negative", "c": "mixed", "d": "positive"})
        rate, failures = run_eval(CASES, model, exact_match)
        self.assertEqual(asked, ["a", "b", "c", "d"])
        self.assertEqual((rate, failures), (1.0, []))

    def test_no_cases_is_an_error_not_a_score(self):
        model, _ = model_from({})
        with self.assertRaises(ValueError):
            run_eval([], model, exact_match)

    def test_a_model_error_fails_that_case_and_the_run_goes_on(self):
        asked = []

        def flaky(text):
            asked.append(text)
            if text == "b":
                raise TimeoutError("no answer in time")
            return {"a": "positive", "c": "mixed", "d": "positive"}[text]

        rate, failures = run_eval(CASES, flaky, exact_match)
        self.assertEqual(asked, ["a", "b", "c", "d"])
        self.assertAlmostEqual(rate, 0.75)
        self.assertEqual(len(failures), 1)
        self.assertEqual(failures[0]["input"], "b")
        self.assertIsNone(failures[0]["output"])
        self.assertIn("no answer in time", failures[0]["error"])


if __name__ == "__main__":
    unittest.main()
