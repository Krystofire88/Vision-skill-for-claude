#!/usr/bin/env bash
# Tests for vision-check/vision_check.py.
#
# Builds two throwaway fixture repos in a temp directory: one designed to trip
# every check, one clean. Asserts the exact findings and exit codes.
#
#   ./tests/test_vision_check.sh
#
# Exit 0 if all assertions pass, 1 otherwise.

set -uo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHECK="$ROOT/vision-check/vision_check.py"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

pass=0
fail=0
assert() { # assert <description> <condition-result>
  if [ "$2" = "0" ]; then printf '  ok    %s\n' "$1"; pass=$((pass+1))
  else printf '  FAIL  %s\n' "$1"; fail=$((fail+1)); fi
}

# ---------------------------------------------------------------- dirty fixture
mkdir -p "$TMP/dirty/docs/suspended"
cat > "$TMP/dirty/VISION.md" <<'EOF'
# VISION

<a id="v-001"></a>
#### V-001 · Answered and cited `[SAID] [CHEAP]`

**Explain:** Fine.

**Q:** Yes?

**A:** Yes.

Prose after the answer must not be swallowed into it.

<a id="v-002"></a>
#### V-002 · Unanswered `[MINE] [BLOCKS]`

**Explain:** Fine.

**Q:** Which?

**A:**

<a id="v-003"></a>
#### V-003 · Orphan `[IMPLIED] [COSTLY]`

**Explain:** Fine.

**Q:** Which?

**A:** the second one

<a id="v-004"></a>
#### V-004 · Missing cost tag `[MINE]`

**Explain:** Fine.

**Q:** Which?

**A:** ok

#### V-005 · No anchor `[MINE] [CHEAP]`

**Explain:** Fine.

**Q:** Which?

**A:** ok

<a id="v-006"></a>
#### V-006 · Withdrawn `[WITHDRAWN]`

Replaced by V-003.
EOF
echo 'Cites V-001 and V-099, which does not exist.' > "$TMP/dirty/CLAUDE.md"
echo 'Suspended docs must not count as citations: V-003.' > "$TMP/dirty/docs/suspended/old.md"

out="$(python3 "$CHECK" --root "$TMP/dirty" 2>&1)"; code=$?
echo "dirty fixture:"
assert "exits 1 when problems exist"            "$([ "$code" = "1" ] && echo 0 || echo 1)"
assert "DEAD on a citation with no entry"       "$(grep -q '^DEAD .*V-099'        <<<"$out" && echo 0 || echo 1)"
assert "UNANSWERED on a blank A:"               "$(grep -q '^UNANSWERED .*V-002'  <<<"$out" && echo 0 || echo 1)"
assert "NO ANCHOR when <a id> is missing"       "$(grep -q '^NO ANCHOR .*V-005'   <<<"$out" && echo 0 || echo 1)"
assert "NO TAG when a cost tag is missing"      "$(grep -q '^NO TAG .*V-004'      <<<"$out" && echo 0 || echo 1)"
assert "ORPHAN when nothing cites an entry"     "$(grep -q '^ORPHAN .*V-003'      <<<"$out" && echo 0 || echo 1)"
assert "an unanswered entry is not ALSO orphan" "$(grep -q '^ORPHAN .*V-002'      <<<"$out" && echo 1 || echo 0)"
assert "withdrawn entries are exempt"           "$(grep -q 'V-006'                <<<"$out" && echo 1 || echo 0)"
assert "docs/suspended does not satisfy ORPHAN" "$(grep -q '^ORPHAN .*V-003'      <<<"$out" && echo 0 || echo 1)"
assert "prose after A: is not read as an answer" "$(grep -q '^UNANSWERED .*V-001' <<<"$out" && echo 1 || echo 0)"
assert "severity order: DEAD before ORPHAN"     "$([ "$(grep -n '^DEAD' <<<"$out" | head -1 | cut -d: -f1)" -lt "$(grep -n '^ORPHAN' <<<"$out" | head -1 | cut -d: -f1)" ] && echo 0 || echo 1)"

out="$(python3 "$CHECK" --root "$TMP/dirty" --no-orphans 2>&1)"
assert "--no-orphans suppresses ORPHAN only"    "$(grep -q '^ORPHAN' <<<"$out" && echo 1 || echo 0)"
assert "--no-orphans keeps DEAD"                "$(grep -q '^DEAD'   <<<"$out" && echo 0 || echo 1)"

# ---------------------------------------------------------------- clean fixture
mkdir -p "$TMP/clean"
cat > "$TMP/clean/VISION.md" <<'EOF'
# VISION

<a id="v-001"></a>
#### V-001 · Answered `[SAID] [CHEAP]`

**Explain:** Fine.

**Q:** Yes?

**A:** Yes.

<a id="v-002"></a>
#### V-002 · Also answered `[MINE] [COSTLY]`

**Explain:** Fine.

**Q:** Which?

**A:** the second one
EOF
echo 'Rules cite V-001 and V-002.' > "$TMP/clean/CLAUDE.md"

out="$(python3 "$CHECK" --root "$TMP/clean" 2>&1)"; code=$?
echo "clean fixture:"
assert "exits 0 when clean"                     "$([ "$code" = "0" ] && echo 0 || echo 1)"
assert "reports clean"                          "$(grep -q 'clean' <<<"$out" && echo 0 || echo 1)"

# ---------------------------------------------------------------- missing file
python3 "$CHECK" --root "$TMP" >/dev/null 2>&1; code=$?
echo "no VISION.md:"
assert "exits 2 when there is no VISION.md"     "$([ "$code" = "2" ] && echo 0 || echo 1)"

echo
echo "$pass passed, $fail failed"
[ "$fail" = "0" ]
