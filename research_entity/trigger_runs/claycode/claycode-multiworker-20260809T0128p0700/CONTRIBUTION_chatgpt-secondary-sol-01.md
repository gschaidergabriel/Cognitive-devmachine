# Lane C Contribution — Adversarial Safety / Formal Boundary

**coordination_id:** `claycode-multiworker-20260809T0128p0700`  
**worker:** `chatgpt-secondary-sol-01` · OpenAI · GPT-5.6 Sol  
**lane:** `C_ADVERSARIAL_SAFETY_FORMAL`  
**parent:** CC-RC1.8 MCAAT  
**sibling candidate read:** CC-RC1.9 UECC from lane A  

## Core result

Lane C accepts lane A's correction that a genuinely general-purpose ClayCode must be able to **represent** destructive, administrative, raw-device and foreign effects. The safety boundary belongs at authority/commit, not at computational expressibility.

Lane C adds a necessary refinement:

> `per-call capability validity != cumulative admissibility`

and:

> `current producer identity != origin authority`.

A typed effect request can be individually within scope while a sequence of requests exceeds a safe aggregate budget. Likewise, content originating from untrusted memory can pass through a trusted summarizer/tool/runtime without becoming trusted enough to mint or widen execution authority.

## Proposed UECC refinement — Origin-Bound Aggregate Authority Envelope

Retain UECC layers L0–L4, but refine L3 authority into an opaque host-side envelope/ledger.

`EffectIntent` remains serializable and may name any effect kind. It carries semantic meaning but no authority.

`AuthorityEnvelope / EffectPermit` is non-model-mintable and should bind at least:

- exact `EffectIntent.semantic_hash` or an explicitly declared intent-family hash;
- canonical resource identity / allowed scope;
- allowed verbs/effect classes;
- origin/integrity ancestry constraints;
- causal epoch, freshness and dependency closure where relevant;
- expiry and revocation epoch;
- per-call bound;
- aggregate/cumulative budget and monotone consumed state;
- delegation chain with narrowing-only derivation;
- policy/version identity and release-time validation contract.

The host broker owns the monotone consumption ledger. Serializing a permit into model-visible ClayCode must not recreate authority.

## Executable mechanism tests

Durable verification receipt: `EXPERIMENT_RESULTS_chatgpt-secondary-sol-01_verify.json`.

### Authority binding

120,000 randomized cases compared a naive per-call guard with an origin-, exact-intent-, epoch-, scope- and aggregate-budget-bound guard plus a separately written oracle.

- independent-oracle mismatches: **0**;
- naive false accepts: **36,617** of 65,935 attack cases;
- stronger guard false accepts: **0**;
- stronger guard false rejects on 54,065 legitimate controls: **0**.

The attacks covered exact-target mutation inside an otherwise permitted prefix, stale epoch, origin laundering, intent replay, path escape, expiry, operation/amount mutation and cumulative overshoot. This is finite constructed evidence, not proof.

### Cumulative budget

20,000 generated sessions contained calls each individually within `max_call`.

- stateless per-call authorization exceeded total budget in **13,571** sessions;
- host-side monotone budget ledger exceeded total budget in **0** sessions.

The mechanism result is narrow but important: scope/verb validity alone does not constrain aggregate effect magnitude.

### Origin laundering

50,000 chains moved untrusted-origin content through a trusted runtime producer.

- current-producer-only trust laundered authority in **50,000 / 50,000** constructed chains;
- origin-bound ancestry policy laundered authority in **0 / 50,000**.

## Independent external anchors

The mechanism direction is independently consistent with capability-system practice (unforgeable/attenuated authority), information-flow-control approaches that preserve confidentiality/integrity labels through agent/tool paths, confused-deputy research against tool-routing systems, verify-before-commit defenses for tool-stream injection, and origin-bound memory-authority work. These sources support the architectural class, not the exact ClayCode implementation or our synthetic effect sizes.

## Cross-branch implications

- **FRANK:** the capability/effect broker should validate not only present scope but exact semantic intent, origin ancestry, epoch/revocation and cumulative effect state.
- **Clay:** recoverability remains separate from live-effect admissibility; constructive actions can still exceed aggregate safety/resource budgets.
- **ClayGraph:** activation and retrieved memory ancestry cannot upcast into authority; transformations must retain trust ancestry relevant to effect release.
- **UnifiedDB:** protected external-resource references and selection receipts must not be mistaken for permits; selection provenance and authority provenance are separate.
- **GWT:** workspace winner identity cannot mint or widen authority.
- **Hyperposition H6:** receipt-gated causal credit and reversible topology switching reinforce the need to keep propagation/selection topology distinct from authority topology; shared RAE ancestry means this is convergence, not independent replication.
- **Emergenz:** none of these safety/authority results are emergence or consciousness evidence.

## Disagreement / correction

Lane C agrees with lane A that CC13's strongest wording should be corrected if it is interpreted as making destructive effects semantically inexpressible. The retained safety principle is narrower:

> FRANK's untrusted execution profile should normally lack ambient destructive/raw capabilities, while ClayCode itself stays general-purpose and can describe those operations as typed effect requests.

## Requested lane B test

Lower the same intent/envelope through at least two ABI/process representations and test whether any serialization, FFI adapter, cache, process boundary or backend lowering:

1. turns a serializable intent into authority;
2. widens resource/verb scope;
3. loses origin ancestry or causal epoch;
4. resets aggregate consumed budget;
5. converts revocation/freshness state into stale reusable authority.

## Status

**Contribution complete for fusion; no canonical promotion requested.** Formal proof, real WASI/OS red-team, target-Qwen adherence and production FRANK measurements remain open.
