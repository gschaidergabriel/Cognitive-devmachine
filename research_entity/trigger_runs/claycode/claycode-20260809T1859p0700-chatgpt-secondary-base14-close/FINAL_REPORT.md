# ClayCode BASE14 blocker-resolution run

Run: `claycode-20260809T1859p0700-chatgpt-secondary-base14-close`
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol
Canonical parent: revision 2 / `04234efdb86c78d32262e8274685df3aca3d2b2a13402e00bf47658a3f489346`

## User objective

Resolve the fourteen ClayCode BASE work-package blockers using every available mechanism, without fabricating target-host or Full-FRANK evidence.

## Outcome

The run converted the former broad 14-item OPEN state into an executable closure pipeline and isolated the remaining honest blockers.

- `CC-WP-01-SPEC-FREEZE`: already formal PASS.
- `CC-WP-02..09`, `CC-WP-11`, `CC-WP-12`: implementation closure paths now exist and are routed through the fail-closed Andreas Ubuntu target gate. They remain formally OPEN until target receipts exist.
- `CC-WP-10`: real target receipt generator exists for nine classes; APP-10 `FULL_FRANK_HANDOFF` is intentionally not fabricated.
- `CC-WP-13`: real frozen FRANK packet-score/subsystem handoff exists; complete H2 ActiveAssembly behavior remains the executable counterexample.
- `CC-WP-14`: final fail-closed auditor and required top-level manifest now exist; the gate remains FAIL while earlier blockers remain.

Current declared release state: `GENERAL_PURPOSE_GATE=FAIL`.

## Material defects found and repaired

1. **P1 parser/canonical identity loss** — anonymous literal terminals could disappear from ordinary Lark trees, so semantically different operator mutations could collide in structural fingerprints. Literal-preserving validation/canonicalization and V7 named operator identity now protect this boundary.
2. **P0 process authority laundering** — an earlier runtime API allowed invocation-time process allowlists. Process authority is now fixed into a runtime-minted policy and current runtime hardening pins executable identity/fingerprint.
3. **P0 arbitrary callable laundering** — an earlier async API accepted caller-provided Python callables. It now accepts only runtime-owned named operations admitted by the sealed capability policy.
4. **P1 stale CI grammar selection** — strict frontend gating was still wired to superseded repair candidates. Current target closure explicitly selects V7.
5. **P1 duplicate compiler semantics** — a new pure vertical slice briefly differed from the integrated BASE compiler on integer division. It was collapsed into a compatibility facade over the integrated compiler; one executable arithmetic/type semantics remains.
6. **P1 stale target application path** — target gate referenced the obsolete app-proxy API after runtime hardening. It now uses the sealed-capability V2 preflight and includes package/effect-runtime integration.

All known P0/P1 software defects from this sweep are CLOSED in `research_entity/claycode/BASE_DEFECT_LEDGER.json`. Evidence gaps remain release blockers and are not mislabeled as software bugs.

## New/updated executable artifacts

### Frontend / parser / canonicalization
- `tools/claycode_base_frontend_validation.py`
- `tools/claycode_base_canonicalizer.py`
- `tools/claycode_base_canonicalizer_validation.py`
- `tools/claycode_v6_fn_regression.py`
- V7 strict/full-corpus target wiring

### Compiler / IR / type / evaluator / lowering
- `tools/claycode_base_pure_toolchain.py` consolidated on `tools/claycode_base_compiler.py`
- `tools/claycode_base_pure_toolchain_validation.py`
- `research_entity/claycode/base/examples/PURE_CORE_V1.clay`

### Runtime / authority / ABI / FFI / resource semantics
- hardened `tools/claycode_base_runtime.py`
- adversarial `tools/claycode_base_runtime_validation.py`
- `tools/claycode_base_stdlib_extensions.py`
- `tools/claycode_base_resource_lifetime_validation.py`
- retained independent `tools/claycode_base_runtime_gateway.py` cross-check

### Packages
- `tools/claycode_base_package_compiler.py`
- `tools/claycode_base_package_validation.py`
- `research_entity/claycode/base/examples/package_demo/*`

### Applications
- `tools/claycode_base_application_proxy_suite_v2.py`
- `tools/claycode_andreas_application_acceptance.py`
- real target receipt schema requires source/artifact hashes, expected/observed, positive/negative tests and explicit non-authority.

### Fuzz / corpus
- `tools/claycode_base_fuzz_conformance.py`
- `tools/claycode_base_corpus_generator.py`
- deterministic family-first train/heldout leak-audit path

### FRANK handoff
- `research_entity/claycode/base/examples/FRANK_ACTIVE_ASSEMBLY_SCORE_V1.clay`
- `tools/claycode_frank_score_handoff_validation.py`
- current H1/H2/H3 mapping retained as the handoff semantic contract.

### Target closure / audit
- hardened `tools/claycode_andreas_ubuntu_target_gate.py`
- `tools/claycode_andreas_base14_closure.py`
- `tools/claycode_base_wp14_audit.py`
- `research_entity/claycode/BASE_DEFECT_LEDGER.json`
- `CLAYCODE_GENERAL_PURPOSE_COMPILER_MANIFEST.json`

## Remaining executable counterexample: Full FRANK H2 ActiveAssembly

The current H1→H2 mapping requires H2 to preserve:

- typed packet/provenance/ancestry identity;
- semantic epoch/version validity;
- bounded relevance/impact/novelty/uncertainty;
- unresolved conflict alternatives;
- deterministic bounded selection and ancestry diversity;
- re-expansion reference identity;
- deterministic assembly semantic hash;
- `capability visibility != bearer authority`;
- no authority mint from model, peer, Needle, Retina/MVC, graph activation or GWT.

Direct compiled ClayCode evidence currently covers the packet scoring subsystem, not the complete behavior above. Per the project owner's "less change, more compile" law, this is now the one named language/compiler/runtime counterexample. A FRANK-specific opaque host call is forbidden as a fake solution. First try generic typed collection/resource/FFI/runtime realization; only an executable failure may justify changing ClayCode semantics.

## Target-host dependency

This ChatGPT worker has GitHub R/W but no terminal connector to the physical Andreas Ubuntu developer system. Therefore it cannot honestly mint target-host PASS receipts in this session.

The target has one canonical convergence command:

```bash
CLAYCODE_TARGET_HOST_ID=ANDREAS_UBUNTU_LINUX_DEVELOPER_SYSTEM python tools/claycode_andreas_base14_closure.py
```

That command is designed to run target component gates, resource-lifetime tests, nine real application classes, then the WP14 auditor. It is expected to remain nonzero until the genuine Full-FRANK handoff exists.

## Promotion decision

**NO PROMOTION.**

Formal BASE status remains FAIL because target receipts and Full-FRANK H2/H3 readiness are not yet proven. This preserves the rule that measurements and real execution outrank implementation intent.

## Next falsifier

Implement the H2 ActiveAssembly behavior using only generic ClayCode/runtime mechanisms, then differential-test H1 ordinary code versus H2 on identical randomized/adversarial packet sets. Require equivalent bounded assembly/conflict/authority invariants and deterministic semantic receipts. Run the complete closure command on Andreas Ubuntu and let `tools/claycode_base_wp14_audit.py` decide promotion.
