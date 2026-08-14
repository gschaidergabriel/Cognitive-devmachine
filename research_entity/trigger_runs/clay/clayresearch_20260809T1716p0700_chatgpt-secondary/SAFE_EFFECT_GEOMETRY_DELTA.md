# SAFE_EFFECT_GEOMETRY_DELTA — clayresearch 2026-08-09

Status: **SUBSTANTIVE OPEN RESEARCH DELTA**  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Delta

The leading Safe-Effect hypothesis is refined from an abstract effect algebra into a concrete BASE compiler/runtime requirement:

`Clay CapabilityToken -> opaque scoped host resource handle -> typed adapter -> child effect closure -> execution receipt`

Authority must not travel as a model-visible string, path, tool name, or generated-code convention. For any generated/child execution:

`EffectiveEffects(child) subseteq Effects(parent_Clay_contract) union ExternalGrant`

The run adds one new sink-class constraint: **terminal/stdout is not universally PURE**. A control-sequence-capable terminal can be an effectful sink, so APP-08 must test/sanitize/bound terminal output rather than assuming that printing text is harmless.

## 1. Language/cognitive evidence

Current G9 already distinguishes `CapabilityToken`, `EffectIntent`, model intent and external effect lifecycle. No new destructive vocabulary ban is proposed. Cognitive expressivity remains broad: the model may reason about dangerous operations while executable authority remains separately typed.

**Status:** architecture-compatible, not target-model validated.

## 2. Compiler/type-system evidence

EXP-SAFE-001 tested the abstract narrowing rule over 100,000 randomized parent/request capability sets and 50,000 nested delegation chains: zero amplification violations for intersection-based narrowing, versus 99.866% violations in the deliberately unsafe request-as-grant comparator.

This supports the algebra, not the compiler. The required compiler check is now explicit: every FFI/tool/subprocess lowering must carry a parent effect set and reject/wrap a child whose effective effect set exceeds it.

**Status:** MEASURED_SYNTHETIC; compiler proof absent.

## 3. Runtime/broker enforcement evidence

External implementation evidence supports capability-handle designs. `cap-std` uses resource handles/`Dir` capabilities and explicitly distinguishes them from ambient path opening. Wasmtime/WASI provides a candidate capability-oriented sandbox/resource boundary.

Counterconstraint: neither library should be treated as a complete Clay safety proof. `cap-std` explicitly does not sandbox arbitrary untrusted Rust that can call ambient/unsafe APIs; Wasmtime host configuration, resource limits, threads and sink behavior remain part of the trusted computing base.

**Status:** external mechanism support; Clay runtime integration absent.

## 4. End-to-end damage-containment evidence

Not yet established. This run did not execute generated Python/Bash/C/Rust/Wasm/FFI/tool escape attempts on the Ubuntu target, did not test resource exhaustion against real budgets, and did not exercise an irreversibility broker.

**Required APP-08 negative matrix:**
- path traversal / ambient file access;
- child process attempting stronger filesystem/network authority;
- generated foreign code calling equivalent destructive APIs;
- FFI/syscall escape;
- terminal control sequences;
- CPU/RAM/disk/process/network/API-budget exhaustion;
- secret-handle materialization/exfiltration;
- self-approval of irreversible broker request.

**Status:** OPEN; no end-to-end claim.

## 5. Ordinary task-utility evidence

No matched utility benchmark was executed. The design hypothesis is that typed host adapters preserve APP-01..09 utility while narrowing ambient effects. This must be measured rather than assumed.

**Required comparison:** baseline Ubuntu host access vs Safe-Effect adapter access on CLI, HTTP, DB, concurrent service, GUI, compiler/tool, numerical/ML, system administration and Frank-component tasks; record success rate, latency, code/IR burden, rejection/repair rate and recovery cost.

**Status:** OPEN.

## Strongest counterhypotheses

- capability mediation introduces excessive implementation/interop overhead;
- generated foreign code finds ambient escape routes outside the parent contract;
- versioning/recoverability creates storage/availability damage;
- terminal policy is environment-specific and may be safely relaxed in a proven inert sink;
- conventional Linux sandboxing plus backup/permissions may match Safe-Effect utility/safety with less semantic machinery.

## Next discriminating implementation

Do not add a new ClayCode primitive first. Compile the existing `CapabilityToken`/`EffectIntent` semantics into a minimal Ubuntu host adapter, then run nested child authority tests plus terminal-sink negatives. A failure that cannot be repaired in lowering/runtime/stdlib/FFI becomes a legitimate language-semantic counterexample.
