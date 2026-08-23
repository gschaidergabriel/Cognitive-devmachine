# Xeno Entry Fabric v1 — causal admission and route binding

Status: **SOURCE CANDIDATE / NO RUNTIME CREDIT**  
Program: **EntityOS + HCU/XCU**  
Stage: **XENO_COMPUTATIONAL_UNIT_BOOTSTRAP**

## Purpose

`XENO_INGRESS_PACKET/v1` is the first executable current-facing Entry Fabric primitive. It deterministically binds new data before cognition without becoming a truth or effect authority.

The key design correction is to separate two identities:

1. `event_sha256` — replay-stable identity of the causal event itself;
2. `admission_sha256` — identity of the concrete admitted ingress instance, including transport arrival, permissions, capability scope and resource budget.

This prevents a mutable `payload_ref` or an HCU routing result from acting as event identity.

## Required ingress fields

```text
schema = XENO_INGRESS_PACKET/v1
ingress_id
causal_id
entity_generation
source
provenance
modality
observed_at
received_at
permissions[]
capability_scope[]
resource_budget{}
payload_ref
payload_sha256
```

`payload_sha256` is mandatory because `payload_ref` can be mutable or rebound. A reference without a content digest is insufficient for causal identity.

## Identity split

`event_sha256` commits to:

```text
schema
causal_id
entity_generation
source
modality
observed_at
payload_sha256
provenance
```

It deliberately excludes `ingress_id`, `received_at`, `payload_ref`, permissions and budget so a transport replay of the same causal event can retain one event identity.

`admission_sha256` commits to:

```text
event_sha256
ingress_id
received_at
payload_ref
permissions
capability_scope
resource_budget
```

Thus replay identity and admission-instance identity are both explicit instead of being conflated.

## HCU / XPU route binding

The reusable route-decision identity is:

```text
H(
  entry event identity,
  route policy identity,
  canonical requested engine identity,
  canonical resolved engine identity,
  resolved engine class,
  route result
)
```

The reference helper is `route_decision_sha256()` in `entry_fabric_v1.py`.

A router MUST positively resolve an internal cognition engine through an admitted registry/capability class before calling the helper. A finite blacklist is not authority. Unknown or unresolved engine identity fails closed.

For the current draft HCU router in PR #1263, the integration target is:

```text
Xeno Entry Fabric
 -> event_sha256
 -> HCU_REACTIVE_EVENT/v1 carries/binds that event identity
 -> positive internal engine resolution
 -> route_decision_sha256(event, policy, engine, route_result)
 -> downstream inference receipt echoes event + route + engine identity
```

Two materially different events that happen to select the same HCU lanes/projection must not alias. Two distinct admitted engines must not alias. An exact replay of the same event under the same route policy and canonical engine must reproduce the same route decision digest.

## Hypothesis / counterhypothesis

**H1 — split event/admission identity is the reusable primitive.** It gives Entry, HCU routing, replay, XPU scheduling and future interconnect packets one causal anchor without tying event identity to transport timing.

**H0 — one hash over the final routing payload is sufficient.** This is cheaper but fails when different events cross the same thresholds and produce the same route result, and it cannot distinguish causal event replay from a new ingress instance.

## Cheapest discriminators

The source regressions define the minimum falsifiers:

- same packet -> identical event/admission identities;
- same causal event, new ingress arrival -> same event identity but different admission identity;
- changed payload bytes digest -> changed event identity;
- stale generation -> fail closed;
- same route result + different event -> different route digest;
- same event/result + different canonical engine -> different route digest;
- exact same event/policy/engine/result replay -> identical route digest.

These tests are present as source obligations only until executed on an authorized isolated sandbox.

## Authority boundary

- canonical durable state/evidence remains outside this module;
- Entry Fabric admission does not make payload semantics true;
- HCU/XCU/J-Space results remain candidate/measurement state;
- EffectGate/EffectJournal remain the only real/state-changing effect boundary;
- no provider, model or route score may mint truth or capability authority.

## Cross-mode reuse

The same event/admission split is intended for `GRID10`, `COGSIM10`, `WM_TEST`, `NESTED_SIM` and `SCALEOUT`. Mode changes topology and budget, not causal identity semantics.

## Evidence boundary

No test execution, HCU runtime, model inference, package rebuild, provider independence or EntityOS runtime PASS is claimed by this source delta. Exact executable credit requires an actually-started authorized isolated run bound to exact source identity.
