# What MCP is

## What you will be able to do

- Explain what MCP is for, and what the host, the client and the server each do.
- Tell tools, resources and prompts apart, and say who decides when each one is used.
- Follow the messages between a client and a server, say how the two transports carry them, and turn a
  server's tools and results into the tool definitions and `tool_result` blocks of the last two lessons.

## The idea

In the last lessons you wrote each tool yourself: its definition, the function that runs it, and the
code that sends its result back. Now picture ten applications that each want to reach your shop's orders.
Each one would write that code again.

**MCP** (Model Context Protocol) is an open-source standard for connecting AI applications to outside
systems[^intro-what]. A *protocol* is an agreed set of rules for how two programs talk. A *standard* is
one agreed way of doing something. *Open-source* means its text and code are public, and anyone may use
them. Its own documentation compares it to a USB-C port: one standard way to plug things
in[^intro-usb]. A shop can write its order lookup once, as an MCP server, and every application that
speaks MCP can use it.

**Host, client, server**

MCP names three participants[^arch-roles]:

- The **host** is the AI application, such as Claude Code or Claude Desktop, Anthropic's desktop app. It connects to one or more
  servers[^arch-participants].
- A **client** is the part of the host that keeps the connection to one server. The host creates one
  client for each server[^arch-participants].
- A **server** is a program that provides context to clients[^arch-roles]. It can
  run on your computer or on another machine: "server" names the role, not the place[^arch-where].

So Claude Code connected to two servers holds two clients. The model is not a participant. The server
never talks to Claude: it talks to the client, and the host decides what reaches the model. MCP only
defines how context is exchanged; it does not say how the application uses the model[^arch-scope].

**Tools, resources and prompts**

A server can offer three kinds of things, and each has a different owner, the one who decides when it is
used[^sc-table]:

| Kind | What it is | Who decides |
|---|---|---|
| **Tools** | Functions the model can call, like your `lookup_order` | The model |
| **Resources** | Data to read for context, such as a file or a database's schema (its tables and their columns) | The application |
| **Prompts** | Ready-made instructions for a task, with blanks to fill in[^sc-params] | The user |

The documentation gives an example: a server for a database can offer tools to query it, a resource
that holds its schema, and a prompt with examples of how to use the tools[^arch-db]. In Claude Code, a
server's prompts appear as commands you type, such as `/servername:promptname`[^cc-prompts].

Each kind has its own *methods*, named operations a client can ask a server to run. `tools/list` finds the tools and `tools/call` runs
one[^sc-tools-ops]. `resources/list` lists the resources and `resources/read` reads
one[^sc-resources-ops]. `prompts/list` lists the prompts and `prompts/get` fetches one[^sc-prompts-ops].

**The messages**

Clients and servers exchange **JSON-RPC 2.0** messages[^arch-jsonrpc]. JSON-RPC is a small format for
asking another program to run a method. A request names the version, `"2.0"`, and the `method` to
run[^jsonrpc-request]. It also carries an `id`, and the answer repeats that `id`, so you can tell which
request it answers[^jsonrpc-id]. (A message with no `id` is a *notification*: the other side does not
answer it[^jsonrpc-notify].) The answer holds a `result` when the call worked, or an `error` when it
did not[^jsonrpc-response].

Here the client asks a shop's server for its tools, and the server answers:

```json
{"jsonrpc": "2.0", "id": 1, "method": "tools/list", "params": {}}
```

```json
{"jsonrpc": "2.0", "id": 1, "result": {"resultType": "complete", "tools": [
  {"name": "lookup_order",
   "description": "Look up a customer's order by its order number and return its status.",
   "inputSchema": {"type": "object", "properties": {"order_id": {"type": "string"}}, "required": ["order_id"]}}
]}}
```

A tool has a `name`, a `description` and an `inputSchema`, a JSON Schema for its input[^spec-tool]. It
looks like the tool definitions you wrote, with one difference in spelling: the Claude API calls the
schema `input_schema`[^dt-fields]. To run the tool, the client sends `tools/call` with the tool's `name`
and its `arguments`[^spec-call]. The result holds a `content` list, which can mix several items of
different types[^spec-content]. It can also hold `isError`: more on it below. `"resultType":
"complete"` marks a finished result[^rt-complete]. A server may instead answer that it needs more input before it can
finish the call[^spec-input]; this lesson does not use that.

The current version of MCP is *stateless*. Like the Messages API you met in the last
lessons[^stateless], the server does not have to remember earlier requests. So every request carries what the server needs, including
the protocol version, in a `_meta` field, and the server can handle each request on its
own[^arch-stateless]. The examples here leave `_meta` out, as do the request examples on the
tools page of the MCP *specification*, the official document that sets the protocol's rules[^spec-meta]. A real
request must include it. Older versions started with an `initialize` handshake, an opening exchange that set up a
*session* (a connection that remembers what came before)[^spec-older], so you will still meet it in older guides and servers.

