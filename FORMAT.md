# The course format and the gates

A course is a folder under `courses/`. The tools in `tools/` (stdlib Python, `bin/courses`) read it,
run its gates and compute each lesson's status. Nothing here depends on the subject: the same format
and gates serve AI engineering today and DevSecOps later.

> **`courses check` runs code from the lessons** (claim scripts, exercise tests). It runs them with a
> minimal environment and a throwaway home folder, but it is still code from whoever wrote the lesson:
> run it only on content you have read, or in a container. `courses status` and `courses coverage`
> run no code; they use the last `check` result for the same content.

## Layout

```
courses/<course>/
├── course.json            the course: languages, levels with exit criteria, modules and their lessons
├── competencies.json      what a learner can DO after the course, per level
├── syllabi/<name>.json    external syllabi mapped onto our competencies (what we cover, what we leave out and why)
└── lessons/<lesson>/
    ├── lesson.json        id, title, level, minutes, competencies, prerequisites
    ├── en.md, ar.md       the lesson text, one file per course language
    ├── sources.json       every source the text cites, with a quote from it
    ├── claims.json        every result the text states that code can produce, and the code that produces it
    ├── claims/*.py        those checks
    ├── exercise/          exercise.json, starter/, solution/, tests/
    ├── quiz.json          choice and open questions, in every language
    └── review.json        what reviewers and learners recorded (never written by hand for the machine gates)
```

A lesson listed in `course.json` without a folder yet is **planned**.

## Files

**course.json** (`"schema": "nexika.course/1"`): `id`, `title` and `audience` per language,
`languages` (e.g. `["en", "ar"]`), `levels` (`id`, `title`, `exit`: what a learner can do when the
level is done), `modules` (`id`, `level`, `title`, `lessons`: lesson ids in order),
`external` (outside courses a level relies on: `title`, `url`, `covers`: competency ids),
`verify` (`min_learners`, `min_pass_rate`).

**competencies.json** (`nexika.competencies/1`): each competency has an `id` (`c<level>.<name>`),
`level`, `can` per language (one ability, written so it can be checked), `concepts`, and
`evidence` (`exercise`, `project`, or `quiz` for an ability that is shown by explaining it).
`course.json` may list `plain_numbers`: patterns of numbers that are names, not facts (`Python 3\\.\\d+`),
which the uncited-number check ignores.

**lesson.json** (`nexika.lesson/1`): `id`, `title` per language, `module`, `level`, `minutes`,
`competencies` (ids it teaches), `prerequisites` (lesson ids; each must come earlier in the course).

**sources.json** (`nexika.sources/1`): `sources` maps an id to `url` (https), `title`, `kind`
(`doc`, `spec`, `paper`, `book`, `repo`), `quote` (the exact words that support the text),
`retrieved` (`YYYY-MM-DD`) and `volatile` (true for facts that change: model names, prices, limits).
The text cites with footnote markers: `... a context window of 200K tokens[^models].`

**claims.json** (`nexika.claims/1`): each claim has an `id`, `says` (the exact words in `en.md` that
state the result; `says_ar` for `ar.md`), `check` (a script in `claims/` that prints the value as
JSON on its last line of standard output) and `expect` (the value, or `{"approx": x, "tol": t}`). The
`says` words must themselves state that value (Arabic-Indic digits count). A check that only prints a
constant passes the machine gate: catching that is the fact checkers' job.

**exercise/exercise.json** (`nexika.exercise/1`): `runner` (`python-unittest`), `goal` per language.
`tests/` runs against `starter/` (must fail, and the starter must load: the tests really test
something) and against `solution/` (must pass). No compiled code, caches, symbolic links or binaries
are allowed under `claims/` or `exercise/`. Whether the tests test the *right* thing is for review.

**quiz.json** (`nexika.quiz/1`): questions of `type` `choice` (`prompt`, four `options`, `answer`
index, `explain`) or `open` (`prompt`, `rubric`: the points a good answer makes), every text per
language.

**review.json** (`nexika.review/1`): `fact_checks` and `teaching` (each `by`, `date`, `result`
`pass` or `fail`, `hash`, `notes`), `learners` (`attempts`, `passes`, `hash`), `experts`
(`github`, `date`, `verdict`, `link`, `hash`). `hash` is the lesson's content hash when the review
was made: a review counts only while the lesson is unchanged (`courses hash <lesson>` prints it). The
hash covers every file of the lesson except `review.json`, plus its module and competencies in the
course. Learners need `passes <= attempts`; an expert entry needs the `link` of its review issue in
this repository. **Only maintainers (MAINTAINERS) change `review.json`, the tools or CI**: CI refuses
those changes from anyone else, and CODEOWNERS asks for a maintainer's review.

## The gates

| Gate | What it checks | Run by |
|---|---|---|
| **structure** | files present and valid, ids unique, every language present with the same headings, prerequisites exist and come earlier | `courses check` (CI) |
| **claims** | each check prints its `expect`ed value, and the `says` words are in the text | `courses check` (CI) |
| **exercise** | tests fail on the starter, pass on the solution | `courses check` (CI) |
| **quiz** | four distinct options, explanations and rubrics present, the right answer not given away by length (never the clear longest; overall not the longest more than a third of the time), answers not all in one place | `courses check` (CI) |
| **sources** | every citation has a source with a quote, every source is cited, volatile sources re-read in the last 45 days, every sentence with a number cites a source or is a checked claim; online: the quote is on the page | `courses check` (CI), `--online` monthly |
| **links** | relative links resolve | `courses check` (CI) |
| **fact check** | two independent reviewers (agents or people) confirm each factual sentence against its quoted source | recorded in `review.json` |
| **teaching** | the teaching rubric in REVIEWING.md, including a "what would a beginner misunderstand" pass | recorded in `review.json` |
| **learners** | learners pass the exercise and the checks, through prof | recorded in `review.json` |
| **experts** | outside experts approve, through the lesson review issue form | recorded in `review.json` |

## Status

Each lesson shows one status and an expert badge:

- **planned**: listed, no folder yet.
- **draft**: a machine gate fails.
- **checked**: every machine gate passes.
- **reviewed**: checked, plus two passing fact checks by different reviewers and one passing teaching
  review, all on the current content.
- **verified**: reviewed, plus at least `verify.min_learners` learners passed at `verify.min_pass_rate`
  or better, on the current content.
- **expert review**: `open`, or the GitHub handles who approved the current content.

Any change to the lesson's content changes its hash, so the reviews made on the old content stop
counting until they are done again.
