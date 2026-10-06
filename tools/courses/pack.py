"""Loading a course, the structure gate, the content hash, status and competency coverage."""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COURSES = ROOT / "courses"
LESSON_ID = re.compile(r"^l\d+-[a-z0-9-]+$")
COMPETENCY_ID = re.compile(r"^c\d+\.[a-z0-9-]+$")
HEADING = re.compile(r"^(#{1,6})\s", re.M)
FENCE = re.compile(r"```.*?```", re.S)
STATUSES = ("planned", "draft", "checked", "reviewed", "verified")
EVIDENCE = ("exercise", "project", "quiz")
CODE_DIRS = ("claims", "exercise")
EXPERT_LINK = re.compile(r"^https://github\.com/nexika/courses/issues/\d+$")


@dataclass
class Problem:
    gate: str
    where: str
    message: str

    def __str__(self) -> str:
        return f"[{self.gate}] {self.where}: {self.message}"


@dataclass
class Lesson:
    id: str
    path: Path
    module: str
    order: int
    meta: dict = field(default_factory=dict)
    errors: list = field(default_factory=list)

    @property
    def exists(self) -> bool:
        return (self.path / "lesson.json").is_file()

    def json(self, name: str) -> dict:
        """The file's data, or {} when it is missing or does not parse (recorded in `errors`)."""
        target = self.path / name
        if not target.is_file():
            return {}
        try:
            return read_json(target)
        except (OSError, ValueError) as error:
            message = f"{name} cannot be read: {error}"
            if message not in self.errors:
                self.errors.append(message)
            return {}

    def text(self, lang: str) -> str:
        target = self.path / f"{lang}.md"
        return target.read_text(encoding="utf-8") if target.is_file() else ""


@dataclass
class Course:
    id: str
    path: Path
    meta: dict
    competencies: list[dict]
    lessons: list[Lesson]

    @property
    def languages(self) -> list[str]:
        return list(self.meta.get("languages") or ["en"])

    def lesson(self, lesson_id: str) -> Lesson | None:
        return next((item for item in self.lessons if item.id == lesson_id), None)


def read_json(path: Path) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a JSON object")
    return data


LOAD_ERRORS: dict[str, list[str]] = {}


def _safe_json(path: Path, errors: list[str]) -> dict:
    try:
        return read_json(path)
    except (OSError, ValueError) as error:
        errors.append(f"{path.name}: {error}")
        return {}


def load_course(path: Path) -> Course:
    """The course; files that do not parse become structure problems instead of crashing."""
    errors: list[str] = []
    meta = _safe_json(path / "course.json", errors)
    comps = _safe_json(path / "competencies.json", errors).get("competencies", []) \
        if (path / "competencies.json").is_file() else []
    lessons, order = [], 0
    for module in meta.get("modules", []) if isinstance(meta.get("modules"), list) else []:
        for lesson_id in module.get("lessons", []):
            lesson = Lesson(str(lesson_id), path / "lessons" / str(lesson_id), module.get("id", ""), order)
            if lesson.exists:
                lesson.meta = _safe_json(lesson.path / "lesson.json", errors)
            lessons.append(lesson)
            order += 1
    course = Course(meta.get("id", path.name), path, meta, comps if isinstance(comps, list) else [], lessons)
    LOAD_ERRORS[str(path)] = errors
    return course


def all_courses(root: Path | None = None) -> list[Course]:
    root = root or COURSES
    return [load_course(p) for p in sorted(root.iterdir()) if (p / "course.json").is_file()] \
        if root.is_dir() else []


# ------------------------------------------------------------------ hash

def lesson_files(lesson: Lesson) -> list[Path]:
    """The lesson's files as they would ship: inside a git checkout, what git tracks or would add (so caches
    that .gitignore keeps out, such as a learner's __pycache__, are not part of the lesson); elsewhere, all."""
    try:
        out = subprocess.run(["git", "ls-files", "-z", "--cached", "--others", "--exclude-standard", "--", "."],
                             cwd=lesson.path, capture_output=True, timeout=30, check=True).stdout
        top = subprocess.run(["git", "rev-parse", "--show-prefix"], cwd=lesson.path, capture_output=True,
                             text=True, timeout=30, check=True).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return sorted(p for p in lesson.path.rglob("*") if p.is_file() or p.is_symlink())
    names = {name[len(top):] if name.startswith(top) else name for name in out.decode().split("\0") if name}
    return sorted(lesson.path / name for name in names if (lesson.path / name).is_file()
                  or (lesson.path / name).is_symlink())


