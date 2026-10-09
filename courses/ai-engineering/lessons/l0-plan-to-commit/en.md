# From plan to commit

## What you will be able to do

- Use plan mode to have Claude explore the code and propose a plan before it changes anything.
- Give Claude a check it can run, then approve the plan and let it implement the change.
- Review the result and commit one change with a message that says what it does.

## The idea

In the first two lessons you approved actions one at a time and read the diff they left. This lesson
puts them in order, for one whole change.

Letting Claude jump straight to coding can produce code that solves the wrong problem[^wrong-problem].
Anthropic's guide gives the remedy: separate research and planning from implementation[^separate].
The workflow it recommends has four phases[^phases]: **explore**, **plan**, **implement**,
**commit**.

**Plan mode.** Plan mode tells Claude to research and propose changes without making them. Claude
reads files, runs shell commands to explore, and writes a plan, but does not edit your
source[^plan-mode]. Enter it by pressing `Shift+Tab` (until the status bar shows `⏸ plan mode on`), by
starting the session with `claude --permission-mode plan`[^start-plan], or by putting `/plan` in
front of one prompt[^enter-plan].

When the plan is ready, Claude shows it and asks how to proceed. Two of the answers matter here:

- **Yes, manually approve edits**: approve the plan, and review each edit individually[^approve-manual].
- **No, keep planning**: stay in plan mode and tell Claude what to change[^keep-planning].

Approving a plan exits plan mode, and Claude starts editing[^approve-exits]. You can also press
`Ctrl+G` to open the plan in your text editor and change it yourself before Claude goes on[^ctrl-g].

**A check Claude can run.** Before Claude implements anything, give it a way to know when it is
done, such as tests[^check]. The guide's example prompt says it directly:
write a failing test that reproduces the issue, then fix it[^failing-test]. A failing test is a test
that describes what you want and fails today, because the code does not do it yet.

**One change, one commit.** A commit records the current contents of the index with a message that
describes the changes[^git-commit]. Commit one change at a time, with a message that says what
changed and why. If the next change goes wrong, you can always come back to this one.

Here is the whole loop on one example. You want `tip` to refuse a negative percent.

- **Explore and plan**, in plan mode: "read tip.py and test_tip.py; I want tip() to refuse a
  negative percent. Make a plan."
- **Review the plan.** Does it change only `tip.py`? Does it say which error it raises? If not,
  answer **No, keep planning** and say what to change.
- **Implement**: approve with **Yes, manually approve edits**, read each edit, and ask Claude to run
  the tests.
- **Review**: read `git diff` and the test output, as in the previous lesson.
- **Commit**: ask Claude to commit with a descriptive message[^commit-step], read the `git commit`
  command in the permission prompt, and approve it.

**When not to plan.** Plan mode is useful, but also adds overhead[^overhead]: it takes extra time and attention. If you could describe
the diff in one sentence, skip the plan[^one-sentence]. The change above is that small: you plan it
here to practise the steps. Planning is most useful when you are uncertain about the approach, when
the change modifies multiple files, or when you are unfamiliar with the code[^planning-useful].

## Try it

Use the `tip-calc` project from the first lesson. Start Claude Code in Manual mode, as before.

### Write the check first

Save this as `test_tip.py` next to `tip.py`:

```python
import unittest

from tip import tip


class TipTest(unittest.TestCase):
    def test_tip(self):
        self.assertEqual(tip(50, 15), 7.5)

    def test_a_negative_percent_is_refused(self):
        with self.assertRaises(ValueError):
            tip(50, -5)


if __name__ == "__main__":
    unittest.main()
```

Run `python3 -m unittest` in the `tip-calc` folder. The new test fails, because `tip` does not
refuse a negative percent yet:

```text
F.
======================================================================
FAIL: test_a_negative_percent_is_refused (test_tip.TipTest.test_a_negative_percent_is_refused)
----------------------------------------------------------------------
Traceback (most recent call last):
  File ".../tip-calc/test_tip.py", line 11, in test_a_negative_percent_is_refused
    with self.assertRaises(ValueError):
AssertionError: ValueError not raised

----------------------------------------------------------------------
Ran 2 tests in 0.000s

FAILED (failures=1)
```

The exact lines can differ a little with your Python version. Commit the test, so the diff later
shows only Claude's change:

```bash
git add test_tip.py
git commit -m "Test that tip refuses a negative percent"
```

### Plan

In Claude Code, press `Shift+Tab` until the status bar shows `⏸ plan mode on`, then type:

```text
read tip.py and test_tip.py. test_a_negative_percent_is_refused fails. Plan the smallest change to tip.py that makes it pass. Do not change the tests.
```

Read the plan. If it touches a file other than `tip.py`, or changes a test, choose
**No, keep planning** and say so.

### Implement and check

Choose **Yes, manually approve edits**. Read the edit in its permission prompt before you approve it.
Then type:

