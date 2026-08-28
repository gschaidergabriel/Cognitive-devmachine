#!/usr/bin/env python3
"""zustand_mess.py — misst Tokengroesse und Latenz von udb.zustand().

Zeichen sind NICHT Token. In diesem Haus ist genau diese Verwechslung schon
schiefgegangen, deshalb wird hier mit einem echten Tokenizer gezaehlt und die
Zeichenzahl nur zum Vergleich mitgefuehrt.

Der Tokenizer liegt NICHT im Prod-Pfad: udb/abruf/zustand.py importiert nur
die Standardbibliothek. tiktoken wird ausschliesslich hier zum Messen
gebraucht. Aufruf:

    python3 -m venv /tmp/tokvenv && /tmp/tokvenv/bin/pip install tiktoken
    /tmp/tokvenv/bin/python zustand_mess.py [--laeufe 300]
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
import time

sys.path.insert(0, "/opt/unifieddb")
from udb.abruf.zustand import (          # noqa: E402
    _verbinden, zustand, zustand_json, zustand_text,
)


def tokens(text: str) -> "int | None":
    try:
        import tiktoken
    except ImportError:
        return None
    return len(tiktoken.get_encoding("cl100k_base").encode(text))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--laeufe", type=int, default=300)
    a = ap.parse_args()

    j = zustand_json()
    t = zustand_text()
    print("== GROESSE")
    for name, s in (("json", j), ("text", t)):
        tk = tokens(s)
        print("  %-5s zeichen=%5d  token=%s  zeichen/token=%s"
              % (name, len(s), tk if tk is not None else "KEIN TOKENIZER",
                 round(len(s) / tk, 2) if tk else "-"))

    # Kalt: eigene Verbindung je Lauf. Warm: eine Verbindung, wie ein
    # Dauerlaeufer sie haelt.
    t0 = time.perf_counter()
    zustand()
    print("\n== LATENZ")
    print("  kalt (mit Verbindungsaufbau): %.1f ms"
          % ((time.perf_counter() - t0) * 1000))

    c = _verbinden()
    for _ in range(5):
        zustand(c=c)                      # aufwaermen
    ms = []
    for _ in range(a.laeufe):
        t1 = time.perf_counter()
        zustand(c=c)
        ms.append((time.perf_counter() - t1) * 1000)
    ms.sort()
    p = lambda q: ms[min(len(ms) - 1, int(q * len(ms)))]   # noqa: E731
    print("  warm n=%d  p50=%.1f ms  p95=%.1f ms  p99=%.1f ms  max=%.1f ms"
          % (a.laeufe, statistics.median(ms), p(0.95), p(0.99), ms[-1]))
    c.close()

    print("\n== ZUSICHERUNG")
    z = zustand()
    print("  modellaufrufe im Ergebnis: %s" % z["modellaufrufe"])
    print("  Teilsysteme: %s" % ", ".join(k for k in z if k not in
                                          ("zeit", "modellaufrufe")))
    print("  lagen: %s" % json.dumps(
        {k: v.get("lage") for k, v in z.items()
         if isinstance(v, dict) and "lage" in v}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
