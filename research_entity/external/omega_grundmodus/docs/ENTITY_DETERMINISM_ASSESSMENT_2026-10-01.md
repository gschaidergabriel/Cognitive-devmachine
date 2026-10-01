# ENTITY_DETERMINISM_ASSESSMENT (clay-global-research-entity, clone read-only, 2026-10-01)
Method: counts + runs on a /tmp COPY (nice, `unshare -rn` = no network). Copy EXCLUDED .git, dump*, "the artefact", agentzeroforschung -> some failures below are copy artefacts, not repo defects (see 3).

## 1. Inventory (measured)
- rae.py = 6-line shim -> rae_core/cli.py (388 L) + possibility_preprocessor.py (373 L). RAE = CLI over ledgers: claim add/transition (6 statuses CURRENT/OPEN/SUPERSEDED/REFUTED/NEGATIVE_RESULT/CONTEXT_ONLY), event log, run state machine (stages INTAKE..PROMOTION, L0-L3 capture), boot (context manifest), query (sqlite sources.db), doctor, benchmark. Single-writer lock .rae_runtime/writer.lock.
- schemas/: 6 JSON Schemas (Draft 2020-12): canonical, claim, event, micro_packet, provenance, topic_packet. Enforced by tools/validate_research_entity.py (121 L, `jsonschema`), run by `rae doctor` + workflow rae-contract-gates.
- governance/: 13 files (Execution-Surface registry/resolution protocol, durable re-entry protocol, authority policies).
- gateflow/: 4 files (contract 197 L, STATE.json, CRITICAL_PATH.json, conversion window) + tools/gateflow.py (430 L, "deterministic compiler/checker", missing denominators stay None).
- tools/: 620 entries. By name: claycode_* 161, trigger2_* 108, trigger1_* 76, run_* 36, free_swarm* 33, grid10* 32; ~71 "gate", 27 probe, 19 bridge, 18 check, 15 validate, 15 receipt, 11 benchmark, 9 audit. Roughly: ~45% compiler/claycode+gates, ~30% trigger1/2 experiment/evidence gates, ~10% swarm/provider runners (LLM-facing), rest search/inference clients.
- tests/: 357 files, 2177 collected (2248 test funcs by grep), 10 collection errors. runtime_checks/: 2 tests. receipts/: 2 (+ ~17 in research_entity/receipts, many more under continuity/, clay_machine/).
- Ledgers: CLAIMS.jsonl 43, CLAIM_STATUS_EVENTS 17, ARTIFACT_PROVENANCE 177, 60 topic packets. Tiny vs. 620 tools.
- CLAYCODE manifest: 14 work packages -> formal PASS 1, OPEN 10, BLOCKED 3; GENERAL_PURPOSE_GATE=FAIL, promotion_allowed=false, implementation_closure_ready 11.
- Gateflow STATE: Frank v0.1 formal progress 3.04 %.
- .github/workflows: 206. Scan: 114 contain test/gate/audit/regression pattern, 94 run on self-hosted runners, 17 reference provider secrets (OpenRouter/Groq/NVIDIA/Mistral/HF/Tavily/Exa = LLM/search), 1 cron, 169 workflow_dispatch/schedule. => ~175 deterministic check/probe workflows vs ~17-30 LLM/provider runs (swarm runners run_6000_*, run_24h_* are scripts, started elsewhere).
- Fail-closed phrasing: ~3200 occurrences (md/py/json); 115 tool files use it; `model_output != execution_authority` 19x. spec_sha256 only 1 file (not a repo-wide mechanism). Create-only/O_EXCL: 6 py files. Evidence classes: TARGET_VPS 43 refs, EXACT_CURRENT_CI 2, LOCAL_EXECUTABLE 2 (weights in gateflow.py: 1.0/0.8/0.5/0.25/0).

## 2. Strongest deterministic components
- tools/preimage_bound_edit_guard_v1.py (170 L, tests 8 pass): contract JSON {path, preimage, proposed, allowed_old_line_range}; sha256 preimage binding + difflib; any change outside declared ranges = FAIL. Provider-free. Guarantee: proposal != truth.
- tools/git_source_identity_v1.py (125 L, 3 pass): HEAD/tree + hash of tracked diff bytes + every untracked file; canonical_sha = sha256 of sorted-key compact JSON. Gives exact "what was tested" identity.
- tools/trigger2_context_binding_split_guard_v1.py (210 L) + split_audit + canonical_atom_split_manifest + dynamic_binding_blueprint_v2_leakage_audit (415 L) + trainingtrace_family_split_linter: TRAIN/VAL/HOLDOUT leakage checks (model-visible surface minus codebook, template family reuse, atom reuse). 36 tests pass, 0 fail. Honest docstring: passing != independence.
- tools/gateflow.py + test_gateflow (11 pass): metric arithmetic over declared evidence (risk_retired = severity*evidence*disposition), WIP/lease limits (1 owner/1 falsifier/1 promoter per subcheck), staleness. Pure function of JSON.
- tools/validate_research_entity.py + check_provenance.py + schemas/: Draft-2020-12 validation + provenance role-vs-registry check.
- tools/archive_secret_scan.py (76 L), harness_ingress_trust_gate.py, current_execution_authority_lint_v1.py, execution_surface_resolver_v1.py, durable_work_cursor_v1.py: authority firewall / reentry primitives (pytest-backed).
- ClayCode: tools/claycode_base_{frontend,canonicalizer,ir,typed_ir,compiler}.py (+ *_validation.py): Lark LALR grammar -> canonical IR -> typed IR; canonical sha256 hashing; fuzz/differential/heldout corpora (wp11/wp12). NOT runnable here (no `lark`); manifest itself says compiler gate FAIL.
- Receipt discipline: receipts record git blob SHA-1 re-computed, exact command, exit_code, "runtime_credit" zeros for unproven layers (e.g. 2026-08-17 MicroVM receipt: 7 passed, kata/k8s/CNI credit = 0).

