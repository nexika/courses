# Connect an MCP server

## What you will be able to do

- Add an MCP server to Claude Code with `claude mcp add`, choose its transport and its scope, check that
  it connected, and allow or deny its tools with permission rules.
- Read a `.mcp.json` file: what each server runs or reaches, and how to keep secrets out of it.
- Decide whether to trust a server before you connect it.

## The idea

In the lesson "What MCP is", the host was a small Python file. Now the host is Claude Code. You tell it which
servers to connect, and it starts or reaches them, lists their tools and offers them to Claude.

**Adding a server**

`claude mcp add` adds a server. A **remote** server is reached over HTTP, at a URL. HTTP is the
recommended transport for remote servers[^cc-http]:

```bash
claude mcp add --transport http notion https://mcp.notion.com/mcp
```

A **local** server runs as a program on your computer, over stdio. It suits tools that need direct
access to your system or your own scripts[^cc-stdio]. You give the command that starts it after `--`:
everything before `--` is for Claude Code (`--transport`, `--env`, `--scope`), and everything after it
is passed to the server untouched[^cc-dashdash]:

```bash
claude mcp add --transport stdio files -- npx -y @modelcontextprotocol/server-filesystem ~/mcp-sandbox
```

Here `files` is the name you give the server. `npx` is Node.js's tool for running a package, and `-y`
confirms that it may install the package[^local-npx]. Node.js is a program that runs JavaScript code. This
server, the Filesystem server, needs Node.js[^local-node], and the folders you list at the end are the
ones it may use[^local-dirs]. `--env NAME=value` sets an environment variable for a local
server[^cc-env-flag]. Do not write the server's name right after an `--env` pair: Claude Code would read the name as
another pair and refuse the command[^cc-env-order].

To see your servers, run `claude mcp list` in a terminal; `claude mcp get <name>` shows one, and
`claude mcp remove <name>` removes one. Inside Claude Code, `/mcp` shows each server's status[^cc-manage].
`claude mcp list` shows a status next to each server, such as connected, needs authentication (you
must sign in to the service first), or failed to connect[^cc-status].

**Scopes: where the setting is stored**

Each server is added at a **scope**, which decides where Claude Code loads it and who else gets
it[^cc-scopes]:

| Scope | Loads in | Shared with your team | Stored in |
|---|---|---|---|
| `local` (the default) | this project only | no | `~/.claude.json` |
| `project` | this project only | yes, through git | `.mcp.json` in the project's folder |
| `user` | all your projects | no | `~/.claude.json` |

`~/.claude.json` is a file in your home folder, outside your project. Local scope is the default, and a
server added at local scope stays private to you[^cc-local]. (Scope is about where the setting is stored;
a remote server can have local scope, and a stdio server can have project scope.) A project server is written to `.mcp.json` at the root of
the project, so that everyone who clones the project (downloads their own copy of it with git) gets the same
servers[^cc-project]. Choose the scope
with `--scope`, for example `--scope project`[^cc-scope-flag]. Here is a `.mcp.json` with two servers (the
`${...}` parts are explained below):

```json
{
  "mcpServers": {
    "files": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "${DOCS_DIR:-./docs}"]
    },
    "tickets": {
      "type": "http",
      "url": "https://tickets.example.com/mcp",
      "headers": {"Authorization": "Bearer ${TICKETS_TOKEN}"}
    }
  }
}
```

An entry with a `command` is a local stdio server[^cc-notype]; it can also have `env`, the environment variables passed to
the server[^cc-env-locations]. An entry with a `url` must also say its `type`, such as
`http`: Claude Code reads an entry with no `type` as a local stdio server, so a `url` without a `type`
is an error in the file[^cc-notype].

When the same name is defined at more than one scope, Claude Code uses one definition: local first,
then project, then user. It takes the whole entry from that scope and does not mix fields from
several[^cc-precedence].

**Secrets stay out of the file**

A remote server often needs a secret *token*: here an access key that proves who you are, not the
model's tokens. It can be sent in a *header*, a line of extra information that goes with every HTTP
request, as in `Authorization: Bearer <token>`[^cc-bearer]. Send it only to an `https://` address.
HTTPS is the encrypted version of HTTP: all communication between a client and a server is
encrypted[^mdn-https]. On a plain `http://` address nothing is encrypted, so others on the network path
could read the token.

