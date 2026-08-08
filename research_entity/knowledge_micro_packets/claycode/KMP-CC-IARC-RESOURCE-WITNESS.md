<!-- RAE_META
{"packet_id":"KMP-CC-IARC-RESOURCE-WITNESS","title":"Semantic target strings do not preserve protected resource identity across commit","domains":["claycode","frank","unifieddb","claygraph","hyperposition"],"topics":["resource-identity","TOCTOU","aliasing","commit-authority","IARC"],"epistemic_class":"CONSTRUCTED_MECHANISM_RESULT_WITH_OS_ANALOGUE","claim_status_hint":"OPEN_SUPPORTED","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","source_refs":["research_entity/trigger_runs/claycode/claycode-multiworker-20260809T0128p0700/EXPERIMENT_RESULTS_chatgpt-secondary-sol-02_resource_identity.json","research_entity/trigger_runs/claycode/claycode-multiworker-20260809T0128p0700/EXTERNAL_EVIDENCE_LEDGER_chatgpt-secondary-sol-02.md"],"evidence_refs":["EXP-CC-LANE-D-RESOURCE-WITNESS-002"],"confidence":0.82,"verification_required":true,"falsifier_or_next_test":"Reproduce against real Linux openat2/file-descriptor operations, database object IDs, URL redirects/DNS and container/namespace changes; compare stable handle vs re-resolve/verify vs lexical/path controls.","predecessor_packet_ids":[],"supersedes_packet_ids":[]}
RAE_META -->

### Claim
Binding effect authority only to a target string/path or to a target resolved once before commit is insufficient when the name-to-resource mapping can change. Candidate primitive: host-issued `ResourceWitness` binding resolver identity, requested semantic target, canonical object/resource identity, and a stable handle or resolver/namespace epoch.

### Constructed result
`EXP-CC-LANE-D-RESOURCE-WITNESS-002` ran 160,000 namespace episodes: 39,987 benign and 120,013 adversarial mutation cases.

- lexical path/scope gate: 89,898 unsafe effects;
- strict no-alias gate: 30,034 unsafe effects and 14,071/14,071 legitimate alias controls rejected;
- resolve-once then later execute by name: 60,021 unsafe effects;
- stable bound-object/handle model: 0 unsafe effects, 39,987/39,987 benign allowed;
- commit-time re-resolve + exact identity equality model: 0 unsafe effects, 39,987/39,987 benign allowed.

The attacks covered initial alias escape, lexical escape, post-check alias swap and post-check name rebinding. Frequencies are coverage choices, not production risk estimates.

### External analogue boundary
Linux `openat2()` and kernel pathname-resolution documentation expose explicit restrictions for trusted programs resolving untrusted path components and discuss changing-path/race scenarios. This supports the systems problem class, not the idealized ClayCode handle model.

### Architecture implication
`AuthorityReservation` should bind a `ResourceWitness`, not only `EffectIntent.semantic_hash` or a textual target. Commit must either operate through the bound stable handle/capability or re-resolve and prove exact identity equality immediately before effect release.

For UnifiedDB, semantic identity must remain distinct from concrete representation identity: the witness should bind the protected semantic resource/object identity plus resolver/placement context, not raw JSON/serialization bytes.

### Negative result retained
A blanket no-symlink/no-alias policy is both insufficient against all rebinding races and unnecessarily rejects legitimate dynamic aliases in the constructed family.
