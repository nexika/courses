"""Decide, as you would at a Claude Code permission prompt, which actions ask first and what to answer.

Fill in asks_first and answer. Run the tests from this folder with:
    python3 -m unittest discover -s ../tests

An action is a dictionary:
    {"tool": "Read", "file": "tip.py"}
    {"tool": "Edit", "file": "tip.py"}
    {"tool": "Bash", "command": "python3 tip.py"}
"""

# Bash commands Claude Code treats as read-only (from its permissions page; git is left out here).
READ_ONLY_COMMANDS = {
    "ls", "cat", "echo", "pwd", "head", "tail", "grep", "find",
    "wc", "which", "diff", "stat", "du", "cd",
}

# Characters that join, redirect or nest commands: a command that has one is not one simple command.
JOINERS = (";", "&", "|", ">", "<", "`", "$(", "\n")


def asks_first(action):
    """Return True when Manual mode would ask before this action runs.

    - Read, Grep and Glob never ask.
    - Edit and Write always ask.
    - Bash asks, unless the command is one simple command (none of JOINERS in it)
      whose program (its first word) is in READ_ONLY_COMMANDS.
    - Any other tool asks.
    """
    raise NotImplementedError("write asks_first")


def answer(action, task_files, expected_commands):
    """Return "no prompt", "yes" or "no": what you answer when Claude asks to take this action.

    - "no prompt" when asks_first(action) is False.
    - Edit or Write: "yes" when action["file"] is in task_files, otherwise "no".
    - Bash: "yes" when the command, without the spaces around it, is in expected_commands,
      otherwise "no".
    - Any other tool: "no".
    """
    raise NotImplementedError("write answer")
