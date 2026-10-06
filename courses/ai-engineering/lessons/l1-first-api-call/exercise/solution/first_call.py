"""Your first API call, offline: build a Messages API request and read the reply."""

ROLES = ("user", "assistant")


def build_request(model, max_tokens, turns, system=None):
    """Return the request body for the Messages API.

    turns: a list of (role, text) pairs, oldest first; role is "user" or "assistant".
    system: the system prompt, or None to leave it out.
    max_tokens must be at least 1: the course's rule for a request that should produce an answer
    (the API itself also accepts 0, which fills the prompt cache and generates no answer).
    """
    if isinstance(max_tokens, bool) or not isinstance(max_tokens, int) or max_tokens < 1:
        raise ValueError("max_tokens must be a whole number of at least 1")
    if not turns:
        raise ValueError("a request needs at least one turn")
    messages = []
    for role, text in turns:
        if role not in ROLES:
            raise ValueError(f"unknown role {role!r}: use 'user' or 'assistant'")
        messages.append({"role": role, "content": text})
    if messages[-1]["role"] != "user":
        raise ValueError("the last turn must come from the user")
    body = {"model": model, "max_tokens": max_tokens, "messages": messages}
    if system:
        body["system"] = system
    return body


def _result(text, stop_reason, input_tokens, output_tokens):
    return {
        "text": text,
        "stop_reason": stop_reason,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cut_off": stop_reason == "max_tokens",
    }


def read_reply(response):
    """Return the answer's text, why it stopped, its token usage, and whether it was cut off."""
    text = "".join(block["text"] for block in response["content"] if block.get("type") == "text")
    usage = response["usage"]
    return _result(text, response["stop_reason"], usage["input_tokens"], usage["output_tokens"])


def join_stream(events):
    """Return the same summary as read_reply, built from a list of streaming events."""
    pieces, stop_reason, input_tokens, output_tokens = [], None, 0, 0
    for event in events:
        kind = event.get("type")
        if kind == "message_start":
            usage = event["message"].get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
        elif kind == "content_block_delta" and event["delta"].get("type") == "text_delta":
            pieces.append(event["delta"]["text"])
        elif kind == "message_delta":
            stop_reason = event["delta"].get("stop_reason") or stop_reason
            # the counts in message_delta are running totals: keep the latest, do not add them up
            output_tokens = event.get("usage", {}).get("output_tokens", output_tokens)
        # ping and any event type we do not know: ignore
    return _result("".join(pieces), stop_reason, input_tokens, output_tokens)
