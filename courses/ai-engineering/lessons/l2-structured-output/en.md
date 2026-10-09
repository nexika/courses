# Get JSON you can trust

## What you will be able to do

- Describe the data you want with a JSON Schema: the fields, their types, and which ones are required.
- Ask Claude for JSON that follows the schema, with `output_config.format`.
- Check every reply before your code uses it, and decide when to ask again and when to stop.

## The idea

Your code cannot read a friendly sentence. If a support app asks Claude to sort a customer message, the
app needs three fields it can trust: a category, a priority and a short summary. Without help, Claude can
write JSON that is broken, or JSON that leaves out a required field, and that breaks your
application[^so-without].

A **JSON Schema** describes the shape of the data you expect. The schema itself is written in JSON: it is
data, not a program[^js-data]. Here is the schema for a support ticket:

```json
{
  "type": "object",
  "properties": {
    "category": {"type": "string", "enum": ["bug", "billing", "question"]},
    "priority": {"type": "integer", "minimum": 1, "maximum": 3},
    "summary": {"type": "string"}
  },
  "required": ["category", "priority", "summary"],
  "additionalProperties": false
}
```

Read it from the top. The value is an object (a JSON object, like a Python dict). `properties` lists its
fields and the schema of each one. `type` names the kind of value: `string`, `integer`, `number`,
`boolean`, `array`, `object` or `null`[^so-types]. An `integer` is a whole
number[^js-integer], and a `number` is any number, even one with a decimal part[^js-number]. In Python, an
`object` is a dict, an `array` a list, a `boolean` (`true` or `false`) a `bool`, and `null` is
`None`[^js-python]. `enum` restricts the value to a fixed set of values[^js-enum]. `minimum` and `maximum`
set the range of a number[^js-range]. Two rules surprise people. In JSON Schema, a field listed in
`properties` is not required unless you name it in `required`[^js-required]. And extra fields are allowed unless you set
`additionalProperties` to `false`[^js-additional].

**Structured outputs** is the Claude API feature that makes Claude follow a schema[^so-intro]. You put
the schema in the request, in `output_config.format`, with `type` set to `json_schema`[^so-send]. Claude
then writes valid JSON that matches your schema, in the reply's text block[^so-read]. It works by
turning your schema into a grammar, a set of rules that limits what Claude can write next[^so-grammar].

The feature does not accept every schema. Each object in the schema must set `additionalProperties` to
`false`[^so-supported]. Number limits such as `minimum` and `maximum` are not supported, and a request
that uses a feature the API does not support fails with an error[^so-unsupported]. So you keep two
versions: the schema you send, without `minimum` and `maximum`, and the full schema, which your own code
checks. The official SDKs also offer helper functions that do this for you. Most of them change a schema that uses
features the API does not support[^so-sdk-most]: they send Claude a simpler schema, and a helper that checks replies still checks every rule of your full schema[^so-sdk].
This lesson does it by hand, so you see each step.

Then why check at all? Because "follows the schema" has exceptions:

- **A refusal.** Claude can decline a request. The reply then has the stop reason `refusal`, and its
  output may not match your schema[^so-refusal]. A refusal is a normal, successful reply, not an
  error[^stop-refusal]. Sending the same request again is not the documented fix: a request refused by
  Claude Opus 5.5 can usually be answered if you send it to another Claude model, by changing
  `model`[^refusal-fallback].
- **A cut-off reply.** If the reply reaches `max_tokens`, the JSON may be incomplete. The documented fix is
  to try again with a higher `max_tokens`[^so-max].
- **Capital letters in `enum` values.** Claude may return `"Bug"` when your schema says `"bug"`: the
  capital letters of enum values are not guaranteed[^so-enum-case]. The docs say to compare enum values
  without regard to case (capital or small letters)[^so-enum].
- **Rules the API does not check,** such as `minimum` and `maximum` above, and rules a schema cannot say at
  all, such as "the date must be in the future". Only your code checks those.

A reply that breaks one of your own rules can be asked for again, but the same request may break the
rule again. Each new request costs tokens, so set a limit, then stop and report the problem. Structured outputs also cost a little: Claude receives an extra
system prompt that explains the format, so your input token count is slightly higher[^so-cost].

## Try it

### With your own key (optional)

This calls the real API, so it needs a key and its tokens are billed. Set up the key and the SDK as in
the lesson "Your first API call". The schema sent here has no `minimum` or `maximum`; a description tells
Claude the range instead.

```python
import json

import anthropic

SENT_SCHEMA = {
    "type": "object",
    "properties": {
        "category": {"type": "string", "enum": ["bug", "billing", "question"]},
        "priority": {"type": "integer", "description": "1 = low, 2 = normal, 3 = urgent"},
        "summary": {"type": "string"},
    },
    "required": ["category", "priority", "summary"],
    "additionalProperties": False,
}

client = anthropic.Anthropic()
response = client.messages.create(
    model="claude-opus-5-5",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Sort this support message: I was charged twice in March."}],
    output_config={"format": {"type": "json_schema", "schema": SENT_SCHEMA}},
)
print("stop_reason:", response.stop_reason)
text = "".join(block.text for block in response.content if block.type == "text")
print(json.loads(text) if response.stop_reason == "end_turn" else text)
```

This follows the plain JSON Schema example (without a helper) in Anthropic's structured outputs guide[^so-raw]. Your reply will
differ from the samples below.

### Without a key: read six sample replies

