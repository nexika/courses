"""Connect MCP servers to Claude Code with care: build the add command, read .mcp.json, flag what to check.

Write add_command(), expand(), pick(), review(), tool_name() and rule_matches().
Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""
import fnmatch
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
    if scope not in SCOPES:
        raise ValueError(f"scope must be one of {', '.join(SCOPES)}")
    if (url is None) == (command is None):
        raise ValueError("give either url or command")
    if url is not None:
        if env:
            raise ValueError("env is for a local server; a remote server takes headers")
        return ["claude", "mcp", "add", "--transport", "http", "--scope", scope, name, url]
    words = ["claude", "mcp", "add", "--transport", "stdio", "--scope", scope, name]
    for key, value in (env or {}).items():
        words += ["--env", f"{key}={value}"]
    return words + ["--", command, *args]


def expand(text, environ):
    """Expand ${VAR} and ${VAR:-default} in text, from the dict environ.

    A variable that is not set and has no default stays as written. Return (text, missing names).
    """
    missing = []

    def one(match):
        name, default = match.group(1), match.group(2)
        if name in environ:
            return environ[name]
        if default is not None:
            return default
        missing.append(name)
        return match.group(0)

    return VARIABLE.sub(one, text), missing


def pick(local, project, user):
    """Which definition of each server Claude Code uses: local, then project, then user.

    Each argument maps server names to entries. Return {name: (scope, entry)}; the whole entry comes from
    one scope, never merged.
    """
    chosen = {}
    for scope, servers in (("user", user), ("project", project), ("local", local)):
        for name, entry in servers.items():
            chosen[name] = (scope, entry)
    return dict(sorted(chosen.items()))


def review(config):
    """Return what to check in a .mcp.json file, as a sorted list of (server name, kind) pairs.

    Kinds:
    - "no-type": the entry has a url but no type
    - "not-https": a remote url that does not start with https:// (a url that starts with ${ is skipped)
    - "secret": a header or env value whose name looks like a secret, written without ${...}
    - "command": the command and args of a local server contain one of RISKY
    """
    found = set()
    for name, entry in config.get("mcpServers", {}).items():
        url = entry.get("url")
        if url is not None:
            if "type" not in entry:
                found.add((name, "no-type"))
            if not url.startswith(("https://", "${")):
                found.add((name, "not-https"))
        for values in (entry.get("headers", {}), entry.get("env", {})):
            for key, value in values.items():
                if SECRET_NAME.search(key) and "${" not in value:
                    found.add((name, "secret"))
        if "command" in entry:
            line = " ".join([entry["command"], *entry.get("args", [])])
            if any(part in line for part in RISKY):
                found.add((name, "command"))
    return sorted(found)


def tool_name(server, tool):
    """Return the name Claude Code gives a server's tool: mcp__<server>__<tool>."""
    return f"mcp__{server}__{tool}"


def rule_matches(rule, server, tool):
    """Say whether a permission rule matches a server's tool.

    "mcp__<server>" matches every tool of that server. Any other rule is compared with the tool's full name
    (tool_name()), where "*" stands for any text: "mcp__<server>__*" matches every tool of the server,
    "mcp__<server>__get_*" its tools whose names start with get_, and "mcp__*" every MCP tool.
    It does not check the rule's kind: in an allow rule, Claude Code skips "mcp__*".
    """
    if rule == f"mcp__{server}":
        return True
    return fnmatch.fnmatchcase(tool_name(server, tool), rule)
