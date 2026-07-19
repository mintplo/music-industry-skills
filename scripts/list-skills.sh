#!/usr/bin/env bash
set -euo pipefail

REPO="$(cd "$(dirname "$0")/.." && pwd)"
cd "$REPO"
find -P skills -type f -name SKILL.md \
  -not -path '*/deprecated/*' \
  -not -path '*/in-progress/*' \
  -not -path '*/node_modules/*' \
  | sort
