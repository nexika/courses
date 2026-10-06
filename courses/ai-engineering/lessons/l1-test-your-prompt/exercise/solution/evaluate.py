"""Test a prompt like code: cases with expected answers, a grader, a pass rate.

Run this file (python3 evaluate.py) to evaluate the stand-in model on CASES. To test a real prompt,
write a function that sends the prompt to Claude and returns the text of the answer, and pass it to
run_eval instead of stand_in_model.
"""

CASES = [
    {"input": "Arrived on time and works perfectly.", "expected": "positive"},
    {"input": "Great screen, terrible battery.", "expected": "mixed"},
    {"input": "Oh great, it stopped working again.", "expected": "negative"},
    {"input": "Not bad at all.", "expected": "positive"},
]

CANNED = {
    "Arrived on time and works perfectly.": "positive",
    "Great screen, terrible battery.": "Mixed.",
    "Oh great, it stopped working again.": "positive",
    "Not bad at all.": " POSITIVE ",
}


def stand_in_model(review):
    """Plays the model: the same made-up answer for the same review, every time."""
    return CANNED[review]


def exact_match(output, expected):
    """True only when the answer is exactly the expected string."""
    return output == expected


def normalized_match(output, expected):
    """True when the two are equal once case, extra spaces and final . or ! are ignored."""

    def clean(text):
        return " ".join(text.split()).lower().rstrip(".!").strip()

    return clean(output) == clean(expected)


def run_eval(cases, model, grader):
    """Run every case through the model and grade it.

    Returns (pass_rate, failures): pass_rate is passed / total, from 0.0 to 1.0; failures lists, in
    case order, a dict with "input", "expected", "output" and "error" for each case that did not pass.
    A model that raises counts as a failure (output None, error the message) and the run goes on.
    """
    if not cases:
        raise ValueError("no cases: a pass rate over zero cases means nothing")
    failures = []
    for case in cases:
        try:
            output, error = model(case["input"]), None
        except Exception as exc:  # one failing call must not stop the whole eval
            output, error = None, f"{type(exc).__name__}: {exc}"
        if error is not None or not grader(output, case["expected"]):
            failures.append({"input": case["input"], "expected": case["expected"], "output": output, "error": error})
    return (len(cases) - len(failures)) / len(cases), failures


if __name__ == "__main__":
    for name, grader in [("exact match", exact_match), ("normalized match", normalized_match)]:
        rate, failures = run_eval(CASES, stand_in_model, grader)
        print(f"{name}: pass rate {rate:.0%}")
        for failure in failures:
            print(f"  FAIL {failure['input']!r}: expected {failure['expected']!r}, got {failure['output']!r}")
