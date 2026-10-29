"""Connect MCP servers to Claude Code with care: build the add command, read .mcp.json, flag what to check.

Write add_command(), expand(), pick(), review(), tool_name() and rule_matches().
Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""
import fnmatch  # noqa: F401  (rule_matches can use it)
import re

SCOPES = ("local", "project", "user")
# ${VAR} or ${VAR:-default}, as in .mcp.json
VARIABLE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::-([^}]*))?\}")
# Header and env names that usually hold a secret
SECRET_NAME = re.compile(r"authorization|token|key|secret|password", re.IGNORECASE)
# Parts of a command line worth reading by hand before you let it run
RISKY = ("sudo", "rm -rf", "curl", "wget", "&&", "|", ";")


def add_command(name, *, url=None, command=None, args=(), scope="local", env=None):
    """Return the `claude mcp add` command as a list of words.

    Give either url (a remote server: transport http) or command and args (a local server: transport
    stdio). Always write --transport and --scope (even the default, local) before the name.
    env maps names to values for a local server; each pair goes after the server name as
    --env NAME=value, and the server's command comes after "--".
    Raise ValueError for an unknown scope, for both or neither of url and command, or for env with a url.
    """
    raise NotImplementedError


def expand(text, environ):
    """Expand ${VAR} and ${VAR:-default} in text, from the dict environ.

    A variable that is not set and has no default stays as written. Return (text, missing names).
    """
    raise NotImplementedError


def pick(local, project, user):
    """Which definition of each server Claude Code uses: local, then project, then user.

    Each argument maps server names to entries. Return {name: (scope, entry)}; the whole entry comes from
    one scope, never merged.
    """
    raise NotImplementedError


def review(config):
    """Return what to check in a .mcp.json file, as a sorted list of (server name, kind) pairs.

    Kinds:
    - "no-type": the entry has a url but no type
    - "not-https": a remote url that does not start with https:// (a url that starts with ${ is skipped)
    - "secret": a header or env value whose name looks like a secret, written without ${...}
    - "command": the command and args of a local server contain one of RISKY
    """
    raise NotImplementedError


def tool_name(server, tool):
    """Return the name Claude Code gives a server's tool: mcp__<server>__<tool>."""
    raise NotImplementedError


def rule_matches(rule, server, tool):
    """Say whether a permission rule matches a server's tool.

    "mcp__<server>" matches every tool of that server. Any other rule is compared with the tool's full name
    (tool_name()), where "*" stands for any text: "mcp__<server>__*" matches every tool of the server,
    "mcp__<server>__get_*" its tools whose names start with get_, and "mcp__*" every MCP tool.
    It does not check the rule's kind: in an allow rule, Claude Code skips "mcp__*".
    """
    raise NotImplementedError
