# Harness Deep Fusion Report — Frank × Needle

Run: `harness-20260809T1854p0700-chatgpt-secondary-needle-fusion`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol, temporary organ of Clay  
Subject: Frank H-WP-04 Needle boundary  
Canonical parent: `r2 · 04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Result

`COMPLETE_DEEP_COMPONENT / H-WP-04 REMAINS OPEN`

This run turned the previous Needle adapter into a much deeper executable and researched boundary. It combined:

- exact Drive-source execution;
- Git provenance archaeology;
- current upstream Needle source comparison;
- current Cactus runtime inspection;
- deterministic and adversarial sandbox tests;
- generated mutation campaigns;
- tool-registry retrieval diagnostics;
- hypothesis/counterhypothesis generation;
- primary web research across structured decoding, tool retrieval, multilingual tool use, confidence/abstention, multi-turn tool use, benchmark label quality and action safety;
- architecture fusion;
- explicit feedback to every affected Clay research branch.

No official Needle semantic-quality claim was promoted because the pinned model/tokenizer binaries could not be mounted into this isolated sandbox.

## 1. Exact source/provenance result

The connected Drive copy is not an unknown fork.

Drive `.git` archaeology established:

- origin: `https://github.com/cactus-compute/needle.git`;
- branch: `main`;
- checkout commit: `6fdddb874dd6f46dabeea88d0bf239fc4a2474c4`.

Comparing that commit with current upstream `main` found only one later commit, changing `README.md` and adding `setup.bat`. The inspected model/training/tokenizer/constraint source did not change.

The Drive Git index also proves why full inference was unavailable here: checkpoint/tokenizer binaries were never tracked in that checkout. They are externally downloaded artifacts.

Pinned official artifact identities are recorded in `NEEDLE_UPSTREAM_PIN_20260809.json`, including:

- `needle.pkl`: 52,633,098 bytes, SHA256 `40a32e91d1d4197bf15ba559b74f6727c342dc8746918742fc7d8e2c1f18df40`;
- `tokenizer/needle.model`: 124,960 bytes, SHA256 `0823f5b9133c68a8140addc5d7a425fa9119c4c8cb4a550363b4bffa4ba1c8c7`.

Direct container download was denied by the sandbox backend. Model size is not the blocker.

## 2. Model architecture consistency

Static source-derived parameter count for current Needle configuration:

`26,315,421 trainable parameters`.

At BF16 that is `52,630,842` raw parameter bytes. The official `needle.pkl` is only 2,256 bytes larger, strongly consistent with the advertised ~26M architecture plus container/config overhead.

This validates size/shape plausibility, not inference quality.

## 3. The strongest implementation result: Frank-level fail-closed boundary

The run now provides executable H1 components:

- `needle_runtime_contract.py` v0.4;
- `needle_runtime_profiles.py` for JAX/Python and Cactus/C++;
- `needle_ingress_preflight.py`;
- 51-tool frozen Frank fixture;
- corresponding tests.

### Ingress preflight

Needle is invoked only when:

- current intent is non-empty and explicitly context-resolved;
- selected toolset exists;
- retrieval, if used, succeeded;
- complete query + complete selected tool catalogue fit the encoder budget with frozen reserve.

Failure at any precondition requires fallback rather than upstream fail-open/truncation behavior.

### Runtime identity

A model receipt must bind:

- runtime profile/source identity;
- checkpoint hash;
- tokenizer hash;
- exact selected toolset hash.

`Needle latest` or a display name is not sufficient provenance.

### Strict output validation

The validator rejects:

- malformed/non-list output;
- duplicate JSON keys;
- NaN/Infinity/non-finite decoded numbers;
- unoffered/blocked tools;
- unknown/missing/type-invalid arguments;
- extra call fields;
- alias/normalization collisions;
- more than one Frank Needle call.

It performs reverse aliases only after strict structured parsing, so argument values are not rewritten by string substitution.

### Frank single-shot/fallback semantics

Project-source fusion confirms:

- Needle is a single-shot tool reflex;
- multi-step planning belongs to the 4B path;
- `[]` means 4B fallback, never silent completion;
- invalid/multi-call output means fallback;
- accepted single route remains `authority=NONE`, `effect_eligible=false`, external effect gate required.

This is now explicit in `NeedleDecisionReceipt.fallback_required` and fixed `FRANK_MAX_NEEDLE_CALLS = 1`.

## 4. Executed test depth

Latest committed component batch:

- runtime contract + runtime profiles: `43/43 PASS`;
- ingress preflight: `8/8 PASS`;
- combined latest unit/adversarial tests: `51/51 PASS`.

Generated structural mutation campaigns across this run total `295,000` cases. The fresh v0.4 campaign used 25,000 valid and 25,000 invalid cases with `0 false accepts` and `0 false rejects` in its generated domain. Earlier campaigns included Unicode, escapes, duplicate-key attacks and malformed/adversarial outputs.

