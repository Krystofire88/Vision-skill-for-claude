#!/usr/bin/env python3
"""Guard for VISION.md and the documents that cite it.

Three checks, all portable — no project language, framework or test runner
involved:

  DEAD      a document cites a V- id that VISION.md does not define
  UNANSWERED an entry's A: block is empty
  ORPHAN    an entry nothing outside VISION.md cites

Plus structural checks on the file itself: duplicate ids, missing anchors, and
entries missing a provenance or cost tag.

Usage:
    vision_check.py [--root DIR] [--vision PATH] [--no-orphans] [--quiet]

Exit status: 0 clean, 1 problems found, 2 could not run.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ENTRY_RE = re.compile(r"^#{2,6}\s+(V-\d+)\s*(?:·|-|:)?\s*(.*)$")
ANCHOR_RE = re.compile(r'<a\s+id="(v-\d+)"\s*>', re.IGNORECASE)
CITE_RE = re.compile(r"\bV-\d+\b")
ANSWER_RE = re.compile(r"^\*\*A:?\*\*:?\s*(.*)$")

PROVENANCE = {"[SAID]", "[IMPLIED]", "[MINE]"}
COST = {"[BLOCKS]", "[COSTLY]", "[CHEAP]"}
WITHDRAWN = "[WITHDRAWN]"

SKIP_DIRS = {
    ".git", ".hg", ".svn", "node_modules", "target", "dist", "build",
    "vendor", ".venv", "venv", "__pycache__", ".next", ".cache",
    ".claude/worktrees",
}
SKIP_PATH_PARTS = {("docs", "suspended")}
TEXT_SUFFIXES = {
    ".md", ".markdown", ".txt", ".rst", ".adoc",
    ".rs", ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".kt",
    ".rb", ".c", ".h", ".cpp", ".hpp", ".cs", ".swift", ".sh", ".toml",
    ".yaml", ".yml", ".json",
}


class Entry:
    __slots__ = ("id", "title", "line", "tags", "answer", "withdrawn")

    def __init__(self, id_, title, line, tags):
        self.id = id_
        self.title = title
        self.line = line
        self.tags = tags
        self.answer = ""
        self.withdrawn = WITHDRAWN in tags


def parse_vision(path: Path):
    """Return (entries, anchors, problems) from a VISION.md."""
    problems = []
    entries = []
    seen = {}
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    anchors = {m.group(1).lower() for line in lines for m in [ANCHOR_RE.search(line)] if m}

    current = None
    collecting = False
    for n, line in enumerate(lines, 1):
        m = ENTRY_RE.match(line)
        if m:
            id_, rest = m.group(1), m.group(2)
            tags = set(re.findall(r"\[[A-Z]+\]", rest))
            current = Entry(id_, re.sub(r"`?\[[A-Z]+\]`?", "", rest).strip(" ·`"), n, tags)
            collecting = False
            if id_ in seen:
                problems.append(
                    f"DUPLICATE  {id_} defined twice — lines {seen[id_]} and {n}. "
                    f"Ids are never reused."
                )
            else:
                seen[id_] = n
                entries.append(current)
            continue
        if current is None:
            continue
        a = ANSWER_RE.match(line)
        if a:
            current.answer = a.group(1).strip()
            collecting = True
            continue
        if collecting:
            if not line.strip():
                collecting = False
            else:
                current.answer += " " + line.strip()

    for e in entries:
        if e.withdrawn:
            continue
        anchor = e.id.lower()
        if anchor not in anchors:
            problems.append(
                f"NO ANCHOR  {e.id} (line {e.line}) has no <a id=\"{anchor}\"> — "
                f"documents linking to it will not land."
            )
        if not e.tags & PROVENANCE:
            problems.append(
                f"NO TAG     {e.id} (line {e.line}) has no provenance tag "
                f"([SAID] / [IMPLIED] / [MINE])."
            )
        if not e.tags & COST:
            problems.append(
                f"NO TAG     {e.id} (line {e.line}) has no cost tag "
                f"([BLOCKS] / [COSTLY] / [CHEAP])."
            )

    return entries, anchors, problems


def skip(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    if any(p in SKIP_DIRS for p in parts):
        return True
    for combo in SKIP_PATH_PARTS:
        if len(parts) >= len(combo) and tuple(parts[: len(combo)]) == combo:
            return True
    return False


def scan_citations(root: Path, vision: Path):
    """Map cited id -> [(relative path, line number)]."""
    cites = {}
    for path in root.rglob("*"):
        if not path.is_file() or path == vision:
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if skip(path, root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if "V-" not in text:
            continue
        rel = path.relative_to(root)
        for n, line in enumerate(text.splitlines(), 1):
            for m in CITE_RE.finditer(line):
                cites.setdefault(m.group(0), []).append((str(rel), n))
    return cites


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--vision", default=None)
    ap.add_argument("--no-orphans", action="store_true",
                    help="skip the 'nothing cites this entry' check")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    vision = Path(args.vision).resolve() if args.vision else root / "VISION.md"
    if not vision.is_file():
        print(f"vision-check: no VISION.md at {vision}", file=sys.stderr)
        return 2

    entries, _, problems = parse_vision(vision)
    if not entries:
        print(f"vision-check: {vision} defines no V- entries", file=sys.stderr)
        return 2

    defined = {e.id for e in entries}
    live = [e for e in entries if not e.withdrawn]

    for e in live:
        if not e.answer:
            problems.append(
                f"UNANSWERED {e.id} · {e.title} (line {e.line}) — "
                f"blank A:. Only the author fills it in."
            )

    cites = scan_citations(root, vision)

    for cited, places in sorted(cites.items()):
        if cited not in defined:
            where = ", ".join(f"{p}:{n}" for p, n in places[:4])
            problems.append(
                f"DEAD       {cited} cited at {where} but VISION.md does not define it."
            )

    if not args.no_orphans:
        for e in live:
            if not e.answer:
                continue  # already reported as UNANSWERED; not an orphan too
            if e.id not in cites:
                problems.append(
                    f"ORPHAN     {e.id} · {e.title} — answered, but no document "
                    f"cites it. The ruling never left the file."
                )

    order = ["DUPLICATE", "DEAD", "UNANSWERED", "NO ANCHOR", "NO TAG", "ORPHAN"]
    def rank(p):
        for i, code in enumerate(order):
            if p.startswith(code):
                return i
        return len(order)
    problems.sort(key=lambda p: (rank(p), p))

    if problems:
        for p in problems:
            print(p)
        print(f"\nvision-check: {len(problems)} problem(s) across "
              f"{len(live)} live entries.")
        return 1

    if not args.quiet:
        print(f"vision-check: clean — {len(live)} entries, all answered, "
              f"all cited, no dead citations.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
