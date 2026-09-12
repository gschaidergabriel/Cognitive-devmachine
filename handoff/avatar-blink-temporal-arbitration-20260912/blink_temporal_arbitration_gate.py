#!/usr/bin/env python3
"""Fail-closed static gate for FranKenstein Avatar blink timing/arbitration.

Read-only: parses one buehne.html supplied by the caller and emits JSON.
It does not modify files, open browsers, contact services, or infer promotion.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def fail(msg: str) -> None:
    raise SystemExit(msg)


def timing_range(src: str, fn: str) -> tuple[float, float]:
    pat = rf"function\s+{re.escape(fn)}\s*\(\)\s*\{{\s*return\s+([0-9.]+)\s*\+\s*Math\.random\(\)\s*\*\s*([0-9.]+)\s*;\s*\}}"
    m = re.search(pat, src)
    if not m:
        fail(f"cannot parse {fn}")
    base, span = map(float, m.groups())
    return base, base + span


def between(src: str, start: str, end: str) -> str:
    a = src.find(start)
    b = src.find(end, a + len(start)) if a >= 0 else -1
    if a < 0 or b < 0:
        fail(f"cannot isolate block: {start!r} .. {end!r}")
    return src[a:b]


def z_index(src: str, selector: str) -> int:
    m = re.search(rf"{re.escape(selector)}\s*\{{[^}}]*?z-index\s*:\s*(-?\d+)", src, re.S)
    if not m:
        fail(f"cannot parse z-index for {selector}")
    return int(m.group(1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("html", type=Path)
    ap.add_argument("--expected-sha256", default=None)
    args = ap.parse_args()

    raw = args.html.read_bytes()
    import hashlib
    sha = hashlib.sha256(raw).hexdigest()
    if args.expected_sha256 and sha != args.expected_sha256:
        fail(f"preimage mismatch: expected={args.expected_sha256} observed={sha}")
    src = raw.decode("utf-8")

    close = timing_range(src, "blinzelDauerSchliessen")
    hold = timing_range(src, "blinzelDauerGeschlossenHalten")
    opening = timing_range(src, "blinzelDauerOeffnen")

    close_total = (9 * close[0], 9 * close[1])
    open_total = (3 * opening[0], 3 * opening[1])
    total = (
        close_total[0] + hold[0] + open_total[0],
        close_total[1] + hold[1] + open_total[1],
    )

    playback = between(src, "function blinzelAbspielen", "function blinzelWeiterPlanen")
    special = between(src, "function sonderausdruckZeigen", "window.sonderausdruckZeigen")

    playback_has_runtime_guard = "_sonderLaeuft" in playback
    special_hides_blink = bool(re.search(r'augen-blink[\s\S]{0,160}?opacity\s*=\s*["\']0["\']', special))
    special_clears_phase = bool(re.search(r"blinzelPhase\s*=\s*null", special))

    blink_z = z_index(src, "#augen-blink")
    expr_z = z_index(src, "#ausdruck-schicht")

    timing_corridor_ok = total[0] >= 250.0 and total[1] <= 350.0
    asymmetry_ok = close_total[1] < open_total[0]
    arbitration_ok = playback_has_runtime_guard and special_hides_blink and special_clears_phase

    # Informational only: code interval. Intent is contradictory in current source comments.
    sm = re.search(r"setTimeout\(\(\)\s*=>\s*blinzeln\(true\),\s*([0-9.]+)\s*\+\s*Math\.random\(\)\s*\*\s*([0-9.]+)\s*\)", src)
    interval = None
    if sm:
        ibase, ispan = map(float, sm.groups())
        interval = [ibase, ibase + ispan]

    result = {
        "schema": "FRANK_AVATAR_BLINK_TEMPORAL_ARBITRATION_GATE/v1",
        "subject": {"path": str(args.html), "sha256": sha},
        "timing_ms": {
            "close_frame": list(close),
            "close_9_frames": list(close_total),
            "closed_hold": list(hold),
            "open_frame": list(opening),
            "open_3_frames": list(open_total),
            "total": list(total),
            "corridor_250_350_ok": timing_corridor_ok,
            "close_strictly_faster_than_open_across_support": asymmetry_ok,
        },
        "arbitration": {
            "blink_z_index": blink_z,
            "special_expression_z_index": expr_z,
            "blink_can_cover_expression_if_visible": blink_z >= expr_z,
            "playback_rechecks__sonderLaeuft": playback_has_runtime_guard,
            "special_expression_immediately_hides_blink": special_hides_blink,
            "special_expression_clears_blink_phase": special_clears_phase,
            "ok": arbitration_ok,
        },
        "scheduler_interval_ms_informational": interval,
        "gate": "PASS" if timing_corridor_ok and asymmetry_ok and arbitration_ok else "FAIL",
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
