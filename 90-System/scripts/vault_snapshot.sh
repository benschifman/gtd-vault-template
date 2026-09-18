#!/bin/bash
# vault_snapshot.sh — periodic full-vault zip archive to Google Drive.
#
# GitHub backs up the vault's TEXT. This backs up EVERYTHING — including the
# PDFs and images that .gitignore excludes — so the two together are a
# complete restore path.
#
# Excludes .git (GitHub already holds the history) and OS cruft.
# Keeps the most recent $KEEP snapshots and prunes older ones.
#
# Run manually:  bash 90-System/scripts/vault_snapshot.sh
# Scheduled via: ~/Library/LaunchAgents/org.example.vault-snapshot.plist

set -euo pipefail

DRIVE="$HOME/Library/CloudStorage/GoogleDrive-jordan@meridianpolicy.org/My Drive/Obsidian"
VAULT="$DRIVE/gtd-vault-template"
DEST="$DRIVE/_vault-snapshots"
KEEP=8

STAMP="$(date +%Y-%m-%d)"
OUT="$DEST/vault-$STAMP.zip"

mkdir -p "$DEST"

# Build into a local temp file first — zipping directly into the Drive stream
# makes Drive sync every intermediate write.
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT
STAGE="$TMP/vault-$STAMP.zip"

cd "$(dirname "$VAULT")"
zip -r -q -X "$STAGE" "$(basename "$VAULT")" \
  -x '*/.git/*' \
  -x '*/.git' \
  -x '*.DS_Store' \
  -x '*/__pycache__/*' \
  -x '*/.venv/*' \
  -x '*/node_modules/*'

mv "$STAGE" "$OUT"

SIZE="$(du -h "$OUT" | cut -f1)"
echo "$(date '+%Y-%m-%d %H:%M')  snapshot written: $OUT ($SIZE)"

# Prune oldest, keeping the most recent $KEEP
cd "$DEST"
COUNT="$(ls -1 vault-*.zip 2>/dev/null | wc -l | tr -d ' ')"
if [ "$COUNT" -gt "$KEEP" ]; then
  ls -1t vault-*.zip | tail -n +$((KEEP + 1)) | while read -r old; do
    echo "  pruning old snapshot: $old"
    rm -f "$old"
  done
fi
