# Tokens, the context window and cost

## What you will be able to do

- Explain what a token is, and why you count tokens rather than words.
- Say what fills the context window of a request, and check that a request leaves room for its answer.
- Read the token counts a response reports, and estimate what one call and a whole workload will cost.

## The idea

A model does not read words or letters. It reads **tokens**. Anthropic's glossary describes them as
"the smallest individual units of a language model", which "can correspond to words, subwords,
characters, or even bytes"[^tokens]. A subword is a piece of a word; a byte is one of the small
units a computer stores text in. Using pieces smaller than words is what lets a model handle
uncommon or never-before-seen words[^rare]. For example, a common word may be a single token, while a
rare word or a name may be cut into several.

How much text fits in one token depends on the text. For Claude, a token is about 3.5 English
characters, and the number varies with the language[^chars]. If you write in Arabic or French, do not
assume the English ratio: measure your own text.

The count also depends on the model. The tokenizer, the part that cuts text into tokens, can change
between models: Claude 4.7 and later models use a newer one, and the same text gives about 30 percent
more tokens than on earlier models[^tokenizer]. A token count is always a count for one model.

**The context window** is "all the text a language model can reference when generating a response,
including the response itself"[^window]. Think of it as the model's working memory for one request.
It is not what the model learned in training: it is what you send now, plus what it writes back.

Everything in the request counts toward it: the system prompt (the instructions you give the model
before the conversation), every message, and any tool definitions (the descriptions of the
functions your program lets the model ask to call)[^everything]. The answer Claude writes counts
too[^output]. Input and output share the same window.

The window has a size, in tokens. Many current models, including Claude Opus 5.5 and Claude Sonnet
5.5, have a context window of one million tokens (written 1M)[^sizes-1m]. Others, such as Claude
Sonnet 4.5, have 200K tokens[^sizes-200k]. If the input alone is larger than the window, the API
refuses the request with a 400 error[^too-long]: you get an error response instead of an answer, and
the request is not run. A bigger window does not mean better answers either: as the token count
grows, accuracy and recall degrade, which Anthropic calls context rot[^rot]. Here "recall" means that
the model finds and uses what is in its context less reliably.

**Input and output tokens.** Input tokens are everything you send. Output tokens are what Claude
writes. You cannot know in advance how long the answer will be, but you can cap it: `max_tokens` is
"the maximum number of tokens to generate before stopping", and the model may stop earlier[^max-tokens].
Each model also has its own ceiling for `max_tokens`: the 1M-token models can generate up to 128k
output tokens in one request[^max-out].

**Usage.** You do not have to guess what a call used. Every response reports it in its `usage`
field[^usage]: `input_tokens` is the number of input tokens used[^usage-in], and `output_tokens` the
number of output tokens used[^usage-out]. In a response, it looks like this:

```json
"usage": {"input_tokens": 12, "output_tokens": 6}
```

This is the whole input only when you do not use prompt caching, a way to reuse the start of a
request across calls, which this lesson does not cover. With caching, the input is split across
`input_tokens`, `cache_read_input_tokens` and `cache_creation_input_tokens`, and all three count
toward the window[^caching]. The cost formula in this lesson ignores caching.

**Cost.** Anthropic prices input and output tokens separately, in US dollars[^usd], per million
tokens, written MTok[^mtok]. So one call costs:

```text
cost = input_tokens × input price / 1,000,000  +  output_tokens × output price / 1,000,000
```

Prices change. On the day this lesson was checked, the pricing page listed these prices, in dollars
per MTok:

| Model | Input | Output |
|---|---|---|
| Claude Opus 5.5[^price-opus] | 4 | 20 |
| Claude Sonnet 5.5[^price-sonnet] | 2 | 10 |
| Claude Haiku 4.5[^price-haiku] | 1 | 5 |

On Claude 4.6 and later models, the price of a token does not grow with the size of the request:
"A 900k-token request is billed at the same per-token rate as a 9k-token request"[^flat]. Claude
Haiku 4.5, in the table above, is not one of those models: the page makes no such promise for it.

A worked example. On Claude Sonnet 5.5, a call that sends 2,000 input tokens and gets 500 output tokens back costs $0.009.
The 500 output tokens alone cost $0.005: a fifth of the tokens, but more than half of the cost.
A workload is many calls: 10,000 such calls a day cost $90 a day.
The same calls on Claude Haiku 4.5 cost $45 a day.
This is how you compare models before you choose one: same token counts, different prices.

## Try it

### Count tokens before you send

The API can count the tokens of a request before you send it[^count]. You will set up an API key in
the next lessons; if you already have one, this counts the input tokens of a short request (it needs
`pip install anthropic`):

```python
import anthropic

client = anthropic.Anthropic()  # reads your key from the ANTHROPIC_API_KEY environment variable
count = client.messages.count_tokens(
    model="claude-sonnet-5-5",
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "How many tokens is this sentence?"}],
)
print(count.input_tokens)
```

The count is an estimate[^estimate], and it covers only the input: the output does not exist yet.
Counting is free, but it has its own rate limits, a cap on how many requests you may send per
minute[^count-free]. The exact numbers you pay for are the
ones in the `usage` field of the real response.

### Estimate the cost of a call

