# CLAYCODE RESEARCH RUN — CC7 Scoped Freshness / Derived Effects / Transition Closure

**run_id:** `claycode-20260808T0549p0700-chatgpt-secondary`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**parent ClayCode run:** `claycode-20260808T0529p0700-chatgpt-secondary` (CC6)  
**intervening research:** Clay G6 + GWT causal-closure work  
**boundary:** local and Judge0 measurements are synthetic/runtime proxies; no live-FRANK scientific state is promoted. The planned Qwen3-4B live reader test reached the provider but was blocked by exhausted Hugging Face inference credit.

## Executive synthesis

CC6 separated ClayCode into semantic IR, reader projections and an external authority gateway. G6 then bound state-aware decoding Γ to a basis root/epoch. CC7 identifies a remaining overconstraint:

> **A whole-state root is excellent snapshot identity and provenance, but is generally too coarse to be the sole commit-freshness predicate when unrelated state changes concurrently.**

The refined OPEN candidate is **`CC-RC1.2 Transition Closure Capsule (TCC)`**:

`canonical semantic operation`
`-> trusted operation-semantics compiler derives dependency/effect closure`
`-> reader/model projection + Γ(basis snapshot)`
`-> proposal carries basis identity, not self-declared authority`
`-> gateway validates relevant object versions + invariant epochs + capability handles + nonce/revocation/expiry`
`-> conservative escalation when effects/dependencies are dynamic or unknown`
`-> commit/effect receipt -> outcome/re-entry`

The crucial trust change is:

**model proposes operation + arguments; trusted semantics derive what that operation reads, writes, can affect and which authority it requires.**

The model is not trusted to describe its own safety-relevant effect footprint.

## What changed since CC6/G6

### 1. Split snapshot identity from commit freshness

Retain a global semantic `state_root` as the immutable identity of the snapshot from which a proposal was generated. If the current root differs, do **not** automatically execute and do **not** automatically discard. Instead, revalidate the trusted operation closure against current state.

A proposed commit can survive unrelated global churn only if:
- its operation semantics/version is still the same;
- all derived read dependencies that matter remain compatible/current;
- derived write targets meet the required compare/version rules;
- applicable invariant epochs or merge proofs remain valid;
- capability handles are current, scoped and unrevoked;
- nonce/expiry/replay rules pass;
- rollback/effect-receipt requirements remain satisfiable.

If the dependency closure is unknown or incomplete, validation escalates to a broader root/lock/coordination boundary. Global-root mismatch is never silently ignored.

### 2. Effects are derived, not self-asserted

The trusted operation registry/compiler should deterministically derive at minimum:

`read_set`
`write_set`
`invariant_set`
`effect_class`
`required_caps`
`op_semantics_version/hash`

A model-produced `read_set`, `write_set`, `effect=PURE`, or `requires=[]` may be useful as a prediction/explanation, but never as the authoritative gate input.

### 3. Semantic identity is not projection identity

CC7 strengthens CC6's projection separation. A semantic ClayCode object must not be identified by incidental JSON/text/protobuf bytes. Protocol Buffers explicitly documents that deterministic serialization is not canonical and that schema/unknown-field evolution makes serialized-byte hashes fragile. RFC 8949 shows that deterministic CBOR profiles are possible, but deterministic wire encoding remains a protocol choice rather than the definition of semantic meaning.

Therefore ClayCode should distinguish:
- `semantic_hash`: versioned canonical semantic normalization;
- `projection_hash` or `wire_hash`: optional transport/debug integrity;
- `state_root`: identity of the basis semantic state snapshot;
- object/version/invariant witnesses used for commit freshness.

### 4. Dynamic dialects are viable only with pinned semantics

MLIR provides strong implementation evidence that semantic IRs can be extensible while transformations operate through declared interfaces and compact bytecode remains a separate concern. ClayCode can adopt the same structural lesson: dynamic operations are acceptable only when their semantic identity, verifier, effect/dependency derivation and migration behavior are explicit and versioned.

