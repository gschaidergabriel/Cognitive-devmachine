#!/usr/bin/env python3
"""Patch candidate for the live FranKenstein avatar roll/eye registration bug.

This tool is deliberately exact-subject bound. It never touches the live file unless
called with that path explicitly, and refuses to operate if the input bytes are not
the measured subject from 2026-09-12.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

EXPECTED_SHA256 = "87cc0e3a94781f90a7533b129743597753876a8410b868767d243b753c5d3645"

OLD = """  kopfRollAusgleichDeg += (kopfRollWert - kopfRollAusgleichDeg) * 0.4;
  // Exakte Translations-Korrektur (siehe KOPF_ROLL_AUGEN_OFFSET oben) --
  // gleiche Lerp-Rate 0.4 wie die Rotation, damit beide Anteile beim
  // 5-Grad-Fotosprung synchron nachziehen, kein neuer Zeitversatz.
  const zielOffset = KOPF_ROLL_AUGEN_OFFSET[String(kopfRollWert)] || {dx:0, dy:0};
  augenOffsetDx += (zielOffset.dx - augenOffsetDx) * 0.4;
  augenOffsetDy += (zielOffset.dy - augenOffsetDy) * 0.4;
"""

NEW = """  // Geometrische Registrierung ist atomar mit dem bereits in kopfRollTick()
  // sichtbaren Foto-Schritt. Nur der gemeinsame #kopf-dreh/#koerper-dreh-Wrapper
  // darf federn. Eine lokale Lerp-Verzoegerung erzeugt sonst 2-3 Frames lang
  // absichtliche Fehlregistrierung zwischen Foto und Augen-/Blink-Overlay.
  kopfRollAusgleichDeg = kopfRollWert;
  const zielOffset = KOPF_ROLL_AUGEN_OFFSET[String(kopfRollWert)] || {dx:0, dy:0};
  augenOffsetDx = zielOffset.dx;
  augenOffsetDy = zielOffset.dy;
"""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def patch_text(text: str) -> str:
    count = text.count(OLD)
    if count != 1:
        raise SystemExit(f"exact target block count={count}, expected=1")
    out = text.replace(OLD, NEW, 1)
    # Fail closed if the obsolete local interpolation still survives anywhere.
    forbidden = [
        "kopfRollAusgleichDeg += (kopfRollWert - kopfRollAusgleichDeg) * 0.4;",
        "augenOffsetDx += (zielOffset.dx - augenOffsetDx) * 0.4;",
        "augenOffsetDy += (zielOffset.dy - augenOffsetDy) * 0.4;",
    ]
    leftovers = [x for x in forbidden if x in out]
    if leftovers:
        raise SystemExit(f"obsolete roll/eye interpolation remains: {leftovers}")
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
    print(f"OUTPUT={args.output}")
    print("PATCH_SCOPE=ROLL_PHOTO_TO_EYE_OVERLAY_ATOMIC_GEOMETRY_ONLY")


if __name__ == "__main__":
    main()
