# CM-I/O shared frontier — canonical Bytes transport across OP_HOSTCALL

Date: 2026-08-17
Program: CLAYVERSE_CLAY_MACHINE_ONLY / CLAY_MACHINE
Product boundary: one executable `EntityOS`
Trigger context: `go`
Affected workstreams: CM-NET, CM-DATA, CM-VIS, CM-AUDIO; adjacent CM-TERM
Execution classification: SOURCE-INSPECTION / ARCHITECTURE-ADJUDICATION / TEST-OBLIGATION DELTA ONLY. No new unusual experiment is introduced or consumed by this update. The user-triggered `go` experiment slot was already consumed by `ATTESTED_SNAPSHOT_CONTENT_TAMPER_FAIL_CLOSED` on exact product head `92b629566452d8f45fd208fba943b823ddd37e8c`; every Bytes discriminator below is ordinary regression/discrimination only.

## Observed anchors

Product `main@6012d2cf4125e65d3a0c2df8d3b37119ae4f7b47` already contains a canonical CLAYVM/2 value surface with `Bytes` function parameters/returns and fail-closed owned-Bytes admission. `ExecutableIR` lowering also admits `Int`/`Bytes` function locals/parameters.

Fresh inspection of active EntityOS draft PR #787 at `ef5bed69c534b79c1a33e692dcf488408b7f01b3` confirms the remaining boundary asymmetry:

- `ClayValue`/CLAYVM/2 can represent owned immutable `Bytes` inside the VM;
- `ClayHost._calls` is still typed as `Callable[[list[int]], int]`;
- `ClayHost.invoke` still receives `list[int]` and returns `int`;
- runtime `OP_HOSTCALL` still rejects every non-`int` argument before invoking the host;
- `claymachine/executable_ir_adapter.py` has an exact hostcall signature table, but the serialized `OP_HOSTCALL` carries only `call_id` and argument count, not the expected Clay argument/result types;
- the only active adapter contract observed in #787 is the existing process request-id `Int -> Int` contract.

Therefore `Bytes` can cross Clay functions but still cannot cross the canonical VM -> host capability boundary. This remains a shared prerequisite for real CM-NET byte I/O, external CM-DATA ingress/egress, visual/video payload transport and audio payload transport.

Historical/draft PRs #740/#741/#744 contain bounded String/Bytes/hostcall evidence but are stale, broad, or explicitly leave general Bytes hostcall transport open. They are evidence inputs only; do not merge them wholesale or revive parallel semantic paths.

## Architecture candidates

### A. Generic `ClayValue` widening without runtime signature enforcement — REJECT

Change only `ClayHost.invoke`/`OP_HOSTCALL` from `int` to `ClayValue` and allow `Bytes` through.

Why it is insufficient:
- lowering knows an exact signature, but the runtime instruction does not carry it;
- a host implementation could return `Bytes` for a contract declared `Int -> Int` (or the reverse) and the VM would have no call-specific type authority with which to reject it;
- relying on each host implementation to self-police recreates backend-local semantics and weakens fail-closed behavior.

Outcome: **REJECT** as canonical solution. Generic widening is allowed only together with a single call-contract authority enforced by the VM.

### B. Shared canonical hostcall ABI registry keyed by `call_id` — RETAIN / preferred smallest candidate

Create one neutral, versioned machine-ABI contract registry containing, for each admitted hostcall:

- stable `call_id`;
- canonical signature identity/name;
- required capability/effect identity;
- exact ordered Clay parameter types;
- exact Clay return type.

Both `executable_ir_adapter.py` and `clayvm.py` import this same registry. The adapter uses it to admit/lower TypedIR hostcalls; the VM uses the same record to validate runtime argument and host-return values before/after invocation. Host implementations receive only values already admitted by that contract and cannot define the Clay type signature themselves.

Why this is currently preferred:
- one signature truth instead of duplicated compiler/VM tables;
- existing serialized `call_id` is sufficient, so no immediate CLAYVM format bump is required;
- legacy `Int -> Int` hostcalls can remain bytecode-compatible;
- exact `Bytes` snapshot/copy semantics can reuse existing CLAYVM/2 normalization;
- capability identity remains explicit and separate from payload bytes.

Authority constraint:
- this registry is a neutral canonical machine ABI artifact, not a host/backend convenience table;
- source/type/effect semantics remain upstream authority; the registry may encode only already-admitted contracts and must fail closed if lowering/runtime identity disagrees.

### C. Serialize full hostcall type/signature identity in bytecode — DEFER as stronger fallback

Extend the VM format so every hostcall instruction/module carries an exact signature identity or parameter/result type vector.

Advantages:
- self-describing serialized artifact;
- runtime validation need not trust an external `call_id -> contract` mapping alone.

Costs/risks:
- likely CLAYVM format/version migration;
- larger compatibility and artifact-reproducibility surface;
- unnecessary churn if a versioned canonical registry keyed by stable `call_id` proves sufficient.

Promotion trigger: revisit only if candidate B cannot preserve exact contract identity across serialization/versioning, introduces cyclic authority, or permits adapter/VM disagreement.

### D. First-class Buffer/lease resource — RETAIN for later high-bandwidth path

Introduce typed Buffer/BufferHandle ownership, lifetime, lease/epoch, mutability and backpressure semantics before large streaming paths.

This is structurally better for low-copy CM-DATA/VIS/AUDIO, but it is too large to block the first canonical owned-Bytes crossing. Use measured copy/latency/pressure evidence after scalar Bytes transport exists to decide where Buffer/lease becomes mandatory.

