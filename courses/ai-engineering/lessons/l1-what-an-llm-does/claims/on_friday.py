"""How many times `friday` follows `on` in the lesson's toy corpus (the Try it code)."""
import json
from collections import Counter
from itertools import pairwise

corpus = """
the team meeting is on monday .
remember the meeting is on monday .
the meeting is on monday as usual .
news the meeting moved and is on friday now .
"""

words = corpus.lower().split()
pairs = Counter(pairwise(words))
print({b: n for (a, b), n in pairs.items() if a == "on"})
print(json.dumps(pairs[("on", "friday")]))
