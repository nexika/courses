# Test your prompt

## What you will be able to do

- Write a small set of test cases for a prompt, each with an input and the answer you expect.
- Grade the model's answers with code: an exact match first, then a more tolerant grader.
- Run every case, report the pass rate, and read the failing cases to decide what to fix.

## The idea

In the last lesson you wrote a clear prompt. How do you know it works? Most people try it once, see a
good answer and move on. That one answer proves very little. It tells you about one input, on one run.
Your users will send inputs you never tried. And the same prompt can answer differently on another run:
the API reference says that even with the temperature at its lowest, the results will not be fully
deterministic[^nondet].

So treat a prompt like code, and test it. Anthropic's guide says that building an LLM application starts
with clearly defining your success criteria and then designing evaluations to measure performance against
them[^cycle]. Its prompt engineering overview expects you to have some ways to empirically test against
those criteria before you start improving a prompt[^before].

A test of a prompt is called an *evaluation*, or *eval*. A first eval has three parts:

- **Cases.** Inputs, each with the answer you expect (people also call it the *golden answer*). Choose
  them like your real traffic: the guide says to design evals that mirror your real-world task
  distribution[^taskspecific]. Include the hard inputs too, not only the easy ones.
- **A grader.** Code that compares the model's answer with the expected answer and says pass or fail. The
  guide recommends structuring questions so they allow automated grading[^automate]. It calls code-based
  grading the fastest and most reliable kind, but notes that it lacks nuance for complex judgments[^codegrade].
- **The pass rate.** The share of cases that pass: the cases that passed divided by all the cases.

Here is a small example. The prompt asks the model to label a product review as positive, negative or
mixed. One case is the review "Great screen, terrible battery." with the expected answer "mixed". If the
model answers "mixed", the case passes.

The simplest grader is an *exact match*: the answer must be the same string as the expected one. It is
strict. It fails "Mixed" and "mixed." although a person would accept both. A *tolerant* grader cleans both
strings before it compares them. The guide describes exact-match evals as checking whether the output
matches a predefined correct answer, typically after normalizing whitespace and case[^exact]. The tolerant
grader in this lesson also ignores a full stop at the end.

Tolerance has a limit. A grader that accepts any answer *containing* the word "positive" would also accept
"not positive". A grader that is too loose gives you a high pass rate that means nothing.

Many simple cases beat a few perfect ones: the guide says more questions with slightly lower signal
automated grading is better than fewer questions with high-quality human hand-graded evals[^volume].
Start small, and add a case each time you find a new failure.

## Try it

Save this as `try_eval.py` and run `python3 try_eval.py`. The model here is a *stand-in*: a function that
returns made-up answers in the style of a model's replies. It needs no network and no key, and it gives
the same result on every run, so you can see exactly what each grader does.

```python
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
```

It prints:

```text
exact match: 4 of 10 passed, pass rate 40%
  FAIL 'Exactly what I ordered.': expected 'positive', got 'Positive'
  FAIL 'The worst purchase I have made.': expected 'negative', got 'negative.'
  FAIL 'Fast delivery, but the box was damaged.': expected 'mixed', got 'Mixed\n'
  FAIL 'Oh great, it stopped working again.': expected 'negative', got 'positive'
  FAIL 'Not bad at all.': expected 'positive', got ' POSITIVE '
  FAIL 'It does the job, but I expected more.': expected 'mixed', got 'The sentiment is mixed.'
normalized match: 8 of 10 passed, pass rate 80%
  FAIL 'Oh great, it stopped working again.': expected 'negative', got 'positive'
  FAIL 'It does the job, but I expected more.': expected 'mixed', got 'The sentiment is mixed.'
```

### Read the results

With the exact-match grader, 4 of 10 cases pass: a pass rate of 40%. Most of those failures are not wrong
answers. "Positive" and "negative." have the right label in a slightly different form.

With the tolerant grader, 8 of 10 cases pass: a pass rate of 80%. The two failures left are real, and they
are different problems:

- "Oh great, it stopped working again." is sarcasm, and the model got the label wrong. Anthropic's own
  example eval marks sarcasm as an edge case[^sarcasm]. The fix belongs in the prompt, for example a
  sentence about sarcasm, and then you run the eval again.
- "The sentiment is mixed." has the right label, but the prompt asked for one word. Make the prompt
  stricter about the format before you make the grader looser.

Look at the first case alone: a perfect answer. If you had tried only that one, you would have seen
nothing wrong.

### Swap in a real model

The official Python SDK gives access to the Claude API from Python[^sdk]. If you have an API key, you can
replace the stand-in with a real call. The model name below is one of the API model IDs in Anthropic's models overview;
model names change, so check that list before you run it[^model].

```python
import anthropic

client = anthropic.Anthropic()  # reads your key from the ANTHROPIC_API_KEY environment variable


def ask_claude(review):
    message = client.messages.create(
        model="claude-opus-5-5",
        max_tokens=10,
        messages=[{"role": "user", "content": PROMPT.format(review=review)}],
    )
    return message.content[0].text


rate, failures = run_eval(CASES, ask_claude, normalized_match)
```

Run it more than once. With a real model the pass rate can change from run to run, which is one more
reason not to trust a single answer.

## Common mistakes

- **"It worked when I tried it."** One input, one run. Test a set of cases and look at the pass rate.
- **Only easy cases.** If every case is obvious, a high pass rate tells you nothing. Add the inputs that
  worry you: sarcasm, mixed feelings, very short or very long text.
- **Changing the expected answers until the tests pass.** The expected answer is what you need, decided
  before you see the output. Change it only when you find it was wrong.
- **A grader that is too strict or too loose.** Too strict, and format slips look like wrong answers. Too
  loose, and wrong answers pass. Read some passing cases too, not only the failing ones.
- **Reporting only the number.** The pass rate tells you how often; the failing cases tell you why.
- **Thinking exact match is enough for every task.** It suits short, clear-cut answers such as labels. For
  answers that need judgment, later lessons use a model as the grader: the guide calls LLM-based grading
  fast and flexible, scalable and suitable for complex judgment[^llmgrade].

## Your exercise

Open `exercise/starter/evaluate.py`. It has a few cases, a stand-in model, and three functions to write:

- `exact_match(output, expected)`: true only when the two strings are identical.
- `normalized_match(output, expected)`: true when they are equal once you ignore upper and lower case,
  extra spaces, and a final full stop or exclamation mark. "not positive" must still fail for "positive".
- `run_eval(cases, model, grader)`: ask the model about each case once, in order, grade each answer with
  `grader(output, expected)`, and return a pair: the pass rate (passed cases divided by all cases) and the
  list of failing cases. Each failing case is a dictionary with `input`, `expected`, `output` and `error`.

Two more rules, because real evals meet them:

- An empty list of cases raises `ValueError`. A pass rate over no cases means nothing.
- If the model raises an exception on one case, that case fails with `output` set to `None` and `error`
  holding the message, and the run goes on with the next case. A real API call can fail; one failure
  must not stop the whole eval.

Run the tests from the starter folder:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

They fail until your functions are written. When they pass, run `python3 evaluate.py` to see the pass
rate of each grader, then try your own cases or swap in `ask_claude`. A worked solution is in
`exercise/solution/`: open it after you have tried.

## Check yourself

Answer the quiz for this lesson. If it feels hard, read "The idea" again, then compare the two outputs in
"Try it" case by case.
