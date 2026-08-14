# ClayCode — current G9 -> Frank v0.1 effect-boundary discriminator

Run: `20260810T2216p0700-chatgpt-secondary-effect-boundary-mismatch`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Program: `FRANK_V0_1`  
Persistent entity: Clay  
Research subject: `self.root` / human surface Frank  
Promotion: **NONE**

## 1. Why this run moved off stale WP03 bookkeeping

Current repository state is newer than the older ClayCode workspace snapshot. The live Frank-v0.1 target already has target-VPS WP04 contract evidence and a concurrent WP04 module-resolution lane. This run therefore avoided duplicating parser/TypedIR archaeology and followed the narrower current production effect boundary.

The active program is one finished Frank v0.1 target on the accepted Hostinger Ubuntu VPS. Historical BASE/H1/H2/H3 identifiers remain evidence only, not active product stages.

## 2. Exact current production evidence

The current target module `gschaidergabriel/Dr.-Unterweger:claycode/frank_effects.clay` is bound to Git blob:

`8679542da4f31b99ae4a171f86554ed894eb6e34`

and semantic SHA-256:

`10fbc45dca45fe09322b4ab7c0b6621547918dd6fa8e1d37be5817b26ab59544`

A current accepted-target-VPS receipt already exists:

- commit: `73724172ffd444ac09427bc64ed1e71ff112f0bf`
- GitHub run: `31402743514`
- evidence class: `REAL_SELF_HOSTED_ACCEPTED_TARGET_VPS_CLAYCODE_WP04_EFFECT_CONTRACT_DISCRIMINATOR`
- status: `PASS_CURRENT_PRODUCTION_EFFECT_CONTRACT`
- no external effect performed
- no WP04 or whole-Frank promotion claimed

The exact resolved production execution signature is:

`execute<T>(EffectIntent<T>, Capability, NodeId, EffectAttempt) -> EffectReceipt`

The same receipt verifies the explicit production chain:

1. `EffectRequest -> authorize_effect -> EffectAuthorization`
2. `EffectIntent + EffectAuthorization -> reserve_effect -> EffectReservationReceipt`
3. `EffectIntent + authorization + reservation + capability + node + idempotency -> begin_effect_attempt -> EffectAttempt`
4. `execute(intent, capability, node, attempt) -> EffectReceipt`
5. `verify_effect(EffectReceipt) -> VerifiedEffectReceipt`
6. `finish(VerifiedEffectReceipt) -> DoneReceipt`

It also verifies that a one-argument production execute contract is absent.

## 3. Cross-source mismatch found

Current G9 V3 still contains both:

- a rule saying `Needle.lowers EffectIntent -> concrete_adapter_plan`; and
- a cycle branch that directly calls `Needle.execute(effect_intent)`.

Its cognitive `EffectIntent` shape is also different from the current target runtime `EffectIntent<T>` shape.

Therefore the current G9 V3 line cannot be treated as an exact production CallContract. It is at best shorthand for a not-yet-materialized typed lowering boundary.

### Result

**SUPPORTED:** current G9 V3 direct effect execution is not structurally bindable as-is to the current production Frank v0.1 effect API.

This closes a narrower question than the older generic "is G9 effect semantics lowerable to Linux?" research. The older result remains useful: no new language primitive is required merely because host enforcement is concrete. The present defect is in implementation/type-effect boundary realization.

## 4. New executable cross-source discriminator

Committed artifacts:

- `3b3a6580875432efa7f371134ae6732a488f1939` — provenance-bound current target effect contract snapshot
- `0003239b14a1ec0070012d8784f71229fe73e9a8` — G9-to-target structural compatibility probe
- `6d9fb95c38bad6b77d55f5f453ebc532878d091d` — self-hosted Ubuntu workflow for the cross-source probe

The probe is intentionally fail-closed. Its success condition is reproduction of the incompatibility; that is negative architecture evidence, never Frank acceptance.

At report time its dedicated persisted CI receipt had not appeared, so no new target-VPS execution credit is claimed for this probe. The exact target production side is nevertheless already independently target-VPS verified by run `31402743514` above.

## 5. Higher-value WP04 authority-provenance falsifier

Cross-reading the exact target policy exposed a second question.

Current target source makes:

- `EffectAuthorization` opaque;
- `Capability` opaque;
- but `EffectRequest` structurally constructible, with value fields including `actor`, `authenticated` and `scoped_capability`.

The current executable Python policy oracle similarly represents `EffectRequest` as a normal frozen dataclass and evaluates authentication/capability facts from those values.

That is not by itself a production exploit. A correct ClayCode module/type/effect/runtime boundary may prevent untrusted cognition from constructing such a request or invoking authorization functions.

But value equality alone cannot encode trusted origin. Therefore WP04 needs an explicit falsifier for authority provenance, not merely correct policy decisions on trusted fixtures.

New target-repository artifacts:

- `f81f28cd8c1481c082446b678e7527b7348cb13b` — `authority_provenance_gap_probe.py`
- `fbc908ef80cb1aecaa34e7e34a250c067a1cb4f5` — accepted-target-VPS workflow

The probe compares:

- an intended authenticated reversible-write request produced by the existing trusted test helper; and
- a directly constructed structurally identical request with `AUTHENTICATED_USER`, `authenticated=true`, `scoped_capability=true` and rollback-safe state.

It performs no external effect. It asks only whether the current value-level gate has any request-origin dimension.

At report time the persisted target-VPS receipt was still pending. Therefore the result remains a **candidate authority-provenance gap**, not a promoted security finding.

## 6. Architecture delta

Committed candidate:

`5a70bde2948611d4f0349c0514348cba780365e0`