## Proposed CC-RC1.2 Transition Closure Capsule

Illustrative semantic fields, not a frozen syntax:

```text
TCC {
  proposal_id
  basis_state_root
  op_id
  op_semantics_hash
  args
  causal_episode_ref?
  provenance_ref

  // derived by trusted semantics, not accepted from model as authority
  derived_read_set[]
  derived_write_set[]
  invariant_set[]
  effect_class
  required_capability_types[]

  // materialized at validation time
  read_version_witnesses[]
  write_compare_witnesses[]
  invariant_epoch_witnesses[]
  capability_handles[]
  nonce
  expiry?
  rollback_contract?
}
```

The model-facing projection need not expose every field. Capability values should be opaque handles/resource references; bearer secrets should not become model tokens.

### Commit algorithm sketch

1. Parse proposal into canonical semantic operation.
2. Resolve pinned `op_id + op_semantics_hash`.
3. Derive dependency/effect/capability closure independently of model claims.
4. Verify the proposal's basis snapshot identity exists and provenance is valid.
5. If current root differs, compare only the required dependency/version/invariant closure **when it is complete and conservative**.
6. On dynamic/unknown effects, unresolved aliases, reflective access, indirect capabilities or uncertain invariants: escalate validation scope or reject.
7. Check external capability handles, revocation, scope, nonce, expiry and policy.
8. Check invariant-confluence / coordination requirement.
9. Commit atomically and issue a causal/effect receipt.
10. Feed outcome/re-entry through the existing FRANK/GWT receipt chain.

## Fusion 1 — internal evidence

CC6 already established:
- canonical semantic IR should be distinct from reader projection;
- compact separator syntax can fail on adversarial payloads;
- positional JSON can round-trip exactly in synthetic tests;
- unknown/conflict/revoked values must remain explicit;
- model output is proposal, never execution authority;
- self-hosting must preserve a deterministic trust root.

G6 then supplied the critical new observation: Γ generated from stale runtime state can still produce references invalid in current state. In its dynamic-symbol proxy, grammar-only invalidity was 63.874%, stale Γ reduced it to 11.911%, fresh Γ reached 0%, and root validation caught the stale remainder. G6 therefore correctly required root/epoch freshness — CC7 asks whether a single global root is the right **granularity** for that check.

The intervening GWT run also introduced a vector Causal Workspace Closure Certificate rather than one scalar metric. CC7 finds the same structural pattern in ClayCode validation: a vector/closure of independent evidence is more informative than one global yes/no token such as `root_equal`.

## Hypothesis generation and counterhypotheses

Sixteen falsifiable hypotheses are stored in `HYPOTHESES.md`. The strongest new pair is:

- **H-CC7-001:** whole-state root equality overrejects proposals under sparse unrelated churn.
- **H-CC7-003:** model-declared effect/dependency footprints are unsafe as authority; trusted operation semantics should derive them.

Strong counterhypotheses remain live:
- real FRANK churn may be low enough that whole-root fail-closed is simpler and cheaper;
- real operations may be too dynamic for useful conservative footprints;
- certificate/version metadata may cost more than retries;
- Qwen may prefer ordinary JSON strongly enough that a compact ClayCode projection has no end-to-end value;
- cryptographic proof carrying may be excessive outside remote distrust boundaries.

## External research — provider-gated

CC7 used the newly deployed allowlisted RAE GitHub-runner bridge. OpenAlex, arXiv, Tavily and Exa requests succeeded and produced sanitized repository results. Semantic Scholar was rate-limited in the current provider health audit. E2B lacked credentials; Judge0 was used as independent executable fallback. Hugging Face model discovery succeeded and exposed `Qwen/Qwen3-4B-Instruct-2507`; model inference then returned HTTP 402 because monthly included credits were depleted.

### Extensible semantic IRs

LLVM MLIR documentation provides direct implementation evidence for:
- dialects with explicit operations/types/attributes;
- interfaces that let analyses reason generically rather than by stringly operation cases;
- dynamic/extensible operations and types;
- dialect-specific compact bytecode independent of textual assembly.

