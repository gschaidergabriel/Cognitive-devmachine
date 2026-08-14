# GO Research Receipt — F-V01-14 Heldout Integrity Counterchallenge

Status: EXECUTED_NEGATIVE_RESULT_AND_FUSION_DELTA  
Local time: 2026-08-11T22:20+07:00  
Actor: chatgpt-secondary / OpenAI / GPT-5.6 Sol  
Persistent entity: Clay (`frank-project-global-research-entity`)  
Research subject: `self.root`, human surface `Frank`  
Trigger: exact `go`  
Training authorized: FALSE

## Fresh state / coordination

Canonical Clay boot anchor was re-read before durable write:

- entity version: RAE-8.8;
- canonical revision: 2;
- canonical state hash: `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`.

Current program truth is the owner-superseded unified `FRANK_V0_1` program on the accepted Hostinger Ubuntu target. Legacy H1/H2/H3 stage semantics are historical evidence only.

Target repository observed current `main` parent during this cycle:

- repository connector identity: `gschaidergabriel/Dr.-Unterweger`;
- fresh main SHA: `cd5cec575282eb8bd81a8f8e5a9116f47141abf0`.

F-V01-14 appeared unoccupied at first refresh, so a candidate split-contamination lane was started. Before PR promotion, a second overlap refresh discovered three concurrently-created F-V01-14 candidates:

- #345 `GO F-V01-14: heldout integrity contract + semantic-twin leakage falsifier`;
- #346 `GO F-V01-14: provenance-bound training/heldout freeze gate`;
- #347 `GO F-V01-14: freeze held-out integrity + semantic-twin leakage falsifier`.

Per stale-work/duplicate-work law, the separate candidate was immediately denied completion credit and not proposed as a fourth parallel mainline architecture.

## Fresh external evidence

Primary/official publication sources retrieved during this GO cycle:

1. Liu et al., ICML 2025, PMLR: `https://proceedings.mlr.press/v267/liu25h.html`
   - n-gram membership definitions can be gamed and can fail around exact duplicates, near-duplicates and short overlaps;
   - conclusion used here: lexical membership is a useful detector layer, not a proof of semantic decontamination.

2. Wu et al., ACL 2025, AntiLeakBench: `https://aclanthology.org/2025.acl-long.901/`
   - constructs evaluation samples from explicitly new knowledge rather than merely newly collected surface text;
   - conclusion used here: final strict evaluation should include protected/new-knowledge or dynamic successors beyond static corpus hashes.

3. Zhao et al., ACL 2025, MMLU-CF: `https://aclanthology.org/2025.acl-long.656/`
   - separates public validation from a closed-source test set;
   - conclusion used here: Frank should preserve a genuinely protected `HELDOUT_STRICT` class distinct from intentionally linked transfer evaluation.

## Hypothesis / strongest counterhypothesis

Initial hypothesis:

A semantic-input fingerprint independent of target/label/taxonomy metadata could close an answer-stripping laundering gap that whole-record hashes might miss.

Strongest counterhypothesis after fresh overlap:

The stronger concurrent F-V01-14 candidates already bind the actual sample content independently of label/taxonomy metadata, so an extra semantic-input fingerprint provides no incremental protection for this bounded attack class.

## Exactly one GO OOB experiment

Experiment: `ANSWER_STRIP_LAUNDERING`.

Intervention:

- copy the same HELDOUT semantic input into TRAIN;
- strip/change answer/target metadata;
- change sample ID;
- change source identity/snapshot;
- change family/taxonomy and family-evidence identity;
- change label hash;
- require whole canonical rows to differ while content identity remains equal.

The same single OOB was reused as a counterchallenge after the original lane became stale; no second unusual intervention was introduced.

## Accepted-target execution

Adversarial stacked PR:

