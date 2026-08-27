# ClayCode Trigger Run — Stage Identity Chain after Source-Chain Failure

Run: `claycode_20260809T1708p0700_chatgpt_stage_identity_chain`  
Trigger: `claycode`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE / IN_PROGRESS`  
Target: Frank v0.1 on Ubuntu Linux developer system only  
Promotion: **NONE**

## Executive result

This run did not redesign ClayCode. It assimilated the newest lexical/source-chain negative evidence and the newly created Harness `SourceChainEvidence v1` oracle, then tested one narrower architectural question:

> Which identities must remain distinct across source -> parse -> canonical semantics -> lowering -> executable artifact -> replay?

A bounded admitted-subset experiment produced 4,958 distinct source/contract identities from 5,000 formatting/field-order variants, while all successful variants collapsed to exactly one canonical semantic identity and one generated executable artifact identity. A semantic mutation changed semantic and artifact identity; a parser-version-only mutation changed contract identity without changing program semantics; a lowerer-version/emitter-byte change changed lowering/artifact identity without changing program semantics; artifact tampering changed artifact identity.

Result: layered content-addressed identities are supported for this bounded class. No BASE gate passes and no canonical claim is promoted.

## Current evidence assimilated

### ClayCode frontend/source chain

The immediately preceding source-chain integrity run found that a prior loop-dynamics fixture was not admitted end-to-end by the current grammar and that its Python lowerer added undeclared terminating-return behavior to `emit`. A 20,000-case discriminator differed in 17,693 cases. The whole-mesh Fusion therefore downgraded those runs from compiler-chain evidence to manually lowered mechanism fixtures and established a hard BASE rule: admitted source -> production parse -> canonical typed IR -> checked lowering -> executable target -> replay receipt.

The lexical-closure run independently found:
- adjacent `@Ref` token overconsumption under the literal current EBNF;
- hyphen/minus ambiguity;
- the need to derive `ProgramSemanticId` after deterministic parse/canonicalization while retaining parser/compiler identity as separate provenance.

### Harness

During this run Harness added `source_chain_oracle_v1.py`, which validates stage continuity, parser admission, type/effect checking, lowering semantic deltas, execution and replay. This is a strong convergence signal, but not independent scientific replication of ClayCode semantics.

A narrow refinement remains: the oracle currently requires a `semantic_hash` on Source, Parse and Typed-IR. The field may be copied as an expected/linked semantic reference, but pre-canonical stages must not be treated as independently minting semantic authority. Canonical verified semantics should define the derivation point.

### UnifiedDB / ClayGraph

A concurrent DB transaction broker experiment executed generic typed ClayCode-like IR through a host-owned SQLite broker: 2,000 randomized differential cases had 0 mismatches; invalid/forged/wrong logical resource handles were denied without state change; crash rollback and idempotency held in the tested class. This supports implementation through generic IR + typed resource/authority boundaries rather than adding a DB-specific core primitive.

ClayGraph implication is identity hygiene rather than a new graph primitive: derived graph semantic nodes/relations should key from canonical semantic identity, while raw source/parser identity stays provenance. Activation remains non-truth and non-authority.

## External independent comparison

Primary technical documentation was used, not worker agreement:

- MLIR Dialect Conversion and progressive lowering: explicit legal/illegal conversion targets, type conversion, staged lowerings and translation validation patterns support ClayCode's existing dialect/lowering architecture instead of new syntax.
  - https://mlir.llvm.org/docs/DialectConversion/
  - https://mlir.llvm.org/docs/Tutorials/Toy/Ch-5/
- WebAssembly Component Model / Canonical ABI: typed interfaces, resources/handles and explicit host/component boundaries reinforce the existing separation between program semantics and host capability/effect authority.
  - https://component-model.bytecodealliance.org/design/canonical-abi.html
  - https://github.com/WebAssembly/component-model/blob/main/design/mvp/Explainer.md

These analogues support architectural separation principles; they do not prove ClayCode correctness.

## Executable experiment

Artifact: `STAGE_CHAIN_PROBE.clay`  
Probe: `STAGE_CHAIN_PROBE.py`  
Receipt: `EXECUTABLE_RESEARCH_RECEIPT.json`

Bounded source:

```clay
module claycode.lab.stage_chain
version "0.1"
record LoopGate {
  recurrence_count:Int;
  recurrence_budget:Int;
}
rule recurrence_count==recurrence_budget => HALT
```

The proxy parser uses only a subset admitted by the current G9 EBNF: module/version/record/rule and existing `==` / `=>` operators. It is deliberately not the production parser.

### Baseline identities

- source SHA-256: `3eb33e0b33995f8d556d88e2bdfc05ad58a2f4f3e01f03fa08db1775689ae765`
- canonical semantic ID: `d7c5d1f615eeb365b1d5b34cdac24d0d00ebad8c7d1310a4187427a8ccb23594`
- contract ID: `27f1c8d47f9b6286403a7a8ba563dc3e5a92e5f3a6ad646a3639610b3fb204c7`
- lowering ID: `ed5065c23ff3f2d9c4a0b21a7afc6159e5c1427f8ba3579088aa4bd84ad255f5`
- generated artifact ID: `73f0722f7c82b3c52d921b074634830ed9425970af65696ce214e6d1ad14a3f5`

Separate-process execution:
- recurrence_count=8, recurrence_budget=8 -> `HALT`, exit 0;
- recurrence_count=7, recurrence_budget=8 -> `NO_CHANGE`, exit 0.

### 5,000-case equivalence fuzz

- parse failures: 0;
- distinct raw source hashes: 4,958;
- distinct contract IDs: 4,958;
- distinct canonical semantic IDs: 1;
- distinct generated artifact IDs: 1.

This is direct bounded evidence that raw source/contract identity and canonical program identity are not the same equivalence relation.

### Mutation matrix

1. `HALT -> STOP` semantic mutation: semantic ID changed; artifact ID changed; observed output `STOP`.
2. parser `v0.1 -> v0.2` with same parse: semantic ID stayed equal; contract ID changed.
3. lowerer `v0.1 -> v0.2` with emitted-byte change: semantic ID stayed equal; lowering ID and artifact ID changed.
4. generated artifact tamper: artifact hash changed and was detected.

## Hypotheses

### H-CC-STAGE-IDENTITY-021 — OPEN_SUPPORTED_BOUNDED_CLASS

BASE receipts should separate source/contract identity, canonical `ProgramSemanticId`, lowering identity, artifact identity and execution/replay identity.

Counterhypothesis: one monolithic source/contract hash plus final execution receipt is sufficient.

Falsifier: production Ubuntu matched tests show no stale-cache, replay, diagnosis or unsafe-reuse benefit and material extra cost from layered identity.

### H-CC-SEMANTIC-MINT-022 — OPEN_REFINED_BY_BOUNDED_TEST

`ProgramSemanticId` should be derived at deterministic canonical typed IR or an equivalently verified canonical semantic stage. Source/Parse may carry source/parser identities and a non-authoritative expected semantic reference, but must not independently mint semantic authority.

Counterhypothesis: copying the same semantic hash through every stage is harmless and unambiguous as long as artifact hashes are separate.

Falsifier: a production/formal chain proves the early semantic field is derivation-verifiable, explicitly non-authoritative and causes no circular evidence, cache or replay ambiguity.

## Goodman anti-echo

No confidence was added merely because FRANK, ClayCode and Harness now agree about a source-chain requirement.

- special FRANK loop syntax: **REFINED away** for tested classes; generic records/rules/effects remain sufficient candidates;
- model/program validity vs execution authority: prior **SUPPORTED** verdict retained with no evidential upgrade;
- adaptive visual learner adequacy remains unresolved until executable H1 evidence exists;
- this run's stage-identity result is compiler evidence, not a FRANK-derived assumption.

## Negative evidence preserved

No earlier failure is erased:
- `N-CC-SOURCE-CHAIN-BYPASS-007`;
- `N-CC-EMIT-RETURN-SEMANTIC-LEAK-008`;
- `NR-CC-REF-LEXICAL-CLOSURE-20260809`;
- `NR-CC-HYPHEN-MINUS-AMBIGUITY-20260809`.

The current experiment avoids those failure classes by staying inside a bounded admitted subset. That is not evidence that the full grammar is closed.

## Concurrent-writer observation

A GitHub write in this run received a 409 because the repository head changed concurrently. The worker did not overwrite or force; it refreshed the live head and retried. This is direct operational evidence for revalidation/CAS discipline under active multi-worker writes, but it is not a promoted scientific language result.

## Architecture/research delta

Current preferred BASE identity chain:

```text
SourceText
  -> SourceArtifactId + Parser/LexerContractId
  -> ParsedArtifactId
  -> TypedCanonicalIR
  -> ProgramSemanticId            # semantic derivation authority begins here
  -> LoweringContractId + LoweredArtifactId
  -> ExecutableArtifactId
  -> ExecutionReceiptId
  -> Replay/Snapshot/Transaction roots
