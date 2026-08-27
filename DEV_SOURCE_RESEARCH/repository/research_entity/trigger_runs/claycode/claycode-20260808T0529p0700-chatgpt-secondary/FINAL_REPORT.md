# CLAYCODE RESEARCH RUN — CC6 Semantic IR / Stateful Projection / Authority Boundary

**run_id:** `claycode-20260808T0529p0700-chatgpt-secondary`  
**trigger:** `claycode`  
**actor:** `chatgpt-secondary` — Independent Secondary Researcher  
**provider/model:** OpenAI / GPT-5.6 Sol  
**canonical parent:** RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
**boundary:** local experiments are synthetic/runtime proxies. No live Qwen3-4B reader was executed and no canonical scientific claim is promoted by this run.

## Executive synthesis

The strongest ClayCode architecture is not one compact surface syntax. It is a three-layer contract:

`canonical semantic IR -> reader/model projection + runtime-indexed decoding Γ -> deterministic external authority/effect gateway -> effect receipt -> outcome/re-entry`

This preserves the current `CC-RC1.1` authority invariant while sharpening the candidate toward a semantic kernel that can be self-representing without being self-authorizing.

The primary delta is:

1. **Canonical Semantic IR** is the durable meaning-bearing form. It has explicit version, stable op/field identities, state root, provenance, typed unknown/conflict/revoked values, assembly/workspace links and causal episode/receipt references.
2. **Projection Compiler** emits reader-specific surfaces (verbose JSON, positional JSON, grammar DSL, binary/MsgPack-like wire form). Projection syntax is disposable and must round-trip to the same semantic IR; it is not canonical truth.
3. **State-aware decoder Γ** can restrict references to entities, fields, capabilities-by-handle, APIs and declarations that actually exist in the current state. It may improve semantic validity but does not decide authority.
4. **Proposal typing** separates `PURE_TRANSFORM`, `STATE_PROPOSAL`, and `EFFECT_PROPOSAL`, allowing local/speculative computation while reserving synchronization and authorization for effect/conflict boundaries.
5. **Authority/effect gateway** is outside the model and outside the grammar. It validates externally minted capability handles, current root, nonce/replay, expiry/revocation, invariants, rollback plan and effect receipts.
6. **Self-hosting is staged**, not magical: K0 minimal deterministic host kernel -> K1 ClayCode parser/validator/interpreter/compiler -> K2 Clay-represented system. The trust root is minimized and audited, not erased.
7. **Qwen3-4B internalization is plausible but unproven for ClayCode.** Current PEFT evidence shows a 4B model can internalize fixed tool knowledge and reduce prompt burden, but forgetting/retention trade-offs are material and must be measured on the target language.

## Internal grounding / Fusion 1

Current RAE evidence already establishes these boundaries:

- `H-G3-006`: model-emitted commit syntax is never authority; external capability/gateway verification is required.
- `KMP-CLAYCODE-AUTHORITY-BOUNDARY`: ClayCode/XENO output is a proposal, not an authorization token.
- G5 `EXP-G5-STATEGRAMMAR-005`: in a constructed symbol-state toy, grammar-only semantic validity was ~20%, state-aware grammar 100%, while independent capability/root checks still rejected ~19.18% of state-valid proposals. This is synthetic separation evidence, not live-reader performance.
- G5 architecture already separates grammar validity, state-semantic validity and execution authority and proposes a pinned Qwen3-4B four-arm factorial as the decisive reader test.
- Canonical r2 identifies `CC-RC1.1 causal episode contract` and `EXP-LIVE-XENO-CLAY-FACTORIAL` as frontier/open work.

### First-generation falsifiable hypotheses

