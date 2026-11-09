#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
manifest="${MANIFEST:-$root/skills-manifest.json}"
target="${SKILLS_DIR:-$HOME/.claude/skills}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT
mkdir -p "$target"

python3 -I - "$manifest" <<'PY' | sort -t$'\t' -k2,2 > "$work/list.tsv"
import json, sys
for name, v in json.load(open(sys.argv[1])).items():
    print(f"{name}\t{v['repo']}\t{v['path']}")
PY

current_repo=""; clone=""
while IFS=$'\t' read -r name repo path; do
  if [[ -e "$target/$name" ]]; then echo "have  $name"; continue; fi
  if [[ "$repo" != "$current_repo" ]]; then
    clone="$work/$(printf '%s' "$repo" | tr -c 'A-Za-z0-9' '_')"
    git clone --quiet --depth 1 "$repo" "$clone"
    current_repo="$repo"
  fi
  if [[ ! -f "$clone/$path/SKILL.md" ]]; then echo "skip  $name (no $path/SKILL.md in $repo)" >&2; continue; fi
  cp -R "$clone/$path" "$target/$name"
  rm -rf "$target/$name/.git"  # present when the skill is a whole repo (path ".")
  echo "added $name"
done < "$work/list.tsv"
