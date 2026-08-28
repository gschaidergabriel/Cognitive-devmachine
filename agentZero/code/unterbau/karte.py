#!/usr/bin/env python3
"""karte.py -- ClayVerse kartiert sich selbst und beide Wirtsrechner.

Ein Schnappschuss, den niemand mit dem vorigen vergleicht, ist eine Datei,
kein Wissen. Deshalb baut dieses Werkzeug beides: die Aufnahme UND den Diff.

    karte.py aufnehmen [wirt]   Schnappschuss je erreichbarem Wirt
    karte.py vergleich [wirt]   neuester vs. voriger Schnappschuss -- nur das Delta
    karte.py stand              wann zuletzt kartiert, wie viele Schnappschuesse

Die Wirtsliste kommt aus wirte.json (selbst ermittelt, siehe wirte.py) --
nie fest eingetragen. Ein nicht erreichbarer Wirt wird als Schnappschuss mit
fehler-Feld festgehalten, nicht stillschweigend ausgelassen (Regel 5).
Fehlt ein Werkzeug auf einem Wirt, steht das als Text im Feld -- eine leere
Liste waere eine Erfindung, keine Messung.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

TABELLE = Path("/var/lib/clay/wirte.json")
KARTE = Path("/var/lib/clay/karte")
STROM = Path("/var/lib/clay/ereignisse.jsonl")
HIER = os.uname().nodename  # lokaler Wirt -- keine SSH-Schleife auf sich selbst
FEHLT = "__FEHLT__"


def _wirte() -> dict:
    if not TABELLE.exists():
        return {}
    d = json.loads(TABELLE.read_text(encoding="utf-8"))
    return dict(d.get("wirte", {}))


def _lauf(befehl: list[str], zeit: int = 20) -> tuple[int, str]:
    try:
        p = subprocess.run(befehl, capture_output=True, text=True, timeout=zeit)
        return p.returncode, (p.stdout + p.stderr)
    except subprocess.TimeoutExpired:
        return 124, "Zeitueberschreitung"
    except Exception as e:
        return 1, str(e)


def _sh(wirt: str, eintrag: dict | None, befehl: str, zeit: int = 20) -> tuple[int, str]:
    """Lokal, wenn wirt == HIER -- sonst per SSH mit dem selbst ermittelten
    Konto aus wirte.json. Kein Konto geraten."""
    if wirt == HIER:
        return _lauf(["bash", "-c", befehl], zeit)
    if not eintrag or not eintrag.get("konto"):
        return 1, "kein Konto ermittelt (wirte.json)"
    ziel = f"{eintrag['konto']}@{eintrag['ip']}"
    return _lauf(["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", ziel, befehl], zeit)


def _ereignis(**felder) -> None:
    STROM.parent.mkdir(parents=True, exist_ok=True)
    with STROM.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z"), **felder},
                            ensure_ascii=False) + "\n")


# -- Aufnahme --------------------------------------------------------------

def _erfassen(wirt: str, eintrag: dict | None) -> dict:
    schnappschuss = {"wirt": wirt, "zeit": time.strftime("%Y-%m-%dT%H:%M:%S%z")}

    rc, aus = _sh(wirt, eintrag, "hostname", 10)
    if rc != 0:
        schnappschuss["erreichbar"] = False
        schnappschuss["fehler"] = aus.strip()[:300] or "nicht erreichbar"
        return schnappschuss
    schnappschuss["erreichbar"] = True

    # Hardware
    _, cpu_modell = _sh(wirt, eintrag, "awk -F: '/model name/{print $2; exit}' /proc/cpuinfo")
    _, cpu_kerne = _sh(wirt, eintrag, "nproc")
    _, ram = _sh(wirt, eintrag, "awk '/MemTotal/{print $2}' /proc/meminfo")
    _, gpu = _sh(wirt, eintrag,
                 f"command -v lspci >/dev/null && lspci | grep -i vga || echo {FEHLT}")
    schnappschuss["hardware"] = {
        "cpu_modell": cpu_modell.strip() or None,
        "cpu_kerne": cpu_kerne.strip() or None,
        "ram_kb": ram.strip() or None,
        "gpu": ("lspci nicht vorhanden" if FEHLT in gpu
                else [z.strip() for z in gpu.splitlines() if z.strip()]),
    }

    # Platten
    _, disks = _sh(wirt, eintrag, f"command -v lsblk >/dev/null && lsblk -J || echo {FEHLT}", 15)
    if FEHLT in disks:
        schnappschuss["disks"] = "lsblk nicht vorhanden"
    else:
        try:
            schnappschuss["disks"] = json.loads(disks).get("blockdevices", [])
        except Exception:
            schnappschuss["disks"] = f"lsblk-Ausgabe nicht lesbar: {disks.strip()[:200]}"

    # USB
    _, usb = _sh(wirt, eintrag, f"command -v lsusb >/dev/null && lsusb || echo {FEHLT}", 10)
    schnappschuss["usb"] = ("lsusb nicht vorhanden" if FEHLT in usb
                             else [z.strip() for z in usb.splitlines() if z.strip()])

    # Netz
    _, adr = _sh(wirt, eintrag, f"command -v ip >/dev/null && ip -j addr || echo {FEHLT}", 10)
    if FEHLT in adr:
        schnappschuss["netz_adressen"] = "ip nicht vorhanden"
    else:
        try:
            schnappschuss["netz_adressen"] = json.loads(adr)
        except Exception:
            schnappschuss["netz_adressen"] = f"ip-Ausgabe nicht lesbar: {adr.strip()[:200]}"

    _, horcht = _sh(wirt, eintrag, f"command -v ss >/dev/null && ss -tlnp 2>&1 || echo {FEHLT}", 10)
    schnappschuss["horchend"] = ("ss nicht vorhanden" if FEHLT in horcht
                                  else [z.strip() for z in horcht.splitlines()[1:] if z.strip()])

    # Dienste
    _, dienste = _sh(wirt, eintrag,
                      "systemctl list-units --type=service --state=running --no-legend", 15)
    schnappschuss["dienste"] = [z.strip() for z in dienste.splitlines() if z.strip()]

    # Benutzer (uid >= 1000, < 65000 -- keine Systemkonten)
    _, passwd = _sh(wirt, eintrag, "getent passwd", 10)
    benutzer = []
    for z in passwd.splitlines():
        f = z.split(":")
        if len(f) >= 3 and f[2].isdigit() and 1000 <= int(f[2]) < 65000:
            benutzer.append({"name": f[0], "uid": int(f[2]), "home": f[5] if len(f) > 5 else None})
    schnappschuss["benutzer"] = benutzer

    return schnappschuss


def aufnehmen(argv: list[str]) -> int:
    wirte = _wirte()
    nur = argv[0] if argv else None
    ziel_namen = [nur] if nur else sorted(set(list(wirte) + [HIER]))
    KARTE.mkdir(parents=True, exist_ok=True)
    ok = fehl = 0
    for name in ziel_namen:
        eintrag = wirte.get(name)
        schnappschuss = _erfassen(name, eintrag)
        # eigenes Unterverzeichnis je Wirt -- ein Praefix-Glob ("clayverse-*")
        # traf sonst auch "clayverse-alt" und mischte die Wirte im Vergleich.
        ordner = KARTE / name
        ordner.mkdir(parents=True, exist_ok=True)
        pfad = ordner / f"{time.strftime('%Y%m%dT%H%M%S')}.json"
        pfad.write_text(json.dumps(schnappschuss, ensure_ascii=False, indent=2), encoding="utf-8")
        if schnappschuss.get("erreichbar"):
            ok += 1
            print(f"  OK   {name:<34} -> {name}/{pfad.name}")
        else:
            fehl += 1
            print(f"  FEHL {name:<34} {schnappschuss.get('fehler', '')}")
        _ereignis(wirt=HIER, instanz=name, organ="karte", art="aufgenommen",
                  erreichbar=schnappschuss.get("erreichbar", False))
    print(f"\n  {ok} von {ok + fehl} erreichbar aufgenommen -> {KARTE}")
    return 0 if fehl == 0 else 1


# -- Vergleich ---------------------------------------------------------------

def _schnappschuesse(wirt: str) -> list[Path]:
    """NUR aus dem eigenen Unterverzeichnis -- kein Praefix-Glob, sonst
    zieht 'clayverse' auch 'clayverse-alt' mit (die Falle, die es hier gab)."""
    return sorted((KARTE / wirt).glob("*.json"))


def _mengen(sch: dict) -> dict[str, set[str]]:
    """Vergleichbare Mengen aus einem Schnappschuss: USB, Platten, Ports,
    Dienste, Benutzer -- genau die fuenf Kategorien aus der Aufgabe."""
    usb = sch.get("usb")
    usb_set = set(usb) if isinstance(usb, list) else set()

    disk_set: set[str] = set()
    disks = sch.get("disks")
    if isinstance(disks, list):
        def _namen(dl):
            for d in dl:
                if isinstance(d, dict):
                    disk_set.add(str(d.get("name")))
                    if d.get("children"):
                        _namen(d["children"])
        _namen(disks)

    port_set: set[str] = set()
    horchend = sch.get("horchend")
    if isinstance(horchend, list):
        for z in horchend:
            teile = z.split()
            if len(teile) >= 4:
                port_set.add(teile[3])  # lokale Adresse:Port aus ss -tlnp

    dienst_set: set[str] = set()
    dienste = sch.get("dienste")
    if isinstance(dienste, list):
        for z in dienste:
            t = z.split()
            if t:
                dienst_set.add(t[0])

    user_set: set[str] = set()
    benutzer = sch.get("benutzer")
    if isinstance(benutzer, list):
        for b in benutzer:
            user_set.add(b.get("name") if isinstance(b, dict) else str(b))

    return {"usb": usb_set, "disks": disk_set, "ports": port_set,
            "dienste": dienst_set, "benutzer": user_set}


def _vergleich_eins(wirt: str) -> int:
    dateien = _schnappschuesse(wirt)
    if len(dateien) < 2:
        print(f"  {wirt}: {len(dateien)} Schnappschuss(e) -- kein Vorgaenger zum Vergleich")
        return 0
    alt = json.loads(dateien[-2].read_text(encoding="utf-8"))
    neu = json.loads(dateien[-1].read_text(encoding="utf-8"))

    if not alt.get("erreichbar") or not neu.get("erreichbar"):
        if bool(alt.get("erreichbar")) != bool(neu.get("erreichbar")):
            zustand = "erreichbar geworden" if neu.get("erreichbar") else "nicht mehr erreichbar"
            print(f"  {wirt}: {zustand}")
            _ereignis(wirt=HIER, instanz=wirt, organ="karte", art="veraendert",
                      kategorie="erreichbarkeit", was=zustand)
            return 1
        print(f"  {wirt}: weiterhin nicht erreichbar, kein Vergleich moeglich")
        return 0

    m_alt, m_neu = _mengen(alt), _mengen(neu)
    beschriftung = {"usb": "USB-Geraet", "disks": "Platte", "ports": "Port",
                     "dienste": "Dienst", "benutzer": "Benutzer"}
    aenderungen = 0
    for kat, label in beschriftung.items():
        for x in sorted(m_neu[kat] - m_alt[kat]):
            print(f"  {wirt}: {label} NEU          {x}")
            _ereignis(wirt=HIER, instanz=wirt, organ="karte", art="veraendert",
                      kategorie=kat, richtung="erschienen", was=x)
            aenderungen += 1
        for x in sorted(m_alt[kat] - m_neu[kat]):
            print(f"  {wirt}: {label} VERSCHWUNDEN {x}")
            _ereignis(wirt=HIER, instanz=wirt, organ="karte", art="veraendert",
                      kategorie=kat, richtung="verschwunden", was=x)
            aenderungen += 1
    if not aenderungen:
        print(f"  {wirt}: keine Veraenderung seit {dateien[-2].name}")
    return aenderungen


def _bekannte_wirte() -> list[str]:
    if not KARTE.exists():
        return []
    return sorted(p.name for p in KARTE.iterdir() if p.is_dir())


def vergleich(argv: list[str]) -> int:
    nur = argv[0] if argv else None
    namen = [nur] if nur else _bekannte_wirte()
    if not namen:
        print("  Noch keine Aufnahme -- `karte.py aufnehmen`")
        return 0
    gesamt = 0
    for w in namen:
        gesamt += _vergleich_eins(w)
    print(f"\n  {gesamt} Aenderung(en) insgesamt")
    return 0


# -- Stand --------------------------------------------------------------

def stand(_argv: list[str]) -> int:
    namen = _bekannte_wirte()
    if not namen:
        print("  Noch keine Aufnahme -- `karte.py aufnehmen`")
        return 0
    jetzt = time.time()
    print()
    for w in namen:
        dateien = _schnappschuesse(w)
        letzte = dateien[-1]
        try:
            letzte_zeit = json.loads(letzte.read_text(encoding="utf-8")).get("zeit", "")
            t = time.mktime(time.strptime(letzte_zeit[:19], "%Y-%m-%dT%H:%M:%S"))
            alter_txt = f"{(jetzt - t) / 3600:.1f} h"
        except Exception:
            letzte_zeit, alter_txt = "?", "unbekannt"
        print(f"  {w:<34} {len(dateien):>3} Schnappschuss(e)  zuletzt {letzte_zeit[:16]}  vor {alter_txt}")
    print()
    return 0


BEFEHLE = {"aufnehmen": aufnehmen, "vergleich": vergleich, "stand": stand}

if __name__ == "__main__":
    b = sys.argv[1] if len(sys.argv) > 1 else "stand"
    if b not in BEFEHLE:
        print(__doc__)
        sys.exit(2)
    sys.exit(BEFEHLE[b](sys.argv[2:]) or 0)
