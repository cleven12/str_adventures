#!/usr/bin/env bash
set -euo pipefail

# Usage: ./atomic_push.sh [files.txt]
# If no argument is given it uses files.txt in the current directory.

FILE_LIST="${1:-files.txt}"

if [[ ! -f "$FILE_LIST" ]]; then
  echo "Error: $FILE_LIST not found"
  exit 1
fi

# Make sure we are in a git repo
if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Error: not inside a git repository"
  exit 1
fi

# Optional: fetch latest so the push is less likely to fail
git fetch origin

while IFS= read -r file || [[ -n "$file" ]]; do
  # skip empty lines and comments
  [[ -z "$file" || "$file" =~ ^[[:space:]]*# ]] && continue

  # trim whitespace
  file=$(echo "$file" | xargs)

  if [[ ! -e "$file" ]]; then
    echo "⚠  Skipping (does not exist): $file"
    continue
  fi

  # Check if the file actually has changes
  if git diff --quiet -- "$file" && git diff --cached --quiet -- "$file"; then
    echo "→ No changes in $file – skipping"
    continue
  fi

  echo "────────────────────────────────────────"
  echo "Processing: $file"

  # Stage only this file
  git add -- "$file"

  # Create a meaningful commit message
  commit_msg="chore: update $(basename "$file")"

  # If you prefer a more descriptive message you can change the line above, e.g.:
  # commit_msg="feat(api): update serializers and views"

  git commit -m "$commit_msg"

  # Push immediately (atomic)
  git push origin HEAD

  echo "✓ Pushed: $file"
  echo
done < "$FILE_LIST"

echo "All done."
