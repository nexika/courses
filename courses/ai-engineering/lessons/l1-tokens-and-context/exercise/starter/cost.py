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
    # Prices are per million tokens. _tokens(usage, "input_tokens") reads a count and raises
    # ValueError when it is negative or not a whole number.
    raise NotImplementedError


def workload_cost(usage, price, calls):
    """The cost in dollars of `calls` calls that each use about `usage`."""
    # One call's cost, times the number of calls. Raise ValueError if calls is negative.
    raise NotImplementedError


def total_usage(responses):
    """Add up the usage of recorded responses: {"input_tokens": ..., "output_tokens": ...}."""
    # Each response looks like {"usage": {"input_tokens": 12, "output_tokens": 6}}.
    raise NotImplementedError


def leaves_room(input_tokens, max_tokens, context_window):
    """True when the input plus the longest answer you allow (max_tokens) fits in the context window."""
    # Input and output share the context window. Raise ValueError for a negative count.
    raise NotImplementedError


def rough_tokens(text, chars_per_token=3.5):
    """A rough guess for English text only. Count with the API when the number matters."""
    # About chars_per_token characters per token: divide and round to a whole number.
    raise NotImplementedError


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
