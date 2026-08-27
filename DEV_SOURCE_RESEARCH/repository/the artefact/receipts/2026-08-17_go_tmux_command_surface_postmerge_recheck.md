# GO post-merge recheck — managed tmux command surface

Date: 2026-08-17
Trigger: `go`
Canonical slice under recheck: `e3c705df766c0fd719bb5fb47e95ae86d330cec7` (still contained by later `main` head `87c9eb3f8d435fcf33d6cdb5398487e6adfcd109`)
Original fusion: PR #491, squash `d0decae930197d4b5c2254b8154d310c8e8aaa23`

## Purpose

Post-fusion regression only. Preserve the original branch receipt unchanged and independently verify that the merged tmux policy remains coherent with adjacent canonical terminal/container tests after parallel workers updated the older tmux-isolation expectations.

## Exact byte bindings

- `clayverse/terminal_sessions.py` -> `b42d175745fa53c45b81fa1affda4f12a4093541`
- `Dockerfile` -> `1722b0983154e389efa723b5f1afeea8c42fd373`
- `.dockerignore` -> `74ab0a192ba32e26fa4cfdd5f970b97f725c864f`
- `tests/test_tmux_command_surface_fence.py` -> `e9600a54bc187111aaa47f3b8067983058ba988a`
- `tests/test_terminal_tmux_isolation.py` -> `d4c25ffed9d1a40dc426c7594805ae06c0b05e35`
- `tests/test_build_context_boundary.py` -> `9fe0a22cd967b680f103eb28282703c39c1f1a30`
- `tests/test_container_control_plane_permissions.py` -> `2dc6479c400c6aca80b8e4e19d7afc75a3ed32fd`

The isolated container recomputed Git blob ids for the material used by each staged regression batch before execution; all compared ids matched.

## Observed isolated execution

Authorized non-production OpenAI container:

1. initial exact focused slice: `pytest -q tests/test_tmux_command_surface_fence.py` -> `5 passed in 0.07s`;
2. adjacent container/control-plane recheck -> `9 passed in 0.05s`;
3. after canonical `test_terminal_tmux_isolation.py` was aligned by parallel fusion, combined recheck:
   `pytest -q tests/test_tmux_command_surface_fence.py tests/test_terminal_tmux_isolation.py tests/test_build_context_boundary.py tests/test_container_control_plane_permissions.py`
   -> `12 passed in 0.05s`.

GitHub Actions for the original PR did not execute test steps: the identity-guard job reported `steps: []` and `runner_id: 0`. This is execution admission failure, not a test failure.

## Live tmux falsifier status

Still UNOBSERVED on this surface.

- no tmux binary is installed locally;
- apt has no local candidate/cache because network package metadata is unavailable;
- Debian current package metadata confirms Trixie/stable uses tmux `3.5a-3`;
- the isolated downloader rejects Debian binary/source archive MIME types, so the relevant package could not be admitted for a real parser/client run.

This limitation is sandbox/tool admission, not ClayVerse PASS or FAIL.

## Current interpretation

- managed tmux source/policy mechanism: SUPPORTED
- adjacent exact source regressions: PASS (12/12 for stated slice)
- canonical fusion to main: DONE
- real packaged tmux behavior: UNOBSERVED
- exact OCI build/runtime: UNOBSERVED
- whole ClayVerse: IN_PROGRESS

Next executable discriminator when an admitted runtime exists: build/start the exact ClayVerse image, inspect effective tmux prefixes/key tables for both canonical servers, then send the former default browser prefix/command sequence and verify it reaches Claude as pane input without creating a tmux command prompt, extra pane, shell, or process.

Unusual experiment: NOT RUN (`COORDINATION_BLOCKED` under the current GO lease because no immutable shared trigger id / sufficiently unique trigger timestamp is available).