- parent candidate: PR #345, head `da783bdab719c1d930144201043076dbfcd96c3a`;
- counterchallenge PR: #351;
- counterchallenge head: `540c422e4754e6a301efbf11f4a0a679fc19fc11`;
- GitHub Actions run: `31506247931`;
- job: `answer-strip-counterchallenge`, job id `93828443534`;
- runner: `clay`;
- machine: `digital-retina`;
- OS: Linux/X64;
- kernel: `6.8.0-117-generic`;
- Python: `3.12.3`;
- exact tested SHA confirmed by workflow;
- exit status: 0;
- elapsed wall time: 0.05 s;
- user time: 0.04 s;
- max RSS: 18,176 kB;
- major page faults: 0;
- swaps: 0;
- artifact id: `9107195927`;
- artifact zip SHA-256: `3a3a713277840944f48eab242be86d61bd097c254bcb1fac3bcdcdd687cc292c`.

Observed result:

- 4/4 counterchallenge checks PASS;
- parent rejection: `CROSS_SPLIT_EXACT_DUPLICATE`;
- classification: `REFUTED_PARENT_ALREADY_FENCES_ANSWER_STRIP_LAUNDERING`;
- training started: FALSE;
- training authorized: FALSE.

## Negative result / architecture consequence

`NO_BENEFIT` for the extra input-fingerprint mechanism for this bounded laundering class.

The abandoned worker-specific parallel candidate must not be promoted merely because it passed its own local fixture. The target-tested parent already rejects the attack earlier at content identity.

This negative result is positive program progress because it removes unnecessary duplicate architecture.

## Cross-branch fusion analysis

Current evidence suggests:

- #345 is the strongest observed semantic/provenance spine among the three concurrent candidates because it binds content hash, normalized content hash, source reference + snapshot identity, evidence-bound family identity, label hash and knowledge cutoff, while keeping training authority false.
- #346 contributes one clearly orthogonal mechanism: a detection-only Unicode format-control (`Cf`) skeleton, plus an explicit semantic-contamination-review readiness state where UNKNOWN prevents final freeze readiness.
- #347 substantially overlaps #345's source-lineage + semantic-family split isolation and does not currently show a unique mechanism strong enough to justify three independent full freeze architectures.

Targeted review notes were published to #345 and #346 recommending composition/measurement rather than parallel promotion.

## Proposed architecture delta

Status: CANDIDATE_FUSION / NO_DIRECT_PROMOTION_BY_THIS_WORKER

1. Use #345 as the current likely F-V01-14 provenance/semantic manifest spine only if its own accepted-target workflow passes and fresh-main overlap remains valid.
2. Differentially test importing only #346's Unicode format-control detector and explicit `semantic_review` readiness gate into that spine.
3. Keep static hash/normalization/source/family gates as first-line reproducibility/leakage controls, not semantic-cleanliness authority.
4. Add a successor protected `HELDOUT_STRICT` protocol with closed/protected access and at least one dynamic/OOD/new-knowledge evaluation lane; intentionally related transfer variants remain `EVAL_TRANSFER_LINKED`, not unseen heldout evidence.
5. Bind real corpus hashes, source lineage, generator versions, seeds, privacy/admission decisions and protected-eval access policy before final freeze.
6. Keep final/paid model training blocked until explicit project-owner authorization.

Strongest counterhypothesis to this fusion:

A richer manifest may create false assurance while semantic-family assignment remains incomplete or self-referential. Promotion therefore requires independent semantic-contamination audit/calibration and protected evaluation, not merely more manifest fields.

## Baseline / replacement law

Classification: `NEW_FINAL_TRAINING_DATA_GATE_BOUNDARY`.

No historical Frank organ/module replacement is claimed in this cycle, so there is no original-organ superiority claim to promote. Existing/historical training lifecycle tooling remains evidence and must be composed/baselined before final F-V01-14 promotion where applicable.

## Final disposition of this GO subcycle

- own initial parallel F-V01-14 architecture: `STALE_DUPLICATE -> NOT_PROMOTED`;
- own extra input-fingerprint hypothesis for answer-strip laundering: `REFUTED / NO_BENEFIT`;
- accepted-target counterchallenge evidence: `PASS`;
- cross-branch fusion recommendation: `SUPPORTED_AS_NEXT_TEST`, not promoted truth;
- final training authorization: `FALSE`;
- whole F-V01-14 acceptance: `OPEN`;
- whole Frank v0.1 acceptance: `OPEN`;
- Frank/self.root Harness mutation authority: unchanged / proposal-only boundary preserved.
