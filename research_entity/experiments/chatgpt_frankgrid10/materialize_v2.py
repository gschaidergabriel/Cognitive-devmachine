#!/usr/bin/env python3
from pathlib import Path
import base64, hashlib, zlib

HERE = Path(__file__).resolve().parent
SRC = HERE / "frankgrid10_v2.py.zlib.b64"
OUT = HERE / "frankgrid10_v2.py"
EXPECTED = "60ec27675b2900e9f71f3c22f50cb3ca28231272d4f3bb7ec016b3127608a03e"

raw = zlib.decompress(base64.b64decode(SRC.read_text(encoding="ascii").strip()))
got = hashlib.sha256(raw).hexdigest()
if got != EXPECTED:
    raise SystemExit(f"hash mismatch: {got} != {EXPECTED}")
OUT.write_bytes(raw)
OUT.chmod(0o755)
print(f"materialized {OUT.name} sha256={got} bytes={len(raw)}")
