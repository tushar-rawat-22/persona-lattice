#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/personalattice-npm-worktree.XXXXXX")"
CHECKOUT="$TMP_DIR/checkout"
WORKTREE_ADDED="false"

cleanup() {
  if [[ "$WORKTREE_ADDED" == "true" ]]; then
    git -C "$ROOT" worktree remove --force "$CHECKOUT" >/dev/null 2>&1 || true
  fi
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

git -C "$ROOT" worktree add --detach "$CHECKOUT" HEAD >/dev/null
WORKTREE_ADDED="true"

(
  cd "$CHECKOUT/apps/web"
  npm ci --no-audit --no-fund --dry-run >/dev/null
)
