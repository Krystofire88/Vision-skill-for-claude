# The VISION.md format

Shared reference for `vision-build`, `vision-apply` and `vision-check`.
Path: `~/.claude/skills/vision-build/vision-format.md`

## Where it lives

Repository root: `VISION.md`. One per repository. Never more than one.

## Why the format is what it is

The failure this file exists to prevent: an assistant's inferences get written
into a project's documents in the same assertive voice as the author's actual
decisions. Once written they are indistinguishable from decisions, are enforced
by every later session, and have to be re-explained during feature work.

Everything below follows from that. The entry structure separates the two
voices, the tags say which is which, and the ids exist so other documents can
cite instead of paraphrase.

## Entry anatomy

Every entry is exactly this shape:

```markdown
<a id="v-045"></a>
#### V-045 · Short title `[MINE] [COSTLY]`

**Explain:** What this thing is, in plain words. No jargon the author has not
already used. If it is a number, say what the number does.

**Q:** The question, stating what the documents currently claim. Ask for the
mechanism, not for a yes or no.

**A:**
```

- **Explain** — plain-language statement of the thing. Written for someone who
  has not read the code.
- **Q** — the question, including what the documents currently assert, so the
  author is correcting a concrete claim rather than answering into a void.
- **A** — blank. **Only the author writes here.** Never prefill it, never
  suggest an answer inside it, never write "TBD".

An `A:` is answered when there is non-whitespace text after it before the next
blank line. Answers may be one word — *"yes"*, *"no"*, *"never asked for this,
delete it"*, *"right idea, wrong number"* are all complete.

## Ids

- Format `V-NNN`, zero-padded to three digits, allocated sequentially.
- Each entry is preceded by `<a id="v-nnn"></a>` (lowercase) so documents can
  link to `VISION.md#v-045`.
- **Ids are never renumbered and never reused.** Other documents cite them by
  anchor; renumbering silently repoints every citation.
- A deleted entry keeps its id and is marked `[WITHDRAWN]` in place, with a
  one-line reason. The number is not recycled.

## The two tag axes

Every entry carries exactly one tag from each axis, provenance first.

### Provenance — where the claim came from

| Tag | Meaning | Requires |
|---|---|---|
| `[SAID]` | Traceable to the author's own words | A citation, written into the Explain block |
| `[IMPLIED]` | Follows from something the author said, but the wording and the edges are the assistant's | Name what it follows from |
| `[MINE]` | The assistant invented it. No trace to the author at all | Nothing — this is the honest default |

**`[SAID]` must be earned.** A citation is one of:

- a line in `CLAUDE.md` / `AGENTS.md` explicitly attributed to the author
  (`the author said:`, `per the author`, `ruled:`, a blockquote of their words)
- an issue or issue comment authored by the author's GitHub account
- a commit message written by the author (not by the assistant, not
  `Co-Authored-By: Claude`)
- an answered `A:` block already in this file
- a README section predating the assistant's first commit

Write the citation into the entry, e.g. `[SAID]` ... *(CLAUDE.md:112)*.
**If there is no citation, the tag is not `[SAID]`.** A plausible-sounding
claim in a document the assistant wrote is `[MINE]`, however confident it reads.

On a project with no author-authored material at all, nearly everything is
`[MINE]`. That is the correct and useful answer, not a failure of the sweep.

### Cost — what it costs if the claim is wrong

| Tag | Meaning |
|---|---|
| `[BLOCKS]` | The thing cannot be built until the author rules |
| `[COSTLY]` | Buildable now, but wrong means tearing something out later |
| `[CHEAP]` | Wrong is a small edit whenever the author notices |

Cost is about rework, not importance. A wrong colour is `[CHEAP]`; a wrong
storage format is `[COSTLY]`; an undecided sync direction is `[BLOCKS]`.

### Reading the pair

`[MINE] [BLOCKS]` is the top of the list — invented, and nothing proceeds
without a ruling. `[SAID] [CHEAP]` is the bottom — already the author's, and
cheap to change. The pair is what makes a 300-entry file answerable: the author
reads down from the top and stops whenever they like.

## File skeleton

```markdown
# VISION — the author's own words

This file is the top authority for <project>. Everything else — `CLAUDE.md`,
the specs, the plans, the issues, the README — describes *how* the thing gets
built. This file records *what the author actually wants*, in the author's own
words. Where any document disagrees with this file, this file wins.

## How to use it

Each entry has a stable id (`V-001`, `V-002`, …). Ids are **never renumbered
and never reused**, because other documents cite them by anchor.

Every entry is **Explain** (what it is), **Q** (the question), and **A**
(blank — only the author writes there). Answers may be one word.

## Tags

| Provenance | Meaning |
|---|---|
| `[SAID]` | Traceable to your own words, with the citation given |
| `[IMPLIED]` | Follows from something you said; the wording is mine |
| `[MINE]` | I invented it. No trace to you |

| Cost if wrong | Meaning |
|---|---|
| `[BLOCKS]` | Cannot be built until you rule |
| `[COSTLY]` | Buildable, but wrong means tearing it out later |
| `[CHEAP]` | Wrong is a small edit whenever you notice |

Start at `[MINE] [BLOCKS]` and work down. `[SAID] [CHEAP]` can be ignored.

## Status

*Built <date>.* <n> entries: <a> `[SAID]`, <b> `[IMPLIED]`, <c> `[MINE]`.
<d> `[BLOCKS]`, <e> `[COSTLY]`, <f> `[CHEAP]`.
<g> unanswered.

---

# 1 · <Section>

<a id="s1"></a>

<A paragraph of plain-language orientation for this area, written for someone
who has not read the code.>

<a id="v-001"></a>
#### V-001 · … `[MINE] [BLOCKS]`
…
```

## Sections

Sections group entries by area of the product, numbered `# 1 ·`, `# 2 ·`, each
with an `<a id="sN">` anchor and a plain-language paragraph before its entries.

Within a section, entries are ordered `[BLOCKS]` → `[COSTLY]` → `[CHEAP]`.
Ids stay in allocation order across the file as a whole; they do not need to be
contiguous within a section, and later rounds append higher ids into existing
sections.

## Rounds

Entries added after the first build go into a new trailing section named for
what raised them — e.g. `# 12 · Round two — raised while building #14`. They
are appended, never interleaved, and never renumbered.

## What never goes in this file

- An `A:` written by anyone but the author.
- A multiple-choice question. Options written by the assistant put its words in
  the author's mouth, which is the exact failure the file exists to prevent.
  Ask in prose, ask for the mechanism, and expect the answer to go further than
  any option would have.
- A rationale in the author's voice. If the author has not said why, the entry
  says the assistant chose it and asks.
- A paraphrase of another entry. Cite the id.
