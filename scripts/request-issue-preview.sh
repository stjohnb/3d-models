#!/usr/bin/env bash
# request-issue-preview.sh — Open a disposable preview PR for candidate geometry proposed on an issue (#518).
#
# No .scad is rendered until a PR exists, so plan review is otherwise blind:
# the planner can't show the maintainer what a proposed model actually looks
# like before the plan is approved. This script runs on the planner host
# (openclaw, ~3.8 GB RAM, shared with the Claws service) and deliberately
# performs ZERO local rendering — it only stages candidate files onto a
# branch and opens a draft PR so build.yml's existing pull_request path
# renders them on the ryzen runner instead.
#
# The resulting PR is a disposable preview artifact, draft + labelled
# "Claws Ignore", and must never be merged as an implementation PR — close
# it once the plan is decided (pr-preview-cleanup.yml then reclaims its S3
# prefix).
#
# Usage: scripts/request-issue-preview.sh <issue-number> <file.scad> [more.scad ...]

set -euo pipefail

ISSUE="${1:-}"
shift || true

case "$ISSUE" in
  ''|*[!0-9]*)
    echo "usage: scripts/request-issue-preview.sh <issue-number> <file.scad> [more.scad ...]" >&2
    exit 2
    ;;
esac

if [ "$#" -eq 0 ]; then
  echo "usage: scripts/request-issue-preview.sh <issue-number> <file.scad> [more.scad ...]" >&2
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
  case "$f" in
    *.scad) ;;
    *)
      echo "request-issue-preview: not a .scad file: $f" >&2
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

branch="claws/preview-issue-${ISSUE}"
git push --force origin "${commit}:refs/heads/${branch}"

pr="$(gh pr list --head "$branch" --state open --json number --jq '.[0].number // empty')"

if [ -n "$pr" ]; then
  # The force-push above already fired `synchronize` on the existing PR;
  # re-creating it would just duplicate what CI is already about to redo.
  url="$(gh pr view "$pr" --json url --jq .url)"
else
  # The "Claws Ignore" label MUST be applied here, at creation. Splitting it
  # into a follow-up `gh pr edit --add-label` would leave a window where
  # Claws could pick the PR up as a normal, non-ignored PR.
  #
  # The body below deliberately refers to "issue ${ISSUE}" as plain text
  # with NO leading '#'. A '#518'-style reference would cross-link this PR
  # into the issue's timeline and risks Claws treating it as the issue's
  # real implementation PR (e.g. marking the issue In Review). Do not "fix"
  # this by adding the '#' back.
  body="$(printf '%s\n' \
    "Disposable preview of candidate geometry proposed for issue ${ISSUE}." \
    "" \
    "Opened by \`scripts/request-issue-preview.sh\` so the maintainer can see rendered, mesh-validated geometry while reviewing the plan. It is a draft, labelled **Claws Ignore**, and must never be merged — close it once the plan is decided (that also reclaims its S3 preview prefix via pr-preview-cleanup.yml)." \
    "" \
    "See docs/ci-pipeline.md, \"Preview PRs for issue planning\".")"
  # A failure here (e.g. the "Claws Ignore" label no longer exists) must
  # propagate as a non-zero exit under `set -e`, not be swallowed — that
  # failure is the correct signal for the planner to see.
  url="$(gh pr create --draft --base main --head "$branch" \
    --label "Claws Ignore" \
    --title "preview: candidate geometry for issue ${ISSUE} [do not merge]" \
    --body "$body")"
fi

echo "$branch"
echo "$url"
echo "Preview comment appears on the PR once the ryzen build finishes: gh pr checks <N> --watch"