`.mcp.json` is shared through git[^cc-scopes], so anyone who can read the project can read it. Never write a secret token in
it.
Write `${NAME}` instead, and Claude Code puts in the value of the environment variable `NAME` from your
machine; `${NAME:-default}` uses `default` when `NAME` is not set[^cc-env-syntax]. This lets teams
share one file while each person keeps their own paths and keys[^cc-env-why]. If a variable is not set
and has no default, the file still loads, `claude mcp list` warns about it, and the text `${NAME}` is
used as it is[^cc-env-unset].

**Trust: what you are letting in**

Connecting a server gives it a place in your work. Anthropic's guide says it plainly: verify you trust
each server before you connect it, and know that servers that fetch outside content can expose you to
prompt injection[^cc-verify], the hidden instructions you met in the lesson on tool use[^hc-untrusted2].
Four questions help.

- **What will run on my computer?** A local server is a program that is downloaded and run on your
  machine[^sec-local]. Its command runs as soon as the host starts the server, which a host can do every
  time it launches[^local-start], before Claude calls any tool: a permission prompt for a tool call comes
  too late to stop it. It runs with your user account's permissions, so it can do any file operation you
  can do[^local-perms]. Read the whole command. An attacker can hide a harmful startup command in a
  server's configuration[^sec-startup], and commands with `sudo` (run as the administrator), `rm -rf`
  (delete files and whole folders without asking) or network access deserve a closer look[^sec-patterns].
- **Who wrote it, and what can it reach?** The specification treats tools as code that can do anything,
  and calls descriptions of tool behavior untrusted unless the server is trusted[^spec-safety]. Prefer
  servers from publishers you know, and give each one as little as it needs: one folder, not your home
  folder; a read-only database user (an account in the database that may only read), so the queries Claude runs cannot change data[^cc-readonly].
- **Does it bring in outside content?** Web pages, email and other content from outside your control
  can carry instructions aimed at Claude[^hc-untrusted2]. Treat what such a server returns as data, not
  as orders.
- **Who approved it?** Claude Code asks before it uses a project's `.mcp.json` servers in an interactive
  session[^cc-approve]. A project can also try to approve them in advance, with settings such as
  `enabledMcpjsonServers` in its `.claude/settings.json`, Claude Code's settings file for that project,
  committed to git with the rest. Claude Code ignores those settings while the folder is
  untrusted[^cc-clone]. When you first run `claude` in a folder, it asks whether you trust it (the
  workspace trust dialog); once you accept, approvals committed in the project count[^cc-trust]. So read
  a cloned project's `.mcp.json` and `.claude/settings.json` before you trust it. But in
  `claude -p` runs (Claude Code started from a script, with no one to answer a prompt), Agent SDK sessions
  (programs built on Anthropic's Agent SDK, a later level of this course) and cloud sessions (Claude Code
  running on a remote machine), Claude Code loads the project's servers without asking[^cc-noprompt]:
  read a project's `.mcp.json` before you run Claude Code on it unattended.

**Using a server's tools**

Once a server is connected, Claude can call its tools like any other tool, and you see a permission
prompt for them as for other actions[^perm-prompts]. Claude Code names each tool
`mcp__<server>__<tool>`[^perm-mcp].

Permission rules, which you met in the lesson on setting up Claude Code, come in three kinds. An `allow`
rule lets Claude use a tool without asking you, an `ask` rule makes Claude Code ask every time, and a
`deny` rule stops Claude from using the tool[^perm-kinds]. Deny rules are checked first and
win[^perm-order]. Rules live in Claude Code's `settings.json` files, and `/permissions` lists them
all[^perm-files]; rules for all your projects go in `~/.claude/settings.json`[^perm-user].

A rule can name a server's tools: `mcp__files` and `mcp__files__*` match every tool of the `files`
server, and `mcp__files__read_file` matches one tool[^perm-mcp]. In a deny or ask rule, a `*` in the tool
name stands for any text, so `mcp__*` matches every MCP tool[^perm-glob]. In an allow rule, a `*` in an
MCP tool name may only come after `mcp__<server>__`, as in `mcp__files__*`: an allow rule `mcp__*` is
skipped and approves nothing[^perm-allow-glob]. This setting lets Claude use every tool of the `files`
server without asking:

