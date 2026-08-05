#!/usr/bin/env python3
"""Mechanical verifier for vision-eval fixture runs.

Hand-grepping gave misleading answers twice (a filter that excluded the file it
should have read; a heuristic that mistook correct citations for survivals), so
every claim a run makes is checked here instead.

    verify.py build <dir>          a /vision-build run
    verify.py build-mc <dir>       ... where the author asked for lettered options
    verify.py apply <dir>          a /vision-apply run that wrote
    verify.py refuse <dir>         a run that should have written nothing
"""
from __future__ import annotations
import re
import subprocess
import sys
from pathlib import Path

OK, BAD = "  ok    ", "  FAIL  "
fails = 0


def check(desc, cond, detail=""):
    global fails
    if cond:
        print(OK + desc)
    else:
        fails += 1
        print(BAD + desc + (f"  [{detail}]" if detail else ""))


def git(d, *args):
    return subprocess.run(["git", "-C", str(d), *args],
                          capture_output=True, text=True).stdout


def entries(text):
    """[(id, tags, body)] for every entry in a VISION.md."""
    out = []
    parts = re.split(r'^(#{2,6} V-\d+.*)$', text, flags=re.M)
    for i in range(1, len(parts), 2):
        head, body = parts[i], parts[i + 1]
        eid = re.search(r'(V-\d+)', head).group(1)
        out.append((eid, set(re.findall(r'\[[A-Z]+\]', head)), body))
    return out


def answer_of(body):
    m = re.search(r'^\*\*A:?\*\*:?[ \t]*(.*)$', body, re.M)
    if not m:
        return None
    first = m.group(1).strip()
    if first:
        return first
    rest = body[m.end():].lstrip("\n")
    line = rest.split("\n", 1)[0].strip()
    return line if line and not line.startswith(("#", "<a ", "-")) else ""


def common(d: Path):
    v = d / "VISION.md"
    check("VISION.md exists", v.is_file())
    if not v.is_file():
        return None, None
    t = v.read_text()
    es = entries(t)
    check("has entries", len(es) > 0, f"{len(es)}")
    ids = [e[0] for e in es]
    check("no duplicate ids", len(ids) == len(set(ids)))
    anchors = set(re.findall(r'<a id="(v-\d+)"', t, re.I))
    missing = [i for i, _, _ in es if i.lower() not in anchors]
    check("every entry has an anchor", not missing, ",".join(missing[:4]))
    notag = [i for i, tg, _ in es
             if not (tg & {"[SAID]", "[IMPLIED]", "[MINE]"})
             or not (tg & {"[BLOCKS]", "[COSTLY]", "[CHEAP]"})]
    check("every entry has both tags", not notag, ",".join(notag[:4]))
    return t, es


def mode_build(d: Path, mc=False):
    t, es = common(d)
    if t is None:
        return
    filled = [i for i, _, b in es if answer_of(b)]
    check("no A: prefilled by the assistant", not filled, ",".join(filled[:4]))
    check("no closing 'left out' section",
          not re.search(r'^#+.*(left out|deliberately (omitted|excluded))',
                        t, re.M | re.I))
    print(f"        {len(es)} entries")

    if not mc:
        lettered = sum(1 for _, _, b in es if re.search(r'^- [a-e]\) ', b, re.M))
        check("questions are prose, not lettered", lettered == 0, f"{lettered} lettered")
        return

    # multiple-choice adaptation
    qs = [b for _, _, b in es if re.search(r'^\*\*Q:?\*\*', b, re.M)]
    esc = [b for b in qs if re.search(r'^- [a-z]\).*(none of these|something else)',
                                      b, re.M | re.I)]
    check("prose escape on every question", len(esc) == len(qs),
          f"{len(esc)}/{len(qs)}")
    m = re.search(r'^#{2,6} V-\d+', t, re.M)   # everything before the FIRST entry
    head = t[:m.start()] if m else t
    check("header explains the deviation",
          bool(re.search(r'(dyslex|repetitive strain|rsi|your words|you overrode|'
                         r'lettered|multiple choice)', head, re.I)))
    # a quote may be a blockquote, inline italics, or plain quotation marks
    check("header quotes the author",
          bool(re.search(r'^>.*\w', head, re.M))
          or bool(re.search(r'[*_"“][^*_"”\n]{20,}[*_"”]', head)))
    blocks = [(i, b) for i, tg, b in es if "[BLOCKS]" in tg]
    flagged = [i for i, b in blocks
               if re.search(r'(yourself|answer this one|decides what|'
                            r'do not take the recommendation|not.*recommendation)',
                            b, re.I)]
    check("every [BLOCKS] entry carries a flag", len(flagged) == len(blocks),
          f"{len(flagged)}/{len(blocks)}")
    # "all recommended" appears in the author's quoted request too; the file's
    # own rule is a different occurrence, so check every one and pass if any
    # scopes it. Lines inside a blockquote are the author's, not the file's.
    hits = [m for m in re.finditer(r'all recommended', t, re.I)
            if not t[:m.start()].rsplit("\n", 1)[-1].lstrip().startswith(">")]
    if hits:
        check("blanket-accept scoped to [CHEAP]",
              any("CHEAP" in t[max(0, m.start() - 500):m.end() + 500]
                  for m in hits),
              f"{len(hits)} non-quoted mention(s)")


