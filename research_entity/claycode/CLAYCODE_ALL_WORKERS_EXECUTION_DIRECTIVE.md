# ClayCode All-Workers Execution Directive

Status: PROJECT_OWNER_DIRECTIVE
Scope: every substantive worker whose pinned/home research room is `claycode`
Applies to roles: CHEF, ABYSS, FORGE, CARTOGRAPHER, REPLICATOR, SYNTHESIZER and any future ClayCode-room worker role

## Owner rule

ClayCode research workers do not stop at proposing tests when an applicable execution surface is currently available.

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
10. do not promote BASE/release work merely because a test ran or passed. Existing acceptance contracts and target-host requirements remain authoritative.

## Execution-surface rule

Use every operational surface that is exposed to the worker and materially applicable, including local/sandbox execution, E2B, SandboxAPI, Judge0, repository CI/runtime tools, compiler toolchains, differential/reference interpreters, fuzz/property runners and target-host execution when actually available.

Provider/tool availability is session-specific. A capability listed in research state but not exposed to the current worker is `AVAILABLE_IN_PROJECT_STATE_BUT_NOT_CALLABLE_HERE`, not runtime evidence.

## Continuation law

`test -> receipt -> learn -> recompute -> next_test`

not

`test_proposal -> stop`

A worker that ends a substantive ClayCode run with executable tests still materially available must state why those tests were not run; absence of such a blocker is an incomplete run.

## Relation to existing ClayCode law

This directive strengthens the existing ClayCode mandatory executable loop and the BASE invariant `less change, more compile`.
It does not authorize gratuitous semantic redesign, self-modification, hidden authority escalation, or skipping the Ubuntu Linux developer-system acceptance target for Frank v0.1.
