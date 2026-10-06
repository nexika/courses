"""Estimate what Claude calls cost, from token counts and a price table.

Prices are in US dollars per million tokens (MTok), one price for input and one for output:
    {"input": 2, "output": 10}
Usage is what a response reports in its `usage` field:
    {"input_tokens": 2000, "output_tokens": 500}
"""
import json
from pathlib import Path

MILLION = 1_000_000
PRICES_FILE = Path(__file__).with_name("prices.json")


def _tokens(usage, field):
    value = usage.get(field, 0)
    if not isinstance(value, int) or isinstance(value, bool) or value < 0:
        raise ValueError(f"{field} must be a whole number of tokens, 0 or more")
    return value


def call_cost(usage, price):
    """The cost in dollars of one call: input and output tokens, each at its own price."""
    input_tokens = _tokens(usage, "input_tokens")
    output_tokens = _tokens(usage, "output_tokens")
    return (input_tokens * price["input"] + output_tokens * price["output"]) / MILLION


def workload_cost(usage, price, calls):
    """The cost in dollars of `calls` calls that each use about `usage`."""
    if not isinstance(calls, int) or isinstance(calls, bool) or calls < 0:
        raise ValueError("calls must be a whole number, 0 or more")
    return call_cost(usage, price) * calls


def total_usage(responses):
    """Add up the usage of recorded responses: {"input_tokens": ..., "output_tokens": ...}."""
    total = {"input_tokens": 0, "output_tokens": 0}
    for response in responses:
        usage = response["usage"]
        for field in total:
            total[field] += _tokens(usage, field)
    return total


def leaves_room(input_tokens, max_tokens, context_window):
    """True when the input plus the longest answer you allow (max_tokens) fits in the context window."""
    for value in (input_tokens, max_tokens, context_window):
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("token counts must be whole numbers, 0 or more")
    return input_tokens + max_tokens <= context_window


def rough_tokens(text, chars_per_token=3.5):
    """A rough guess for English text only. Count with the API when the number matters."""
    return round(len(text) / chars_per_token)


def load_prices(path=PRICES_FILE):
    """The price table shipped with the exercise, without its note."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {model: price for model, price in data.items() if not model.startswith("_")}


if __name__ == "__main__":
    prices = load_prices()
    usage = {"input_tokens": 2000, "output_tokens": 500}
    for model, price in prices.items():
        print(f"{model}: one call ${call_cost(usage, price):.4f}, "
              f"10,000 calls ${workload_cost(usage, price, 10_000):.2f}")