This is strong component evidence. It is not semantic tool-routing evidence.

## 5. Current upstream Needle Python/JAX counterexamples

Direct source execution/inspection established:

1. `constrained.py` documents `parameters.properties` extraction but iterates direct `parameters`; ordinary OpenAI JSON Schema requires adapter flattening.
2. constraint state activates only on exact compact markers. Of 16 legal whitespace variants around the name marker, only 1 constrained; of 64 argument-marker variants, only 1 constrained.
3. multiple constraint states fail open to original logits.
4. encoder tool-token stream can be blindly sliced when over budget.
5. snake-case normalization can silently collapse distinct tool names.
6. invalid-JSON reverse alias fallback can replace alias text inside argument values.
7. contrastive retrieval excludes no-tool examples.
8. contrastive loss runs only every 1000 text-training steps in the inspected training loop.
9. stock finetune quick evaluation/best-checkpoint selection does not protect no-tool quality.
10. current Python checkpoint loader uses pickle.

These findings are persisted with source identity in `UPSTREAM_EXECUTABLE_COUNTEREXAMPLES.md`.

## 6. Historical correction: the old anti-top-k argument was overstated

The Aug-4 handover argued that Needle learned roughly `600 queries × 51 tools` contrastively, suggesting every query directly saw the full tool inventory as contrastive supervision.

Exact code shows instead:

- each contrastive query gets one randomly selected positive tool;
- negatives are other paired tools in the contrastive batch;
- no-tool queries are excluded from those batches.

Under documented/default `mini_alle` arithmetic (~600 training examples, batch 64, one epoch), the run would have about 9 steps while contrastive loss activates every 1000 steps. If defaults were used, the Frank mini-finetune performed zero contrastive updates.

The exact historical CLI/log remains unrecovered, so the zero-update statement is conditional on those defaults. The old `all 51 tools per query` rationale itself is corrected by code.

This reopens retrieval as an experiment; it does not promote top-k.

## 7. Current Cactus runtime differential

Cactus is not identical to the Python path.

### Improvement over Python

Cactus intentionally converts standard JSON Schema into the flat parameter map expected by Needle, so the Python `parameters.properties` mismatch must not be generalized to all runtimes.

### Separate Cactus weaknesses

Current Cactus source also exposed:

- string-pattern-based schema extraction sensitive to ordinary JSON whitespace/escaping;
- the same compact-marker Needle constraint-state weakness;
- syntax validation that accepts duplicate keys;
- no sufficient Frank-level guarantee of offered-tool membership/required keys from the Needle parser/constrainer alone;
- Tool RAG fail-open-to-all behavior on retrieval failure;
- generic confidence rather than proven Needle correctness calibration;
- single-shot query formatting that uses system/developer text plus only the latest user message.

Therefore Frank cannot delegate its acceptance/authority boundary to either runtime implementation.

## 8. Dialogue/context result

Current Cactus source confirms that Needle does not receive ordinary multi-turn conversation history. Earlier user/assistant/tool turns are not Needle dialogue memory.

That aligns with Frank's own concept: phrases such as `das von vorhin` or `mach weiter` are context-suspicious and must go to the 4B path unless an external normalizer first resolves them into a self-contained current intent.

The new `NeedleIngressPreflight` records that requirement rather than attempting a brittle hard-coded phrase detector.

## 9. Encoder-budget correction

The historical minimal catalogue figure was 793 Needle tokens. The later zero-shot gate also asks for at least 200 tokens of headroom.

Arithmetic:

`1024 - 793 - 1(<tools>) - 200 = 30 query tokens`.

So `the 51-tool catalogue fits` and `the catalogue fits with 200-token reserve for normal queries` are different claims. The new preflight passes at 30 and rejects at 31 query tokens under this historical catalogue assumption.

Exact distributional measurement still requires the official tokenizer.

## 10. Retrieval fusion: promising, not promoted

Two plausible prefilter families remain:

- Needle's own contrastive retrieval head;
- Cactus hybrid Tool RAG (embedding + BM25 + weighted RRF).

Cactus Tool RAG is concrete production code, but its BM25 lexical tokenizer is byte/ASCII oriented. In current Frank German descriptions:

- 945 content words inspected;
- 65 non-ASCII words (~6.9%) are altered;
- terms such as `für`/`größe` can disappear from the lexical arm.

A small deterministic 27-query BM25 diagnostic gave:

- current Cactus-like lexical arm: top-1 16/27, top-5 22/27;
- Unicode-aware lexical arm: top-1 17/27, top-5 22/27.

Therefore the Unicode defect is real, but fixing it alone showed only modest benefit in this tiny lexical-only probe.

### Tool descriptions matter

Same diagnostic:

- names only: top-1 7/27, top-5 9/27;
- name + full description: top-1 16/27, top-5 22/27.

Descriptions carry real signal. Blind removal is not supported.

