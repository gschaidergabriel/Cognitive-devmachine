<!-- RAE_META
{"packet_id":"FRANK_SELF_HOSTED_RUNNER_AUTHORITY_OPEN_20260810","title":"Persistent self-hosted Frank runner currently couples execution and receipt-write authority","domains":["security","harness","frank"],"topics":["GitHub Actions","self-hosted runner","GITHUB_TOKEN","contents write","ephemeral runner","receipt authority"],"epistemic_class":"OPEN_HYPOTHESIS","claim_status_hint":"OPEN","origin_class":"WEB_RESEARCH_SYNTHESIS_PLUS_CODE_INSPECTION","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T00:12:00+07:00","updated_at":"2026-08-10T00:12:00+07:00","source_refs":["gschaidergabriel/Dr.-Unterweger:.github/workflows/frank-vps-deep-integrity.yml","https://docs.github.com/en/actions/reference/runners/self-hosted-runners","https://docs.github.com/en/actions/concepts/runners/self-hosted-runners","research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md"],"evidence_refs":["gschaidergabriel/Dr.-Unterweger:.github/workflows/frank-vps-deep-integrity.yml"],"related_claim_ids":[],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"HIGH_THAT_AUTHORITY_IS_COUPLED_LOW_THAT_ANY_COMPROMISE_EXISTS","verification_required":true,"falsifier_or_next_test":"Implement read-only execution plus separate constrained receipt persistence and compare reproducibility/operability; evaluate JIT or ephemeral runner lifecycle for higher-authority workloads.","search_terms":["self-hosted runner security","contents write","persist credentials","ephemeral runner","Frank receipt writer"]}
RAE_META -->

### Core
Frank's current self-hosted VPS workflows execute untrusted-to-runtime build/test/model code and also hold repository `contents: write` authority with checkout credentials persisted so the same job can commit receipts. This couples execution authority and canonical-repository write capability on a persistent runner.

### Evidence / boundary
GitHub documents that self-hosted runners do not necessarily start clean for each job and recommends ephemeral self-hosted runners for clean-job isolation in autoscaling scenarios. The current workflow visibly requests `contents: write` and `persist-credentials: true`. **No compromise or exploit is observed.** The claim is about attack-surface/authority coupling, not a breach.

### Implication
Remote research execution is valuable, but higher-authority production use should minimize credentials available to the executor.

### Next test
Split the workflow into read-only execution and separate constrained receipt persistence, then test end-to-end evidence durability; evaluate ephemeral/JIT runner options without weakening reproducibility.