Transfer to ClayCode: keep the semantic operation registry authoritative and make reader/wire forms replaceable.

### Serialization identity

Protocol Buffers documentation explicitly rejects treating deterministic serialization as canonical identity: schema/library changes and unknown fields can alter serialized bytes. RFC 8949 separately defines deterministic CBOR restrictions for protocols that require reproducible bytes.

Transfer to ClayCode: a deterministic wire profile is useful, but `wire_hash != semantic_hash` unless a deliberately versioned semantic normalization says otherwise.

### Typed interfaces and opaque resources

The WebAssembly Component Model's WIT defines typed contracts rather than behavior, including resource-style handles managed across component boundaries. This is a useful architecture analogue for ClayCode capability references: model-visible operands can be typed opaque handles whose actual authority remains host/gateway controlled.

### Effect systems

Current effect-system research, including *Rows and Capabilities as Modal Effects* (`arXiv:2507.10301`), shows that effect tracking and capabilities can be represented as related but separable mechanisms. This supports CC7's distinction between `effect_class` (what computation can do) and current capability authority (whether this invocation may do it).

### Proof/witness mechanisms

Current proof-carrying/attestation work shows that Merkle commitments and cryptographic certificates can make remote claims independently checkable. CC7 does **not** conclude that every local Clay transition should carry a zk proof. The more plausible use is optional proof/witness material at remote/distributed trust boundaries, audit boundaries or high-value effects, while local transitions use cheaper deterministic version/invariant checks.

## Empirical work

### EXP-CC7-SCOPED-FRESHNESS-001

Constructed 10,000-key state; 100,000 operations per churn regime; complete dependency closure.

As mean unrelated changed keys rose:
- `0.1`: global-root reject `9.502%`; scoped reject/actual conflict `0.201%`;
- `0.5`: `39.527%` vs `0.896%`;
- `1`: `63.051%` vs `1.417%`;
- `3`: `95.040%` vs `2.204%`;
- `10`: `99.994%` vs `3.011%`.

This strongly demonstrates the *possible* concurrency cost of whole-root freshness under sparse independent churn. It is constructed and does not establish FRANK's actual retry distribution.

### EXP-CC7-HIDDEN-DEP-002

Counterexperiment deliberately injected dependencies absent from the scoped closure. Missed accepted conflicts rose from `0` with complete dependencies to ~`0.892%` when hidden-dependency probability reached 25% in this workload.

**Negative result:** narrow freshness is not intrinsically safe. Its safety comes from a complete/conservative trusted dependency closure.

### EXP-CC7-DERIVED-EFFECT-003

100,000 typed-operation proxy cases; 29,929 proposals deliberately omitted one true dependency from their claimed footprint.

- trusting the proposal's own claimed footprint missed actual conflicts at rate `10.748%`;
- deriving the footprint from trusted operation semantics missed `0` in the constructed operation family.

### EXP-CC7-DERIVED-EFFECT-JUDGE0-004

Independent remote execution through Judge0, Python 3.8.1, 50,000 cases:

- trusted claimed footprint miss rate: `7.398%`;
- derived footprint misses: `0`.

The absolute miss rate changes with the workload, as expected. The safety direction replicated independently.

### EXP-CC7-MERKLE-COST-005

Pure-Python SHA-256 tree, 16,384 leaves, depth 14:
- full tree root reconstruction mean: ~`7.458 ms`;
- verify eight inclusion paths mean: ~`0.0577 ms`;
- proxy ratio: ~`129x`.

This demonstrates only that targeted witnesses *can* be much cheaper than full reconstruction. It does not establish freshness or justify Merkle proofs as the default local validation mechanism.

### EXP-CC7-QWEN4B-READER-006

Prepared a pinned four-arm comparison on exactly the same 18 semantic state records and ten queries:
1. verbose object JSON;
2. positional JSON;
3. readable ClayCode compact projection;
4. aggressive numeric projection.

