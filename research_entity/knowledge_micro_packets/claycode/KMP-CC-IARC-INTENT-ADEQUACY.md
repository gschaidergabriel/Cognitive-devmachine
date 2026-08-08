<!-- RAE_META
{"packet_id":"KMP-CC-IARC-INTENT-ADEQUACY","title":"Capability-valid is not task-justified: UserIntentContract plus TypedRelease candidate","domains":["claycode","frank","clay","claygraph","unifieddb","gwt","hyperposition","emergenz"],"topics":["intent-adequacy","prompt-injection","information-flow","effect-authority","IARC"],"epistemic_class":"CONSTRUCTED_MECHANISM_RESULT_WITH_EXTERNAL_ANALOGUES","claim_status_hint":"OPEN_SUPPORTED","origin_actor":"chatgpt-secondary","provider":"OpenAI","model":"GPT-5.6 Sol","source_refs":["research_entity/trigger_runs/claycode/claycode-multiworker-20260809T0128p0700/EXPERIMENT_RESULTS_chatgpt-secondary-sol-02_intent_adequacy.json","research_entity/trigger_runs/claycode/claycode-multiworker-20260809T0128p0700/EXTERNAL_EVIDENCE_LEDGER_chatgpt-secondary-sol-02.md"],"evidence_refs":["EXP-CC-LANE-D-UIC-NONINTERFERENCE-001"],"confidence":0.78,"verification_required":true,"falsifier_or_next_test":"Target-Qwen/real-tool factorial under prompt injection: capability-only vs task verifier vs UIC+TypedRelease vs combined verifier+deterministic gate; measure attack success, false blocks, task utility and latency.","predecessor_packet_ids":[],"supersedes_packet_ids":[]}
RAE_META -->

### Claim
A valid capability and a semantically well-formed `EffectIntent` do not by themselves establish that an effect is justified by the user's current task. Candidate repair: a protected host/user-bound `UserIntentContract` plus narrow `TypedRelease` information-flow witnesses before effect authority is reserved.

### Constructed result
In `EXP-CC-LANE-D-UIC-NONINTERFERENCE-001`, 120,000 generated episodes contained 29,905 benign and 90,095 mutated attack cases. The capability-only gate admitted all 90,095 attack cases. A coarse task-ID gate still admitted 80,059. A static exact-target gate admitted 41,872 attacks and rejected all 4,732 legitimate dynamic-target controls. The UIC+TypedRelease arm admitted 0/90,095 constructed attacks while allowing 29,905/29,905 benign controls, including all 4,732 dynamic cases.

Nine targeted ablations (target, release, target provenance, payload flow, amount, epoch, task, invocation and approval binding) each changed 0/3,000 full-gate accepts into 3,000/3,000 accepts when the named check was removed in the deliberately constructed single-axis family.

A separate 40,000-case structural consent model showed generic boolean confirmation accepted 25,982/25,982 changed manifests; confirmation bound to the exact manifest accepted 0 changed manifests and all 14,018 clean controls. This is structural binding evidence only, not human-comprehension evidence.

### External analogue boundary
Task Shield, VIGIL, CaMeL, Fides, AgentSecBench, ARGUS, CXI, IGAC and RFC 9396 independently support distinctions among task alignment, information-flow control, structured authorization and commit binding. They do not validate ClayCode's exact UIC or synthetic effect sizes.

### Negative results retained
- Static exact-target allowlisting is not a general solution: it loses legitimate dynamic utility and still misses other influence/authority dimensions.
- Generic boolean confirmation is structurally swappable.
- Model-generated UIC is not accepted as trusted authority merely because it is well typed.

### Next falsifier
Run actual target-model/tool workflows and deliberately vary untrusted context while holding trusted user intent fixed. Protected sink fields, effect kind, protected target and invocation authority must remain invariant except through explicit typed releases.
