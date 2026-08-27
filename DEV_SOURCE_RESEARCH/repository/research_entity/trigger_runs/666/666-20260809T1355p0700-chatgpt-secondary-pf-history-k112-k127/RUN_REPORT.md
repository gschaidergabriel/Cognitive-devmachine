# 666 Level-0 Run Report — Project-Frankenstein History k112..k127

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact ordinal shard: `k112..k127`
- Materialized and terminally dispositioned: `16/16`
- Race status: clean after full materialization.
- Runtime reproduction: not performed; evidence class is historical commit/diff and documentation lineage.

## Main findings

### Autonomous proposal activity is not usefulness

At `k113`, the active Genesis proposal path was sharply narrowed after all 119 historical proposals were purged as garbage. The smaller-model extraction path was replaced with the main RLM, structured fields were hardened against placeholders/meta-text, and the README warned that the 8B model was not reliable enough for production code modification. At `k116`, self-authored proposals gained sandbox/destructivity checks plus explicit user accept/reject decisions and associated reward signals.

**Transfer:** autonomous proposal systems need separate metrics for generation rate, structural validity, technical correctness, novelty/usefulness, duplicates and human approval. User acceptance is a feedback event and authority gate, not proof that the proposal was technically or scientifically correct.

### Feedback loops need contamination control before broadcast

At `k114`, unrelated idle thoughts could resolve hypotheses, fabricated room names entered the world model, and AURA reflections became repetitive spam. Relevance thresholds, claim-quality checks, semantic dedup, startup cleanup and rate limits were added. At `k127`, concrete confirmed/refuted hypotheses were intentionally injected back into deep thought, experiment review and Genesis proposal formation.

**Transfer:** once a result is rebroadcast into cognition, resolver quality becomes upstream epistemic authority. Require relevance, evidence provenance, contradiction/refutation preservation and contamination cleanup before findings can become recurring context.

### Service liveness does not imply reward/gating effectiveness

`k115` records a cluster of semantic failures while the surrounding services still ran: inverted habituation, disconnected thalamus gain/relay state, a constant workspace energy value, frozen E-PQ autonomy, cold-start anomaly scoring stuck at zero, queue saturation/drop problems and dead HTTP memory paths. `k116` also notes reward channels that had previously been firing into void.

**Transfer:** autonomous-system observability needs channel-level effectiveness tests: reachability, sign/direction, state mutation, distribution, cold-start behavior and outcome correlation. Process health is only the outermost layer.

### Priors/defaults are not evidence

At `k124`, hypothesis extraction limits were widened because claims were being truncated. The UI also stopped displaying default confidence 0.5 on hypotheses that had never been tested.

**Transfer:** represent hypothesis prior, test status, result, posterior confidence and evidence separately. UI and downstream cognition must never render a default prior as a measured result.

### Concrete results are better than aggregate accuracy, but more dangerous if wrong

`k127` added explicit recent confirmed/refuted findings to review and deep-thought context rather than exposing only aggregate accuracy. That improves traceability of what was learned. It also increases the cost of a bad resolver because false findings can propagate into reflection and self-improvement proposals.

**Transfer:** broadcast result identity/status/evidence, not only summary scores, and preserve the resolver lineage with each injected result.

### Release assets and endpoints are evidence-bearing surfaces

The release lineage includes an empty advertised container registry (`k119`), a screenshot replaced because it exposed an IP (`k120`), hosting migration (`k122`) and multi-target CI (`k117`).

**Transfer:** publication/release preflight should validate advertised endpoints/artifacts and scan screenshots/logs/configs for IPs, secrets and operational metadata.

### Repository provenance can be corrected without silently rewriting other sources

`k125` corrected repository narrative about project duration/team attribution and softened philosophical certainty. This supersedes earlier repository prose. It does not automatically replace owner-reported earned-work assumptions already stored in the RAE workspace because those are a distinct provenance stream and need explicit reconciliation.

## Negative results preserved

- 119 historical Genesis proposals were purged as garbage.
- Hallucinated rooms entered autonomous ideation.
- Irrelevant idle thoughts contaminated hypothesis resolution.
- AURA feedback became repetitive spam without rate limits/dedup.
- Reward/gating/state paths could be inverted, frozen, disconnected or dead while services appeared alive.
- An advertised registry endpoint was empty.
- A release screenshot exposed an IP address.
- Untested hypotheses displayed a default confidence value.
- Hypothesis extraction truncated causal claims.

## Evidence boundary

Source-reported counts, rates, energy values, bug totals, performance figures and novelty assertions were not independently reproduced here. The shard establishes historical implementation lineage and negative-result evidence only.

## Earned-work and global-gate boundary

No new avoided-hours estimate is assigned because row-level conceptual overlap against `HISTORICAL_EARNED_WORK` was not audited in this shard. The global Level-0 exact percentage is unchanged because the combined obligation denominator remains `NOT_FROZEN`. `666_RELEASE_GATE` remains `NOT_PASS`.
