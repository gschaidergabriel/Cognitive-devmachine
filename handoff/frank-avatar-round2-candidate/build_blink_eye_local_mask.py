#!/usr/bin/env python3
"""Build a deterministic eye-local blink asset set.

Default is non-destructive: reads <visual_root>/augen_blink and writes a separate
output directory. It never edits buehne.html or filmlook.js.
"""
from __future__ import annotations

import argparse
import binascii
import hashlib
import json
import math
import shutil
import struct
import zlib
from pathlib import Path

EXPECTED = {
    "blink_000.png": "f7c0abd552a91e117f90880bc67c29f22311f1ed5b90a043b169e93495fff44f",
    "blink_001.png": "6bf13c8bbc7dc8934d25910cca4a3938a132a9643481f24f86e6741e57df3384",
    "blink_002.png": "e7dce5c8859f97e53bb29edaaa0093aac0887ed134b15c32283e7e4337452019",
    "blink_003.png": "5c3a76bda483b6bd2ed6a488b8cd2584a857f3aa72da15acbbcd7cbd8c9d0c7f",
    "blink_004.png": "58eabd5484fc8b9ab28063ebc5e10be0fb4b56d977a5c9ca3c8c959cd03b2fb8",
    "blink_005.png": "a426ae34297e4624c4a6cf974006d39dd89fba1a8eb293177f949fd60bcfe316",
    "blink_006.png": "f7cc3fc538478c9a0f5748f2139a8bba7234f74aa59b634dc3f266caa237d0fa",
    "blink_007.png": "ce9599334eec60b7b848b752a3262ec10f992c9550bb5f1edf9256b1bf5bbebf",
    "blink_008.png": "8eb96677ea4d24548e201e779a56ae1417b5c5650f88c75e063c445c8963ed1c",
    "blink_009.png": "58eabd5484fc8b9ab28063ebc5e10be0fb4b56d977a5c9ca3c8c959cd03b2fb8",
    "blink_010.png": "e7dce5c8859f97e53bb29edaaa0093aac0887ed134b15c32283e7e4337452019",
    "blink_011.png": "f7c0abd552a91e117f90880bc67c29f22311f1ed5b90a043b169e93495fff44f",
}
EXPECTED_OUTPUT = {
    "blink_000.png": "c9304ad603ba97ce20c69c8c0640ec389f181e082c06b2f5a5b25bf5fcaf7128",
    "blink_001.png": "5d4c90e3ac8e24b4200707effb2012b5fca96056729221d956caf296ac913037",
    "blink_002.png": "84a351f07501f6fc720fe1d59d90f556e31a883ed1364b36aaeafe58a68dfc41",
    "blink_003.png": "a618be54bbe10e5cebb9fd9558dbc0399bc0df4f46f8689cce3a7730ff3981a5",
    "blink_004.png": "2bd30253393c78e2af2efc1703c84d0d13122f91b466781b41346fd39123c002",
    "blink_005.png": "6c593d09afbf3775f84eecfc98d8a3430b4097f88831381f7bcd7664dad49be7",
    "blink_006.png": "06f160a42e396f7c80a633c8954458f09e64f904c7345b5722d9639f030e0c46",
    "blink_007.png": "837dac5229487c0b1d6fbe4b803ebb6736c24821befea5f15cb0f07a3b4c2718",
    "blink_008.png": "4a031574f88c421a2b7a6a393905d34b60c25e941e9e7f4811a543e759aeb6ac",
    "blink_009.png": "2bd30253393c78e2af2efc1703c84d0d13122f91b466781b41346fd39123c002",
    "blink_010.png": "84a351f07501f6fc720fe1d59d90f556e31a883ed1364b36aaeafe58a68dfc41",
    "blink_011.png": "c9304ad603ba97ce20c69c8c0640ec389f181e082c06b2f5a5b25bf5fcaf7128",
}


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    ds = (abs(p - a), abs(p - b), abs(p - c))
    return (a, b, c)[ds.index(min(ds))]


