# When a tool fails

## What you will be able to do

- Report a tool's failure to Claude in a `tool_result` with `is_error`, instead of crashing or making up a result.
- Write error messages that tell Claude what went wrong and what to try next.
- Check Claude's input before you run a tool, and answer every call, even when most of them fail.

## The idea

Tools fail. A service is down, an order number does not exist, or Claude calls a tool with an input that
does not fit. Your code has three bad choices and one good one.

- **Crash.** Your program stops, and the user gets nothing. Catching the error but sending no result is
  no better: every `tool_use` block needs its `tool_result` right after it[^hc-follow], or the next
  request fails[^hc-missing].
- **Send nothing useful,** such as an empty result or `"failed"`. Claude has nothing to work with.
- **Make up a result,** such as a default status. Claude sees only the result you return, not how you
  got it[^hw-sees], so it cannot tell a made-up result from a real one.
- **Report the failure.** Send a `tool_result` whose `content` says what went wrong, with `"is_error":
  true`[^hc-exec]. Claude then works the error into its answer, for example by telling the user that the
  service is not available[^hc-exec-claude].

`is_error` is an optional field of the `tool_result` block: set it to `true` when running the tool ended
in an error[^hc-is-error]. Here is a failed lookup:

```json
{
  "role": "user",
  "content": [
    {
      "type": "tool_result",
      "tool_use_id": "toolu_sample_02",
      "content": "No order A-999. Ask the user to check the number: order numbers are A- followed by four digits.",
      "is_error": true
    }
  ]
}
```

The message is written for Claude. Anthropic's guide asks for instructive error messages: instead of a
generic `"failed"`, say what went wrong and what Claude should try next. That gives Claude the context to
recover or adapt without guessing[^hc-instructive]. Remember who reads it next: Claude may repeat it to
the user[^hc-exec-claude]. So leave out what neither should see, such as stack traces (the list of
calls Python prints when an error is not caught), server addresses or passwords.

Failures come in two kinds:

- **The tool ran and failed:** the order does not exist, or the service timed out. Report what happened.
- **Claude's call was wrong:** a required field is missing, a field has the wrong type, a field is not
  allowed, or the tool name does not exist. Check the input against the tool's `input_schema` before you run anything, and report
  the problems. Claude will then try the tool again with the missing information filled in[^hc-invalid]:
  if a call is invalid or misses parameters, Claude retries 2 to 3 times with corrections before it
  apologizes to the user[^hc-retries]. During development, a wrong call usually means the tool's
  `description` needs more detail[^hc-desc]. If you need inputs that always match the schema, the API
  offers strict tool use, with `strict: true` on the tool definition[^hc-strict]. Even then the tool itself
  can still fail, so you still need error results.

Retries cost a round each, and the limit on rounds from the last lesson still holds.

## Try it

The folder `exercise/tests/` holds a sample reply with four tool calls. It is shaped like a real reply,
not recorded from a real call, and a real reply rarely holds this many mistakes at once. One call is
fine. One asks for an order that does not exist. One sends a field named `order` instead of `order_id`.
One calls `track_parcel`, a tool that does not exist. Save this as `four_calls.py` in the lesson folder
and run `python3 four_calls.py` from that folder:

```python
"""Four tool calls, three failures: every call still gets a tool_result. No network, no key."""
import json
from pathlib import Path

reply = json.loads(Path("exercise/tests/sample_four_calls.json").read_text(encoding="utf-8"))
ORDERS = {"A-1042": "shipped"}


def lookup_order(order_id):
    if order_id not in ORDERS:
        raise LookupError(f"No order {order_id}. Ask the user to check the number: order numbers are A- followed by four digits.")
    return {"order_id": order_id, "status": ORDERS[order_id]}


FUNCTIONS = {"lookup_order": lookup_order}
results = []
for block in reply["content"]:
    if block["type"] != "tool_use":
        continue
    result = {"type": "tool_result", "tool_use_id": block["id"]}
    if block["name"] not in FUNCTIONS:
        result.update(content=f"Unknown tool '{block['name']}'. Available tools: lookup_order.", is_error=True)
    else:
        try:
            result["content"] = json.dumps(FUNCTIONS[block["name"]](**block["input"]))
        except LookupError as error:
            result.update(content=str(error), is_error=True)
        except TypeError:  # the input's fields do not fit the function
            result.update(content="Invalid input for lookup_order: it takes one field, order_id. "
                                  "Call it again with a corrected input.", is_error=True)
    results.append(result)
    print(json.dumps(result))
print(sum(1 for r in results if r.get("is_error")), "of", len(results), "results have is_error set")
```

Every call gets a `tool_result`, in order, and 3 of the 4 results carry `is_error`. Nothing crashed, and
nothing was made up. Catching `TypeError` is a shortcut here: it is what Python raises when the input's
fields do not fit the function. Your exercise checks the input against the schema before it runs the
tool, which gives Claude a more precise message.

## Common mistakes

- **Letting the exception escape.** The loop stops, and the `tool_use` block never gets its
  `tool_result`[^hc-missing]. Catch the failure and report it.
- **Returning an error as a normal result.** Without `is_error`, the text `No order A-999` looks like
  data. Set `"is_error": true`[^hc-is-error].
- **Generic messages.** `"failed"` gives Claude nothing to act on. Say what went wrong and what to try
  next[^hc-instructive].
- **Sending the raw exception.** A stack trace can hold file paths, addresses or secrets, and Claude may
  repeat the error to the user[^hc-exec-claude]. Name the kind of failure; keep the details in your logs
  (the records your program writes for you, such as a file of messages).
- **Running the tool on input you did not check.** Check required fields, fields that are not allowed, and types first.
  A wrong call is reported so Claude can correct it[^hc-invalid].
- **Skipping the calls after the first failure.** Each `tool_use` block needs its own
  `tool_result`[^hc-missing]. Answer all of them.

## Your exercise

### What to build

Open `exercise/starter/errors.py`. It gives you `JSON_TYPES` and `ToolError`, an exception your tools raise
when they fail in a way they can explain. Write three functions:

- `check_input(tool, args)` returns the problems with Claude's input: missing required fields, values of
  the wrong type, and, when the schema sets `additionalProperties` to `false`, fields it does not list.
  As the lesson on JSON output showed, a schema without that setting allows extra fields.
- `run_one(call, tools, functions)` runs one call and always returns a `tool_result` block. Report an
  unknown tool by listing the real ones; report bad input without running the tool; pass a `ToolError`'s
  message to Claude; and for any other exception, name the tool and the kind of exception, but not its
  message.
- `tool_results(response, tools, functions)` returns the `user` message with one result per call, in
  order. It never raises.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

The tests fail until your functions work. A solution is in `exercise/solution/`: try first, then compare.

## Check yourself

Take the quiz for this lesson. If a question is hard, read the four choices at the start of "The idea"
again.

[^hc-missing]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-exec]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-exec-claude]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-is-error]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-instructive]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-invalid]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-retries]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-desc]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hc-follow]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^hw-sees]: How tool use works, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/how-tool-use-works>
[^hc-strict]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