Decision:

**Do not weaken the production effect lifecycle to match the G9 shorthand. Do not enlarge ClayCode semantics yet. Implement the missing deterministic typed Needle boundary.**

The boundary must:

- consume cognitive effect intent as proposal only;
- resolve exact action/target/payload from current typed semantic state;
- source authenticated actor/current credential scope from trusted runtime state, never model/GWT text;
- resolve an opaque current capability from trusted capability state;
- construct/evaluate the exact production `EffectRequest` path;
- obtain authorization;
- atomically reserve before external attempt;
- create an attempt bound to authorization/reservation/node/idempotency/capability;
- call exact current `frank.effects.execute/4`;
- preserve unknown-outcome/reconciliation semantics;
- independently verify outcome;
- re-enter only provenance-valid verified outcome before DONE.

Forbidden shortcuts include fuzzy signature inference, stale contract credit, token-presence-as-unlimited-authority and any model-minted authorization/capability/attempt object.

## 7. Goodman anti-echo

Older Ubuntu effect-boundary result:

`c999441a759c8f319d27090c0768e9d6762b8d6a`

That run showed that G9 capability/effect semantics could plausibly lower to Linux enforcement without new language primitives. It did not have today's concrete Frank-v0.1 lifecycle contract.

Current verdict: **REFINED, NOT REFUTED**.

The semantic idea survives. The current source wiring does not.

A WebAssembly Component Model/WIT primary-source comparison was used only as an engineering prior: explicit typed interfaces use named typed parameters and results. It does not supply or justify Frank production signatures; those remain bound only to current project source and target-VPS receipts.

Goodman review commit:

`bd9169bb4a641c295f5c70d563c46c6cb1f6a465`

## 8. Mesh re-entry

Interconnect commit:

`6ed4a8f12aa653f1ac5390b6c2df10bc2cb3253d`

Branch consequences:

- **claycode:** WP04 must resolve exact typed/provenance authority boundaries before effect execution admission.
- **frank:** preserve current guarded effect lifecycle; do not bend it around cognitive shorthand.
- **harness:** add malicious-construction, stale authority, replay, idempotency, verification and re-entry tests for the final adapter.
- **unifieddb:** contract/component/binary/state-lineage/lease currentness remain separate provenance dimensions.
- **gwt:** effect selection/ignition never supplies authentication or authority.
- **claygraph:** topology is diagnostic; graph similarity cannot resolve signatures or authority.
- **hyperposition:** retain competing adapter/binding candidates until executable evidence selects one.
- **emergenz:** no emergence claim follows from a more elaborate effect pipeline.
- **q23:** perception/model confidence remains non-authoritative downstream input.

## 9. Concurrent WP04 work respected

A sibling target-repository lane is currently building deterministic module/import nominal resolution rather than mapping unresolved types to `Any`. This run did not duplicate that lane. The authority-provenance discriminator is orthogonal: after names resolve, the checker still has to prove that an untrusted module cannot mint trusted authority facts merely by constructing structurally valid values.

## 10. External-knowledge delta

Current official WebAssembly Component Model WIT documentation supports explicit typed interface boundaries as a mature component-ABI design pattern. That is useful for ClayCode lowering design, especially exact named parameters/results and explicit interface worlds.

It is deliberately not used to infer Frank-specific signatures, authority classes or runtime identities.

## 11. What is actually achieved

Achieved now:

- current target production effect contract located and bound to exact target-VPS receipt;
- G9 V3 one-argument execute shorthand conclusively rejected as a current production CallContract;
- exact production execute/4 and lifecycle obligations materialized into a durable cross-source snapshot;
- executable cross-source compatibility probe and VPS workflow committed;
- typed Needle boundary architecture candidate committed;
- new authority-provenance negative-control probe and target-VPS workflow committed;
- mesh feedback and Goodman review committed;
- no semantic-language churn introduced.

Not achieved / not claimed:

- no WP04 PASS;
- no Typed-Needle adapter implementation yet;
- no proof yet that malicious ClayCode construction is reachable or blocked in production;
- no external effect execution by this run;
- no whole Frank v0.1 acceptance;
- no paid/final model training authorization.

## 12. Next highest-information falsifier

The next ClayCode step is now sharply defined:

1. create a malicious ClayCode fixture that attempts to construct authenticated/capability authority facts and invoke `authorize_effect`;
2. create the trusted-runtime counterpart fixture;
3. finish enough WP04 module/type universe resolution to type both exactly;
4. require the type/effect checker to reject the malicious fixture for authority-provenance/effect-capability reasons while accepting the trusted runtime path;
5. bind the accepted path to the exact production lifecycle and current `self.root` binary/state/lease identity;
6. run both on the accepted Hostinger Ubuntu VPS;
7. only then implement/connect the G9 -> Needle adapter in the real cycle.

That test distinguishes a real machine-enforced authority boundary from a policy object that is correct only when callers are assumed trustworthy.

## 13. Durable run artifacts

- `TARGET_FRANK_EFFECT_CONTRACT_SNAPSHOT.json`
- `claycode_effect_boundary_compatibility_probe.py`
- `ARCHITECTURE_DELTA.json`
- `FRANK_CLAYCODE_GOODMAN_REVIEW.json`
- `INTERCONNECT_MANIFEST.json`
- `EXECUTABLE_RESEARCH_RECEIPT.json`
- `FINAL_REPORT.md`

Research delta: **COMMITTED**.  
Remote execution: **existing production contract PASS; newly added cross-source/provenance probes pending persisted receipts**.  
Frank v0.1: **IN_PROGRESS / NOT PASS**.
