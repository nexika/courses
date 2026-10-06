"""The gates catch what they promise to catch: one good lesson, then one fault per gate."""
from __future__ import annotations

import datetime
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from courses import cli, gates, pack  # noqa: E402

TODAY = datetime.date.today().isoformat()


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def dump(path: Path, data) -> None:
    write(path, json.dumps(data, ensure_ascii=False, indent=1))


def both(en: str, ar: str) -> dict:
    return {"en": en, "ar": ar}


EN = """# Counting tokens

A model reads text as tokens[^tok]. The word list below has 3 entries.

## Try it

Run `python count.py` to see it.

[^tok]: Anthropic, Glossary.
"""
AR = """# عدّ الرموز

يقرأ النموذج النص على شكل رموز[^tok]. قائمة الكلمات أدناه فيها 3 عناصر.

## جرّبها

شغّل `python count.py` لترى ذلك.

[^tok]: Anthropic، المسرد.
"""
QUESTIONS = [
    {"id": "q1", "type": "choice", "prompt": both("What does a model read?", "ماذا يقرأ النموذج؟"),
     "options": [both("Tokens", "رموزًا"), both("Pixels", "بكسلات"), both("Bytes only", "بايتات فقط"),
                 both("Images", "صورًا")], "answer": 0, "explain": both("Text becomes tokens.", "يصبح النص رموزًا.")},
    {"id": "q2", "type": "choice", "prompt": both("How many entries?", "كم عنصرًا؟"),
     "options": [both("Two", "اثنان"), both("Three", "ثلاثة"), both("Four hundred", "أربعمئة"), both("Twelve", "اثنا عشر")],
     "answer": 1, "explain": both("The list has three.", "القائمة فيها ثلاثة.")},
    {"id": "q3", "type": "choice", "prompt": both("Which runs it?", "ما الذي يشغّلها؟"),
     "options": [both("make", "make"), both("npm", "npm"), both("python", "python"), both("pipenv run", "pipenv run")],
     "answer": 2, "explain": both("The lesson uses Python.", "الدرس يستخدم Python.")},
    {"id": "q4", "type": "open", "prompt": both("Why count tokens?", "لماذا نعدّ الرموز؟"),
     "rubric": both("Mentions cost and the context window.", "يذكر التكلفة ونافذة السياق.")},
]


@pytest.fixture
def root(tmp_path, monkeypatch):
    """A course with one complete, passing lesson and one planned lesson."""
    courses = tmp_path / "courses"
    course = courses / "demo"
    dump(course / "course.json", {
        "schema": "nexika.course/1", "id": "demo", "title": both("Demo", "تجربة"), "audience": both("All", "الجميع"),
        "languages": ["en", "ar"],
        "levels": [{"id": 1, "title": both("Basics", "أساسيات"), "exit": both("You can count.", "تستطيع العدّ.")}],
        "modules": [{"id": "m1", "level": 1, "title": both("Start", "البداية"),
                     "lessons": ["l1-count-tokens", "l1-later"]}],
        "verify": {"min_learners": 2, "min_pass_rate": 0.5}})
    dump(course / "competencies.json", {"schema": "nexika.competencies/1", "competencies": [
        {"id": "c1.count", "level": 1, "evidence": "exercise", "concepts": ["tokens"],
         "can": both("Count tokens.", "تعدّ الرموز.")},
        {"id": "c1.other", "level": 1, "evidence": "exercise", "concepts": [], "can": both("Other.", "أخرى.")}]})
    lesson = course / "lessons" / "l1-count-tokens"
    dump(lesson / "lesson.json", {"schema": "nexika.lesson/1", "id": "l1-count-tokens",
                                  "title": both("Counting tokens", "عدّ الرموز"), "module": "m1", "level": 1,
                                  "minutes": 20, "competencies": ["c1.count"], "prerequisites": []})
    write(lesson / "en.md", EN)
    write(lesson / "ar.md", AR)
    dump(lesson / "sources.json", {"schema": "nexika.sources/1", "sources": {"tok": {
        "url": "https://example.org/tokens", "title": "Tokens", "kind": "doc",
        "quote": "Models process text in units called tokens.", "retrieved": TODAY, "volatile": True}}})
    dump(lesson / "claims.json", {"schema": "nexika.claims/1", "claims": [
        {"id": "entries", "says": "has 3 entries", "says_ar": "فيها 3 عناصر", "check": "count.py", "expect": 3}]})
    write(lesson / "claims" / "count.py", "import json\nprint(json.dumps(len(['a', 'b', 'c'])))\n")
    ex = lesson / "exercise"
    dump(ex / "exercise.json", {"schema": "nexika.exercise/1", "runner": "python-unittest",
                                "goal": both("Write count().", "اكتب الدالة count().")})
    write(ex / "starter" / "work.py", "def count(words):\n    raise NotImplementedError\n")
    write(ex / "solution" / "work.py", "def count(words):\n    return len(words)\n")
    write(ex / "tests" / "test_work.py",
          "import unittest\nfrom work import count\n\n\nclass T(unittest.TestCase):\n"
          "    def test_count(self):\n        self.assertEqual(count(['a', 'b']), 2)\n")
    dump(lesson / "quiz.json", {"schema": "nexika.quiz/1", "questions": QUESTIONS})
    monkeypatch.setattr(pack, "COURSES", courses)
    return course


