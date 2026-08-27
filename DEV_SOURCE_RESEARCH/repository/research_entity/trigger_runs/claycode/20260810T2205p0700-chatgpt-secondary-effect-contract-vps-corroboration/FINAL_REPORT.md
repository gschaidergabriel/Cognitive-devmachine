# ClayCode — WP04 Production Effect Contract VPS Corroboration

Run: `20260810T2205p0700-chatgpt-secondary-effect-contract-vps-corroboration`  
Actor: `chatgpt-secondary` / OpenAI / GPT-5.6 Sol  
Persistent entity: Clay  
Research subject: `self.root` / Frank  
Program: `FRANK_V0_1`

## Result

A new target-repository discriminator and self-hosted Ubuntu VPS workflow were implemented and executed against the current canonical Frank effect sources.

Target commits:

- probe: `1e09c785004c4750dcb75d30054dd7de7b0e3685`
- workflow: `1699b55b6c083f60f2196411a9052fc84b86aa5f`
- VPS run: `31402743514`
- receipt: `runtime/vps_unifieddb/claycode_wp04_effect_contract_v1/LATEST.json`

Observed on the accepted Linux/X64 target lane:

- 17/17 contract/authority structure checks passed;
- exit status `0`;
- wall time `0.04 s`;
- max RSS `17152 kB`;
- socket messages sent/received `0/0`;
- external effect performed: `false`;
- one-argument production `execute` contract present: `false`.

The current exact production execution signature is:

`execute<T>(EffectIntent<T>, Capability, NodeId, EffectAttempt) -> EffectReceipt`

The required current lifecycle explicitly includes request/authorization, reservation, attempt creation, execution, independent verification and completion/re-entry semantics.

## Fused finding

Concurrent ClayCode work bound the same current `frank.effects` source and reproduced a G9 V3 mismatch: the current research G9 cycle still contains `Needle.execute(effect_intent)` with arity 1 and a structurally different `EffectIntent` record. The new target-VPS receipt independently corroborates the production side of that mismatch.

Therefore:

- G9 V3 direct one-argument effect execution is not an executable current production CallContract;
- WP04 must stay fail-closed at this boundary;
- the mismatch is an implementation/type-effect integration defect, not evidence that frozen ClayCode grammar/semantics require change;
- model/GWT/Needle output still cannot mint capability, authorization, reservation or attempt state.

## Goodman / anti-echo

The target-VPS execution is independent operational corroboration of the production contract, but not independent semantic ancestry: it executes a discriminator against the same canonical target sources. It therefore increases runtime confidence but does not justify scientific overpromotion.

No claim is made for:

- `CC-WP-04-TYPE-EFFECT = PASS`;
- Frank v0.1 acceptance;
- a new ClayCode primitive;
- an implicit one-argument Needle execution signature.

## Interconnect

Affected current components:

- `F-V01-02-CLAYCODE-COMPILER-RUNTIME`
- `F-V01-03-COGNITIVE-LOOP-CORE`
- `F-V01-07-NEEDLE-TRANSLATOR`
- `F-V01-09-EFFECT-AUTHORITY`
- `F-V01-13-SECURITY-RECOVERY-OBSERVABILITY`

ClayGraph consequence: keep semantic identity, graph epoch, salience and authority separate; no activation can repair a missing callable contract.

UnifiedDB consequence: exact authorization/reservation/attempt identities and epochs must remain transaction/replay-visible; a stale or mismatched identity must fail closed.

GWT consequence: selected/broadcast intent remains proposal/cognition; causal use and verified outcome remain distinct from effect authority.

Hyperposition consequence: unresolved alternative boundary mappings may remain represented, but none receives execution authority without an exact current contract.

## Negative result preserved

The earlier hypothesis that the problem might simply be an absent production execute contract is refuted for the current target source. A concrete guarded contract exists. The remaining defect is the exact typed binding from the cognitive/G9 representation into that contract.

## Next falsifiers

1. Consume the current imported-nominal-resolution VPS receipt when it is actually persisted; do not infer its outcome before then.
2. Bind exact module exports/imports so every nominal type resolves without `Any` or name-guessing.
3. Implement a deterministic typed G9/Needle boundary adapter using only current production contracts and trusted runtime state.
4. Prove that cognitive intent cannot supply/mint authenticated actor, capability, authorization, reservation or attempt state.
5. Add stale/tampered/revoked capability/authorization/epoch negatives and recovery/re-entry checks.
6. Re-run on the accepted target VPS before any WP04 promotion.

## Architecture disposition

`TESTING` / `NO_SEMANTIC_LANGUAGE_CHANGE`.

The correct near-term move is to finish binding and checking current semantics, not reopen ClayCode surface design.
