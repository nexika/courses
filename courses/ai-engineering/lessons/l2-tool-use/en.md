# Give Claude a tool

## What you will be able to do

- Define a tool: its name, a description of when to use it, and a JSON Schema for its input.
- Read Claude's request for a tool, run the tool in your code, and send the result back.
- Run the tool loop: keep going while Claude asks for tools, and stop when it answers.

## The idea

Claude cannot look up an order in your shop's database. It has never seen that data. But your code can.
**Tool use** (also called function calling) lets Claude call functions that you define[^ov-what]. You
describe a tool; Claude decides when to call it, based on the user's request and the tool's
description[^ov-what].

The model never runs anything itself. It writes a structured request, your code runs the operation, and
the result goes back into the conversation[^hw-contract]. Claude never sees your code: it sees only the
definition you gave it and the result you send back[^hw-sees].

A tool definition goes in the `tools` list of the request[^dt-tools]. It has three parts[^dt-fields]:

- `name`: letters, digits, `_` or `-`, at most 128 characters[^dt-fields].
- `description`: what the tool does, when to use it and how it behaves.
- `input_schema`: a JSON Schema for the tool's input, like the schemas of the last lesson.

```json
{
  "name": "lookup_order",
  "description": "Look up a customer's order by its order number and return its status. Use it when the user asks where an order is or whether it has shipped. It returns only the status and the days to delivery, not what the order contains.",
  "input_schema": {
    "type": "object",
    "properties": {
      "order_id": {"type": "string", "description": "The order number, such as A-1042."}
    },
    "required": ["order_id"]
  }
}
```

The description matters more than anything else: Anthropic's guide calls it by far the most important
factor in how well a tool works, and asks for at least three or four sentences[^dt-desc].

Here is one round of the **tool exchange**, for the question `Where is order A-1042?`:

1) You send the question and the `tools` list.
2) Claude replies with the stop reason `tool_use` and a `tool_use` block. The block holds an `id`, the tool's
   `name`, and an `input` object for it[^hc-block]. Claude often writes a short text block first, such as
   "I'll look up that order."[^dt-comment]
3) Your code runs the tool with that input.
4) You send a new request: the whole conversation so far, Claude's reply as an `assistant` turn, and a
   `user` turn with a `tool_result` block. Its `tool_use_id` is the `id` of the call it answers, and its
   `content` is the result[^hc-result].
5) Claude reads the result and writes its answer[^hc-continue].

A reply can hold one or more `tool_use` blocks[^hc-block]: answer every one. The Claude API has no
special `tool` role: tool calls travel in `assistant` turns and results in `user` turns[^hc-roles]. Two
rules about order matter. The tool results must come right after the turn that asked for them, with no
message in between. And in that `user` turn, the `tool_result` blocks come first, before any
text[^hc-order].

**The tool loop** repeats this. While the stop reason is `tool_use`, run the tools and continue the
conversation. Any other stop reason ends the loop: Claude has answered, or stopped for a reason your code
must handle[^hw-loop]. Each round is another request, and every request sends the whole history again,
so put a limit on the number of rounds.

Tools cost tokens. The tool definitions count as input tokens[^ov-price], and the API adds a system prompt
that enables tool use[^ov-enables]: 286 tokens on Claude Opus 5.5[^ov-prompt].

## Try it

### Without a key: one round, by hand

The folder `exercise/tests/` holds two sample replies, shaped like real ones but not recorded from real
calls: Claude's call to `lookup_order`, and its final answer. Here they stand in for Claude. Save this as
`one_round.py` in the lesson folder and run `python3 one_round.py` from that folder:

```python
"""One round of the tool exchange, offline: two sample replies stand in for Claude."""
import json
from pathlib import Path

folder = Path("exercise/tests")
replies = [json.loads((folder / name).read_text(encoding="utf-8"))
           for name in ("sample_tool_call.json", "sample_final_answer.json")]


def lookup_order(order_id):
    """Real code would ask the shop's database. This one knows a single order."""
    return {"order_id": order_id, "status": "shipped", "days_to_delivery": 2}


messages = [{"role": "user", "content": "Where is order A-1042?"}]
reply = replies[0]  # the reply to request 1: Claude asks for the tool
print("stop_reason:", reply["stop_reason"])
messages.append({"role": "assistant", "content": reply["content"]})
results = []
for block in reply["content"]:
    if block["type"] == "tool_use":
        print("Claude calls", block["name"], "with", block["input"])
        output = lookup_order(**block["input"])
        results.append({"type": "tool_result", "tool_use_id": block["id"], "content": json.dumps(output)})
messages.append({"role": "user", "content": results})
print("request 2 sends", len(messages), "messages:", [m["role"] for m in messages])
reply = replies[1]  # the reply to request 2: Claude answers with the result
print("stop_reason:", reply["stop_reason"])
print("".join(block["text"] for block in reply["content"] if block["type"] == "text"))
```