### E. Hidden integer handle registry — REJECT unless promoted to an explicit typed resource

An opaque backend dictionary keyed by arbitrary `Int` would move byte ownership/lifetime semantics outside Clay. It is not an acceptable default workaround. Integer handles become admissible only if the handle itself is an explicit typed Clay resource with canonical ownership/lifetime/provenance rules.

## Strongest counterhypotheses against candidate B

1. **Duplicate-authority counterhypothesis:** a shared registry may silently become a second semantic authority next to TypedIR. Falsifier: construct a source/TypedIR signature that disagrees with the registry; admission must fail before VM execution and no host adapter may override it.
2. **Serialization-identity counterhypothesis:** `call_id` alone may be insufficient across ABI evolution. Falsifier: change/rebind a contract under the same ID in a compatibility fixture; the system must reject incompatible ABI identity rather than reinterpret old bytecode.
3. **Runtime-return counterhypothesis:** the VM may still trust host return type. Falsifier: registered `Int -> Int` host returns `Bytes`; VM must trap at the canonical hostcall boundary before the value can enter Clay state/caller frames.
4. **Mutable-alias counterhypothesis:** bytes-like host input/output may alias mutable producer memory. Falsifier: mutate a producer-owned `bytearray`/view after boundary admission; VM-visible owned `Bytes` must remain unchanged, or the input must be rejected if the ownership contract does not admit it.
5. **Legacy-regression counterhypothesis:** widening the generic boundary may perturb existing `Int -> Int` process/uname behavior or CLAYVM/1 compatibility. Falsifier: exact legacy vectors and serialized fixtures must remain unchanged unless an explicit versioned migration says otherwise.

## First Bytes contract: semantic-admission rule

The earlier transport-only proposal `test.bytes.echo.v0::(Bytes)->Bytes` is useful as a discriminator but must **not** silently become permanent product semantics merely because it is convenient to test.

Preferred order:
1. identify the first real, already-required product boundary whose natural canonical payload is `Bytes` and whose source/type/effect contract can be stated without guessing;
2. use that admitted contract to prove both Bytes argument and Bytes return transport when possible;
3. only if no real contract is yet ready, permit `test.bytes.echo.v0` as an explicitly test-only/bounded diagnostic adapter excluded from release semantic authority.

No diagnostic echo result may be promoted to CM-NET, CM-DATA, CM-VIS or CM-AUDIO PASS by itself.

## Ordinary deterministic Vercel Sandbox gate — zero new unusual experiments

For the first implementation candidate, require an actually-started exact-source Vercel Sandbox and record `new_unusual_experiment_count=0`.

Required deterministic observations:
1. one canonical ABI registry is imported by lowering and VM; no second independent runtime signature table exists;
2. exact source/type/effect/signature identity is admitted before lowering;
3. serialized VM hostcall resolves to the same immutable ABI contract by stable ID/version;
4. exact `Bytes` payload survives argument and return transport, including NUL and non-UTF-8 octets, without text interpretation;
5. wrong argument type fails closed before host invocation;
6. wrong host return type fails closed before the value reaches Clay state/caller frames;
7. capability denial fails closed independently of payload type;
8. mutable/bytes-like boundary admission either snapshots exactly once into owned immutable `Bytes` or rejects according to the declared contract; aliasing cannot mutate VM-owned data;
9. legacy `Int -> Int` hostcall behavior and relevant CLAYVM/1/2 fixtures remain unchanged;
10. direct VM execution and serialized load/execute roundtrip agree;
11. ordinary regression/full-pytest remains nonzero, zero-skips where required, and does not consume another unusual experiment;
12. if the candidate is carried into `EntityOS`, rebuild twice and bind the exact one-file artifact digest; this is scoped regression evidence, not whole-machine acceptance.

## Promotion path after transport proof

- CM-NET: define explicit address/connection/timeout/cancellation/partial-I/O semantics at TypedIR before DNS/socket/TLS adapters.
- CM-DATA: fuse Bytes crossing with producer epoch/stability/ownership and measure copies, allocations, latency and backpressure.
- CM-VIS: carry typed visual envelopes plus opaque Bytes/Buffer payload without mandatory decode.
- CM-AUDIO: carry typed audio envelopes plus opaque Bytes/Buffer payload without mandatory decode.

Streaming/resource semantics must choose between owned Bytes chunks and first-class Buffer/lease using measured evidence, not assumption.

## Coordination / outcome

The attested one-file EntityOS lane has exact Vercel Sandbox evidence only for product head `92b629566452d8f45fd208fba943b823ddd37e8c`; later PR #787 descendants do not inherit that executable PASS. Its exactly-one `go` unusual experiment is consumed, so this Bytes lane is regression/discrimination only.

No new product Bytes branch is opened by this research update. Reason: the current blocker is semantic-authority placement, not lack of code. Opening a generic `ClayValue` patch before the ABI authority is canonicalized would create a tempting fail-open/duplicate-signature path.

Outcome:
- **REJECT** generic untyped `ClayValue` widening;
- **RETAIN/PREFER** one versioned canonical hostcall ABI registry shared by lowering + VM;
- **DEFER** bytecode-carried full hostcall signature as fallback if registry identity cannot be made stable/fail-closed;
- **RETAIN** Buffer/lease as later measured high-bandwidth evolution;
- require a real admitted Bytes product contract, or explicitly bounded test-only echo, before product implementation;
- all next execution is ordinary Vercel Sandbox regression with `new_unusual_experiment_count=0`.

Whole EntityOS / whole Clay Computer acceptance remains open.