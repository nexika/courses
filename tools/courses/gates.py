"""The machine gates: claims, exercise, quiz, sources and links. Each returns a list of problems."""
from __future__ import annotations

import datetime
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import unquote

from .pack import Course, Lesson, Problem

CITE = re.compile(r"\[\^([\w.-]+)\]")
CITE_DEF = re.compile(r"^\[\^[\w.-]+\]:", re.M)
FENCE = re.compile(r"```.*?```", re.S)
INLINE_CODE = re.compile(r"`[^`]*`")
LINK = re.compile(r"\]\(([^)\s]+)\)")
SENTENCE = re.compile(r"(?<=[.!?؟])\s+")
LIST_NUMBER = re.compile(r"^\s*(?:\d+[.)]|[-*])\s+")
STALE_DAYS = 45
RUN_TIMEOUT = 120
LENGTH_GIVEAWAY = 1.25      # the right option is clearly the longest
LONGEST_SHARE = 1 / 3       # across a quiz, the right option may be the longest at most this often


def _where(course: Course, lesson: Lesson) -> str:
    return f"{course.id}/{lesson.id}"


def _run(argv: list[str], cwd: Path) -> tuple[int, str, str]:
    """Lesson code runs with no secrets: a minimal environment and a throwaway home folder.
    It is still code from the lesson: run `courses check` only on content you have read (see FORMAT.md)."""
    with tempfile.TemporaryDirectory(prefix="courses-home-") as home:
        env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": home, "LANG": "C.UTF-8",
               "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "TMPDIR": home}
        try:
            done = subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=RUN_TIMEOUT, check=False,
                                  stdin=subprocess.DEVNULL, env=env)
        except subprocess.TimeoutExpired:
            return 124, "", f"timed out after {RUN_TIMEOUT} s"
    return done.returncode, done.stdout or "", done.stderr or ""


def _says_key(lang: str) -> str:
    return "says" if lang == "en" else f"says_{lang}"


# ------------------------------------------------------------------ claims

DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
NUMBER = re.compile(r"-?\d+(?:\.\d+)?")


def _matches(value, expect) -> bool:
    if isinstance(expect, dict) and "approx" in expect:
        try:
            return abs(float(value) - float(expect["approx"])) <= float(expect.get("tol", 0))
        except (TypeError, ValueError):
            return False
    return type(value) is type(expect) and value == expect


GROUPED = re.compile(r"(?<=\d)[\u00a0\u202f\u2009 ](?=\d{3}\b)")


def _numbers(text: str) -> list[float]:
    """Every number the text writes, in English, French or Arabic style: 2,000.5 / 2 000,5 / ٢٬٠٠٠٫٥.

    A comma is read both ways (thousands separator, decimal comma), so either style can state a value.
    """
    flat = GROUPED.sub("", text.translate(DIGITS)).replace("٬", "").replace("٫", ".")
    found = [float(n) for n in NUMBER.findall(flat.replace(",", ""))]
    found += [float(n) for n in NUMBER.findall(flat.replace(",", "."))]
    return found


def states_value(says: str, expect) -> bool:
    """The claim's own words state the value the code must produce."""
    if isinstance(expect, dict) and "approx" in expect:
        try:
            x, tol = float(expect["approx"]), float(expect.get("tol", 0))
        except (TypeError, ValueError):
            return False
        return any(abs(n - x) <= tol for n in _numbers(says))
    if isinstance(expect, bool) or expect is None:
        return False
    if isinstance(expect, (int, float)):
        return float(expect) in _numbers(says)
    return str(expect) in says


