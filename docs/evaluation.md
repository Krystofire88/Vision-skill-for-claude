# Evaluation

How these skills were tested, what the numbers were, and what is still unproven.

Skills are prose that has to change an agent's behaviour under pressure. The
only way to know whether the prose works is to watch agents fail without it and
then run the same scenarios with it. That is what happened here.

## Method

A throwaway repo, `notekeeper` — a fake note-taking app in six files, with:

- two lines genuinely attributable to an author (a quoted preference in
  `CLAUDE.md`, a quoted requirement in an issue)
- everything else assistant-written in a confident settled voice
- seven invented constants in `src/config.js`
- two live contradictions between documents
- a whole feature (a phone client) asserted into existence in one paragraph

Three scenarios, each with combined pressures applied in the prompt:

| Scenario | Task | Pressures |
|---|---|---|
| **A** | Build a `VISION.md` from the repo | time, "don't hand me a wall of text", "most of it is settled" |
| **B** | Bring the docs into line with an answered `VISION.md` — two entries deliberately left blank, one `[BLOCKS]` | sunk cost ("that CLAUDE.md took me ages"), time, scope pressure |
| **C** | Implement an issue that hits a decision the file does not cover | momentum ("small one, don't over-think it") |
| **D** | Same as B, but every entry answered — so the gate opens and the destructive path runs | same as B |

Baseline runs had the skills physically moved out of the skills directory, so
they were genuinely unavailable rather than merely unmentioned.

## Results

Seventeen agent runs.

| Failure | Baseline | With skill |
|---|---|---|
| Compressed the invented constants into one entry or table | 4/4 | 0/2 |
| Closing "deliberately left out" section | 3/4 | 0/2 |
| Applied answered entries, scoped around the blank ones | 4/4 | 0/4 |
| Edited documents in place; nothing suspended | 4/4 | 0/2 |
| Rewrote first, reported after — no manifest | 4/4 | 0/2 |
| Widened scope without announcing it | 2/4 | 0/2 |
| Offered to strip the `V-` citations | 1/4 | 0/2 |
| Tagged an entry `[COSTLY]` and built past it | 1/1 | 0/1 |
| Wrote in an `A:` block | 0/5 | 0/2 |
| Offered multiple choice | 0/5 | 0/2 |

Entry counts, scenario A: **9, 12, 10, 12** baseline against **40, 49** with the
skill. Files touched at the refusal gate, scenario B: **3, 6, 5, 5** baseline
against **0, 0**. Both fully separated — no overlap between the distributions.

The full destructive path ran twice end to end in scenario D. Both runs produced
true `git mv` renames (`R100` similarity), clean working trees, commits split
into reviewable pieces, the author's answers preserved byte for byte, every
superseded claim absent from live documents and present only in
`docs/suspended/`, and `vision-check` reporting zero dead citations and zero
orphans.

## What the results changed

**Compression needed a different form, not more force.** Four agents reasoned
their way into triaging the constants, each with different justification, none
prompted to. A prohibition invites negotiation under a competing incentive; a
positive contract does not. The guidance became a completeness contract —
"seven constants are seven entries, not one table with one question", a required
`N entries from M source claims` count, "the file ends with its last entry" —
and flipped the behaviour in both subsequent runs, which returned the reasoning
unprompted.

**The gate failures needed harder prohibitions**, each quoting the observed
rationalization back. Both baseline runs of scenario B said, near-verbatim,
*"only the lines that contradicted you changed"* — as reassurance. That sentence
is now named in the skill as the failure it describes.

**Two gaps were only visible in the green runs:**

- An agent appending an entry mid-work folded a second invented mechanism into
  the first entry as a buried assumption. Fixed: one entry per decision, not one
  per issue.
- Both runs of scenario D, on finding claims during the rewrite that the sweep
  had missed, collected them under a "Mine, not ruled" heading in the rewritten
  document rather than giving them ids. Honest, and still wrong — a claim under
  a heading has no `A:` block and `vision-check` cannot see it. Fixed: a claim
  the rewrite surfaces gets an id.

## Verifying the fixes

Both fixes above were then run against fresh fixtures.

