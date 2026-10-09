"""When a tool fails: report the failure to Claude in a tool_result, never crash the loop."""
import json

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
    """Return a list of problems with the input Claude sent for a tool; an empty list means it is fine."""
    schema = tool["input_schema"]
    props = schema.get("properties", {})
    problems = [f"missing required field '{name}'" for name in schema.get("required", []) if name not in args]
    for name, value in args.items():
        if name not in props:
            if schema.get("additionalProperties") is False:
                problems.append(f"field '{name}' is not allowed")
            continue
        kind = props[name].get("type")
        if kind in JSON_TYPES and not JSON_TYPES[kind](value):
            problems.append(f"field '{name}' must be a {kind}")
    return problems


def run_one(call, tools, functions):
    """Run one tool call and return its tool_result block. Never raises."""
    def error(text):
        return {"type": "tool_result", "tool_use_id": call["id"], "content": text, "is_error": True}

    by_name = {tool["name"]: tool for tool in tools}
    name = call["name"]
    available = sorted(n for n in by_name if n in functions)
    if name not in available:
        return error(f"Unknown tool '{name}'. Available tools: {', '.join(available)}.")
    problems = check_input(by_name[name], call["input"])
    if problems:
        return error(f"Invalid input for {name}: {'; '.join(problems)}. Call it again with a corrected input.")
    try:
        result = functions[name](**call["input"])
    except ToolError as failure:
        return error(str(failure))
    except Exception as failure:  # any other failure: say what kind, keep the details out
        return error(f"{name} failed with an internal error ({type(failure).__name__}). "
                     "Do not guess the result: tell the user it is not available right now.")
    text = result if isinstance(result, str) else json.dumps(result)
    return {"type": "tool_result", "tool_use_id": call["id"], "content": text}


def tool_results(response, tools, functions):
    """Return the user message with one tool_result per tool_use block of the reply, in order."""
    calls = [block for block in response["content"] if block.get("type") == "tool_use"]
    return {"role": "user", "content": [run_one(call, tools, functions) for call in calls]}
