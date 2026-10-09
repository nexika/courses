# Set up Claude Code and approve its actions

## What you will be able to do

- Install Claude Code and start a session in a project folder.
- Ask Claude Code to read and explain code, then to change it.
- Tell which actions Claude Code asks you about, and approve or refuse each one.

## The idea

Claude Code is an AI-powered coding assistant that helps you build features, fix bugs, and automate
development tasks[^what]. You talk to it in your terminal. This course uses it in every module, so
this first lesson is about working with it safely.

Two names matter here. Claude is the AI model: the program that reads your request and chooses
what to do. Claude Code is the program on your computer around it: it gives Claude its tools and
manages what Claude sees[^harness].

This lesson assumes what the Level 0 outside course teaches: you can open a terminal, move between
folders, run a Python file, and use git to commit and read a diff (the lines that changed between
two versions of a file).

**What happens when you ask.** When you give Claude a task, it works through three phases: gather context, take action, and verify
results[^loop]. It does this with tools. Without tools, Claude can only respond with text; with
tools, it can read your code, edit files, run commands, search the web, and interact with external
services[^tools].

Here is an example. You type:

```text
add a function that splits the bill between people
```

Claude reads your files to find where the bill is computed (gather context). It edits a file to add
the function (take action). It may run the file to see that it works (verify). Each of those steps
is an action on your computer.

**Who decides what runs.** Some actions are harmless: reading a file changes nothing. Others change your files or run programs.
Claude Code has permission modes that decide which actions it takes without asking you. In Manual
mode, Claude Code stops and asks you before most actions that edit files, run shell commands, or
reach the network[^manual]. A shell command is a command typed in the terminal, such as
`python3 tip.py`.

When it asks, you see a permission prompt. A permission prompt shows what Claude is about to do,
followed by your options[^prompt]. You select **Yes** to approve[^first-change] or **No** to refuse[^deny]. Many prompts also offer
**Yes, and don't ask again**, which also approves later actions of the same kind; for how long
depends on the action[^bash-approval]. Read the prompt before you answer. It is the moment you decide.

Not every command asks. Claude Code recognizes a built-in set of Bash commands as read-only and runs
them without a permission prompt in every mode[^read-only]. Bash is the program that runs shell
commands. The set includes `ls`, `cat`, `echo`, `pwd`, `head`, `tail`, `grep`, `find`, `wc`, `which`,
`diff`, `stat`, `du`, `cd`, and read-only forms of `git`[^read-only-list]. These commands look at
files; they do not change them.

**The mode a session starts in.** With Claude Code v2.1.283 or later, auto mode is the built-in starting permission mode for
interactive terminal and VS Code sessions[^auto-default]. In auto mode, a second model, the
classifier, reviews actions instead of you[^classifier]. A classifier is a program that sorts each
action into allowed or blocked. It is a model too, so it can be wrong.

In this module you review every action yourself, so you start in Manual mode. The command line
accepts `manual` as a name for it: `claude --permission-mode manual`[^manual-flag]. You can also
press `Shift+Tab` at any time to switch the permission mode of the session you are in[^shift-tab].

## Try it

You need a Claude account to use Claude Code: a Claude subscription (Pro, Max, Team, or Enterprise),
a Claude Console account (API access with pre-paid credits; the API is the way your own programs call Claude)[^console], or
access through a supported cloud provider (a company that runs Claude on its own servers)[^account]. These are paid
services; check the price before you sign up.

### Install

On macOS, Linux or WSL (Linux inside Windows), the install command is[^install]:

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

In the Windows command prompt (CMD), it is[^install-windows]:

```bat
curl -fsSL https://claude.ai/install.cmd -o install.cmd && install.cmd && del install.cmd
```

When the installer finishes, open a new terminal window and run `claude --version`. A working
installation prints a version number[^version].

### A small project

Make a folder with one Python file and commit it, so git can show you later what Claude changed:

```bash
mkdir tip-calc
cd tip-calc
git init
```

Save this as `tip.py`:

```python
"""A small tip calculator."""


def tip(total, percent):
    """Return the tip on a bill: percent of the total, rounded to cents."""
    return round(total * percent / 100, 2)


if __name__ == "__main__":
    print(tip(50, 15))
```

The program computes a tip: a percentage of the bill. Run it with `python3 tip.py`. It prints:

```text
7.5
```

Then commit it:

```bash
git add tip.py
git commit -m "Add the tip calculator"
```

### Your first session

Open your terminal in any project directory and start Claude Code[^start]. Here the project is
`tip-calc`, and you start in Manual mode:

```bash
claude --permission-mode manual
```

Claude Code prompts you to log in on first use[^login]. Follow its steps in the browser.

**Ask it to read and explain.** Type:

```text
explain what tip.py does, line by line
```

Claude Code reads your project files as needed; you do not have to paste them in[^reads]. Reading
files inside your project folder needs no approval[^reads-free], so it answers without a prompt.
Check its answer against the code: does it say that `round(..., 2)` keeps two decimals?

**Ask it to change the code.** Type:

```text
add a function split(total, percent, people) to tip.py that returns what each person pays, tip included
```

A permission prompt appears for the edit. It shows what Claude is about to do[^prompt]. Read it. If the change does what you asked and touches only `tip.py`, choose **Yes**. If it
does something else, choose **No**.

**Ask it to run the file.** Type:

```text
run tip.py
```

`python3` is not in the read-only set, so a prompt asks before the command runs. Approve it: you
know what `tip.py` does.

