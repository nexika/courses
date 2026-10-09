"""When a tool fails: report the failure to Claude in a tool_result, never crash the loop.

Write check_input(), run_one() and tool_results(). Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""
import json  # noqa: F401  (run_one needs it)

# What each JSON Schema type accepts in Python. True and False are not numbers here.
JSON_TYPES = {
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
}


class ToolError(Exception):
    """Raised by a tool when it fails in a way it can explain. The message is written for Claude:
    what went wrong and what to try next."""


def check_input(tool, args):
    """Return a list of problems with the input Claude sent for a tool; an empty list means it is fine.

    tool is a tool definition (with "input_schema"); args is the tool_use block's input.
    Report each required field that is missing, each field whose value does not match its "type"
    (use JSON_TYPES), and, only when the schema sets "additionalProperties" to False, each field that is
    not in "properties". Name the field in each problem.
    """
    raise NotImplementedError


def run_one(call, tools, functions):
    """Run one tool call and return its tool_result block. Never raises.

    call is {"id": ..., "name": ..., "input": ...}; tools is the list of tool definitions;
    functions maps a tool name to its Python function.
    - unknown tool name (not in tools, or with no function): an error result that lists the available
      tool names (those with both a definition and a function)
    - check_input finds problems: an error result that names them and asks Claude to call again
    - the function raises ToolError: an error result whose content is the error's message
    - the function raises any other exception: an error result that names the tool and the kind of
      exception (type(e).__name__) but not its message, and tells Claude not to guess
    - success: {"type": "tool_result", "tool_use_id": ..., "content": ...}, content as in the last lesson
    An error result is the same block with "is_error": True.
    """
    raise NotImplementedError


def tool_results(response, tools, functions):
    """Return the user message with one tool_result per tool_use block of the reply, in order.
    It never raises, whatever the tools do."""
    raise NotImplementedError
