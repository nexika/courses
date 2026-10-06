# What an LLM does

## What you will be able to do

- Explain in plain words what a large language model does when it writes an answer.
- Name what it cannot do: know about things after its training data ends, and always be right.
- Say what these limits mean for the software you build with one.

## The idea

A large language model (LLM) is a program trained on a very large amount of text. Anthropic describes
LLMs this way: "these models are trained on vast amounts of text data and can generate human-like text"[^llm].

Its core skill is one small step, repeated. Given the text so far, it guesses what comes next. When a
model like the one under Claude is first trained (this is called *pretraining*), it learns "to predict
the next word, given the previous context of text in the document"[^pretraining].

Strictly speaking, the model works with *tokens*, not words. A token is a piece of text that can be a
whole word, part of a word, a character, or even a byte[^tokens]. The next lesson is about tokens. In
this lesson, "the next word" is close enough.

Take the start of a sentence: "The cat sat on the ...". You probably thought of "mat". You did not look
it up: you have seen that phrase many times. A language model does something similar, at a huge scale.
It writes a whole answer by predicting one piece, adding it to the text, and predicting the next piece.

Claude is more than a raw predictor: Anthropic notes that "it has already been fine-tuned to be a helpful
assistant"[^finetune]. That training makes it follow instructions and answer questions well. It does not
change the basic mechanism: the answer is still produced from patterns the model learned. Two limits
follow from that.

**First limit: no live knowledge.** A model learns from data collected up to some date: its *training data
cutoff*. Anthropic's model overview lists this date for every current model[^models]. It gives Jun 2026
for Claude Fable 5.1, Claude Opus 5.5 and Claude Sonnet 5.5, and Jul 2025 for Claude Haiku 4.5[^models].
About anything after that date, the model has seen no text, so it has no patterns to draw on.

The model can only work with newer facts if you give them to it. You can paste a document into the
prompt. You can let your code fetch relevant documents and pass them in with the question; Anthropic's
glossary says this "allows the model to access and use information beyond its training data"[^rag]. Or
you can give it a tool, such as web search, which lets Claude "answer questions with up-to-date
information beyond its knowledge cutoff"[^websearch].

**Second limit: confident mistakes.** A pattern that is common is not the same as a fact that is true.
Anthropic warns that even the most advanced models "can sometimes generate text that is factually
incorrect or inconsistent with the given context", and calls this *hallucination*[^halluc]. A wrong
answer comes out as fluent and as sure of itself as a right one. The tone tells you nothing.

**Why this matters to you as an engineer.** Treat what a model writes as a draft to check, not as the
result of a database lookup. Put the facts it needs into the prompt, and tell it to use only those:
Anthropic suggests you "explicitly instruct Claude to only use information from provided documents and
not its general knowledge"[^halluc-docs]. Let it say when it does not know; the same guide advises you to
"explicitly give Claude permission to admit uncertainty"[^halluc-idk]. And keep a check in your code or
your process: these techniques reduce hallucinations, but "they don't eliminate them entirely"[^halluc-limit].

## Try it

Here is a next-word predictor small enough to read in one go. It learns from a toy *corpus* (the text it
is trained on): a few messages from a team chat. It counts which word comes right after which, then
predicts the word that came next most often.

Save this as `predict.py` and run `python3 predict.py`:

```python
from collections import Counter
from itertools import pairwise

corpus = """
the team meeting is on monday .
remember the meeting is on monday .
the meeting is on monday as usual .
news the meeting moved and is on friday now .
"""

words = corpus.lower().split()
pairs = Counter(pairwise(words))  # (word, next word) -> how many times


def predict(word):
    followers = {b: n for (a, b), n in pairs.items() if a == word}
    if not followers:
        return None  # never seen: no pattern to follow
    return max(followers, key=followers.get)


print("after 'on':", {b: n for (a, b), n in pairs.items() if a == "on"})

sentence = ["meeting"]
for _ in range(4):
    sentence.append(predict(sentence[-1]))
print(" ".join(sentence))

print("after 'tuesday':", predict("tuesday"))
```

You should see:

```
after 'on': {'monday': 3, 'friday': 1}
meeting is on monday .
after 'tuesday': None
```

Look at what happened. In this corpus, `monday` follows `on` 3 times, and `friday` follows it only 1 time.
So, starting from `meeting`, the predictor writes "meeting is on monday ." one word at a time. The
sentence is fluent, and it is wrong: the latest message says the meeting moved to Friday. The predictor
did not check anything. It followed the most common pattern.

Notice two more things. First, the period is a "word" here, so the predictor also learned where
sentences end. Second, it has nothing to say about `tuesday`, because that word is not in its corpus.
Now imagine the last message had been sent after the corpus was collected: the predictor would not even
know Friday was possible. That is a training data cutoff in miniature.

A real LLM is far more capable than this: it learns from vastly more text and uses much more of the
context than the one word before[^pretraining]. But the lesson carries over. It writes what its patterns
make likely, and likely is not the same as true.

## Common mistakes

- **"The model looks the answer up."** It does not search a store of facts. It predicts the next piece of
  text from what came before[^pretraining]. To ground it in facts, give it the facts[^rag].
- **"It sounds sure, so it is right."** Fluent and confident text can still be factually wrong[^halluc].
  Check what matters, whatever the tone.
- **"It knows today's news."** Without documents or tools, it has no information past its training data
  cutoff[^websearch]. Ask it about a recent version, price or event and it may answer from older patterns.
- **"Temperature at zero makes it correct."** Lower temperatures give outputs "that stick to the most
  probable phrasing and answers"[^temperature]. Most probable is what our toy predictor always picks, and
  it still said Monday.
- **"A few prompt tricks remove hallucinations."** They reduce them; the guide advises you to "always
  validate critical information, especially for high-stakes decisions"[^halluc-validate].

## Your exercise

Build the predictor yourself, as two functions you can test. The starter is in
`exercise/starter/predictor.py`. Write:

- `build_counts(text)`: lowercase the text, split it on whitespace, and return a dict that maps each word
  to a dict of the words that came right after it, with how many times.
- `next_word(counts, word)`: return the word that most often came after `word` (compare in lowercase). On
  a tie, return the alphabetically first word. If `word` was never followed by anything, return `None`.

Run the tests from the starter folder:

```bash
cd exercise/starter
python3 -m unittest discover -s ../tests
```

They fail until your two functions work. One test chains your predictions from `meeting`, as in Try it.
When everything passes, compare your code with `exercise/solution/predictor.py`.

## Check yourself

Answer the questions in `quiz.json`. If they feel hard, re-read the two limits in The idea and the end of
Try it.

[^llm]: Anthropic, Glossary, "LLM".
[^pretraining]: Anthropic, Glossary, "Pretraining".
[^tokens]: Anthropic, Glossary, "Tokens".
[^finetune]: Anthropic, Glossary, "Fine-tuning".
[^rag]: Anthropic, Glossary, "RAG (Retrieval augmented generation)".
[^temperature]: Anthropic, Glossary, "Temperature".
[^models]: Anthropic, Models overview.
[^websearch]: Anthropic, Web search tool.
[^halluc]: Anthropic, Reduce hallucinations.
[^halluc-docs]: Anthropic, Reduce hallucinations, "External knowledge restriction".
[^halluc-idk]: Anthropic, Reduce hallucinations, "Allow Claude to say I don't know".
[^halluc-limit]: Anthropic, Reduce hallucinations.
[^halluc-validate]: Anthropic, Reduce hallucinations.
