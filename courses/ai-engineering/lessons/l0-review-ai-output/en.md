# Check what Claude changed

## What you will be able to do

- Read a diff: see which files changed, and which lines were added and removed.
- Run the tests yourself, and check that they still test what they tested before.
- Spot the changes that need a closer look before you accept them: files outside the task, changed
  or deleted tests, and skipped tests.

## The idea

In the previous lesson you approved or refused each action. This lesson is about the result: the
change Claude leaves in your files.

Claude stops when the work looks done[^looks-done]. Looking done and being right are not the same.
Anthropic's guide names a common failure: Claude produces a plausible-looking implementation that
doesn't handle edge cases[^trust-gap]. An edge case is an unusual input, such as zero people sharing
a bill. The guide's fix is direct: always provide verification (tests, scripts, screenshots); if you
cannot verify it, do not ship it[^verify].

So before you accept a change, you do two things: you read the diff, and you run the tests.

**A diff.** A diff shows what changed between two versions of a file. `git diff` shows changes
between the working tree and the index[^git-diff]. The working tree is your files as they are now;
the index, also called the staging area, is where `git add` puts the contents of your next
commit[^git-add]. If you have not run `git add` since your last
commit, `git diff` shows everything changed since that commit. Inside Claude Code, the command
`/diff` lets you look over the changes in your working tree without leaving the session[^slash-diff].

Here is part of a diff. The task given to Claude was "make `test_split_needs_people` pass": the test
checks that `split` refuses a bill shared by zero people.

```diff
--- a/tip.py
+++ b/tip.py
@@ -3,4 +3,6 @@
 
 
 def split(total, percent, people):
-    return round((total + tip(total, percent)) / people, 2)
+    if people < 1:
+        raise ValueError("people must be at least 1")
+    return round(total / people + tip(total, percent), 2)
```

Read it from the top:

- `--- a/tip.py` and `+++ b/tip.py` name the old and the new version of the file. A file that was
  created or deleted shows `/dev/null` on one side[^dev-null]. The output of `git diff` also starts
  each file with a line such as `diff --git a/tip.py b/tip.py`[^git-header].
- A line that starts with `@@` opens a hunk: one or more hunks follow, and each shows one area where
  the files differ[^hunks]. The numbers between the `@@` marks say which lines of the old and new
  file the hunk covers[^hunk-header].
- Each line then starts with one character: `-` for a line that was removed, `+` for a line that was
  added, and a space for a line that did not change[^plus-minus].

This change does two things. The two `+` lines that raise `ValueError` are what the task asked for.
But the last line changed too: the old code divided the whole bill, tip included, by the number of
people; the new code divides only the total and then adds the whole tip to each share. Nobody asked
for that. It is the kind of change you find only by reading.

**The tests.** Tests are your check, but a change can touch the tests too. Here is the rest of the
same diff:

```diff
--- a/test_tip.py
+++ b/test_tip.py
@@ -1,6 +1,6 @@
 class TipTest(unittest.TestCase):
     def test_split(self):
-        self.assertEqual(split(100, 10, 4), 27.5)
+        self.assertEqual(split(100, 10, 4), 35.0)
```

`test_split` used to say each person paid 27.5. The new code broke that, and the test was changed to
match: now each person pays 35.0. All the tests pass, and the code is wrong: four people paying that much
each means together they pay 140.0, while the bill with its tip is 110.0. A changed assertion (a
line that checks a result, such as `assertEqual`) is a changed claim about what the code must do.
Ask why it changed.

**What to look for.** Before you accept a change, check:

- **Files outside the task.** Every file in the diff should have a reason to be there.
- **Changed or deleted tests.** A `-` line in a test file can remove a check. Read it.
- **Skipped tests.** `@unittest.skip` above a test skips it: the test no longer runs[^skip].
- **Errors hidden instead of fixed.** The guide asks Claude to address the root cause, not suppress
  the error[^root-cause]. A new `try` and `except` that swallows an error is worth a question.

Then run the tests yourself, and read their output. If you ask Claude whether the tests pass, have
it show evidence rather than assert success: the test output, the command it ran and what it
returned[^evidence].

**If the change is wrong.** Tell Claude what is wrong, or throw the change away. `git restore`
restores files in the working tree from a restore source[^git-restore]: `git restore tip.py` puts
back the version git has for `tip.py` (the one in the index, which is your last commit if you have
not run `git add` since).

## Try it

This script builds the diff above with Python's `difflib`, so you can see the format without a
session or a repository. Unified diffs are a compact way of showing just the lines that have changed
plus a few lines of context[^difflib], and `git diff` uses the same `+`, `-` and space markers.

Save it as `see_the_diff.py` and run `python3 see_the_diff.py`:

```python
"""Show what a change did to two files, in the same format as git diff."""
import difflib

before = {
    "tip.py": '''def tip(total, percent):
    return round(total * percent / 100, 2)


def split(total, percent, people):
    return round((total + tip(total, percent)) / people, 2)
''',
    "test_tip.py": '''class TipTest(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split(100, 10, 4), 27.5)

    def test_split_needs_people(self):
        with self.assertRaises(ValueError):
            split(100, 10, 0)
''',
}

# The task was: "make test_split_needs_people pass". This is the change that came back.
after = {
    "tip.py": '''def tip(total, percent):
    return round(total * percent / 100, 2)


def split(total, percent, people):
    if people < 1:
        raise ValueError("people must be at least 1")
    return round(total / people + tip(total, percent), 2)
''',
    "test_tip.py": '''class TipTest(unittest.TestCase):
    def test_split(self):
        self.assertEqual(split(100, 10, 4), 35.0)

    def test_split_needs_people(self):
        with self.assertRaises(ValueError):
            split(100, 10, 0)
''',
}

for name in before:
    lines = difflib.unified_diff(
        before[name].splitlines(keepends=True),
        after[name].splitlines(keepends=True),
        fromfile=f"a/{name}",
        tofile=f"b/{name}",
    )
    print("".join(lines))
```

It prints the two parts of the diff from "The idea", with a few unchanged lines after the assertion.
Now change `after` yourself: put back the old `return` line in `tip.py`, and the old value in
`test_tip.py`. Run the script again. Only the lines the task needed are left.

In your own project, after a session, run `git diff` (or `/diff` inside Claude Code), then
`python3 -m unittest`, and read both before you commit.

## Common mistakes

**"The tests pass, so the change is right."** Tests pass when the code matches the tests. If the
tests changed too, read how. In the example, every test passes and the code is wrong.

**"Claude said the tests pass."** A sentence is not a test run. Ask for the output, or run the tests
yourself[^evidence].

**"Only the `+` lines matter."** The `-` lines show what is gone. A removed assertion or a removed
check is a change in behaviour.

**"More changes means more work done."** A file outside the task is a question, not a bonus. Ask why
it changed, or refuse it.

**"Accepting edits automatically means I skip the review."** The docs suggest `acceptEdits` mode for
when you want to review changes in your editor or with `git diff` after the fact, rather than
approving each edit as it happens[^accept-edits]. The review moves; it does not go away.

**"I can always rewind."** Checkpoints track only the changes made through Claude's file editing
tools; changes made by shell commands are not captured, and checkpoints are not a replacement for
git[^not-git]. Commit before a session, and you can always get back to that point.

**"A review tool replaces my review."** Claude Code has a `/code-review` command that checks the
current diff for correctness bugs[^code-review]. It is useful, and it is also a model: it can miss
things. It does not know what you meant to ask for. You do.

## Your exercise

Open `exercise/starter/diff_review.py`. You write two functions that read the text `git diff`
prints.

### What to build

`parse_diff(text)` returns a dictionary with one entry per file, in the order the files appear. Each
entry maps the file's path (without the `a/` or `b/` prefix) to a dictionary:

- `"status"`: `"added"` when the old side is `/dev/null`, `"deleted"` when the new side is
  `/dev/null`, otherwise `"modified"`;
- `"added"`: the lines added, without their leading `+`;
- `"removed"`: the lines removed, without their leading `-`.

Header lines (`diff --git`, `index`, `---`, `+++`, `@@`) are not content. Careful: a removed line
whose text starts with `--` is printed as `---`, so it looks like a header. Use the `@@` line: it
gives, for each side, where the hunk starts and how many lines it has, as `-start,count +start,count`.
If a hunk contains just one line, only its start line number appears[^hunk-one]: the count is then
one. Count the lines as you read them, and you always know when the hunk ends.

`red_flags(text, task_files)` returns a list of `(path, reason)` pairs, in the order of the files,
and for each file in this order of reasons:

- `"outside the task"`: the path is not in `task_files`;
- `"test deleted"`: a test file was deleted;
- `"assertion changed"`: a removed line in a test file contains `assert`;
- `"test skipped"`: an added line contains `unittest.skip`, `skipTest(` or `mark.skip`.

A test file is one whose name starts with `test_` or ends with `_test.py`.

### Run the tests

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

They fail until your functions are right. A solution is in `exercise/solution/`; try on your own
first. Then use it on a real change: after a Claude Code session, run
`git diff > change.diff` and pass the text of `change.diff` to `red_flags`. A flag is a reason to
read closely. No flag does not mean the change is right: read the diff anyway.

## Check yourself

Answer the questions in `quiz.json`. If they are hard, read the two diffs in "The idea" again, line
by line.

[^looks-done]: Claude Code docs, Best practices for Claude Code.
[^trust-gap]: Claude Code docs, Best practices for Claude Code.
[^verify]: Claude Code docs, Best practices for Claude Code.
[^git-diff]: Git documentation, git-diff.
[^slash-diff]: Claude Code docs, Interactive mode.
[^dev-null]: Git documentation, git-diff.
[^git-header]: Git documentation, git-diff.
[^hunks]: GNU diffutils manual, Detailed Description of Unified Format.
[^hunk-header]: GNU diffutils manual, Detailed Description of Unified Format.
[^plus-minus]: Git documentation, git-diff.
[^root-cause]: Claude Code docs, Best practices for Claude Code.
[^evidence]: Claude Code docs, Best practices for Claude Code.
[^git-restore]: Git documentation, git-restore.
[^difflib]: Python documentation, difflib.
[^accept-edits]: Claude Code docs, Choose a permission mode.
[^not-git]: Claude Code docs, Best practices for Claude Code.
[^code-review]: Claude Code docs, Commands.
[^git-add]: Git documentation, git-add.
[^skip]: Python documentation, unittest.
[^hunk-one]: GNU diffutils manual, Detailed Description of Unified Format.
