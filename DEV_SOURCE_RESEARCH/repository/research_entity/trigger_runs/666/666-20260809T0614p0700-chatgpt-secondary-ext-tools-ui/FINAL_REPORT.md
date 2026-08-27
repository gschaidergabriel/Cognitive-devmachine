# 666 Level-0 Run — 2026-08-09 06:14+07 — ext/tools/UI + denominator reconciliation

## Result

`L0_ARCHIVE_ASSIMILATION` remains `NOT_PASS`, but this run exact-closed two AICORE roots, converted a third from an opaque open root into a structured residual graph, added executable chronology/authority Harness oracles, and crossread a peer closure that freezes the Project-Frankenstein Level-0 history scope at 545 commit units.

## 1. AICORE `ext` — exact recursive alias closure

Drive root: `aicore/ext` / `1mHs3PzFJPMOaX_zeXU7Yqc260fzzu6a7`.

Exact recursive denominator:
- root files: 10
- `sovereign/`: 8 files
- `genesis/`: 3 files
- total recursive leaf files: **21**

Every Drive file was raw-streamed, Git-blob hashed and compared against frozen Project-Frankenstein head `abba90a5767d85abc8a1ac340bae92842dab35c1`.

Result: **21/21 byte-identical**.

This includes the historical `sovereign/frank-execute` and `frank-execute.sudoers` privileged-execution lineage. Drive therefore adds no new sovereign variant. This material remains historical PF safety lineage and gets zero duplicate earned-work credit.

Durable manifest:
`research_entity/archive_assimilation/manifests/DRIVE_AICORE_EXT_EXACT_ALIAS_SUBMANIFEST.json`

Center event:
`research_entity/rooms/center_events/666-20260809T0614p0700-chatgpt-secondary-ext-alias-closure.json`

## 2. AICORE `tools` — exact one-file denominator, divergent mixed side branch

Correct AICORE tools root: `14Kp5BLJDacoX84yTIHIZTZ_jdfkL5Iad`.

It contains exactly one recursive leaf: `toolboxd.py`.

Identity:
- Drive Jul-31 blob: `51d500cd67898168970d7b5490875b018fb7a9b7`
- PF frozen-head blob: `e17687c8ba66c3e062b1d61cf1ec0ec3348b2c00`
- result: **divergent**

The later Drive file is not a clean newer architecture. It is a mixed side branch:

1. It contains old entity-session retrieval helpers/endpoints (`/entity/sessions`, `/entity/session`, `/entity/search`) whose lineage was introduced in PF commit `59dfd4534c06f4545633231a434ab42956b803f6` and later superseded by the Rooms replacement (`b3df2f9885bede8ec38ced0c21763a06699d14b9`).
2. It also contains later Drive-only Identity Forge mutation endpoints (`/self/observe_relationship`, `/self/make_pact`, `/self/review_pact`) using the already-discovered `services/identity_forge.py` recovery lineage.

Therefore **newer mtime/file != newer architecture**. Archive merge must be mechanism/lineage granular; whole-file newest-wins restoration is falsified by this concrete case.

Authority findings:
- localhost/loopback is transport locality, not authority;
- a source comment such as `Frank-only` is not machine-enforced authorization;
- persona/model identity cannot mint state-mutation authority;
- read-only historical recall and relationship/pact mutation need distinct effect classes and authority budgets;
- identity mutation requires explicit provenance, durability, snapshot/replay/recovery and rollback semantics.

No new earned-work hours are credited because Identity Forge was already mapped by recovery archaeology and entity-session tooling already exists in PF history. The new value is chronology, merge and authority negative evidence.

Durable artifacts:
- `research_entity/archive_assimilation/manifests/DRIVE_AICORE_TOOLS_TOOLBOX_SIDE_BRANCH_MANIFEST.json`
- `research_entity/archive_assimilation/receipts/666_20260809T0621p0700_chatgpt_secondary_drive_aicore_toolbox_side_branch.json`
- `research_entity/harness/fixtures/TOOLBOX_SIDE_BRANCH_CHRONOLOGY_AUTHORITY_ORACLES.json`
- `research_entity/rooms/center_events/666-20260809T0621p0700-chatgpt-secondary-toolbox-mixed-lineage-delta.json`

Harness fixture adds:
- `TBX-CHR-001` newer-mtime-does-not-imply-newer-semantics;
- `TBX-AUTH-002` loopback-is-not-authority;
- `TBX-AUTH-003` persona-comment-is-not-authority;
- `TBX-EFFECT-004` read-recall-vs-identity-mutation effect split;
- `TBX-STATE-005` identity-mutation replay/recovery contract.

## 3. AICORE `ui` — topology substantially frozen, root identity exact-closed

Correct AICORE UI root: `17UgqDx9-7hj_LJoemVkVR97xcMmmQPVB`.

Direct root:
- 6 folders: `sounds`, `adi_popup`, `ui_tester`, `ewish_popup`, `fas_popup`, `webui`
- 5 files: `__init__.py`, `chat_overlay.py`, `frank-toggle.sh`, `toggle_overlay.sh`, `frank_overlay_launcher.sh`

All five root files were raw-hash compared to PF and are **5/5 exact aliases**.

