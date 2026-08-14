# Harness deep continuation — Frank v0.1 direct ingress/security convergence

**Run:** `harness-20260810T2037p0700-deep-frank-v01-ingress`  
**Actor:** chatgpt-secondary / OpenAI / GPT-5.6 Sol  
**Final active program:** `FRANK_V0_1`  
**Target:** `self.root` / human-surface Frank v0.1 on accepted Hostinger Ubuntu VPS  
**Research authority:** Clay Research Entity implementation/test authority  
**Target self-Harness authority:** PROPOSAL_ONLY  
**Promotion result:** **NO PROMOTION** — direct target validation remains red/unknown

## 1. Program drift handled during the run

The run began under the historical staged Harness workspace. While it was executing, the project owner-fixed program was superseded to one active target only: `FRANK_V0_1`. H1/H2/H3 and separate Reference/Clay Harness releases became historical evidence/diagnostic methods, not active stages or release blockers.

The worker stopped using H1 progress semantics, preserved already-built H1 artifacts as immutable lineage, closed its old H-WP-14/H-WP-17 claims as legacy evidence, and re-entered material results into the unified Frank v0.1 program.

## 2. Historical freeze drift discriminator

The 2026-08-09 Reference Harness architecture freeze was confirmed stale relative to owner-fixed 2026-08-10 semantics. A versioned compatibility overlay was created rather than rewriting the historical baseline.

The strengthened gate checks:

- base architecture semantic hash;
- exact contract hash;
- seven owner-fixed additive modules;
- twelve owner-fixed state-contract families;
- seventeen acceptance families;
- identity/language/agency/web/authority invariant tokens;
- target identity (`self.root`, Frank surface, server-binary, target VPS);
- five exact owner-fixed source-path bindings with Git blob SHA presence.

Local reference controls demonstrated:

- legacy base without overlay: rejected;
- exact base + overlay: accepted by compatibility preflight;
- semantic-hash mutation: rejected;
- exact-contract-hash mutation: rejected;
- unhashed required source binding: rejected.

This gate is now historical diagnostic evidence only under `FRANK_V0_1`, not an H1 release product.

## 3. External security evidence changed the test surface

Fresh 2026 primary research sharpened the owner-fixed open-web boundary:

- **Agent Data Injection / arXiv:2607.05120**: trusted-looking data fields or metadata can become an attack surface even when instruction-like content is separately controlled; therefore envelope-level `instruction_authority=NONE` is not a sufficient test by itself.
- **VIGIL / ACL 2026, 2026.acl-long.443**: verify-before-commit over streamed tool results is a useful competing defensive mechanism.
- **Persistent control / arXiv:2605.31042**: untrusted control-like content may become durable through an intermediate workspace write and activate later; therefore taint must survive persistence/re-read.
- **UCM / arXiv:2607.05277**: privilege-separated trusted/untrusted web observation is a competing mechanism that must be benchmarked rather than assuming field-level taint is uniquely best.

These papers were used to create test obligations and countermechanisms, not to promote a production architecture from literature alone.

## 4. New reference mechanism: field-level ingress trust

Research-side reference implementation:

- `tools/harness_ingress_trust_gate.py`
- `tests/test_harness_ingress_trust_gate.py`
- `tools/harness_ingress_trust_fuzz.py`

Core distinction:

```text
content channel trust
!= field trust
!= field verification
!= commit authority
!= effect authority
```

Untrusted channels include open web, untrusted tool results, external visual data and external files. Authenticated direct messages remain a separate scoped-intent channel.

Security-sensitive fields include authority, instruction/effect authority, actor/caller/author identity, resource identity, credential scope, tool call/result identity, confirmation receipt, current-instance lease, binary identity, state lineage and provenance origin.

A sensitive field is verified only when a trusted verifier binds the exact field name + exact value hash + provenance. Model confidence, GWT ignition, ClayGraph salience and translator style are explicitly non-verifiers.

Even a verified `resource_identity` does **not** authorize an effect. Control-surface commit additionally requires independent trusted commit authority. Untrusted persistent-control writes are blocked.

## 5. Executed reference results

### Deterministic adversarial matrix

**14 / 14 PASS**.

