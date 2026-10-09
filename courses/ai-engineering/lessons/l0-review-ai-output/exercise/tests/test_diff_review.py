import unittest
from pathlib import Path

from diff_review import parse_diff, red_flags

# A real `git diff` of one change: a new README.md, an edited notes.txt and tip.py,
# a deleted test_old.py, and an edited test_tip.py with a skipped test.
SAMPLE = (Path(__file__).parent / "sample.diff").read_text()

ONE_FILE = """diff --git a/tip.py b/tip.py
index 9efacd8..8c63923 100644
--- a/tip.py
+++ b/tip.py
@@ -5,2 +5,4 @@ def tip(total, percent):
 def split(total, percent, people):
-    return round((total + tip(total, percent)) / people, 2)
+    if people < 1:
+        raise ValueError("people must be at least 1")
+    return round((total + tip(total, percent)) / people, 2)
"""


class ParseDiff(unittest.TestCase):
    def test_one_file(self):
        self.assertEqual(parse_diff(ONE_FILE), {
            "tip.py": {
                "status": "modified",
                "added": [
                    "    if people < 1:",
                    '        raise ValueError("people must be at least 1")',
                    "    return round((total + tip(total, percent)) / people, 2)",
                ],
                "removed": ["    return round((total + tip(total, percent)) / people, 2)"],
            },
        })

    def test_every_file_in_order_with_its_status(self):
        files = parse_diff(SAMPLE)
        self.assertEqual(list(files), ["README.md", "notes.txt", "test_old.py", "test_tip.py", "tip.py"])
        self.assertEqual([f["status"] for f in files.values()],
                         ["added", "modified", "deleted", "modified", "modified"])

    def test_a_new_file_has_only_added_lines(self):
        readme = parse_diff(SAMPLE)["README.md"]
        self.assertEqual(readme["added"], ["-- a line that starts with two dashes", "++ and one with two pluses"])
        self.assertEqual(readme["removed"], [])

    def test_content_that_looks_like_a_header_is_still_content(self):
        notes = parse_diff(SAMPLE)["notes.txt"]
        self.assertEqual(notes["removed"], ["-- old notes"])
        self.assertEqual(notes["added"], ["++ new notes"])

    def test_a_deleted_file_has_only_removed_lines(self):
        old = parse_diff(SAMPLE)["test_old.py"]
        self.assertEqual(old["added"], [])
        self.assertEqual(old["removed"][0], "import unittest")
        self.assertEqual(old["removed"][-1], "        self.assertTrue(True)")
        self.assertEqual(len(old["removed"]), 6)

    def test_unchanged_lines_are_not_content(self):
        test_tip = parse_diff(SAMPLE)["test_tip.py"]
        self.assertEqual(test_tip["added"], [
            '    @unittest.skip("later")',
            "        self.assertEqual(split(100, 10, 4), 35.0)",
        ])
        self.assertEqual(test_tip["removed"], ["        self.assertEqual(split(100, 10, 4), 27.5)"])

    def test_an_empty_diff_has_no_files(self):
        self.assertEqual(parse_diff(""), {})


class RedFlags(unittest.TestCase):
    def test_a_change_inside_the_task_has_no_flag(self):
        self.assertEqual(red_flags(ONE_FILE, ["tip.py"]), [])

    def test_a_file_outside_the_task_is_flagged(self):
        self.assertEqual(red_flags(ONE_FILE, ["README.md"]), [("tip.py", "outside the task")])

    def test_every_flag_of_the_sample_in_order(self):
        self.assertEqual(red_flags(SAMPLE, ["tip.py", "test_tip.py"]), [
            ("README.md", "outside the task"),
            ("notes.txt", "outside the task"),
            ("test_old.py", "outside the task"),
            ("test_old.py", "test deleted"),
            ("test_old.py", "assertion changed"),
            ("test_tip.py", "assertion changed"),
            ("test_tip.py", "test skipped"),
        ])

    def test_a_removed_assert_counts_only_in_a_test_file(self):
        diff = ONE_FILE.replace("-    return round", "-    assert people\n-    return round").replace(
            "@@ -5,2 +5,4 @@", "@@ -5,3 +5,4 @@")
        self.assertEqual(red_flags(diff, ["tip.py"]), [])
        as_test = diff.replace("tip.py", "test_tip.py")
        self.assertEqual(red_flags(as_test, ["test_tip.py"]), [("test_tip.py", "assertion changed")])

    def test_files_ending_in_test_py_are_test_files(self):
        diff = SAMPLE.replace("test_old.py", "old_test.py")
        self.assertIn(("old_test.py", "test deleted"), red_flags(diff, []))

    def test_every_skip_mark_is_flagged(self):
        for mark in ("self.skipTest(\"slow\")", "@pytest.mark.skip", "@unittest.skipIf(True, \"x\")"):
            diff = ONE_FILE.replace('+    if people < 1:', "+    " + mark)
            self.assertEqual(red_flags(diff, ["tip.py"]), [("tip.py", "test skipped")], mark)


if __name__ == "__main__":
    unittest.main()