`lookup_order(**block["input"])` passes the input's fields as keyword arguments, so
`{"order_id": "A-1042"}` becomes `lookup_order(order_id="A-1042")`. The second request sends 3 messages:
the question, Claude's call, and the result.

### With your own key (optional)

This runs the real loop, so it needs a key and its tokens are billed. Set up the key and the SDK as in
the lesson "Your first API call".

```python
import json

import anthropic

client = anthropic.Anthropic()
tools = [{
    "name": "lookup_order",
    "description": ("Look up a customer's order by its order number and return its status. "
                    "Use it when the user asks where an order is or whether it has shipped. "
                    "It returns only the status and the days to delivery, not what the order contains."),
    "input_schema": {
        "type": "object",
        "properties": {"order_id": {"type": "string", "description": "The order number, such as A-1042."}},
        "required": ["order_id"],
    },
}]


def lookup_order(order_id):
    return {"order_id": order_id, "status": "shipped", "days_to_delivery": 2}


messages = [{"role": "user", "content": "Where is order A-1042?"}]
for round_number in range(5):  # a limit, so the loop cannot run forever
    response = client.messages.create(model="claude-opus-5-5", max_tokens=1024, tools=tools, messages=messages)
    if response.stop_reason != "tool_use":
        break
    messages.append({"role": "assistant", "content": response.content})
    results = []
    for block in response.content:
        if block.type == "tool_use":
            output = lookup_order(**block.input)
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": json.dumps(output)})
    messages.append({"role": "user", "content": results})
print("stop_reason:", response.stop_reason)
print("".join(block.text for block in response.content if block.type == "text"))
```

The SDK can also run this loop for you, with its Tool Runner[^hc-runner]. Write the loop by hand first, so
you know what it does.

## Common mistakes

- **"Claude runs my function."** It never does. It asks; your code runs it and reports back[^hw-contract].
  Your code decides what a tool may do.
- **A one-line description.** The description is the main thing Claude has to choose a tool and fill its
  input[^dt-desc]. Say what it does, when to use it, and what it does not return.
- **Forgetting the `assistant` turn.** The next request must hold Claude's reply, with its `tool_use`
  blocks, before your results. The API is stateless: it does not remember the call[^stateless].
- **Text before the results.** In the results turn, `tool_result` blocks come first. Text before them
  makes the request fail[^hc-order].
- **Answering only the first call.** A reply can hold several `tool_use` blocks[^hc-block]. Send a result
  for each, matched by `tool_use_id`.
- **Trusting the input blindly.** When the user leaves out a required value, Claude may ask for it, or may
  guess one, such as a city you never named[^ov-guess]. Check the input before you act on it.
- **Trusting what a tool returns.** Web pages, emails and other outside content can hide instructions
  aimed at Claude. Treat tool results as untrusted, and keep such content inside `tool_result`
  blocks[^hc-untrusted].
- **Forcing a tool with `tool_choice`.** On Claude Opus 5.5, forcing a tool with `tool_choice` set to
  `any` or `tool` returns an error[^dt-forced]. Leave it on `auto`, the default[^ov-auto], and write a
  better description or prompt.

## Your exercise

### What to build

Open `exercise/starter/tools.py` and write four functions. They work offline: in the tests, a stand-in
plays Claude's part, as in the last lesson.

- `define_tool(name, description, properties, required)` returns a tool definition. Raise `ValueError` for a
  name the API would refuse, an empty description, or a required field that is not in `properties`.
- `tool_calls(response)` returns the reply's tool calls, in order, as dicts with `id`, `name` and `input`.
- `tool_results(response, functions)` runs each call and returns the `user` message with one
  `tool_result` block per call. `functions` maps a tool's name to the Python function that runs it.
- `run_tool_loop(ask, question, tools, functions, max_rounds)` runs the loop: `ask(messages, tools)` stands
  in for the API call. It returns the answer's text and the whole conversation, and raises `RuntimeError`
  if Claude still calls a tool after `max_rounds` rounds.

In this lesson every tool succeeds. The next lesson handles tools that fail.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

The tests fail until your functions work. A solution is in `exercise/solution/`: try first, then compare.

## Check yourself

Take the quiz for this lesson. If a question is hard, read the five steps of the tool exchange in "The
idea" again.

[^ov-what]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hw-contract]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^hw-sees]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^dt-tools]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^dt-fields]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^dt-desc]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-block]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-comment]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^hc-result]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-continue]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-roles]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-order]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hw-loop]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^ov-price]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^ov-prompt]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^ov-enables]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-runner]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^stateless]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^ov-guess]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
[^hc-untrusted]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^dt-forced]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^ov-auto]: Tool use with Claude, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview>