| ID | Hypothesis | Strong counterprediction / falsifier |
|---|---|---|
| H-CC6-001 | Canonical semantics separated from reader projection yields safer evolution and reader-specific optimization than one universal syntax. | A single syntax matches/exceeds semantic fidelity, migration cost and all target-reader metrics. |
| H-CC6-002 | Runtime-indexed grammar Γ reduces ghost/invalid state references versus syntax-only grammar. | Equal ghost-reference rate at matched decoding cost. |
| H-CC6-003 | Grammar validity, state validity and authority are irreducible gates. | A grammar-only arm safely authorizes effects with no false accepts under adversarial root/capability tests. |
| H-CC6-004 | Canonical hashes must be defined over semantic canonicalization, not arbitrary wire bytes. | Cross-version/cross-reader wire bytes remain stable and equivalence-preserving without a semantic canonicalizer. |
| H-CC6-005 | Unknown/conflict/revoked must be explicit algebraic states, not absence/default. | Defaulting preserves all decisions and roundtrips across mixed-version readers. |
| H-CC6-006 | Stable operation/field IDs plus explicit version/migration hooks reduce schema-evolution breakage. | Name/position-only evolution is equally robust under old/new reader interop. |
| H-CC6-007 | `PURE_TRANSFORM` / `STATE_PROPOSAL` / `EFFECT_PROPOSAL` typing permits cheaper selective synchronization without correctness loss. | All-transition synchronization is required to preserve invariants on real workloads. |
| H-CC6-008 | Capability references must be externally issued opaque handles, not model-mintable strings. | Model-generated capability identifiers cannot escalate or alias real privileges under adversarial tests. |
| H-CC6-009 | Root + nonce + expiry + revocation checks block stale/replayed effect proposals independently of model quality. | Adversarial replay/stale-root cases still pass gateway validation. |
| H-CC6-010 | A minimal K0 host plus reproducible/diverse bootstrap checks can make ClayCode self-hosting auditable without pretending to remove the root of trust. | Self-hosted output cannot be independently reproduced/equivalence-checked from source. |
| H-CC6-011 | Qwen3-4B can internalize stable ClayCode/tool semantics with PEFT and reduce prompt/token overhead. | Target model loses task quality or general capability enough to erase the context savings. |
| H-CC6-012 | Reader projections are model-specific optimization targets rather than semantic standards. | One projection dominates across Qwen3-4B and independent readers at equal semantics. |
| H-CC6-013 | Hard constrained decoding can lower semantic quality when the valid support excludes a preferred safe/correct continuation. | No semantic-quality or safety degradation under adversarial grammar conditions. |
| H-CC6-014 | Incremental patch operations reduce transition payload/recompute versus full-state snapshots for sparse updates. | Full snapshots equal or beat patches after validation/recovery costs on target workloads. |
| H-CC6-015 | Self-representation does not imply self-authorization; keeping these separate remains necessary even inside a Clay-written runtime. | Self-hosting safely eliminates the external authorization boundary under red-team testing. |
| H-CC6-016 | Every effect should emit a receipt tied to proposal/root/capability/outcome/re-entry so causal episodes remain auditable. | Equivalent causal validation/recovery works without receipt identity. |

## Hypothesis-guided external research / Fusion 2

### 1. Stateful constrained decoding is technically plausible

Zhang et al., `arXiv:2607.18357`, introduce environment-indexed decode-time grammars Γ whose allowed references are populated from runtime state and updated as new declarations are generated. They prove a No-Ghost property for Γ-slotted references and evaluate across TileLang, SQL and P4. This is a close external analogue of ClayCode state-aware decoding; it supports H-CC6-002 but not ClayCode efficacy itself.

Li et al., `arXiv:2608.03065`, show parser-stack classification can make grammar-mask computation far cheaper: reported mask computation is up to 700x faster on complex programming-language grammars and 30x on schema JSON, with end-to-end throughput approaching unconstrained decoding. Therefore grammar overhead is an empirical break-even problem, not a reason to discard constrained decoding.

### 2. Constrained decoding is not a security boundary

Zhang et al., `arXiv:2606.11817`, report that benign code grammars can themselves become a jailbreak surface and increase malicious-code attack success by more than 30 percentage points on average across their evaluated models/benchmarks. This strongly supports H-CC6-003/H-CC6-013: a grammar can constrain syntax while simultaneously removing safe continuations. ClayCode therefore must treat the grammar as a generation aid/policy input, never as authorization.

### 3. Strongly typed IR + target projections has a close agent analogue

SkCC (`arXiv:2605.03353`) uses a strongly typed intermediate representation to decouple skill semantics from framework-specific formatting, then compiles target-specific projections. Reported experiments show pass-rate gains and 10–46% runtime token savings. This does not prove the ClayCode design, but it is direct external evidence that semantic IR -> reader-specific compilation is useful in heterogeneous LLM-agent systems.

### 4. Qwen3-4B internalization is plausible, with retention risk

Shemla et al., `arXiv:2605.17774`, fine-tune Qwen3-4B and Gemma E4B with QLoRA on about 1,700 tool-use examples. Under description-free inference they report 82.6% less input length versus an informed unfine-tuned baseline; Qwen3-4B reaches judge score 3.78 while using less memory/faster execution than the compared Gemma model, but shows greater catastrophic forgetting. This supports attempting ClayCode internalization but makes retention/forgetting a mandatory metric.

### 5. IR evolution needs explicit dialect/version semantics

MLIR provides extensible dialects and a stable versioned bytecode format with dialect-specific version hooks and post-parse upgrade mechanisms. This is a useful engineering analogue for governed ClayCode dialect evolution: stable semantic identities and migrations can coexist with reader-specific encodings.