The folder `exercise/tests/` holds six sample replies to the ticket request. They are shaped like real
replies, not recordings of real calls. One of them, `sample_not_json.json`, is what a request without
`output_config` can return: JSON with a sentence before it. Save this code as `read_samples.py` in the
lesson folder and run `python3 read_samples.py` from that folder:

```python
"""Read six sample replies and say which ones your code could use. No network, no key."""
import json
from pathlib import Path

CATEGORIES = ("bug", "billing", "question")
folder = Path("exercise/tests")

for path in sorted(folder.glob("sample_*.json")):
    reply = json.loads(path.read_text(encoding="utf-8"))
    if reply["stop_reason"] != "end_turn":
        print(f"{path.name}: not usable, stop_reason is {reply['stop_reason']}")
        continue
    text = "".join(block["text"] for block in reply["content"] if block["type"] == "text")
    try:
        ticket = json.loads(text)
    except json.JSONDecodeError as error:
        print(f"{path.name}: not usable, not JSON ({error})")
        continue
    problems = []
    if str(ticket.get("category")).lower() not in CATEGORIES:
        problems.append("unknown category")
    priority = ticket.get("priority")
    if type(priority) is not int or not 1 <= priority <= 3:
        problems.append("priority must be a whole number from 1 to 3")
    if not isinstance(ticket.get("summary"), str):
        problems.append("no summary")
    print(f"{path.name}: " + ("not usable, " + ", ".join(problems) if problems else "usable"))
```

Only 2 of the 6 sample replies are usable. `sample_enum_case.json` passes because the category check
ignores case. `sample_out_of_range.json` is valid JSON with every field, but it sets the priority to 5:
no schema feature sent to the API stopped that, so only your check catches it. Two replies stopped early,
one with `max_tokens` and one with `refusal`, and one has a sentence before its JSON, so `json.loads` cannot *parse* it: it cannot turn
the text into Python values.

## Common mistakes

- **"Structured outputs means I never check."** A refusal or a cut-off reply may not match the
  schema[^so-refusal] [^so-max], and number limits are not sent to the API[^so-unsupported]. Check every
  reply.
- **Sending `minimum` or `maximum` in the schema.** The request fails[^so-unsupported]. Keep the full
  schema in your code and send the simpler one.
- **Forgetting `required`.** Without it, every field is optional[^js-required], and your code meets a
  missing key later.
- **Comparing enum values exactly.** `"Bug"` can come back for `"bug"`[^so-enum-case]. Compare without regard
  to case, then use your schema's spelling.
- **Treating `True` as a number.** In Python, `bool` is a kind of `int`[^py-bool], so `isinstance(True, int)`
  is `True`. A check for an integer must turn booleans away.
- **Asking for Claude's reasoning in a field.** A field that asks for the model's thinking or
  step-by-step reasoning may cause a refusal. Ask for a short explanation instead[^so-reasoning].
- **Retrying without a limit.** Every attempt costs tokens. Stop after a few, and do not send a refused
  request again unchanged: the documented fix is another model[^refusal-fallback].

## Your exercise

### What to build

Open `exercise/starter/structured.py`. It gives you `TYPES` (what each JSON Schema type accepts in
Python), the `ReplyError` exception (an error your code raises, with a `reason`), and
`use_schema_spelling()`, which puts enum values back in the schema's spelling. Write three functions:

- `validate(value, schema)` returns a list of problems, empty when the value is valid. It supports
  `type`, `enum` (ignoring case), `minimum`, `maximum`, `properties`, `required`,
  `additionalProperties: false` and `items` (the schema for each element of an array). Report every
  problem, each starting with where it is, such as `$.priority` (`$` stands for the whole value).
- `parse_reply(response, schema)` returns the checked value, or raises `ReplyError` with the reason
  `refusal`, `cut_off`, `not_json` or `invalid`.
- `ask_until_valid(ask, schema, max_tokens, attempts)` calls `ask(max_tokens)` until a reply passes.
  In the tests, `ask` is a stand-in: a function that plays the part of the API and returns sample
  replies, so no call is billed. It stops at once on a refusal, doubles `max_tokens` after a cut-off
  reply (doubling is this course's choice; the docs only say to raise it), and raises `ReplyError` with
  the reason `gave_up` after the last attempt.

The full ticket schema is in `exercise/tests/ticket_schema.json`.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

The tests fail until your functions work. A solution is in `exercise/solution/`: try first, then compare.

## Check yourself

Take the quiz for this lesson. If a question is hard, read again the list of exceptions in "The idea":
refusal, cut-off reply, enum case, and rules the API does not check.

[^so-without]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^js-data]: What is a schema? (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/about>
[^js-required]: object (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/object>
[^js-additional]: object (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/object>
[^so-intro]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-send]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-read]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-grammar]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-supported]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-unsupported]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-sdk]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-refusal]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^stop-refusal]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^refusal-fallback]: Stop reasons and fallback, <https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons>
[^so-max]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-enum]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-enum-case]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-cost]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-types]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^js-enum]: Enumerated values (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/enum>
[^js-range]: Numeric types (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/numeric>
[^js-integer]: Numeric types (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/numeric>
[^js-number]: Numeric types (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/numeric>
[^js-python]: Type-specific keywords (Understanding JSON Schema), <https://json-schema.org/understanding-json-schema/reference/type>
[^so-sdk-most]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^so-raw]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
[^py-bool]: Built-in Types (Python documentation), <https://docs.python.org/3/library/stdtypes.html>
[^so-reasoning]: Structured outputs, <https://platform.claude.com/docs/en/build-with-claude/structured-outputs>
