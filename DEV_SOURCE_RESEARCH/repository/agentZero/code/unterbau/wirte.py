#!/usr/bin/env python3
"""wirte.py — die Wirtstabelle stellt sich selbst in Frage.

Der Grund, warum es diese Datei gibt: eine fest eingetragene Wirtstabelle ist
selbst eine Annahme. Sie enthielt `gabriel@100.70.87.28` — auf dem Rechner
heißt das Konto aber `ai-core-node`. **Jede Messung durch dieses Werkzeug wäre
auf dieselbe Weise falsch gewesen**, und zwar unbemerkt, weil das Werkzeug ja
„geprüft" hätte.

Deshalb: Die Tabelle wird nicht gepflegt, sondern **ermittelt**. Und sie wird
zyklisch nachgeprüft, weil sich Adressen, Konten und Namen ändern.

    wirte.py ermitteln    Tabelle aus dem Tailnet neu bestimmen
    wirte.py zeigen       aktuelle Tabelle
    wirte.py pruefen      jeden Eintrag anfassen — stimmt er noch?
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

TABELLE = Path("/var/lib/clay/wirte.json")
KONTEN = ("root", "ai-core-node", "gabriel", "andreas", "ubuntu")


def _lauf(b: list[str], t: int = 20) -> tuple[int, str]:
    try:
        p = subprocess.run(b, capture_output=True, text=True, timeout=t)
        return p.returncode, (p.stdout + p.stderr).strip()
    except Exception as e:
        return 1, str(e)


def _tailnet() -> list[tuple[str, str]]:
    rc, aus = _lauf(["tailscale", "status", "--json"], 25)
    if rc != 0:
        return []
    d = json.loads(aus)
    knoten = []
    for p in list(d.get("Peer", {}).values()) + [d.get("Self", {})]:
        if not p:
            continue
        ips = p.get("TailscaleIPs") or []
        v4 = next((i for i in ips if ":" not in i), None)
        name = (p.get("HostName") or "").strip()
        if v4 and name and p.get("Online"):
            knoten.append((name, v4))
    return sorted(set(knoten))


def ermitteln() -> int:
    """Findet je Wirt heraus, mit WELCHEM Konto man hinkommt — durch Probieren,
    nicht durch Annehmen."""
    gefunden = {}
    for name, ip in _tailnet():
        eintrag = {"ip": ip, "konto": None, "hostname": None,
                   "geprueft": time.strftime("%Y-%m-%dT%H:%M:%S%z")}
        for k in KONTEN:
            rc, aus = _lauf(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6",
                             "-o", "StrictHostKeyChecking=accept-new",
                             f"{k}@{ip}", "hostname; id -un"], 15)
            if rc == 0 and aus:
                z = aus.splitlines()
                eintrag["konto"] = k
                eintrag["hostname"] = z[0].strip()
                eintrag["ist_konto"] = z[-1].strip() if len(z) > 1 else k
                break
        gefunden[name] = eintrag
        z = eintrag
        marke = "✓" if z["konto"] else "—"
        print(f"  {marke} {name:<24} {ip:<16} "
              f"{(z['konto'] + '@') if z['konto'] else 'kein Zugang'}"
              f"{('  → ' + z['hostname']) if z['hostname'] else ''}")

    TABELLE.parent.mkdir(parents=True, exist_ok=True)
    TABELLE.write_text(json.dumps(
        {"erzeugt": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "wirte": gefunden},
        ensure_ascii=False, indent=2), encoding="utf-8")
    erreichbar = sum(1 for v in gefunden.values() if v["konto"])
    print(f"\n  {erreichbar} von {len(gefunden)} erreichbar · {TABELLE}")
    return 0


def zeigen() -> int:
    if not TABELLE.exists():
        print("  Noch nicht ermittelt — `wirte.py ermitteln`"); return 1
    d = json.loads(TABELLE.read_text(encoding="utf-8"))
    print(f"\n  ermittelt {d['erzeugt'][:16]}\n")
    for n, v in d["wirte"].items():
        alter = ""
        print(f"  {n:<24} {v['ip']:<16} "
              f"{(v['konto'] or '—'):<14} {v.get('hostname') or ''}{alter}")
    print()
    return 0


def pruefen() -> int:
    """Zyklische Selbstprüfung: stimmt jeder Eintrag noch? Ein Messwerkzeug,
    das nie hinterfragt wird, misst irgendwann verlässlich das Falsche."""
    if not TABELLE.exists():
        return ermitteln()
    d = json.loads(TABELLE.read_text(encoding="utf-8"))
    abweichung = 0
    for n, v in d["wirte"].items():
        if not v.get("konto"):
            continue
        rc, aus = _lauf(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=6",
                         f"{v['konto']}@{v['ip']}", "hostname"], 15)
        ist = aus.strip().splitlines()[0] if rc == 0 and aus else None
        if ist == v.get("hostname"):
            print(f"  ✓ {n:<24} unverändert")
        else:
            abweichung += 1
            print(f"  ⚠ {n:<24} war '{v.get('hostname')}', ist '{ist or 'nicht erreichbar'}'")
    if abweichung:
        print(f"\n  {abweichung} Abweichung(en) — Tabelle wird neu ermittelt.\n")
        return ermitteln()
    print("\n  Tabelle stimmt.\n")
    return 0


if __name__ == "__main__":
    b = sys.argv[1] if len(sys.argv) > 1 else "zeigen"
    sys.exit({"ermitteln": ermitteln, "zeigen": zeigen, "pruefen": pruefen}
             .get(b, zeigen)())
