import unittest

from cost import call_cost, leaves_room, rough_tokens, total_usage, workload_cost

# A price table made up for the tests, in dollars per million tokens.
PRICES = {"small": {"input": 1, "output": 5}, "large": {"input": 3, "output": 15}}


class CallCost(unittest.TestCase):
    def test_input_and_output_each_use_their_own_price(self):
        usage = {"input_tokens": 1_000_000, "output_tokens": 0}
        self.assertAlmostEqual(call_cost(usage, PRICES["large"]), 3.0)
        usage = {"input_tokens": 0, "output_tokens": 1_000_000}
        self.assertAlmostEqual(call_cost(usage, PRICES["large"]), 15.0)

    def test_a_small_call(self):
        usage = {"input_tokens": 2000, "output_tokens": 500}
        self.assertAlmostEqual(call_cost(usage, PRICES["small"]), 0.0045)
        self.assertAlmostEqual(call_cost(usage, PRICES["large"]), 0.0135)

    def test_no_tokens_costs_nothing(self):
        self.assertEqual(call_cost({"input_tokens": 0, "output_tokens": 0}, PRICES["small"]), 0)

    def test_negative_counts_are_refused(self):
        with self.assertRaises(ValueError):
            call_cost({"input_tokens": -1, "output_tokens": 10}, PRICES["small"])
        with self.assertRaises(ValueError):
            call_cost({"input_tokens": 10, "output_tokens": -5}, PRICES["small"])


class WorkloadCost(unittest.TestCase):
    def test_many_calls(self):
        usage = {"input_tokens": 2000, "output_tokens": 500}
        self.assertAlmostEqual(workload_cost(usage, PRICES["small"], 10_000), 45.0)
        self.assertAlmostEqual(workload_cost(usage, PRICES["large"], 300), 4.05)

    def test_zero_calls_cost_nothing(self):
        self.assertEqual(workload_cost({"input_tokens": 50, "output_tokens": 50}, PRICES["large"], 0), 0)

    def test_negative_calls_are_refused(self):
        with self.assertRaises(ValueError):
            workload_cost({"input_tokens": 50, "output_tokens": 50}, PRICES["large"], -1)


class TotalUsage(unittest.TestCase):
    def test_adds_up_recorded_responses(self):
        responses = [
            {"usage": {"input_tokens": 12, "output_tokens": 6}},
            {"usage": {"input_tokens": 30, "output_tokens": 309}},
            {"usage": {"input_tokens": 42, "output_tokens": 1}},
        ]
        self.assertEqual(total_usage(responses), {"input_tokens": 84, "output_tokens": 316})

    def test_no_responses(self):
        self.assertEqual(total_usage([]), {"input_tokens": 0, "output_tokens": 0})

    def test_the_total_prices_like_the_calls(self):
        responses = [{"usage": {"input_tokens": 1000, "output_tokens": 200}},
                     {"usage": {"input_tokens": 3000, "output_tokens": 800}}]
        each = sum(call_cost(r["usage"], PRICES["large"]) for r in responses)
        self.assertAlmostEqual(call_cost(total_usage(responses), PRICES["large"]), each)


class LeavesRoom(unittest.TestCase):
    def test_input_and_output_share_the_window(self):
        self.assertTrue(leaves_room(150_000, 50_000, 200_000))
        self.assertFalse(leaves_room(150_001, 50_000, 200_000))
        self.assertFalse(leaves_room(10, 300_000, 200_000))

    def test_negative_counts_are_refused(self):
        with self.assertRaises(ValueError):
            leaves_room(-1, 10, 200_000)
        with self.assertRaises(ValueError):
            leaves_room(10, -1, 200_000)
        with self.assertRaises(ValueError):
            leaves_room(10, 10, -200_000)


class RoughTokens(unittest.TestCase):
    def test_about_three_and_a_half_characters_per_token(self):
        self.assertEqual(rough_tokens("x" * 7000), 2000)
        self.assertEqual(rough_tokens(""), 0)

    def test_the_ratio_can_change(self):
        self.assertEqual(rough_tokens("x" * 300, chars_per_token=3), 100)


if __name__ == "__main__":
    unittest.main()