Covered cases include:

- plain web claim as data-only;
- instruction-like web text preserved as data-only;
- untrusted effect-authority field blocked;
- spoofed trusted author label quarantined;
- independently verified metadata admitted only as data;
- verified resource identity cannot mint effect authority;
- verified resource + authenticated scoped intent can reach the next effect gate;
- untrusted persistent-control write blocked even with caller commit authority;
- model confidence cannot verify security metadata;
- mismatched verification hash rejected;
- visual instruction cannot enter executable configuration;
- authenticated direct message stays a distinct scoped-intent channel;
- delimiter/structure-looking payload stays opaque data;
- malformed field structure quarantined.

### Property fuzz

Seed: `1729`  
Cases: **25,000**  
Property violations: **0**

Decision distribution:

```text
ALLOW_DATA_ONLY   644
ALLOW_SCOPED      1,169
ALLOW_VERIFIED    3,918
BLOCK_COMMIT      8,238
QUARANTINE       11,031
TOTAL            25,000
```

### Mutation sensitivity control

Mutation: remove the independent trusted commit-authority requirement from untrusted control-surface writes.

Same seed / same 25,000 generated cases:

- detected invariant violations: **708**;
- first violation: case **7**;
- first failure class: `PASS_WITHOUT_TRUSTED_CONTROL_COMMIT_AUTHORITY`.

Interpretation: the property corpus is not a vacuous always-pass test; it is sensitive to removal of the central authority separation.

Evidence class remains `LOCAL_DETERMINISTIC_SANDBOX_REFERENCE`, not production acceptance.

## 6. Direct Frank v0.1 source audit

Current target main observations:

### `claycode/frank_security.clay`

Still keys `SecurityState.frank` and `security_boot` to `Frank.id`. It provides repository/capability gates but no field-level web/tool/visual taint semantics.

### `claycode/frank_runtime.clay`

Still contains `one_entity_across_nodes`, conflicting with the owner-fixed server-binary/state-lineage `self.root` boundary in which clients/provider peers are external capabilities/relations rather than SELF.

### `claycode/frank_effects.clay`

Already provides a useful effect skeleton:

```text
intent -> capability match/currentness -> final_security_gate -> execute -> independent observation -> DONE
```

Therefore the ingress mechanism should feed this existing authority/effect architecture rather than create a second effect system.

### `claycode/frank_api_fabric.clay`

This is a provider capability/credential registry, not the required inbound production token-authenticated Frank API. The inbound API remains a separate unfinished Frank-v0.1 obligation.

## 7. Direct target code candidate

Draft target PR: **gschaidergabriel/Dr.-Unterweger #105**  
Branch: `clay/frank-v01-ingress-trust-20260810`

Discriminator-first commits were created before production code so initial failure could be retained as negative evidence.

Candidate production file:

`claycode/frank_web_ingress.clay`

Candidate semantics include:

- `target_native_self = self.root`;
- typed untrusted channels versus authenticated direct message;
- field-level trust state;
- exact value-hash/provenance verification receipts;
- explicit non-authority signals;
- data-only open-web admission;
- separate direct-token scoped intent;
- verify-before-commit;
- no untrusted persistent-control write;
- no untrusted commit-authority minting;
- no implication that verified resource identity authorizes an effect;
- no absolute prompt-injection-impossibility claim.

This file is a **candidate**, not promoted production semantics. It is not yet compiled/type-checked through the current target runtime or integrated into the corrected self.root runtime path.

## 8. Direct CI evidence — negative and unresolved

Observed target PR #105 conformance runs:

1. `31395289386` at head `73e2f293...`: **FAIL** — expected before production candidate existed.
2. `31395431336` at head `a98e5253...`: **FAIL** after candidate addition; cause UNKNOWN because decoded logs unavailable.
3. `31395735324` at head `29c5ca66...`: **FAIL** after explicit PR-head-SHA checkout binding; cause still UNKNOWN.
4. `31396108926` at head `04646fb7...`: **FAIL** after workflow was changed to upload diagnostic JSON under `if: always()` before final enforcement.

