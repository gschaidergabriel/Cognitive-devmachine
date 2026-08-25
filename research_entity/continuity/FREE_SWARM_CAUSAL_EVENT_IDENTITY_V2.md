# FREE SWARM CAUSAL EVENT IDENTITY v2

Status: SOURCE-LEVEL SUCCESSOR PRIMITIVE; NOT YET ACTIVE BACKFILL AUTHORITY
Authority epoch observed at design time: supervisor 8.78 / FREE_ONLY
Product: EntityOS
Architecture: HCU

## Problem

The historical Free-Swarm backfill currently derives `source_event_id` from a payload that includes the concrete `source_path` plus line identity and worker fields. The GO878 cumulative-line repair addresses one source of replay drift (incremental resumes resetting a local line counter), but an absolute artifact-root move can still change the preimage for the same physical worker event.

That is incompatible with the current causal-identity law: replay-stable causal event identity must remain distinct from a concrete transport/admission/location identity.

A silent replacement of the existing `source_event_id` preimage is forbidden because current rows, chunks, candidate provenance and receipts already bind the v1 identifier.

## Decision

Introduce an additive identity layer:

- retain existing `source_event_id` exactly as historical/compatibility admission identity;
- introduce `causal_event_id` under schema `CLAY_FREE_SWARM_CAUSAL_EVENT_IDENTITY/v2`;
- derive v2 from a logical path relative to the configured artifact root, absolute line identity, stable worker identity fields, producer repo head and text digest;
- never include the concrete artifact-root prefix in the v2 causal preimage;
- fail closed when a source cannot be relativized beneath the declared artifact root;
- never rewrite legacy identifiers in place merely because v2 can be computed.

The initial reusable implementation is `tools/free_swarm_causal_identity_v2.py`.

## Integration law

Active backfill integration is intentionally deferred until the existing GO878 line-identity predecessor and replay-idempotent source-support successor are executable on an admitted zero-cost runtime surface.

When integrated, use additive schema migration rather than reinterpretation:

1. add nullable `causal_event_id` / logical-source identity fields to the relevant historical provenance surfaces;
2. preserve `source_event_id` values and all existing append-only receipts;
3. populate v2 only when the artifact root, stored source path, absolute line and worker payload are sufficient to reproduce the identity deterministically;
4. mark unresolved rows explicitly instead of fabricating an ID;
5. keep `source_count` on legacy semantics while provenance coverage is mixed;
6. only after complete candidate-linked v2 coverage, change scheduling support to `COUNT(DISTINCT causal_event_id)` through an explicit successor schema/test gate;
7. do not change chunk IDs or other v1 hashes silently. If causal chunk identity is needed, add a separate successor field.

## Acceptance discriminators

A future active integration must prove at exact source identity:

1. **root relocation:** copying the same artifact tree under a different absolute root produces the same v2 causal IDs;
2. **incremental equivalence:** one-shot and resumed scans produce the same absolute-line + v2 causal identities;
3. **admission separation:** legacy/concrete admission IDs may differ while the v2 causal ID remains equal for the same relocated event;
4. **distinct-run separation:** different logical run paths do not collapse merely because text/model/worker fields match;
5. **support idempotence:** repeated observation/chunk/extractor links for one v2 causal event add zero scheduling support after first admission;
6. **mixed migration fail-closed:** candidates with incomplete v2 provenance cannot receive v2-derived support credit;
7. **second saturation pass:** no new causal IDs, candidate support or accepted dataset tokens are created by pure replay.

## Counterhypothesis / bounded claim

Relative-path identity fixes artifact-root relocation, not arbitrary re-homing of the same worker row under a different logical run directory. The stronger future discriminator is to bind v3, if needed, to an immutable producer run identity from the run manifest or worker receipt rather than path ancestry. Until such an immutable run ID is present and historically recoverable, v2 must not be described as path-independent in the general case.

## Evidence boundary

The v2 helper has deterministic source-level unit coverage for root relocation, logical-run separation, line separation and fail-closed invalid inputs. This is not historical-backfill runtime credit, whole EntityOS/HCU credit, J-Space/model credit or training credit.

No unusual experiment, paid provider call, Together call or external model intervention is authorized or implied by this specification.
