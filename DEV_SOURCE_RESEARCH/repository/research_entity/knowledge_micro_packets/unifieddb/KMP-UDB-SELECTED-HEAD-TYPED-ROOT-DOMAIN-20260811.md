# KMP-UDB-SELECTED-HEAD-TYPED-ROOT-DOMAIN-20260811

packet_id: `KMP-UDB-SELECTED-HEAD-TYPED-ROOT-DOMAIN-20260811`
domains: `unifieddb, semantic_root, lineage, selected_head, recovery`
epistemic_class: `ACCEPTED_TARGET_VPS_NEGATIVE_TYPE_DOMAIN_EVIDENCE`
status_hint: `SELECTED_HEAD_CAS_SUPPORTED_BUT_ROOT_TYPE_MUST_BE_STRENGTHENED`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Parent mechanism

PR #267 selected semantic-lineage head CAS remains useful evidence for one-current-sibling selection. It stores/compares `semantic_root_hash` as bare 64 lowercase hex.

PR #297 later introduced a stronger independent semantic checkpoint-root family, and target scope PR #304 showed that root inclusion semantics themselves require an explicit versioned manifest.

Those two facts make the bare selected-head root type insufficient.

## Target scope falsifier

Diagnostic PR #307:
`UnifiedDB diagnostic: selected head must bind typed semantic-root domain`

Head: `191195427ca9edbfdbb2faeb9a4ef002a1c4fcda`
Target run: `31438812356`
Result: `SUCCESS`
Artifact: `frank-selected-head-root-domain-31438812356`
Artifact id: `9082034637`
Artifact digest: `sha256:83877aa9dfbddb9c0bb11951c5e5e472fb6e307dcbccc85486e15cfc5c84210c`

The probe defined two root evidences with:
- different root protocol versions;
- different semantic inclusion manifest identities;
- deliberately identical 64-hex root bytes.

A typed candidate identity over `protocol + manifest_id + root_hash` distinguished them.

The current #267 store could not: it initialized the selected head from evidence A and `selected_matches()` returned true for both A and incompatible evidence B because only the bare root bytes participate.

Therefore:

`bare root hash equality != semantic checkpoint identity equality`.

## Required type

`SemanticCheckpointIdentity := root_protocol + semantic_root_manifest_id + semantic_root_hash`.

Selected-head state, head hash and CAS comparison must bind the full typed identity.

Root protocol/manifest transitions require an explicit migration/bridge receipt. The same digest bytes must never be silently reinterpreted under a new semantic domain.

This is type strengthening, not a rejection of #267's CAS mechanism.

## Recovery consequence

External rollback floors, snapshot admission and continuation receipts should also bind the typed SemanticCheckpointIdentity rather than a bare hash, otherwise a recovery artifact can cross a root-protocol boundary without changing the byte string it presents.

## Promotion boundary

`SELECTED_HEAD_CAS_SUPPORTED_BUT_TYPED_ROOT_DOMAIN_OPEN`.

No canonical mutation, external effect, selected-head product migration, recovery-floor authority, whole Frank v0.1 acceptance, final training authorization or Frank/self.root Harness authority follows from this packet.
