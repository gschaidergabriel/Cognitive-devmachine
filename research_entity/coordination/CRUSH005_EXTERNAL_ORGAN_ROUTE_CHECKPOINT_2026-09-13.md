# CRUSH005 — EXTERNAL ORGAN ROUTE OBSERVATION CHECKPOINT — 2026-09-13

Status: **FULL BOUNDED EXACT-DONOR COMPILE PASS**

This checkpoint is scoped. It does not activate a provider, call ChatGPT/Claude/Free-Pool, replace any existing bridge/router, mutate Gabriel's live Free-Frank harness, or promote whole OMEGA/HCU/GRID/GWT/product credit.

## Exact subjects

- Research branch: `chatgpt-work/entityos-crush-omega-bootstrap-20260913`
- CRUSH005 seed/source head under test: `bbca92180f7d11b38b4679d39a1bb79db8918e60`
- Source commit: `758dbe1c036f72d9d93a8846b949104fcb913164` — `CRUSH005: add external organ route observations`
- Test commit: `bbca92180f7d11b38b4679d39a1bb79db8918e60` — `CRUSH005: test external organ route continuity`
- Exact upstream donor: `charmbracelet/crush@d333e04385f9e1d1523cea7b417cb5e8798a713a`
- Validation host: `machine_id=ai-core-node`, `owner=gabriel`, `execution_boundary=REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`

## What CRUSH005 adds

CRUSH004 already established the single portable `omega.OrganRoute` observation contract and binds its digest into persistent turn/reentry lineage without deriving EntityIdentity from provider/model routing.

CRUSH005 reuses that exact contract. It does **not** add a second router or dispatch layer.

New evidence-only constructors in `internal/omega/external_route.go` map already-selected external surfaces to the existing `OrganRoute`:

- ChatGPT bridge -> `kind=bridge`, `organ_id=chatgpt`
- Claude Code / CLI bridge -> `kind=bridge`, `organ_id=claude-code`
- Free-Pool provider path -> `kind=provider`, `organ_id=free-pool`

`adapter_id`, `provider_id`, and `model_id` are caller-supplied observations and are normalized by the pre-existing `OrganRoute` contract. Constructing any of these values grants no dispatch, provider, effect, login, permission, or mutation authority.

This preserves the established Frankenstein bridge law: the external bridge/CLI/provider surface owns execution; OMEGA records route evidence only.

## Executable discriminators

`external_route_test.go` proves at bounded package scope:

1. ChatGPT / Claude Code / Free-Pool route observations normalize into distinct non-empty route digests.
2. Route-only evidence does not leak into `RenderSystemContext()`.
3. Swapping ChatGPT -> Claude Code -> Free-Pool preserves persistent `EntityID`.
4. The predecessor/reentry chain remains continuous across organ swaps.
5. Every turn persists the route digest that was actually supplied to `Compile()`.

## Preserved negative evidence

The first real-host validator was **FAIL / exit 1**:

- command: `crush005-ai-core-node-20260913t1457-route-compile`
- machine/owner/boundary attribution was valid.
- failure occurred before the first live-file hash because the validator incorrectly addressed the three harness files directly under `$HOME`.
- this is a validator/subject-binding failure, not an OMEGA/Go semantic negative.

It is intentionally not relabeled PASS.

A follow-up locator command, `crush005-ai-core-node-20260913t1459-locate-live-harness`, returned **PASS / exit 0** and re-established the exact live subjects:

- `/home/ai-core-node/.claude/star/harness_crush_knopf.sh`
  - `95a9311a4f47457b3c5e100fe9bd8d62253711eb889386e521bc68a3ddf7fce3`
- `/home/ai-core-node/.claude/star/harness_crush_knopf.py`
  - `db05347f908c891e526bdb47d6497e24aa1defc94b824f502ecd579ab73dbd61`
- `/home/ai-core-node/.claude/star/harness_crush.py`
  - `59a3a043c0b4b687e998837027f86a8fd982ff4038ca58b8834f3243ae2b0613`
- `/home/ai-core-node/frankenstein-repo/CRUSH.md`
  - `1980f471ff088d3fea923b66f69eb1e0e8d837f546c86a84740111bbbeddbf99`

The locator also found `/home/ai-core-node/.config/crush/CRUSH.md` with a different hash. It is **not** substituted for the already-bound live Free-Frank harness subject.

## Exact-donor Go closure

Corrected validator:

`crush005-ai-core-node-20260913t1500-route-compile-v2`

Receipt:

- status: `PASS`
- exit: `0`
- host: `ai-core-node`
- owner: `gabriel`
- machine_id: `ai-core-node`
- execution boundary: `REAL_LOCAL_HOST_AI_CORE_NODE_NOT_SANDBOXED`
- exact donor: `d333e04385f9e1d1523cea7b417cb5e8798a713a`
- exact seed: `bbca92180f7d11b38b4679d39a1bb79db8918e60`
- Go archive SHA-256: `63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445`
- toolchain: `go version go1.27.1 linux/amd64`

Results:

- `go test ./internal/omega -count=1` -> PASS
- `go test ./internal/agent -run '^$' -count=1` -> PASS / compile closure
- all four live Free-Frank harness hashes before/after -> byte-identical
- markers:
  - `CRUSH005_EXTERNAL_ROUTE_GO_TEST_PASS`
  - `CRUSH005_AGENT_COMPILE_PASS`
  - `CRUSH005_LIVE_HARNESS_BYTE_INVARIANT_PASS`

## Promotion fence

Promoted now, and only now:

**CRUSH005 portable external-organ route observation + organ-swap identity/reentry continuity + exact-donor Go-1.27 component compile closure.**

Not promoted:

- no actual ChatGPT/Claude/Free-Pool dispatch from OMEGA;
- no provider authority or Free-Pool reactivation;
- no proof yet that each existing external execution call-site emits this route observation during a real turn;
- no live Free-Frank harness mutation;
- no production activation;
- no whole OMEGA/HCU/GRID/GWT/J-Space/training/product credit.

## Next nonduplicate boundary

Do **not** build another router.

First discover and bind the already-existing external organ/activity ingress surfaces (including the current Frankenstein ChatGPT send/harvest path, Claude Code/CLI route, and provider-fallback activity path). The next gate is to make those existing execution call-sites emit/adapt route metadata into the same `OrganRoute` / persistent-turn observation path **without moving dispatch authority into OMEGA** and without reopening current provider HARD_OFF constraints.

If a canonical organ-activity/event ingress already exists, reuse it; do not introduce a parallel event fabric.
