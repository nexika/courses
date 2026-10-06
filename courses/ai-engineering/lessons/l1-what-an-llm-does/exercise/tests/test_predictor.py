import unittest

from predictor import build_counts, next_word

CORPUS = """
the team meeting is on monday .
remember the meeting is on monday .
the meeting is on monday as usual .
news the meeting moved and is on friday now .
"""


class BuildCounts(unittest.TestCase):
    def test_counts_each_word_pair(self):
        counts = build_counts("the cat sat on the mat")
        self.assertEqual(dict(counts["the"]), {"cat": 1, "mat": 1})
        self.assertEqual(dict(counts["cat"]), {"sat": 1})
        self.assertEqual(dict(counts["on"]), {"the": 1})

    def test_repeated_pairs_add_up(self):
        counts = build_counts("a b a b a c")
        self.assertEqual(dict(counts["a"]), {"b": 2, "c": 1})
        self.assertEqual(dict(counts["b"]), {"a": 2})

    def test_the_last_word_has_no_followers(self):
        counts = build_counts("the cat sat")
        self.assertFalse(counts.get("sat"))

    def test_case_and_whitespace_do_not_matter(self):
        counts = build_counts("The  cat\nTHE\tdog")
        self.assertEqual(dict(counts["the"]), {"cat": 1, "dog": 1})
        self.assertEqual(dict(counts["cat"]), {"the": 1})

    def test_empty_text_gives_no_counts(self):
        self.assertFalse(build_counts(""))
        self.assertFalse(build_counts("alone"))

    def test_the_lesson_corpus(self):
        counts = build_counts(CORPUS)
        self.assertEqual(dict(counts["on"]), {"monday": 3, "friday": 1})
        self.assertEqual(dict(counts["is"]), {"on": 4})


class NextWord(unittest.TestCase):
    def test_picks_the_most_frequent_follower(self):
        counts = build_counts("x y x z x z")
        self.assertEqual(next_word(counts, "x"), "z")

    def test_a_tie_goes_to_the_alphabetically_first(self):
        self.assertEqual(next_word(build_counts("a c a b"), "a"), "b")
        self.assertEqual(next_word(build_counts("a b a c"), "a"), "b")

    def test_the_word_is_compared_in_lowercase(self):
        counts = build_counts("Hello world")
        self.assertEqual(next_word(counts, "HELLO"), "world")

    def test_an_unseen_word_gives_none(self):
        counts = build_counts(CORPUS)
        self.assertIsNone(next_word(counts, "tuesday"))
        self.assertIsNone(next_word({}, "on"))

    def test_the_pattern_wins_over_the_latest_news(self):
        counts = build_counts(CORPUS)
        self.assertEqual(next_word(counts, "on"), "monday")

    def test_chaining_predictions_writes_a_sentence(self):
        counts = build_counts(CORPUS)
        sentence = ["meeting"]
        for _ in range(4):
            sentence.append(next_word(counts, sentence[-1]))
        self.assertEqual(" ".join(sentence), "meeting is on monday .")


if __name__ == "__main__":
    unittest.main()