def content_hash(lesson: Lesson, course: Course | None = None) -> str:
    """A hash of everything a reviewer judges: every file of the lesson except review.json (images and
    bytecode included), plus the lesson's module and competencies in the course. Reviews carry it."""
    digest = hashlib.sha256()
    files = [p for p in lesson_files(lesson) if p.name != "review.json"]
    for file in files:
        digest.update(file.relative_to(lesson.path).as_posix().encode())
        digest.update(b"\0")
        digest.update(os.readlink(file).encode() if file.is_symlink() else file.read_bytes())
        digest.update(b"\0")
    if course is not None:
        wanted = set(lesson.meta.get("competencies", []))
        module = next((m for m in course.meta.get("modules", []) if lesson.id in m.get("lessons", [])), {})
        context = {"module": module, "competencies": [c for c in course.competencies if c.get("id") in wanted]}
        digest.update(json.dumps(context, sort_keys=True, ensure_ascii=False).encode())
    return digest.hexdigest()[:16]


def unsafe_files(lesson: Lesson) -> list[str]:
    """Files that would run without being what reviewers read: bytecode, caches, links, binaries."""
    found = []
    for p in lesson_files(lesson):
        rel = p.relative_to(lesson.path).as_posix()
        if rel.split("/")[0] in CODE_DIRS:
            if p.is_symlink():
                found.append(f"{rel} is a symbolic link")
            elif "__pycache__" in rel.split("/") or p.suffix in (".pyc", ".pyo", ".so", ".pyd", ".pth"):
                found.append(f"{rel} is compiled or cached code")
            elif p.is_file() and b"\0" in p.read_bytes()[:8192]:
                found.append(f"{rel} is a binary file")
    return found


# ------------------------------------------------------------------ structure gate

def _per_language(value, langs: list[str]) -> bool:
    return isinstance(value, dict) and all(isinstance(value.get(lang), str) and value[lang].strip() for lang in langs)


