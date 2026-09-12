#!/usr/bin/env python3
"""Exact-subject candidate patch for rolled-head / mouth-overlay registration.

This does NOT mutate production unless somebody explicitly points source/output at
production. Default use should be source -> scratch output. It is bound to the
current production buehne.html SHA observed by Local Bridge on 2026-09-12.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"

# Exact manifest geometry already documented in the live source.
CANVAS_W = 1536.0
CANVAS_H = 1024.0
NECK_X = 768.0
NECK_Y = 600.0
MOUTH_X = 622.0
MOUTH_Y = 352.0
MOUTH_W = 295.0
MOUTH_H = 182.0

ORIGIN_X_PCT = (NECK_X - MOUTH_X) / MOUTH_W * 100.0
ORIGIN_Y_PCT = (NECK_Y - MOUTH_Y) / MOUTH_H * 100.0

OLD_CSS = '''  #mund-effekt{position:absolute;left:40.49%;top:34.38%;width:19.21%;height:17.77%;
    z-index:4;pointer-events:none;
    transition:opacity .06s linear}'''

NEW_CSS = f'''  #mund-effekt{{position:absolute;left:40.49%;top:34.38%;width:19.21%;height:17.77%;
    transform-origin:{ORIGIN_X_PCT:.8f}% {ORIGIN_Y_PCT:.8f}%;
    z-index:4;pointer-events:none;will-change:transform;
    transition:opacity .06s linear}}'''

OLD_JS = '''  $("augen-blink").style.transform =
    `translate(${augenDxCss.toFixed(2)}px, ${augenDyCss.toFixed(2)}px) rotate(${kopfRollAusgleichDeg.toFixed(2)}deg)`;
}'''

NEW_JS = '''  $("augen-blink").style.transform =
    `translate(${augenDxCss.toFixed(2)}px, ${augenDyCss.toFixed(2)}px) rotate(${kopfRollAusgleichDeg.toFixed(2)}deg)`;
  // The roll-image generator and the CSS patch transform have the same rotation.
  // The expand+bottom-center repin difference is therefore one common translation
  // for every point in the head crop. Reuse the already measured atomic roll
  // translation for the neutral-coordinate mouth/face patch; only its own
  // transform-origin differs because the patch box starts at manifest anchor 622,352.
  $("mund-effekt").style.transform =
    `translate(${augenDxCss.toFixed(2)}px, ${augenDyCss.toFixed(2)}px) rotate(${kopfRollAusgleichDeg.toFixed(2)}deg)`;
}'''


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_text(text: str) -> str:
    if text.count(OLD_CSS) != 1:
        raise SystemExit(f"CSS target count={text.count(OLD_CSS)}, expected=1")
    if text.count(OLD_JS) != 1:
        raise SystemExit(f"JS target count={text.count(OLD_JS)}, expected=1")
    out = text.replace(OLD_CSS, NEW_CSS, 1).replace(OLD_JS, NEW_JS, 1)
    if out.count('$("mund-effekt").style.transform') != 1:
        raise SystemExit("mouth transform writer is not unique after patch")
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--allow-subject-sha", default=EXPECTED_SHA256)
    args = ap.parse_args()

    raw = args.source.read_bytes()
    actual = sha256_bytes(raw)
    if actual != args.allow_subject_sha:
        raise SystemExit(
            f"SUBJECT_MISMATCH expected={args.allow_subject_sha} actual={actual}; refusing patch"
        )
    text = raw.decode("utf-8")
    out = patch_text(text).encode("utf-8")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(out)
    print(f"SOURCE_SHA256={actual}")
    print(f"OUTPUT_SHA256={sha256_bytes(out)}")
    print(f"MOUTH_TRANSFORM_ORIGIN={ORIGIN_X_PCT:.8f}% {ORIGIN_Y_PCT:.8f}%")
    print(f"OUTPUT={args.output}")
    print("PATCH_SCOPE=ROLL_PHOTO_TO_MOUTH_OVERLAY_ATOMIC_GEOMETRY_ONLY")


if __name__ == "__main__":
    main()
