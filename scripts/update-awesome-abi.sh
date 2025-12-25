#!/usr/bin/env bash
set -euo pipefail

# -----------------------------
# Awesome-Abi Star Updater (Bash)
# Run from anywhere
# -----------------------------

# 1) CONFIG: set your repo folder (absolute path)
REPO_DIR="/c/Users/Abi/Desktop/github/my-collection-index"   # Git Bash on Windows example
# REPO_DIR="$HOME/Desktop/github/my-collection-index"        # macOS/Linux example

# 2) CONFIG: set your GitHub username
GITHUB_USER="YOUR_GITHUB_USERNAME"

# 3) OPTIONAL: token handling
# Prefer exporting in your shell profile:
# export GITHUB_TOKEN="ghp_xxx..."
# Or uncomment below (not recommended for shared machines):
# export GITHUB_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

echo
echo "============================================================"
echo "  Awesome-Abi: Stars -> README Auto Update (Bash)"
echo "============================================================"
echo "Repo: $REPO_DIR"
echo "User: $GITHUB_USER"
echo

if [[ ! -d "$REPO_DIR" ]]; then
  echo "ERROR: Repo folder not found: $REPO_DIR"
  echo "Fix REPO_DIR in this script."
  read -rp "Press Enter to exit..."
  exit 1
fi

cd "$REPO_DIR"

if [[ ! -f "scripts/update_from_stars.py" ]]; then
  echo "ERROR: scripts/update_from_stars.py not found in:"
  echo "  $REPO_DIR"
  read -rp "Press Enter to exit..."
  exit 1
fi

PYTHON_BIN="${PYTHON_BIN:-python}"

echo "--- Step 1: Dry run (safe preview) ---"
$PYTHON_BIN scripts/update_from_stars.py --user "$GITHUB_USER" --dry-run

echo
echo "--- Step 2: Write README (updates AUTO-MANAGED block) ---"
$PYTHON_BIN scripts/update_from_stars.py --user "$GITHUB_USER" --write

echo
echo "✅ Done! README.md updated."
echo "Next:"
echo "  git diff"
echo "  git add README.md"
echo "  git commit -m \"Auto-update curated index from stars\""
echo "  git push"
echo

read -rp "Press Enter to close..."
