"""courses: check lessons, show their status, measure competency coverage."""
from __future__ import annotations

import argparse
import fnmatch
import json
import subprocess
import sys

from . import gates, pack

ICONS = {"planned": "·", "draft": "✗", "checked": "◐", "reviewed": "◑", "verified": "●", "unchecked": "?"}
RESULTS = pack.ROOT / ".courses" / "results.json"
PROTECTED = ("*review.json", "tools/*", "bin/*", ".github/*", "CODEOWNERS", "MAINTAINERS", "FORMAT.md",
             "REVIEWING.md", "pyproject.toml")


def _load_results() -> dict:
    try:
        return json.loads(RESULTS.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_results(results: dict) -> None:
    RESULTS.parent.mkdir(exist_ok=True)
    RESULTS.write_text(json.dumps(results, indent=1), encoding="utf-8")


def _select(target: str) -> list[tuple[pack.Course, list[pack.Lesson]]]:
    """'' = every course; 'course' = its lessons; 'course/lesson' = one lesson."""
    course_id, _, lesson_id = target.partition("/")
    picked = []
    for course in pack.all_courses():
        if course_id and course.id != course_id:
            continue
        lessons = [lesson for lesson in course.lessons if not lesson_id or lesson.id == lesson_id]
        if lesson_id and not lessons:
            continue
        picked.append((course, lessons))
    if target and not picked:
        raise SystemExit(f"courses: nothing called {target!r}")
    return picked


def cmd_check(args) -> int:
    """Runs every machine gate, lesson code included: only on content you have read."""
    problems: list[pack.Problem] = []
    one_lesson = "/" in args.target
    results = _load_results()
    for course, lessons in _select(args.target):
        structure = pack.check_course(course)
        if one_lesson:
            problems += [p for p in structure if p.where.endswith("/" + lessons[0].id)]
        else:
            problems += structure + pack.check_syllabi(course)
        for lesson in lessons:
            if not lesson.exists:
                continue
            mine = [p for p in structure if p.where.endswith("/" + lesson.id)]
            mine += gates.check_lesson(course, lesson, online=args.online)
            if one_lesson:
                problems += [p for p in mine if p not in problems]
            else:
                problems += [p for p in mine if p.gate != "structure" and p.gate != "review"]
            blocking = [p for p in mine if not (args.stale == "warn" and p.gate == "stale")]
            results[f"{course.id}/{lesson.id}"] = {"hash": pack.content_hash(lesson, course),
                                                  "problems": len(blocking)}
    _save_results(results)
    warnings = [p for p in problems if args.stale == "warn" and p.gate == "stale"]
    problems = [p for p in problems if p not in warnings]
    if args.json:
        print(json.dumps({"problems": [vars(p) for p in problems], "warnings": [vars(p) for p in warnings]},
                         ensure_ascii=False, indent=1))
    else:
        for problem in problems:
            print(problem)
        for warning in warnings:
            print(f"warning {warning}")
        print(f"{len(problems)} problem(s)" if problems else "All gates pass.")
    return 1 if problems else 0


def lesson_rows(course: pack.Course, lessons: list[pack.Lesson], run: bool = True) -> list[dict]:
    """Each lesson's status. Without `run`, lesson code is not executed: the result of the last
    `courses check` on the same content is used, and a lesson changed since then is `unchecked`."""
    structure = pack.check_course(course)
    results = _load_results()
    rows = []
    for lesson in lessons:
        machine = [p for p in structure if p.where.endswith("/" + lesson.id)]
        if run:
            machine += gates.check_lesson(course, lesson)
        found = pack.status(course, lesson, machine)
        if not run and lesson.exists:
            last = results.get(f"{course.id}/{lesson.id}") or {}
            if last.get("hash") != found["hash"]:
                found["status"] = "unchecked"
            elif last.get("problems"):
                found["status"] = "draft"
        title = (lesson.meta.get("title") or {}).get(course.languages[0], "")
        rows.append({"course": course.id, "lesson": lesson.id, "title": title, "module": lesson.module,
                     **found, "problems": len(machine)})
    return rows


def cmd_status(args) -> int:
    rows = [row for course, lessons in _select(args.target) for row in lesson_rows(course, lessons, args.run)]
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
        return 0
    for row in rows:
        experts = ", ".join(row["experts"]) or "open"
        extra = f"  {row['problems']} problem(s)" if row["problems"] else ""
        print(f"{ICONS[row['status']]} {row['status']:<9} {row['course']}/{row['lesson']:<32} "
              f"{row['hash'] or '-':<16} expert review: {experts}{extra}")
    return 0


def cmd_coverage(args) -> int:
    worst = 100.0
    report = []
    for course, _ in _select(args.target.split("/")[0]):
        found = pack.coverage(course)
        report.append({"course": course.id, **found})
        share = 100 * found["covered"] / found["total"] if found["total"] else 100.0
        worst = min(worst, share)
        if not args.json:
            print(f"{course.id}: {found['covered']}/{found['total']} competencies covered ({share:.0f}%)")
            for row in found["rows"]:
                where = ", ".join(row["lessons"]) or ("outside course" if row["external"] else "-")
                print(f"  {'✓' if row['covered'] else '·'} L{row['level']} {row['id']:<28} {where}")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=1))
    return 1 if args.min is not None and worst < args.min else 0


