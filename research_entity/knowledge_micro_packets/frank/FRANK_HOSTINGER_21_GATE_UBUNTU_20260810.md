<!-- RAE_META
{"packet_id":"FRANK_HOSTINGER_21_GATE_UBUNTU_20260810","title":"Hostinger runner executes 21/21 Frank Ubuntu integrity gates with resource receipts","domains":["frank","harness","performance"],"topics":["Hostinger","GitHub Actions","Ubuntu","integrity","resource measurement"],"epistemic_class":"MEASURED_RESULT_SUMMARY","claim_status_hint":"CURRENT","origin_class":"REMOTE_EXECUTION_RECEIPT","origin_actor":"chatgpt-secondary","created_at":"2026-08-10T00:08:00+07:00","updated_at":"2026-08-10T00:08:00+07:00","source_refs":["gschaidergabriel/Dr.-Unterweger:runtime/vps_integrity/latest.json","research_entity/reports/20260810T0007p0700_CHATGPT_FRANK_V01_DEEP_RESEARCH_VPS_FUSION.md"],"evidence_refs":["gschaidergabriel/Dr.-Unterweger@5aa980244630d63f8ecbe6f2a5a31482ff12a19f","gschaidergabriel/Dr.-Unterweger@097e3fb86ce74d7f66cf9db8d9824ea1bb3345ab"],"related_claim_ids":["FRANK-HOSTINGER-BUILDTEST-001"],"related_experiment_ids":[],"predecessor_packet_ids":[],"supersedes_packet_ids":[],"confidence":"HIGH_FOR_EXACT_TESTED_EFFECT","verification_required":true,"falsifier_or_next_test":"Repeat comparable matrix across multiple commits and reproduce final stack on Andreas' designated Ubuntu developer system.","search_terms":["21/21","Hostinger runner","digital-retina","gate RSS","pytest Frank Ubuntu"]}
RAE_META -->

### Core
The self-hosted GitHub runner `clay` on Ubuntu/Linux executed the current Frank deep-integrity matrix at commit `097e3fb...` with 21/21 gates PASS. The matrix took 10,469 ms wall time; measured child processes summed 3.954190 s user CPU, 0.955706 s system CPU, and a 66,216 KiB peak single-gate RSS.

### Evidence / boundary
This is real remote execution evidence for the exact tested code and host. `pytest_all` also passed 17 tests. It is not a whole-Frank release receipt and does not measure Qwen4B resident memory, sustained inference, energy, thermals, or Andreas-PC behavior.

### Implication
Hostinger is now a proven priority remote Ubuntu build/test lane rather than merely a connected runner.

### Next test
Repeat the matrix for variance calibration and later reproduce the integrated release candidate on Andreas' actual Ubuntu system.
