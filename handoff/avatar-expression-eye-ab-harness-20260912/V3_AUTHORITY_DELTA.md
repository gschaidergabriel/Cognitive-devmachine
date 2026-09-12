# V3 authority delta — special-expression eye A/B

Status: **SOURCE-READY READ-ONLY PRE-GATE — NO LIVE MUTATION / NO RUNTIME CREDIT**

This delta closes the specific authority hole that caused recent special-expression staging and shadow-harness attempts to fail for infrastructure/source-binding reasons rather than avatar semantics.

## Exact bound subject

- `buehne.html`: `18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e`
- `buehne_daemon.py`: `5527a1510e4101bcd97a9f57317580638757485d929a9b8e68c3d0ea9d91fcd2`
- productive localized open eye, `augen_blink_relief2/blink_000.png`: `8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9`
- productive gaze, `augen_gaze_relief2/rotglow_tracking_master.png`: `8e07af6c8fd44eb00816c4c94f6716cbd078159ab6808152650a5861385d28ef`

## What `expression_eye_authority_gate_v3.py` proves before v2 visual A/B is interpreted

1. Local bytes for all four exact subjects match the expected hashes.
2. Stable public HTTP `/`, `/augen_blink/blink_000.png`, and `/augen_gaze/rotglow_tracking_master.png` resolve to those exact productive bytes; the harness never hard-codes `_relief2` into browser URLs.
3. The isolated browser has exactly one `#kopf-dreh`, one `#augen-blink`, and one `#pupillen-glow`; both eye layers are descendants of the same head transform authority.
4. After entering a real special expression, the harness observes the browser's actual changed image URL rather than guessing a path.
5. Any active `/ausdruck_erweitert/.../stufe_*.png` route is fetched over HTTP and compared byte-for-byte with the corresponding file under `ausdruck_erweitert_relief2`.
6. All bound live source/assets are re-hashed after the probe. Any mutation fails the gate.

The gate deliberately does **not** decide visual quality. If it passes, run the existing v2 clipped A/B harness on the same unchanged subject. Only the combination of exact authority PASS + v2 visual/compositing PASS can justify considering a reversible live semantic-eye integration.

## Failure classification

A V3 failure is `SOURCE/AUTHORITY/HARNESS_NEGATIVE` unless it specifically demonstrates a product-visible rendering failure. It must not trigger arbitrary eye/head mutation.

The current canonical eye-mask candidate remains the single mask authority. This branch does not introduce another mask, another eye asset, or another transform chain.