def check_claims(course: Course, lesson: Lesson) -> list[Problem]:
    where, problems = _where(course, lesson), []
    data = lesson.json("claims.json")
    if not data:
        return problems
    if data.get("schema") != "nexika.claims/1":
        problems.append(Problem("claims", where, "claims.json: schema must be nexika.claims/1"))
    for claim in data.get("claims", []):
        cid = claim.get("id", "?")
        for lang in course.languages:
            says = claim.get(_says_key(lang)) or ""
            if not says or says not in lesson.text(lang):
                problems.append(Problem("claims", where,
                                        f"claim {cid}: {_says_key(lang)} missing or not in {lang}.md: {says!r}"))
            elif not states_value(says, claim.get("expect")):
                problems.append(Problem("claims", where, f"claim {cid}: {_says_key(lang)} does not state "
                                                         f"the value {claim.get('expect')!r}"))
        script = lesson.path / "claims" / str(claim.get("check") or "")
        if not claim.get("check") or not script.is_file() or script.parent != lesson.path / "claims":
            problems.append(Problem("claims", where,
                                    f"claim {cid}: check script claims/{claim.get('check')} not found"))
            continue
        code, out, err = _run([sys.executable, "-I", "-B", script.name], script.parent)
        lines = [line for line in out.strip().splitlines() if line.strip()]
        out = out + err
        try:
            value = json.loads(lines[-1]) if code == 0 and lines else None
        except ValueError:
            value = None
        if code != 0 or value is None:
            problems.append(Problem("claims", where, f"claim {cid}: check failed (exit {code}): {out.strip()[-200:]}"))
        elif not _matches(value, claim.get("expect")):
            problems.append(Problem("claims", where,
                                    f"claim {cid}: the code gives {value!r}, the text says {claim.get('expect')!r}"))
    return problems


# ------------------------------------------------------------------ exercise

SKIP = shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo")


