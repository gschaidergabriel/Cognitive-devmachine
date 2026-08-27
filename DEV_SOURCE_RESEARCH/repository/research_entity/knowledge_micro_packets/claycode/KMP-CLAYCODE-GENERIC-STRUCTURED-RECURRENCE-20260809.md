# KMP — Generic structured recurrence is sufficient for current FRANK loop-of-loops representation

- packet_id: `KMP-CLAYCODE-GENERIC-STRUCTURED-RECURRENCE-20260809`
- domains: `claycode, frank, harness, gwt, emergenz, hyperposition, claygraph, unifieddb, clayresearch`
- epistemic_class: `LOCAL_PROXY_EXECUTABLE_RESEARCH_PLUS_PRIMARY_SOURCE_TRIANGULATION`
- status_hint: `OPEN_SUPPORTED_NOT_PROMOTED`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`
- canonical_parent: `r2 / 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Atomic claim

The current FRANK loop-of-loops requirement does **not** yet justify a FRANK-specific ClayCode cognitive primitive. A generic structured recurrence/control-flow IR with explicit loop-carried state, finite budgets, continuation/exit conditions, halt reasons, provenance and effect boundaries is sufficient for the tested nested-loop proxy.

## Evidence

Current-run experiment `EXP-CC-G9-STRUCTURED-RECURRENCE-20260809`:
- parser -> canonical IR -> Python lowering -> execution;
- separate AST interpreter as semantic oracle;
- 2,000 randomized nested-loop differential cases;
- 0 semantic mismatches;
- 4/4 negative cases rejected;
- generated code executed successfully in a separate `/usr/bin/python3` process.

Primary-source triangulation:
- MLIR SCF represents generic structured loops with loop-carried values and explicit continuation conditions;
- recurrent-depth literature independently supports adaptive recurrence, overthinking failure and stability concerns, but does not prove FRANK equivalence.

## Negative / gap

CURRENT `research_entity/claycode/g9/grammar.ebnf` has `cycle(...)` but no general checked `while/for/break/return` structured-control path, while G9 V3 source already contains an `if` form not represented by that grammar. This is a compiler/control-flow completeness gap.

## Boundary

- not production-parser evidence;
- not E2B evidence;
- not FRANK runtime evidence;
- not emergence evidence;
- not proof that spectral-radius or attractor metrics causally improve FRANK;
- source syntax never grants effect authority.

## Falsifier / next test

Freeze a typed structured-control IR and run the real production parser/compiler across:
1. nested bounded loops;
2. loop-carried typed values;
3. break/continue/return and error paths;
4. async/concurrent recurrence;
5. effectful loop bodies with external permit revalidation;
6. H1 frozen FRANK replay loops;
7. translation validation against an independent interpreter/oracle.

If a real FRANK recurrence requirement cannot be represented without a FRANK-specific primitive, reopen the semantic design.
