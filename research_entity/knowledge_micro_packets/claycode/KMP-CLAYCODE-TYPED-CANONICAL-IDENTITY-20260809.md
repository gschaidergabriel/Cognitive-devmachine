# KMP-CLAYCODE-TYPED-CANONICAL-IDENTITY-20260809

- packet_id: `KMP-CLAYCODE-TYPED-CANONICAL-IDENTITY-20260809`
- domains: `claycode`, `claygraph`, `unifieddb`, `frank`, `harness`
- epistemic_class: `EXECUTABLE_RESEARCH_RESULT`
- status_hint: `OPEN_REFINED`
- origin_actor: `chatgpt-secondary`
- provider/model: `OpenAI / GPT-5.6 Sol`

## Atomic result

ClayCode semantic canonicalization must be type-directed: explicit `Set` fields may normalize member order and duplicates, while `Ordered`/list/role/path/effect-lifecycle structure must preserve order. Runtime capability/resource instance identity should remain separate from stable semantic and generated-artifact identity and be bound in deployment/execution receipts.

## Evidence

- `research_entity/trigger_runs/claycode/claycode_20260809T1606p0700_chatgpt_semhash_typedcanon/EXECUTABLE_RESEARCH_RECEIPT.json`
- `research_entity/trigger_runs/claycode/claycode_20260809T1606p0700_chatgpt_semhash_typedcanon/HYPOTHESIS_MATRIX.json`
- concurrent HTTP v1 target-hash counterexample in `claycode_20260809T1607p0700_chatgpt_http_app02`

## Key measurements

- Set equivalence: 20,000/20,000 preserved semantic hash.
- Ordered mutations: 20,000/20,000 changed semantic hash.
- Semantic mutations: 50,000/50,000 changed semantic hash.
- Schema-blind sorter collided forward/reversed ordered lifecycle.
- 10,000 embedded authority instances yielded 10,000 artifact hashes; runtime-handle binding yielded one stable artifact hash while retaining 10,000 deployment identities.

## Falsifier / next test

Production parser + typed IR + canonicalizer + evaluator/replay across the complete G9/dialect corpus and H1/H2 traces shows the proposed identity separation loses required semantics, prevents correct security binding or materially worsens reproducibility/repair cost.

## Promotion boundary

Candidate/research result only. No CURRENT ClayCode, canonical revision or BASE work-package promotion follows from this packet alone.
