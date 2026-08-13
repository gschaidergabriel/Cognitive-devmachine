# WP1: runs-on ubuntu-latest -> self-hosted

Repo: gschaidergabriel/Dr.-Unterweger. Timestamp: 20260813T1659p0700.

## Measured fact (starting point, given by task)
4 self-hosted runner ONLINE: clay, clay-2, clay-3, clay-4, label exactly
`["self-hosted","Linux","X64"]`. Workflow job pinned to `runs-on: ubuntu-latest`
never get assigned a GitHub-hosted runner in this repo -> job dies at ~4s,
0 step ran, empty runner name -> counted among the 278 fake-red mark.

## Live count (measured in shallow clone /tmp/dru)
- workflow yml file total in `.github/workflows/`: **145**
- file using `runs-on: ubuntu-latest` (plain, non-matrix): **9**
- file already using `runs-on: self-hosted`: **139**
- matrix/array form `runs-on: [ubuntu-latest]`: **0** found

9 + 139 = 148, not 145 — some file use neither literal pattern at top job
level (not investigated further, out of package scope).

## 9 file changed
- .github/workflows/clay-v18-push-dispatch-bridge.yml
- .github/workflows/claycode-wp04-pr-hosted-shadow.yml
- .github/workflows/frank-bounded-issue-dispatch-bridge.yml
- .github/workflows/frank-central-state.yml
- .github/workflows/clay-go-python-import-path-equivalence.yml
- .github/workflows/frank-effect-authority-provenance-gap.yml
- .github/workflows/frank-vps-runner-cross-repo-scope-probe.yml
- .github/workflows/frank-sqlite-v5-evidence-gate-v1.yml
- .github/workflows/frank-v71-hardening.yml

## Change
`git diff` before commit: exactly 9 files changed, 9 insertions(+), 9
deletions(-), each a single line `runs-on: ubuntu-latest` ->
`runs-on: self-hosted`. Nothing else touched.

## Delivery
- branch: `fix/runs-on-self-hosted`
- commit: `92c927f5dc53e2b9840e72dce2f9f40111d72a11`
- PR: **#575** — https://github.com/gschaidergabriel/Dr.-Unterweger/pull/575
- PR base: `main`, head: `fix/runs-on-self-hosted`
- live recheck via `gh pr view 575 ...`: state `OPEN`, mergeable
  `MERGEABLE`
- main branch: not touched (no push, no merge, no --no-verify)

## Open / PENDING
- PENDING: no workflow run of the 9 changed file has been triggered or
  observed yet, so it is not confirmed the job actually goes green on a
  clay runner — only the runner-assignment failure mode is removed.
- PENDING: outcome on `main` after eventual merge not measured (out of
  package scope; PR not merged, no push to main was done).