**Refuse once, on purpose.** Ask for something you do not want, such as `delete tip.py`. If Claude first asks you in the
conversation whether you are sure, say yes, so that the permission prompt appears. Then choose **No**. If you select **No** without a comment, Claude Code stops the turn: it stops working on your
request[^deny]. Try it again and,
before you answer, move to **No** and press `Tab` to open a comment field[^comment], and type a
reason. Claude Code sends your comment
to Claude as the reason for the denial, and Claude continues working[^deny-comment].

To leave, type `/exit`[^exit]. Then run `git diff` in the terminal: it shows every line Claude changed
since your commit. The next lesson is about reading it.

## Common mistakes

**"Claude Code does what it wants on my computer."** In Manual mode it asks before most edits,
commands and network access[^manual]. What runs is your decision, so read each prompt.

**"Reading is safe, so everything is safe."** Reads and the read-only commands run without asking.
Edits and other commands ask. A **Yes** to an edit or a command changes your files.

**"Yes, and don't ask again is the same as Yes."** It is not. For an edit, the approval lasts until
the session ends[^edit-approval]. For a Bash command, the rule is saved and applies to future
sessions anywhere in that repository[^bash-approval]. Choose it only for commands you would approve
every time.

**"If I write 'never delete files' in my request, it cannot delete files."** Permission rules are
enforced by Claude Code, not by the model[^enforced]. Your words guide what Claude tries. The
permission prompts and rules decide what runs.

**"A new session asks me about everything."** On recent versions a new session starts in auto mode,
where a classifier decides instead of you[^auto-default]. Start with
`claude --permission-mode manual`, or switch with `Shift+Tab`, when you want to review each action.

**"Once it has started, I cannot stop it."** Press `Esc` to stop Claude immediately[^esc]. Before
Claude edits a file, it saves a copy of the current contents; press `Esc` twice to rewind to an
earlier state, or ask Claude to undo[^rewind]. Rewind does not cover everything: it does not track
files changed by Bash commands[^bash-untracked]. Commit your work, so git can always bring it back.

## Your exercise

You cannot run Claude Code inside a test, so this exercise practises the decision you make at each
prompt. Open `exercise/starter/permission_check.py`. It describes each action Claude asks to take
as a dictionary, for example `{"tool": "Edit", "file": "tip.py"}` or
`{"tool": "Bash", "command": "python3 tip.py"}`.

Write two functions.

`asks_first(action)` returns `True` when Manual mode would ask you first:

- `Read`, `Grep` and `Glob` (the tools that read and search files) never ask;
- `Edit` and `Write` (the tools that change files) always ask;
- `Bash` asks, unless the command is one simple command (no `;`, `&`, `|`, `>`, `<`, backquote,
  `$(` or line break) whose program is in `READ_ONLY_COMMANDS`;
- any other tool asks: when you are not sure, ask.

In a shell command, `>` sends a command's output into a file, and `<` feeds a file into a command;
both are called redirections.

This is a simplified model that asks whenever it is not sure. The real Claude Code looks closer:
for example, it checks the file a redirection (`>` or `<`) points to as if Claude wrote or
read that file directly[^redirect], and it treats read-only forms of `git` as read-only[^read-only-list]. The exercise leaves those cases out.

`answer(action, task_files, expected_commands)` returns what you would answer:

- `"no prompt"` when `asks_first(action)` is `False`;
- for `Edit` or `Write`: `"yes"` when the file is one of `task_files`, otherwise `"no"`;
- for `Bash`: `"yes"` when the command, without the spaces around it, is one of
  `expected_commands`, otherwise `"no"`;
- for any other tool: `"no"`.

Run the tests from the starter folder (`exercise/starter/`):

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

They fail until your functions are right. A solution is in `exercise/solution/`; try on your own
first. Then do the real thing: one session in Manual mode on `tip-calc`, where you approve one edit
and refuse one action.

## Check yourself

Answer the questions in `quiz.json`. If they are hard, read "The idea" again, and the
mistakes about **Yes, and don't ask again**.

[^what]: Claude Code docs, Overview.
[^loop]: Claude Code docs, How Claude Code works.
[^tools]: Claude Code docs, How Claude Code works.
[^manual]: Claude Code docs, Choose a permission mode.
[^prompt]: Claude Code docs, Configure permissions.
[^read-only]: Claude Code docs, Configure permissions.
[^read-only-list]: Claude Code docs, Configure permissions.
[^auto-default]: Claude Code docs, Choose a permission mode.
[^classifier]: Claude Code docs, Choose a permission mode.
[^manual-flag]: Claude Code docs, Choose a permission mode.
[^shift-tab]: Claude Code docs, Quickstart.
[^account]: Claude Code docs, Quickstart.
[^install]: Claude Code docs, Quickstart.
[^install-windows]: Claude Code docs, Quickstart.
[^version]: Claude Code docs, Quickstart.
[^start]: Claude Code docs, Quickstart.
[^login]: Claude Code docs, Quickstart.
[^reads]: Claude Code docs, Quickstart.
[^deny]: Claude Code docs, Configure permissions.
[^deny-comment]: Claude Code docs, Configure permissions.
[^edit-approval]: Claude Code docs, Configure permissions.
[^bash-approval]: Claude Code docs, Configure permissions.
[^enforced]: Claude Code docs, Configure permissions.
[^esc]: Claude Code docs, How Claude Code works.
[^rewind]: Claude Code docs, How Claude Code works.
[^bash-untracked]: Claude Code docs, Checkpointing.
[^reads-free]: Claude Code docs, Configure permissions.
[^harness]: Claude Code docs, How Claude Code works.
[^first-change]: Claude Code docs, Quickstart.
[^comment]: Claude Code docs, Configure permissions.
[^exit]: Claude Code docs, Quickstart.
[^console]: Claude Code docs, Quickstart.
[^redirect]: Claude Code docs, Configure permissions.
