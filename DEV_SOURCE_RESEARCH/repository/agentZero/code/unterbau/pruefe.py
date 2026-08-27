#!/usr/bin/env python3
"""pruefe.py — die Werkzeuge gegen die Messfehler aus bau/MESSFEHLER.md.

Jedes Unterkommando entspricht einem Muster, das schon einmal schiefging.
Der Sinn: die Regel läuft als Code, nicht als Vorsatz.

    pruefe wirkung  ssh|firewall|dienst|http   Wirkung statt Konfiguration
    pruefe wer      <muster> [wirt]            über ALLE Benutzerkonten suchen
    pruefe gibtsdas <begriff>                  gibt es das schon?
    pruefe vonwo    <adresse>                  von mehreren Standorten messen
    pruefe erreichbar <wirt>                   Weg, Richtung, Tempo vor der Übertragung
    pruefe vollstaendig <soll-datei> <wurzel>  Soll gegen Ist
    pruefe behauptung "<satz>" -- <befehl>     Aussage nur mit Beleg

Rückgabe 0 = geprüft und wahr. Alles andere = nicht belegt.
"""
from __future__ import annotations

import json
import os
import shlex
import socket
import subprocess
import sys
import time
from pathlib import Path

def _wirte() -> dict:
    """Aus der selbst ermittelten Tabelle — nie fest eingetragen.

    Eine feste Wirtstabelle ist selbst eine Annahme: die erste enthielt
    `gabriel@` für einen Rechner, auf dem das Konto `root` heißt. Jede Messung
    durch sie wäre gleich falsch gewesen, und zwar unauffällig.
    """
    t = Path("/var/lib/clay/wirte.json")
    if not t.exists():
        return {}
    d = json.loads(t.read_text(encoding="utf-8"))
    return {n: f"{v['konto']}@{v['ip']}"
            for n, v in d["wirte"].items() if v.get("konto")}

STROM = Path("/var/lib/clay/ereignisse.jsonl")


def _lauf(befehl: list[str], zeit: int = 30) -> tuple[int, str]:
    try:
        p = subprocess.run(befehl, capture_output=True, text=True, timeout=zeit)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "Zeitüberschreitung"
    except Exception as e:
        return 1, str(e)


def _fern(wirt: str, befehl: str, zeit: int = 30) -> tuple[int, str]:
    ziel = _wirte().get(wirt, wirt)
    return _lauf(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
                  ziel, befehl], zeit)


def _ereignis(art: str, **rest) -> None:
    try:
        STROM.parent.mkdir(parents=True, exist_ok=True)
        with STROM.open("a", encoding="utf-8") as f:
            f.write(json.dumps({
                "zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "wirt": os.uname().nodename, "instanz": "pruefe",
                "organ": "messung", "art": art, **rest}, ensure_ascii=False) + "\n")
    except Exception:
        pass


# ── C · Wirkung statt Konfiguration ──────────────────────────────────────

def wirkung(argv: list[str]) -> int:
    """Fragt den DIENST, nicht die Datei. Eine geschriebene Konfiguration ist
    keine Wirkung — das war Fehler C1 (sshd) und C2 (nginx)."""
    was = argv[0] if argv else ""
    wirt = argv[1] if len(argv) > 1 else "clayverse"
    pruefungen = {
        "ssh": ("sshd -T | grep -E '^(passwordauthentication|permitrootlogin|kbdinteractiveauthentication)'",
                "Was sshd WIRKLICH tut — nicht was in der Datei steht"),
        "firewall": ("nft list chain inet filter input | grep -E 'policy|dport'",
                     "Geladener Regelsatz, nicht /etc/nftables.conf"),
        "dienst": ("systemctl list-units --state=running --no-legend --type=service | wc -l",
                   "Laufende Dienste"),
        "http": ("for h in seimensch.net leihmich.org herzrad.at frank.ink; do "
                 "printf '%-16s %s\\n' $h "
                 "$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 --resolve $h:443:127.0.0.1 https://$h/); done",
                 "Antwortcodes vom Wirt selbst"),
    }
    if was not in pruefungen:
        print(f"Bekannt: {' '.join(pruefungen)}"); return 2
    befehl, zweck = pruefungen[was]
    print(f"  {zweck}")
    rc, aus = _fern(wirt, befehl)
    for z in aus.splitlines():
        print(f"    {z}")
    _ereignis("wirkung", was=was, wirt=wirt, ok=(rc == 0))
    return rc