Hugging Face model discovery returned `Qwen/Qwen3-4B-Instruct-2507`, but the first live inference request returned `HTTP 402: monthly included credits depleted`. Subsequent same-provider arms therefore cannot yield a valid reader comparison in this run.

**Result:** `BLOCKED_QUOTA`; no Qwen accuracy/token claim.

## Negative results / revisions

- **N-CC7-001:** global-root equality should not automatically be interpreted as the uniquely correct freshness granularity; it can massively overreject unrelated churn in sparse constructed workloads.
- **N-CC7-002:** dependency-scoped freshness without complete/conservative dependency knowledge is unsafe.
- **N-CC7-003:** model-declared read/write/effect footprints cannot be treated as authority; local and independent Judge0 proxies both produced missed conflicts under omission.
- **N-CC7-004:** deterministic serialization is not automatically semantic canonicalization.
- **N-CC7-005:** compact authenticated witnesses do not by themselves prove semantic/current-state validity.
- **N-CC7-006:** a Qwen3-4B reader advantage for ClayCode remains unmeasured; the attempted live test was blocked by provider quota.
- **N-CC7-007:** cryptographic proof-carrying is not justified as a mandatory mechanism for every local transition based on current evidence.

## Architecture delta

### CC-RC1.2 — Transition Closure Capsule

The new candidate refines, rather than replaces, CC-RC1.1:

**CC-RC1.1 retained:** causal episode identity, provenance, model-output-is-not-authority, capability/commit gateway, receipts, rollback discipline.

**CC-RC1.2 added:**
- separate basis snapshot identity from scoped current-freshness evidence;
- trusted derived dependency/effect/capability closure;
- object/version and invariant-epoch witnesses;
- semantic-operation version/hash;
- conservative escalation for dynamic/unknown closure;
- semantic hash separated from projection/wire hash;
- optional targeted/Merkle/cryptographic witnesses only where trust/cost justifies them.

### Proposed trust partition

**Model may choose/propose:**
- op id from exposed grammar;
- arguments/references allowed by Γ;
- goal/reason/candidate relation;
- optional prediction of affected state.

**Trusted semantic runtime derives:**
- operation semantics identity/version;
- read/write closure;
- invariant classes;
- effect class;
- capability type requirements;
- canonical semantic normalization.

**External gateway decides:**
- current freshness;
- capability validity/scope/revocation;
- nonce/expiry/replay;
- coordination/invariant-confluence;
- rollback/effect policy;
- commit and effect receipt.

This keeps self-representation compatible with a strict authority boundary.

## Highest-information next experiments

1. **Real op-registry footprint experiment:** implement 10–20 representative ClayCode operations and derive effects/dependencies from their semantics; compare against dynamic access instrumentation and mutation tests.
2. **Real/twin freshness benchmark:** whole-root fail-closed vs object/version scoped vs invariant-aware scoped validation under measured FRANK churn, proposal delay, crashes and replay.
3. **Pinned Qwen3-4B reader factorial:** rerun the four prepared arms when an inference-capable target is available; measure exact task success, input/output tokens, repairs, latency and malformed-reference rate. Do not substitute a larger model for the target result.
4. **Semantic identity migration test:** one semantic object across verbose JSON, positional JSON, deterministic CBOR/custom bytecode, reordered fields, old/new readers and unknown extensions; semantic identity must remain stable where semantics are unchanged.
5. **Dynamic-op adversarial test:** reflection, aliases, plugin-defined ops and indirect capability calls must either derive a conservative closure or escalate.
6. **Optional witness crossover:** compare object versions/invariant epochs, Merkle witnesses and stronger cryptographic certificates only at trust boundaries where auditability outweighs proof cost.

## Promotion decision

**Canonical promotion: NOT PERFORMED.**

CC7 produces a strong architecture delta and independently replicated proxy evidence for derived effects, but the decisive live substrate tests remain open. `CC-RC1.2 Transition Closure Capsule` is stored as an **OPEN research candidate**, not current canonical truth. Canonical RAE revision remains r2 unless a separate validated promotion changes it.