```json
{"permissions": {"allow": ["mcp__files__*"]}}
```

And this one refuses every MCP tool[^perm-deny]:

```json
{"permissions": {"deny": ["mcp__*"]}}
```

A deny rule stops Claude's tool calls. It does not stop a local server's own command, which already ran
when the server started.

## Try it

### Without Claude Code: read a `.mcp.json`

`exercise/tests/sample_mcp.json` is a made-up project file with five servers. This script starts
nothing: it prints what each server would run or reach, with variables filled in from a pretend
environment. Save it as `read_mcp_json.py` in the lesson folder and run `python3 read_mcp_json.py` from
that folder:

```python
"""Read a .mcp.json file and say what each server would run or reach. Nothing is started."""
import json
import re
from pathlib import Path

config = json.loads(Path("exercise/tests/sample_mcp.json").read_text(encoding="utf-8"))
environ = {"TICKETS_TOKEN": "tk-demo"}  # a pretend environment: only this one variable is set


def expand(text):
    """Replace ${VAR} and ${VAR:-default}; leave an unset variable with no default as written."""
    def one(match):
        name, default = match.group(1), match.group(2)
        return environ.get(name, default if default is not None else match.group(0))
    return re.sub(r"\$\{(\w+)(?::-([^}]*))?\}", one, text)


for name, entry in config["mcpServers"].items():
    if "command" in entry:
        line = " ".join(expand(word) for word in [entry["command"], *entry.get("args", [])])
        print(f"{name}: runs on your computer: {line}")
    else:
        kind = entry.get("type", "NO TYPE")
        print(f"{name}: connects to {expand(entry['url'])} ({kind})")
    for key, value in entry.get("headers", {}).items():
        print(f"    sends the header {key}: {expand(value)}")
```

The pattern `\$\{(\w+)(?::-([^}]*))?\}` finds `${`, a name, an optional `:-` with a default, and `}`.
`re.sub(pattern, one, text)` calls the function `one` for each `${...}` it finds, and puts in whatever
`one` returns; `match.group(0)` is the whole `${...}`, `match.group(1)` the variable's name and `match.group(2)` its default, or `None`.
In `[entry["command"], *entry.get("args", [])]`, the `*` puts the items of the args list into the new list,
after the command.

The output shows that 2 of the 5 servers run a command on your computer. Read each line as a reviewer
would. `files` is a known server limited to one folder. `crm` has its token written in the file, where
everyone with the project can read it. `wiki` has no `type`, so Claude Code would not connect it.
`helper` downloads a script from the internet with `curl` and runs it with `sh` (a shell, like Bash): do not connect it until
you know exactly what that script does.

### With Claude Code (optional)

This part uses a real server and Claude Code, so it needs Node.js, and the requests Claude makes use your
Claude Code plan or are billed to your API key. Make a small folder for the server to use, with nothing
private in it:

```bash
mkdir -p ~/mcp-sandbox
echo "Remember to water the plants." > ~/mcp-sandbox/note.txt
claude mcp add --transport stdio files -- npx -y @modelcontextprotocol/server-filesystem ~/mcp-sandbox
claude mcp list
```

Start `claude --permission-mode manual`, so that Claude Code asks before it uses a tool, as in the lesson on
setting up Claude Code. Type `/mcp` to see the server and its tools, then ask: `Use the files server to
read note.txt in ~/mcp-sandbox.` Watch which tool Claude calls (its name starts with `mcp__files__`),
and read the permission prompt before you answer it. Without the words "the files server", Claude may
read the file with its own tools instead. When you are done, remove the server with `claude mcp remove files`.

## Common mistakes

- **Writing a secret token in `.mcp.json`.** The file is shared through git. Use `${NAME}` and keep the value in
  your environment[^cc-env-syntax].
- **A `url` with no `type`.** Claude Code reads it as a stdio server and reports a configuration
  error[^cc-notype]. Add `"type": "http"`.