def check_course(course: Course) -> list[Problem]:
    problems: list[Problem] = []
    meta, langs, where = course.meta, course.languages, course.id

    def bad(message: str, at: str = where, gate: str = "structure") -> None:
        problems.append(Problem(gate, at, message))

    for error in LOAD_ERRORS.get(str(course.path), []):
        bad(f"cannot read {error}")

    if meta.get("schema") != "nexika.course/1":
        bad("course.json: schema must be nexika.course/1")
    for key in ("title", "audience"):
        if not _per_language(meta.get(key), langs):
            bad(f"course.json: {key} must be given in {', '.join(langs)}")
    level_ids = [level.get("id") for level in meta.get("levels", [])]
    for level in meta.get("levels", []):
        if not _per_language(level.get("title"), langs) or not _per_language(level.get("exit"), langs):
            bad(f"course.json: level {level.get('id')} needs title and exit in every language")
    comp_ids = [c.get("id") for c in course.competencies]
    if len(set(comp_ids)) != len(comp_ids):
        bad("competencies.json: duplicate ids")
    for comp in course.competencies:
        if not COMPETENCY_ID.match(comp.get("id") or ""):
            bad(f"competency id {comp.get('id')!r} must look like c1.call-api")
        if comp.get("level") not in level_ids:
            bad(f"competency {comp.get('id')}: level {comp.get('level')} is not a course level")
        if not _per_language(comp.get("can"), langs):
            bad(f"competency {comp.get('id')}: `can` must be given in every language")
        if comp.get("evidence") not in EVIDENCE:
            bad(f"competency {comp.get('id')}: evidence must be exercise, project or quiz")
    for ext in meta.get("external", []):
        for cid in ext.get("covers", []):
            if cid not in comp_ids:
                bad(f"external {ext.get('title')!r} covers unknown competency {cid}")
    ids = [lesson.id for lesson in course.lessons]
    if len(set(ids)) != len(ids):
        bad("a lesson id appears twice in the modules")
    for module in meta.get("modules", []):
        if module.get("level") not in level_ids or not _per_language(module.get("title"), langs):
            bad(f"module {module.get('id')}: needs a known level and a title in every language")
    order = {lesson.id: lesson.order for lesson in course.lessons}
    listed = set(order)
    folder = course.path / "lessons"
    for extra in sorted(p.name for p in folder.iterdir() if p.is_dir()) if folder.is_dir() else []:
        if extra not in listed:
            bad(f"lessons/{extra} is not listed in course.json, so nothing checks it")
    module_of = {lid: (m.get("id"), m.get("level")) for m in meta.get("modules", []) for lid in m.get("lessons", [])}
    for lesson in course.lessons:
        at = f"{course.id}/{lesson.id}"
        if not LESSON_ID.match(lesson.id):
            bad("lesson id must look like l1-what-is-an-llm", at)
        if not lesson.exists:
            continue
        lm = lesson.meta
        if lm.get("schema") != "nexika.lesson/1" or lm.get("id") != lesson.id:
            bad("lesson.json: schema nexika.lesson/1 and an id matching the folder", at)
        if not _per_language(lm.get("title"), langs):
            bad("lesson.json: title in every language", at)
        if (lm.get("module"), lm.get("level")) != module_of.get(lesson.id):
            bad("lesson.json: module and level must match where course.json lists the lesson", at)
        for problem in unsafe_files(lesson):
            bad(problem, at)
        for name, key in (("claims.json", "claims"), ("quiz.json", "questions")):
            ids = [item.get("id") for item in lesson.json(name).get(key, []) if isinstance(item, dict)] \
                if (lesson.path / name).is_file() else []
            if len(ids) != len(set(ids)):
                bad(f"{name}: duplicate ids", at)
        for problem in check_review(lesson):
            bad(problem, at, "review")
        for name in ("sources.json", "claims.json", "quiz.json", "exercise/exercise.json"):
            lesson.json(name)
        for error in lesson.errors:
            bad(error, at)
        if not isinstance(lm.get("minutes"), int) or lm["minutes"] <= 0:
            bad("lesson.json: minutes must be a positive whole number", at)
        if not lm.get("competencies"):
            bad("lesson.json: teaches no competency", at)
        for cid in lm.get("competencies", []):
            if cid not in comp_ids:
                bad(f"lesson.json: unknown competency {cid}", at)
        for pre in lm.get("prerequisites", []):
            if pre not in order:
                bad(f"prerequisite {pre} is not a lesson of the course", at)
            elif order[pre] >= lesson.order:
                bad(f"prerequisite {pre} comes after this lesson", at)
        headings = None
        for lang in langs:
            text = lesson.text(lang)
            if not text.strip():
                bad(f"{lang}.md is missing or empty", at)
                continue
            shape = [len(h) for h in HEADING.findall(FENCE.sub("", text))]
            if headings is None:
                headings = shape
            elif shape != headings:
                bad(f"{lang}.md has a different heading structure from {langs[0]}.md", at)
    return problems


# ------------------------------------------------------------------ review.json

def check_review(lesson: Lesson) -> list[str]:
    """What review.json may hold: well-formed entries, learners that add up, experts with a review issue."""
    if not (lesson.path / "review.json").is_file():
        return []
    try:
        review = read_json(lesson.path / "review.json")
    except (OSError, ValueError) as error:
        return [f"review.json cannot be read: {error}"]
    found = []
    if review.get("schema") != "nexika.review/1":
        found.append("review.json: schema must be nexika.review/1")
    for kind in ("fact_checks", "teaching"):
        for entry in review.get(kind, []):
            if not isinstance(entry, dict) or entry.get("result") not in ("pass", "fail") or not entry.get("by") \
                    or not entry.get("hash"):
                found.append(f"review.json: every {kind} entry needs by, result (pass or fail) and hash")
    learners = review.get("learners") or {}
    try:
        attempts, passes = int(learners.get("attempts") or 0), int(learners.get("passes") or 0)
    except (TypeError, ValueError):
        attempts, passes = 0, -1
    if passes < 0 or attempts < 0 or passes > attempts:
        found.append("review.json: learners need 0 <= passes <= attempts")
    for entry in review.get("experts", []):
        if not isinstance(entry, dict) or not entry.get("github") or not EXPERT_LINK.match(str(entry.get("link"))):
            found.append("review.json: an expert review needs a github handle and the link of its review issue")
    return found