def problems(course_path: Path) -> list[pack.Problem]:
    course = pack.load_course(course_path)
    found = pack.check_course(course) + pack.check_syllabi(course)
    for lesson in course.lessons:
        found += gates.check_lesson(course, lesson)
    return found


def lesson_path(course: Path) -> Path:
    return course / "lessons" / "l1-count-tokens"


def edit_json(path: Path, change) -> None:
    data = json.loads(path.read_text(encoding="utf-8"))
    change(data)
    dump(path, data)


# ---------------------------------------------------------------- the good lesson

def test_a_complete_lesson_passes_every_gate(root):
    assert problems(root) == []
    course = pack.load_course(root)
    rows = cli.lesson_rows(course, course.lessons)
    assert [r["status"] for r in rows] == ["checked", "planned"]


# ---------------------------------------------------------------- one fault per gate

def test_claims_catch_text_and_code_disagreeing(root):
    edit_json(lesson_path(root) / "claims.json", lambda d: d["claims"][0].update(expect=4))
    assert any("the code gives 3" in p.message for p in problems(root))


def test_claims_need_their_words_in_every_language(root):
    edit_json(lesson_path(root) / "claims.json", lambda d: d["claims"][0].update(says_ar="غير موجود"))
    assert any("says_ar" in p.message for p in problems(root))


def test_exercise_tests_must_fail_on_the_starter(root):
    write(lesson_path(root) / "exercise" / "starter" / "work.py", "def count(words):\n    return len(words)\n")
    assert any("pass on the starter" in p.message for p in problems(root))


def test_exercise_tests_must_pass_on_the_solution(root):
    write(lesson_path(root) / "exercise" / "solution" / "work.py", "def count(words):\n    return 0\n")
    assert any("fail on the solution" in p.message for p in problems(root))


def test_quiz_catches_an_answer_given_away_by_length(root):
    def longer(d):
        d["questions"][1]["options"][1] = both("Three, because the list holds exactly three words", "ثلاثة لأن القائمة فيها ثلاث كلمات بالضبط")
    edit_json(lesson_path(root) / "quiz.json", longer)
    assert any("clearly the longest" in p.message for p in problems(root))


def test_quiz_catches_answers_all_in_one_place_and_missing_explanations(root):
    def same(d):
        for q in d["questions"][:3]:
            q["options"][0], q["options"][q["answer"]] = q["options"][q["answer"]], q["options"][0]
            q["answer"] = 0
        d["questions"][0]["explain"] = both("", "")
    edit_json(lesson_path(root) / "quiz.json", same)
    found = [p.message for p in problems(root)]
    assert any("same position" in m for m in found) and any("explain" in m for m in found)


