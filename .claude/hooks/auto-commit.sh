#!/bin/bash
# Auto-commit vault changes, then push to the GitHub backup.

# Navigate to the root of the vault (two directories up from .claude/hooks)
cd "$(dirname "$0")/../.." || exit 1

# Check if there are any uncommitted changes
if [[ -n $(git status --porcelain) ]]; then
  git add -A
  git commit -m "auto-commit: $(date +'%Y-%m-%d %H:%M:%S')"
  echo "Vault changes auto-committed."
else
  echo "No vault changes to commit."
fi

# Push whenever local is ahead of the remote — including commits from earlier
# runs that failed to push. Never fail the hook on a network error; the commits
# are safe locally and go up on the next run.
if git remote get-url origin >/dev/null 2>&1; then
  if [[ -n $(git log origin/main..HEAD --oneline 2>/dev/null) ]]; then
    if git push --quiet origin main 2>/dev/null; then
      echo "Pushed to GitHub backup."
    else
      echo "WARNING: push to GitHub failed (offline?). Commits are safe locally."
    fi
  fi
fi
