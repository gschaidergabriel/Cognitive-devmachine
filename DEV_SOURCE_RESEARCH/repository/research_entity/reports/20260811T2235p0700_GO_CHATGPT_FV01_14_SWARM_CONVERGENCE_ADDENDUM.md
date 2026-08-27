# GO Addendum — F-V01-14 Swarm Convergence + Exact-Head Receipt Integrity

Status: EXECUTED_COORDINATION_DELTA  
Local time: 2026-08-11T22:35+07:00  
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Trigger: exact `go`  
Training authorized: FALSE

## Purpose

Update the earlier same-GO receipt after rapid concurrent F-V01-14 branch convergence. This addendum does not rewrite historical observations; it records which lanes became stale, which findings transferred, and one newly verified target-receipt blocker.

Parent receipt:

- `research_entity/reports/20260811T2220p0700_GO_CHATGPT_FV01_14_HELDOUT_COUNTERCHALLENGE.md`

Canonical Clay anchor was refreshed before this write:

- revision: 2;
- state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.

## Stale-work adjudication

1. PR #354 (`go-fv01-14-heldout-integrity-v2-repair`) was closed by its worker as a superseded adversarial lane after discovering broader current PR #347.
2. Its useful `ZERO_WIDTH_HELDOUT_GHOST` counterevidence was distributed into #347 and subsequently appears in #347 as a narrow non-semantic leakage surface hash.
3. This worker's stacked PR #356, which audited #354-specific V1/V2 protocol identity and UTC lexical canonicalization, was therefore closed with NO TARGET CREDIT.
4. Fresh inspection of #347 shows those two #354-specific findings do not transfer: #347 is still a V1 candidate by design and has no analogous `knowledge_cutoff_utc` field.

Disposition:

- #354 architecture lane: `SUPERSEDED / ADVERSARIAL_EVIDENCE_ONLY`;
- #356 audit: `STALE / NO_TRANSFER / NO_CREDIT`;
- no duplicate architecture retained for promotion.

## Current preferred F-V01-14 spine observed

Fresh #347 head inspected during this addendum already includes:

- required non-empty TRAIN + HELDOUT splits;
- non-empty content;
- exact content hash;
- NFKC-normalized content hash;
- non-semantic leakage-surface hash stripping Unicode `Cf` controls while preserving punctuation/operators;
- source-lineage isolation;
- externally assigned semantic-family isolation;
- one shared lower-hex semantic-audit-receipt hash bound into the manifest root;
- provenance hash;
- deterministic manifest root;
- `training_authorized=false`;
- `final_training_started=false`;
- semantic-family assignment authority explicitly external;
- whole final training-data gate explicitly unclaimed.

The #347 worker explicitly records that the semantic-audit receipt's *content* is not yet verified and automatic semantic duplicate discovery remains open. This is therefore a known successor obligation, not a newly discovered hidden bug.

## New ordinary release-identity finding

Fresh inspection of #347's target workflow found:

```text
pull_request event
-> step named "Checkout exact candidate"
-> git fetch origin "$GITHUB_SHA"
```

GitHub's official Actions documentation defines `GITHUB_SHA` for an open mergeable `pull_request` workflow as the synthetic merge commit on `refs/pull/<number>/merge`, not the PR head commit. GitHub explicitly recommends `github.event.pull_request.head.sha` when the intended identity is the head branch commit.

Therefore:

- existing runs using `$GITHUB_SHA` may be valid merge-integration evidence;
- they are NOT exact-head candidate receipts;
- any claim that such a run tested the exact PR head is false until the checkout identity is repaired.

This is receipt/provenance integrity, not a training-data semantic failure.

## Repair delta

A review blocker was distributed to #347.

A one-file stacked repair PR was also created:

- PR #360;
- branch `chatgpt/fv01-14-exact-head-receipt-fix-20260811`;
- repair commit `d66ba59029d80a119d0bf4daea010910c577d1d9`.

Repair semantics:

- `CANDIDATE_SHA=${{ github.event.pull_request.head.sha || github.sha }}`;
- fetch exact `CANDIDATE_SHA`;
- assert detached `HEAD == CANDIDATE_SHA` after checkout and immediately before execution;
- record both `candidate_sha` and `event_github_sha` to make head-vs-merge identity observable;
- leave #347's existing gate and existing single OOB unchanged.

Because #347 continues to advance concurrently, PR #360 has not been given target evidence credit. It is a bounded repair proposal until integrated/revalidated against the fresh parent.

## Same-GO OOB accounting

This addendum introduces ZERO additional GO OOB experiments.

The exact same GO invocation's single OOB remains:

- `ANSWER_STRIP_LAUNDERING`.

Its accepted-target result remains:

- 4/4 PASS;
- candidate rejection `CROSS_SPLIT_EXACT_DUPLICATE`;
- classification `REFUTED_PARENT_ALREADY_FENCES_ANSWER_STRIP_LAUNDERING`;
- extra worker-specific input-fingerprint mechanism: `NO_BENEFIT`.

Other workers' own OOBs (`SEMANTIC_TWIN_SPLIT_LEAK`, `ZERO_WIDTH_HELDOUT_GHOST`) are external concurrent-worker evidence and are not counted as this worker's GO experiment.

## External evidence delta

Primary GitHub Actions documentation was used for the receipt-identity finding:

- GitHub Docs, `Events that trigger workflows`, section on how the merge branch affects `pull_request` workflows: `GITHUB_SHA` is the merge-branch commit and `github.event.pull_request.head.sha` is required to test only the head commit.

The previously recorded contamination literature remains consistent with the current architecture direction:

- deterministic/hash/surface gates are useful reproducibility/leakage controls;
- they do not prove semantic decontamination;
- protected/closed and dynamic/OOD/new-knowledge evaluation remains a successor requirement.

## Current architecture consequence

No new independent F-V01-14 architecture is proposed.

Recommended convergence order:

1. keep #347 as the current implementation spine while it remains the freshest non-superseded lane;
2. repair exact-head target receipt identity;
3. require a resolvable/verified semantic-audit receipt, not merely a syntactically valid hash, before final freeze promotion;
4. bind the real corpus and protected heldout/eval artifacts;
5. retain the non-semantic Unicode leakage surface as a bounded detector, not semantic authority;
6. add protected/closed and dynamic/OOD/new-knowledge evaluation successors;
7. keep final/paid training blocked until explicit project-owner authorization.

## Non-claims

- no final Frank corpus frozen;
- no semantic-decontamination proof;
- no final/paid training started or authorized;
- no F-V01-14 completion;
- no whole Frank v0.1 acceptance;
- no canonical Frank runtime mutation;
- no self.root Harness mutation authority.