# ------------------------------------------------------------------ status

def _current(entries: list[dict], digest: str) -> list[dict]:
    return [e for e in entries if isinstance(e, dict) and e.get("hash") == digest]


def status(course: Course, lesson: Lesson, machine_problems: list[Problem]) -> dict:
    """planned, draft, checked, reviewed or verified, and the expert reviewers of this version."""
    if not lesson.exists:
        return {"status": "planned", "hash": "", "experts": []}
    digest = content_hash(lesson, course)
    try:
        review = lesson.json("review.json")
    except (OSError, ValueError):
        review = {}
    experts = [e.get("github") for e in _current(review.get("experts", []), digest) if e.get("verdict") == "approve"]
    found = {"status": "draft", "hash": digest, "experts": experts}
    if machine_problems:
        return found
    found["status"] = "checked"
    facts = {e.get("by") for e in _current(review.get("fact_checks", []), digest) if e.get("result") == "pass"}
    failed = [e for e in _current(review.get("fact_checks", []) + review.get("teaching", []), digest)
              if e.get("result") == "fail"]
    teaching = [e for e in _current(review.get("teaching", []), digest) if e.get("result") == "pass"]
    if len(facts) < 2 or not teaching or failed:
        return found
    found["status"] = "reviewed"
    learners = review.get("learners") or {}
    rules = course.meta.get("verify") or {}
    attempts, passes = int(learners.get("attempts") or 0), int(learners.get("passes") or 0)
    if learners.get("hash") == digest and passes >= int(rules.get("min_learners", 3)) and attempts and \
            passes / attempts >= float(rules.get("min_pass_rate", 0.6)):
        found["status"] = "verified"
    return found


# ------------------------------------------------------------------ coverage and syllabi

def coverage(course: Course) -> dict:
    """Which competencies have a lesson with an exercise and a quiz, or an outside course."""
    external = {cid for ext in course.meta.get("external", []) for cid in ext.get("covers", [])}
    taught: dict[str, list[str]] = {}
    for lesson in course.lessons:
        if lesson.exists and (lesson.path / "exercise" / "exercise.json").is_file() and \
                (lesson.path / "quiz.json").is_file():
            for cid in lesson.meta.get("competencies", []):
                taught.setdefault(cid, []).append(lesson.id)
    rows = []
    for comp in course.competencies:
        cid = comp["id"]
        rows.append({"id": cid, "level": comp["level"], "lessons": taught.get(cid, []),
                     "external": cid in external, "covered": bool(taught.get(cid)) or cid in external})
    done = sum(1 for row in rows if row["covered"])
    return {"covered": done, "total": len(rows), "rows": rows}


def check_syllabi(course: Course) -> list[Problem]:
    """Every topic of an outside syllabus maps to our competencies or says why it is left out."""
    problems = []
    comp_ids = {c["id"] for c in course.competencies}
    folder = course.path / "syllabi"
    for path in sorted(folder.glob("*.json")) if folder.is_dir() else []:
        data = read_json(path)
        at = f"{course.id}/syllabi/{path.name}"
        source = data.get("source") or {}
        if data.get("schema") != "nexika.syllabus/1" or not source.get("url") or not source.get("retrieved"):
            problems.append(Problem("syllabi", at,
                                    "needs schema nexika.syllabus/1 and a source with url and retrieved"))
        for topic in data.get("topics", []):
            maps, out = topic.get("maps_to") or [], topic.get("out_of_scope")
            if not maps and not out:
                problems.append(Problem("syllabi", at, f"topic {topic.get('topic')!r} is neither mapped nor ruled out"))
            for cid in maps:
                if cid not in comp_ids:
                    problems.append(Problem("syllabi", at, f"topic {topic.get('topic')!r} maps to unknown {cid}"))
    return problems


def today() -> datetime.date:
    return datetime.date.today()
