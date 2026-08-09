# ClayCode Trigger Run — Rule-Surface Partition / Full-Corpus Discriminator

Run: `claycode-20260809T1710p0700-chatgpt-rule-surface-partition`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: r2 `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `BASE_CLAYCODE_RELEASE`  
Promotion: **NONE**  
Gate advancement: **NONE**

## Executive result

This run closes an uncertainty exposed by the immediately preceding typed-RelationIR sibling run: **semantic-hash equivalence of several relation surfaces was not enough to choose a production frontend; full-corpus closure and fail-closed diagnostics were still missing.**

The new executable corpus probe shows:

- current expression grammar proxy: **29/53** admitted G9 `rule` lines;
- minimal relational repair (`<`, `>`, `<=`, `>=`): **33/53**;
- registered typed `PredicateIR` compatibility adds **17** deterministic rules;
- resulting deterministic partition: **50/53**;
- **3/53 remain intentionally unresolved** because automatic normalization would choose semantics rather than merely parse syntax.

The three ambiguous clauses are:

1. `Needle.lowers EffectIntent -> concrete_adapter_plan`
2. `Claude_only consumes latest stack + writes task receipts`
3. `training_data personalizes_for_Andreas_when_FRANK_target && preserves_general_transfer_variants`

Therefore the immediate BASE frontend direction should be:

**closed executable operators + typed declarative PredicateIR/ConstraintIR + explicit surface ownership + bounded legacy normalization + fail-closed ambiguous clauses.**

Do **not** make every bare identifier an executable operator/relation.

## Live-worker integration

A concurrent run, `claycode-20260809T1707p0700-chatgpt-relation-ir-oracle`, established that declared-bare, disjoint-sigil and generic-call candidate relation surfaces could all lower to the same typed Relation IR/hash in its micro oracle. Its own negative result explicitly required full-corpus closure, diagnostics, mutation survival and parser/compiler complexity before selecting a surface.

This run treats that work as shared-project sibling evidence, not independent replication, and adds the missing full-corpus/adversarial discriminator.

## Executable experiment

Artifact: `EXECUTABLE_RESEARCH_RECEIPT.json`.

Method:

1. implement the checked G9 `expr` production as an executable Lark-based proxy;
2. compare current operator set to the smallest relational-operator repair;
3. classify remaining admitted G9 rule forms;
4. normalize only explicitly registered, deterministic relation shapes to typed `PredicateIR`;
5. reject unknown relation names;
6. preserve ambiguous mixed prose/control forms as failures rather than guessing;
7. stress semantic identity and mutation behavior.

Results:

- 20,000/20,000 whitespace variants preserved predicate semantic hash;
- 10,000/10,000 ordered binary operand swaps changed semantic hash;
- 5,000/5,000 unknown-relation mutations were rejected by the registry-gated arm;
- a permissive any-word relation parser accepted 5,000/5,000 generated nonsense triples.

One earlier Earley stress attempt exceeded the hosted execution limit and is excluded. The optimized fail-closed rerun above completed successfully.

Evidence class remains `LOCAL_EXECUTABLE_PROXY`: this is not the production parser and not the target Ubuntu machine.

## Fusion 1 — internal state

### ClayCode

The earlier `<,>,<=,>=` + `if` repair remains necessary but is not sufficient. Current G9 also contains declarative relation phrases (`never_implies`, `loads`, `cannot_authorize`, `includes`, etc.) and several source forms that are not safely reducible to the existing generic expression grammar.

The right response is frontend partitioning, not another broad semantic redesign.

### FRANK

The loop-of-loops architecture still requires machine-readable coupling, scheduling, budget, outcome and re-entry relations. This run refines the compiler representation: those relations should lower through typed non-authorizing PredicateIR/ConstraintIR rather than free-form pseudo-operators.

No new FRANK cognitive primitive is justified.

### Harness

Recent Harness work separates semantic state identity, provenance/source binding, execution binding and trace identity. That makes canonical relation identity and order semantics compiler-critical: relation surface differences must normalize before semantic hashing, while ordered arguments must remain order-sensitive.

### ClayGraph

Current ClayGraph already has typed hyperrelation member roles, provenance/admissibility fields and explicit separation of activation from authority. Typed ClayCode relations fit this substrate without a new graph primitive. A compiler relation cannot acquire effect authority merely because a graph edge/hyperrelation exists.

### UnifiedDB

Current UnifiedDB keeps capability/resource observations, freshness, execution truth classes, work revisions and authority scopes explicit. Relation-signature identity can be persisted/queryable, but compiler relation resolution is not execution truth and does not imply physical database consolidation.

### GWT / Hyperposition / Emergenz

Machine-extractable relations help GWT selection/use/re-entry tracing and Hyperposition role/codependency structure. They do not create causal credit, emergence evidence, truth or execution authority. Existing intervention/lesion/rescue/shuffle requirements remain unchanged.

## External primary-source research

### Soufflé Datalog

Official Soufflé documentation separates declared relations, rules and constraints and uses static typing/checking for relation attributes and rule variables. This is an engineering analogue for declared relation signatures rather than arbitrary word-as-operator acceptance.

Sources: Soufflé `Rules`, `Constraints`, `Types`, and `Program` documentation.

### MLIR ODS / language reference

MLIR represents operations with unique names and explicit constraints; ODS can generate parsing, printing and verification machinery while still permitting custom assembly forms. This supports separating canonical typed semantics from surface syntax rather than letting surface spelling define meaning.

Sources: MLIR Operation Definition Specification and MLIR Language Reference.

### WASI / Component Model

WASI's official documentation describes a capability-based sandbox with no ambient authority until the host grants capabilities. The Component Model likewise separates typed interfaces from internal behavior/host-provided functionality. This independently supports the project boundary that semantic RelationIR does not mint effect authority.

Sources: WASI.dev introduction/security model and Bytecode Alliance Component Model documentation.

## Fusion 2 / anti-echo

Strongest surviving interpretation:

- **SUPPORTED_LOCAL_PROXY:** minimal relational operator expansion alone is insufficient;
- **SUPPORTED_LOCAL_PROXY:** typed registered PredicateIR closes most remaining deterministic G9 relations without new cognitive semantics;
- **SUPPORTED_ADVERSARIAL_PROXY:** arbitrary bare relation acceptance is fail-open and should not be the BASE default;
- **OPEN:** exact textual relation surface (declared-bare vs sigil vs generic call) is not yet selected;
- **OPEN:** current protocol/control `.clay` artifacts need explicit parser/surface ownership; only 27/65 current stack rules match the checked expression proxy, but they may intentionally belong to a different surface;
- **NEGATIVE_RESULT:** three admitted G9 rules cannot be automatically normalized without selecting semantics.

## Goodman review

`FRANK_CLAYCODE_GOODMAN_REVIEW.json` records:

- FRANK loop/coupling requirement: **REFINED** — keep requirement, encode through typed declared relation IR instead of endlessly widening executable operators;
- model/semantic output != execution authority: **SUPPORTED** with independent WASI capability evidence and non-authorizing PredicateIR design.

Shared FRANK/ClayCode ancestry was collapsed and not counted as replication.

## BASE architecture delta

### Justified now

1. Add compiler-visible surface classes:
   - executable `ExprIR`;
   - declarative typed `PredicateIR/ConstraintIR`;
   - explicitly owned protocol/research surfaces.
2. Require relation signatures/registry ownership and arity/role semantics.
3. Keep relation semantic identity independent of textual spelling.
4. Keep binary/n-ary ordered roles order-sensitive unless explicitly typed set-like.
5. Add bounded legacy normalization for current G9 only where mapping is deterministic.
6. Fail closed on ambiguous legacy clauses until an authoritative AST/rewrite is frozen.
7. Keep PredicateIR authority at `NONE`; effect authority remains capability/gateway state.

### Not justified

- arbitrary identifiers as general-purpose executable operators;
- a new GWT/FRANK/ClayGraph/UnifiedDB semantic primitive;
- BASE gate advancement;
- canonical grammar/source mutation from this research run alone.

## Highest-value next implementation test

On the real BASE frontend:

`all current G9 + dialect files -> parser -> typed surface classification -> canonical IR -> semantic hash -> canonical print -> parse`

Required checks:

- current G9 source itself is a mandatory fixture;
- the three ambiguous clauses produce precise fail-closed diagnostics until explicitly frozen;
- typed interface method signatures and comments are covered;
- unknown relation names reject;
- whitespace/surface aliases preserve semantic identity;
- ordered relation-role mutations change semantic hash;
- PredicateIR never grants effect authority;
- then replicate on Andreas' Ubuntu developer target.

After that, compile one ClayGraph hyperrelation/projection receipt and one UnifiedDB semantic transaction/replay fixture through the same production frontend before claiming CC-WP-02/03 progress.

## Stage impact

`BASE_CLAYCODE_RELEASE`: **IN_PROGRESS**.  
`GENERAL_PURPOSE_GATE`: **NOT_PASS**.  
No release work package or mandatory application is marked complete by this run.

## Provenance

Origin actor: `chatgpt-secondary`  
Provider/model: OpenAI / GPT-5.6 Sol  
Canonical parent: r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
External evidence class: primary/official technical documentation  
Executable evidence class: local synthetic compiler-front-end proxy  
Canonical promotion: none
