import re
import unittest

from prompt_builder import build_prompt

BLOCK = re.compile(r"<(\w+)>\n(.*)\n</\1>", re.S)

TASK = "Classify the ticket as billing, bug or feature_request."
CONTEXT = "We sell a photo-editing app."
EXAMPLES = ["Ticket: Export does nothing.\nCategory: bug", "Ticket: Add a dark mode?\nCategory: feature_request"]
FORMAT = "Reply with the category only."


def blocks(prompt):
    """The prompt's top-level parts as (tag, content) pairs, checking each is one well-formed tag."""
    found = []
    for part in prompt.split("\n\n"):
        match = BLOCK.fullmatch(part)
        if not match:
            raise AssertionError(f"not a tagged part on its own lines: {part!r}")
        found.append((match.group(1), match.group(2)))
    return found


class BuildPrompt(unittest.TestCase):
    def test_every_part_sits_in_its_own_tag_in_order(self):
        parts = blocks(build_prompt(TASK, CONTEXT, EXAMPLES, FORMAT))
        self.assertEqual([name for name, _ in parts], ["task", "context", "examples", "output_format"])
        self.assertEqual(parts[0][1], TASK)
        self.assertEqual(parts[1][1], CONTEXT)
        self.assertEqual(parts[3][1], FORMAT)

    def test_each_example_has_its_own_example_tag_inside_examples(self):
        content = dict(blocks(build_prompt(TASK, examples=EXAMPLES)))["examples"]
        inner = re.findall(r"<example>\n(.*?)\n</example>", content, re.S)
        self.assertEqual(inner, EXAMPLES)
        self.assertEqual(content, "\n".join(f"<example>\n{e}\n</example>" for e in EXAMPLES))

    def test_a_task_alone_gives_only_the_task(self):
        self.assertEqual(build_prompt(TASK), f"<task>\n{TASK}\n</task>")

    def test_empty_and_blank_parts_are_left_out(self):
        prompt = build_prompt(TASK, context="   ", examples=["", "  \n"], output_format="\n")
        self.assertEqual(blocks(prompt), [("task", TASK)])
        for name in ("context", "examples", "example", "output_format"):
            self.assertNotIn(f"<{name}>", prompt)

    def test_missing_parts_keep_the_order_of_the_others(self):
        parts = blocks(build_prompt(TASK, output_format=FORMAT, context=CONTEXT))
        self.assertEqual([name for name, _ in parts], ["task", "context", "output_format"])
        parts = blocks(build_prompt(TASK, examples=EXAMPLES[:1], output_format=FORMAT))
        self.assertEqual([name for name, _ in parts], ["task", "examples", "output_format"])

    def test_blank_examples_are_skipped_and_the_rest_kept(self):
        content = dict(blocks(build_prompt(TASK, examples=("first", " ", "second"))))["examples"]
        self.assertEqual(re.findall(r"<example>\n(.*?)\n</example>", content, re.S), ["first", "second"])

    def test_spaces_around_each_part_are_removed(self):
        parts = blocks(build_prompt(f"  {TASK}\n", f"\n{CONTEXT}  ", [f"  {EXAMPLES[0]} "], f" {FORMAT}\n\n"))
        self.assertEqual(parts[0], ("task", TASK))
        self.assertEqual(parts[1], ("context", CONTEXT))
        self.assertIn(f"<example>\n{EXAMPLES[0]}\n</example>", parts[2][1])
        self.assertEqual(parts[3], ("output_format", FORMAT))

    def test_an_empty_task_is_refused(self):
        for task in ("", "   ", "\n"):
            with self.assertRaises(ValueError):
                build_prompt(task, CONTEXT, EXAMPLES, FORMAT)


if __name__ == "__main__":
    unittest.main()
