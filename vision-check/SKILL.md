---
name: vision-check
description: Use when a project has a VISION.md and documents may have drifted from it, when a V- citation might be dead or renumbered, when entries were added mid-issue and possibly never answered, or when the author asks to check or verify a VISION.md
---

# vision-check

## Overview

Checks that a project's `VISION.md` and the documents citing it still agree.

**The rule this exists to hold:** a prose ruling that lives only in prose gets
undone by ordinary editing, usually twice, usually silently. What can be checked
mechanically should be.

Three things are checkable in any project, any language:

| Check | Catches |
|---|---|
| `DEAD` | A document cites a `V-` id `VISION.md` does not define — a renumber, a deletion, a typo'd anchor |
| `UNANSWERED` | An entry with a blank `A:` — one added mid-issue and then forgotten |
| `ORPHAN` | An answered entry no document cites — a ruling that never left the file |
| `NOT MOVED` | A live document byte-identical to its copy in `docs/suspended/` — suspended by copy and never rewritten |

Plus structural checks on the file: duplicate ids, missing `<a id>` anchors,
entries missing a provenance or cost tag.

**What it cannot check:** paraphrase. "Cite, never restate" is not
string-matchable, so a document that quietly rewords an entry passes. That is a
review job, not a guard's.

## Running it

```bash
python3 ~/.claude/skills/vision-check/vision_check.py --root .
```

Exit `0` clean, `1` problems found, `2` could not run (no `VISION.md`, or it
defines no entries). `--help` for the flags; `--no-orphans` suppresses the
orphan check, which is the right call early on when most entries are answered
but the documents have not been rewritten yet.

## Wiring it into a project

Copy the script into the project — `scripts/vision_check.py` or equivalent —
rather than leaving it in the personal skills directory, so it runs in CI and
for anyone else.

Then, in order of preference:

1. **Into the project's own test suite**, if you can tell what it is. A Rust
   project gets a `tests/vision.rs` that shells out and asserts exit 0; a
   Python project a `test_vision.py`; a Node project a script in `package.json`.
   This is the strongest form — the check fails the build.
2. **As a pre-commit or CI step**, if the suite is not obvious.
3. **Manual only**, and say so in `CLAUDE.md` so the next session knows to run
   it.

Do not guess at a test framework. If you cannot identify it from the project's
own files, fall back to 2 or 3 and tell the author which you chose.

## Reading the output

- **`DEAD`** — almost always a renumber. Ids are never renumbered and never
  reused; if one has been, the fix is to restore the id, not to repoint the
  citations.
- **`UNANSWERED`** — the entry is waiting on the author. If it is `[BLOCKS]` or
  `[COSTLY]`, work depending on it should not have proceeded. Report it; do not
  answer it.
- **`ORPHAN`** — either the ruling needs carrying into a document, or the entry
  was answered and nothing needed to change. Both are fine outcomes; the check
  only makes the choice visible.
- **`NOT MOVED`** — `vision-apply` suspended a document by copying it and never
  wrote the replacement. Redo that document: `git mv` the original, then write
  the new one from `VISION.md`. Note the limit — this catches only the total
  failure. A run that copies *and then* rewrites the live file leaves the two
  differing, so the content check passes; only
  `git log --diff-filter=R --name-status -M` shows whether the suspension was a
  real rename.

## Common mistakes

- **Answering an `UNANSWERED` entry to make the check pass.** Only the author
  writes an `A:`. Making a guard green by writing in the author's voice is the
  exact failure the file exists to prevent.
- **Deleting an `ORPHAN` entry.** Ids are never reused. Withdraw it in place
  with `[WITHDRAWN]` and a one-line reason if it is genuinely obsolete.
- **Running it before `vision-apply`.** Every entry will be an orphan, because
  no document cites anything yet. Use `--no-orphans` until the documents have
  been rewritten.