def test_sources_catch_an_uncited_number(root):
    write(lesson_path(root) / "en.md", EN.replace("tokens[^tok].", "tokens[^tok]. Prices fell 40% last year."))
    assert any("a number with no source" in p.message for p in problems(root))


def test_sources_catch_a_missing_or_stale_source(root):
    def stale(d):
        d["sources"]["tok"]["retrieved"] = "2020-01-01"
    edit_json(lesson_path(root) / "sources.json", stale)
    write(lesson_path(root) / "ar.md", AR.replace("[^tok]", "[^nothing]"))
    found = [p.message for p in problems(root)]
    assert any("read it again" in m for m in found) and any("has no nothing" in m for m in found)


def test_links_must_resolve_inside_the_course(root):
    write(lesson_path(root) / "en.md", EN + "\nSee [the setup](../l0-missing/en.md) and [x](../../../../etc/passwd).\n")
    found = [p.message for p in problems(root)]
    assert any("does not exist" in m for m in found) and any("outside the course" in m for m in found)


def test_structure_catches_language_drift_and_forward_prerequisites(root):
    write(lesson_path(root) / "ar.md", AR.replace("## جرّبها", "جرّبها"))
    edit_json(lesson_path(root) / "lesson.json", lambda d: d.update(prerequisites=["l1-later"]))
    found = [p.message for p in problems(root)]
    assert any("heading structure" in m for m in found) and any("comes after" in m for m in found)


# ---------------------------------------------------------------- status from reviews

def review(course: Path, **parts) -> None:
    dump(lesson_path(course) / "review.json", {"schema": "nexika.review/1", **parts})


def test_status_climbs_with_reviews_of_the_current_content(root):
    course = pack.load_course(root)
    lesson = course.lessons[0]
    digest = pack.content_hash(lesson, course)
    fact = [{"by": "agent:a", "result": "pass", "hash": digest}, {"by": "agent:b", "result": "pass", "hash": digest}]
    teach = [{"by": "agent:c", "result": "pass", "hash": digest}]
    review(root, fact_checks=fact[:1], teaching=teach)
    assert pack.status(course, lesson, [])["status"] == "checked"  # one fact check is not enough
    review(root, fact_checks=fact, teaching=teach)
    assert pack.status(course, lesson, [])["status"] == "reviewed"
    review(root, fact_checks=fact, teaching=teach, learners={"attempts": 3, "passes": 2, "hash": digest},
           experts=[{"github": "someone", "verdict": "approve", "hash": digest}])
    found = pack.status(course, lesson, [])
    assert found["status"] == "verified" and found["experts"] == ["someone"]
    assert pack.status(course, lesson, [pack.Problem("quiz", "x", "y")])["status"] == "draft"


def test_changing_the_lesson_voids_old_reviews(root):
    course = pack.load_course(root)
    lesson = course.lessons[0]
    digest = pack.content_hash(lesson, course)
    review(root, fact_checks=[{"by": "a", "result": "pass", "hash": digest}, {"by": "b", "result": "pass", "hash": digest}],
           teaching=[{"by": "c", "result": "pass", "hash": digest}])
    assert pack.status(course, lesson, [])["status"] == "reviewed"
    write(lesson_path(root) / "en.md", EN + "\nOne more sentence.\n")
    assert pack.content_hash(lesson, course) != digest
    assert pack.status(course, lesson, [])["status"] == "checked"


def test_a_failed_review_holds_the_lesson_back(root):
    course = pack.load_course(root)
    lesson = course.lessons[0]
    digest = pack.content_hash(lesson, course)
    review(root, fact_checks=[{"by": "a", "result": "pass", "hash": digest}, {"by": "b", "result": "pass", "hash": digest},
                              {"by": "d", "result": "fail", "hash": digest}],
           teaching=[{"by": "c", "result": "pass", "hash": digest}])
    assert pack.status(course, lesson, [])["status"] == "checked"


