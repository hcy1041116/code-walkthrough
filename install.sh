#!/usr/bin/env bash
# Install the walkthrough skill for Claude Code (symlink, so `git pull` updates it) and create ~/learning.
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"
DEST="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
mkdir -p "$DEST"
if [ -e "$DEST/walkthrough" ] && [ ! -L "$DEST/walkthrough" ]; then
  echo "$DEST/walkthrough exists and is not a symlink; move it away first" >&2
  exit 1
fi
ln -sfn "$HERE/skills/walkthrough" "$DEST/walkthrough"
python3 "$HERE/skills/walkthrough/engine/run.py" init-learning
echo "installed: $DEST/walkthrough -> $HERE/skills/walkthrough"
echo "next: fill in ${WT_LEARNING:-$HOME/learning}/PROFILE.md, then ask Claude for a walkthrough of your code"
