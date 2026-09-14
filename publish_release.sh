#!/bin/bash
set -euo pipefail

usage() {
  printf '%s\n' \
    "Usage: ./publish_release.sh VERSION [--publish] [--notes-file FILE]" \
    "" \
    "Default: validate and print the release plan without changing Git or GitHub." \
    "--publish: commit selected files, push the current branch, and create a GitHub Release."
}

version=""
publish=0
notes_file=""
while (($#)); do
  case "$1" in
    --publish) publish=1 ;;
    --notes-file)
      shift
      (($#)) || { usage; exit 2; }
      notes_file="$1"
      ;;
    -h|--help) usage; exit 0 ;;
    -*) printf 'Unknown option: %s\n' "$1" >&2; usage; exit 2 ;;
    *)
      [[ -z "$version" ]] || { printf 'Only one VERSION is allowed.\n' >&2; exit 2; }
      version="$1"
      ;;
  esac
  shift
done

[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { usage; exit 2; }

script_dir="$(cd "$(dirname "$0")" && pwd)"
cd "$script_dir"
manifest="$script_dir/release-files.txt"
asset="$script_dir/dist/SSGReciprocalDatabase-$version.paclet"
tag="v$version"
branch="$(git branch --show-current)"

[[ -n "$branch" ]] || { printf 'Detached HEAD is not supported.\n' >&2; exit 1; }
[[ -f "$manifest" ]] || { printf 'Missing release manifest: %s\n' "$manifest" >&2; exit 1; }
[[ -f "$asset" ]] || { printf 'Missing release asset: %s\n' "$asset" >&2; exit 1; }
[[ -z "$notes_file" || -f "$notes_file" ]] || { printf 'Missing notes file: %s\n' "$notes_file" >&2; exit 1; }

declared="$(sed -n 's/^[[:space:]]*Version[[:space:]]*->[[:space:]]*"\([^"]*\)".*/\1/p' SSGReciprocalDatabase/PacletInfo.wl)"
[[ "$declared" == "$version" ]] || {
  printf 'Version mismatch: PacletInfo.wl=%s, requested=%s\n' "$declared" "$version" >&2
  exit 1
}

remote_url="$(git remote get-url origin)"
[[ "$remote_url" == *github.com* ]] || { printf 'origin is not a GitHub remote: %s\n' "$remote_url" >&2; exit 1; }

files=()
while IFS= read -r path; do
  [[ -z "$path" || "$path" == \#* ]] && continue
  [[ -e "$path" ]] || { printf 'Manifest path does not exist: %s\n' "$path" >&2; exit 1; }
  files+=("$path")
done < "$manifest"

checksum="$(shasum -a 256 "$asset" | awk '{print $1}')"
printf 'Release v%s\n' "$version"
printf 'Branch: %s\n' "$branch"
printf 'Remote: %s\n' "$remote_url"
printf 'Asset: %s\n' "$asset"
printf 'SHA256: %s\n' "$checksum"
printf 'Manifest entries: %s\n' "${#files[@]}"

if ((publish == 0)); then
  if gh auth status -h github.com >/dev/null 2>&1; then
    printf 'GitHub authentication: OK\n'
  else
    printf 'GitHub authentication: EXPIRED OR MISSING\n'
    printf 'Run once before publishing: gh auth login -h github.com -p https -w\n'
  fi
  printf '\nDry run only. Files that differ from HEAD within the release manifest:\n'
  git status --short -- "${files[@]}"
  printf '\nRun ./publish_release.sh %s --publish to publish.\n' "$version"
  exit 0
fi

if ! gh auth status -h github.com >/dev/null 2>&1; then
  printf '%s\n' \
    'GitHub authentication is missing or expired.' \
    'Run this once: gh auth login -h github.com -p https -w' \
    'The credential will be stored by GitHub CLI/macOS Keychain; do not put a token in this script.' >&2
  exit 1
fi

[[ -z "$(git diff --cached --name-only)" ]] || {
  printf 'The Git index already contains staged changes. Commit or unstage them before publishing.\n' >&2
  exit 1
}

git add -- "${files[@]}"
if [[ -z "$(git diff --cached --name-only)" ]]; then
  expected_subject="Release SSGReciprocalDatabase $version"
  actual_subject="$(git log -1 --format=%s)"
  [[ "$actual_subject" == "$expected_subject" ]] || {
    printf 'No release files changed and HEAD is not the expected release commit.\n' >&2
    exit 1
  }
  printf 'Resuming from existing release commit: %s\n' "$actual_subject"
else
  printf '\nFiles staged for release:\n'
  git diff --cached --name-status
  git commit -m "Release SSGReciprocalDatabase $version"
fi
git push origin "$branch"

if gh release view "$tag" >/dev/null 2>&1; then
  printf 'GitHub Release already exists; nothing more to upload.\n'
  gh release view "$tag" --json url,tagName,name,assets
  exit 0
fi

release_args=(release create "$tag" "$asset" --target "$branch" --title "SSGReciprocalDatabase $version")
if [[ -n "$notes_file" ]]; then
  release_args+=(--notes-file "$notes_file")
else
  release_args+=(--generate-notes)
fi
gh "${release_args[@]}"
gh release view "$tag" --json url,tagName,name,assets
