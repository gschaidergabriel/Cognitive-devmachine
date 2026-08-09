# FRANK v0.1 — Direct Claude Code Cognitive Tool Contract

**Status:** PROJECT_OWNER_FIXED_TARGET_CAPABILITY  
**Effective:** 2026-08-09  
**Target:** local embodied FRANK / Clay-native 4B on Andreas' Ubuntu developer system  
**Harness scope:** H1 Reference -> H2 ClayCode equivalence -> H3 one-module lowering

## 0. Target capability

FRANK must be able to know that Claude Code is a currently reachable cognitive/body-extension capability when that route is actually available, and must be able to communicate/delegate to it through a typed tool exposed to FRANK's normal tool surface.

Human shorthand: `Claude Code` appears to FRANK as a tool/cognitive extension it can intentionally use.

This is not ambient authority and not a hard-coded claim that Claude Code is always online.

## 1. Dynamic visibility

The tool is visible to the local 4B only from current capability evidence.

`current Claude Code resource/capability observations`
`-> UnifiedDB current capability state`
`-> derived current capability/possibility view`
`-> bounded ActiveAssembly/tool projection`
`-> 4B knows Claude Code is reachable/unreachable/stale and what it can do`.

No permanent prompt sentence such as "Claude is always available" may substitute for live capability state.

## 2. Tool semantic identity

Canonical target tool identity:

`claude_code_peer`

The final UI may display a human-friendly label, but model/tool semantics use a stable typed identity.

Minimum request:

```text
ClaudeCodePeerRequest {
  request_id
  requester_instance
  goal
  task
  context_refs
  required_capabilities
  desired_outputs
  write_scope
  execution_scope
  completion_test
  privacy_class
  budget
  basis_epoch
  provenance
}
```

Minimum result:

```text
ClaudeCodePeerResult {
  request_id
  responder_instance
  status
  result_semantics
  evidence_refs
  artifact_refs
  execution_receipts
  unresolved
  capability_observations
  local_effects_claimed
  basis_epoch
  provenance
}
```

## 3. State semantics

Claude Code and local FRANK do not share one transient internal state.

The tool carries a typed message/result boundary:

`FRANK local state -> request projection -> Claude Code local cognition/execution -> result/receipt -> UnifiedDB semantic delta -> future FRANK Assembly`.

A returned result is not copied wholesale into model state and does not overwrite local state.

## 4. What Claude Code can contribute

Depending on current observed capability/authority, the route may provide:

- local repository/file analysis;
- code generation/editing;
- local build/test/debug;
- system/runtime inspection;
- execution measurements;
- artifact creation;
- dependency/environment diagnosis;
- structured research/build results;
- capability/resource observations.

The actual current capability set is dynamic and evidence-derived.

## 5. Effect and truth boundary

`Claude Code statement != truth`.

`Claude Code proposed patch != applied patch`.

`Claude Code local verified execution receipt = strong operational evidence for exactly that local effect`.

FRANK's use of this tool never bypasses effect/capability/approval rules. A cognition result cannot mint an external capability.

## 6. Semantic writeback

Material results must be translated into typed semantic/evidence/capability/work deltas and admitted to the relevant UnifiedDB/event lineage.

They then affect future dynamic topology/Hyperposition/GWT/Assembly derivation through normal semantic rules.

Do not maintain a separate prose-only Claude memory or standalone PossibilitySpace.

## 7. UI/tool-surface requirement

The local FRANK tool registry/overlay must be able to expose the direct Claude Code route just like other tools, with current availability represented separately from the static tool definition.

The UI/tool metadata should expose at least:

- available / unavailable / stale / degraded;
- capability summary;
- authority/write scope;
- privacy/export scope;
- expected cost/latency/resource class where known;
- active request state;
- last result/receipt link;
- failure state.

The user does not need to manually copy results between Claude Code and FRANK when the route is operational.

## 8. H1 required tests

H1 must simulate or execute, depending on current environment:

1. Claude tool visible when fresh CAN_NOW/CAN_DELEGATE evidence permits it;
2. tool absent/degraded when capability is stale/unavailable;
3. successful request/result correlation;
4. result provenance preserved;
5. Claude opinion cannot masquerade as local execution receipt;
6. actual local execution receipt is scoped to the effect it verified;
7. stale basis/request is rejected/replanned before consequential execution;
8. timeout/disconnect/reconnect;
9. duplicate/out-of-order result;
10. conflicting Claude vs local/ChatGPT evidence enters conflict semantics rather than silent overwrite;
11. result becomes a typed UnifiedDB delta and can influence a later Assembly;
12. full returned prose/state is not blindly mirrored into the 4B context;
13. direct-Claude route lesion and rescue;
14. compare task outcome/context cost with and without the route.

## 9. H2/H3

H2 must express the same request/result/capability/authority semantics in ClayCode and differential-test against H1.

H3 may lower transport/runtime plumbing into the one-module FRANK architecture, but the semantic peer/tool boundary, dynamic capability visibility, provenance and effect authority distinctions remain observable.

## 10. Dynamic research rule

The exact transport, model/session lifecycle and UI presentation remain researchable and may change from the newest evidence.

The target capability itself is fixed by the owner:

> FRANK can directly communicate with Claude Code through a tool, and FRANK knows dynamically when that capability exists and what it currently makes possible.
