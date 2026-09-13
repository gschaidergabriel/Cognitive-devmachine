# CRUSH004 — ORGAN ROUTE / REENTRY CHECKPOINT — 2026-09-13

Status: **FULL BOUNDED EXACT-DONOR COMPILE PASS**

This checkpoint is scoped. It does not activate production, reopen provider authority, promote whole HCU/GRID/GWT credit, or mutate Gabriel's live Free-Frank harness.

## Trigger reentry

`CRUSH` was resolved through the current donor lock and current authority before mutation.

Exact upstream Crush donor used for this cycle:

`charmbracelet/crush@d333e04385f9e1d1523cea7b417cb5e8798a713a`

Current Gabriel live harness donor was refreshed through Local Bridge and its four locked hashes remained unchanged. Current VPS OMEGA donor was refreshed independently and remained on release:

`093e470c5c06e3568fda535f081be7f1dcd30035-sigma-cortex-retina-v1-reconcilerfix-001`

Current authority remained fail-closed for new external ClayCode provider execution and explicitly retained `DO_NOT_MODIFY_FRANK_HARNESS`.

## CRUSH004 delta

CRUSH003 already established one shared persistent OMEGA runtime in the top-level Crush coordinator while subagents receive `omega.NoopRuntime{}`.

CRUSH004 adds a portable `omega.OrganRoute` observation with:

- `kind`
- `organ_id`
- `adapter_id`
- `provider_id`
- `model_id`

The normalized route is reduced to a stable SHA-256 `RouteDigest`.

The route is **evidence, not identity and not dispatch authority**:

- EntityIdentity is not derived from provider/model.
- OMEGA does not select or call providers at this seam.
- Crush remains provider/model execution authority.
- Existing Frankenstein/ChatGPT/Claude/Free-Pool bridges remain external execution surfaces until explicitly adapted.
- `RouteDigest` is kept out of `RenderSystemContext()` unless future semantic gates explicitly admit route-derived content.

`TurnInput` now carries `Route OrganRoute` and `Frame` carries `RouteDigest`.

`PersistentRuntime.Compile()` binds `RouteDigest` into turn identity while preserving the persistent `EntityID`.

`PersistentRuntime.Reenter()` stores the route digest in the turn record together with input/output/state lineage digests.

The Crush agent seam observes the already-selected native model as:

- `Kind = provider`
- `OrganID = crush-model`
- `AdapterID = crush-native`
- `ProviderID = largeModel.ModelCfg.Provider`
- `ModelID = largeModel.ModelCfg.Model`

No provider call was made by this CRUSH cycle.

## Executable discriminators

Tests prove:

1. Route digest is deterministic after whitespace normalization.
2. Provider/model swap changes route evidence.
3. Empty route produces no artificial route identity.
4. A provider/model swap combined with a process/runtime-object restart preserves the same `EntityID`.
5. The second turn reenters from the first turn (`PredecessorTurnID`) and advances revision.
6. Route metadata does not leak into model system context by itself.
7. Both route digests persist in causal turn history.

## Exact-donor structural evidence

The private branch was fetched into the authenticated VPS carrier and applied to an isolated checkout of the exact locked Crush donor.

`crush004-structural-readback-20260913T0735Z` = PASS / exit 0.

Readback on exact donor confirmed:

- `ProviderID: largeModel.ModelCfg.Provider`
- `ModelID: largeModel.ModelCfg.Model`
- top-level coordinator constructs `omega.NewPersistentRuntime(...)`
- Noop fallback remains present
- `RouteDigest` is compiled and persisted
- `TestProviderSwapChangesRouteEvidenceNotEntityIdentity` is present
- `git diff --check` passed

The scratch subject showed only the intended donor modifications:

- `internal/agent/agent.go`
- `internal/agent/coordinator.go`
- new `internal/omega/`

## Full Go 1.27 closure

`crush004-full-go-validate-20260913T0740Z` = **PASS / exit 0** on `ai-core-node`, inside an isolated validation cache.

The validator did not install Go system-wide. It resolved the official Go 1.27.1 linux/amd64 archive metadata from `go.dev/dl`, verified SHA-256:

`63d339f0da5ab53635a56f2490a7984dfe12dfcff22ad749f63edaf590168445`

and used:

`go version go1.27.1 linux/amd64`

Exact build subjects:

- donor: `d333e04385f9e1d1523cea7b417cb5e8798a713a`
- CRUSH004 seed: `8006983dfbc92eae0ccae142c78709916a9ed074`

Results:

- `go test ./internal/omega -count=1` -> PASS
- `go test ./internal/agent -run '^$' -count=1` -> PASS / compile closure
- live Gabriel harness hashes before and after -> byte-identical
- final marker: `CRUSH004_FULL_GO_VALIDATION_PASS`

The four invariant live hashes remained:

- `harness_crush_knopf.sh` = `95a9311a4f47457b3c5e100fe9bd8d62253711eb889386e521bc68a3ddf7fce3`
- `harness_crush_knopf.py` = `db05347f908c891e526bdb47d6497e24aa1defc94b824f502ecd579ab73dbd61`
- `harness_crush.py` = `59a3a043c0b4b687e998837027f86a8fd982ff4038ca58b8834f3243ae2b0613`
- `frankenstein-repo/CRUSH.md` = `1980f471ff088d3fea923b66f69eb1e0e8d837f546c86a84740111bbbeddbf99`

## Preserved negative / infrastructure evidence

Do not repaint these earlier failures:

- First VPS validator: exact public donor checkout succeeded; private HTTPS clone lacked credential forwarding.
- Second VPS validator: authenticated carrier fetched exact CRUSH004 head and patches applied; build stopped because the VPS sandbox has no `go/gofmt` executable.
- First ai-core scratch validator: exact public donor checkout succeeded; private SSH clone failed because this execution context has no SSH key.
- ai-core normal PATH had no `go` executable.
- VPS probe found no normal Go executable/common install/preexisting Go builder.

These are build-surface/toolchain findings, not CRUSH004 semantic negatives. The later isolated Go-1.27.1 validator closes the component compile boundary without rewriting this history.

## Promotion fence

Promoted now:

**CRUSH004 portable route-observation + provider-swap identity separation + persistent reentry + exact-donor Go-1.27 component compile closure.**

Not promoted now:

- Gabriel live Free-Frank/Crush installation
- production Crush binary
- external provider execution
- ChatGPT/Claude/Free-Pool adapter runtime
- whole OMEGA cognition
- whole HCU/GRID/GWT semantics
- training
- Andreas host state

## Next nonduplicate boundary

The next architectural boundary is **bridge-route adaptation without router duplication**: map existing external ChatGPT / Claude Code / Free-Pool execution paths into the same portable `OrganRoute` observation contract while preserving their current dispatch/authority surfaces and current provider hard-off constraints.
