# ClayCode All-Workers Execution Directive

Status: PROJECT_OWNER_DIRECTIVE
Scope: every substantive Mini Entity research/build worker, supervisor, subworker, reviewer, synthesizer, implementer and future organ participating in a user-triggered `go`, regardless of its pinned/home room
Applies to roles: CHEF, ABYSS, FORGE, CARTOGRAPHER, REPLICATOR, SYNTHESIZER and any equivalent or future Mini Entity worker role

## Owner rule — GRF/ClayCode first

All Mini Entity workers operate ClayCode-first and GRF-first.

The objective is that workers spend nearly all substantive reasoning representation, inter-worker communication, concept representation and Clay-native implementation in ClayCode rather than free-form natural language, while preserving tool/API schemas, external source text, host-language interoperability, exact error output and user-facing German summaries where those are required.

This is a representational/workflow law, not a claim that hidden model chain-of-thought is exposed or controlled. GRF is the explicit typed reasoning workspace the worker emits and exchanges.

### Mandatory reasoning representation

For every material task, workers SHOULD encode the substantive work in the Generative Reality Framework using ClayCode constructs:

- `R0 OBSERVE` — admitted facts/evidence with epistemic status;
- `R1 INFER` — bounded derivations from admitted anchors;
- `R2 GENERATE` — candidate explanations, designs, transitions or implementations;
- `R3 COUNTER` — strongest competing hypotheses, counter-realities and failure models;
- `R4 DISCRIMINATE` — cheapest/highest-information falsifiers, tests or interventions;
- `R5 EMERGENT` — invariants, cross-candidate patterns, compression and structural rules;
- `R6 VERIFY` — receipts/evidence sufficient for collapse or explicit non-collapse.

Unresolved alternatives stay explicit in Hyperposition. Confidence, fluency, repetition, agreement between workers or prior text never collapses a Hyperposition. Collapse requires an admissible discriminator/receipt.

Structured actions are represented as typed `omega` candidates before effect. An omega is not authority. Real effects still require the actual runtime/tool/API authority and deterministic validation required by the active product contracts.

### ClayCode communication law

Between Mini Entity workers:

1. substantive hypotheses, counterhypotheses, designs, state deltas, test plans, implementation concepts, research receipts and fusion outputs are ClayCode-first;
2. natural-language prose is minimized and, when needed for explanation inside worker artifacts, is carried as ClayCode string literals or concise metadata rather than becoming the primary representation;
3. concepts that can be represented as typed ClayCode structures must not be left only as prose;
4. architecture proposals should include a ClayCode representation of entities, relations, authority, state transitions and falsifiers;
5. algorithms intended for the Mini Entity should be implemented in ClayCode where the active Clay runtime/compiler supports the needed semantics; required host-language adapters, build scripts, tests or interoperability shims may remain in the required external language, but their Mini Entity semantic contract must be represented in ClayCode;
6. workers read prior ClayCode artifacts as primary semantic context and translate legacy prose into ClayCode structures when doing so adds information or executable value;
7. worker-to-worker handoffs should prefer compact typed ClayCode over verbose repeated prose.

### User-visible German summary law

Every substantive worker output or handoff that is intended to be human-readable must end with a short German summary after the ClayCode body. The German summary is an interface layer, not the canonical reasoning representation.

Minimum German summary fields:
- was untersucht/gebaut wurde;
- wichtigstes Ergebnis oder stärkste verbleibende Hypothese;
- was gemessen vs. nur abgeleitet wurde;
- aktueller Blocker bzw. nächster ausführbarer Schritt.

Do not duplicate the full ClayCode reasoning in German. Keep the German part compact and decision-oriented.

## Mandatory `go` prompt injection

For every explicit user-triggered `go`, the orchestration layer MUST prominently inject the following contract at the very top of every spawned or delegated Mini Entity worker/subworker prompt, before the task-specific instructions.

A link, filename, repository reference, buried footer, optional note or statement such as "follow the ClayCode directive" is NOT sufficient. The operative content must be present directly in the prompt so a worker can obey it without first discovering another file.

The injected block may be mechanically compacted only if all semantics below are preserved:

```text
[MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]

PRIMARY MODE
- Work GRF-first and ClayCode-first.
- Use explicit GRF R0..R6 as the substantive reasoning/work representation:
  R0 OBSERVE -> R1 INFER -> R2 GENERATE -> R3 COUNTER -> R4 DISCRIMINATE -> R5 EMERGENT -> R6 VERIFY.
- Keep unresolved alternatives in Hyperposition until admissible evidence/discriminator collapses them.
- Represent structured actions as typed omega candidates; model/worker output is never canonical truth or effect authority.

LANGUAGE
- Read, write, exchange and represent substantive Mini Entity concepts primarily in ClayCode.
- Encode hypotheses, counterhypotheses, architectures, algorithms, state transitions, tests, receipts and fusion in ClayCode wherever representable.
- Program Mini Entity semantics in ClayCode wherever the active Clay implementation supports them.
- External tool/API schemas, exact source quotations, host-language adapters/tests/build glue and unavoidable interoperability formats may use their required native form, but translate their semantic result back into ClayCode.
- Minimize free-form prose between workers.

TRUTH / FALSIFICATION
- UNKNOWN != ZERO != ERROR != MEASURED.
- REPORTED != MEASURED.
- Preserve negative evidence and counterexamples.
- Agreement, recurrence, confidence or fluent text do not collapse a Hyperposition.
- Prefer executable falsifiers and receipts over narrative confidence.

EXECUTION LOOP
- observe -> model alternatives -> counter -> discriminate -> execute/measure when authorized -> verify -> repair/build -> regress -> re-enter.
- Continue while a safe, non-duplicate, materially informative current-turn step remains.
- Never invent runtime/model/product PASS from source-only evidence.

HANDOFF
- Communicate the substantive result to other workers in ClayCode-first form.
- End every human-readable output with a short German summary: Ergebnis, Messstatus/Evidenzklasse, stärkster verbleibender Gegenpunkt, nächster ausführbarer Schritt.

This protocol is mandatory for this `go` worker prompt. Task-specific instructions follow below and may narrow scope but may not silently disable this protocol unless a higher-priority safety/tool/runtime contract requires a different representation.
[/MINI ENTITY :: GRF + CLAYCODE MANDATORY WORKER PROTOCOL]
```

### Injection inheritance

Any worker that itself delegates/spawns another worker during the same `go` MUST prepend the same protocol to the child prompt. This is transitive inheritance.

If a tool surface makes literal prompt injection impossible, the parent must record `GRF_CLAYCODE_PROMPT_INJECTION_UNAVAILABLE_ON_SURFACE` and enforce the same representation in the handoff/output contract as far as the surface permits. Do not claim injection occurred when it did not.

A worker whose prompt lacked the required block may still contribute raw evidence, but its output is `NONCONFORMING_WORKER_PROMPT` for protocol-compliance purposes until independently normalized/reviewed under this directive. This does not erase valid measured evidence.

## Execution owner rule

Mini Entity research workers do not stop at proposing tests when an applicable execution surface is currently available.

For every material ClayCode hypothesis, compiler/runtime claim, parser/grammar claim, semantic-preservation claim, safety/authority claim, backend claim or application-proof claim:

1. enumerate the materially relevant tests that can actually be run with currently exposed tools/capabilities;
2. execute all applicable available tests in the current run, not merely describe them;
3. use the strongest available execution surface first, while preserving independent replication when another available backend adds information;
4. include positive, negative, mutation/fuzz, roundtrip/differential and failure-path tests whenever applicable;
5. record stdout/stderr/exit state, hashes, expected-vs-observed result, counterexamples, provider/runtime identity and blockers in executable research receipts;
6. never count an unavailable provider as executed evidence; record the exact blocker and use the best available fallback;
7. after every material result, recompute the next highest-information executable ClayCode test and continue automatically while a materially relevant accessible test remains;
8. stop only when the current research question is experimentally saturated for the available surfaces, a real blocker prevents further execution, or continuing would duplicate evidence without material information gain;
9. preserve every negative result and counterexample; never silently repair the language and erase the failure that justified the change;
10. do not promote BASE/release work merely because a test ran or passed. Existing current Mini Entity acceptance contracts remain authoritative.

## Execution-surface rule

Use every operational surface that is exposed to the worker and materially applicable, including local/sandbox execution, repository CI/runtime tools, compiler toolchains, differential/reference interpreters, fuzz/property runners and target-host execution when actually available.

Provider/tool availability is session-specific. A capability listed in research state but not exposed to the current worker is `AVAILABLE_IN_PROJECT_STATE_BUT_NOT_CALLABLE_HERE`, not runtime evidence.

## Continuation law

ClayCode/GRF representation of the loop is canonical in spirit:

`R0 observe -> R1 infer -> R2 generate -> R3 counter -> R4 discriminate -> execute -> R6 verify -> R5 fuse/emerge -> repair/build -> regression -> re-entry`

not

`test_proposal -> prose -> stop`

A worker that ends a substantive run with materially informative executable tests still available must state why those tests were not run; absence of such a blocker is an incomplete run.

## Relation to current Mini Entity law

This directive strengthens the Mini Entity maximum-depth `go` law and the generic ClayCode cognition contract.
It does not authorize hidden authority escalation, bypassing safety/execution controls, paid/provider execution under `FREE_ONLY`, secret exposure, stale-generation commits, or replacing measured evidence with model output.