def cmd_hash(args) -> int:
    picked = _select(args.target)
    lessons = picked[0][1] if len(picked) == 1 else []
    if "/" not in args.target or len(lessons) != 1 or not lessons[0].exists:
        raise SystemExit("courses hash needs course/lesson of a lesson that exists")
    print(pack.content_hash(lessons[0], picked[0][0]))
    return 0


def cmd_guard(args) -> int:
    """CI: a pull request by someone who is not a maintainer may not touch reviews, tools or CI."""
    maintainers = {line.strip().lstrip("@").lower() for line in (pack.ROOT / "MAINTAINERS").read_text().splitlines()
                   if line.strip() and not line.startswith("#")} if (pack.ROOT / "MAINTAINERS").is_file() else set()
    if args.author.lower() in maintainers:
        print(f"{args.author} is a maintainer.")
        return 0
    changed = subprocess.run(["git", "diff", "--name-only", f"{args.base}...HEAD"], cwd=pack.ROOT,
                             capture_output=True, text=True, check=True).stdout.split()
    blocked = [f for f in changed if any(fnmatch.fnmatch(f, pattern) for pattern in PROTECTED)]
    for name in blocked:
        print(f"protected: {name} (reviews, tools and CI change only through a maintainer)")
    return 1 if blocked else 0


def parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(prog="courses", description="Check and track Nexika courses.", allow_abbrev=False)
    sub = top.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", allow_abbrev=False, help="run the machine gates (exit 1 on any problem)")
    p.add_argument("target", nargs="?", default="", help="course or course/lesson (default: everything)")
    p.add_argument("--online", action="store_true", help="also check that each quote is on its page")
    p.add_argument("--stale", choices=["fail", "warn"], default="fail", help="volatile sources past 45 days")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_check)
    p = sub.add_parser("status", allow_abbrev=False, help="each lesson's status (no code runs unless --run)")
    p.add_argument("target", nargs="?", default="")
    p.add_argument("--run", action="store_true", help="run the gates now, lesson code included")
    p.add_argument("--json", action="store_true")
    p.set_defaults(run=cmd_status)
    p = sub.add_parser("coverage", allow_abbrev=False, help="which competencies are taught")
    p.add_argument("target", nargs="?", default="")
    p.add_argument("--json", action="store_true")
    p.add_argument("--min", type=float, help="exit 1 below this percentage")
    p.set_defaults(run=cmd_coverage)
    p = sub.add_parser("hash", allow_abbrev=False, help="a lesson's content hash (reviews record it)")
    p.add_argument("target")
    p.set_defaults(run=cmd_hash)
    p = sub.add_parser("guard", allow_abbrev=False, help="CI: refuse protected changes from non-maintainers")
    p.add_argument("--base", required=True)
    p.add_argument("--author", required=True)
    p.set_defaults(run=cmd_guard)
    return top


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    return args.run(args)


def entry() -> None:
    sys.exit(main())
