#!/usr/bin/env bash
set -euo pipefail

COMMIT_MSG="chore: init commit -restructure cms"
BRANCH=$(git branch --show-current)

echo "Current branch: $BRANCH"
echo "Commit message: $COMMIT_MSG"
echo

# Optional safety check
if [[ "$BRANCH" != "bcn/main" ]]; then
  echo "You are on '$BRANCH', not 'bcn/main'. Continue? (y/N)"
  read -r ans
  [[ "$ans" =~ ^[Yy]$ ]] || exit 1
fi

git fetch origin || true

process_file() {
  local file="$1"
  [[ -z "$file" ]] && return
  [[ "$file" == *"/__pycache__/"* || "$file" == *"__pycache__" || "$file" == *.pyc ]] && return

  echo "────────────────────────────────────────"
  echo "→ Processing: $file"

  git add -- "$file"

  if git diff --cached --quiet; then
    echo "  (nothing staged – skipped)"
    return
  fi

  git commit -m "$COMMIT_MSG"
  echo "  ✓ committed"

  git push origin "$BRANCH"
  echo "  ✓ pushed to origin/$BRANCH"
  echo
}

echo "===== 1. Modified / Deleted files ====="
while IFS= read -r file; do
  process_file "$file"
done < <(git diff --name-only)

echo
echo "===== 2. Untracked files ====="
while IFS= read -r file; do
  process_file "$file"
done < <(git ls-files --others --exclude-standard)

echo
echo "===== Final status ====="
git status
echo
echo "All done."