Protocol Buffers documentation explicitly warns that deterministic serialization is not canonical across languages/builds and that unknown fields complicate canonicalization. Therefore a ClayCode state hash should be specified over a semantic canonical form, not over whichever projection/wire serializer happened to emit bytes.

### 6. Capability sandboxing supports, but does not replace, the gateway

Wasmtime/WASI defaults to no filesystem access and grants selected directories through preopened handles with explicit permissions. This is implementation evidence for least-authority capability handles. It still does not answer application-level questions such as whether the current state root is fresh, whether a Clay proposal is allowed by FRANK policy, or whether the action has a valid nonce/rollback plan. Sandbox and authorization remain separate layers.

### 7. Self-hosting needs an explicit bootstrap trust story

Bootstrappable/Reproducible Builds work treats self-hosting compilers as a chicken-and-egg/trust problem, minimizing opaque bootstrap binaries and independently reproducing outputs. A documented Mes bootstrap produced bit-identical binaries through diverse compiler paths. The transfer to ClayCode is architectural: a Clay-written runtime should be accepted through staged bootstrap + reproducibility/equivalence evidence, not by circular self-assertion.

## Executable experiments — local sandbox, `simulation_only`

### EXP-CC6-PROJECTION-001 — adversarial projection roundtrip

A naive pipe-delimited mini-syntax (`v=...|id=...|...|args=<json>|x=<json>`) failed on an adversarial string containing delimiter-like text (`|x=` / `|id=`), producing a JSON parsing failure. This is a negative result against ad-hoc delimiter compression without a real grammar/escaping/framing rule.

A robust positional-JSON projection `[v,id,kind_code,root,cap,nonce,args,x]` was then fuzzed on 50,000 generated records containing quotes, backslashes, delimiter sequences, braces, Unicode, emoji, newlines and tabs. Result: **0 semantic-hash/roundtrip failures**.

Byte-size proxy on that corpus:
- canonical-ish object JSON projection: mean **184.70 B**
- positional JSON: **121.36 B** (**34.29% smaller**)
- MsgPack array: **86.86 B** (**52.97% smaller**)

Parsing microbenchmark, 20,000-record corpus, median records/s in this Python runtime:
- object JSON parse: ~**452k/s**
- positional JSON raw parse: ~**568k/s**
- positional JSON parse + semantic reconstruction: ~**493k/s**
- MsgPack unpack: ~**1.676M/s**

These are byte/parser proxies, **not Qwen token, latency or accuracy measurements**. A positional array is also brittle to uncontrolled field insertion, which strengthens the need for versioned semantics and projection governance.

### EXP-CC6-EXTENSION-002 — old-reader unknown preservation

20,000 mixed-version-style records were modified by an old-reader proxy while retaining an opaque extension bag `x`. Result: **0 extension losses**. This shows a simple compatibility mechanism can preserve unknown payloads in the toy; it does not prove production migration correctness.

### EXP-CC6-STATE-003 — unknown/conflict/default collapse

Five semantic states were represented: known false, known true, unknown, conflict(false|true), and revoked(prior=true). A naive Boolean/default projection mapped **known false + unknown + conflict + revoked** to the same `false` value. Therefore absence/default is observably lossy for Clay's set-valued/conflict-preserving semantics.

### EXP-CC6-GATEWAY-004 — independent effect gate predicate

A reference gateway checked proposal kind, current root, capability existence/revocation/scope, expiry and nonce replay. Across 100,000 fuzzed proposals, comparison to an independently implemented oracle produced **0 false accepts and 0 false rejects**. Outcome counts: 66,799 non-effect; 22,061 stale root; 5,545 missing/revoked cap; 2,855 wrong scope; 1,102 expired; 26 replay; 1,612 authorized.

This validates the toy predicate implementation only. It is not a security proof and does not cover capability issuer compromise, TOCTOU races, indirect tool effects, rollback failure or OS/runtime vulnerabilities.

## Second-generation hypotheses / architecture delta

External evidence plus local falsification transforms the design as follows:

1. **ClayCode should be a semantic protocol, not a single text language.** `CC-RC1.1` should remain the authority/causal contract while surface syntax becomes a negotiated projection.
2. **The decoder Γ is a partial semantic front-end.** It may consume the current root/view and eliminate impossible references early, but its output is still a proposal.
3. **Projection provenance becomes security-relevant.** Because grammar constraints can alter model safety behavior, the exact grammar/projection version and source hash should be recorded in proposal provenance and effect receipts.
4. **Canonicalization must be independently specified.** Semantic hashes should normalize typed values/relations/ordering rules and exclude unstable serializer accidents; wire-format determinism is insufficient.
5. **Unknown/conflict/revoked are first-class value constructors.** They must survive old/new reader traversal and cannot be silently defaulted.
6. **Capabilities are unforgeable references from an external issuer.** ClayCode may carry a capability handle/request but cannot mint the authority it denotes.
7. **Self-hosted ClayCode keeps a minimal K0 trust kernel.** A K1/K2 runtime may be written/described in ClayCode, but acceptance requires independent parser/validator/build equivalence and effect-gateway checks.
8. **Internalization is a cache, not the source of semantics.** Qwen weights may internalize stable projections/operations; the canonical operation registry/version/provenance remains external and inspectable so drift can be detected and repaired.

