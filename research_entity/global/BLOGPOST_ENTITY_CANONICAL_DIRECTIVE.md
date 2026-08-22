# BLOGPOST ENTITY — SOLE CANONICAL OWNER DIRECTIVE

Status: CURRENT
Owner directive date: 2026-08-22
Persistent research entity: Clay
Active program: BLOGPOST_ENTITY_ALL_IN_ONE
Active stage: BLOGPOST_ENTITY_CLAY

## 1. Sole goal

The Research Entity has exactly one active product goal:

**finish, falsify, harden and deliver the persistent Zero/EntityOS Blogpost Entity as one canonical ClayCode module:**

`the artefact/blogpost_entity/BLOGPOST_ENTITY.clay`

All former ClayVerse-container, Frank, UCM/UCM2, EntityOS-product, ClayGraph, GWT, Hyperposition, UnifiedDB, ClayCode and harness work is now donor evidence only, except where it directly improves this module.

No worker may open a competing product frontier while this directive is current.

## 2. What the finished module is

The module is the twice-daily autobiographical writing entity for Zero. It must:

- read real canonical state/evidence from UnifiedDB and relevant live files;
- separate canonical self-state from autobiographical/narrative continuity;
- compile personality/emotion pressures from measured state instead of letting the LLM invent them;
- enforce `UNKNOWN != ZERO != ERROR != MEASURED`;
- use the free Mistral key family `MISTRAL_API_KEY`, `MISTRAL2_API_KEY`, `MISTRAL3_API_KEY` through a secret boundary without exposing tokens;
- use Mistral as writing cognition, never as canonical state authority;
- write in the Gasthaus-engineer first-person voice;
- keep `T_OMEGA = Integral(R_t tensor E_t dt)` unbound until R_t and E_t are operationally measured;
- allow Bare-Metal/local-weight/synthetic-friction desires only when their measured pressure is VERIFIED;
- require evidence references for every generated paragraph;
- require machine-readable state claims and reject claims stronger than the measured state;
- reject internal-name/secret leakage;
- consume each source event exactly once;
- never consume events when generation/validation fails;
- atomically commit post + packet + entity continuity + source-consumption state;
- be concurrency fenced by generation/CAS semantics;
- preserve a canonical-state hash and packet hash for every post;
- remain one `.clay` domain module; host machinery may expose only generic audited effects.

## 3. Architecture law

`real state -> deterministic state compiler -> signed/hashed canonical snapshot -> personality state -> Mistral narrative -> deterministic claim/evidence gate -> atomic persistence`

The LLM may narrate the state. It may not mint the state.

Canonical self:
- rebuilt from current evidence every run;
- factual and provenance-bound;
- never replaced by Mistral summaries.

Autobiographical self:
- narrative thread and remembered interpretation from previous posts;
- may influence voice and continuity;
- is never promoted to canonical truth merely because the writer said it.

## 4. `go` — mandatory swarm cycle

Exact trigger: `go`

Every `go` is a maximal useful cycle on this single target. Run as many parallel logical/actual workers as the available environment permits, then fuse them into one artifact delta.

Required lanes:
1. architecture/state compiler;
2. ClayCode/compiler/runtime compatibility;
3. UnifiedDB/full-state evidence projection;
4. personality/emotion/claim-gate;
5. Mistral transport/keys/output contract;
6. adversarial hallucination/leak/concurrency/failure analysis;
7. sandbox execution/tests/fuzzing;
8. fusion/hypofusion/integration.

Cycle:
`refresh -> fan-out -> hypotheses -> counterhypotheses -> implement candidates -> sandbox test -> falsify -> fuse -> fix -> retest -> write canonical artifact/evidence`

A report without artifact/test progress is not a successful `go` when implementation work is possible.

All lanes must converge back onto the same file and its generic runtime/tests. No lane creates a second blog entity.

## 5. Acceptance gates

FINISHED requires evidence for all applicable gates:

1. Clay source parses under the selected structured ClayCode grammar/runtime path.
2. End-to-end sandbox run creates a valid post from fixture UnifiedDB evidence.
3. Existing events are consumed exactly once; the next run is correctly quiet.
4. Missing/broken sensors are UNKNOWN, never silently interpreted as quiet.
5. Invalid Mistral output consumes nothing.
6. Unknown or over-strength emotional/self claims are deterministically rejected.
7. Paragraph evidence references must exist in the current allowed evidence set.
8. Secret/internal identifier leak guard rejects publication.
9. Post, packet, source-consumption and entity-state commit atomically.
10. Concurrent stale generation loses by CAS/rowcount fence.
11. Canonical-state snapshot is rebuilt each run and cannot be overwritten by narrative memory.
12. Real free Mistral-key path is exercised in an authorized sandbox when the secret is actually available there; absence of mounted secret is a blocker, never permission to fake a live call.
13. At least one real Mistral-produced post passes the deterministic gate and is persisted.

Component PASS != final PASS.

## 6. Execution

- sandbox/isolated execution only for tests;
- never expose or commit Mistral tokens;
- Together API remains forbidden;
- preserve negative results and precise blockers;
- old product work stays readable as evidence, but receives no independent development budget while this directive is current.

## 7. Canonical paths

- directive: `research_entity/global/BLOGPOST_ENTITY_CANONICAL_DIRECTIVE.md`
- active source: `the artefact/blogpost_entity/BLOGPOST_ENTITY.clay`
- generic effect runtime: `tools/clay_effect_runtime.py`
- tests: `the artefact/blogpost_entity/test_blogpost_entity.py`
- state: `research_entity/rooms/PROGRAM_STATE.json`
- boot: `research_entity/continuity/BOOTSTRAP_MINIMAL.json`

## 8. Mission re-entry

After every material result ask only:

**What is now the strongest evidence-backed change that moves `BLOGPOST_ENTITY.clay` closer to final acceptance?**