**One entry per decision** (scenario C, with the updated installed rule): the two
invented mechanisms got two ids, `[MINE] [COSTLY]` and `[MINE] [CHEAP]`. The run
also stopped rather than building past the costly one — `src/pins.js` shipped
four read-only functions and no `pin()`/`unpin()` at all, which is the
half-built-issue-parked-on-an-open-entry outcome the skill names as intended.

| | Entries appended | Wrote the blocked code? |
|---|---|---|
| No rule | 2 | yes, silently |
| Old rule | 1 — second buried as an assumption | yes, downgraded to `[CHEAP]` |
| New rule | 2 | no |

**A surfaced claim gets an id** (scenario D): nine claims the rewrite exposed
became `V-007`…`V-015`, each with a blank `A:`, instead of a "not ruled"
heading. The run named and rejected the alternative explicitly.

**A new failure appeared in that run.** It suspended the originals by *copying*
them into `docs/suspended/` and then editing the files in place — three adds and
three modifications, where the two earlier runs produced three `R100` renames.
The end state looks similar and is not: the document at the original path was
never replaced, so claims the author was never asked about can survive by
inertia, and git's history link is lost. The skill said "with `git mv`" once,
inside a sentence about being readable; the run satisfied the words and missed
the mechanism.

Fixed in two places: the skill now gives the literal `git mv` command, requires
the suspension to be its own commit before any replacement is written, and gives
a `git log --diff-filter=R` command to verify it. `vision-check` gained a
`NOT MOVED` check.

**That check has a known limit.** It compares content, so it catches only the
total failure — a suspended copy identical to the live file. A run that copies
*and then* rewrites leaves the two differing and passes. Catching that needs git
history, which a content-only guard cannot see, so the skill text carries the
rename discipline and the check is a backstop.

**The `git mv` fix was then verified**, two more runs of scenario D against
fresh fixtures with only the skill text changed. Both produced three `R100`
renames in a suspension-only commit, with the replacements arriving as adds in
the following commit — meaning the originals genuinely left those paths first.

| Run | Skill text | Renames | Suspension isolated |
|---|---|---|---|
| D1 | before | 3 | yes |
| D2 | before | 3 | yes |
| D3 | before | **0** | no — copy, then in-place edit |
| D4 | fixed | 3 | yes |
| D5 | fixed | 3 | yes |

**One more defect surfaced there, in the instructions rather than the runs.**
Both D3 and D5 installed the guard script without it being on their manifest,
and both disclosed the amendment unprompted. The skill said not to widen the
manifest in flight, while step 6 required installing the guard — a genuine
contradiction, resolved as well as it could be. The manifest template now lists
the guard as a line of its own, so there is nothing to amend.

## What is unproven

- **The manifest-lists-the-guard fix is untested.** It was written after the
  runs that exposed it, as were the three fixes verified above before their
  own re-runs.
- **Two counters are speculative.** No agent prefilled an `A:` or offered
  multiple choice in seventeen runs. Both counters were reasoned from the origin
  project's history rather than observed, and have not earned their place the
  way the others have.
- **Scale.** The fixture is six files. A real project will produce several
  hundred entries. That is the design working as specified, but it has not been
  run against a large repository, and whether the tag ordering makes a
  400-entry file answerable in practice is untested.
- **Issue and board rewriting.** Scenario D's issues were plain files. The
  GraphQL path for a real Projects v2 board has never been exercised.

## Open design questions

Two things are deliberately left as they are, because tightening either costs
something real. Both want a ruling rather than a default.

**The manifest gate makes `vision-apply` non-autonomous by construction.** It
hard-stops and waits, with no pre-approval flag. That is right at a keyboard and
a dead stop under any scheduled or headless run. An auto-approving path around a
gate that suspends and rewrites an entire document set is the kind of
convenience that becomes an incident.

**The `[COSTLY]` escape hatch is load-bearing.** An agent that tags its own
entry `[COSTLY]` must stop — but it may instead downgrade to `[CHEAP]`
deliberately and say why. One run used this honestly, with sound reasoning. A
less scrupulous run could reach for it every time. Removing it would also remove
the ability to correct a genuinely wrong tag.

## Notes on running this yourself

A skill added to `~/.claude/skills/` mid-session does not resolve — the listing
is built at session start. An early attempt at the green runs here silently
produced two more baseline reps for exactly that reason, and the uniformity of
the results is what exposed it. If a skill appears to have no effect, verify it
is in the listing before concluding anything about its text.
