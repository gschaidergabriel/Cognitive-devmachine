# 666 Level-0 — AICORE Services Cross-Source Reconciliation

Run: `666-20260809T0533p0700-chatgpt-secondary-aicore-services`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Trigger: `666`  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## Result

This run materially reduces the open AICORE/services cross-source denominator and discovers one Drive-only security lineage with a reproduced fail-open regression oracle. It does **not** claim Level-0 PASS.

## Exact cross-source closures

Three complete Drive service subtrees were fetched as raw bytes and compared file-by-file against the frozen Project-Frankenstein head `abba90a5767d85abc8a1ac340bae92842dab35c1` using canonical Git blob SHA-1 identity.

### hypothesis_engine

Manifest: `research_entity/archive_assimilation/manifests/DRIVE_AICORE_SERVICES_HYPOTHESIS_ENGINE_CROSSSOURCE_MANIFEST.json`

- 6 direct files
- 6/6 byte-identical to frozen PF head
- Drive-unique semantic delta: none
- additional earned-work credit: 0

### context_gate

Manifest: `research_entity/archive_assimilation/manifests/DRIVE_AICORE_SERVICES_CONTEXT_GATE_CROSSSOURCE_MANIFEST.json`

- 7 direct files
- 7/7 byte-identical to frozen PF head
- Drive-unique semantic delta: none
- additional earned-work credit: 0

### invariants

Manifest: `research_entity/archive_assimilation/manifests/DRIVE_AICORE_SERVICES_INVARIANTS_CROSSSOURCE_MANIFEST.json`

- 11 direct files
- 11/11 byte-identical to frozen PF head
- Drive-unique semantic delta: none
- additional earned-work credit: 0

Combined exact closure from this worker: **24 files across three complete service subtrees**. These are now corroborative mirrors rather than duplicate semantic obligations.

## Drive-only post-head security lineage

Receipt: `research_entity/archive_assimilation/receipts/666_20260809T0542p0700_chatgpt_secondary_aicore_services_security_supersession.json`

The Drive `aicore/services/injection_guard.py` module is absent from the frozen PF head. Drive `services/tools.py` is also byte-divergent and integrates the guard into external web-search and document-ingest text paths.

Four relevant Drive files were raw-fetched and SHA-256/Git-blob hashed:

- `tools.py` — divergent from PF
- `injection_guard.py` — absent at PF frozen head
- `subconscious.py` — divergent, exact semantic delta not yet atomized
- `dream_daemon.py` — divergent, exact semantic delta not yet atomized

Major PPO/dream/memory mechanisms are already present in PF; timestamps or whole-file divergence are therefore **not** treated as proof that all semantics are new.

## Reproduced injection-guard failure

Harness fixture: `research_entity/harness/fixtures/AICORE_INJECTION_GUARD_TAIL_CLEARANCE_ORACLE.json`

Historical implementation behavior:

1. deterministic regex scan examines the complete input;
2. when a finding exists, the mandatory free-LLM second opinion sees only `text[:2000]`;
3. `injektion=false` from that verifier changes the finding to `sauber`;
4. the original complete input is then returned unchanged.

Isolated non-network regression reproduction placed a strong `ignore previous instructions` match after character 2000. The deterministic detector found it with score 3, the verifier prompt did **not** contain the matched span, the stub verifier returned `injektion=false`, and the historical guard returned the original unsafe full document unchanged.

Control: when the free verifier is unavailable, the historical implementation preserves the deterministic finding and neutralizes the input. That path is fail-closed.

Required current invariant:

> No untrusted-data path may transform DETECTED_UNSAFE into SAFE_ORIGINAL unless the clearing mechanism actually evaluated the relevant evidence under an explicitly authorized typed policy.

Implications:

- verifier coverage must be span-addressed / explicit;
- lower-assurance verifier output must not silently gain complete clearance authority;
- source trust belongs in structured provenance, not free-form display strings;
- untrusted text must remain typed data across FRANK/ClayCode/UnifiedDB boundaries.

Earned-work candidate for this unique negative oracle: 0.5 / 2 / 4 hours low/center/high. **Global credit not applied** pending row-level safety overlap reconciliation.

## Peer crossread / dedup

A concurrent services safety/recovery worker found separate negative oracles: ASRS shell-classifier bypass, executable invariant contradiction, non-independent Triple-Reality replication, systemd transitional-state restart failure, zombie resurrection and ContextGate bypass-channel scope.

The long-tail injection-clearance failure from this worker is not present in that peer receipt, so it remains a distinct regression oracle. The invariants/context-gate semantic families receive no additional credit here because their Drive trees are exact PF mirrors and peer semantic analysis already exists.

## Remaining services denominator boundary

A sibling denominator worker proved an important connector limitation:

- exactly 13 direct `services` folders are visible;
- at least 87 direct files are visible;
- normal folder fetch caps at 100 children;
- no pagination is exposed;
- relevance/search filters are non-exhaustive for known direct files.

Therefore the **services root direct-file denominator must remain OPEN**. Exact folder subshards can still be closed independently, as this run did. Global Level-0 exact progress must not be increased on the basis of an unverifiable root-file count.

## Status

`PARTIAL_LEVEL0_MATERIAL_ADVANCE_24_EXACT_MIRROR_FILES_CLOSED_DRIVE_ONLY_SECURITY_ORACLE_ADDED_GLOBAL_GATE_NOT_PASS`
