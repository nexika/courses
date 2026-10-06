"""Test a prompt on ten cases with two graders. No network: the model is a stand-in."""

PROMPT = (
    "Classify the sentiment of this product review as positive, negative or mixed. "
    "Answer with one word.\n\nReview: {review}"
)

CASES = [
    {"input": "Arrived on time and works perfectly.", "expected": "positive"},
    {"input": "Broke after two days.", "expected": "negative"},
    {"input": "Great screen, terrible battery.", "expected": "mixed"},
    {"input": "Exactly what I ordered.", "expected": "positive"},
    {"input": "The worst purchase I have made.", "expected": "negative"},
    {"input": "Fast delivery, but the box was damaged.", "expected": "mixed"},
    {"input": "I love it.", "expected": "positive"},
    {"input": "Oh great, it stopped working again.", "expected": "negative"},
    {"input": "Not bad at all.", "expected": "positive"},
    {"input": "It does the job, but I expected more.", "expected": "mixed"},
]

# Made-up answers in the style of a model's replies, so this example gives the same result on every run.
CANNED = {
    "Arrived on time and works perfectly.": "positive",
    "Broke after two days.": "negative",
    "Great screen, terrible battery.": "mixed",
    "Exactly what I ordered.": "Positive",
    "The worst purchase I have made.": "negative.",
    "Fast delivery, but the box was damaged.": "Mixed\n",
    "I love it.": "positive",
    "Oh great, it stopped working again.": "positive",
    "Not bad at all.": " POSITIVE ",
    "It does the job, but I expected more.": "The sentiment is mixed.",
}


def stand_in_model(review):
    """Plays the model. A real one would receive PROMPT.format(review=review)."""
    return CANNED[review]


def exact_match(output, expected):
    return output == expected


def normalized_match(output, expected):
    def clean(text):
        return " ".join(text.split()).lower().rstrip(".")

    return clean(output) == clean(expected)


def run_eval(cases, model, grader):
    failures = []
    for case in cases:
        output = model(case["input"])
        if not grader(output, case["expected"]):
            failures.append({**case, "output": output})
    passed = len(cases) - len(failures)
    return passed / len(cases), failures


if __name__ == "__main__":
    for name, grader in [("exact match", exact_match), ("normalized match", normalized_match)]:
        rate, failures = run_eval(CASES, stand_in_model, grader)
        print(f"{name}: {len(CASES) - len(failures)} of {len(CASES)} passed, pass rate {rate:.0%}")
        for failure in failures:
            print(f"  FAIL {failure['input']!r}: expected {failure['expected']!r}, got {failure['output']!r}")
