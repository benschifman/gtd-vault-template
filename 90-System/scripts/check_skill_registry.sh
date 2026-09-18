#!/usr/bin/env bash
# Verify the skill/agent discovery registry.
#
# Skills and agents live in domain-local NN-90-System/ folders; 90-System/skills/
# and 90-System/agents/ hold relative symlinks that Claude Code actually scans.
# A broken symlink fails SILENTLY — the skill just stops loading — so check here.
#
# Usage: bash 90-System/scripts/check_skill_registry.sh
# Exit 0 = healthy, 1 = problems found.

set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

fail=0

check_registry() {  # $1=registry dir  $2=file that must be readable inside each entry
  local dir="$1" inner="$2" entry name target
  for entry in "$dir"/*; do
    [ -e "$entry" ] || [ -L "$entry" ] || continue
    name=$(basename "$entry")
    case "$name" in .DS_Store) continue ;; esac

    if [ ! -L "$entry" ]; then
      printf 'NOT A SYMLINK  %s/%s (real file left in the registry — move it to a domain folder)\n' "$dir" "$name"
      fail=1; continue
    fi

    target=$(readlink "$entry")
    if [ -n "$inner" ]; then
      [ -r "$entry/$inner" ] || { printf 'BROKEN         %s/%s -> %s\n' "$dir" "$name" "$target"; fail=1; continue; }
    else
      [ -r "$entry" ] || { printf 'BROKEN         %s/%s -> %s\n' "$dir" "$name" "$target"; fail=1; continue; }
    fi
    printf 'ok             %-28s -> %s\n' "$name" "$target"
  done
}

echo "=== skills (90-System/skills) ==="
check_registry "90-System/skills" "SKILL.md"
echo
echo "=== agents (90-System/agents) ==="
check_registry "90-System/agents" ""
echo

# A skill that uses relative ../ paths breaks when moved between domain folders.
echo "=== relative ../ paths inside skills (should be none) ==="
if grep -rn '\.\./' 90-System/skills/*/SKILL.md 2>/dev/null; then
  echo "WARNING: use vault-relative paths from the root instead."
  fail=1
else
  echo "none found"
fi
echo

[ $fail -eq 0 ] && echo "RESULT: registry healthy" || echo "RESULT: problems found"
exit $fail