A candidate first-statement compression reduced retrieval text from 7,207 to 5,052 bytes (~29.9%) while preserving 22/27 top-5 in this small lexical diagnostic. This is a useful experimental arm, not proof of end-to-end Needle behavior.

### `crl_session`

Drive sources resolve CRL as `Consciousness Research Loop`, a weekly Claude-Code research session. A descriptive Needle-only alias such as `run_weekly_research_session` improved one targeted English lexical probe from rank 2 to rank 1, but effects were small/local. It remains A/B-only.

## 11. Confidence/abstention fusion

Cactus exposes generic confidence/fallback machinery, but the normal path derives a confidence-like value from entropy unless a specialized wrongness/handoff probe exists.

Calibration literature independently warns that raw confidence/logits are not automatically correctness probabilities.

Frank should therefore log candidate confidence surfaces — preferably pre-constraint scores too — and choose an abstention threshold only from held-out risk-coverage calibration on the audited German set.

No default `0.7` or any other threshold is promoted.

## 12. Evaluation quality result

The project-local 328-case report already documents incorrect reference labels. Upstream Needle finetune evaluation additionally has a no-tool blind spot.

Therefore a 90% semantic gate is only meaningful after:

- a versioned/audited gold set;
- disagreement ledger;
- explicit no-tool precision/recall/false-trigger metrics;
- paired evaluation across the same corrected cases.

Structure can be hardened deterministically; semantic routing still needs a clean measurement substrate.

## 13. Architecture overlay returned to Frank research

`NEEDLE_H1_ARCHITECTURE_OVERLAY.json` freezes only evidence-supported boundary laws:

`dialogue/current input -> external context/intent normalizer -> NeedleIngressPreflight -> runtime-profile canonicalization -> optional audited retrieval -> pinned unchanged Needle -> strict independent validator -> NeedleDecisionReceipt -> typed Clay ingress -> independent effect authority`

Frozen:

- single-shot;
- context-resolution preflight;
- complete encoder-budget preflight;
- pinned runtime/model/tokenizer/toolset provenance;
- strict validation;
- no-tool/rejected fallback;
- zero Needle execution authority.

Not frozen:

- retriever family;
- top-k;
- description compression;
- CRL alias;
- confidence surface/threshold.

## 14. Branch feedback

Explicit feedback is recorded in `BRANCH_FEEDBACK_MANIFEST.json` for:

- Frank — adopt typed boundary overlay;
- ClayCode — H2 type/effect/provenance expressibility requirement;
- UnifiedDB — receipt/replay persistence fields;
- ClayGraph — diagnostic causal/provenance edges only;
- GWT — distinguish validated route vs fallback uptake without promoting confidence to truth;
- Hyperposition — preserve competing retrieval/confidence/description alternatives;
- Harness — retain all executable components, H-WP-04 remains open;
- Emergenz / ClayResearch — no emergence claim and no fixed-target change.

## 15. Highest-information next executable work

The next decisive step is no longer another abstract architecture discussion.

Mount into the Ubuntu/reference lane:

1. official pinned `tokenizer/needle.model`;
2. official pinned JAX checkpoint and/or Cactus CQ4 bundle;
3. audited/versioned German tool/no-tool cases.

Then execute, in order:

1. exact query/catalogue token distributions and 200-headroom failure rate;
2. unchanged official Needle German zero-shot baseline;
3. runtime differential JAX vs Cactus, later ONNX if available;
4. full catalogue vs retrieval k={2,4,8,12,16,24};
5. full vs compressed/bilingual descriptions;
6. Frank names vs deterministic English aliases and CRL A/B;
7. constrained vs unconstrained generation, always with the strict post-validator;
8. confidence calibration/risk-coverage;
9. no-tool and context-dependent fallback suite;
10. end-to-end `NeedleDecisionReceipt -> ClayIngressEnvelope -> external effect gate` replay on target Ubuntu.

Only those measurements can close H-WP-04 honestly.

## Final epistemic state

### Confirmed/implemented

- strict outer validation/fallback/provenance architecture;
- project single-shot/no-tool/context fallback semantics;
- current Python and Cactus source counterexamples;
- exact source provenance/history equivalence;
- evaluation no-tool blind spot;
- historical contrastive-rationale correction;
- encoder-budget arithmetic conflict;
- current 51-tool deterministic component behavior.

### Strong candidates, not promoted

- retrieval before generation;
- first-statement description compression;
- bilingual/English retrieval text;
- CRL descriptive alias;
- calibrated selective abstention;
- JAX/Cactus/ONNX differential runtime strategy.

### Still unknown

- actual official-checkpoint German zero-shot accuracy;
- exact official-tokenizer catalogue/query distribution;
- retrieval recall/accuracy on corrected Frank cases;
- calibrated confidence threshold;
- target-Ubuntu latency and end-to-end reliability.

The run therefore materially reduces architectural uncertainty without pretending that unavailable model execution happened.
