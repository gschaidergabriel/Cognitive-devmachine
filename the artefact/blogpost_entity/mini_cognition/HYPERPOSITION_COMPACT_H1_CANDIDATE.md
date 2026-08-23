# H1 — compact Hyperposition ClayCode transport candidate

Status: RESEARCH_CANDIDATE / NOT_ADMITTED_INTRINSIC / NOT_VALIDATED
Parent theory: `research_entity/global/HYPERPOSITION_GWT_INFORMATION_GEOMETRY_V1.md`

## Goal

Encode the minimum sufficient unresolved-belief state for cognition with very low generated-token overhead, while keeping full precision, provenance, evidence, truth and effect authority outside the model string.

Candidate compact call:

`h(c,"a-3|b#e7?d4!6")`

This is **not currently an admitted ClayCode intrinsic**. Existing syntax/admission must continue to fail closed on unknown intrinsic `h` until an explicit grammar/runtime candidate is separately implemented and tested.

## H1 grammar

```text
H1 := h(c,"A(|A)*[|T]#E[?D]!6")
A  := ID[Q]
Q  := [+-]INT
T  := ~Q
E  := ID
D  := ID
```

Semantic constraints:
1. at least two alternatives;
2. exactly one `A` omits `Q`; it is the explicit reference hypothesis with relative logit 0;
3. all other `Q` values are quantized relative logits;
4. v1 scale is `delta=0.25 nat`;
5. reference normally denotes the full-precision posterior leader and is the deterministic tie-break if quantization creates a tie;
6. `E` resolves the local aliases to canonical candidate IDs, full evidence/provenance ancestry and unquantized state;
7. optional `D` names a current discriminator candidate; omission means none is currently carried, not that none exists;
8. `!6` means only an admitted R6 receipt may epistemically collapse the state;
9. optional `~Q` is an aggregated omitted-tail pseudo-alternative and prevents compressed omission from masquerading as certainty;
10. ordering is canonicalized by stable identities for semantic hashing and must not alter decoded semantics.

## Decode

Let reference `r` have `q_r=0` and other alternatives carry integer `q_i`.

`z_i = delta*q_i`

`p_i = exp(z_i)/sum_j exp(z_j)`.

Example:

`h(c,"a-3|b#e7?d4!6")`

has `z_a=-0.75`, `z_b=0`, so:

`p(a) ~= 0.321`

`p(b) ~= 0.679`.

These decoded probabilities are a **derived cognition view**, never the canonical posterior.

## Why relative logits

A K-way categorical distribution has K-1 degrees of freedom. Relative logits use exactly K-1 scalar coordinates and make Bayes evidence updates additive before quantization.

For binary alternatives:

`L=log(p_a/p_b)`

so only one scalar is required.

The information-theoretic lower bound also grows with K-1: for probability masses discretized to N total quanta, the number of states is `C(N+K-1,K-1)`, requiring at least `log2 C(N+K-1,K-1)` bits. H1 does not claim to reach that coding bound, but it avoids serializing mathematically redundant K normalized decimals.

## What must NOT be serialized

Do not include if deterministically derivable from `E + q`:
- normalized `p_i`;
- entropy;
- effective hypothesis count;
- posterior margin;
- semantic tension/covariance;
- Fisher-Rao movement;
- full source/provenance text;
- full candidate prose;
- repeated collapse policy strings.

Rule:

`SERIALIZE SUFFICIENT COORDINATES; DERIVE STATISTICS`.

## Candidate alias law

`a`,`b`,... are ephemeral/local aliases. They have no standalone semantic authority.

`#e7` must resolve them to a canonical evidence bundle containing at minimum:
- relation/task identity;
- full candidate IDs/semantic handles;
- admitted provenance/ancestry references;
- full-precision evidence-derived log-beliefs or sufficient evidence state;
- generation/causal binding required by runtime;
- optional task utility/discriminator references.

If resolution fails, H1 fails closed. Alias reuse across an unbound bundle is invalid.

## Tail law

Compression may omit alternatives only under a measured representation/value budget. If omitted posterior/value-relevant mass is non-negligible, H1 carries a tail pseudo-state, e.g.:

`h(c,"a-3|b|~-8#e7?d4!6")`

The tail has no invented factual semantics. It means only: `some admitted omitted mass remains`.

## Action is separate from collapse

H1 encodes epistemic alternatives. A runtime may choose an expected-utility action while the H1 state remains open.

`ACTION_COMMIT != EPISTEMIC_COLLAPSE`.

`!6` therefore protects fact promotion, not ordinary decision making.

## Quantization research

Candidate `delta=0.25 nat` is deliberately conservative.

Synthetic sweep used as a research discriminator only:
- binary p in 0.01..0.99: maximum absolute probability error about 0.0312, mean about 0.0106, p95 about 0.0259;
- sampled K=3..8 distributions: mean largest-component error around 0.012..0.014; mean KL below about 0.0013 in those runs.

Near ties can quantize together. The explicit reference identity preserves leader tie-breaking, but **downstream action/discriminator equivalence must still be tested**. H1 is never allowed to overwrite unquantized canonical belief state.

## Character compactness discriminator

Representative current Hyperposition-specific call sequence:

```text
let hp=hyper_new(c,"hp0")
hyper_alt(hp,"cause_a","PLAUSIBLE")
hyper_alt(hp,"cause_b","PLAUSIBLE")
hyper_discriminator(hp,"test")
collapse_guard(hp,"R6_required")
```

is approximately 161 characters.

H1:

`h(c,"a-3|b#e7?d4!6")`

is 20 characters, approximately 87.6% fewer characters for the Hyperposition-specific carrier in this example.

**Character reduction is not token reduction.** Exact token counts for the current target `Qwen/Qwen3.5-0.8B` tokenizer remain UNMEASURED. Promotion requires exact tokenizer benchmarking over held-out realistic H1 and verbose-equivalent corpora.

## Current-compatible non-authoritative carrier

For corpus/format experiments only, a currently parseable carrier could be:

`state_note(c,"H","a-3|b#e7?d4!6","COMPUTED")`

This is only a computed note. It is **not** Hyperposition runtime semantics, cannot collapse anything, and must not receive false intrinsic credit.

## Validation obligations before `h` can exist

1. lexical parser accepts only exact H1 grammar;
2. reject comments/escapes/delimiter injection/overflow/negative-zero/duplicate aliases;
3. exactly one reference;
4. bounded K and bounded integer magnitude;
5. evidence bundle exists and is generation/causal bound;
6. every alias resolves uniquely;
7. canonical reorder has identical semantic hash;
8. encode/decode/encode is canonical and idempotent;
9. fuzz tests reject malformed strings;
10. full precision bundle remains authority;
11. quantized transport cannot promote truth or effect authority;
12. exact target-tokenizer savings measured;
13. matched-budget task ablation shows no material utility/calibration regression;
14. value-directed compression beats or matches simpler top-k at equal budget before added complexity is accepted.

## H1 research hypothesis

H1 is useful only if:

`task_utility(H1) - lambda*token_cost(H1)`

exceeds the same quantity for:
- current verbose Hyperposition calls;
- no explicit Hyperposition;
- simpler top-k identifiers without logits;
- full-precision explicit probabilities.

Otherwise H1 should be rejected despite its compact appearance.