"""Decide, as you would at a Claude Code permission prompt, which actions ask first and what to answer."""

# Bash commands Claude Code treats as read-only (from its permissions page; git is left out here).
READ_ONLY_COMMANDS = {
    "ls", "cat", "echo", "pwd", "head", "tail", "grep", "find",
    "wc", "which", "diff", "stat", "du", "cd",
}

# Characters that join, redirect or nest commands: a command that has one is not one simple command.
JOINERS = (";", "&", "|", ">", "<", "`", "$(", "\n")

READ_TOOLS = {"Read", "Grep", "Glob"}
EDIT_TOOLS = {"Edit", "Write"}


def is_read_only(command):
    """True when the command is one simple command whose program is in READ_ONLY_COMMANDS."""
    command = command.strip()
    if not command or any(joiner in command for joiner in JOINERS):
        return False
    return command.split()[0] in READ_ONLY_COMMANDS


def asks_first(action):
    """Return True when Manual mode would ask before this action runs."""
    tool = action.get("tool")
    if tool in READ_TOOLS:
        return False
    if tool == "Bash":
        return not is_read_only(action.get("command", ""))
    return True


def answer(action, task_files, expected_commands):
    """Return "no prompt", "yes" or "no": what you answer when Claude asks to take this action."""
    if not asks_first(action):
        return "no prompt"
    tool = action.get("tool")
    if tool in EDIT_TOOLS:
        return "yes" if action.get("file") in task_files else "no"
    if tool == "Bash":
        return "yes" if action.get("command", "").strip() in expected_commands else "no"
    return "no"
