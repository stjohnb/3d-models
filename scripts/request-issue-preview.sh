#!/usr/bin/env bash
# request-issue-preview.sh — Render candidate geometry proposed on an issue, without a PR.
#
# No .scad is rendered until something pushes it to CI, so plan review is
# otherwise blind: the planner can't show the maintainer what a proposed
# model actually looks like before the plan is approved. This script runs on
# the planner host (openclaw, ~3.8 GB RAM, shared with the Claws service) and
# deliberately performs ZERO local rendering — it only stages candidate files
# onto a claws/preview-issue-<id> branch. build.yml renders pushes to that
# branch on a self-hosted Linux runner and deploys site/ to
# issue-preview/<id>/<sha8>/, including a machine-readable
# preview-summary.json that Claws' issue-preview-sync mirrors onto the issue.
#
# No PR is opened. Claws deletes the branch once the plan is decided (Refined)
# or the issue closes, which fires pr-preview-cleanup.yml to reclaim
# issue-preview/<id>/. `--cleanup <id>` is the manual fallback when Claws'
# sync is unavailable or the issue is not tracked by Claws.
#
# Usage: scripts/request-issue-preview.sh <issue-id> <file> [more files ...]
#        scripts/request-issue-preview.sh --cleanup <issue-id>
# <issue-id> is a GitHub issue number or a Claws-native clw_… id.
# <file> is a .scad, or a project's meta.json or dependency-graph.md (a new
# project needs meta.json to reach models.json).

set -euo pipefail

USAGE="usage: scripts/request-issue-preview.sh <issue-id> <file> [more files ...]
       scripts/request-issue-preview.sh --cleanup <issue-id>"
ID_RE='^([0-9]+|clw_[A-Za-z0-9]+)$'
PREVIEW_BASE="https://www.bstjohn.net/3d-models/issue-preview"

MODE=preview
if [ "${1:-}" = "--cleanup" ]; then
  MODE=cleanup
  shift
fi

ISSUE="${1:-}"
shift || true

if ! [[ "$ISSUE" =~ $ID_RE ]]; then
  echo "$USAGE" >&2
  exit 2
fi

branch="claws/preview-issue-${ISSUE}"

if [ "$MODE" = cleanup ]; then
  if [ "$#" -ne 0 ]; then
    echo "$USAGE" >&2
    exit 2
  fi
  # Legacy previews (issue #518 era) were draft PRs on this branch; close
  # them so pr-preview-cleanup.yml also reclaims their pr-preview/pr-<N>/
  # prefix. Captured first so a gh failure aborts under `set -e`.
  prs="$(gh pr list --head "$branch" --state open --json number --jq '.[].number')"
  for pr in $prs; do
    gh pr close "$pr" --comment "Issue preview retired by scripts/request-issue-preview.sh --cleanup."
    echo "Closed legacy preview PR $pr"
  done
  rc=0
  git ls-remote --exit-code --heads origin "$branch" >/dev/null || rc=$?
  if [ "$rc" -eq 0 ]; then
    git push origin --delete "$branch"
    echo "Deleted $branch; pr-preview-cleanup.yml reclaims issue-preview/${ISSUE}/ on the branch-delete event."
  elif [ "$rc" -eq 2 ]; then
    echo "$branch does not exist on origin; nothing to delete."
    echo "To reclaim an orphaned prefix: gh workflow run pr-preview-cleanup.yml -f issue_id=${ISSUE}"
  else
    echo "request-issue-preview: could not query origin for $branch (git ls-remote exit $rc)" >&2
    exit "$rc"
  fi
  exit 0
fi

if [ "$#" -eq 0 ]; then
  echo "$USAGE" >&2
  exit 2
fi

REPO_ROOT="$(git rev-parse --show-toplevel)"
cd "$REPO_ROOT"

NAME_RE='^[A-Za-z0-9._ -]+$'
files=()
for f in "$@"; do
  if [ ! -f "$f" ]; then
    echo "request-issue-preview: not a regular file: $f" >&2
    exit 2
  fi
  case "$(basename -- "$f")" in
    *.scad|meta.json|dependency-graph.md) ;;
    *)
      echo "request-issue-preview: not a .scad, meta.json or dependency-graph.md file: $f" >&2
      exit 2
      ;;
  esac

  rel="$(realpath --relative-to="$REPO_ROOT" -- "$f")"
  case "$rel" in
    /*|../*)
      echo "request-issue-preview: path escapes the repo: $f" >&2
      exit 2
      ;;
  esac

  base="$(basename -- "$rel")"
  if ! [[ "$base" =~ $NAME_RE ]]; then
    echo "request-issue-preview: basename violates filename charset [A-Za-z0-9._ -]: $f" >&2
    exit 2
  fi

  files+=("$rel")
done

git fetch origin main --quiet

# Build the preview commit without touching HEAD, the working tree, or the
# real index, so this can run mid-plan without disturbing any other work in
# the worktree.
tmp_index="$(mktemp "${TMPDIR:-/tmp}/issue-preview-index.XXXXXX")"
trap 'rm -f "$tmp_index"' EXIT
export GIT_INDEX_FILE="$tmp_index"
# read-tree seeds the index with the whole origin/main tree (flake.nix,
# .github/, scripts/, ...) so the pushed branch can still run build.yml; a
# bare `git add` into an empty index would push only the candidate files
# and CI would have nothing to render them with.
git read-tree origin/main
# -f is required: candidate files under an ignore rule (e.g. *.stl) would
# otherwise be silently skipped instead of staged.
git add -f -- "${files[@]}"
tree="$(git write-tree)"
commit="$(git commit-tree "$tree" -p "$(git rev-parse origin/main)" \
    -m "preview: candidate geometry for issue ${ISSUE}")"
unset GIT_INDEX_FILE

git push --force origin "${commit}:refs/heads/${branch}"

viewer="${PREVIEW_BASE}/${ISSUE}/${commit:0:8}/"
echo "$branch"
echo "$viewer"
echo "${viewer}preview-summary.json"
echo "Both URLs serve once the CI build finishes: gh run list --branch $branch"
