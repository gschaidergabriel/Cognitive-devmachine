# 666 Level-0 Archive Assimilation — Safety / Execution Authority Shard

Run: `666-20260809T0417p0700-chatgpt-secondary-safety`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Canonical parent: RAE-8.8 r2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`  
Program stage: `L0_ARCHIVE_ASSIMILATION`  
Project-Frankenstein frozen head: `abba90a5767d85abc8a1ac340bae92842dab35c1`

## Result

This worker joined the live `center`, cross-read concurrent 666 workers, selected a non-overlapping Project-Frankenstein history lane focused on execution authority/security boundaries, analyzed the historical safety lineage, mapped the result into current Clay Safe-Effect research, published a cross-room delta, added a provisional historical-earned-work mapping, updated the Level-0 workspace, reread the durable outputs, and emitted a LEAVE handoff.

Level 0 remains `NOT_PASS`. No exact Level-0 percentage was awarded because the Drive archive and full Project-Frankenstein history/tree denominators remain unfrozen.

## Live mesh coordination

At join/pulse time, parallel workers were already covering architecture history, state/identity/failure, GWT runtime and XENO/ClayCode. This worker therefore restricted its lane to:

- model output versus execution authority;
- approval-gate failures;
- sandbox/capability boundary evolution;
- destructive-effect restrictions;
- fail-open enforcement behavior;
- safety-evaluation failures;
- cross-subsystem authority drift.

Durable coordination artifacts:

- `research_entity/rooms/center_events/20260809T0417p0700_666_chatgpt_secondary_safety_join.json`
- `research_entity/rooms/center_events/20260809T0420p0700_666_safety_authority_cross_room_delta.json`
- `research_entity/rooms/center_events/20260809T0422p0700_666_chatgpt_secondary_safety_leave.json`

## Primary historical negative result

Project-Frankenstein commit `c9bb3bcb3fcac61a1ae0f1de95d814dda3038302` states that the agentic system used `skip_approval=True`, bypassing high-risk safety checks for tools including bash execution and file deletion. The repair commit reports that this allowed arbitrary destructive commands without user consent and caused a full system wipe.

Epistemic boundary: this is a developer-reported incident preserved in the historical security repair commit. It is treated as a high-value historical negative result, not independently reproduced current runtime evidence.

Current implication:

`model output != execution authority`

must be a runtime invariant rather than a prompt convention.

## Additional historical safety lineage

### Post-wipe defense in depth

The repair added:

- a safe auto-approval whitelist;
- explicit user approval for mutating/high-risk tools;
- protected-path checks;
- expanded dangerous-command detection;
- Firejail filesystem restrictions;
- repair of the approval-id flow itself.

### Hard-delete capability removal

Commit `fff1c5ccfdc3829db75cbf7c0da28e88857467e0` later removed `fs_delete` and attempted to block deletion equivalents across bash and Python. This is a direct historical precursor of the current Safe-Effect direction, while still being weaker than semantic/effect closure.

### Compound risk and resource budgets

Commit `165d7149fb0aa499bb2474c1b85fca3b1367ec8c` introduced compound plan risk `1 - product(1-risk_i)`, EMA failure scoring, and Firejail CPU/RAM/filesize/network restrictions. This supports treating multi-step risk and resource damage compositionally.

The same implementation warned and continued unsandboxed when Firejail was unavailable. That becomes an explicit historical fail-open falsifier for the current architecture.

### Restricted autonomous capabilities and proposal/commit separation

Autonomous research historically used a limited tool subset plus cooldown/session budgets. Genesis self-authored proposals passed sandbox validation/destructivity checks and a separate FAS accept/reject path before registration. These mechanisms support per-context capability subsets and proposal/validation/commit separation.

### Reactive content filters are not authority containment

V15/V25 safety evaluations produced concrete harmful-output/tooling failures that were repaired by increasingly specific prefilters, regexes, filename checks and executor blocklists. These are useful regression inputs but cannot establish prompt-injection resistance or effect safety.

### Authority drift across subsystems

The separate Projects/Claude coding-agent subsystem first constrained file operations to a project-root sandbox, then deliberately removed the sandbox and granted full-system file/bash/service/package authority while retaining only a small destructive-command blocklist. This demonstrates that local subsystem implementations can silently widen ambient authority.

## Fusion with current Clay Safe-Effect research

The historical evidence materially raises the priority of the current permanent Safe-Effect research axis, especially:

- authority non-amplification: `A(S_t+1) subseteq A(S_t) union ExternalGrant_t`;
- foreign-code closure: `EffectiveEffects(child_program) subseteq Effects(parent_Clay_contract)`;
- external irreversible-effect brokerage;
- resource-budget boundedness;
- recoverability/versioning instead of ambient destructive mutation;
- fail-closed enforcement-backend semantics.

This history does **not** prove the candidate Clay effect algebra complete or sound. It provides direct project-specific failure evidence and discriminating regression targets.

## Required executable regression conversion

Highest-value follow-on Harness tests from this shard:

1. Bind approval to exact normalized effect + capability set + protected-state hash + expiry + single-use nonce; mutation must invalidate approval.
2. Remove/kill the sandbox/effect broker and verify protected effects fail closed.
3. Attempt equivalent protected destruction via Clay, Bash, Python, C/Rust/WASM/FFI and nested tools; child effective effects must not exceed the parent contract.
4. Create/modify a secondary agent subsystem and attempt to widen file/process/network scope without `ExternalGrant`; runtime must reject the expansion.
5. Execute long sequences of individually moderate-risk actions and verify aggregate resource/risk budgets prevent emergent damage while retaining ordinary build/test utility.

## Earned-work mapping

Added mapping `HEW-PF-SAFETY-005`:

- category: `NEGATIVE_RESULT_VALUE`;
- current rows: ClayCode BASE, Harness 1, Harness 2, one-module FRANK, final acceptance;
- provisional avoided future work: 4h low / 9h center / 18h high;
- confidence: medium for test reuse, low for hour estimate;
- no global completion credit applied while Level-0 coverage is insufficient.

At the time this worker integrated its mapping, the shared partial center estimate moved from 29h to 38h. Subsequent concurrent Level-0 workers increased the live gross mechanism-deduped center mapping further; final row-level reconciliation is still required.

## Drive blocker

The Drive source currently exposes a single archive:

- `all frank data 1.tar.xz`
- file id `1plv5-cP4zi_RfSPKtIlqqGkLuOSckoRU`
- size `663552000` bytes

The available Drive raw fetch surface rejects files above `104857600` bytes. The blocker was reproduced in this session. Therefore archive-member enumeration is not possible through the current connector and exact Drive coverage remains zero.

## Durable outputs

- `research_entity/archive_assimilation/receipts/666_20260809T0420p0700_chatgpt_secondary_pf_safety_authority_shard.json`
- `research_entity/rooms/center_events/20260809T0420p0700_666_safety_authority_cross_room_delta.json`
- `research_entity/forecast/HISTORICAL_EARNED_WORK.json` mapping `HEW-PF-SAFETY-005`
- `research_entity/archive_assimilation/666_WORKSPACE.json`
- this final run report

## Final state

`PARTIAL_LEVEL0_MATERIAL_SAFETY_DELTA_COMMITTED`

The worker slice is complete. The global 666 Level-0 process remains active and is continuing through parallel non-overlapping workers. The highest global blocker remains exact access to the oversized Drive archive; Project-Frankenstein semantic/history analysis can continue in parallel without weakening exact-progress discipline.
