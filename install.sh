#!/usr/bin/env bash
# Symlink every skill in ./skills into the personal skill folders that
# GitHub Copilot (~/.copilot/skills) and Claude Code (~/.claude/skills) read.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGETS=("$HOME/.copilot/skills" "$HOME/.claude/skills")

for target in "${TARGETS[@]}"; do
  mkdir -p "$target"
  for skill in "$HERE"/skills/*/; do
    name="$(basename "$skill")"
    ln -sfn "${skill%/}" "$target/$name"
    echo "linked $target/$name -> ${skill%/}"
  done
done
echo "Done. Restart VS Code / Copilot CLI to pick up new skills."