Exact child topology established so far:
- `sounds`: 5 media files, no subfolders
- `adi_popup`: 8 recursive leaves including one style file
- `ui_tester`: 9 recursive leaves including one style file
- `ewish_popup`: 5 recursive leaves including one style file
- `fas_popup`: 8 recursive leaves including one style file
- `webui`: 4 direct files + `static/`

Known leaf files outside `webui/static`: **44**.

`webui/static` is intentionally split as its own large residual because it contains:
- 3 direct HTML files;
- 7 child folders: `assets`, `img`, `sprites`, `synteq`, `js`, `fonts`, `css`.

Crucially `webui/static/synteq` is the separate Aug-6 web/UI Synteq tree (`15X9JGa5v09TbVYWJ_3aX9adFQEIDgjWs`), not the AICORE runtime `synteq` subtree. Conflating these two same-named branches would corrupt chronology and denominator accounting.

Durable manifest:
`research_entity/archive_assimilation/manifests/DRIVE_AICORE_UI_PARTIAL_RECURSIVE_DENOMINATOR.json`

UI is NOT claimed complete. Root identity is closed; recursive static identity remains open.

## 4. AICORE runtime `synteq` — correctly disambiguated and bounded at root

AICORE runtime Synteq is Drive folder `1LnsZ7HLTdcnsuclwJwn61sWAxHmSnA6K`, distinct from the WebUI static Synteq tree.

Its direct root contains 10 folders (`kern`, `vault`, `konzepte`, `bin`, `ui`, `lib`, `systemd`, `pruefung`, `fusion`, `zwilling`) plus four files (`UEBERGABE-P2.md`, `README.md`, `START.md`, `__init__.py`).

It is a larger independent shard and was deliberately not half-closed in this run.

## 5. Project-Frankenstein history scope ambiguity — closed by peer scope law

A sibling 666 tranche correctly resolved the previous `parentless root OR scope law` blocker without inventing unavailable Git parent metadata.

Frozen Level-0 PF history scope:
- inclusive scope base: `e1a8812767668091d146ee958bbc2ebb2743031c`
- inclusive frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`
- verified merge base: the scope base
- head ahead by: 544
- base behind by: 0
- frozen PF history obligation: **545 commit units**

Material earlier than this base is outside the PF Git-history denominator unless independently materialized through Drive/recovery lineage, in which case it remains a cross-source reconciliation obligation.

This explicitly replaces the need to prove that the base commit is literally parentless.

Artifact:
`research_entity/archive_assimilation/manifests/PROJECT_FRANKENSTEIN_LEVEL0_SCOPE_LAW.json`

PF still requires exact frozen-head file-tree denominator / ordered history identity where not already frozen and final history-tree-Drive reconciliation.

## 6. Parallel Retina denominator progress crossread

Sibling work froze exact recursive `digital-retina-e2e` enumeration:
- root code: 4
- shots: 9
- coverage/measurement lineage: 18
- fresh held-out benchmark images: 32
- generated `__pycache__`: 1
- total recursive leaf files: **64**

All 64 are identified/classified and lineage-linked; exact binary content-hash closure remains pending. No duplicate earned-work credit is taken here.

Artifact:
`research_entity/archive_assimilation/manifests/DRIVE_DIGITAL_RETINA_E2E_RECURSIVE_DENOMINATOR.json`

A dedicated Retina research domain was also established in parallel; this run does not duplicate that research.

## 7. Concurrency / dedup

Observed peer state during this run:
- AICORE `configs` exact-closed as PF alias;
- AICORE `konzepte` work was paused/released to prioritize a full Needle source sandbox validation worker;
- Needle source sandbox validation is actively claimed by a sibling worker;
- services world/embodiment tranche completed;
- Retina E2E denominator frozen and deep Retina research domain established.

This worker avoided those active lanes.

## 8. Accounting and gate

Unique exact closures by this worker in this run:
- AICORE `ext`: 21 exact PF aliases
- AICORE `tools`: 1 exact denominator, divergent mechanism-adjudicated side branch
- AICORE UI root: 5 exact PF aliases

Additional structural progress:
- UI known non-static leaf set bounded at 44;
- WebUI static residual separated into 7 source-class subtrees;
- two Synteq trees disambiguated;
- PF history scope crossread as 545 frozen commit units;
- Retina E2E crossread as 64 frozen recursive leaves.

Earned-work hours newly applied by this worker: **0**. This is intentional: duplicate identity closure and already-mapped mechanism lineage must not inflate lifetime progress.

Global exact Level-0 progress remains **0%** under the strict current law because the combined Drive + PF file-tree/history + reconciliation denominator is not yet frozen in the authoritative workspace.

No paid/final model training was started.

## 9. Current highest-value residuals

After fresh peer pulse, prioritize non-overlapping work among:
1. exact PF frozen-head file tree / ordered identity obligations;
2. `aicore/ui/webui/static` recursive source/media/generated classification and hash closure;
3. AICORE runtime `synteq` recursion;
4. `aicore/skills` sharded recursive denominator;
5. remaining `training` lineage outside already-audited v27 material;
6. top-level Retina/recovery/XENO/Titan/frank-project support/generated trees;
7. final Drive↔PF↔recovery chronology reconciliation, branch feedback and historical earned-work freeze.

## Final gate result

`666_RELEASE_GATE = NOT_PASS`.

The run materially reduced and clarified the denominator without weakening the definition of PASS.