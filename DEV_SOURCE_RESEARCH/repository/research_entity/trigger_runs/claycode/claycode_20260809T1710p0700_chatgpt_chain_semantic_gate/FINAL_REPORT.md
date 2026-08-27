# ClayCode Trigger Run — Compiler Provenance × Semantic Gate

Run: `claycode_20260809T1710p0700_chatgpt_chain_semantic_gate`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Target: Ubuntu/Linux developer system for Frank v0.1  
Promotion: **NONE**  
Gate: **NOT_PASS**

## Executive result

This run does not add another ClayCode surface generation. It refines the BASE compiler evidence contract.

The current mesh already established that G9 source exceeds the checked EBNF, that `Ref` and hyphen/minus lexing are not closed for tested classes, that control-flow/evaluation order is not fully frozen, and that manually lowered fixtures can bypass the source->parser->typed-IR chain. The new question was narrower:

> If ClayCode adds an explicit cryptographic compiler-provenance chain, is that enough to prove semantic-preserving compilation?

**No.**

A local executable discriminator built a joined chain:

`source_hash -> grammar/parser -> AST_hash -> typed_IR_hash -> semantic_hash -> lowering_version -> artifact_hash -> execution_receipt`

and then attacked it.

Results:

- inconsistent tamper mutations detected: **50,000 / 50,000**;
- clean generated source variants falsely rejected: **0 / 10,000**;
- whitespace-only source variant: different source/contract hash, but identical AST, typed IR, semantic and generated-artifact hashes;
- deliberately wrong but self-consistent lowering: chain integrity passed **10,000 / 10,000**;
- semantic oracle detected **9,996 / 10,000** behavioral differences; the four misses were observationally equivalent cases where the right operand was zero;
- one separately executed wrong-lowering witness produced `2` where the source operation required `12`, with **zero chain-integrity errors**.

Therefore:

`provenance integrity != semantic preservation`

and BASE needs both.

## New BASE contract candidate

A ClayCode compiler acceptance receipt should bind at least:

1. exact source/provenance identity;
2. grammar + parser version;
3. canonical AST identity;
4. typed IR/type-effect identity;
5. ProgramSemanticId;
6. lowering/backend version;
7. exact generated artifact identity;
8. execution receipt/environment identity;
9. **independent semantic-preservation evidence** for the translation (reference evaluator, differential oracle, formal proof, or equivalent discriminating check appropriate to the operation).

The receipt chain is an audit/replay spine. It must not be treated as proof simply because every hash is self-consistent.

## Why this matters across the mesh

### ClayCode

This directly refines CC-WP-02/03/05/06/11. Frontend closure remains the first blocker, but once a parser exists, acceptance cannot stop at “all stage hashes line up.” A wrong compiler can faithfully hash its own wrong outputs.

### Harness

The current `TurnTraceEnvelope` validator is complementary, not redundant. Compiler/build provenance answers *which source/IR/lowering produced this artifact*; runtime causal tracing answers *what the artifact did in a specific episode*. Link them, do not collapse them.

### Frank

C9's separation of semantic identity, execution identity and authority is retained in refined form. This run independently supports semantic-vs-exact identity separation, but does **not** validate all mutable-resource or effect-authority assumptions. `FRANK_CLAYCODE_GOODMAN_REVIEW.json` preserves those evidence boundaries.

### ClayGraph

Stable Ref/provenance/selection identity depends on deterministic parsing and canonical semantics. A compiler receipt can identify the transformation lineage but cannot turn graph activation or a selected relation into truth/authority.

### UnifiedDB

The U2 distinction between typed semantic identity and exact emitted representation identity is directly reproduced in miniature: whitespace source variants had different exact source/contract identities but the same canonical semantic and artifact identities.

### GWT / Hyperposition / Emergenz

No new primitive is justified. Receipt integrity improves observability/replay only; it is not evidence of receiver causal use, topology necessity, emergence, or consciousness.

## External independent checks

External primary/official sources were used as architecture checks, not as authority over ClayCode:

- **in-toto** models a continuous software-supply-chain evidence chain using step/link metadata over materials and products.
- **SLSA** requires provenance that identifies output artifacts by cryptographic digest and describes how they were produced; its provenance schema separates build definition and run details.
- **CompCert** makes compiler correctness a semantic-preservation property between source and generated target behavior, not merely artifact identity.
- **Translation validation** treats each produced translation as a correctness object that can be validated independently of trusting the compiler implementation.

These sources support the architecture split revealed by the executable counterexample: provenance and semantic correctness are different evidence dimensions.

## Goodman anti-echo result

Three materially imported FRANK assumptions were reviewed.

- semantic identity vs execution/provenance identity: **REFINED** and independently supported by the whitespace-equivalence experiment;
- receipts/effect authority: **REFINED** — a valid receipt chain is evidence, never authority or semantic correctness;
- mutable resource instance identity: **UNRESOLVED** in this run because no fresh alias/rebind/TOCTOU target-host experiment was executed.

No FRANK↔ClayCode agreement was counted twice.

## Negative results preserved

1. A cryptographically self-consistent compiler ancestry chain is **not sufficient** semantic-preservation evidence.
2. The initial fuzz harness strategy of spawning a process per case exceeded the tool window; the optimized harness preserved the failure and separated executable witnesses from in-process mutation testing.
3. This run does not close the existing G9 grammar/lexer/control-flow blockers.
4. This is local synthetic Linux evidence, not execution on Andreas' exact Ubuntu developer host.
5. No BASE work package or application gate is promoted.

## Highest-information next implementation

1. Finish the authoritative CC-WP-02 parser over the admitted executable G9 surface.
2. Emit joined compiler provenance receipts for every stage.
3. Freeze explicit canonical control/evaluation semantics.
4. Add translation-validation/differential checks between source/reference evaluator and each backend lowering.
5. Mutation-test the receipt chain **and** the semantic oracle separately.
6. Feed compiler receipt identity into Harness `TurnTraceEnvelope` without conflating build identity with runtime causal identity.
7. Run APP-01/APP-02 and then the remaining application suite on the Ubuntu target; only surviving executable counterexamples may justify new language semantics.

## Final synthesis

ClayCode's BASE convergence rule becomes:

`deterministic frontend`
`-> canonical typed semantics`
`-> joined provenance chain`
`-> independent translation/semantic validation`
`-> backend artifact`
`-> runtime causal receipt`
`-> application proof`

not:

`hashes match -> compiler is correct`.

This is a research delta, not a release advance.