The messages travel over a **transport**. With **stdio**, the client starts the server as a program on
your computer, and they exchange one message per line through its standard input and output (stdin and
stdout: the streams a program reads from and prints to). With **Streamable HTTP**, each message is sent
to the server as an HTTP POST, the kind of request a program uses to send data to a web
address[^spec-transports]. HTTP is the protocol of the web, the one web browsers and web APIs use. A local server on
stdio usually serves one client; a remote server on HTTP usually serves many[^arch-local].

**What the host does with the tools**

The host gathers the tools of all its servers into one list that the model can use[^arch-registry]. When
the model calls one, the host sends the call to the right server and passes the result back to the
model[^arch-route]. The model still sees a tool definition and a `tool_result`, as in the last lessons.

Two servers may each offer a tool named `search`. The specification asks clients to tell them apart, for
example by putting a server name in front of the tool name[^spec-collide]. Names must also fit the API:
MCP allows a dot in a tool name[^spec-names], but a Claude tool name may only hold letters, digits, `_`
and `-`[^dt-fields].

Failures come in two kinds here too. A **protocol error**, such as an unknown tool, comes back as a
JSON-RPC `error` with a number code, such as `-32602`[^spec-errors], JSON-RPC's code for invalid
parameters[^jsonrpc-codes]: the tool's name is one of the parameters of `tools/call`. A **tool execution error**, such as an order that does not exist, comes
back as a normal result with `isError` set to true, and holds feedback the model can use to correct
itself[^spec-errors-exec]. The specification asks clients to pass tool execution errors on to the model. Protocol errors may be
passed on too, but they are less likely to help it recover[^spec-errors-model]. Either way, every `tool_use` block
needs its `tool_result` right after it[^hc-follow], or the next request you send to Claude
fails[^hc-missing]. In this course the host turns both
kinds into a `tool_result` with `is_error`, as in the last lesson[^hc-is-error].

## Try it

This file plays all three parts, with no network and no MCP library. `shop_server` stands in for a
server, `send` is the client, and the rest is the host. A sample `tool_use` block stands in for Claude.
Save it as `host_and_server.py` and run `python3 host_and_server.py`:

```python
"""A host, its client and a server in one file. No network, no key, no MCP library."""
import json

ORDERS = {"A-1042": "shipped"}


def shop_server(message):
    """Stands in for an MCP server: it reads one JSON-RPC request and returns the response."""
    reply = {"jsonrpc": "2.0", "id": message["id"]}
    if message["method"] == "tools/list":
        reply["result"] = {"resultType": "complete", "tools": [{
            "name": "lookup_order",
            "description": "Look up a customer's order by its order number and return its status.",
            "inputSchema": {"type": "object", "properties": {"order_id": {"type": "string"}},
                            "required": ["order_id"]}}]}
    elif message["method"] == "tools/call" and message["params"]["name"] == "lookup_order":
        order_id = message["params"]["arguments"]["order_id"]
        found = order_id in ORDERS
        text = f"Order {order_id}: {ORDERS[order_id]}." if found else f"No order {order_id}."
        reply["result"] = {"resultType": "complete", "content": [{"type": "text", "text": text}],
                           "isError": not found}
    elif message["method"] == "tools/call":
        reply["error"] = {"code": -32602, "message": "Unknown tool: " + message["params"]["name"]}
    else:
        reply["error"] = {"code": -32601, "message": "Method not found"}
    return reply


next_id = 0


def send(method, params):
    """The client: it numbers each request, sends it to its one server, and returns the response."""
    global next_id  # next_id lives outside the function: this line lets send change it
    next_id += 1
    message = {"jsonrpc": "2.0", "id": next_id, "method": method, "params": params}
    print("client ->", json.dumps(message))
    response = shop_server(message)
    print("server ->", json.dumps(response))
    return response


# 1. The client asks the server which tools it has.
listing = send("tools/list", {})
# 2. The host turns them into tool definitions for the Claude API.
tools = [{"name": "shop__" + tool["name"], "description": tool["description"],
          "input_schema": tool["inputSchema"]} for tool in listing["result"]["tools"]]
print("tools for Claude:", [tool["name"] for tool in tools])
# 3. Claude asks for the tool. This sample tool_use block stands in for Claude's reply.
use = {"type": "tool_use", "id": "toolu_sample_01", "name": "shop__lookup_order", "input": {"order_id": "A-1042"}}
# 4. The host sends the call to the server, then turns the answer into a tool_result for Claude.
answer = send("tools/call", {"name": use["name"].removeprefix("shop__"),  # "shop__lookup_order" -> "lookup_order"
                             "arguments": use["input"]})
result = {"type": "tool_result", "tool_use_id": use["id"],
          "content": "\n".join(item["text"] for item in answer["result"]["content"] if item["type"] == "text")}
if answer["result"]["isError"]:
    result["is_error"] = True
print("tool_result for Claude:", json.dumps(result))
```

The output shows each message. Claude sees one tool, `shop__lookup_order`, and never sees a JSON-RPC
message. Change the order number in `use` to `A-999` and run it again: the server answers with `isError`
true, and the `tool_result` gets `is_error`. This demo also calls the tool without asking anyone: a real host
must get the user's consent first[^spec-consent].

