"""Give Claude a tool: define it, read Claude's call, return the result, and run the loop.

Write the four functions. Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""
import json  # noqa: F401  (tool_results needs it)
import re

# The rule the API sets for a tool's name.
TOOL_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


def define_tool(name, description, properties, required=()):
    """Return a tool definition for the "tools" list of a Messages API request:
    {"name": ..., "description": ..., "input_schema": {"type": "object", "properties": ..., "required": [...]}}

    Raise ValueError when the name does not match TOOL_NAME, when the description is empty,
    or when a required field is not in properties.
    """
    raise NotImplementedError


def tool_calls(response):
    """Return the tool calls in a reply, in order: a list of {"id": ..., "name": ..., "input": ...},
    one for each content block whose type is "tool_use". Ignore every other block."""
    raise NotImplementedError


def tool_results(response, functions):
    """Run each tool Claude asked for and return the user message that carries the results.

    functions maps a tool name to a Python function; call it with the tool's input as keyword
    arguments: functions[name](**input). The message is {"role": "user", "content": [...]} with one
    {"type": "tool_result", "tool_use_id": ..., "content": ...} block per call, in the same order.
    content is the function's result: a string as it is, anything else as JSON text (json.dumps).
    """
    raise NotImplementedError


def run_tool_loop(ask, question, tools, functions, max_rounds=5):
    """Ask, run the tools Claude calls, send the results back, until Claude stops calling tools.

    ask(messages, tools) stands in for the API call and returns a reply as a dict.
    Start with one user message holding the question. While the reply's stop_reason is "tool_use",
    add the reply as an assistant message (its whole content) and then the tool_results() message.
    Return (answer_text, messages): messages is the whole conversation, ending with Claude's final reply.
    If Claude still calls a tool after max_rounds rounds of tool calls, raise RuntimeError.
    """
    raise NotImplementedError
