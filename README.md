# vision — skills for keeping a project's decisions separable from an assistant's

Three Claude Code skills that build and maintain a `VISION.md`: a file that
records what **you** decided, in your words, and keeps it distinguishable from
what an assistant inferred and wrote down as though you had.

## The problem it solves

An assistant writes documentation for your project. Some of it records your
actual decisions. Most of it records its own inferences — numbers it picked,
mechanisms it invented, defaults nobody asked for — asserted in exactly the same
confident voice.

Once written, the two are indistinguishable. Every later session enforces the
whole document as settled. You end up re-explaining the same things during
feature work, and there is no way to tell, from the file alone, which sentences
are yours.

This is not hypothetical. The project these skills were extracted from deleted
and rebuilt its entire document set because of it.

## The fix

One file at the repo root, `VISION.md`, that outranks every other document.
Every claim the project makes about itself becomes a numbered entry:

```markdown
<a id="v-013"></a>
#### V-013 · The purge window is 30 days `[MINE] [COSTLY]`

**Explain:** Archived notes are destroyed after 30 days. I chose 30.

**Q:** How long should an archived note survive, and should it be destroyed
automatically at all?

**A:**
```

You answer in the `A:` blocks. Nothing else writes there. Then every other
document is rewritten to **cite** `V-013` rather than restate it — because a
citation cannot drift and a paraphrase can.

### Two tag axes

Every entry carries one tag from each. Provenance says where the claim came
from; cost says what it costs you if it is wrong.

| Provenance | | Cost if wrong | |
|---|---|---|---|
| `[SAID]` | your words, with the citation given | `[BLOCKS]` | cannot be built until you rule |
| `[IMPLIED]` | follows from you; the wording is the assistant's | `[COSTLY]` | buildable, but wrong means tearing it out |
| `[MINE]` | invented, no trace to you | `[CHEAP]` | wrong is a small edit whenever you notice |

`[SAID]` must be earned by a real citation — a line attributed to you, an issue
you filed, a commit you wrote, an answer already in the file. Confidence is not
evidence, so the honest default is `[MINE]`.

The pair is what makes a long file usable. You read down from `[MINE] [BLOCKS]`
and stop wherever you like. `[SAID] [CHEAP]` can be ignored forever.

## The three commands

| Command | What it does |
|---|---|
| `/vision-build` | Sweeps `CLAUDE.md`, README, docs, specs, issues, the board, git history and code constants. Writes `VISION.md` on a branch. Touches nothing else. |
| `/vision-apply` | Refuses while any `A:` is blank. Otherwise shows a manifest and waits, then suspends the old documents to `docs/suspended/` and rewrites them from the file. |
| `/vision-check` | Guards it: dead citations, unanswered entries, orphaned rulings, duplicate ids, missing anchors, missing tags. |

`vision-apply` also installs a rule into the rewritten `CLAUDE.md` so this stops
being a one-off sweep. From then on, when work reaches something the file does
not cover, the session appends a new `V-` entry instead of deciding for you or
asking in chat — because a question asked in chat dies when the context is
trimmed, and one written to disk does not.

## Install

```bash
git clone https://github.com/Krystofire88/Vision-skill-for-claude.git
cd Vision-skill-for-claude
./install.sh            # copy into ~/.claude/skills/
./install.sh --link     # or symlink, so edits here are live
```

**Then restart Claude Code.** The skill listing is built when a session starts,
so a skill added mid-session will not resolve. Type `/vision` to confirm all
three appear.

## Usage

```
/vision-build           # answer the A: blocks it writes, in your own words
/vision-apply           # after answering — shows a manifest, waits for you
/vision-check           # any time
```

`vision-check` runs standalone too, in any project and any language:

```bash
python3 vision-check/vision_check.py --root .
# exit 0 clean, 1 problems, 2 could not run
```

## Tests

```bash
./tests/test_vision_check.sh     # 19 assertions against fixture repos
```

The skills themselves were tested behaviourally against subagents — baseline
runs without the skill, then the same scenarios with it. See
[docs/evaluation.md](docs/evaluation.md) for the method, the measured before and
after, and what remains unproven.

## What it will not do

- **Write an answer for you.** Only you write in an `A:`.
- **Offer multiple choice.** Options written by an assistant put its words in
  your mouth, which is the exact failure the file exists to prevent. Questions
  are asked in prose and expect the answer to go further.
- **Renumber or reuse an id.** Documents cite them by anchor.
- **Rewrite anything without showing you a manifest first.**
- **Run unattended.** The manifest gate is a hard stop; there is deliberately no
  pre-approval flag. See [docs/evaluation.md](docs/evaluation.md#open-design-questions).

## Origin

Extracted from a private project whose `VISION.md` reached 135 entries across 28
sections and six rounds of questions. The mechanism — cite never paraphrase,
stable ids, blank answer blocks, `docs/suspended/` — is that project's; the two
tag axes and the three commands are the generalisation of it.
