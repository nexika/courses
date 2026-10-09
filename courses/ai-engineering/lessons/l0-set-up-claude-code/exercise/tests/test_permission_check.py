import unittest

from permission_check import answer, asks_first

TASK = ["tip.py"]
EXPECTED = ["python3 tip.py", "python3 -m unittest"]


def bash(command):
    return {"tool": "Bash", "command": command}


class AsksFirst(unittest.TestCase):
    def test_reading_and_searching_never_ask(self):
        for tool in ("Read", "Grep", "Glob"):
            self.assertFalse(asks_first({"tool": tool, "file": "tip.py"}), tool)

    def test_changing_a_file_always_asks(self):
        for tool in ("Edit", "Write"):
            self.assertTrue(asks_first({"tool": tool, "file": "tip.py"}), tool)

    def test_read_only_commands_do_not_ask(self):
        for command in ("ls", "cat tip.py", "  wc -l tip.py ", "grep def tip.py", "pwd", "cd src"):
            self.assertFalse(asks_first(bash(command)), command)

    def test_other_commands_ask(self):
        for command in ("python3 tip.py", "rm tip.py", "git commit -m x", "pip install requests", "catalog"):
            self.assertTrue(asks_first(bash(command)), command)

    def test_a_read_only_program_joined_to_another_command_asks(self):
        for command in ("ls; rm tip.py", "cat tip.py | sh", "echo x > tip.py", "ls && rm -r .",
                        "cat $(find . -name x)", "echo `rm tip.py`", "ls\nrm tip.py", "cat < tip.py",
                        "ls & rm tip.py"):
            self.assertTrue(asks_first(bash(command)), command)

    def test_an_empty_command_asks(self):
        self.assertTrue(asks_first(bash("   ")))

    def test_an_unknown_tool_asks(self):
        self.assertTrue(asks_first({"tool": "WebFetch", "url": "https://example.com"}))


class Answer(unittest.TestCase):
    def test_actions_that_do_not_ask_need_no_answer(self):
        self.assertEqual(answer({"tool": "Read", "file": "secrets.txt"}, TASK, EXPECTED), "no prompt")
        self.assertEqual(answer(bash("ls"), TASK, EXPECTED), "no prompt")

    def test_edits_to_the_task_files_are_approved(self):
        self.assertEqual(answer({"tool": "Edit", "file": "tip.py"}, TASK, EXPECTED), "yes")
        self.assertEqual(answer({"tool": "Write", "file": "tip.py"}, TASK, EXPECTED), "yes")

    def test_edits_to_other_files_are_refused(self):
        self.assertEqual(answer({"tool": "Edit", "file": "README.md"}, TASK, EXPECTED), "no")
        self.assertEqual(answer({"tool": "Write", "file": "test_tip.py"}, TASK, EXPECTED), "no")

    def test_only_the_expected_commands_are_approved(self):
        self.assertEqual(answer(bash("python3 tip.py"), TASK, EXPECTED), "yes")
        self.assertEqual(answer(bash("  python3 -m unittest \n"), TASK, EXPECTED), "yes")
        self.assertEqual(answer(bash("rm tip.py"), TASK, EXPECTED), "no")
        self.assertEqual(answer(bash("python3 tip.py; rm tip.py"), TASK, EXPECTED), "no")

    def test_other_tools_are_refused(self):
        self.assertEqual(answer({"tool": "WebFetch", "url": "https://example.com"}, TASK, EXPECTED), "no")

    def test_nothing_is_approved_when_nothing_was_expected(self):
        self.assertEqual(answer({"tool": "Edit", "file": "tip.py"}, [], []), "no")
        self.assertEqual(answer(bash("python3 tip.py"), [], []), "no")


if __name__ == "__main__":
    unittest.main()
