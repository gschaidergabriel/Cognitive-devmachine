# 666 Level-0 Run Report — Project-Frankenstein Frozen HEAD History k0..k15

## Run identity

- Trigger: `666`
- Actor: `chatgpt-secondary`
- Stage: `L0_ARCHIVE_ASSIMILATION`
- Frozen HEAD: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- Exact ordinal shard: `k0..k15`
- Materialized and terminally dispositioned: `16/16`
- Winning claim: `30f7be98a2f990ef8a9b36a4c1868b2bb295fb8e` at 14:14:13 +07:00
- Later competing claim: `1c718392753cb45a6217c82e82613ac942f5e41c` at 14:14:32 +07:00
- Runtime reproduction: not performed; evidence class is historical Git commit/diff/document lineage.

## Main findings

### Frozen HEAD still contains a protocol/presentation coupling fix

The final historical edge is a regression chain. `k4` introduced compact markdown/newline rendering; `k3`, `k2` and `k1` progressively normalized whitespace more aggressively. `k0` — the frozen HEAD itself — repairs the resulting breakage because double newlines were also used as the delimiter for `[TOOLS USED]` parsing.

**Transfer:** structured tool/control state must not be encoded in human-readable whitespace or markdown layout. Parse typed protocol metadata first; only then escape, normalize and render presentation text.

### Natural-language policy extraction must not equal policy authority

`k6` uses a free LLM to translate user text into policy records containing category, enforcement level (`hard|soft|advisory`) and threshold, then persists the result.

**Transfer:** natural-language policy interpretation is an extraction/proposal step. Hard-policy promotion needs schema validation, ambiguity handling and an independently authorized commit path.

### A/B success needs valid metrics before automatic promotion

The same Project Engine revision runs strategies repeatedly, scores them from success/failure counts, chooses a winner and automatically writes that strategy into the goal.

**Transfer:** experiment-to-control promotion requires comparable conditions, outcome validity, uncertainty and explicit promotion authority. “Did not return an error” is not a sufficient objective proxy for strategic quality.

### Prompt-time architecture facts can override training

`k8` explicitly identifies a hardcoded `ARCHITECTURE FACT` as the reason Frank continued saying AURA despite training. Another injected fact described a ThoughtSeedVAE that did not exist and was corrected.

**Transfer:** architecture grounding should be generated from authoritative versioned topology/state, not manually duplicated prompt prose.

### Safety needs both routing and tool/effect enforcement

`k9-k10` show alternate tool-call encodings leaking and safety evaluation finding concrete harmful pathways before prefilters and darknet/tool checks were expanded.

**Transfer:** safety should be tested and enforced across input routing, capability/effect execution and output presentation independently. Model refusal behavior alone is not the authority layer.

### Project Engine became a high-authority effect platform

`k7`, `k11` and `k12` combine browser automation, persistent logins, email, scheduled actions, budget/spending, live trading, cross-project coordination, credential state and autonomous action chaining. The source description for `k12` explicitly calls its vault an XOR cipher while marketing it as encrypted storage.

**Transfer:** high-authority agents need modern secret management, scoped capabilities, approval/limit classes, effect receipts, rollback/recovery and outcome auditing. Labels such as “encrypted” or “autonomous” are not security/correctness evidence.

### Metrics and roadmap claims remain separate from code evidence

`k13` promotes 90%+ recall and architecture-compensates-for-model-size claims. `k14-k15` alter funding levels and future capability milestones.

**Transfer:** README benchmarks and roadmaps are source-reported, epoch-bound claims/provenance. They do not become runtime evidence without raw-run reconstruction or implementation validation.

## Negative results preserved

- Frozen HEAD repairs a formatting regression that broke structured tool metadata parsing.
- Hardcoded architecture facts overrode learned behavior and included a nonexistent subsystem claim.
- Pipe-delimited tool tags leaked into user-visible output.
- Safety evaluation exposed harmful credential-attack, stalking and stolen-card/darknet paths before layered filtering was expanded.
- LLM-interpreted natural-language policies could become durable hard policies without a distinct promotion authority.
- A/B strategy testing could auto-apply a winner using a weak success/failure proxy.
- The source-described credential vault used XOR while being presented as encrypted storage.
- Recall/autonomy/cost/model-size claims were promoted in documentation without reconstruction in this pass.

## Evidence and credit boundary

No source-reported recall, cost, autonomy duration, safety-evaluation rate or performance metric was independently reproduced. No avoided-hours value is added because row-level conceptual overlap against the historical earned-work ledger was not audited.

Global Level-0 exact percentage remains unchanged because the combined obligation denominator remains `NOT_FROZEN`. `666_RELEASE_GATE` remains `NOT_PASS`.