```

Rules:
1. identical semantics may have different raw source/contract IDs;
2. parser/compiler/lowerer versions are provenance/contract identity, not program meaning by default;
3. semantic changes invalidate semantic and downstream executable identity;
4. lowerer changes invalidate lowering/artifact identity even if source semantics are stable;
5. executable artifact identity must detect target tampering;
6. execution/replay identity remains separate from static program semantics;
7. none of these hashes grants effect authority.

## Branch feedback

Feedback is materialized in `BRANCH_FEEDBACK_MANIFEST.json` for all nine current foundations.

Highest-information next implementation:
1. amend/test Harness `SourceChainEvidence` semantics so canonical semantic derivation authority is explicit;
2. finish production lexer/parser closure and parse the full admitted G9 corpus;
3. add parse -> canonical print -> parse property tests;
4. feed typed-IR hash into the Harness source-chain oracle;
5. run the same identity/invalidation matrix through the production parser/type-effect/lowerer on the Ubuntu developer host;
6. then progress APP-06/compiler-tool and remaining BASE application proofs instead of reopening syntax absent an executable counterexample.

## Completion boundary

Completed:
- canonical join/revalidation;
- all nine current foundation inputs assembled;
- newest live ClayCode/Harness/UnifiedDB deltas assimilated;
- independent primary-source architecture comparison;
- executable bounded source/parse/canonical/lowering/target experiment;
- 5,000-case equivalence fuzz;
- mutation/invalidation matrix;
- Goodman anti-echo review;
- explicit nine-branch feedback;
- durable run artifacts.

Not claimed:
- production parser/compiler validation;
- exact Andreas Ubuntu-host execution;
- E2B execution;
- local repository preflight/Goodman CLI execution;
- ClayCode BASE progress credit;
- canonical revision/scientific promotion.