This runs with no key and no network. It takes the `usage` of a response and the price table, and
prints the cost of one call and of many calls:

```python
import json

# US dollars per million tokens (MTok), copied from Anthropic's pricing page.
# Prices change: read the page again before you rely on them.
PRICES = {
    "claude-opus-5-5": {"input": 4, "output": 20},
    "claude-sonnet-5-5": {"input": 2, "output": 10},
    "claude-haiku-4-5": {"input": 1, "output": 5},
}

# The usage part of a response, in the shape the API reports it (the numbers are an example).
response = json.loads('{"usage": {"input_tokens": 2000, "output_tokens": 500}}')
usage = response["usage"]


def call_cost(usage, price):
    """Dollars for one call: each kind of token at its own price, per million tokens."""
    return (usage["input_tokens"] * price["input"] + usage["output_tokens"] * price["output"]) / 1_000_000


for model, price in PRICES.items():
    one = call_cost(usage, price)
    print(f"{model}: one call ${one:.4f}, 10,000 calls ${one * 10_000:.2f}")

# A rough guess for English text only: about 3.5 characters per token.
text = "x" * 7000  # stands in for 7,000 characters of English
print("rough guess:", round(len(text) / 3.5), "tokens")
```

Save it as `estimate.py` and run `python3 estimate.py`:

```text
claude-opus-5-5: one call $0.0180, 10,000 calls $180.00
claude-sonnet-5-5: one call $0.0090, 10,000 calls $90.00
claude-haiku-4-5: one call $0.0045, 10,000 calls $45.00
rough guess: 2000 tokens
```

The last line is a rough guess: 7,000 characters of English text come to about 2,000 tokens.
Use it for a sense of scale, never to fill a budget to the last token. Change the usage numbers
and see how much more the output tokens move the cost than the input tokens.

## Common mistakes

- **"A token is a word."** A token can be a word, a piece of a word, a character or a byte[^tokens].
  Count tokens; do not count words.
- **"The context window is my prompt."** The answer is in the window too[^output]. A request whose
  input nearly fills the window leaves little room for the answer.
- **"Input and output cost the same."** In the price table above, an output token costs five times
  as much as an input token[^price-opus][^price-sonnet][^price-haiku]. Long answers are often the expensive part.
- **"A count from one model is valid for another."** Tokenizers change between models, and the same
  text can give about 30 percent more tokens on newer ones[^tokenizer]. Count again for the model you
  will use.
- **"`count_tokens` tells me the bill."** It is an estimate of the input[^estimate]. The `usage` field
  of the response is what was really used[^usage].
- **"These prices are fixed."** They change, so read the pricing page again before you plan a budget.
  Options change them too: for example, the Batch API (requests sent in bulk and processed later,
  not right away) gives a 50% discount on input and output tokens[^batch]. Later lessons come back to cost.

## Your exercise

Open `exercise/starter/cost.py` and write five small functions. Prices are dollars per million
tokens, like `{"input": 2, "output": 10}`; usage is the `usage` of a response, like
`{"input_tokens": 2000, "output_tokens": 500}`.

- `call_cost(usage, price)`: the cost of one call, in dollars.
- `workload_cost(usage, price, calls)`: the cost of `calls` calls with that usage.
- `total_usage(responses)`: add up the `usage` of a list of recorded responses.
- `leaves_room(input_tokens, max_tokens, context_window)`: `True` when the input plus the longest
  answer you allow fits in the window.
- `rough_tokens(text, chars_per_token=3.5)`: the rough guess from "Try it", rounded to a whole number.

Refuse a negative count with a `ValueError`. The file `prices.json` next to it holds the price table
from this lesson; `python3 cost.py` uses it once your functions work.

Run the tests from the starter folder:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

They fail until your functions are right. A solution is in `exercise/solution/`; try on your own first.

## Check yourself

Answer the questions in `quiz.json`. If they are hard, read "The idea" again, and redo the worked
example by hand: input and output tokens, each at its own price per million.

[^tokens]: Anthropic, Glossary.
[^rare]: Anthropic, Glossary.
[^chars]: Anthropic, Glossary.
[^tokenizer]: Anthropic, Token counting.
[^window]: Anthropic, Context windows.
[^everything]: Anthropic, Context windows.
[^output]: Anthropic, Context windows.
[^sizes-1m]: Anthropic, Context windows.
[^sizes-200k]: Anthropic, Context windows.
[^too-long]: Anthropic, Context windows.
[^rot]: Anthropic, Context windows.
[^max-tokens]: Anthropic, Create a Message (API reference).
[^max-out]: Anthropic, Context windows.
[^usage]: Anthropic, Context windows.
[^usage-in]: Anthropic Python SDK, types/usage.py.
[^usage-out]: Anthropic Python SDK, types/usage.py.
[^caching]: Anthropic, Context windows.
[^usd]: Anthropic, Pricing.
[^mtok]: Anthropic, Pricing.
[^price-opus]: Anthropic, Pricing.
[^price-sonnet]: Anthropic, Pricing.
[^price-haiku]: Anthropic, Pricing.
[^flat]: Anthropic, Pricing.
[^count]: Anthropic, Token counting.
[^estimate]: Anthropic, Token counting.
[^count-free]: Anthropic, Token counting.
[^batch]: Anthropic, Pricing.