- **Forgetting `--` before a local server's command.** Without it, Claude Code tries to read the server's
  own options, such as `--port`, as its own[^cc-nodash].
- **"Local scope means a local server."** Scope says where the setting is stored and who shares it; the
  transport says how Claude Code reaches the server[^cc-scopes].
- **Expecting scopes to merge.** The whole entry comes from one scope: local, then project, then
  user[^cc-precedence].
- **"It is on a list of servers, so it is safe."** Check what it runs, who wrote it and what it can
  reach[^cc-verify]. A local server has your permissions[^local-perms].
- **Giving a server more than it needs.** One folder, a read-only user, only the tools you
  use. A read-only database user, for example, cannot change data[^cc-readonly]. Deny the tools you do not want with permission rules[^perm-mcp].
- **"Claude Code always asks before loading a project's servers."** Not in `claude -p` runs, Agent SDK
  sessions or cloud sessions[^cc-noprompt], and not once you trust a folder whose committed settings approve
  them[^cc-trust].

## Your exercise

### What to build

Open `exercise/starter/mcp_setup.py` and write six functions. They work offline on plain Python values;
nothing runs Claude Code or a server.

- `add_command(name, url=..., command=..., args=..., scope=..., env=...)` returns the `claude mcp add`
  command as a list of words, always with `--transport` and `--scope` before the name: `--transport http` and the URL for a remote server, or `--transport stdio`,
  `--env` pairs after the name, `--` and the command for a local one. It raises `ValueError` for an
  unknown scope, for both or neither of `url` and `command`, or for `env` with a `url`.
- `expand(text, environ)` fills in `${NAME}` and `${NAME:-default}` and returns the text and a list of the
  names that were missing. A missing name with no default stays as written.
- `pick(local, project, user)` returns, for each server name, the scope and the entry Claude Code uses.
- `tool_name(server, tool)` returns the name Claude Code gives the tool, and `rule_matches(rule, server,
  tool)` says whether a permission rule such as `mcp__files` or `mcp__*` matches it. It does not check
  whether the rule is an allow or a deny rule. Python's standard module `fnmatch` compares a name with a
  pattern that holds `*`.
- `review(config)` reads a `.mcp.json` and returns what to check, as `(server, kind)` pairs: `no-type`,
  `not-https` (a remote URL that does not start with `https://`; a URL that starts with `${` is skipped, since its
  value is only known later), `secret` (a header or `env` value whose
  name looks like a secret, written without `${...}`), and `command` (a local command with `sudo`,
  `rm -rf`, `curl` or `wget` (both download from the internet), `&&`, `|` or `;`).

`review` is a first filter, not a security check. It cannot tell a safe command from a harmful one: it
only points at what a person must read.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

The tests fail until your functions work. A solution is in `exercise/solution/`: try first, then compare.

## Check yourself

Take the quiz for this lesson. If a question is hard, read the scopes table and the four trust questions
again.

[^cc-http]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-stdio]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-dashdash]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^local-node]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^local-npx]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^local-dirs]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^cc-env-order]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-manage]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-status]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-scopes]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-local]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-project]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-notype]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-precedence]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-syntax]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-why]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-env-unset]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-verify]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^hc-untrusted2]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^sec-local]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^local-perms]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^sec-startup]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^sec-patterns]: Security Best Practices, <https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices>
[^spec-safety]: MCP specification, <https://modelcontextprotocol.io/specification/2026-07-28>
[^cc-readonly]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-approve]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-clone]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-noprompt]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-nodash]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-mcp]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-env-locations]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-bearer]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^mdn-https]: HTTPS, MDN Web Docs, <https://developer.mozilla.org/en-US/docs/Glossary/HTTPS>
[^local-start]: Connect to local MCP servers, <https://modelcontextprotocol.io/docs/develop/connect-local-servers>
[^perm-prompts]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-files]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-env-flag]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^cc-scope-flag]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-user]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-kinds]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-order]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^cc-trust]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^perm-glob]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-allow-glob]: Configure permissions, <https://code.claude.com/docs/en/permissions>
[^perm-deny]: Configure permissions, <https://code.claude.com/docs/en/permissions>
