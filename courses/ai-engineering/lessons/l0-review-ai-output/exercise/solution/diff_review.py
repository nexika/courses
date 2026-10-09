"""Read the text git diff prints, and flag the changes that need a closer look."""
import re

SKIP_MARKS = ("unittest.skip", "skipTest(", "mark.skip")
HUNK = re.compile(r"^@@ -\d+(?:,(\d+))? \+\d+(?:,(\d+))? @@")


def is_test_file(path):
    """True for a test file: its name starts with test_ or ends with _test.py."""
    name = path.rsplit("/", 1)[-1]
    return name.startswith("test_") or name.endswith("_test.py")


def _path(side):
    """The path named on a --- or +++ line, without its a/ or b/ prefix; None for /dev/null."""
    side = side.split("\t")[0].strip()
    if side == "/dev/null":
        return None
    return side[2:] if side.startswith(("a/", "b/")) else side


def parse_diff(text):
    """Return {path: {"status": ..., "added": [...], "removed": [...]}}, one entry per file, in order."""
    files, current = {}, None
    old_left = new_left = 0  # lines still to read in the current hunk, from its @@ header
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if old_left or new_left:
            if line.startswith("+"):
                current["added"].append(line[1:])
                new_left -= 1
            elif line.startswith("-"):
                current["removed"].append(line[1:])
                old_left -= 1
            elif not line.startswith("\\"):  # "\ No newline at end of file" counts for nothing
                old_left, new_left = old_left - 1, new_left - 1
        elif line.startswith("--- ") and i + 1 < len(lines) and lines[i + 1].startswith("+++ "):
            old, new = _path(line[4:]), _path(lines[i + 1][4:])
            status = "added" if old is None else "deleted" if new is None else "modified"
            current = files[new or old] = {"status": status, "added": [], "removed": []}
            i += 1
        elif current is not None and HUNK.match(line):
            counts = HUNK.match(line)
            old_left = int(counts.group(1) or 1)
            new_left = int(counts.group(2) or 1)
        i += 1
    return files


def red_flags(text, task_files):
    """Return a list of (path, reason) pairs: files in diff order, and for each file, reasons in this order."""
    flags = []
    for path, change in parse_diff(text).items():
        test = is_test_file(path)
        if path not in task_files:
            flags.append((path, "outside the task"))
        if test and change["status"] == "deleted":
            flags.append((path, "test deleted"))
        if test and any("assert" in line for line in change["removed"]):
            flags.append((path, "assertion changed"))
        if any(mark in line for line in change["added"] for mark in SKIP_MARKS):
            flags.append((path, "test skipped"))
    return flags
