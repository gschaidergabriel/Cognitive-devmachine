# FINAL REPORT ADDENDUM — 666 New Drive Data Expansion

Run: `666-20260809T0431p0700-chatgpt-secondary`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: `r2` / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

This addendum records Level-0 work discovered after the initial Retina/LCME/adapter report while traversing the newly accessible extracted Drive tree.

## 1. New source classes actually found

The newly exposed Drive data is not just more prose. It contains at least these materially distinct source classes outside the frozen 655-document concept submanifest:

- `digital-retina` and `digital-retina-e2e`: implementation/evaluation trees;
- `titan-memory`: LCME source/tests/benchmarks;
- `frank-werkzeuge/genesis-monitor`: raw runtime trajectories plus failure reports;
- `frank-werkzeuge/healing-log.md`: long runtime failure/fix atlas;
- `frank-adapter-sicherung`: physical LoRA adapter artifacts/configuration;
- `synteq-umbau`: historical multiagent/XENO/measurement runtime and persistent Bausteine snapshot;
- `aicore`: a later runtime/training tree that is provably not byte-identical to the frozen Project-Frankenstein head;
- `frank-projects`: 14 application/use-case project directories;
- `frank-demo`: historical static/Vercel demo assets;
- `frank-library`: empty at direct root when inspected.

The frozen concept index remains useful but cannot be the whole-Drive denominator.

## 2. Digital Retina measurement archaeology

Recovered historical measurements must remain protocol-bound:

- May-20 held-out phrase protocol: 82.4% at tau=0.22 over 47 images / 1196 phrases; reported realistic-FPR lower bound 68.8%;
- May-26 Tier-3 strict text: 35.3% hard / 47.5% easy;
- June-9 after phrase-emission optimization: 87.1% strict tuned-hard and 70.0% strict independent Freshset; CLIP-lenient 94.6% / 92.5% but strongly threshold-sensitive.

Historical failure families include art/AI object errors, vocabulary gaps, stylized OCR failure, compositional-binding gaps and a Region-BLIP case where an additional stage worsened semantic reliability through hallucination.

Current implication: `VisualPercept` acceptance must bind exact dataset, threshold, match semantics, tuning ancestry, stage provenance and uncertainty. Weak-signal coverage is not interchangeable with semantic correctness.

## 3. Genesis raw dynamics: a direct anti-Goodhart fixture

A raw 28-minute monitor trace was downloaded and parsed. It contains 15 records, SHA-256:

`6811fed4e313eb7e2fb3225ce755cb83b1378cb21afa937edd561d7e85bd6a52`

Observed deltas:

- population 99 -> 100;
- +349 births / +348 deaths;
- +409 mutations;
- 0 fusions;
- 0 additional crystals;
- average fitness 0.2721 -> 0.3709;
- emotion spread 0.0000 -> 0.3223;
- final approach mix strongly dominated by caching (51%).

This is high-value historical evidence that internal activity, diversity proxies and fitness can improve while the intended output path remains completely dead. It becomes an emergence/Harness anti-Goodhart trajectory fixture, not consciousness evidence.

The healing log adds threshold-reachability, startup-grace, orphan/singleton, cumulative-state, sign-math and semantic-readiness failures. Generic safety/concurrency lessons were deduplicated against earlier receipts.

## 4. Synteq coordination archaeology and live-CLI falsifier

`RAHMEN.md` asserted that Claude background agents could be started/addressed with `--bg -p` and `--resume <id> -p`. A later measured `MELDUNGEN.md` run contradicts that design assumption: `--bg` and `--print` conflict, running background agents reject `--resume <uuid> -p`, and `--fork-session` creates a copy rather than messaging the running agent.

This is primary historical evidence for the current repo-native research-center design: durable Git events, pulses, leases and handoffs must remain the shared coordination truth instead of depending on assumed direct live-session messaging.

A recovered `bausteine.db.sql` snapshot hashes to:

`a0aab0a89ef348a035fbaff2220920dd86f81ccc4435c11f7dc44f4c8c76b26c`

and contains 17 versioned Baustein rows, 231 usage rows, 2 voice rows and 56 recorded moves. It preserves machine-language/GWT/cache/ablation lineage as stateful historical evidence.

A sibling worker independently integrated the higher-value structured-source/projection/package/telemetry part of the same Aug-6 branch as `HEW-DRIVE-SYNTEQ-010` (7h center provisional), so this run adds zero duplicate hours for overlapping Synteq mechanisms.

## 5. Drive aicore is a distinct later runtime lineage

The extracted `aicore` tree contains services/router/training/model/runtime/UI/etc. It must not be treated as a duplicate mirror of Project-Frankenstein.

Same-path proof for `router/app.py`:

- Drive modified: 2026-08-04T13:28:32Z;
- Drive size: 21,155 bytes;
- Drive SHA-256: `cc06366c2784c22289a2a530c521ec70703bc0cc3065d6733576c5f6237749fa`;
- Drive Git-blob SHA-1: `04c70818bb46e525809b7a5c1e08fff4751b3fef`;
- frozen Project-Frankenstein GitHub blob SHA-1 at `abba90a...`: `601b4aa067a7505bef0f2f5ba91cd0e09e97a713`.

