# SPL-001 design refutation

## Result

`SPL-001` is **not supported as a distinct Frank v0.1 architecture component by the current synthetic proxy**.

The experiment produced two useful positives:

1. same-codec semantic roundtrip can be perfectly self-consistent while being wrong with respect to source semantics under systematic/common-mode faults;
2. independent hard-field validation can detect those modeled errors and explicit UNKNOWN handling can fail closed.

Neither positive is unique to SPL.

## Main discriminator

Across 100,000 main controlled-German cases, 56,486 candidate frames were deliberately corrupted in an active hard field.

- TYPE_ONLY false-accepted 56,486/56,486 corruptions.
- SAME_CODEC_ROUNDTRIP false-accepted 56,486/56,486 corruptions.
- SPL detected 56,486/56,486, with zero false deny on 43,514 valid cases.
- A conventional independent full semantic validator also detected 56,486/56,486 with zero false deny.
- The independent full validator was faster in this Python proxy: p50 3.044 us versus SPL p50 5.187 us; p95 3.375 us versus 5.968 us.

Five independent 40,000-case replications reproduced the qualitative result: both strong mechanisms had 0 false allow / 0 false deny, and the full validator had lower p50 latency in every replication.

## Ablation refutation

SPL v0.1 used one narrow oracle per hard field. When the oracle for the actually corrupted field was removed, every one-field corruption in that class escaped:

- person: 100%
- negation: 100%
- modality: 100%
- quantity: 100%
- temporal: 100%
- speech act: 100%
- permission: 100%
- effect intent: 100%

Therefore the v0.1 'lattice' was factorized validation, not genuine redundant parity for a coordinate.

## Rescue attempt

A second oracle family was added in a checker-fault experiment. One oracle/full-validator family was deliberately given the same systematic fault as the main translator.

On 52,053 activated corruptions:

- one faulty full validator: 100% false allow;
- one faulty SPL family: 100% false allow;
- two full validators (faulty + exact): 0% false allow;
- dual SPL families (faulty + exact): 0% false allow.

The dual SPL rescue therefore demonstrated ordinary redundancy/failure-diversity, not unique SPL behavior. Two full validators achieved the same fault containment and were faster in this micro-harness (p50 7.791 us versus dual SPL 22.944 us).

## Prior-art collision

This negative decision is reinforced by external research:

- per-run translation validation is established;
- reduced products combine independently analyzed abstract observations;
- N-version software is established and known to suffer correlated failures;
- metamorphic MT testing is established;
- round-trip/lens consistency is established.

SPL may still be a useful **implementation decomposition** if real German validation shows tiny hard-field sensors are substantially cheaper than a second full semantic parser/model. That resource hypothesis was not measured here and cannot rescue architecture promotion now.

## Surviving durable result

Do not make `German -> Clay -> German` roundtrip success a sufficient Frank v0.1 translator acceptance criterion.

Required release obligation:

1. independent source-to-hard-Clay semantic validation for owner-hard fields, or a demonstrably equivalent independent oracle path;
2. explicit UNKNOWN/AMBIGUOUS instead of silent success when a hard source field cannot be independently established;
3. common-mode fault corpus in which same-codec roundtrip remains stable but source truth is wrong;
4. per-field lesion tests proving every hard field has an actual validator;
5. ExpressionState noninterference tests;
6. source/request/version witness binding and stale-witness rejection;
7. compare any partial-oracle implementation against a strong full independent validator on real German and target-VPS resources before adopting it.

## Architecture decision

`NO_ARCHITECTURE_PROMOTION_FROM_SYNTHETIC_PROXY`

SPL remains a possibility only under this reopen condition:

> A real German / target-VPS differential demonstrates matched hard-field safety with materially lower bounded compute/RAM/latency or stronger independently measured fault containment than the smallest conventional independent validator.
