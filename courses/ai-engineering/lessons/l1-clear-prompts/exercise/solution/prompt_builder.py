"""Build a clear prompt from its parts, each part in its own XML tag."""


def tag(name, text):
    """Wrap text in <name> ... </name>, the tags on their own lines."""
    return f"<{name}>\n{text}\n</{name}>"


def build_prompt(task, context="", examples=(), output_format="", input_text=""):
    """Return a prompt with the task, context, examples, output format and input in separate XML tags."""
    task = task.strip()
    if not task:
        raise ValueError("a prompt needs a task")
    parts = [tag("task", task)]
    if context.strip():
        parts.append(tag("context", context.strip()))
    kept = [example.strip() for example in examples if example.strip()]
    if kept:
        parts.append(tag("examples", "\n".join(tag("example", example) for example in kept)))
    if output_format.strip():
        parts.append(tag("output_format", output_format.strip()))
    if input_text.strip():
        parts.append(tag("input", input_text.strip()))
    return "\n\n".join(parts)