def mode_apply(d: Path):
    t, es = common(d)
    if t is None:
        return
    base = "master" if git(d, "rev-parse", "--verify", "master").strip() else "main"
    rng = f"{base}..HEAD"
    check("working tree clean", not git(d, "status", "--porcelain").strip())
    log = git(d, "log", "--diff-filter=R", "--name-status", "-M", "--format=", rng)
    renames = [l for l in log.splitlines() if l.startswith("R")]
    check("originals suspended by git mv", len(renames) >= 3, f"{len(renames)} renames")
    # suspension must be its own commit, and first
    commits = git(d, "log", "--name-status", "-M", "--format=@@%h", "--reverse", rng)
    first = commits.split("@@")[1] if "@@" in commits else ""
    check("suspension is its own first commit",
          first.count("R") >= 3 and "\nM\t" not in first and "\nA\t" not in first,
          first.split("\n")[0][:40])
    check("docs/suspended/ populated", (d / "docs" / "suspended").is_dir()
          and any((d / "docs" / "suspended").iterdir()))
    old = git(d, "show", f"{base}:VISION.md")
    oldmap = {i: answer_of(b) for i, _, b in entries(old)}
    newmap = {i: answer_of(b) for i, _, b in es}
    changed = [i for i in oldmap if oldmap[i] != newmap.get(i)]
    check("author's answers preserved verbatim", not changed, ",".join(changed[:4]))
    added = [i for i in newmap if i not in oldmap]
    check("new entries all blank", all(not newmap[i] for i in added),
          f"{len(added)} added")
    chk = Path.home() / ".claude/skills/vision-check/vision_check.py"
    out = subprocess.run([sys.executable, str(chk), "--root", str(d)],
                         capture_output=True, text=True).stdout
    check("no DEAD citations", "DEAD " not in out)
    check("no NOT MOVED", "NOT MOVED" not in out)
    print(f"        {len(es)} entries, {len(added)} added")


def mode_refuse(d: Path):
    check("nothing written", not git(d, "status", "--porcelain").strip(),
          git(d, "status", "--porcelain")[:60])
    branches = [b.strip() for b in git(d, "branch", "--format=%(refname:short)").split()]
    check("no branch created", len(branches) <= 1, ",".join(branches))
    t = (d / "VISION.md").read_text()
    blanks = [i for i, _, b in entries(t) if not answer_of(b)]
    check("blank A: blocks still blank", len(blanks) >= 1, f"{len(blanks)} blank")


if __name__ == "__main__":
    mode, target = sys.argv[1], Path(sys.argv[2])
    print(f"=== {mode} :: {target.name} ===")
    {"build": lambda: mode_build(target),
     "build-mc": lambda: mode_build(target, mc=True),
     "apply": lambda: mode_apply(target),
     "refuse": lambda: mode_refuse(target)}[mode]()
    print(f"  {'PASS' if not fails else str(fails) + ' FAILURE(S)'}\n")
    sys.exit(1 if fails else 0)
