"""Read the text git diff prints, and flag the changes that need a closer look.

Fill in parse_diff and red_flags. Run the tests from this folder with:
    python3 -m unittest discover -s ../tests
"""


def is_test_file(path):
    """True for a test file: its name starts with test_ or ends with _test.py."""
    name = path.rsplit("/", 1)[-1]
    return name.startswith("test_") or name.endswith("_test.py")


def parse_diff(text):
    """Return {path: {"status": ..., "added": [...], "removed": [...]}}, one entry per file, in order.

    - path: the file's path without the a/ or b/ prefix (for a deleted file, the old path).
    - status: "added" when the old side is /dev/null, "deleted" when the new side is /dev/null,
      otherwise "modified".
    - added / removed: the content lines that start with + / -, without that first character.
    Header lines (diff --git, index, ---, +++, @@) are not content.
    Hint: a removed line "-- x" prints as "--- x". The @@ line says how many old and new lines the
    hunk has (@@ -start,count +start,count @@, and a missing count means 1): count them as you read.
    """
    raise NotImplementedError("write parse_diff")


def red_flags(text, task_files):
    """Return a list of (path, reason) pairs: files in diff order, and for each file, reasons in this order.

    - "outside the task": the path is not in task_files.
    - "test deleted": a test file was deleted.
    - "assertion changed": a removed line in a test file contains "assert".
    - "test skipped": an added line contains "unittest.skip", "skipTest(" or "mark.skip".
    """
    raise NotImplementedError("write red_flags")
