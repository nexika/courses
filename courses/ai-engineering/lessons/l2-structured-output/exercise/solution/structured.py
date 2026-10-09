"""Get JSON you can trust: check a reply against a schema before you use it."""
import json

TYPES = {
    "object": lambda v: isinstance(v, dict),
    "array": lambda v: isinstance(v, list),
    "string": lambda v: isinstance(v, str),
    "integer": lambda v: isinstance(v, int) and not isinstance(v, bool),
    "number": lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    "boolean": lambda v: isinstance(v, bool),
    "null": lambda v: v is None,
}


class ReplyError(Exception):
    """A reply that cannot be used. `reason` is refusal, cut_off, not_json, invalid or gave_up."""

    def __init__(self, reason, detail=""):
        super().__init__(f"{reason}: {detail}" if detail else reason)
        self.reason = reason
        self.detail = detail


def use_schema_spelling(value, schema):
    """Return a copy of value where each enum string is spelled exactly as in the schema.

    Structured outputs do not guarantee the capitalization of enum values, so "Bug" becomes "bug".
    (Given: you do not need to change this function.)
    """
    if isinstance(value, dict):
        props = schema.get("properties", {})
        return {k: use_schema_spelling(v, props.get(k, {})) for k, v in value.items()}
    if isinstance(value, list):
        return [use_schema_spelling(v, schema.get("items", {})) for v in value]
    if isinstance(value, str):
        for allowed in schema.get("enum", []):
            if isinstance(allowed, str) and allowed.lower() == value.lower():
                return allowed
    return value


def validate(value, schema, where="$"):
    """Return a list of problems, one string per problem; an empty list means the value is valid."""
    problems = []
    kind = schema.get("type")
    if kind is not None and not TYPES[kind](value):
        return [f"{where}: expected {kind}, got {type(value).__name__}"]
    if "enum" in schema:
        allowed = [a.lower() if isinstance(a, str) else a for a in schema["enum"]]
        probe = value.lower() if isinstance(value, str) else value
        if probe not in allowed:
            problems.append(f"{where}: {value!r} is not one of {schema['enum']}")
    if TYPES["number"](value):
        if "minimum" in schema and value < schema["minimum"]:
            problems.append(f"{where}: {value} is below the minimum {schema['minimum']}")
        if "maximum" in schema and value > schema["maximum"]:
            problems.append(f"{where}: {value} is above the maximum {schema['maximum']}")
    if isinstance(value, dict):
        props = schema.get("properties", {})
        for name in schema.get("required", []):
            if name not in value:
                problems.append(f"{where}.{name}: required field is missing")
        for name, item in value.items():
            if name in props:
                problems += validate(item, props[name], f"{where}.{name}")
            elif schema.get("additionalProperties") is False:
                problems.append(f"{where}.{name}: field not allowed by the schema")
    if isinstance(value, list) and "items" in schema:
        for i, item in enumerate(value):
            problems += validate(item, schema["items"], f"{where}[{i}]")
    return problems


def parse_reply(response, schema):
    """Return the reply's JSON value, checked against the schema, or raise ReplyError."""
    stop = response.get("stop_reason")
    if stop == "refusal":
        raise ReplyError("refusal", "Claude declined; do not retry the same request")
    if stop == "max_tokens":
        raise ReplyError("cut_off", "the reply reached max_tokens; the JSON may be incomplete")
    text = "".join(b["text"] for b in response.get("content", []) if b.get("type") == "text")
    try:
        value = json.loads(text)
    except json.JSONDecodeError as error:
        raise ReplyError("not_json", str(error)) from None
    problems = validate(value, schema)
    if problems:
        raise ReplyError("invalid", "; ".join(problems))
    return use_schema_spelling(value, schema)


def ask_until_valid(ask, schema, max_tokens=1024, attempts=3):
    """Call ask(max_tokens) until a reply passes parse_reply, at most `attempts` times.

    A refusal stops at once. A cut-off reply is asked again with twice the max_tokens.
    A reply that is not JSON, or not valid, is asked again unchanged.
    After the last attempt, raise ReplyError("gave_up", ...) with the last problem.
    """
    last = ""
    for _ in range(attempts):
        try:
            return parse_reply(ask(max_tokens), schema)
        except ReplyError as error:
            if error.reason == "refusal":
                raise
            if error.reason == "cut_off":
                max_tokens *= 2
            last = str(error)
    raise ReplyError("gave_up", last)
