"""Build a clear prompt from its parts, each part in its own XML tag.

Fill in build_prompt. Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""


def build_prompt(task, context="", examples=(), output_format=""):
    """Return a prompt with the task, context, examples and output format in separate XML tags.

    - task (str): what Claude should do. Required: an empty or blank task raises ValueError.
    - context (str): what Claude needs to know and does not. Optional.
    - examples (list of str): sample inputs with their answers. Optional.
    - output_format (str): the shape the answer must have. Optional.

    Each non-empty part, with surrounding spaces removed, goes in its own tag, in this order:
    <task>, <context>, <examples> (one <example> per example inside it), <output_format>.
    A tag sits on its own line, before and after its content. Parts are separated by one blank line.
    Empty or blank parts, and blank examples, are left out entirely.
    """
    raise NotImplementedError("write build_prompt")
