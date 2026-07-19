#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
DEST="${CODEX_HOME:-$HOME/.codex}/skills"
NAMES_FILE="$(mktemp)"
SKILLS_FILE="$(mktemp)"
trap 'rm -f "$NAMES_FILE" "$SKILLS_FILE"' EXIT

"$REPO/scripts/list-skills.sh" > "$SKILLS_FILE"

if { [ -e "$DEST" ] || [ -L "$DEST" ]; } && [ ! -d "$DEST" ]; then
  echo "error: skill destination is not a directory: $DEST" >&2
  exit 1
fi

while IFS= read -r skill_path; do
  source_dir="$REPO/${skill_path%/SKILL.md}"
  name="$(basename "$source_dir")"
  target="$DEST/$name"

  if grep -Fqx "$name" "$NAMES_FILE"; then
    echo "error: duplicate active skill name: $name" >&2
    exit 1
  fi
  printf '%s\n' "$name" >> "$NAMES_FILE"

  if [ -L "$target" ]; then
    if [ "$target" -ef "$source_dir" ]; then
      continue
    fi
    current="$(readlink "$target")"
    echo "error: refusing to replace foreign symlink: $target -> $current" >&2
    exit 1
  fi

  if [ -e "$target" ]; then
    echo "error: refusing to replace non-symlink target: $target" >&2
    exit 1
  fi
done < "$SKILLS_FILE"

mkdir -p "$DEST"
while IFS= read -r skill_path; do
  source_dir="$REPO/${skill_path%/SKILL.md}"
  name="$(basename "$source_dir")"
  target="$DEST/$name"

  if [ ! -L "$target" ]; then
    ln -s "$source_dir" "$target"
  fi
  echo "linked $name -> $source_dir"
done < "$SKILLS_FILE"