A real server is a separate program, and a real host speaks to it through a transport. The lesson
"Connect an MCP server" connects one to Claude Code.

## Common mistakes

- **"MCP replaces tool use."** It does not. The model still sees tool definitions and tool
  results[^arch-route]. MCP standardizes how the application gets tools and data from servers.
- **"The server talks to Claude."** The server talks to a client in the host. The host decides what the
  model sees[^arch-scope].
- **"A server is a remote machine."** A server is a program, wherever it runs[^arch-where]. A stdio
  server runs on your own computer, started by the client[^spec-transports].
- **"Resources and prompts are tools too."** The model decides when to call a tool. The application
  decides which resources to use, and the user picks a prompt[^sc-table].
- **"Every failure is a JSON-RPC error."** An unknown tool is a protocol error. A tool that ran and
  failed returns a result with `isError`, which the model should see so it can correct
  itself[^spec-errors-model].
- **"What a server says about its tools is true."** The specification calls tools arbitrary code
  execution, which means a tool can run any code at all on the machine where the server runs. It says descriptions of tool behavior are untrusted unless the server is
  trusted[^spec-safety]. The host must get the user's consent before it calls a tool[^spec-consent]. The
  lesson on connecting a server comes back to trust.

## Your exercise

### What to build

Open `exercise/starter/mcp_host.py` and write the host's side of MCP, as four functions. The tests use
sample server responses from `exercise/tests/`; nothing runs a real server.

- `request(request_id, method, params)` returns a JSON-RPC request.
- `claude_tools(server, listing, routes)` turns a server's `tools/list` response into Claude tool
  definitions, and returns them with `routes`. Each name becomes the server name (the name the host gave the server), `__`, then the tool's name, with any character the API
  refuses replaced by `_`. It fills `routes`, which maps each new name back to its server and its MCP
  name. It raises `ValueError` for an error response, a name that is too long, or a name already taken.
- `call_request(request_id, tool_use, routes)` turns Claude's `tool_use` block into the server's name
  and a `tools/call` request. It raises `KeyError` for a tool that no server owns.
- `tool_result(tool_use_id, sent, response)` turns the server's response to the request `sent` into a
  `tool_result` block. It raises `ValueError` for a response whose `id` does not match, reports a protocol error with `is_error`, and keeps
  `isError` from a tool execution error. Content items that are not text, such as images, become a
  short note like `[image not shown]`.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

The tests fail until your functions work. A solution is in `exercise/solution/`: try first, then compare.

## Check yourself

Take the quiz for this lesson. If a question is hard, read "Host, client, server" and the table of
tools, resources and prompts again.

[^intro-what]: What is the Model Context Protocol (MCP)?, <https://modelcontextprotocol.io/docs/getting-started/intro>
[^intro-usb]: What is the Model Context Protocol (MCP)?, <https://modelcontextprotocol.io/docs/getting-started/intro>
[^arch-roles]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-participants]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-where]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-scope]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^sc-table]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^arch-db]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^cc-prompts]: Connect Claude Code to tools via MCP, <https://code.claude.com/docs/en/mcp>
[^sc-tools-ops]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^sc-resources-ops]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^sc-prompts-ops]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^arch-jsonrpc]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^jsonrpc-request]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^jsonrpc-id]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^jsonrpc-response]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^spec-tool]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^dt-fields]: Define tools, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/define-tools>
[^spec-content]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-call]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^sc-params]: Understanding MCP servers, <https://modelcontextprotocol.io/docs/learn/server-concepts>
[^arch-stateless]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^spec-meta]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-older]: MCP specification: Transports, <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports>
[^spec-transports]: MCP specification: Transports, <https://modelcontextprotocol.io/specification/2026-07-28/basic/transports>
[^arch-local]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-registry]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^arch-route]: Architecture overview, <https://modelcontextprotocol.io/docs/learn/architecture>
[^spec-collide]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-names]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-errors]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-errors-exec]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^spec-errors-model]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^hc-is-error]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^spec-safety]: MCP specification, <https://modelcontextprotocol.io/specification/2026-07-28>
[^spec-consent]: MCP specification, <https://modelcontextprotocol.io/specification/2026-07-28>
[^spec-input]: MCP specification: Tools, <https://modelcontextprotocol.io/specification/2026-07-28/server/tools>
[^jsonrpc-codes]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^hc-follow]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
[^rt-complete]: MCP specification: Schema Reference, <https://modelcontextprotocol.io/specification/2026-07-28/schema>
[^jsonrpc-notify]: JSON-RPC 2.0 Specification, <https://www.jsonrpc.org/specification>
[^stateless]: Using the Messages API, <https://platform.claude.com/docs/en/build-with-claude/working-with-messages>
[^hc-missing]: Handle tool calls, <https://platform.claude.com/docs/en/agents-and-tools/tool-use/handle-tool-calls>