For run 4, GitHub reports **zero uploaded artifacts**. This narrows the likely failure to checkout/job/action infrastructure or another pre-upload path, but does not prove the candidate itself passed. Exact step remains UNKNOWN.

`Frank Deep Integrity` is independently failing on the same PR heads. Logs/steps were not available through the connector, so its cause is not attributed to the ingress candidate.

Direct target CI status therefore remains:

```text
TARGET_VALIDATION = FAIL/UNKNOWN_CAUSE
CANDIDATE_PROMOTION = DENIED
```

## 9. Strongest counterhypothesis

The field-level mechanism may be unnecessary or over-restrictive.

Possible simpler explanation:

- structured external JSON already strips instruction authority;
- current `frank.effects` capability checks and final security gate already prevent effect escalation;
- the Python reference models control surfaces that the actual ClayCode runtime never exposes;
- field-level verification could add latency, state amplification and false blocking without reducing real target attack success.

This counterhypothesis remains LIVE.

Required comparison:

```text
A = current envelope-only structured non-authority boundary + existing effect gate
B = A + field-level taint/value-hash/provenance verification + verify-before-commit
C = privilege-separated browsing/sandbox isolation baseline
```

Measure real attack success, false-block rate, latency, CPU/RAM/state amplification, restart/replay correctness and legitimate tool/web utility on the target VPS.

## 10. Architecture consequence

The strongest current architecture direction is not “more filters.” It is a four-boundary composition:

```text
untrusted observation
-> field-level evidence identity/provenance
-> verified semantic admission
-> independent scoped commit authority
-> existing deterministic effect authority
```

This prevents four concepts from collapsing into one:

```text
observed data != verified data != authorized state change != authorized external effect
```

It also matches the existing project law that GWT/ClayGraph/model/translator signals can bias cognition but cannot mint authority.

## 11. Program re-entry

During this run the project moved to the unified `FRANK_V0_1` program. Material output was re-entered at:

`research_entity/frank_v0_1/evidence/20260810T2059p0700_harness_ingress_security_reentry.json`

CI tail:

`research_entity/frank_v0_1/evidence/20260810T2105p0700_harness_ingress_ci_tail.json`

Open direct work item:

GitHub issue **#187** — integrate and target-validate field-level ingress trust after CI transport repair.

Affected active packages:

- F-V01-01 identity/server-binary;
- F-V01-08 token API/clients;
- F-V01-09 effect authority;
- F-V01-10 proactive agency/web;
- F-V01-13 security/recovery/observability;
- F-V01-16 end-to-end acceptance.

The Clay live-fusion worker also absorbed the evidence and independently retained `promotion=NONE`.

## 12. Exact next frontier

1. Recover a usable target-repo CI execution/log channel or alternate equivalent target execution receipt.
2. Compile/type-check `frank_web_ingress.clay` with the current ClayCode compiler.
3. Complete the owner-fixed self.root identity migration first or jointly, avoiding a mixed runtime where the new ingress module is self.root-native but runtime/security remains `Frank.id`/`one_entity_across_nodes`.
4. Route real open-web/tool/visual ingress through the candidate boundary.
5. Bind legitimate effect requests into existing `frank.effects` rather than duplicating effect authority.
6. Execute deterministic corpus and property fuzz against real target pathways.
7. Add persistence/restart/re-read attacks to prove taint survives workspace/UnifiedDB roundtrips.
8. Compare envelope-only vs field-level vs privilege-separated baselines.
9. Measure false positives, latency, RAM and state amplification.
10. Promote only after target-VPS and full Frank Deep Integrity receipts pass.

## 13. Final evidence judgment

**Supported now:** field-level provenance + independent commit authority is a falsifiable, mutation-sensitive defensive mechanism worth direct Frank v0.1 testing.

**Not supported yet:** that it is superior to simpler baselines on the real target; that PR #105 is correct ClayCode; that CI failure is caused by the candidate; that prompt injection is impossible; that F-V01-10/F-V01-13 are complete.

**Concrete progress delivered:** new executable reference gate, adversarial test matrix, 25k property fuzz, mutation control, target-source audit, direct target PR/code candidate, four CI negative receipts, unified Frank-v0.1 evidence re-entry, live-fusion uptake and an explicit target-validation work item.
