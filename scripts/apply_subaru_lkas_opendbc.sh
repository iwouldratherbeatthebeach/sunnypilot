#!/usr/bin/env bash
set -euo pipefail

# Apply Subaru LKAS-angle/Crosstrek-related opendbc PRs into sunnypilot's opendbc submodule.
# Run from the root of your sunnypilot fork.
#
# Optional environment variables:
#   SUBARU_BRANCH=subaru-crosstrek-wilderness-lkas-angle
#   OPENDBC_REMOTE=git@github.com:YOUR_GITHUB_USER/opendbc.git
#   PUSH_OPENDBC=1
#
# Why a separate opendbc remote matters:
# sunnypilot keeps opendbc as a git submodule. Your main sunnypilot fork can only
# reference opendbc commits that exist in a reachable opendbc repository. If you
# want to push the result and install from GitHub, fork opendbc too and set
# OPENDBC_REMOTE to your opendbc fork.

SUBARU_BRANCH="${SUBARU_BRANCH:-subaru-crosstrek-wilderness-lkas-angle}"
OPENDBC_DIR="opendbc_repo"

if [[ ! -d .git ]]; then
  echo "ERROR: run this from the root of your sunnypilot fork" >&2
  exit 1
fi

if [[ ! -f .gitmodules ]] || ! grep -q "path = ${OPENDBC_DIR}" .gitmodules; then
  echo "ERROR: this repo does not appear to have the ${OPENDBC_DIR} submodule" >&2
  exit 1
fi

git submodule update --init --recursive "${OPENDBC_DIR}"

pushd "${OPENDBC_DIR}" >/dev/null

if ! git remote | grep -qx commaai; then
  git remote add commaai https://github.com/commaai/opendbc.git
fi

git fetch commaai master
# PR #2864: 2025 Crosstrek platform + LKAS angle support work.
git fetch commaai pull/2864/head:pr-2864-crosstrek-lkas
# PR #3454: upstream-focused Subaru LKAS Angle support and safety model.
git fetch commaai pull/3454/head:pr-3454-subaru-lkas-safety

git checkout -B "${SUBARU_BRANCH}"

merge_pr() {
  local ref="$1"
  local label="$2"
  echo "\n--- merging ${label} (${ref}) ---"
  if git merge --no-edit --no-ff "${ref}"; then
    echo "merged ${label}"
  else
    echo "\nMerge conflict while applying ${label}." >&2
    echo "Resolve conflicts inside ${OPENDBC_DIR}, then run:" >&2
    echo "  git add <resolved files>" >&2
    echo "  git commit" >&2
    echo "Then return to the sunnypilot root and commit the submodule pointer." >&2
    exit 2
  fi
}

merge_pr pr-2864-crosstrek-lkas "PR #2864 Crosstrek/LKAS angle platform work"
merge_pr pr-3454-subaru-lkas-safety "PR #3454 Subaru LKAS angle safety model"

if [[ -n "${OPENDBC_REMOTE:-}" ]]; then
  if git remote | grep -qx userfork; then
    git remote set-url userfork "${OPENDBC_REMOTE}"
  else
    git remote add userfork "${OPENDBC_REMOTE}"
  fi
  if [[ "${PUSH_OPENDBC:-0}" == "1" ]]; then
    git push -u userfork "${SUBARU_BRANCH}"
  else
    echo "\nOPENDBC_REMOTE is set but PUSH_OPENDBC!=1; not pushing submodule branch."
    echo "Push manually with: git push -u userfork ${SUBARU_BRANCH}"
  fi
fi

popd >/dev/null

git add "${OPENDBC_DIR}"

echo "\nSubaru LKAS opendbc submodule branch prepared."
echo "Review and commit in the parent sunnypilot repo:"
echo "  git diff --submodule"
echo "  git commit -m 'subaru: update opendbc for Crosstrek LKAS angle testing'"
echo "\nThen push both repos if you are using a personal opendbc fork:"
echo "  (cd ${OPENDBC_DIR} && git push -u <your-opendbc-remote> ${SUBARU_BRANCH})"
echo "  git push -u origin <your-sunnypilot-branch>"
