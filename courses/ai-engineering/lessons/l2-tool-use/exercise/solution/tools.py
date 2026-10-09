"""Give Claude a tool: define it, read Claude's call, return the result, and run the loop."""
import json
import re

TOOL_NAME = re.compile(r"^[a-zA-Z0-9_-]{1,128}$")


def define_tool(name, description, properties, required=()):
    """Return a tool definition for the "tools" list of a Messages API request."""
    if not isinstance(name, str) or not TOOL_NAME.match(name):
        raise ValueError(f"bad tool name {name!r}: use letters, digits, _ or -, at most 128")
    if not description or not description.strip():
        raise ValueError("a tool needs a description")
    unknown = [field for field in required if field not in properties]
    if unknown:
        raise ValueError(f"required fields not in properties: {unknown}")
    return {
        "name": name,
        "description": description,
        "input_schema": {"type": "object", "properties": dict(properties), "required": list(required)},
    }


def tool_calls(response):
    """Return the tool calls in a reply, in order, as dicts with id, name and input."""
    return [{"id": block["id"], "name": block["name"], "input": block["input"]}
            for block in response["content"] if block.get("type") == "tool_use"]


def tool_results(response, functions):
    """Run each tool Claude asked for and return the user message that carries the results."""
    content = []
    for call in tool_calls(response):
        result = functions[call["name"]](**call["input"])
        text = result if isinstance(result, str) else json.dumps(result)
        content.append({"type": "tool_result", "tool_use_id": call["id"], "content": text})
    return {"role": "user", "content": content}


def run_tool_loop(ask, question, tools, functions, max_rounds=5):
    """Ask, run the tools Claude calls, send the results back, until Claude stops calling tools.

    ask(messages, tools) stands in for the API call and returns a reply as a dict.
    Return (answer_text, messages): messages is the whole conversation, ending with Claude's final reply.
    If Claude still calls a tool after max_rounds rounds of tool calls, raise RuntimeError.
    """
    messages = [{"role": "user", "content": question}]
    for rounds in range(max_rounds + 1):
        response = ask(messages, tools)
        if response["stop_reason"] != "tool_use":
            text = "".join(b["text"] for b in response["content"] if b.get("type") == "text")
            return text, messages + [{"role": "assistant", "content": response["content"]}]
        if rounds == max_rounds:
            break
        messages = messages + [{"role": "assistant", "content": response["content"]},
                               tool_results(response, functions)]
    raise RuntimeError(f"still calling tools after {max_rounds} rounds")
