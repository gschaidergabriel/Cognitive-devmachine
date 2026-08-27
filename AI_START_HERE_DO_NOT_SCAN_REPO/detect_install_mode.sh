#!/usr/bin/env bash
set -u

# Trigger-3 installer discovery helper.
# Read-only and non-networking: no provider calls, no secret lookup, no writes.
# This is discovery input only, never installation/runtime PASS evidence.

start_path="${1:-.}"
repo_root=""

have() { command -v "$1" >/dev/null 2>&1; }
yn() { if "$@"; then printf 'yes'; else printf 'no'; fi; }

if have git; then
  repo_root="$(git -C "$start_path" rev-parse --show-toplevel 2>/dev/null || true)"
fi

printf 'FRANKENSTEIN_INSTALL_DISCOVERY/v1\n'
printf 'start_path=%s\n' "$start_path"
printf 'git_command=%s\n' "$(yn have git)"
printf 'repo_detected=%s\n' "$(if [ -n "$repo_root" ]; then printf yes; else printf no; fi)"

if [ -n "$repo_root" ]; then
  printf 'repo_root=%s\n' "$repo_root"
  printf 'repo_readable=%s\n' "$(if [ -r "$repo_root" ]; then printf yes; else printf no; fi)"
  printf 'repo_writable=%s\n' "$(if [ -w "$repo_root" ]; then printf yes; else printf no; fi)"
  printf 'git_worktree_clean=%s\n' "$(if [ -z "$(git -C "$repo_root" status --porcelain 2>/dev/null)" ]; then printf yes; else printf no; fi)"
  printf 'head=%s\n' "$(git -C "$repo_root" rev-parse HEAD 2>/dev/null || printf unknown)"
else
  printf 'repo_root=unknown\n'
  printf 'repo_readable=unknown\n'
  printf 'repo_writable=unknown\n'
  printf 'git_worktree_clean=unknown\n'
  printf 'head=unknown\n'
fi

printf 'claude_cli=%s\n' "$(yn have claude)"
printf 'codex_cli=%s\n' "$(yn have codex)"
printf 'hermes_cli=%s\n' "$(yn have hermes)"
printf 'python3=%s\n' "$(yn have python3)"
printf 'bash=%s\n' "$(yn have bash)"
printf 'network_test=NOT_RUN\n'
printf 'provider_test=NOT_RUN\n'
printf 'secret_lookup=NOT_RUN\n'
printf 'lifecycle_hook=UNVERIFIED\n'
printf 'durable_state=UNVERIFIED\n'
printf 'effect_receipt=UNVERIFIED\n'
printf 'classification=DISCOVERY_ONLY_NOT_AN_INSTALL_RESULT\n'