# Your first API call

## What you will be able to do

- Call Claude from Python with the official SDK, and read the answer and how many tokens it used.
- Build a conversation: a system prompt, then user and assistant turns.
- Choose the model and `max_tokens` for a request, and handle a reply that stopped because it ran out of tokens.
- Read a streamed reply piece by piece as it arrives.

## The idea

An API (application programming interface) is a door one program opens for other programs. Claude's door
is the Messages API: your code sends a request over the internet, and a reply comes back.

Your calls use an API key: a secret string that identifies your account, so keep it private. The usual
place for it is an environment variable on your machine[^start-key]: a named value that your terminal
hands to the programs it starts, outside your code. The official Python SDK (software development kit: a
library you install) reads it from `ANTHROPIC_API_KEY` without you passing it in[^start-env]. The SDK gives
Python programs access to the Claude API[^sdk].

A request is a small JSON object. JSON is a text format for data that looks like a Python dict: names in
quotes, each followed by a colon and a value. These are the fields you will use first:

- `model`: which Claude model answers. If you are unsure, Anthropic's docs suggest starting with Claude
  Opus 5.5[^models-start], whose API name is `claude-opus-5-5`[^model-id]. Model names change, so check the
  models page before you pick one.
- `max_tokens`: "the maximum number of tokens to generate before stopping"[^max-tokens]. It is a ceiling,
  not a target: the model may stop before it[^max-early].
- `system` (optional): the system prompt, a way to give Claude context and instructions, such as a goal or
  a role[^system].
- `messages`: the conversation so far, oldest first. Each turn has a `role`, `user` or `assistant`, and its
  `content`. In a request, `content` can be a plain string, as in the example below[^content-string]; in a
  reply it is a list of blocks, as you will see further down. The models are trained on alternating user
  and assistant turns[^alternating], so put your turns in that order: user, assistant, user, and so on.

```json
{
  "model": "claude-opus-5-5",
  "max_tokens": 1024,
  "system": "You are a patient tutor. Answer in two sentences.",
  "messages": [
    {"role": "user", "content": "What is a token?"}
  ]
}
```

The API is stateless: it does not remember your earlier calls, so you send the full conversation history
every time[^stateless]. To ask a follow-up, you add Claude's answer as an `assistant` turn and your new
question as a `user` turn, then send all of it again. The last turn should be the user's. Ending on an
assistant turn ("prefill") is not supported on Claude 4.6 and later models, including Claude Opus 5.5,
the model used here[^prefill]. Such a request returns an error[^prefill-error].

You may meet `temperature` in older examples: it sets how much randomness goes into the answer[^temperature].
On Claude 4.7 and later models, including Claude Opus 5.5, `temperature` and the other sampling settings,
`top_p` and `top_k`, are not supported[^sampling], and a value other than the default makes the request
fail[^sampling-error]. Guide the answer with your prompt
instead.

Here is a reply, shown as JSON. It is a sample shaped like a real reply, not a recording of a real call,
so its token counts are illustrative.

```json
{
  "id": "msg_sample_01",
  "type": "message",
  "role": "assistant",
  "model": "claude-opus-5-5",
  "content": [
    {
      "type": "text",
      "text": "A token is a small piece of text, such as a word or part of a word. Claude reads your prompt and writes its answer as tokens."
    }
  ],
  "stop_reason": "end_turn",
  "stop_sequence": null,
  "usage": {
    "input_tokens": 41,
    "output_tokens": 28
  }
}
```

Three parts matter most:

- `content` is a list of blocks, not one string. A `text` block holds words of the answer. Other kinds of
  blocks exist. For example, when thinking is turned on, Claude reasons in thinking blocks before it
  answers, and they arrive before the text blocks[^thinking-blocks]. So collect the blocks whose type is
  `text` instead of assuming the first block is the answer.
- `stop_reason` says why Claude stopped writing[^stop-every]. `end_turn` means Claude finished its answer
  naturally[^stop-end]. `max_tokens` means it reached the `max_tokens` limit in your request[^stop-max]: the
  text is cut off, and the fix is to raise `max_tokens` or continue the answer[^stop-max-do]. A stop reason
  is not an error: it tells you why a successful reply ended[^stop-not-error]. Other values exist; later
  lessons meet them.
- `usage` counts the input tokens (what you sent)[^usage] and the output tokens (what Claude
  wrote)[^usage-output]. The output count includes every output token, thinking included, and is the
  figure billed for output[^usage-billing]. Because you resend the history on every
  call, the input count grows as a conversation gets longer.

Streaming changes how the reply travels, not what it says. With `"stream": true` the API sends the reply
in pieces, as server-sent events (a standard way for a server to send many small messages over one open
connection)[^stream-sse], so you can show text while Claude is still writing. For requests with large
`max_tokens` values, the SDK requires streaming to avoid timeouts, where the connection gives up because
the reply takes too long[^stream-timeout].
The stream starts with a `message_start` event that holds a message with empty content[^stream-start].
Each content block then arrives as a `content_block_start` event, one or more `content_block_delta`
events, and a `content_block_stop` event[^stream-flow]. A delta is a small change, such as the next piece of
text. Each delta updates the block at a given index, the block's position in the reply's `content`
list[^stream-delta]. The token counts in the `message_delta` event are running totals, not additions to
make[^stream-cumulative]. A stream may also hold `ping` events[^stream-ping], and your code should handle
event types it does not know without crashing[^stream-unknown].

