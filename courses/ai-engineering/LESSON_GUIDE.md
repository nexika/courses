# Writing a lesson for AI Engineering with Claude Code

FORMAT.md says what files a lesson has and what the gates check. This guide says how a lesson reads,
so every lesson feels like the same course. REVIEWING.md is how it is judged.

## Voice
- Talk to one learner: "you". Short sentences. One idea per paragraph.
- Define every term the first time, in plain words. Gloss technical terms the same way in every
  lesson: Arabic `الرموز (tokens)`, `الموجّه (prompt)`, `موجّه النظام (system prompt)`; French keeps
  the words French developers use (*prompt*, *tokens*, *commit*).
- Never present something as simpler, safer or more certain than it is. Say what it cannot do.
- No filler, no hype, no "simply", no "just". No dates like "in 2026" unless a source needs them.
- Each language is written for its readers, not translated word by word. Same facts, same structure,
  same headings, same code.

## Shape (the same headings in every lesson, in every language)

```
# <Title>
## What you will be able to do        two or three abilities, matching the lesson's competencies
## The idea                           the concept with a small example, before any code
## Try it                             a complete, runnable example (stdlib Python, no network)
## Common mistakes                    the wrong ideas people have about this, corrected
## Your exercise                      what to build, where the starter is, how to run the tests
## Check yourself                     points to the quiz; one line on what to review if it is hard
```

Under "Try it" and "Your exercise", sub-headings (`###`) are allowed but must match across languages.

The six headings are worded the same in every lesson:

| English | Arabic | French |
|---|---|---|
| What you will be able to do | ما الذي ستتمكن من فعله | Ce que vous saurez faire |
| The idea | الفكرة | L'idée |
| Try it | جرّبها | Essayez |
| Common mistakes | أخطاء شائعة | Erreurs fréquentes |
| Your exercise | تمرينك | Votre exercice |
| Check yourself | اختبر نفسك | Vérifiez vos acquis |

## Facts, numbers and sources
- Every factual sentence about the world (models, limits, prices, behaviour) cites a source with a
  footnote marker `[^id]`, and `sources.json` quotes the exact words from that page. Prefer Anthropic's
  own documentation at platform.claude.com (docs.claude.com and docs.anthropic.com redirect there;
  cite the final address) and the official SDKs.
- Model names, prices and limits change: mark those sources `"volatile": true`.
- A number the lesson's own code produces is a claim in `claims.json` (with a check script), not a
  citation. The claim's words must contain the number, in every language.
- Do not state a number you cannot source or compute. Write it without the number instead.

## Code
- Examples and exercises use the Python standard library only and never call the network. Where a
  real API call is the point, show it in the text as a block the learner may run with their own key,
  and make the graded exercise work on a recorded response or a stand-in function.
- The starter loads and has stubs (`raise NotImplementedError` is fine); the tests fail on it and
  pass on the solution. Tests check behaviour, not wording.
- Code is identical in all three languages; only comments and strings shown to the learner change.

## Quiz
- Three or four `choice` questions and one `open` question with a rubric.
- Wrong options are believable mistakes a learner makes, of similar length to the right one, in
  every language. Vary the right answer's position.
- Every choice question has an explanation in every language.
