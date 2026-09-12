#!/usr/bin/env python3
"""Fail-closed source gate for the Avatar roll/eye registration chain.

This is intentionally a *source-coherence* gate only.  It proves that the live
HTML uses one pose value for the visible roll frame, blink patch and pupil glow,
and that the pose-specific offset table is complete for the 11 admitted roll
frames.  It does not claim perceptual acceptance; a matched real-browser A/B is
still required for that scope.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any

EXPECTED_ROLLS = tuple(range(-25, 26, 5))


def _fail(checks: list[dict[str, Any]], name: str, detail: str) -> None:
    checks.append({"check": name, "ok": False, "detail": detail})


def _pass(checks: list[dict[str, Any]], name: str, detail: str = "") -> None:
    checks.append({"check": name, "ok": True, "detail": detail})


def _function_body(text: str, name: str) -> str | None:
    marker = f"function {name}("
    start = text.find(marker)
    if start < 0:
        return None
    brace = text.find("{", start)
    if brace < 0:
        return None
    depth = 0
    quote: str | None = None
    escaped = False
    template = False
    i = brace
    while i < len(text):
        ch = text[i]
        if quote:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == quote:
                quote = None
        elif template:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == "`":
                template = False
        else:
            if ch in ("'", '"'):
                quote = ch
            elif ch == "`":
                template = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[brace + 1 : i]
        i += 1
    return None


def _parse_offsets(text: str) -> dict[int, tuple[float, float]]:
    obj = re.search(
        r"const\s+KOPF_ROLL_AUGEN_OFFSET\s*=\s*\{(?P<body>.*?)\}\s*;",
        text,
        re.S,
    )
    if not obj:
        return {}
    pairs: dict[int, tuple[float, float]] = {}
    pat = re.compile(
        r'["\'](?P<deg>-?\d+)["\']\s*:\s*\{\s*dx\s*:\s*(?P<dx>-?\d+(?:\.\d+)?)\s*,\s*dy\s*:\s*(?P<dy>-?\d+(?:\.\d+)?)\s*\}'
    )
    for match in pat.finditer(obj.group("body")):
        pairs[int(match.group("deg"))] = (float(match.group("dx")), float(match.group("dy")))
    return pairs


def assess(text: str) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    offsets = _parse_offsets(text)
    keys = tuple(sorted(offsets))
    if keys == EXPECTED_ROLLS:
        _pass(checks, "offset_table_complete", f"keys={list(keys)}")
    else:
        missing = sorted(set(EXPECTED_ROLLS) - set(keys))
        extra = sorted(set(keys) - set(EXPECTED_ROLLS))
        _fail(checks, "offset_table_complete", f"missing={missing} extra={extra}")

    if offsets.get(0) == (0.0, 0.0):
        _pass(checks, "neutral_offset_zero")
    else:
        _fail(checks, "neutral_offset_zero", f"value={offsets.get(0)!r}")

    roll_tick = _function_body(text, "kopfRollTick")
    roll_step = _function_body(text, "kopfKoerperDrehSchritt")
    loop = _function_body(text, "schleife")
    gaze = _function_body(text, "gazeSchritt")

    if roll_tick and "kopfRollWert = schritt.w" in roll_tick:
        _pass(checks, "visible_frame_updates_pose_value")
    else:
        _fail(checks, "visible_frame_updates_pose_value", "kopfRollTick assignment missing")

    if loop:
        i_tick = loop.find("kopfRollTick(t)")
        i_anchor = loop.find("kopfKoerperDrehSchritt()")
        if 0 <= i_tick < i_anchor:
            _pass(checks, "same_frame_order", "roll frame commits before eye transform")
        else:
            _fail(checks, "same_frame_order", f"tick={i_tick} anchor={i_anchor}")
    else:
        _fail(checks, "same_frame_order", "schleife() missing")

    if roll_step:
        required = {
            "atomic_pose_rotation": "kopfRollAusgleichDeg = kopfRollWert",
            "offset_from_same_pose": 'KOPF_ROLL_AUGEN_OFFSET[String(kopfRollWert)]',
            "blink_uses_dx": "augenOffsetDx * _kopfCanvasScale",
            "blink_uses_dy": "augenOffsetDy * _kopfCanvasScale",
            "blink_uses_rotation": "rotate(${kopfRollAusgleichDeg.toFixed(2)}deg)",
        }
        for name, token in required.items():
            if token in roll_step:
                _pass(checks, name)
            else:
                _fail(checks, name, f"token missing: {token}")
    else:
        for name in (
            "atomic_pose_rotation",
            "offset_from_same_pose",
            "blink_uses_dx",
            "blink_uses_dy",
            "blink_uses_rotation",
        ):
            _fail(checks, name, "kopfKoerperDrehSchritt() missing")

    if gaze:
        required = {
            "glow_uses_same_dx": "dx + augenOffsetDx * _kopfCanvasScale",
            "glow_uses_same_dy": "dy + augenOffsetDy * _kopfCanvasScale",
            "glow_uses_same_rotation": "rotate(${kopfRollAusgleichDeg.toFixed(2)}deg)",
        }
        for name, token in required.items():
            if token in gaze:
                _pass(checks, name)
            else:
                _fail(checks, name, f"token missing: {token}")
    else:
        for name in ("glow_uses_same_dx", "glow_uses_same_dy", "glow_uses_same_rotation"):
            _fail(checks, name, "gazeSchritt() missing")

    origin = re.search(r"#kopf-dreh\s*\{[^}]*transform-origin\s*:\s*50%\s+58\.59%", text, re.S)
    if origin:
        _pass(checks, "neck_origin_bound", "50% 58.59%")
    else:
        _fail(checks, "neck_origin_bound", "expected neck transform-origin missing")

    ok = all(c["ok"] for c in checks)
    return {
        "schema": "FRANK_AVATAR_ROLL_ANCHOR_SOURCE_GATE/v1",
        "ok": ok,
        "scope": "SOURCE_COHERENCE_ONLY_NOT_PERCEPTUAL_OR_PRODUCTION_PROMOTION",
        "roll_offsets": {str(k): {"dx": v[0], "dy": v[1]} for k, v in sorted(offsets.items())},
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--html", required=True, type=Path)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()
    try:
        text = args.html.read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"schema": "FRANK_AVATAR_ROLL_ANCHOR_SOURCE_GATE/v1", "ok": False, "error": str(exc)}))
        return 2
    result = assess(text)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
