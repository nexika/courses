"""A tiny next-word predictor built from word-pair counts.

Fill in the two functions. Run the tests from this folder:
    python3 -m unittest discover -s ../tests
"""


def build_counts(text):
    """Count, for every word, which words come right after it.

    Lowercase the text and split it on whitespace. Return a dict that maps
    each word to a dict {next word: how many times it came next}.
    A word that is never followed by anything does not need a key.
    """
    raise NotImplementedError


def next_word(counts, word):
    """Return the word that most often came after `word` in the counts.

    Compare in lowercase. On a tie, return the alphabetically first word.
    Return None if `word` was never followed by anything.
    """
    raise NotImplementedError