# ---------------------------------------------------------------- coverage, syllabi, CLI

def test_coverage_counts_lessons_with_an_exercise_and_a_quiz(root):
    found = pack.coverage(pack.load_course(root))
    assert (found["covered"], found["total"]) == (1, 2)


def test_syllabi_must_map_or_rule_out_every_topic(root):
    dump(root / "syllabi" / "outside.json", {"schema": "nexika.syllabus/1",
                                             "source": {"url": "https://example.org", "retrieved": TODAY},
                                             "topics": [{"topic": "Tokens", "maps_to": ["c1.count"]},
                                                        {"topic": "Robots", "out_of_scope": "not this course"},
                                                        {"topic": "Forgotten"},
                                                        {"topic": "Typo", "maps_to": ["c9.nope"]}]})
    found = [p.message for p in problems(root)]
    assert any("Forgotten" in m for m in found) and any("c9.nope" in m for m in found)
    assert not any("Robots" in m or "'Tokens'" in m for m in found)


def test_cli_exit_codes(root, capsys):
    assert cli.main(["check"]) == 0
    assert cli.main(["coverage", "--min", "60"]) == 1
    assert cli.main(["hash", "demo/l1-count-tokens"]) == 0
    assert len(capsys.readouterr().out.strip().splitlines()[-1]) == 16
    edit_json(lesson_path(root) / "claims.json", lambda d: d["claims"][0].update(expect=9))
    assert cli.main(["check", "demo/l1-count-tokens"]) == 1
    with pytest.raises(SystemExit):
        cli.main(["check", "demo/l9-none"])


# ---------------------------------------------------------------- review findings

def test_the_claim_words_must_state_the_value(root):
    def five(d):
        d["claims"][0].update(says="has 3 entries", expect=3)
    edit_json(lesson_path(root) / "claims.json", five)
    write(lesson_path(root) / "en.md", EN.replace("has 3 entries", "has 3 entries"))
    assert problems(root) == []
    edit_json(lesson_path(root) / "claims.json", lambda d: d["claims"][0].update(says="The word list", expect=3))
    assert any("does not state the value" in p.message for p in problems(root))


def test_a_short_claim_does_not_exempt_other_numbers(root):
    write(lesson_path(root) / "en.md", EN.replace("has 3 entries.", "has 3 entries. It costs $75 per million."))
    assert any("$75" in p.message for p in problems(root))


def test_numbers_in_tables_and_plain_inline_code_need_a_source(root):
    write(lesson_path(root) / "en.md", EN + "\n| Model | Price |\n|---|---|\n| Big | 75 |\n\nA `1000000` token window.\n")
    found = [p.message for p in problems(root)]
    assert any("Big" in m for m in found) and any("1000000" in m for m in found)


def test_a_future_retrieved_date_is_refused(root):
    edit_json(lesson_path(root) / "sources.json", lambda d: d["sources"]["tok"].update(retrieved="2099-12-31"))
    assert any("in the future" in p.message for p in problems(root))


def test_compiled_code_and_links_in_code_folders_are_refused(root):
    write(lesson_path(root) / "exercise" / "tests" / "__pycache__" / "test_work.cpython-313.pyc", "x")
    (lesson_path(root) / "claims" / "link.py").symlink_to("/etc/hostname")
    found = [p.message for p in problems(root)]
    assert any("compiled or cached" in m for m in found) and any("symbolic link" in m for m in found)


def test_forged_reviews_are_refused(root):
    review(root, learners={"attempts": 1, "passes": 9, "hash": "x"},
           experts=[{"github": "torvalds", "verdict": "approve", "hash": "x", "link": "https://example.org"}])
    found = [p.message for p in problems(root)]
    assert any("passes <= attempts" in m for m in found) and any("review issue" in m for m in found)