```text
run python3 -m unittest and show me the output
```

Approve the command. Both tests should pass. Read the output yourself: it is your evidence.

### Review and commit

Run `git diff` in another terminal, or `/diff` in Claude Code. Only `tip.py` should have changed,
and only to refuse a negative percent. Then type:

```text
commit this change with a descriptive message
```

The permission prompt shows the `git commit` command and its message. Approve it if the message says
what changed. Run `git log --oneline` to see your two commits: the test, then the fix.

## Common mistakes

**"Plan mode makes the change safe."** Plan mode keeps Claude from editing your source while it
plans[^plan-mode]. The plan itself can still be wrong. Read it, and correct Claude as soon as you
notice it going off track[^course-correct].

**"Always plan first."** Planning adds overhead[^overhead]. For a change you can describe in one
sentence, skip it[^one-sentence].

**"Approving the plan means approving every edit."** Not with **Yes, manually approve edits**: you
still review each edit[^approve-manual]. The other approve option, **Yes, and use auto mode**, starts auto mode; where auto mode is not
available, it reads **Yes, auto-accept edits**[^approve-auto]. In auto mode, most file edits in your working directory are approved without asking[^auto-edits]. Choose it only when you will review the
diff afterwards.

**"Claude wrote tests, so the change is tested."** Tests written after the code can test what the
code does instead of what you wanted. Write or read the check before the implementation, and look at
test changes in the diff.

**"One commit at the end of the day is enough."** A commit that mixes several changes is hard to
review and hard to undo. Commit each change on its own, once its tests pass and you have read its
diff.

**"Claude committed, so the history is fine."** Read the commit message in the permission prompt.
It should say what changed. If it does not, answer **No**, and say what the message should be.

## Your exercise

### What to build

Open `exercise/starter/bill.py`. Its function `split_bill(total_cents, tip_percent, people)` splits a
bill, tip included, between people in whole cents. Working in cents (integers) avoids the rounding
surprises of decimal numbers: the shares must add up exactly to the bill and its tip. The docstring
says the rules: the tip is rounded to the nearest cent (a half cent rounds up), the cents that do not
divide evenly go one each to the first people, and bad inputs raise `ValueError`. The tests in
`exercise/tests/` are the check.

Take this change from plan to commit with Claude Code:

- Copy `exercise/starter/bill.py` and `exercise/tests/test_bill.py` into a new folder, run
  `git init` there, and commit both files.
- Run `python3 -m unittest` and see the tests fail.
- In plan mode, ask Claude to read both files and plan an implementation of `split_bill` that makes
  the tests pass without changing them. Review the plan. Ask it to keep planning if anything is
  unclear.
- Approve with **Yes, manually approve edits**. Review each edit.
- Have Claude run the tests and show you the output. Read `git diff`: only `bill.py` should change.
- Ask Claude to commit with a descriptive message, and check that message before you approve.

### Run the tests

Your folder holds `test_bill.py`, so run the tests there, after each step:

```bash
python3 -m unittest
```

When they pass, check your `bill.py` with the course's own copy of the tests too: copy it into
`exercise/starter/`, over the stub, and run:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

Both fail until `split_bill` is right. A solution is in `exercise/solution/`; look at it only after
your own commit. The tests check the code, not the way you got there: the plan, the review and the
commit are yours to practise. Your `git log` should end with one commit that changes only `bill.py`.

## Check yourself

Answer the questions in `quiz.json`. If they are hard, read the five steps in "The idea" again.

[^wrong-problem]: Claude Code docs, Best practices for Claude Code.
[^separate]: Claude Code docs, Best practices for Claude Code.
[^phases]: Claude Code docs, Best practices for Claude Code.
[^plan-mode]: Claude Code docs, Choose a permission mode.
[^start-plan]: Claude Code docs, Best practices for Claude Code.
[^enter-plan]: Claude Code docs, Choose a permission mode.
[^approve-manual]: Claude Code docs, Choose a permission mode.
[^keep-planning]: Claude Code docs, Choose a permission mode.
[^approve-exits]: Claude Code docs, Choose a permission mode.
[^ctrl-g]: Claude Code docs, Choose a permission mode.
[^check]: Claude Code docs, Best practices for Claude Code.
[^failing-test]: Claude Code docs, Best practices for Claude Code.
[^git-commit]: Git documentation, git-commit.
[^commit-step]: Claude Code docs, Best practices for Claude Code.
[^overhead]: Claude Code docs, Best practices for Claude Code.
[^one-sentence]: Claude Code docs, Best practices for Claude Code.
[^planning-useful]: Claude Code docs, Best practices for Claude Code.
[^course-correct]: Claude Code docs, Best practices for Claude Code.
[^approve-auto]: Claude Code docs, Choose a permission mode.
[^auto-edits]: Claude Code docs, Choose a permission mode.
