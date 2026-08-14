# CCW-001 durable architecture delta

Status: `NO_NEW_RUNTIME_ARCHITECTURE / RETAINED_TEST_AND_SEMANTIC_LAW`

CCW-001 is not promoted as a new physical runtime architecture. The strongest conventional persisted-receipt baseline matched its encoded closure correctness and atomic recovery while materially outperforming derived-view terminal reads.

The run nevertheless leaves one durable Frank v0.1 obligation:

**A persisted terminal DONE receipt is not sufficient semantic authority.**

For any consequential use of terminal closure, Frank must be able to re-establish an exact canonical support chain equivalent to:

`admitted execution generation -> GWT episode + reconstructed/used receiver path -> exact verified effect outcome -> non-correlated causal credit targeting that effect -> admitted semantic delta OR explicit typed no-learning -> provenance-bound re-entry`.

A fast persisted DONE receipt/cache may remain for performance and audit, provided:

1. it cannot create effect authority;
2. its source support identity/hash/epoch is recorded;
3. verifier/recovery can revalidate it against canonical support;
4. invalid/quarantined support makes the cache insufficient even if the historical row remains;
5. recovery never retries the external effect merely because causal closure became invalid;
6. verified provider outcome evidence remains durable independently of learning/re-entry validity;
7. the conventional target repair in PR279/PR280 is reused rather than duplicated.

## Required test obligation

Extend the eventual V17 promotion gate with a post-terminal support-invalidity/quarantine control. The test should prove that a historical DONE receipt alone cannot make the verifier/recovery report causally closed when one required canonical support witness is no longer valid/current. The correct response must preserve verified external outcome while moving causal/re-entry status to explicit review/rebuild/invalid state without minting retry authority.

This is a test/semantic obligation, not authorization to mutate the current target from this ATOMIC branch.