## 3. Measured test runs (copy, no network)
- test_gateflow 11 pass 1.3 s; preimage_guard 8 pass 0.8 s; git_source_identity 3 pass 0.9 s.
- 7 split/leak/secret/lint suites: 35 pass, 1 FAIL (authority-lint "projection consistent": failed on copy, likely partial-copy artefact; unverified).
- FULL tests/: 1977 passed, 204 failed, 10 collection errors, 2 xfail, 254 s. Failures cluster in xeno_*, zero_ucf_*, vps_control_sync, ucf_boot_ancestry (FileNotFound -> missing excluded dirs/runtime state). So ~90 % green on a degraded copy; true rate on a full clone UNBELEGT.
- rae doctor (copy): schema check FAIL (4 error lines: packets lacking required `summary`; status 'CLOSED_DIAGNOSTIC' not in enum), provenance check FAIL (actor_role disagrees with registry at ARTIFACT_PROVENANCE line 177), source_db ok. => the repo's own validators fail on its own data.

## 4. HONEST WEAKNESSES
- Scale vs substance: 620 tools/206 workflows, but ledgers hold 43 claims, 1/14 compiler WPs formally PASS, Frank v0.1 3 %. Mass of versioned one-offs (trigger1_*_v1..v13, claycode_*_v4..v21, restart_authority v1..v4): mostly dead/superseded variants, no index of which is live.
- Schemas: only 6, small, partly stale vs data (see doctor). Most gates define their own ad-hoc schema string ("CLAY_X/v1") and check in-code; no central registry.
- Hash "chains": no prev_hash chain found in tools/rae_core (grep 0). JSONL ledgers are append-by-convention + git history, not tamper-evident chains. Hashes are per-artifact bindings, not a chain.
- Fail-closed is largely DECLARED in prose (3200 mentions); executable enforcement is in the ~115 tool files only.
- Many receipts are authored by an LLM (GPT-5.6 Sol) via "container.exec" and verified by blob-hash recompute from GitHub fetches: trust root is the LLM report unless re-run. Repo marks items "NOT YET EXECUTABLY PROVEN" (found 3 files, e.g. controller verified-load rebind receipt, coordination delta T7).
- Evidence-class vocab inconsistent (METHOD_ONLY_SYNTHETIC_WORLD 48, REAL_SELF_HOSTED_UBUNTU_EXECUTION 23 vs gateflow TARGET_VPS...).
- Heavy runtime coupling: many tests need Linux runner state, llama.cpp, Qwen, VPS paths, lark; not portable.
- Deterministic = Python/JSON checks. LLM-judgment remains in: hypothesis generation, adjudication prose, swarm output, directive/steering .md (hundreds of "ALL_WORKERS_EXECUTION_DIRECTIVE" files steer behaviour by text, not code).

## 5. REUSE for us (mechanical acceptance layer)
Pattern: task spec JSON -> check script -> JSON verdict + exit code -> receipt.
1. preimage_bound_edit_guard_v1.py: `python3 tools/preimage_bound_edit_guard_v1.py --contract c.json` ; gate for any ChatGPT-worker file edit (scope + preimage hash). Best direct fit.
2. git_source_identity_v1.py: `python3 tools/git_source_identity_v1.py --repo . --require-clean` ; freeze/hash procedure: binds exact tested source state into receipt.
3. trigger2_context_binding_split_guard_v1.py (+ split_audit, canonical_atom_split_manifest): `python3 tools/trigger2_context_binding_split_guard_v1.py a.jsonl b.jsonl --audit-out out.json` ; leak/dup cross-split check. Needs adapting to our row format (expects CODEBOOK span + family fields): copy the logic (normalized-surface sha256, family/atom reuse), not the tool as-is.
4. validate_research_entity.py pattern + schemas/*.json: jsonschema Draft2020-12 per-record validation; adopt the pattern (our own schemas for task spec/receipt), reuse claim/event schemas only if we adopt their ledger.
5. gateflow.py weights/lease logic for worker-slot WIP limits and anti-Goodhart accounting (optional); receipt template of 2026-08-17 MicroVM receipt (command, exit_code, tested blob hashes, runtime_credit=0 for unproven layers) as our PASS/FAIL receipt shape.
Also: archive_secret_scan.py (leak of secrets in artefacts), harness_ingress_trust_gate.py (reject model-minted receipts) as concept.
Call standalone: all are argparse scripts with stdlib (+jsonschema); run from repo root; copy to a work dir, do not run inside the clone.

## 6. Do NOT adopt
- The 206-workflow / GitHub-Actions / VPS / ChatGPT-bridge control plane; swarm runners (run_6000_*, run_24h_*); steering-by-markdown directives.
- Versioned-variant sprawl (v1..v21); ClayCode compiler as dependency (gate FAIL, Lark, 161 tools) unless we need its canonical-IR hashing idea.
- Its vocabulary/authority hierarchy (TRIGGER, GO, evidence tiers) wholesale; its ledgers (43 claims) as truth.
- Anything marked LLM-authored "receipts" without our own re-execution.

## 7. UNBELEGT
- Full-clone test pass rate (copy degraded; 204 failures unattributed beyond sampling).
- Whether authority-lint failure is copy artefact.
- ClayCode compiler behaviour (lark missing, no network install).
- Workflow LLM/deterministic split is regex-based approximation, not read per file.
- Whether any workflow actually ran green on GitHub (no network).
- Hash-chain absence: grep only for common names; other chaining schemes may exist.
- "Percent deterministic" of the whole system: no measurement, only counts.
