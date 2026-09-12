#!/usr/bin/env python3
"""Patch buehne.html so canonical eye overlays survive special expressions.

This is deliberately separate from the asset builder. Promotion order is:
1) atomically stage/swap canonical-eye expression assets;
2) patch HTML so gaze + blink remain enabled during _sonderLaeuft.
Rollback order is the reverse.
"""
from __future__ import annotations
import argparse
import hashlib
from pathlib import Path

EXPECTED_HTML_SHA256 = "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

BLINK_OLD = '''function blinzeln(zeitplanNeu = true){
  if(_sonderLaeuft){
    if(zeitplanNeu) blinzelWeiterPlanen(); // Kette haelt, kein zweiter Strang
    return;
  }
  const schritte = [];'''
BLINK_NEW = '''function blinzeln(zeitplanNeu = true){
  // 2026-09-12 canonical-eye invariant: Sonderausdruck-Frames have their
  // own eye pixels neutralized offline, so the ONE canonical blink channel
  // remains valid here too. No second scheduler is created.
  const schritte = [];'''

GAZE_OLD = '$("pupillen-glow").style.opacity = _sonderLaeuft ? "0" : String(ziel.opazitaet);'
GAZE_NEW = '''// 2026-09-12 canonical-eye invariant: special-expression frames no longer
  // own a competing eye identity. Keep the same measured gaze signal active.
  $("pupillen-glow").style.opacity = String(ziel.opazitaet);'''

COMMENT_OLD = '''// ⭐ 2026-09-11: waehrend eines Sonderausdrucks aus -- dessen Frames tragen
  // ihre eigenen Augen, sonst laege der Erkennungs-Glimmer auf einem fremden
  // Gesicht (zweites Augenpaar statt zweiter Kopf).'''
COMMENT_NEW = '''// Sonderausdrucks-Frames werden vor Promotion mit
  // build_canonical_eye_expressions.py im gemessenen Augenbereich auf den
  // kanonischen Neutral-Kopf zurueckgefuehrt. Deshalb bleibt der EINZIGE
  // Erkennungs-Glimmer auch waehrend _sonderLaeuft derselbe.'''

BLINK_COMMENT_OLD = '''// BlinzelWeiterPlanen() zurueck. Blinzeln bleibt unabhaengig von der
// Gesichtserkennung (das Lid braucht kein Signal); nur #pupillen-glow
// bleibt erkennungs-gekoppelt. Läuft NICHT ueber einem Sonderausdruck
// (dessen Frames tragen ihre eigenen Augen).'''
BLINK_COMMENT_NEW = '''// BlinzelWeiterPlanen() zurueck. Blinzeln bleibt unabhaengig von der
// Gesichtserkennung (das Lid braucht kein Signal); nur #pupillen-glow
// bleibt erkennungs-gekoppelt. Seit 2026-09-12 laeuft derselbe kanonische
// Blink-Kanal auch ueber Sonderausdruecken; deren konkurrierende Augenpixel
// werden vor Promotion offline neutralisiert.'''

def replace_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    if n != 1:
        raise SystemExit(f"FAIL {label}: expected exactly 1 match, got {n}")
    return text.replace(old, new, 1)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input_html", type=Path)
    ap.add_argument("output_html", type=Path)
    ap.add_argument("--allow-hash-drift", action="store_true",
                    help="diagnostic only; never use for promotion")
    args = ap.parse_args()

    raw = args.input_html.read_bytes()
    got = sha256_bytes(raw)
    if got != EXPECTED_HTML_SHA256 and not args.allow_hash_drift:
        raise SystemExit(f"FAIL live HTML preimage drift: {got}")

    text = raw.decode("utf-8")
    text = replace_once(text, BLINK_OLD, BLINK_NEW, "blink special-expression guard")
    text = replace_once(text, GAZE_OLD, GAZE_NEW, "gaze special-expression suppression")
    text = replace_once(text, COMMENT_OLD, COMMENT_NEW, "gaze ownership comment")
    text = replace_once(text, BLINK_COMMENT_OLD, BLINK_COMMENT_NEW, "blink ownership comment")

    if '_sonderLaeuft ? "0" : String(ziel.opazitaet)' in text:
        raise SystemExit("FAIL stale gaze suppression survived")
    if "if(_sonderLaeuft){\n    if(zeitplanNeu) blinzelWeiterPlanen()" in text:
        raise SystemExit("FAIL stale blink suppression survived")

    out = text.encode("utf-8")
    args.output_html.write_bytes(out)
    print(f"OK preimage_sha256={got}")
    print(f"OK output_sha256={sha256_bytes(out)}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
