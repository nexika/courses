# Reviewing a lesson

> Reviewing a pull request? `bin/courses check` runs the lesson's code: read the claim scripts and the
> exercise first, or run it in a container. `bin/courses status` runs nothing.

Every lesson asks for review. A lesson's page links to the
[lesson review form](https://github.com/nexika/courses/issues/new?template=lesson-review.yml);
reviews that are accepted are recorded in the lesson's `review.json` and credited by GitHub handle.

## Fact check

For each factual sentence: is it supported by the quote in `sources.json`, and does the quote say
that on the cited page? Report the sentence and what is wrong. Numbers that the code produces are
already checked by the machine gates; check that the text explains them correctly.

## Teaching rubric

A lesson passes when all of these hold:

1. **Objective:** it says what the learner will be able to do, and that matches its competencies.
2. **Prerequisites:** nothing is used before it is taught (here or in a listed prerequisite, or in one of its own prerequisites: they carry over).
3. **Concept before code:** the idea is explained with an example before the implementation.
4. **Worked example:** at least one complete example the learner can run.
5. **Exercise fits:** the exercise practises the objective, not something else.
6. **Misconceptions:** the common wrong ideas about the topic are named and corrected.
7. **Beginner pass:** read it as someone who only has the prerequisites: list every sentence they
   would misunderstand or every word they would not know. The lesson passes when the list is empty.
8. **Plain language:** short sentences, defined terms, no filler; the Arabic and the French each
   read as written in that language, not as a translation; technical terms are glossed the same way
   in every lesson.
9. **Honest:** limits and trade-offs are stated; nothing is presented as simpler or safer than it is.

## Expert review

If you work in the field: read the lesson as above and say `approve` or `changes` with your
reasons. Your handle appears on the lesson as an expert reviewer for the version you reviewed.