# ── B · über ALLE Benutzerkonten suchen ──────────────────────────────────

def wer(argv: list[str]) -> int:
    """Fehler B2: Ich suchte in /home/gabriel und meldete 'nicht installiert' —
    dabei lief es unter /home/andreas."""
    if not argv:
        print("pruefe wer <muster> [wirt]"); return 2
    muster, wirt = argv[0], (argv[1] if len(argv) > 1 else "andreas")
    befehl = (
        "for h in $(awk -F: '$3>=1000 && $3<65000 {print $6}' /etc/passwd) /opt /srv /usr/local; do "
        f"find $h -maxdepth 4 -iname '*{muster}*' 2>/dev/null | head -6; done; "
        "echo '--- laufende Prozesse:'; "
        f"ps -eo user,args --no-headers | grep -i '[{muster[0]}]{muster[1:]}' | head -5"
    )
    rc, aus = _fern(wirt, befehl, 45)
    if not aus.strip():
        print(f"  Nichts gefunden zu '{muster}' auf {wirt} — über ALLE Konten gesucht.")
    for z in aus.splitlines():
        print(f"  {z}")
    _ereignis("wer", muster=muster, wirt=wirt, treffer=len(aus.splitlines()))
    return 0


# ── D · gibt es das schon? ───────────────────────────────────────────────

def gibtsdas(argv: list[str]) -> int:
    """Fehler D1: Tresor gebaut, obwohl vault.py existierte."""
    if not argv:
        print("pruefe gibtsdas <begriff>"); return 2
    b = argv[0]
    print(f"  Suche nach '{b}' über alle Wirte — VOR dem Bauen.\n")
    treffer = 0
    for name in list(_wirte())[:4]:
        befehl = (
            "for w in /opt /srv /usr/local $(awk -F: '$3>=1000 && $3<65000 {print $6}' /etc/passwd); do "
            f"find $w -maxdepth 5 \\( -iname '*{b}*' \\) -not -path '*/.git/*' "
            "-not -path '*/node_modules/*' -not -path '*/venv/*' 2>/dev/null | head -8; done"
        )
        rc, aus = _fern(name, befehl, 60)
        zeilen = [z for z in aus.splitlines() if z.strip()]
        print(f"  ── {name}: {len(zeilen)} Treffer")
        for z in zeilen[:8]:
            print(f"       {z}")
        treffer += len(zeilen)
    print()
    if treffer:
        print(f"  ⚠ {treffer} Treffer. Erst ansehen, dann entscheiden ob neu gebaut wird.")
    else:
        print("  Nichts gefunden — Neubau ist begründet.")
    _ereignis("gibtsdas", begriff=b, treffer=treffer)
    return 0


# ── B · von mehreren Standorten messen ───────────────────────────────────

def vonwo(argv: list[str]) -> int:
    """Fehler B1: 000 gelesen als Serverausfall — es war die eigene
    /etc/hosts. Ein Netzbefund von einem Standort ist kein Befund."""
    if not argv:
        print("pruefe vonwo <adresse>"); return 2
    a = argv[0]
    print(f"  Namensauflösung hier:")
    rc, aus = _lauf(["getent", "hosts", a])
    print(f"    {aus or '(nichts)'}")
    rc, oeff = _lauf(["dig", "+short", "A", a, "@1.1.1.1"])
    print(f"    öffentlich (1.1.1.1): {oeff or '(nichts)'}")
    if aus and oeff and oeff.split()[0] not in aus:
        print(f"    ⚠ WEICHT AB — hier zeigt {a} woanders hin als im Netz.")
        print(f"      Ein Befund von diesem Rechner sagt nichts über den Dienst.")
    print(f"\n  Antwort von mehreren Standorten:")
    for name in list(_wirte())[:4]:
        rc, c = _fern(name, f"curl -s -o /dev/null -w '%{{http_code}}' --max-time 8 https://{a}/ 2>/dev/null")
        print(f"    {name:<14} {c or '—'}")
    _ereignis("vonwo", adresse=a)
    return 0


