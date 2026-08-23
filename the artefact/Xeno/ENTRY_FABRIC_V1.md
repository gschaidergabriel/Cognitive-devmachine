# Xeno Entry Fabric v1

Status: **SOURCE CANDIDATE / EXACT-BLOB BOUNDED COMPONENT EVIDENCE**
Date: 2026-08-23

## Purpose

`entry_fabric.py` is the current-facing typed ingress primitive for Xeno. It binds new/untrusted data to causal identity, generation, producer identity, modality, timestamps, permissions/capability scope, resource budget and payload reference **before cognition**.

It deliberately does not own canonical durable state, truth, replay history or real effects.

Canonical durable admission/replay evidence remains in the current canonical Xeno state substrate (MiniUnifiedDB/UnifiedDB lineage). Real effects remain behind EffectGate/EffectJournal.

## Schemas

- `XENO_INGRESS_PACKET/v1`
- `XENO_ENTRY_ADMISSION/v1`

Ingress classes:

- `HUMAN_PROMPT`
- `EXTERNAL_EVENT`
- `TOOL_OUTCOME`
- `SENSOR_STREAM`
- `DATABASE_CHANGE`
- `SYSTEM_EVENT`

## Admission path

```text
raw/new event
   |
   v
IngressRequest strict validation
   |
   +-- source + event_id -> deterministic event_key
   +-- causal_id + generation + event/payload identity -> ingress_id
   +-- reject stale generation
   +-- reject event_key already present in canonical replay set
   |
   v
XenoIngressPacket
   |
   v
EntryAdmissionReceipt
   |
   v
canonical state store persists/attests receipt
   |
   v
validate_for_dispatch(... live current_generation ...)
   |
   v
XPU / GRID10 / other admitted Xeno mode
```

The module receives canonical replay/receipt state from its caller. It never creates a second durable replay ledger.

## Dispatch-generation fence

Generation is checked twice:

1. at ingress admission;
2. immediately before cognition/dispatch.

This closes the admission -> queue -> entity-generation-rollover gap. A packet admitted at generation `g` cannot receive dispatch credit after the live generation becomes `g+1`, even when its original admission receipt remains internally self-consistent.

## Producer replay identity

The replay key is derived from `source + event_id`. This follows the useful event-identity principle that producer scope plus producer event id identifies a distinct event, while Xeno additionally binds its own `causal_id`, generation and payload identity into the ingress packet id.

This is not a claim of full CloudEvents conformance. Xeno retains its own schema and authority semantics.

## Trace propagation

`traceparent` is optional metadata only. It can preserve distributed-trace correlation without replacing Xeno `causal_id`, `generation` or canonical state identity.

## Authority invariants

- input semantics cannot mint truth;
- packet existence cannot mint canonical state;
- admission receipt existence cannot itself prove durable admission;
- dispatch requires the exact canonical receipt digest supplied from canonical state;
- stale generation fails closed at admission and dispatch;
- duplicate producer event identity fails closed;
- Entry Fabric exposes no direct canonical write and no real-effect primitive;
- EffectGate/EffectJournal remain the only real-effect authority.

## Cross-mode reuse

The same ingress packet can feed:

- `XENO_GRID10`;
- `XENO_COGSIM10`;
- `XENO_WM_TEST`;
- `XENO_NESTED_SIM`;
- `XENO_SCALEOUT`.

Mode selection changes topology/resource use after ingress; it does not change event identity or authority.

## Exact bounded evidence

Bound branch at evidence time:

`gpt56sol/go-xeno-entry-fabric-v1-20260823-2323`

Base main:

`2178d9b0a062636231ff0e3c533417c2268a7a96`

Exact Git blobs:

- `the artefact/Xeno/entry_fabric.py`: `110a9137b76fb85cd589cefbdaae729657838e13`
- `the artefact/Xeno/tests/test_entry_fabric.py`: `7f6ed314c26e2ea4a4f227463e39287c3eb140cb`

Observed isolated component checks on those exact blobs:

- Python `3.13.5`;
- Linux `6.18.35` x86_64;
- `py_compile`: PASS;
- focused unit regressions: **9/9 PASS**.

Evidence class:

`EXACT_BLOB_BOUNDED_COMPONENT_MECHANISM`

This grants zero GRID10 scheduler, bundled model, XCU inference, J-Space, world-model, EntityOS or whole-product runtime credit.

## One GO unusual discriminator

Hypothesis: ingress-time generation binding alone is sufficient.

Counterhypothesis: a valid packet can remain queued across an entity generation rollover and later be consumed stale.

Intervention: admit a generation-7 packet and receipt, roll the live generation to 8 without mutating the packet/receipt, then compare an admission-only check with `validate_for_dispatch`.

Observed:

- admission-only self-consistency remains true;
- dispatch-time live-generation validation rejects the packet fail-closed.

Outcome: **counterhypothesis retained; second generation fence required**.

All remaining focused cases are deterministic regressions, not additional unusual experiments.

## Next integration gate

Wire one canonical adapter that:

1. reads the live generation and replay set from the current canonical state substrate;
2. calls `admit_ingress`;
3. durably persists the exact admission receipt in that same canonical authority;
4. passes the persisted receipt digest to XPU/GRID10;
5. calls `validate_for_dispatch` immediately before each cognition dispatch;
6. exercises restart/replay/generation rollover in authorized isolated exact-source execution.

Do not create a parallel Entry DB, replay ledger, effect path or mode-specific ingress schema.
