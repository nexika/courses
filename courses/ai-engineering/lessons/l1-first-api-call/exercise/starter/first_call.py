"""Your first API call, offline: build a Messages API request and read the reply.

Fill in the three functions. Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""

ROLES = ("user", "assistant")


def build_request(model, max_tokens, turns, system=None):
    """Return the request body for the Messages API, as a dict.

    turns: a list of (role, text) pairs, oldest first; role is "user" or "assistant".
    system: the system prompt, or None to leave it out.

    The body has "model", "max_tokens" and "messages" (a list of {"role": ..., "content": ...}),
    plus "system" only when a system prompt is given.
    Raise ValueError when max_tokens is not a whole number of at least 1, when there are no turns,
    when a role is not "user" or "assistant", or when the last turn is not from the user.
    """
    raise NotImplementedError


def read_reply(response):
    """Return a dict with:
    "text": the text of every block whose type is "text", joined together;
    "stop_reason": the response's stop_reason;
    "input_tokens" and "output_tokens": from the response's usage;
    "cut_off": True when the reply stopped because it reached max_tokens.
    """
    raise NotImplementedError


def join_stream(events):
    """Return the same dict as read_reply, built from a list of streaming events.

    Text arrives in content_block_delta events whose delta has type "text_delta".
    input_tokens comes from message_start; stop_reason and output_tokens from message_delta
    (its counts are running totals, so keep the latest). Ignore any other event.
    """
    raise NotImplementedError