## Candidate ClayCode semantic skeleton (OPEN, non-canonical)

A minimal canonical operation should semantically contain at least:

- `ir_version`, `op_id`, `op_kind`
- `base_root` / state version
- origin/provenance (`actor`, model/provider where applicable, source/projection hash)
- typed inputs and outputs with explicit `known | unknown | conflict | revoked | error`
- relation/assembly/workspace references by stable identity
- optional causal episode identity (`candidate -> ... -> outcome -> reentry` links)
- proposal class: pure/state/effect
- capability **reference/request**, never capability minting
- nonce/expiry for effect proposals
- rollback/compensation intent where effectful
- extension bag / dialect id + version

The canonical IR does **not** need to expose all of this verbosely to a 4B reader. Projection compilers can choose compact positional or grammar-native forms and must prove semantic roundtrip.

## Highest-information next tests

1. **`EXP-LIVE-XENO-CLAY-FACTORIAL` — decisive:** pinned Qwen3-4B; free text vs JSON/schema vs grammar-only vs state-aware Γ vs state-aware Γ + external gateway. Measure exact semantic validity, ghost refs, retries, latency, generated+prompt tokens, energy/RAM, unsafe/unauthorized-effect attempts, repair cost and task score.
2. **Internalization factorial:** base Qwen3-4B vs LoRA/QLoRA ClayCode internalization; with/without operation catalog in context; test task quality, token savings, OOD schema changes and catastrophic forgetting.
3. **Projection bake-off:** verbose object JSON vs positional JSON vs a generated CFG projection vs binary/MsgPack for parser cost plus *actual target tokenizer tokens* and model accuracy. The local byte savings must not be mistaken for token savings.
4. **State evolution suite:** old/new dialect version, unknown op/field, conflicting roots, revoked entity, migration and downgrade; require semantic-hash preservation or explicit non-equivalence receipts.
5. **Authority red-team:** stale roots, replay, revoked caps, cap aliasing, capability strings hallucinated by model, grammar injection, indirect tool calls, TOCTOU, rollback failure.
6. **Self-hosting gate:** implement K0 host interpreter and K1 ClayCode interpreter/compiler; execute the same conformance corpus through independent K0/K1 paths and compare normalized semantic traces/hashes; later add reproducible/diverse builds.

## Negative results / non-promotions

- **N-CC6-001:** ad-hoc delimiter compression is not safe merely because it is compact; adversarial delimiters broke the naive reader.
- **N-CC6-002:** grammar validity is not semantic validity and neither is authority; external evidence adds that grammar constraints can themselves create a safety attack surface.
- **N-CC6-003:** byte-size reduction is not evidence of Qwen token-efficiency or reader accuracy.
- **N-CC6-004:** default Boolean-like projection cannot represent Clay's unknown/conflict/revoked semantics without information loss.
- **N-CC6-005:** self-hosting cannot remove all external trust/authority merely by expressing the runtime in its own IR.
- No live Qwen3-4B result, no production-security claim, no consciousness claim, and no canonical promotion.

## Tool/provider execution boundary

The RAE provider plan classified this run as `scholarly + current_web + implementation + executable + model_experiment`.

Direct provider adapters registered inside the repository (OpenAlex, arXiv adapter, Tavily, Exa, Hugging Face) were not exposed as invokable connectors to this ChatGPT worker. Their required attempts are therefore recorded as `CONNECTOR_BLOCKED`/`RUNTIME_UNAVAILABLE` with native-web/direct-primary-source fallback. Semantic Scholar remains pending runtime verification in the registry; E2B lacks a permitted credential channel. GitHub connector and local sandbox were executed successfully. The target Hugging Face/Qwen model experiment therefore remains open rather than being replaced by a fake simulation claim.

## Promotion decision

`canonical_promotion = NOT_PERFORMED`.

Reason: the architecture delta is well supported as an **OPEN research candidate**, and local deterministic invariants were exercised, but the decisive target-reader factorial and real authority/runtime red-team have not run. The durable result of CC6 is the sharper architecture and falsification plan, not a promotion of ClayCode efficacy.
