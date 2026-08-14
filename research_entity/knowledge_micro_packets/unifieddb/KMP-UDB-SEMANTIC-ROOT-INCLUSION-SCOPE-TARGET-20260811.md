# KMP-UDB-SEMANTIC-ROOT-INCLUSION-SCOPE-TARGET-20260811

packet_id: `KMP-UDB-SEMANTIC-ROOT-INCLUSION-SCOPE-TARGET-20260811`
domains: `unifieddb, semantic_root, recovery, provenance, schema_metadata`
epistemic_class: `ACCEPTED_TARGET_VPS_NEGATIVE_SCOPE_EVIDENCE`
status_hint: `ROOT_MECHANISM_SUPPORTED_BUT_INCLUSION_MANIFEST_OPEN`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Parent mechanism

PR #297 semantic checkpoint root remains target-supported within its declared checkpoint-evidence scope.
Its target run `31436294602` passed 27/27 checks. 50k synthetic rows were rooted in ~120.803 ms in the root-specific measurement block; whole target probe wall was ~413.488 ms.

This packet narrows the semantic inclusion boundary before any checkpoint-admission / selected-head authority composes that root.

## Target scope falsifier

Diagnostic PR #304:
`UnifiedDB diagnostic: falsify semantic checkpoint root operational boundary`

Head: `48264aa64ab2fc315b044d1e3575012564a3ad89`
Target run: `31438521066`
Result: `SUCCESS`
Artifact: `frank-semantic-root-scope-31438521066`
Artifact id: `9081928959`
Artifact digest: `sha256:2e0d0da8436a000c82922de5f328cf31da8667a0eb8be976a2c6c97b9ebd5c51`

The first attempt failed only because the #297 root deliberately leaves the caller connection `query_only=ON`; the corrected disposable fixture explicitly disabled query_only only before its injected mutations. That confirms the read-only guard and is not negative evidence against #297.

Corrected target result reproduced two false-difference surfaces while ordinary application schema/data controls remained unchanged.

### SRoot-1 — `PRAGMA user_version` moves the root

A user_version increment changed the semantic checkpoint root. Restoring the original header value restored the exact baseline root.

Current repository search found no application use establishing user_version itself as cognitive/semantic state.

Therefore its inclusion is currently implicit rather than justified by a versioned semantic-state contract.

### SRoot-2 — operational `runtime_*` meta is semantic unless explicitly denylisted

The #297 root excludes a hard-coded set of known materialization/certificate `meta` keys. A new bookkeeping key with a `runtime_*` operational role but absent from that list entered the semantic root and changed it. Deleting it restored the exact baseline root.

Therefore:

`hard-coded non-semantic key denylist != stable semantic inclusion manifest`.

The mechanism is vulnerable to silent semantic-scope drift as future operational metadata keys are added.

## Required root-contract refinement

Before checkpoint admission / selected-head publication, define an explicit versioned SemanticRootManifest:

- tables/columns/namespaces classified `SEMANTIC_INCLUDED`, `CAUSAL_RUNTIME_INCLUDED`, `PROVENANCE_ONLY`, `DERIVED_EXCLUDED`, `OPERATIONAL_EXCLUDED`;
- explicit treatment of SQLite header fields such as `user_version` and `application_id`;
- fail closed on unknown semantic-scope classifications during manifest/version transition rather than silently including/excluding;
- manifest identity included in the checkpoint-root receipt;
- migrations that change semantic scope produce an explicit root-protocol version transition.

This is not an argument to simply remove all runtime/provenance state. V15/V16/effect state can be semantically/causally relevant and #297 already correctly showed that legitimate V15 changes move the root. The boundary must be typed, not inferred from naming alone.

## Promotion boundary

#297 remains `ROOT_MECHANISM_SUPPORTED_PENDING_CHECKPOINT_ADMISSION_AND_SELECTED_HEAD_COMPOSITION`, but product composition now additionally requires the semantic inclusion manifest to be adjudicated.

No canonical mutation, external effect, selected-head publication, recovery authority, whole Frank v0.1 acceptance, final training authorization or Frank/self.root Harness authority follows from this packet.