Therefore byte identity is false. Exact Level-0 reconciliation needs recursive path/hash clustering across GitHub head/history, rescue copies and the later Drive runtime tree.

## 6. v27 training lineage

The later `aicore/training/v27` branch supplies concrete data-quality history:

- v27 report: 3,785 total training lines;
- 1,449-example recast distributed exactly over seven behavioral response classes;
- 4,261 generated candidates rejected by explicit gate rules;
- explicit tool tags in recast answers reduced 4,180 -> 0;
- system text still contained tool/marker syntax because declaration/runtime knowledge was intentionally distinct from answer behavior.

A later audit corrected a dangerous validator interpretation: `intent` and `hypothesis` were absent from the external tool registry but were live internal marker tags consumed by runtime components. Removing them as 'dead tools' would have broken those subsystems. Current implication: internal cognitive markers, declarative tool descriptions and external effect authority require distinct typed namespaces; syntax resemblance is not capability authority.

The same lineage records:

- automatic classifier first achieved only about 15-16/30 manual agreement;
- after fixing named systematic errors it reached 29/30 on a fresh hand sample, with a residual `when`-clause error class;
- blind evaluation initially observed a growing sample (57 then 140 lines) and explicitly froze SHA-256 `e0bd070308f09f08ef7161dec8b9cefeed7783d8c8cd068c6ce66a759669afb2` before continuing;
- dataset-only prompt cleanup was rejected because runtime prompts would remain different, recreating train-inference drift.

These become final training-data/Harness oracles. No training was started.

## 7. Application corpus classification

`frank-projects` contains 14 direct project folders. Sampling shows why project existence cannot be mistaken for compiler evidence:

- `grazcamperfinder`: architecture/spec/status, no sampled execution receipt;
- `ai-research-agent`: sampled code path only exposed a small `hello.py`;
- `video-launch-page`: real static frontend/deployment assets, but static HTML cannot satisfy the ClayCode contract's mandatory real HTTP/backend application proof.

The corpus is valuable for ordinary-application requirement discovery. It receives zero APP proof credit until exact source/dependency/compile/execute/expected-vs-observed receipts exist.

## 8. Crossread and earned-work accounting

The live shared workspace was reread during this run. Peer work had already materialized:

- Project-Frankenstein state/safety/LCME/XENO/model shards;
- Drive XENO/Thalamus index;
- Drive recovery/IdentityForge;
- Drive audit oracles;
- Drive Synteq projection/measurement shard.

Shared materialized provisional avoided-work total at final pulse: `84h center` (32 low / 168 high), still not global completion credit.

This run created additional *unapplied* unique candidates:

- Digital Retina historical fixture reuse: 5h center candidate;
- Genesis raw dynamics fixture reuse: 3h center candidate;
- v27 training/data-quality reuse: 4h center candidate.

Total new candidate center = 12h, deliberately not added to the shared total in this worker because final row/mechanism dedup and single-writer materialization remain required.

## 9. Level-0 gate state

`666_RELEASE_GATE` remains `NOT_PASS`.

Strict exact progress remains 0% because the whole-source atomic denominator is not frozen. This does **not** mean no work was done. It means exact percentage is forbidden until:

1. whole Drive recursive code/database/model/binary/nonsemantic inventory is frozen;
2. Drive aicore vs GitHub/history/rescue path/hash/version reconciliation is frozen;
3. Project-Frankenstein full relevant history denominator is frozen;
4. every obligation is analyzed/integrated or has an explicit no-delta receipt;
5. cross-source reconciliation and branch feedback are audited.

The former >100 MiB raw-tarball connector limit is no longer a semantic traversal blocker because the extracted Drive tree is accessible. The raw tarball remains a provenance/reconciliation obligation.

## 10. Durable artifacts from this run

- `research_entity/archive_assimilation/receipts/666_20260809T0431p0700_chatgpt_secondary_drive_retina_lcme_adapter_shard.json`
- `research_entity/archive_assimilation/receipts/666_20260809T0431p0700_chatgpt_secondary_drive_genesis_healing_shard.json`
- `research_entity/archive_assimilation/receipts/666_20260809T0431p0700_chatgpt_secondary_drive_synteq_coordination_shard.json`
- `research_entity/archive_assimilation/receipts/666_20260809T0431p0700_chatgpt_secondary_drive_runtime_inventory_classification.json`
- `research_entity/archive_assimilation/receipts/666_20260809T0431p0700_chatgpt_secondary_drive_aicore_v27_training_shard.json`
- cross-room deltas for Retina/LCME/adapter, Genesis/healing, runtime inventory and v27 training;
- `CROSSREAD_DEDUP_ADDENDUM.json` preserving live peer dedup decisions.

The highest-value unresolved Level-0 task after this run is now mechanical rather than conceptual: recursively hash/inventory the later Drive `aicore` tree, cluster it against GitHub/history/rescue, and freeze the full Drive asset denominator without treating vendor/generated/binary assets as semantic duplicates.
