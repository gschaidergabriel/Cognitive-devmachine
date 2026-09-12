#!/usr/bin/env python3
"""Build a non-live HTML candidate for canonical eye identity semantics.

Fail-closed and writes only to --out. The canonical public URL remains
/augen_blink/...; the daemon's current BLINK_DIR authority resolves that route
to augen_blink_relief2. This avoids creating a second serving authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

EXPECTED_HTML_SHA256 = (
    "18770d8e333af1bc49a818da4dbd5c2e482b859e0142d0213df6c956184c931e"
)
EXPECTED_OPEN_RELIEF2_SHA256 = (
    "8ab1a11c6f8a738e34c516bbf65c00e0f48de70c7341bfa970f236e002c94fc9"
)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


def replace_one(text: str, old: str, new: str, name: str) -> tuple[str, int]:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{name}: expected exactly one occurrence, got {count}")
    return text.replace(old, new, 1), 1


def require_one(text: str, needle: str, name: str) -> None:
    count = text.count(needle)
    if count != 1:
        raise RuntimeError(f"{name}: expected exactly one occurrence, got {count}")


def rewrite_css_rule(text: str, selector: str, transform, name: str) -> tuple[str, int]:
    match = re.search(re.escape(selector) + r"\{[^}]*\}", text, re.S)
    if not match:
        raise RuntimeError(f"{name}: missing CSS rule {selector}")
    old = match.group(0)
    new = transform(old)
    if new == old:
        raise RuntimeError(f"{name}: rule transform was a no-op: {old!r}")
    return text[: match.start()] + new + text[match.end() :], 1


def find_braced_region(text: str, open_brace: int) -> tuple[int, int]:
    depth = 0
    for index in range(open_brace, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return open_brace, index + 1
    raise RuntimeError("unterminated braced region")


def extract_function(text: str, signature: str, name: str) -> tuple[int, int, str]:
    start = text.find(signature)
    if start < 0:
        raise RuntimeError(f"{name} signature not found")
    brace = text.find("{", start)
    if brace < 0:
        raise RuntimeError(f"{name} opening brace not found")
    _, end = find_braced_region(text, brace)
    return start, end, text[start:end]


def rewrite_blink_function(text: str) -> tuple[str, dict[str, object]]:
    """Remove only the special-expression early return from blinzeln().

    The current live subject delegates frame playback and end-state opacity to
    blinzelAbspielen(); keeping this rewrite scoped to the scheduler makes the
    builder resilient to that split call graph while remaining fail-closed.
    """
    start, end, fn = extract_function(
        text, "function blinzeln(zeitplanNeu = true){", "blinzeln"
    )

    guard = re.search(r"if\s*\(\s*_sonderLaeuft\s*\)\s*\{", fn)
    if not guard:
        raise RuntimeError("_sonderLaeuft blink guard not found inside blinzeln")
    guard_brace = fn.find("{", guard.start())
    _, guard_end = find_braced_region(fn, guard_brace)
    removed = fn[guard.start() : guard_end]
    if "return" not in removed or "blinzelWeiterPlanen" not in removed:
        raise RuntimeError(f"unexpected special-expression guard: {removed!r}")
    fn = fn[: guard.start()] + fn[guard_end:]

    rewritten = text[:start] + fn + text[end:]
    return rewritten, {
        "removed_guard_sha256": sha256_bytes(removed.encode("utf-8")),
        "removed_guard_bytes": len(removed.encode("utf-8")),
        "blink_scheduler_rewritten": True,
    }


def rewrite_blink_player(text: str) -> tuple[str, dict[str, object]]:
    """Keep the canonical open-eye plate visible after frame playback ends."""
    start, end, fn = extract_function(
        text,
        "function blinzelAbspielen(schritte, idx, zeitplanNeu){",
        "blinzelAbspielen",
    )
    old_end = '$("augen-blink").style.opacity = "0";'
    if fn.count(old_end) != 1:
        raise RuntimeError(
            "blink end opacity: expected one occurrence inside "
            f"blinzelAbspielen, got {fn.count(old_end)}"
        )
    replacement = (
        '$("augen-blink").src = BLINK_BILDER[0];\n'
        '    $("augen-blink").style.opacity = "1";'
    )
    fn = fn.replace(old_end, replacement, 1)
    rewritten = text[:start] + fn + text[end:]
    return rewritten, {
        "blink_player_end_rewritten": True,
        "blink_player_open_plate_restored": True,
    }


def build(source: Path, visual_root: Path, out: Path) -> dict[str, object]:
    raw = source.read_bytes()
    source_sha = sha256_bytes(raw)
    if source_sha != EXPECTED_HTML_SHA256:
        raise RuntimeError(
            f"source mismatch: {source_sha} != {EXPECTED_HTML_SHA256}"
        )

    relief2_open = visual_root / "augen_blink_relief2" / "blink_000.png"
    if sha256_file(relief2_open) != EXPECTED_OPEN_RELIEF2_SHA256:
        raise RuntimeError("relief2 open-eye asset does not match measured candidate")
    relief2_frames = sorted((visual_root / "augen_blink_relief2").glob("blink_*.png"))
    if len(relief2_frames) != 12:
        raise RuntimeError(f"expected 12 relief2 blink frames, got {len(relief2_frames)}")

    text = raw.decode("utf-8")
    changes: dict[str, object] = {}

    # Preserve the canonical route. buehne_daemon.py resolves /augen_blink/*
    # through BLINK_DIR, which is currently _vielleicht_ai(...)->relief2.
    # Rewriting the URL to /augen_blink_relief2 would create/bypass authority.
    blink_img = '<img id="augen-blink" src="/augen_blink/blink_000.png" alt="">'
    blink_array = '`/augen_blink/blink_${String(i).padStart(3,"0")}.png`'
    require_one(text, blink_img, "canonical blink img route")
    require_one(text, blink_array, "canonical BLINK_BILDER route")
    changes["blink_route_preserved"] = True

    text, changes["blink_css_open"] = rewrite_css_rule(
        text,
        "#augen-blink",
        lambda rule: re.sub(
            r"opacity\s*:\s*0(?=\s*[;}])", "opacity:1", rule, count=1
        ),
        "blink CSS open state",
    )
    text, changes["glow_above_eye"] = rewrite_css_rule(
        text,
        "#pupillen-glow",
        lambda rule: re.sub(
            r"z-index\s*:\s*4(?=\s*[;}])", "z-index:5", rule, count=1
        ),
        "glow z order",
    )

    text, blink_meta = rewrite_blink_function(text)
    changes.update(blink_meta)
    text, player_meta = rewrite_blink_player(text)
    changes.update(player_meta)

    text, changes["glow_coupling"] = replace_one(
        text,
        '$("pupillen-glow").style.opacity = _sonderLaeuft ? "0" : String(ziel.opazitaet);',
        '$("pupillen-glow").style.opacity = blinzelPhase ? "0" : String(ziel.opazitaet);',
        "gaze glow coupling",
    )

    text = text.replace(
        "</head>",
        '<meta name="go-eye-shadow" content="v5-split-blink-player">\n</head>',
        1,
    )

    invariants = {
        "old_special_glow_coupling_absent": (
            '_sonderLaeuft ? "0" : String(ziel.opazitaet)' not in text
        ),
        "special_blink_guard_absent": not bool(
            re.search(
                r"function blinzeln\(zeitplanNeu = true\)\{.*?if\s*\(\s*_sonderLaeuft\s*\)",
                text,
                re.S,
            )
        ),
        "canonical_blink_img_route_present": blink_img in text,
        "canonical_blink_array_route_present": blink_array in text,
        "explicit_relief2_url_absent": "/augen_blink_relief2/" not in text,
        "blink_css_open": bool(
            re.search(r"#augen-blink\{[^}]*opacity\s*:\s*1", text, re.S)
        ),
        "blink_player_restores_open_plate": (
            '$("augen-blink").src = BLINK_BILDER[0];' in text
            and '$("augen-blink").style.opacity = "1";' in text
        ),
        "glow_z_five": bool(
            re.search(r"#pupillen-glow\{[^}]*z-index\s*:\s*5", text, re.S)
        ),
    }
    if not all(invariants.values()):
        raise RuntimeError(f"candidate invariant failure: {invariants}")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(text, encoding="utf-8")
    manifest: dict[str, object] = {
        "schema": "GO_AVATAR_EYE_SEMANTIC_SHADOW/v3",
        "source_sha256": source_sha,
        "candidate_sha256": sha256_file(out),
        "relief2_open_sha256": sha256_file(relief2_open),
        "relief2_frame_count": len(relief2_frames),
        "serving_authority": {
            "public_route": "/augen_blink/",
            "productive_backing_dir": "augen_blink_relief2",
            "route_rewrite": False,
        },
        "changes": changes,
        "invariants": invariants,
        "live_mutation": False,
    }
    return manifest


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--visual-root", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    manifest = build(
        args.source.resolve(), args.visual_root.resolve(), args.out.resolve()
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
