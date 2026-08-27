# GO — compiler capability audit + composed-frontier revalidation

Run: `go-20260811T2256p0700-chatgpt-secondary-compiler-capability-audit`

## Result

This cycle did not promote a compiler or a Frank v0.1 gate. It found and repaired an evidence-instrument defect in the first Python-AST lowering candidate while re-steering to the newer composed ClayCode frontier.

The concrete defect was in target PR `Dr.-Unterweger#364`: the gate contained two literal-`True` receipt checks named `external_effect_performed_false` and `authority_minted_false`. Those labels described desired properties but measured nothing.

Two target commits repair that evidence surface without changing ClayCode semantics:

- `1f954beac9da5b40a8d57a38e1dea410f5117243` exposes the exact generated `ast.Module` object from the bounded compiler projection;
- `e0b84927072a4b0ee136a5ba18749582e9126aa0` replaces the tautologies with an independent generated-AST/call-surface allowlist, exact execution-namespace check, empty-builtins check, and helper-identity checks.

A concurrent worker modified the same test between read and write. GitHub CAS returned 409; the stale write was stopped, the current blob re-read, and the newer paired warm benchmark was preserved before applying the capability-audit delta. This is positive concurrency-control evidence: no stale overwrite occurred.

## Exactly one GO out-of-box experiment

`ADVERSARIAL_AST_HOST_CAPABILITY_GRAFT`

The gate deep-copies the generated AST and injects a synthetic forbidden `os.system`-style `Attribute` call edge. It does not execute that edge. The independent audit must detect and reject the graft. A local secondary AST sanity check detected `Attribute` as both a forbidden node and invalid call shape. Accepted-target evidence remains pending.

## Fresh frontier fusion

The current ClayCode supervisor moved the critical path while this run was executing:

- PR #357, current head `2ac082f8694dd7a37388a4e2691ca8bf766d54e4`, is the higher-priority composed 90%-surface/evaluator/package frontier. Its exact-head Ubuntu workflows remained queued at last observation, therefore no promotion credit exists yet.
- PR #364, current head `e0b84927072a4b0ee136a5ba18749582e9126aa0`, is now a better-instrumented bounded CPython-AST lowering candidate, but its exact target workflow was still queued, therefore no compiler credit exists yet.
- PR #366, current head `ee6536ea9ca5382931a050cb0c195d4945ca9cdc`, is a stacked native-C counterbackend. Its GitHub-hosted shadow was failing and its accepted-target run was pending; it also depends on PR #357. It therefore receives no credit.

The important architecture rule is now stronger: multiple host backends over the same Clay source/evaluator ancestry are useful translation-validation diversity, but not independent semantic authority.

## External refresh

Python 3.12 documentation confirms that Python AST can be compiled to code objects and explicitly warns that the abstract syntax can change between Python releases. Therefore the backend remains a version-bound projection with runtime/generated-artifact identity in evidence, not ClayCode semantic authority.

Current Cranelift/Wasmtime remains a plausible later native backend ecology. Current release history also contains compiler/sandbox-relevant bug fixes, which reinforces rather than relaxes the need for exact translation-validation and capability-boundary evidence. A larger backend is not automatically safer or more authoritative.

## Architecture/test delta

Candidate rule: bounded lowering promotion should require all of the following together:

1. exact Clay semantic source + grammar identity;
2. deterministic generated artifact identity;
3. value/behavior differential against the source evaluator and an independent shipping reference where available;
4. fail-closed refusal for unresolved/open semantics;
5. computed backend capability-surface evidence rather than labelled constants;
6. exact accepted-Ubuntu execution/resource receipt;
7. dependency/frontier acceptance where the lowering branch is stacked.

No ClayCode semantic rule changed. No external effect was executed. No Frank Harness authority changed. No final training was authorized.

## Next falsifiers

First, execute PR #357 exact current head on the accepted Ubuntu lane and inspect the full composed receipt. Only after that dependency closes should PR #364/#366 receive bounded lowering credit. If the PR #364 capability audit itself fails on exact target bytes, preserve the failure and repair the smallest falsified audit boundary. If PR #366 remains red, diagnose its backend/gate rather than using backend plurality as confidence by itself.