def decode_png(data: bytes) -> tuple[int, int, bytes]:
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not PNG")
    pos, ids, meta = 8, [], None
    while pos < len(data):
        size = struct.unpack(">I", data[pos:pos + 4])[0]
        typ = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + size]
        pos += 12 + size
        if typ == b"IHDR":
            meta = struct.unpack(">IIBBBBB", chunk)
        elif typ == b"IDAT":
            ids.append(chunk)
        elif typ == b"IEND":
            break
    if meta is None:
        raise ValueError("missing IHDR")
    w, h, bd, ct, _comp, _flt, interlace = meta
    if (bd, ct, interlace) != (8, 6, 0):
        raise ValueError(f"expected non-interlaced RGBA8, got {meta}")
    raw = zlib.decompress(b"".join(ids))
    stride = w * 4
    prev = bytearray(stride)
    out = bytearray()
    off = 0
    for _y in range(h):
        f = raw[off]
        off += 1
        cur = bytearray(raw[off:off + stride])
        off += stride
        for x in range(stride):
            a = cur[x - 4] if x >= 4 else 0
            b = prev[x]
            c = prev[x - 4] if x >= 4 else 0
            if f == 1:
                cur[x] = (cur[x] + a) & 255
            elif f == 2:
                cur[x] = (cur[x] + b) & 255
            elif f == 3:
                cur[x] = (cur[x] + ((a + b) // 2)) & 255
            elif f == 4:
                cur[x] = (cur[x] + paeth(a, b, c)) & 255
            elif f != 0:
                raise ValueError(f"unsupported PNG filter {f}")
        out += cur
        prev = cur
    return w, h, bytes(out)


def png_chunk(typ: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + typ + data + struct.pack(">I", binascii.crc32(typ + data) & 0xFFFFFFFF)


def encode_png(w: int, h: int, pixels: bytes) -> bytes:
    raw = b"".join(b"\x00" + pixels[y * w * 4:(y + 1) * w * 4] for y in range(h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0)
    return b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr) + png_chunk(b"IDAT", zlib.compress(raw, 9)) + png_chunk(b"IEND", b"")


def connected_components(w: int, h: int, pixels: bytes) -> list[list[int]]:
    active = {i for i in range(w * h) if pixels[i * 4 + 3] > 0}
    out = []
    while active:
        seed = active.pop()
        queue = [seed]
        comp = [seed]
        while queue:
            i = queue.pop()
            x, y = i % w, i // w
            for nx, ny in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                if 0 <= nx < w and 0 <= ny < h:
                    j = ny * w + nx
                    if j in active:
                        active.remove(j)
                        queue.append(j)
                        comp.append(j)
        out.append(comp)
    return sorted(out, key=len, reverse=True)


def bbox(comp: list[int], w: int) -> tuple[int, int, int, int]:
    xs = [i % w for i in comp]
    ys = [i // w for i in comp]
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("visual_root", type=Path)
    ap.add_argument("output_dir", type=Path)
    args = ap.parse_args()

    source_dir = args.visual_root / "augen_blink"
    gaze = args.visual_root / "augen_gaze" / "rotglow_tracking_master.png"
    args.output_dir.mkdir(parents=True, exist_ok=False)

    for name, expected in EXPECTED.items():
        got = sha(source_dir / name)
        if got != expected:
            raise SystemExit(f"stale source {name}: {got} != {expected}")

    w, h, gaze_pixels = decode_png(gaze.read_bytes())
    comps = [c for c in connected_components(w, h, gaze_pixels) if len(c) >= 20][:2]
    if len(comps) != 2:
        raise SystemExit(f"expected exactly two gaze components, got {len(comps)}")

    eyes = []
    for comp in sorted(comps, key=lambda c: bbox(c, w)[0]):
        x0, y0, x1, y1 = bbox(comp, w)
        cx = (x0 + x1 - 1) / 2
        cy = (y0 + y1 - 1) / 2
        rx = max(46, (x1 - x0) / 2 + 30)
        ry = max(34, (y1 - y0) / 2 + 24)
        eyes.append((cx, cy, rx, ry))

    report = {"gaze_components": [bbox(c, w) for c in comps], "eyes": eyes, "frames": []}
    for name in sorted(EXPECTED):
        sw, sh, pixels = decode_png((source_dir / name).read_bytes())
        if (sw, sh) != (w, h):
            raise SystemExit(f"dimension mismatch {name}")
        out = bytearray(pixels)
        nonzero = opaque = 0
        for y in range(h):
            for x in range(w):
                weight = 0.0
                for cx, cy, rx, ry in eyes:
                    r = math.sqrt(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2)
                    v = 1.0 if r <= 0.72 else (0.0 if r >= 1.0 else (1.0 - r) / 0.28)
                    weight = max(weight, v)
                idx = (y * w + x) * 4 + 3
                out[idx] = round(out[idx] * weight)
                nonzero += out[idx] > 0
                opaque += out[idx] >= 250
        data = encode_png(w, h, bytes(out))
        got = hashlib.sha256(data).hexdigest()
        if got != EXPECTED_OUTPUT[name]:
            raise SystemExit(f"nondeterministic output {name}: {got} != {EXPECTED_OUTPUT[name]}")
        (args.output_dir / name).write_bytes(data)
        report["frames"].append({
            "frame": name,
            "sha256": got,
            "alpha_nonzero_frac": round(nonzero / (w * h), 6),
            "alpha_opaque_frac": round(opaque / (w * h), 6),
        })

    (args.output_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
