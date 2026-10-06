"""A tiny next-word predictor built from word-pair counts."""

from itertools import pairwise


def build_counts(text):
    """Count, for every word, which words come right after it."""
    words = text.lower().split()
    counts = {}
    for word, following in pairwise(words):
        followers = counts.setdefault(word, {})
        followers[following] = followers.get(following, 0) + 1
    return counts


def next_word(counts, word):
    """Return the word that most often came after `word`; ties go to the alphabetically first."""
    followers = counts.get(word.lower())
    if not followers:
        return None
    return min(followers, key=lambda w: (-followers[w], w))
