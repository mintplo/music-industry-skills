#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
TARGET="${1:-codex}"

if [ "$#" -gt 1 ]; then
  echo "usage: $0 [codex|claude|agents]" >&2
  exit 2
fi

case "$TARGET" in
  codex)
    CLIENT_LABEL="Codex"
    CLIENT_ROOT="${CODEX_HOME:-$HOME/.codex}"
    ;;
  claude)
    CLIENT_LABEL="Claude Code"
    CLIENT_ROOT="${CLAUDE_CONFIG_DIR:-${CLAUDE_HOME:-$HOME/.claude}}"
    ;;
  agents)
    CLIENT_LABEL="Agent Skills"
    CLIENT_ROOT="${AGENTS_HOME:-$HOME/.agents}"
    ;;
  *)
    echo "usage: $0 [codex|claude|agents]" >&2
    exit 2
    ;;
esac

validate_client_root() {
  local input="$1"
  local current remainder component candidate

  case "$input" in
    /*) current="/" ;;
    *) current="$(pwd -P)" ;;
  esac
  remainder="$input"

  while :; do
    while [ "${remainder#/}" != "$remainder" ]; do
      remainder="${remainder#/}"
    done
    [ -n "$remainder" ] || break

    case "$remainder" in
      */*)
        component="${remainder%%/*}"
        remainder="${remainder#*/}"
        ;;
      *)
        component="$remainder"
        remainder=""
        ;;
    esac

    case "$component" in
      ""|.) continue ;;
      ..)
        if [ "$current" != "/" ]; then
          current="${current%/*}"
          [ -n "$current" ] || current="/"
        fi
        continue
        ;;
    esac

    if [ "$current" = "/" ]; then
      candidate="/$component"
    else
      candidate="$current/$component"
    fi
    if [ -L "$candidate" ]; then
      echo "error: $CLIENT_LABEL home must not be a symlink; $CLIENT_LABEL home path contains a symlink: $candidate" >&2
      return 1
    fi
    current="$candidate"
  done

  CLIENT_ROOT="$current"
}

validate_skill_source() {
  local skill_path="$1"
  local current="$REPO" remainder="$skill_path" component candidate

  case "$skill_path" in
    skills/*/SKILL.md) ;;
    *)
      echo "error: unsafe skill source in inventory: $skill_path" >&2
      return 1
      ;;
  esac

  while :; do
    case "$remainder" in
      */*)
        component="${remainder%%/*}"
        remainder="${remainder#*/}"
        ;;
      *)
        component="$remainder"
        remainder=""
        ;;
    esac

    case "$component" in
      ""|.|..)
        echo "error: unsafe skill source in inventory: $skill_path" >&2
        return 1
        ;;
      deprecated|in-progress|node_modules)
        echo "error: unsafe skill source is excluded: $skill_path" >&2
        return 1
        ;;
    esac

    candidate="$current/$component"
    if [ -L "$candidate" ]; then
      echo "error: unsafe skill source contains a symlink: $skill_path" >&2
      return 1
    fi
    current="$candidate"
    [ -n "$remainder" ] || break
  done

  if [ ! -f "$current" ]; then
    echo "error: unsafe skill source is not a regular file: $skill_path" >&2
    return 1
  fi
}

validate_client_root "$CLIENT_ROOT"
if [ "$CLIENT_ROOT" = "/" ]; then
  DEST="/skills"
else
  DEST="$CLIENT_ROOT/skills"
fi
NAMES_FILE="$(mktemp)"
SKILLS_FILE="$(mktemp)"
trap 'rm -f "$NAMES_FILE" "$SKILLS_FILE"' EXIT

"$REPO/scripts/list-skills.sh" > "$SKILLS_FILE"

if [ -L "$CLIENT_ROOT" ]; then
  echo "error: $CLIENT_LABEL home must not be a symlink: $CLIENT_ROOT" >&2
  exit 1
fi

if [ -e "$CLIENT_ROOT" ] && [ ! -d "$CLIENT_ROOT" ]; then
  echo "error: $CLIENT_LABEL home is not a directory: $CLIENT_ROOT" >&2
  exit 1
fi

if [ -L "$DEST" ]; then
  echo "error: skill destination must not be a symlink: $DEST" >&2
  exit 1
fi

if [ -e "$DEST" ] && [ ! -d "$DEST" ]; then
  echo "error: skill destination is not a directory: $DEST" >&2
  exit 1
fi

while IFS= read -r skill_path; do
  validate_skill_source "$skill_path"
  source_dir="$REPO/${skill_path%/SKILL.md}"
  name="$(basename "$source_dir")"
  target="$DEST/$name"

  if grep -Fqx -e "$name" "$NAMES_FILE"; then
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
