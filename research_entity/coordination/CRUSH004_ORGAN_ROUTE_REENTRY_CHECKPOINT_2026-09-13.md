# CRUSH004 — ORGAN ROUTE / REENTRY CHECKPOINT — 2026-09-13

Status: **BOUNDED SOURCE + EXACT-DONOR STRUCTURAL PASS; FULL GO-1.27 AGENT COMPILE RECEIPT PENDING**

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

CRUSH004 adds a portable `omega.OrganRoute` observation:

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

## New executable discriminators

Added tests prove:

1. Route digest is deterministic after whitespace normalization.
2. Provider/model swap changes route evidence.
3. Empty route produces no artificial route identity.
4. A provider/model swap combined with a process/runtime-object restart preserves the same `EntityID`.
5. The second turn reenters from the first turn (`PredecessorTurnID`) and advances revision.
6. Route metadata does not leak into model system context by itself.
7. Both route digests persist in causal turn history.

## Exact-donor evidence

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

## Preserved negative / infrastructure evidence

Do not repaint these failures as product negatives or passes:

- First VPS validator: exact public donor checkout succeeded; private HTTPS clone lacked credential forwarding.
- Second VPS validator: authenticated carrier fetched exact CRUSH004 head and patches applied; build stopped because the VPS sandbox has no `go/gofmt` executable.
- First ai-core scratch validator: exact public donor checkout succeeded; private SSH clone failed because this execution context has no SSH key.
- ai-core toolchain probe: host PATH has no `go` executable.
- VPS toolchain probe: no Go executable/common install/preexisting Go builder was found.

These are build-surface/toolchain findings, not CRUSH004 semantic negatives.

## Full compile closure command

A final isolated ai-core validation was queued under:

`crush004-full-go-validate-20260913T0740Z`

Its contract is deliberately non-installing:

- hash live Gabriel harness before;
- resolve official Go 1.27.1 linux-amd64 artifact + SHA-256 from `go.dev/dl`;
- download/extract only under the CRUSH validation cache;
- keep `GOCACHE` and `GOMODCACHE` inside scratch;
- checkout exact donor `d333e043...`;
- fetch exact CRUSH branch through existing `gh` auth;
- apply both patches;
- `gofmt`, `git diff --check`;
- `go test ./internal/omega -count=1`;
- `go test ./internal/agent -run '^$' -count=1`;
- re-hash live harness and require byte-identical pre/post hashes.

At checkpoint creation, no receipt for that command existed yet. Therefore **full exact-donor Go-1.27 compile credit remains pending** and must not be inferred from the structural PASS.

## Promotion fence

Promoted now:

**CRUSH004 portable route-observation + identity-separation design and exact-donor structural integration.**

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

First consume the exact `crush004-full-go-validate-20260913T0740Z` receipt if it exists. Only on a valid PASS may CRUSH004 gain full exact-donor component compile closure.

After that, the next architectural boundary is **bridge-route adaptation without router duplication**: map existing external ChatGPT / Claude Code / Free-Pool execution paths into the same portable `OrganRoute` observation contract while preserving their current dispatch/authority surfaces.
