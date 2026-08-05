#!/usr/bin/env bash
# Install the vision skills into your personal Claude Code skills directory.
#
#   ./install.sh            copy into ~/.claude/skills/
#   ./install.sh --link     symlink instead, so edits here are live
#
# Restart Claude Code afterwards: the skill listing is built at session start,
# so a skill added mid-session will not resolve until the process restarts.

set -euo pipefail
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
MODE="${1:-copy}"

mkdir -p "$DEST"
for skill in vision-build vision-apply vision-check; do
  rm -rf "${DEST:?}/$skill"
  if [ "$MODE" = "--link" ]; then
    ln -s "$SRC/$skill" "$DEST/$skill"
    echo "linked  $DEST/$skill -> $SRC/$skill"
  else
    cp -r "$SRC/$skill" "$DEST/$skill"
    echo "copied  $DEST/$skill"
  fi
done

echo
echo "Done. Restart Claude Code, then type /vision to confirm all three appear."