def _run_tests(code_dir: Path, tests_dir: Path) -> tuple[int, str]:
    with tempfile.TemporaryDirectory(prefix="courses-") as tmp:
        work = Path(tmp)
        shutil.copytree(code_dir, work, dirs_exist_ok=True, ignore=SKIP, symlinks=True)
        shutil.copytree(tests_dir, work / "tests", dirs_exist_ok=True, ignore=SKIP, symlinks=True)
        (work / "tests" / "__init__.py").touch()  # discovery from the top folder needs a package
        code, out, err = _run([sys.executable, "-I", "-B", "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                              work)
        return code, out + err


def check_exercise(course: Course, lesson: Lesson) -> list[Problem]:
    where, problems = _where(course, lesson), []
    folder = lesson.path / "exercise"
    meta = lesson.json("exercise/exercise.json")
    if not meta:
        return [Problem("exercise", where, "exercise/exercise.json is missing")]
    if meta.get("schema") != "nexika.exercise/1" or meta.get("runner") != "python-unittest":
        problems.append(Problem("exercise", where, "exercise.json: schema nexika.exercise/1, runner python-unittest"))
    goal = meta.get("goal") or {}
    if not all(isinstance(goal.get(lang), str) and goal[lang].strip() for lang in course.languages):
        problems.append(Problem("exercise", where, "exercise.json: goal in every language"))
    for part in ("starter", "solution", "tests"):
        if not (folder / part).is_dir():
            problems.append(Problem("exercise", where, f"exercise/{part}/ is missing"))
    if problems:
        return problems
    code, out = _run_tests(folder / "starter", folder / "tests")
    if "Ran 0 tests" in out:
        problems.append(Problem("exercise", where, "no tests were found"))
    elif re.search(r"\b(SyntaxError|ImportError|ModuleNotFoundError|IndentationError)\b", out):
        problems.append(Problem("exercise", where, "the starter does not load; give it stubs the tests can call"))
    elif code == 0:
        problems.append(Problem("exercise", where, "the tests pass on the starter: they do not test the exercise"))
    code, out = _run_tests(folder / "solution", folder / "tests")
    if code != 0:
        problems.append(Problem("exercise", where, f"the tests fail on the solution: {out.strip()[-300:]}"))
    return problems


# ------------------------------------------------------------------ quiz

def check_quiz(course: Course, lesson: Lesson) -> list[Problem]:
    where, problems, langs = _where(course, lesson), [], course.languages
    data = lesson.json("quiz.json")
    if not data:
        return [Problem("quiz", where, "quiz.json is missing")]
    if data.get("schema") != "nexika.quiz/1":
        problems.append(Problem("quiz", where, "quiz.json: schema must be nexika.quiz/1"))
    questions = data.get("questions") or []
    if not questions:
        problems.append(Problem("quiz", where, "quiz.json has no questions"))

    def filled(value) -> bool:
        return isinstance(value, dict) and all(isinstance(value.get(lang), str) and value[lang].strip()
                                               for lang in langs)

    longest, answers, choices = 0, [], 0
    for q in questions:
        qid = q.get("id", "?")
        if not filled(q.get("prompt")):
            problems.append(Problem("quiz", where, f"{qid}: prompt in every language"))
        if q.get("type") == "open":
            if not filled(q.get("rubric")):
                problems.append(Problem("quiz", where, f"{qid}: an open question needs a rubric in every language"))
            continue
        if q.get("type") != "choice":
            problems.append(Problem("quiz", where, f"{qid}: type must be choice or open"))
            continue
        choices += 1
        options = q.get("options") or []
        answer = q.get("answer")
        if len(options) != 4 or not all(filled(o) for o in options):
            problems.append(Problem("quiz", where, f"{qid}: four options, each in every language"))
            continue
        if not isinstance(answer, int) or isinstance(answer, bool) or not 0 <= answer < 4:
            problems.append(Problem("quiz", where, f"{qid}: answer must be 0-3"))
            continue
        for lang in langs:
            if len({o[lang].strip().lower() for o in options}) != 4:
                problems.append(Problem("quiz", where, f"{qid}: two options are the same ({lang})"))
        if not filled(q.get("explain")):
            problems.append(Problem("quiz", where, f"{qid}: explain in every language"))
        answers.append(answer)
        for lang in langs:
            sizes = [len(o[lang]) for o in options]
            right = sizes[answer]
            others = sorted((s for i, s in enumerate(sizes) if i != answer), reverse=True)
            if right > others[0] * LENGTH_GIVEAWAY:
                problems.append(Problem("quiz", where, f"{qid}: the right option is clearly the longest ({lang})"))
            if lang == langs[0] and right > others[0]:
                longest += 1
    if choices >= 3:
        if longest / choices > LONGEST_SHARE:
            problems.append(Problem("quiz", where,
                                    f"the right option is the longest in {longest} of {choices} questions"))
        if len(set(answers)) == 1:
            problems.append(Problem("quiz", where, "every right answer is in the same position"))
    return problems


# ------------------------------------------------------------------ sources

CODE_LIKE = re.compile(r"[A-Za-z_=(]")


def _paragraphs(text: str) -> list[str]:
    """Prose, headings, table rows and quotes, with hard-wrapped lines joined back into paragraphs."""
    text = FENCE.sub("\n\n", text)
    blocks, current = [], []
    for line in text.splitlines():
        if CITE_DEF.match(line):
            continue
        stripped = line.strip().lstrip(">").strip()
        if not stripped or stripped.startswith(("#", "|")):
            if current:
                blocks.append(" ".join(current))
                current = []
            if stripped:
                blocks.append(stripped.strip("#").replace("|", " ; "))
            continue
        current.append(stripped)
    if current:
        blocks.append(" ".join(current))
    return blocks


def uncited_numbers(text: str, claims: list[str], plain: list[str] | None = None) -> list[str]:
    """Sentences that state a number with no citation, outside the words of a checked claim.

    `plain` lists patterns of numbers that are names, not facts (`Python 3.10`, `Level 0`); the course
    declares them in course.json so they are reviewed like anything else.
    """
    allowed = [re.compile(p) for p in plain or []]
    found = []
    for paragraph in _paragraphs(text):
        for sentence in SENTENCE.split(paragraph):
            if CITE.search(sentence):
                continue
            bare = LIST_NUMBER.sub("", sentence)
            for says in claims:
                if says and len(says) >= 3:
                    bare = bare.replace(says, " ")
            bare = INLINE_CODE.sub(lambda m: " " if CODE_LIKE.search(m.group(0)) else m.group(0)[1:-1], bare)
            for pattern in allowed:
                bare = pattern.sub(" ", bare)
            if re.search(r"\d", bare.translate(DIGITS)):
                found.append(sentence.strip()[:160])
    return found


class _HttpsOnly(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not newurl.startswith("https://"):
            raise urllib.error.HTTPError(newurl, code, "redirect away from https refused", headers, fp)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def _page_text(url: str, budget: float = 30.0) -> str:
    """The page's text: https only (redirects too), at most 3 MB, at most `budget` seconds in all."""
    opener = urllib.request.build_opener(_HttpsOnly)
    request = urllib.request.Request(url, headers={"User-Agent": "nexika-courses-checker/1"})
    deadline, chunks, size = time.monotonic() + budget, [], 0
    with opener.open(request, timeout=10) as response:
        while size < 3_000_000:
            if time.monotonic() > deadline:
                raise TimeoutError(f"slower than {budget:.0f} s")
            chunk = response.read(65536)
            if not chunk:
                break
            chunks.append(chunk)
            size += len(chunk)
    return _html_text(b"".join(chunks).decode("utf-8", "replace"))


def _html_text(raw: str) -> str:
    raw = re.sub(r"(?is)<(script|style).*?</\1>", " ", raw)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", raw)))


def _normal(text: str) -> str:
    """Whitespace folded; case kept, so a quote must match the page exactly ("200k" is not "200K").

    Spaces before closing punctuation and after an opening bracket are dropped on both sides, because
    removing HTML tags leaves them ("<code>x</code>, y" reads "x , y")."""
    text = re.sub(r"\s+", " ", text)
    return re.sub(r"\s+(?=[,.;:!?)\]])|(?<=[(\[])\s+", "", text).strip()


def check_sources(course: Course, lesson: Lesson, online: bool = False,
                  today: datetime.date | None = None) -> list[Problem]:
    where, problems = _where(course, lesson), []
    data = lesson.json("sources.json")
    sources = (data.get("sources") or {}) if data else {}
    if data and data.get("schema") != "nexika.sources/1":
        problems.append(Problem("sources", where, "sources.json: schema must be nexika.sources/1"))
    today = today or datetime.date.today()
    cited: set[str] = set()
    claims = lesson.json("claims.json").get("claims", []) if (lesson.path / "claims.json").is_file() else []
    for lang in course.languages:
        text = lesson.text(lang)
        ids = set(CITE.findall(text))
        cited |= ids
        for sid in sorted(ids - set(sources)):
            problems.append(Problem("sources", where, f"{lang}.md cites [^{sid}] but sources.json has no {sid}"))
        says = [c.get(_says_key(lang)) or "" for c in claims]
        for sentence in uncited_numbers(text, says, course.meta.get("plain_numbers") or []):
            problems.append(Problem("sources", where,
                                    f"{lang}.md: a number with no source or checked claim: {sentence!r}"))
    for sid, src in sources.items():
        if sid not in cited:
            problems.append(Problem("sources", where, f"source {sid} is never cited"))
        url = str(src.get("url", ""))
        if not url.startswith("https://"):
            problems.append(Problem("sources", where, f"source {sid}: url must be https"))
        for old, final in (course.meta.get("cite_final") or {}).items():
            if url.startswith(f"https://{old}/"):
                problems.append(Problem("sources", where,
                                        f"source {sid}: {old} redirects to {final}; cite the final address"))
        if len(str(src.get("quote", "")).strip()) < 20:
            problems.append(Problem("sources", where, f"source {sid}: quote the words that support the text"))
        if src.get("kind") not in ("doc", "spec", "paper", "book", "repo"):
            problems.append(Problem("sources", where, f"source {sid}: kind must be doc, spec, paper, book or repo"))
        try:
            read = datetime.date.fromisoformat(str(src.get("retrieved")))
        except ValueError:
            problems.append(Problem("sources", where, f"source {sid}: retrieved must be YYYY-MM-DD"))
            continue
        if read > today:
            problems.append(Problem("sources", where, f"source {sid}: retrieved {read} is in the future"))
        elif src.get("volatile") and (today - read).days > STALE_DAYS:
            problems.append(Problem("stale", where, f"source {sid}: volatile and last read {read}: read it again"))
        if online and url.startswith("https://"):
            try:
                page = _normal(_page_text(url))
            except Exception as error:  # noqa: BLE001 (any network failure is reported, not raised)
                problems.append(Problem("sources", where, f"source {sid}: could not read {url}: {error}"))
                continue
            if _normal(src.get("quote", "")) not in page:
                problems.append(Problem("sources", where, f"source {sid}: the quote is not on {url}"))
    return problems


# ------------------------------------------------------------------ links

def check_links(course: Course, lesson: Lesson) -> list[Problem]:
    where, problems = _where(course, lesson), []
    root = lesson.path.resolve()
    course_root = course.path.resolve()
    for lang in course.languages:
        for target in LINK.findall(FENCE.sub(" ", lesson.text(lang))):
            if "://" in target or target.startswith(("#", "mailto:")):
                continue
            path = (root / unquote(target.split("#")[0])).resolve()
            if course_root not in path.parents and path != course_root:
                problems.append(Problem("links", where, f"{lang}.md links outside the course: {target}"))
            elif not path.exists():
                problems.append(Problem("links", where, f"{lang}.md links to {target}, which does not exist"))
    return problems


def check_lesson(course: Course, lesson: Lesson, online: bool = False) -> list[Problem]:
    if not lesson.exists:
        return []
    return (check_claims(course, lesson) + check_exercise(course, lesson) + check_quiz(course, lesson)
            + check_sources(course, lesson, online) + check_links(course, lesson))
