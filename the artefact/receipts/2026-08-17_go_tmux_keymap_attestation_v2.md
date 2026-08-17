# ClayVerse tmux transport-only keymap attestation v2 receipt

Date: 2026-08-17
Organ: GPT-5.6 Sol temporary Clay organ
Trigger: `go` at 13:52 +07
Unusual experiment count added: **0**

## Counterexample found after v1 merge

The v1 managed policy used `unbind-key -a` and described it as removing the browser tmux keymap. Current upstream tmux source shows that `unbind-key -a` without `-T` selects only the `prefix` table. It does not remove the `root`, `copy-mode`, or `copy-mode-vi` tables. This invalidated the stronger v1 wording and left a real no-prefix/key-table counterhypothesis.

Upstream source anchors inspected:
- `tmux/tmux` `cmd-unbind-key.c` Git blob `f537fb57670ebe6d4f362e8f2d0142880bfb17c0`: `-a` removes one selected table; without `-T`/`-n`, that table defaults to `prefix`.
- `tmux/tmux` `cmd-list-keys.c` Git blob `e8617c2e3340f6c86715c7a1d975a4ab9986fd56`: unfiltered `list-keys` enumerates all key-binding tables and returns normally with no printed lines when the binding set is empty.

## v2 fix

Branch: `go/tmux-keymap-attestation-20260817-1352-sol`
Base at branch creation: `8710287cafbb13a0eb760aa7e553185afe774a9a`

Exact candidate blobs:
- `the artefact/clayverse/terminal_sessions.py`: `beaf9d829833525decc67338b08b70ffed4b7592`
- `the artefact/policy/managed-tmux.conf`: `559c3bb7e53a81a487bc32250d7cd1b37ccd38d8`

Policy changes:
- explicit `unbind-key -a -T prefix`;
- explicit `unbind-key -a -T root`;
- explicit `unbind-key -a -T copy-mode`;
- explicit `unbind-key -a -T copy-mode-vi`;
- versioned final marker `clayverse-browser-transport-v2`.

Runtime admission additionally requires `tmux list-keys` to return success with empty stdout. Therefore any surviving default/custom/root/copy-mode binding fails closed, even if a server can otherwise present the marker and prefix values.

## Exact isolated execution

Authorized non-production isolated OpenAI container; no VPS/self-hosted/production host.

Before execution, Git-blob hashing matched the candidate identities exactly:
- source `beaf9d829833525decc67338b08b70ffed4b7592`;
- policy `559c3bb7e53a81a487bc32250d7cd1b37ccd38d8`.

Results:
- Python compile: PASS
- focused v2 policy/attestation tests: **8 passed / 0 failed**
- explicit four default tables present in policy: PASS
- valid v2 empty-keymap server: PASS
- v1 marker: FAIL CLOSED / PASS
- surviving root binding: FAIL CLOSED / PASS
- surviving copy-mode binding: FAIL CLOSED / PASS
- reactivated prefix: FAIL CLOSED / PASS
- existing canonical session with valid v2 state: PASS
- newly created server with surviving binding: FAIL CLOSED / PASS

## Scope

This corrects a source/mechanism defect in the already-merged v1 fence. It does not establish live tmux runtime, packaged Claude Code runtime, OCI acceptance, Clerk/PTY acceptance, or whole ClayVerse PASS. Vercel Sandbox preview admission remains the next preferred live discriminator when the provider rate limit reopens.
