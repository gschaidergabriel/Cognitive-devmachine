# 666 Level-0 tranche report — 2026-08-09 06:14–06:22 +07:00

## Result

Status: `CURRENT_SESSION_TRANCHE_COMPLETE_LEVEL0_REMAINS_OPEN`

This tranche attacked denominator ambiguity and, after an owner-provided source update, closed the previously open external Needle source-replication lane at source level.

## Durable closures

### 1. Project-Frankenstein Level-0 history scope law

Artifact: `research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_LEVEL0_SCOPE_LAW.json`

Verified GitHub compare:
- scope base inclusive: `e1a8812767668091d146ee958bbc2ebb2743031c`
- frozen head inclusive: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- merge base: `e1a8812767668091d146ee958bbc2ebb2743031c`
- head ahead by: `544`
- base behind by: `0`

Frozen Level-0 PF Git-history obligation count: `545` commit units = one inclusive base + 544 verified descendants.

This closes the prior blocker `verify parentless root OR explicitly define pre-base scope law` without claiming unavailable parent metadata. Material earlier than the inclusive base is outside the PF Git-history denominator unless independently materialized by Drive/recovery, in which case it is reconciled under that source lineage.

Still open on PF: ordered commit identity manifest if not already frozen elsewhere, exact frozen-head file tree, and final history/tree/Drive reconciliation.

### 2. AICORE `configs` exact alias

Artifact: `research_entity/archive_assimilation/manifests/DRIVE_AICORE_CONFIGS_EXACT_ALIAS_MANIFEST.json`

Drive `aicore/configs` contains exactly one recursive leaf: `configs/models.yaml`, 280 bytes. Its Drive-derived Git blob identity is `a7576e8b886464684b16527a1ca46735aa7914ae`, exactly matching the frozen PF head blob. Classification: `EXACT_ALIAS_CLOSED`, zero earned-work credit.

This is distinct from the already-closed singular `aicore/config` subtree.

### 3. AICORE `ext` denominator crosscheck

Local artifact: `research_entity/archive_assimilation/manifests/DRIVE_AICORE_EXT_RECURSIVE_DENOMINATOR.json`

Independent traversal reconstructed exactly 21 recursive leaves: 10 root files + 8 `sovereign` files + 3 `genesis` files. During final pulse, a peer closure was discovered that had already byte-checked all 21 files and classified them 21/21 exact PF aliases: `research_entity/archive_assimilation/manifests/DRIVE_AICORE_EXT_EXACT_ALIAS_SUBMANIFEST.json` / commit `2f3f099f3db837cbaeb99c19851a67f136e4265a`.

Therefore this tranche's ext artifact is corroborative denominator evidence only: zero additional semantic or earned-work credit.

### 4. Full external Needle source snapshot + sandbox architecture validation

Owner added a complete Needle source checkout during this tranche. Its own `.git` metadata pins the source to:

`cactus-compute/needle@6fdddb874dd6f46dabeea88d0bf239fc4a2474c4`

The upstream commit was independently resolved. The working tree outside `.git` is frozen as exactly 40 leaf files and key Drive blobs match the pinned upstream Git blobs.

Artifacts:
- `research_entity/archive_assimilation/manifests/DRIVE_EXTERNAL_NEEDLE_SOURCE_SUBMANIFEST.json`
- `research_entity/archive_assimilation/receipts/666_20260809T0615p0700_chatgpt_secondary_needle_source_sandbox.json`
- `research_entity/harness/fixtures/NEEDLE_SOURCE_SANDBOX_ORACLES.json`
- `research_entity/frank/NEEDLE_CLAY_BOUNDARY_SANDBOX_DELTA.md`
- `research_entity/trigger_runs/666/666-20260809T0614p0700-chatgpt-secondary/BRANCH_FEEDBACK_MANIFEST.json`

Source-level sandbox findings:

1. Historical constrained decoding has fail-open paths. A synthetic tokenizer piece that closes a valid constrained tool name and carries structural/invalid next-span suffix is accepted at the closing quote; after state update the next constrained buffer can be off-trie, where the historical decoder returns original unconstrained logits. Exact real-SentencePiece reachability remains an open runtime replay test.
2. Constraint exhaustion and off-trie states return original logits rather than typed abstention.
3. Tool-name normalization is non-injective and last-write-wins. The archived FRANK 51-active-tool set itself has no observed collision, so this is a registry-evolution oracle rather than a claimed historical FRANK incident.
4. The pinned source uses a flat Needle parameter dialect. Standard-ish JSON Schema `parameters.properties` produces the wrong constrained key; arbitrary provider schema pass-through is invalid. A versioned deterministic Clay→Needle projection is required.
5. Constrained decoding binds names/argument keys but not required/value type/range semantics. Complete deterministic post-decode schema validation is required.
6. Historical encoder budget is 1024 tokens and tool tokens are tail-truncated after the query. The verbose 51-tool projection is ~11.9k characters; a minimal name+argument projection is ~3.5k characters. Exact tokenizer fit and tool-order invariance remain mandatory measurements.
7. Historical finetune code force-downloads an unpinned `needle.pkl` and deserializes it with Python pickle. This lane is forbidden inside final FRANK authority. Current upstream SafeTensors/Cactus is a preferred production candidate, still requiring immutable revision/hash pinning.
8. `TransformerConfig` silently drops unknown kwargs; config must be strict-versioned before weights load.

The current boundary is therefore:

`Clay CapabilityRegistry -> versioned NeedleProjection -> Needle -> untrusted raw route -> strict deterministic validator -> provenance-bound Clay ToolProposal -> Safe-Effect/authority gate -> effect -> Clay EffectReceipt`

Needle remains the dedicated semantic router/proposer. It never mints execution authority.

If exact full-registry context does not fit, a measured Needle-only multistage/tournament router is retained as a candidate so semantic tool selection need not be pushed back into the 4B model. It is not adopted until held-out differential tests beat or match the single-pass baseline.

Full model/tokenizer replay was not falsely claimed: this execution sandbox lacks the exact binary bundle/Flax runtime and external binary/package download is unavailable. The remaining runtime replay gates are explicitly enumerated in the receipt and harness fixture.

No new earned-work hours are applied for this Needle lane because earlier Level-0 Needle archaeology already carries the reuse candidate; this run closes source-replication uncertainty and adds falsifiers/oracles rather than double-crediting the same mechanism family.

## Concurrency / dedup

- `aicore/konzepte` was claimed in this session, reached a clean safe point, and was paused/released when the owner supplied the higher-value full Needle source. Its root already identifies V7 derived concept-index lineage; it can resume without restarting.
- `aicore/papers` and services world/embodiment were already closed by peers and were not duplicated.
- `aicore/ext` overlap was discovered only at final pulse; peer exact-alias result outranks the local denominator-only artifact for identity classification. No duplicate credit is applied.
- Needle historical `aicore/needle` semantics were cross-read only; the new work targeted the previously open external source-replication/runtime-assumption lane.

## Gate effect

Material Level-0 progress:
- PF root-vs-scope ambiguity: **closed by explicit scope law**.
- PF history denominator: **545 commit units now explicitly bounded**.
- AICORE configs: **exact-recursive closed 1/1 alias**.
- AICORE ext: **exact-recursive closed 21/21 alias** by peer, independently denominator-crosschecked here.
- external Needle source identity: **40/40 Working-Tree leaves frozen at upstream commit 6fdddb8; source-level architecture sandbox complete**.

Strict global Level-0 progress remains `0%` under the current program law because the combined Drive + PF + reconciliation denominator is not yet frozen in the authoritative workspace.

Remaining hard classes include the exact PF frozen-head tree, any still-unfrozen ordered commit identity obligation, remaining Drive recursive roots/support/generated classification, exact Needle model/tokenizer/Cactus runtime differential replay, and final cross-source reconciliation / branch feedback / earned-work audit.

## Earned work / training

- new earned-work hours applied by this tranche: `0`
- new duplicate Needle earned-work credit: `0`
- final/paid training started: `false`
- owner training authorization remains required after the data gate.
