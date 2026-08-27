# KMP-UDB-GRAPH-IDENTITY-VECTOR-V1-TARGET-20260811

packet_id: `KMP-UDB-GRAPH-IDENTITY-VECTOR-V1-TARGET-20260811`
domains: `unifieddb, claygraph, projection_identity, hyperposition, activation, replay`
epistemic_class: `ACCEPTED_TARGET_VPS_MECHANISM_EVIDENCE`
status_hint: `SUPPORTED_TARGET_LAYERED_GRAPH_IDENTITY_NOT_PRODUCT_INTEGRATED`
origin_actor: `chatgpt-secondary`
provider: `OpenAI`
model: `GPT-5.6 Sol`
trigger: `unifieddb`
program: `FRANK_V0_1`
work_package: `F-V01-04-UNIFIEDDB-STATE-CONTINUITY`

## Motivation

Target-negative PR #298 proved current ClayGraph `derivation_hash` is not topology/content identity. Its small rescue oracle also showed that a structural content root could be deterministic, lesion-sensitive and rebuildable.

A production successor cannot hash all Graph tables into one scalar because one SQLite file contains structurally different state classes: truth-derived topology, epistemic possibilities, transient activation/selection, and provenance/materialization/query receipts.

## Target candidate

PR #308:
`UnifiedDB: layered GraphIdentityVector V1 over structural, epistemic and dynamic state`

Base: current main `2bdeb35d722417a1c2d9b71a3b3ac9125acf46c3`
Head: `448ed699a27c5584280d3e93ee154da688420ab6`
Target run: `31439072374`
Result: `SUCCESS`
Artifact: `frank-graph-vector-v1-31439072374`
Artifact id: `9082140957`
Artifact digest: `sha256:748c045389427cbb8a1b45ace046887c850beeffbb02ac05f73dec05e4e3c0d5`
Environment:
- Linux `6.8.0-117-generic` x86_64;
- Python `3.12.3`;
- SQLite `3.45.1`.

Mechanism result: `PASS_GRAPH_IDENTITY_VECTOR_V1_MECHANISM`.
Whole mechanism probe wall ~0.19 s, max RSS 25,712 KiB; not a per-query benchmark.

## Layered identity

### StructuralProjectionRoot
Manifested tables:
- nodes;
- edges;
- edge_evidence;
- graph_dependencies;
- relation_instances;
- relation_members;
- organ_graph_map;
- organ_function_paths;
- coupling_edges.

Source/graph epoch attempt columns are excluded where the external typed source SemanticCheckpointIdentity is already bound. Temporal validity fields remain included because they change read semantics.

### EpistemicRoot
Manifested tables:
- graph_conflicts;
- alternative_groups;
- alternative_nodes;
- alternative_compatibility;
- possibility_paths.

### DynamicRoot
Manifested tables:
- activation_state;
- activation_channels;
- assemblies;
- assembly_members;
- candidate_sets;
- candidate_members;
- receiver_influence.

### Provenance/control
Explicitly classified but excluded from content-layer roots:
- meta;
- graph_epochs;
- projection_receipts;
- topology_versions;
- graph_query_receipts;
- projection_jobs;
- topology_snapshots/deltas;
- higher-order reduction tests;
- lesion/rescue tests;
- graph_materialization_state.

Unknown persistent Graph tables fail closed until classified.

## Target differential results

All checks passed:
- same-source rebuild with new graph epoch/reason kept StructuralRoot, EpistemicRoot and ProjectionIdentity stable;
- node-label structural lesion changed StructuralRoot and ProjectionIdentity;
- rebuild restored exact structural/projection identity;
- edge `valid_to` mutation changed StructuralRoot and ProjectionIdentity; restoring validity restored identity;
- activation mutation changed only DynamicRoot/dynamic snapshot, not StructuralRoot/ProjectionIdentity;
- possibility-path mutation changed EpistemicRoot/ProjectionIdentity but not StructuralRoot;
- extra projection provenance receipt changed none of the content roots/ProjectionIdentity;
- changing only the source typed SemanticCheckpointIdentity preserved layer content roots but changed ProjectionIdentity;
- unclassified future table was rejected with `GRAPH_IDENTITY_MANIFEST_MISMATCH`;
- final SQLite integrity/FK state clean.

Representative final target identities:
- manifest digest `66a2dc7258da83a8cc2a98869d4d15dc8b3371792ca287ef02aa59b6f77e4f25`;
- structural root `7766e404b18ac9ad4e5bcab7a2975f1239de7764ab487e1ef3f0319131bd5f24`;
- epistemic root `894b44ec67736fed0def8f6c33098bce55178ce99838719844e9bc1bfef5d267`;
- dynamic root `0d7211eb7f74d9633a10155e5906cebcacd412ff6819b5ac809f958f58d647b2`;
- final projection identity in the final probe state `b4ac0fab43be15bab1e6a05924e4a83a22b7763d3cd56809633e04035acdef9d`.

## Architecture consequence

ClayGraph identity is vector-valued:

`GraphIdentity := <typed source SemanticCheckpointIdentity, manifest, StructuralRoot, EpistemicRoot, DynamicRoot, provenance/control receipts>`.

A stable ProjectionIdentity binds source identity + materializer + manifest + StructuralRoot + EpistemicRoot.

Dynamic activation/selection gets a separate dynamic snapshot identity. Attention can therefore move without pretending canonical truth-derived topology changed.

This also prevents a Graph provenance receipt or build attempt epoch from becoming content identity.

## Product gates still open

- integrate with #294 schema/authority admission;
- bind typed #297/#304 SemanticCheckpointIdentity rather than synthetic source id;
- enforce global STALE/CONFLICT/DEGRADED read gating;
- finalize table/layer taxonomy with Hyperposition/GWT owners;
- feed ProjectionIdentity into SelectionReceipt/approximate-route validity;
- measure root update strategy on large real Graphs; current mechanism recomputes full layer roots;
- preserve exact UnifiedDB fallback if Graph layer invalid/quarantined.

## Promotion boundary

`SUPPORTED_TARGET_LAYERED_GRAPH_IDENTITY_NOT_PRODUCT_INTEGRATED`.

No canonical state mutation, external effect, semantic truth/effect authority, whole Frank v0.1 acceptance, final training authorization or Frank/self.root Harness authority follows from this packet.
