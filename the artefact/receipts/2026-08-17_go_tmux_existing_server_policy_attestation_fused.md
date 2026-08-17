# ClayVerse fused tmux existing-server policy attestation receipt

Date: 2026-08-17
Organ: GPT-5.6 Sol temporary Clay organ
Trigger: `go` at 13:52 +07
Classification: ordinary product hardening/regression after the single globally claimed unusual experiment; adds **zero** unusual experiments.

## Problem

Passing `-f /etc/clayverse/managed-tmux.conf` on every tmux client invocation does not by itself establish that a pre-existing server on the same `-L` socket loaded that policy. A stale server could therefore retain a tmux command surface even though later clients were launched with `-f`.

## Fused candidate

Branch: `go/tmux-policy-attestation-fused-20260817-1352-sol`
Base observed when branch was created: `e7d11124a2e3d51a7e1c7aaa188783cadf62c9ed`

Exact implementation identities:
- `the artefact/clayverse/terminal_sessions.py` Git blob: `b37101df4bc959996e5c6dfd3a17c87977ce9a68`
- `the artefact/policy/managed-tmux.conf` Git blob: `840d5048bda96b778cd9fb7f148bf7f24b60fa88`

The policy writes `@clayverse_managed_policy=clayverse-browser-transport-v1` only after disabling both tmux prefixes and unbinding keys. `TerminalSessionManager` then checks the live server marker, `prefix=None`, and `prefix2=None` before reusing an existing session and after creating a new one. Missing, mismatched, timeout, or OS-error attestation fails closed with `TerminalRuntimeError`.

The candidate is fused with the current explicit Claude MCP tool allowlist (`session_state`, `request_effect`); it does not restore the older wildcard.

## Authorized isolated execution

Environment: authorized non-production isolated OpenAI container; no VPS/self-hosted/production execution.

Before the focused run, the locally executed source and policy were Git-blob hashed and matched the branch identities above exactly.

Focused result:
- Python `compileall`: PASS
- focused tmux policy/attestation pytest slice: **7 passed / 0 failed**
- managed policy structure/marker: PASS
- canonical `-L`/`-f` command pinning: PASS
- live-server attestation command construction: PASS
- existing server missing marker: FAIL CLOSED / PASS
- existing server with restored `C-b` prefix: FAIL CLOSED / PASS
- new-session command pinning: PASS
- new session missing marker: FAIL CLOSED / PASS

Adjacent command/env tests were updated only to keep their existing responsibility focused by stubbing `_assert_tmux_server_policy`; the attestation behavior is tested in the dedicated tmux fence suite.

## External mechanism basis

Upstream tmux documentation states that configuration is processed for a server and documents server-scoped user options (`@...`) via `set-option -s`; it also documents user options as server/session/window/pane scoped. This supports the marker mechanism but is not a substitute for live runtime execution.

## Remaining evidence gap

Real tmux binary execution for this exact candidate remains UNOBSERVED. The authorized Vercel Sandbox bridge is currently blocked before Sandbox start by the provider preview/build-rate limit. An attempted official Debian tmux package fetch in the isolated OpenAI container could not resolve the package host, so no binary was installed and no live tmux claim is made.

Next discriminator: once Vercel preview admission reopens, execute this exact candidate with a real tmux server in two cases: (1) server freshly started with the managed policy must attest and remain usable; (2) deliberately pre-existing server started without the policy must be rejected before browser attachment.

Whole ClayVerse product PASS is not established by this receipt.
