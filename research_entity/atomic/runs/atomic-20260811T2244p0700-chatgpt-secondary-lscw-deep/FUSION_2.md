# ATOMIC LSCW — Fusion 2

## External-collision outcome

The external research destroys broad novelty claims.

Established mechanism families already cover:

- proof-carrying code: machine-checkable safety-policy evidence attached to code;
- proof-carrying data: messages carrying proofs that their data and history comply with a property;
- translation validation: per-translation refinement validation in a common semantic framework;
- verified compilation: compositional semantic preservation across compiler passes;
- typestate and linear resources: operation legality and state/resource protocols;
- capabilities and provenance: non-forgeable authority/provenance models;
- in-toto/SLSA: artifact/supply-chain provenance and attestation;
- RATS: evidence, verification, relying-party appraisal and freshness;
- 2026 agent-governance work: action certificates, canonical action identity, approval binding, execution/replay attestation.

Therefore LSCW must **not** be presented as a new proof-carrying, provenance, capability, typestate, action-certificate, or verified-compilation invention.

## What survives recombination

Four pre-search hypotheses compose into the only candidate worth carrying forward:

- H02 linear consume/reissue witness;
- H04 generalized per-transition semantic refinement;
- H07 dual semantic/product identity roots;
- H14 semantic-dimension conservation/residual.

H05 proof-carrying transition is demoted to optional evidence encoding, not the mechanism identity.
H06 capability semantics becomes one implementation option for linearity, not the main claim.
H09 typestate becomes a legal-sequence layer, not sufficient by itself.
H03 strict hash chain remains the strongest simple integrity baseline but is predicted to over-reject legitimate semantic-preserving recompilation.
H01 no-new-primitive conjunction remains the strongest counterhypothesis.

## Selected candidate after collision

**LSCW-001 — Linear Semantic Conservation Witness**

A material lifecycle transition consumes exactly one current witness containing a typed semantic projection and provenance-bound predecessor identity. The stage declares a finite set of dimensions it is permitted to transform. The verifier computes the changed semantic dimensions and rejects any change outside that set as a residual. If the relation passes, it issues a unique successor witness tied to the concrete object actually consumed and produced.

Two roots are deliberately distinct:

1. `semantic_root`: equivalence/preservation of Clay semantic obligations under allowed transformation;
2. `product/artifact/runtime identity`: exact current objects/lineage required for ProductStart, dependency admission and recovery.

This distinction prevents two symmetric errors:

- strict byte identity rejecting a legitimate semantically equivalent representation change;
- semantic equivalence incorrectly authorizing an unadmitted sibling artifact/state as current `self.root`.

## Alien mechanism after formalization

The cross-domain conservation metaphor survives only in a precise form:

`semantic residual = changed material dimensions - stage.allowed_transform_dimensions`

`residual != empty -> fail closed`

The value, if any, is not the word "conservation". The value is a common machine-checkable semantic basis that makes **unexplained change** a first-class defect across previously separate lifecycle stages.

If an ordinary set of typed pre/postconditions implements the same relation more simply, the conservation candidate is killed as an architectural primitive and may survive only as a testing notation.

## Critical collision with current ProductStart AND-gate

The fresh ProductStart gate is conjunctive. LSCW does not replace it.

ProductStart answers:

`Are all required current evidence axes jointly present?`

LSCW asks a different question:

`Did this accepted successor preserve all dimensions that were not explicitly allowed to change, and is it the unique valid successor of the exact current predecessor?`

If the current gate plus current local guards already answers the second question in all real paths, LSCW is redundant and must be refuted.

## Critical collision with current effect-authority path

Execution-generation fencing, provider idempotency/reconciliation and V17 re-entry remain authoritative. LSCW cannot replace:

- provider-side durable idempotency;
- timeout-after-acceptance reconciliation;
- confirmation policy;
- destructive/security-sensitive effect gates;
- verified outcome evidence;
- causal-use receipts.

LSCW may at most carry/check that those dimensions remain bound and current.

## SQLite-specific fusion

Official SQLite documentation states the WAL-reset corruption race is fixed in 3.51.3 and later, and 3.53.4 contains the fix. PR359's private 3.53.4 V4 admission path is therefore directionally aligned with the primary source.

The remaining Frank-specific question is not merely version selection. It is whether ProductStart and subsequent runtime consumption can prove that the **actual loaded object** is the admitted fixed object and whether this remains true across installed restart/recovery. That is a concrete LSCW consume-bound dimension.

## Post-search novelty classification

`NOVEL_COMBINATION_CANDIDATE`

No equivalent complete Frank-specific lifecycle composition was found in the searched scope, but the constituent mechanisms are heavily occupied by prior art. No world-first or general-superiority claim is allowed.

## Strongest counterhypothesis

A conventional `CurrentExecutionContext` containing the same typed fields, validated by existing stage-local guards plus the ProductStart AND-gate, will reject every meaningful mutant with lower state amplification and less trusted code. If so, LSCW is architectural bureaucracy and should be deleted.