## Try it

### With your own key (optional)

This part calls the real API, so it needs an API key, and the tokens it uses are billed[^pricing].
Skip it if you have no key: the next part and the exercise work without one. Put the key in your environment, never in your code, and
never commit it (a commit is a saved snapshot of your project in Git, which others may later see). The
first line below sets the environment variable for this terminal window. The second line creates a virtual environment (venv): a separate Python environment
for this project, so what you install stays out of the rest of your system. The third line uses pip, Python's package
installer, to install the SDK.

```bash
export ANTHROPIC_API_KEY="your-key-here"
python3 -m venv .venv && source .venv/bin/activate
pip install anthropic
```

```python
import os

import anthropic

if "ANTHROPIC_API_KEY" not in os.environ:
    raise SystemExit("Set ANTHROPIC_API_KEY in your environment first.")

client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from the environment

history = [{"role": "user", "content": "What is a token?"}]
message = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    system="You are a patient tutor. Answer in two sentences.",
    messages=history,
)
answer = "".join(block.text for block in message.content if block.type == "text")
print(answer)
print("stop_reason:", message.stop_reason)
print("tokens in:", message.usage.input_tokens, "out:", message.usage.output_tokens)

# A follow-up: send the whole conversation again, with the new question last.
history += [
    {"role": "assistant", "content": answer},
    {"role": "user", "content": "And what is a context window?"},
]
with client.messages.stream(
    model="claude-opus-5-5",
    max_tokens=1024,
    system="You are a patient tutor. Answer in two sentences.",
    messages=history,
) as stream:
    for text in stream.text_stream:
        print(text, end="", flush=True)  # each piece appears as soon as it arrives
print()
```

Save this code as a file, for example `live_call.py`, and run it with `python3 live_call.py`. Your answer
will not match the samples below word for word, and neither will its token counts.

### Without a key: read a sample reply

The lesson folder holds the sample reply above, a reply that was cut off, and a sample stream, in
`exercise/tests/`. Save this code as a file in the lesson folder, for example `read_samples.py`, and run
`python3 read_samples.py` from that folder:

```python
import json
from pathlib import Path

folder = Path("exercise/tests")
for name in ("sample_reply.json", "sample_cut_off.json"):
    reply = json.loads((folder / name).read_text(encoding="utf-8"))
    text = "".join(block["text"] for block in reply["content"] if block["type"] == "text")
    print(name, "->", reply["stop_reason"], reply["usage"])
    print("  ", text)
```

The first reply used 41 input tokens and 28 output tokens, and it ended with `end_turn`. The second
ended with `max_tokens`: Claude wrote 16 output tokens and stopped mid-sentence: it had reached the
request's `max_tokens` limit. Its text ends with "that a model can", a sentence with no end. In
`sample_stream.json`, the same first answer arrives in 6 text pieces.

## Common mistakes

- **Writing the key in your code.** Code gets shared and committed. Read the key from the environment
  instead[^start-env].
- **Expecting the API to remember.** Each call stands alone[^stateless]. If you send only the new question,
  Claude has never seen the first one.
- **Putting the system prompt in `messages`.** Instructions that apply from the start go in the top-level
  `system` field[^system-top].
- **Reading `content[0]` as the answer.** The answer is the text blocks, and the first block may be of
  another kind[^thinking-blocks].
- **Ignoring `stop_reason`.** A reply cut off by `max_tokens` looks like a normal reply that ends mid-sentence.
  Check `stop_reason` before you trust the text[^stop-every].
- **Adding up the stream's token counts.** The counts in `message_delta` are running totals: keep the
  latest[^stream-cumulative].

## Your exercise

### What to build

Open `exercise/starter/first_call.py` and write three functions. They work offline, on the samples in
`exercise/tests/`:

- `build_request(model, max_tokens, turns, system=None)` returns the request body as a dict (a Python
  dictionary, which maps names to values, like the JSON above). `turns` is a list of `(role, text)` pairs. Add `system` only when there is a system prompt. Raise `ValueError` (Python's usual error for a bad value) for a
  `max_tokens` below one or not a whole number, for no turns, for a role other than `user` or
  `assistant`, and for a last turn that is not the user's. The rule on `max_tokens` is this course's rule for a request
  that should produce an answer: the API itself also accepts 0, which fills the prompt cache (a store
  that lets later requests reuse the same prompt) and writes no answer[^max-zero].
- `read_reply(response)` returns a dict with `text` (all text blocks joined), `stop_reason`,
  `input_tokens`, `output_tokens`, and `cut_off`, which is true when the reply stopped at `max_tokens`.
- `join_stream(events)` returns the same dict from a list of streaming events.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

`unittest` is Python's built-in test runner. The tests fail until your functions work. A solution is in `exercise/solution/`: try first, then compare.

## Check yourself

Take the quiz for this lesson. If a question is hard, read the part of "The idea" about the request fields,
`stop_reason` or streaming again.