# ── B · erreichbar, bevor 59 GB anfangen ─────────────────────────────────

def erreichbar(argv: list[str]) -> int:
    """Fehler B3: rsync hing drei Minuten, weil der Weg gar nicht existierte."""
    if not argv:
        print("pruefe erreichbar <wirt>"); return 2
    w = argv[0]
    ziel = _wirte().get(w, w)
    print(f"  Ziel: {ziel}")
    rc, aus = _lauf(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
                     ziel, "hostname; df -h / | tail -1"], 25)
    if rc != 0:
        print(f"  ✗ NICHT erreichbar: {aus[:160]}")
        print("    Nicht anfangen. Erst den Weg herstellen.")
        _ereignis("erreichbar", wirt=w, ok=False)
        return 1
    for z in aus.splitlines():
        print(f"    {z}")
    # Tempo an einer kleinen Probe, bevor Großes läuft
    print("  Tempoprobe (20 MB):")
    _lauf(["dd", "if=/dev/urandom", "of=/tmp/.pruefe-probe", "bs=1M", "count=20"], 40)
    t0 = time.time()
    rc, _ = _lauf(["rsync", "-q", "/tmp/.pruefe-probe", f"{ziel}:/tmp/.pruefe-probe"], 180)
    dt = max(time.time() - t0, 0.1)
    if rc == 0:
        mbs = 20 / dt
        print(f"    {mbs:.1f} MB/s  →  1 GB dauert {1024/mbs/60:.0f} min, "
              f"60 GB dauern {60*1024/mbs/3600:.1f} h")
    else:
        print("    Übertragung fehlgeschlagen")
    _ereignis("erreichbar", wirt=w, ok=(rc == 0))
    return rc


# ── E · Soll gegen Ist ───────────────────────────────────────────────────

def vollstaendig(argv: list[str]) -> int:
    """Fehler E1: Sicherungsliste aus dem Kopf statt aus dem Bestand."""
    if len(argv) < 2:
        print("pruefe vollstaendig <soll-datei> <wurzel>"); return 2
    soll = [z.strip() for z in Path(argv[0]).read_text().splitlines() if z.strip()]
    wurzel = Path(argv[1])
    fehlt = [p for p in soll if not (wurzel / p.lstrip("/")).exists()]
    print(f"  Soll: {len(soll)}   vorhanden: {len(soll)-len(fehlt)}   FEHLT: {len(fehlt)}")
    for p in fehlt:
        print(f"    ✗ {p}")
    _ereignis("vollstaendig", soll=len(soll), fehlt=len(fehlt))
    return 1 if fehlt else 0


# ── A · Aussage nur mit Beleg ────────────────────────────────────────────

def behauptung(argv: list[str]) -> int:
    """Fehler A1/A2/A3: aus dem Gedächtnis behauptet. Hier geht eine Aussage
    nur mit dem Befehl durch, der sie belegt — und der Befehl läuft."""
    if "--" not in argv:
        print('pruefe behauptung "<satz>" -- <befehl>'); return 2
    i = argv.index("--")
    satz, befehl = " ".join(argv[:i]), argv[i+1:]
    if not satz.strip():
        print("Ohne Satz kein Beleg."); return 2
    print(f"  Behauptung: {satz}")
    print(f"  Beleg:      {' '.join(befehl)}")
    rc, aus = _lauf(befehl, 60)
    for z in aus.splitlines()[:20]:
        print(f"    {z}")
    print(f"  → {'BELEGT' if rc == 0 else 'NICHT BELEGT (Rückgabe ' + str(rc) + ')'}")
    _ereignis("behauptung", satz=satz[:200], belegt=(rc == 0))
    return rc


BEFEHLE = {"wirkung": wirkung, "wer": wer, "gibtsdas": gibtsdas,
           "vonwo": vonwo, "erreichbar": erreichbar,
           "vollstaendig": vollstaendig, "behauptung": behauptung}

if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] not in BEFEHLE:
        print(__doc__); sys.exit(2)
    sys.exit(BEFEHLE[sys.argv[1]](sys.argv[2:]) or 0)
