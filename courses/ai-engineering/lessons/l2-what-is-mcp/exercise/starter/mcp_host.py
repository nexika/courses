"""The host's side of MCP: turn a server's tools into Claude's tools, and Claude's calls into MCP calls.

Write request(), claude_tools(), call_request() and tool_result(). Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""
import re

# The Claude API accepts tool names made of these characters, 1 to 128 of them.
NOT_ALLOWED = re.compile(r"[^A-Za-z0-9_-]")
MAX_NAME = 128


def request(request_id, method, params):
    """Return a JSON-RPC 2.0 request: the version, its id, the method name and its params."""
    raise NotImplementedError


def claude_tools(server, listing, routes=None):
    """Turn a server's tools/list response into tool definitions for the Claude API.

    server is the name you gave the server; listing is its JSON-RPC response to tools/list.
    Each tool's name becomes server + "__" + its MCP name, with every character the API does not
    accept replaced by "_". Its inputSchema becomes input_schema.
    routes maps each Claude tool name to (server, MCP tool name); pass the same dict for every server,
    and the function adds to it. Return (tools, routes).
    Raise ValueError if the response is an error, or if a name is too long or already taken.
    """
    raise NotImplementedError


def call_request(request_id, tool_use, routes):
    """Turn Claude's tool_use block into (server, tools/call request) for the server that owns the tool.

    Raise KeyError if no server owns the tool.
    """
    raise NotImplementedError


def tool_result(tool_use_id, sent, response):
    """Turn the server's response to a tools/call request into a tool_result block for Claude.

    sent is the request you sent. Raise ValueError if the response's id is not the request's id.
    - an error response (a protocol error): is_error true, content "MCP error <code>: <message>"
    - a result: the text of its text items, one per line; any other item becomes "[<type> not shown]";
      is_error true only when the result's isError is true
    """
    raise NotImplementedError
