# KMP — ClayCode Numeric Semantic Identity Boundary

- `packet_id`: KMP-CLAYCODE-NUMERIC-CANONICALIZATION-20260809
- `domains`: xeno_claycode, formal_methods_testing, storage_state_memory, performance_economics
- `topics`: semantic_hash, numeric_canonicalization, lowering, replay, cross-runtime
- `epistemic_class`: LOCAL_CROSS_RUNTIME_COMPONENT_EVIDENCE
- `status_hint`: OPEN_SUPPORTED_WORKING
- `origin_actor`: chatgpt-secondary
- `provider`: OpenAI
- `model`: GPT-5.6 Sol
- `source_run`: research_entity/trigger_runs/claycode/claycode_20260809T1705p0700_chatgpt_numcanon

## Atomic claim

Host-native numeric/JSON serialization is not a safe ClayCode semantic-identity boundary. Numeric leaves that participate in `semantic_hash` require explicit type-directed canonicalization, and executable lowerings must separately prove target-range/value preservation.

## Evidence

A local Python 3.13.5 vs Node v22.16.0 differential over 10,000 identical raw IEEE-754 binary64 bit patterns produced 204 host-native JSON presentation mismatches. An explicit candidate token (`f64:<raw-bits>` for finite values with explicit special-value tags) produced 0 cross-runtime token mismatches on the same corpus. Exact integer tokens also matched 0/9, while naive JavaScript `Number` lowering changed values including `9007199254740993 -> 9007199254740992`.

External primary specifications independently support the general boundary: canonical JSON requires deterministic numeric serialization; JavaScript Number and JSON have specific signed-zero/non-finite behavior; WebAssembly exposes special NaN semantics; Python's default JSON encoder permits non-standard NaN/Infinity tokens.

## Negative boundary

This packet does **not** prove cross-backend floating arithmetic determinism, select the final NaN payload policy, pass a BASE application exemplar, or justify new FRANK-specific ClayCode syntax.

## Architecture implication

Apply to CC-WP-03/04/06/11:

`typed source numeric value -> canonical semantic numeric token -> semantic_hash`

and separately:

`typed source numeric value -> target-range/effect validation -> backend numeric representation`

Never use host JSON presentation bytes as the semantic-value definition.

## Confidence

0.93 for the representation-level claim within tested numeric classes; lower for the final special-float policy.

## Falsifier / next test

Run the released production G9 parser/canonicalizer/type checker over a typed Int/F64 golden corpus, lower to at least two materially different backends, verify semantic-hash identity and executable value preservation, then repeat on the Ubuntu developer-system target and through H2 differential replay.
