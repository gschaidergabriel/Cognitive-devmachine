# GO receipt — tmux browser command-surface fence

Date: 2026-08-17
Trigger: `go`
Base canonical main: `ebb16ac031780c920fe9e4617b404ade73c4dd20`
Tested branch commit: `60253ca4f7a0e318af739d9d18e620129e4b6220`
Branch: `go/tmux-command-surface-fence-20260817-1353`

## Frontier selected

The browser attaches as a full tmux client to the persistent Claude session. Per upstream tmux semantics, default attached clients have a command prefix and command prompt, and tmux commands such as new-window/split-window/run-shell can start programs. That creates a process-execution path outside the ClayVerse EffectGate even though Claude built-in tools and Bash are denied.

No overlapping PR was found for a tmux command-surface/command-prompt fence. Existing tmux isolation work separates Gabriel and Andreas onto different tmux servers but does not remove tmux's own command language from the browser-facing client.

## Repair

- add root-owned image policy `policy/managed-tmux.conf`;
- set both tmux prefixes to `None`;
- remove all tmux key bindings with `unbind-key -a`;
- require the managed tmux policy at readiness;
- route session probe, session creation, and browser attach through one `_tmux_argv` helper that always supplies `-f /etc/clayverse/managed-tmux.conf`;
- install the policy read-only (`0444`) in the image;
- add focused regression tests for policy content, probe/create/attach argv fencing, and image ownership/permissions.

## Exact isolated regression evidence

Execution surface: authorized isolated OpenAI container, non-production.
Network clone path: unavailable because the container could not resolve `github.com`; branch files were therefore read back through the GitHub connector and reconstructed byte-for-byte in the isolated container.

Git blob identity checks before test:

- `clayverse/terminal_sessions.py` -> `b42d175745fa53c45b81fa1affda4f12a4093541` MATCH
- `clayverse/identity.py` -> `c3b8ecba0942c722d08efbf03e57d71c3a4f5cf3` MATCH
- `policy/managed-tmux.conf` -> `1130ff0ab6db7c608ce33819ad97256eb4afbfbb` MATCH
- `Dockerfile` -> `1722b0983154e389efa723b5f1afeea8c42fd373` MATCH
- `tests/test_tmux_command_surface_fence.py` -> `e9600a54bc187111aaa47f3b8067983058ba988a` MATCH

Observed commands/results:

- Python compile of `clayverse/terminal_sessions.py`: PASS
- `pytest -q tests/test_tmux_command_surface_fence.py`: `5 passed in 0.07s`
- tmux binary presence check: NOT AVAILABLE on this execution surface

Interpretation: source mechanism and focused regression are supported at the exact tested branch bytes. Actual tmux parser/runtime behavior inside the final OCI image remains UNOBSERVED here and must not be promoted to runtime PASS.

## External mechanism check

Current upstream tmux documentation states that attached clients use a prefix and command prompt by default; new-window/split-window can start commands; `-f` selects an alternative configuration file; `prefix` and `prefix2` accept `None`; and `unbind-key -a` removes all key bindings. This supports the repair mechanism independently of the source test.

## Counterhypothesis / remaining falsifier

Strongest remaining counterhypothesis: the packaged tmux version or actual image startup does not apply the managed file as expected, or an unbound non-key client control path remains reachable from browser bytes.

Required falsifier: in an exact built ClayVerse OCI image, start each user tmux server with the managed policy, inspect effective prefix/key tables, attach through the browser-facing PTY, inject the former default prefix/command sequence, and prove no additional shell/program/pane can be created while normal Claude terminal input still passes through.

## GO unusual experiment

NOT RUN — `COORDINATION_BLOCKED`. The available user-trigger timestamp is only minute-precise (`2026-08-17T13:53+07:00`) and no immutable shared request/turn id is available, so the current GO experiment lease protocol requires fail-closed consumption of zero unusual experiments.

## Acceptance

- component source repair: CANDIDATE
- focused exact-blob regression: PASS
- live tmux runtime: UNOBSERVED
- OCI runtime: UNOBSERVED
- whole ClayVerse: IN_PROGRESS