def test_structure_reports_mismatches_unlisted_folders_and_bad_json(root):
    edit_json(lesson_path(root) / "lesson.json", lambda d: d.update(level=5))
    write(root / "lessons" / "l1-stray" / "en.md", "# Stray\n")
    write(lesson_path(root) / "quiz.json", "{not json")
    found = [p.message for p in problems(root)]
    assert any("module and level" in m for m in found) and any("l1-stray" in m for m in found)


def test_code_comments_are_not_headings(root):
    write(lesson_path(root) / "en.md", EN + "\n```bash\n# run it\npython count.py\n```\n")
    assert not any("heading structure" in p.message for p in problems(root))


def test_status_runs_no_code_and_says_unchecked_after_a_change(root, monkeypatch, tmp_path):
    monkeypatch.setattr(cli, "RESULTS", tmp_path / "results.json")
    assert cli.main(["check", "demo"]) == 0
    course = pack.load_course(root)
    assert cli.lesson_rows(course, course.lessons, run=False)[0]["status"] == "checked"
    write(lesson_path(root) / "en.md", EN + "\nChanged.\n")
    course = pack.load_course(root)
    assert cli.lesson_rows(course, course.lessons, run=False)[0]["status"] == "unchecked"


def test_guard_blocks_protected_changes_from_others(monkeypatch, capsys):
    monkeypatch.setattr(cli.subprocess, "run", lambda *a, **k: type("R", (), {"stdout": "courses/x/lessons/l1-a/review.json\ncourses/x/lessons/l1-a/en.md\n"})())
    assert cli.main(["guard", "--base", "origin/main", "--author", "someone-else"]) == 1
    assert "review.json" in capsys.readouterr().out
    assert cli.main(["guard", "--base", "origin/main", "--author", "loaiattar"]) == 0


def test_every_course_language_is_required(root):
    edit_json(root / "course.json", lambda d: d.update(languages=["en", "ar", "fr"]))
    found = [p.message for p in problems(root)]
    assert any("fr.md is missing" in m for m in found)
    assert any("title" in m and "fr" in m for m in found)
    assert any("says_fr" in m for m in found)
    assert any("prompt in every language" in m for m in found)


def test_numbers_can_be_written_in_each_language_style():
    assert gates.states_value("costs 0,009 $", 0.009)
    assert gates.states_value("costs $0.009", 0.009)
    assert gates.states_value("2 000 tokens", 2000) and gates.states_value("2,000 tokens", 2000)
    assert gates.states_value("٢٬٠٠٠ رمز", 2000) and gates.states_value("٠٫٠٠٩", 0.009)
    assert not gates.states_value("costs 0,009 $", 9.5)


def test_old_documentation_addresses_must_be_replaced(root):
    edit_json(root / "course.json", lambda d: d.update(cite_final={"example.org": "example.com"}))
    assert any("cite the final address" in p.message for p in problems(root))


def test_ignored_caches_are_not_part_of_the_lesson_but_tracked_bytecode_is(root):
    import subprocess
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text("__pycache__/\n")
    lesson = pack.load_course(root).lessons[0]
    before = pack.content_hash(lesson)
    write(lesson_path(root) / "exercise" / "tests" / "__pycache__" / "test_work.cpython-313.pyc", "x")
    assert pack.content_hash(lesson) == before
    assert not any("compiled or cached" in p.message for p in problems(root))
    subprocess.run(["git", "-C", str(root), "add", "-f", "."], check=True)
    assert any("compiled or cached" in p.message for p in problems(root))


def test_quotes_match_pages_despite_spaces_left_by_removed_tags():
    page = gates._normal(gates._html_text("<p>Use <code>max_tokens</code>, then read the <b>usage</b> .</p>"))
    assert gates._normal("Use max_tokens, then read the usage.") in page
    assert gates._normal("use max_tokens, then") not in page


def test_every_citation_has_its_footnote_line(root):
    path = lesson_path(root) / "en.md"
    text = path.read_text(encoding="utf-8")
    path.write_text("\n".join(line for line in text.splitlines() if not line.startswith("[^tok]:")) + "\n", encoding="utf-8")
    assert any("no [^tok]: line" in p.message for p in problems(root))
