#!/usr/bin/env python3
"""Build a timing-only Avatar blink shadow from one exact production preimage.

Changes exactly three scalar timing functions and nothing else. The source file
is never modified. Output is a separate caller-chosen path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

EXPECTED_SOURCE_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"

REPLACEMENTS = {
    "function blinzelDauerSchliessen(){ return 15 + Math.random()*5; }":
        "function blinzelDauerSchliessen(){ return 11 + Math.random()*2; }",
    "function blinzelDauerGeschlossenHalten(){ return 30 + Math.random()*20; }":
        "function blinzelDauerGeschlossenHalten(){ return 40 + Math.random()*15; }",
    "function blinzelDauerOeffnen(){ return 40 + Math.random()*12; }":
        "function blinzelDauerOeffnen(){ return 46 + Math.random()*9; }",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--manifest", type=Path, required=True)
    args = ap.parse_args()

    raw = args.source.read_bytes()
    source_sha = sha256(raw)
    if source_sha != EXPECTED_SOURCE_SHA256:
        raise SystemExit(
            f"SOURCE_DRIFT expected={EXPECTED_SOURCE_SHA256} observed={source_sha}"
        )
    text = raw.decode("utf-8")

    counts = {}
    for old, new in REPLACEMENTS.items():
        n = text.count(old)
        counts[old] = n
        if n != 1:
            raise SystemExit(f"AMBIGUOUS_PREIMAGE occurrence_count={n} needle={old!r}")
        text = text.replace(old, new, 1)

    candidate = text.encode("utf-8")
    if candidate == raw:
        raise SystemExit("NO_CHANGE")

    # Fail closed on collateral edits: applying the inverse transform must
    # recover the exact source bytes.
    inverse = text
    for old, new in REPLACEMENTS.items():
        if inverse.count(new) != 1:
            raise SystemExit(f"POSTIMAGE_AMBIGUOUS needle={new!r}")
        inverse = inverse.replace(new, old, 1)
    if inverse.encode("utf-8") != raw:
        raise SystemExit("ROUNDTRIP_MISMATCH")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_bytes(candidate)
    manifest = {
        "schema": "FRANK_AVATAR_BLINK_TIMING_SHADOW/v1",
        "source_sha256": source_sha,
        "candidate_sha256": sha256(candidate),
        "changed_function_count": len(REPLACEMENTS),
        "exact_old_occurrence_counts": counts,
        "timing_ms": {
            "close_9_frames": [99, 117],
            "closed_hold": [40, 55],
            "open_3_frames": [138, 165],
            "total": [277, 337],
            "close_strictly_faster_than_open": True,
            "inside_declared_250_350_corridor": True,
        },
        "scope": "TIMING_ONLY_SHADOW_NO_LIVE_WRITE",
        "live_mutation": False,
        "semantic_arbitration_change": False,
        "asset_change": False,
        "css_change": False,
    }
    args.manifest.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
