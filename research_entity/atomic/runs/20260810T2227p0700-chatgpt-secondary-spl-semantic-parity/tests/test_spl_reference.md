# SPL-001 reference test manifest

The executable discriminator was run locally against the semantics encoded in `candidate/CANDIDATE_ATOMIC_SPL_001.clay`.

## Executed suites

### Main fault differential

- seed: `20260810`
- total cases: `100000`
- deliberately corrupted typed candidates: `56486`
- valid candidates: `43514`
- fault classes: negation drop, modality escalation, person swap, quantity mutation, question->command, read->write, allow->deny, tomorrow->now
- TYPE_ONLY false allow: `56486/56486`
- SAME_CODEC_ROUNDTRIP false allow: `56486/56486`
- independent full validator false allow: `0/56486`
- SPL false allow: `0/56486`
- independent full validator valid false deny: `0/43514`
- SPL valid false deny: `0/43514`

### Independent replications

Seeds `20260811..20260815`, each 40,000 cases, total 200,000 additional cases.

Every replication reproduced:

- TYPE_ONLY corrupt false-allow rate = 1.0;
- SAME_CODEC_ROUNDTRIP corrupt false-allow rate = 1.0;
- independent full validator false allow = 0;
- SPL false allow = 0;
- independent full validator false deny = 0;
- SPL false deny = 0;
- independent full validator p50 latency lower than SPL p50 in this Python controlled-language proxy.

### Per-field causal lesion

For every fault class that changed exactly one hard coordinate, the corresponding sole SPL field oracle was removed. The corruption escape rate became `1.0` for person, negation, modality, quantity, temporal, speech-act, permission and effect-intent faults.

Interpretation: the v0.1 oracle is causally necessary but not redundant.

### UNKNOWN / ambiguity

2,526 deliberately unsupported hard-field forms were injected in the main run's ambiguity control. SPL false acceptance was zero. The full validator also did not accept them.

### ExpressionState proxy lesion

5,000 typed frames were each rendered with four soft style wrappers. Recovered hard-field drift was zero in this deterministic proxy. This is not evidence for a learned/state-aware German renderer.

### Binding/replay controls

- 10,000 shuffled source-hash bindings: reject rate `1.0` in proxy.
- 10,000 stale schema/version controls: reject rate `1.0` in proxy.

### Checker common-mode fault and redundancy rescue

52,053 active corruptions were run with a validator/oracle deliberately sharing the main translator's systematic fault.

- one faulty full validator: false-allow `1.0`;
- one faulty SPL family: false-allow `1.0`;
- two full validators, one faulty and one exact: false-allow `0.0`;
- dual SPL families, one faulty and one exact: false-allow `0.0`.

p50 latency in this micro-harness:

- faulty full: `5.979 us`;
- two full: `7.791 us`;
- faulty SPL: `48.292 us`;
- dual SPL: `22.944 us`.

This rescue is ordinary redundancy; it does not establish unique SPL fault containment.

## Scope limitations

The benchmark language is intentionally controlled German with explicit hard-field markers. It is a semantic mechanism/fault discriminator, not a natural-language quality benchmark. No claim is made about:

- unrestricted German coverage;
- real DE_TO_CLAY model error distribution;
- real CLAY_TO_DE fluency;
- target-VPS latency/RAM/CPU;
- token/model inference cost;
- ASVB origin-authentication correctness;
- final effect-authority correctness.

Those remain real-system tests, now tracked by target issue `#162`.
