"""Get JSON you can trust: check a reply against a schema before you use it.

Write validate(), parse_reply() and ask_until_valid(). Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""
import json  # noqa: F401  (parse_reply needs it)

# What each JSON Schema "type" accepts in Python. True and False are not numbers here.
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
    """Return a list of problems, one string per problem; an empty list means the value is valid.

    Support these schema keywords:
      "type"                  one of the names in TYPES; if it does not match, report only that
      "enum"                  the value must be one of the listed values; compare strings ignoring case
      "minimum", "maximum"    for numbers
      "properties"            check each field that has a schema, at where + "." + name
      "required"              each listed field must be present
      "additionalProperties"  when False, a field not in "properties" is a problem
      "items"                 check each element of an array, at where + "[i]"
    Each problem starts with where it is, for example "$.priority: ...".
    """
    raise NotImplementedError


def parse_reply(response, schema):
    """Return the reply's JSON value, checked against the schema, or raise ReplyError.

    - stop_reason "refusal"    -> ReplyError("refusal", ...)
    - stop_reason "max_tokens" -> ReplyError("cut_off", ...)
    - the text blocks, joined, are not JSON -> ReplyError("not_json", ...)
    - validate() finds problems             -> ReplyError("invalid", ...)
    Otherwise return the value with use_schema_spelling() applied.
    """
    raise NotImplementedError


def ask_until_valid(ask, schema, max_tokens=1024, attempts=3):
    """Call ask(max_tokens) until a reply passes parse_reply, at most `attempts` times.

    A refusal stops at once. A cut-off reply is asked again with twice the max_tokens.
    A reply that is not JSON, or not valid, is asked again unchanged.
    After the last attempt, raise ReplyError("gave_up", ...) with the last problem.
    """
    raise NotImplementedError
