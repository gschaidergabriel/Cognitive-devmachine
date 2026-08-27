#!/usr/bin/env python3
"""weg.py -- die Wegtabelle stellt sich selbst in Frage (B6, zweite Haelfte).

wirte.py und karte.py beantworten WO ein Wirt steht und WAS dort laeuft.
Sie beantworten nicht, WIE man hinkommt. Das ist diese Datei.

Wie wirte.py: die Tabelle wird nicht gepflegt, sondern ERMITTELT. Ein
handgepflegter Wegeplan luegt still vor sich hin -- genau der Fehler, den
wirte.py bei sich selbst fand (gabriel@ statt root@). Deshalb geht `laufen`
jede Route tatsaechlich, mit einem harmlosen lesenden Befehl (hostname;
whoami; date -u), und schreibt genau das auf, was zurueckkam -- Erfolg UND
Fehlschlag gleichermassen. Ein toter Wirt (desktop-ufb20ka) ist ein Befund
mit Wert, keine Leerstelle.

AUCH GEMESSEN, NICHT ANGENOMMEN: welches Tor auf dem Weg gilt. Bei jedem
Lauf wird live geprueft, ob /etc/claude-code/managed-settings.json und
/var/lib/clay-tor auf dem ZIEL existieren (tor_hook.py-Infrastruktur) bzw.
ob ~/.schranke lokal existiert -- statt das aus einer alten Notiz zu
uebernehmen.

EINE ROUTE HAT EINEN URSPRUNG, NICHT NUR EIN ZIEL. clayverse-alt ist von
hier aus WHICHTIG ANDERS erreichbar als von clayverse aus (siehe Auftrag) --
deshalb ist (ursprung, ziel_wirt, transport) der Schluessel, nicht ziel_wirt
allein.

ALTERUNGSREGEL (B27): ein alter Eintrag ist brauchbar, solange sein Alter
genannt wird. `wie` liefert `zuletzt_bewiesen` und das Alter in Sekunden
IMMER mit -- nie eine stille Behauptung von Aktualitaet.

Mechanical only. No model calls, no network calls beyond the actual SSH
probes the job requires. Reads /var/lib/clay/wirte.json (read-only
reference, never duplicated/maintained here). Writes only ONE new table
(weg) in /var/lib/clay/wiki.db. Never touches artikel/kante/kuration/
anreicherung/fts_*/datei/fundort/messung/graph_*/problem/folgerung.

    weg.py laufen           jede bekannte Route tatsaechlich gehen, weg neu fuellen
    weg.py zeigen           alle Routen
    weg.py wie <ziel> [--von <ursprung>]   die beste bewiesene Route + Alter
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
import sys

# Modulgrenze: der LESE-Zweig oeffnet die Datenbank nicht mehr selbst.
# udb ist die Vordertuer fuer den nur-lesenden Fall; der Schreib-Zweig
# bleibt lokal, weil udb.verbindung() strukturell nur liest.
sys.path.insert(0, "/opt/unifieddb")
import udb
import time
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = "/var/lib/clay/wiki.db"
WIRTE_TABELLE = Path("/var/lib/clay/wirte.json")
HIER = os.uname().nodename  # lokaler Wirt -- wie karte.py

# --- Wegekandidaten ----------------------------------------------------
# Das ist die einzige "gepflegte" Liste hier -- und sie pflegt nur, WELCHE
# Kombinationen (Ursprung, Ziel, Transport, Adresse) ueberhaupt versucht
# werden, genau wie wirte.py's KONTEN-Tupel Kandidaten-Konten pflegt statt
# ein fertiges Ergebnis. Ob eine Kombination WIRKLICH funktioniert, welches
# Konto greift, welches Tor gilt und wie das Ergebnis aussieht -- das wird
# bei jedem `laufen` neu GEMESSEN, nie hier eingetragen.
#
# konto_kandidaten: Konten, die probiert werden (gemessen wie wirte.py).
# adresse: die tatsaechliche IP/der Alias, der fuer DIESEN Transport benutzt
#          wird -- das ist der Kern der Sache: derselbe Wirt hat mehrere
#          Adressen, und welche erreichbar ist, haengt vom Ursprung ab.
ROUTEN_KANDIDATEN = [
    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "ai-core-node-projekt-frankenstein",
     "transport": "lokal", "adresse": None, "konto_kandidaten": None, "proxyjump_via": None, "schritte": None},

    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "clayverse",
     "transport": "ssh-ueber-Tailscale", "adresse": "100.71.48.1",
     "konto_kandidaten": ["root", "clay", "ai-core-node"], "proxyjump_via": None, "schritte": None},
    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "clayverse",
     "transport": "ssh-direkt", "adresse": "31.97.117.141",
     "konto_kandidaten": ["root", "clay"], "proxyjump_via": None, "schritte": None},

    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "clayverse-alt",
     "transport": "ssh-ueber-Tailscale", "adresse": "100.116.119.67",
     "konto_kandidaten": ["root", "ubuntu"], "proxyjump_via": None, "schritte": None},
    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "clayverse-alt",
     "transport": "ssh-direkt", "adresse": "72.61.19.188",
     "konto_kandidaten": ["root", "ubuntu"], "proxyjump_via": None, "schritte": None},
    # BUG gefangen beim ersten Testlauf: diese Zeile probierte anfangs nur
    # nochmal die IP aus der ssh-direkt-Zeile (adresse=72.61.19.188) unter
    # anderem Namen -- ein Etikettenschwindel, kein echter ProxyJump-Test.
    # Jetzt via_ursprung_ssh gesetzt: die Zeile geht WIRKLICH ueber
    # clayverse als Sprung, genau wie die schritte-Liste behauptet.
    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "clayverse-alt",
     "transport": "ProxyJump", "adresse": "100.116.119.67",
     "konto_kandidaten": ["root", "ubuntu"], "proxyjump_via": "clayverse (31.97.117.141)",
     "via_ursprung_ssh": ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "root@31.97.117.141"],
     "schritte": [
         "1) ssh root@31.97.117.141   (nach clayverse)",
         "2) ssh root@100.116.119.67  (von dort weiter nach clayverse-alt, Tailscale)",
     ]},

    # Der vom Auftrag genannte Fall: derselbe Weg von einem ANDEREN Ursprung
    # aus. Wird eigenstaendig gelaufen (per SSH-Doppelsprung), nicht aus der
    # obigen Zeile abgeleitet.
    {"ursprung": "clayverse", "ziel_wirt": "clayverse-alt",
     "transport": "ssh-ueber-Tailscale", "adresse": "100.116.119.67",
     "konto_kandidaten": ["root", "ubuntu"], "proxyjump_via": None, "schritte": None,
     "via_ursprung_ssh": ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8", "root@31.97.117.141"]},

    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "andreas-MACO",
     "transport": "ssh-ueber-Tailscale", "adresse": "100.92.234.52",
     "konto_kandidaten": ["gabriel", "andreas"], "proxyjump_via": None, "schritte": None},

    {"ursprung": "ai-core-node-projekt-frankenstein", "ziel_wirt": "desktop-ufb20ka",
     "transport": "ssh-ueber-Tailscale", "adresse": "100.123.67.108",
     "konto_kandidaten": ["Win11"], "proxyjump_via": None, "schritte": None},
]

PROBE_BEFEHL = "hostname; whoami; date -u"


# ---------------------------------------------------------------- utilities

def connect_db(readonly=False):
    if readonly:
        con = udb.verbindung()
    else:
        con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    return con


def retry_locked(fn, tries=6, base_sleep=0.5):
    last = None
    for i in range(tries):
        try:
            return fn()
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() or "busy" in str(e).lower():
                last = e
                time.sleep(base_sleep * (i + 1))
                continue
            raise
    raise last


def now_iso():
    return datetime.now(timezone.utc).isoformat()


def _lauf(befehl: list, zeit: int = 15) -> tuple:
    try:
        p = subprocess.run(befehl, capture_output=True, text=True, timeout=zeit)
        return p.returncode, (p.stdout + p.stderr).strip()
    except subprocess.TimeoutExpired:
        return 124, "Zeitueberschreitung"
    except Exception as e:
        return 1, str(e)


def _ssh_opts():
    return ["-o", "BatchMode=yes", "-o", "ConnectTimeout=8",
            "-o", "StrictHostKeyChecking=accept-new"]


def _ssh_befehl(konto, adresse, remote_cmd, via_ursprung_ssh=None):
    """Baut den tatsaechlichen SSH-Aufruf. via_ursprung_ssh, falls gesetzt,
    fuehrt den Sprung ZUERST aus und haengt den zweiten ssh-Aufruf als
    EINEN Remote-Befehlsstring an (echter Doppelsprung, kein ProxyJump-
    Alias -- der Fallback-Weg, falls der direkte je wieder blockiert wird)."""
    if via_ursprung_ssh:
        inner_cmd = "ssh " + " ".join(_ssh_opts()) + f" {konto}@{adresse} '{remote_cmd}'"
        return via_ursprung_ssh + [inner_cmd]
    return ["ssh"] + _ssh_opts() + [f"{konto}@{adresse}", remote_cmd]


def _tor_lage_lokal() -> str:
    schranke = Path.home() / ".schranke"
    if schranke.is_dir():
        n = len(list(schranke.glob("anfrage-*.txt")))
        return f"lokale Schranke aktiv (~/.schranke, {n} Anfragen archiviert)"
    return "keine lokale Schranke gefunden (~/.schranke fehlt)"


def _tor_lage_remote(konto, adresse, via_ursprung_ssh=None) -> str:
    """Live gemessen, nicht angenommen: existieren die Tor-Marker auf dem
    ZIEL? Prueft in EINEM SSH-Aufruf beide bekannten Marker-Pfade."""
    probe = ("test -f /etc/claude-code/managed-settings.json && echo MSJ_JA || echo MSJ_NEIN; "
             "test -d /var/lib/clay-tor && echo TOR_JA || echo TOR_NEIN")
    befehl = _ssh_befehl(konto, adresse, probe, via_ursprung_ssh)
    rc, aus = _lauf(befehl, 12)
    if rc != 0:
        return f"nicht messbar ({aus[:120]})"
    msj = "MSJ_JA" in aus
    tor = "TOR_JA" in aus
    if msj and tor:
        return "tor_hook.py PreToolUse via /etc/claude-code/managed-settings.json (gilt fuer `claude`-Sitzungen auf diesem Wirt, NICHT fuer rohe SSH-Admin-Befehle wie diesen)"
    if not msj and not tor:
        return "kein Tor gefunden (kein managed-settings.json, kein /var/lib/clay-tor -- nackter Wirt ohne Clay-Stack)"
    return f"teilweise: managed-settings.json={msj} /var/lib/clay-tor={tor}"


def _darf_messen(konto, adresse, via_ursprung_ssh=None, lokal=False) -> str:
    """lesen ist durch die erfolgreiche Anmeldung selbst bewiesen. root oder
    passwortloses sudo -> effektiv lesen+schreiben+ausfuehren, GEMESSEN per
    `sudo -n true`, nicht angenommen."""
    if konto == "root":
        return "lesen,schreiben,ausfuehren (root)"
    probe = "sudo -n true"
    if lokal:
        rc, _ = _lauf(["bash", "-c", probe], 8)
    else:
        befehl = _ssh_befehl(konto, adresse, probe, via_ursprung_ssh)
        rc, _ = _lauf(befehl, 12)
    if rc == 0:
        return f"lesen,schreiben,ausfuehren ({konto} + passwortloses sudo, gemessen)"
    return f"lesen (nur {konto}, sudo nicht passwortlos oder nicht gemessen)"


def weg_id(ursprung, ziel_wirt, transport, proxyjump_via):
    h = hashlib.sha256(
        f"{ursprung}|{ziel_wirt}|{transport}|{proxyjump_via or ''}".encode("utf-8")
    ).hexdigest()
    return f"w_{h[:24]}"


def ensure_schema(con):
    con.executescript("""
        CREATE TABLE IF NOT EXISTS weg(
            id TEXT PRIMARY KEY,
            ursprung TEXT NOT NULL,
            ziel_wirt TEXT NOT NULL,
            ziel_dienst TEXT,
            ziel_pfad TEXT,
            transport TEXT NOT NULL,
            proxyjump_via TEXT,
            konto TEXT,
            befehl TEXT NOT NULL,
            tor TEXT NOT NULL,
            darf TEXT NOT NULL,
            schritte TEXT,
            erreichbar INTEGER NOT NULL,
            fehler TEXT,
            zuletzt_bewiesen TEXT NOT NULL,
            beleg TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_weg_ziel ON weg(ziel_wirt);
        CREATE INDEX IF NOT EXISTS idx_weg_ursprung_ziel ON weg(ursprung, ziel_wirt);
    """)
    con.commit()


# ---------------------------------------------------------------- laufen

def cmd_laufen(args):
    t0 = time.time()
    if not WIRTE_TABELLE.exists():
        print(f"warnung: {WIRTE_TABELLE} fehlt -- wirte.py ermitteln zuerst laufen lassen", file=sys.stderr)

    proven, failed = 0, 0
    rows = []
    for kand in ROUTEN_KANDIDATEN:
        ursprung = kand["ursprung"]
        ziel = kand["ziel_wirt"]
        transport = kand["transport"]
        via_ursprung_ssh = kand.get("via_ursprung_ssh")
        proxyjump_via = kand.get("proxyjump_via")
        schritte = kand.get("schritte")
        rid = weg_id(ursprung, ziel, transport, proxyjump_via)
        zeit = now_iso()

        if transport == "lokal":
            rc, aus = _lauf(["bash", "-c", PROBE_BEFEHL], 10)
            konto = os.environ.get("USER") or _lauf(["whoami"])[1]
            erreichbar = rc == 0
            befehl = PROBE_BEFEHL + "  (lokal)"
            tor = _tor_lage_lokal()
            darf = _darf_messen(konto, None, lokal=True) if erreichbar else "nichts"
            fehler = None if erreichbar else aus[:300]
        else:
            konto_treffer = None
            rc, aus = 1, "kein Konto probiert"
            for konto in kand["konto_kandidaten"]:
                befehl_liste = _ssh_befehl(konto, kand["adresse"], PROBE_BEFEHL, via_ursprung_ssh)
                rc, aus = _lauf(befehl_liste, 15)
                if rc == 0 and aus:
                    konto_treffer = konto
                    break
            erreichbar = konto_treffer is not None
            konto = konto_treffer
            if via_ursprung_ssh:
                befehl = (f"ssh root@31.97.117.141 'ssh {konto or kand['konto_kandidaten'][0]}@{kand['adresse']} "
                          f"\"{PROBE_BEFEHL}\"'  (Doppelsprung von {ursprung} aus)")
            else:
                befehl = f"ssh {konto or kand['konto_kandidaten'][0]}@{kand['adresse']}  \"{PROBE_BEFEHL}\""
            if erreichbar:
                tor = _tor_lage_remote(konto, kand["adresse"], via_ursprung_ssh)
                darf = _darf_messen(konto, kand["adresse"], via_ursprung_ssh)
                fehler = None
            else:
                tor = "nicht messbar (Ziel nicht erreichbar)"
                darf = "nichts"
                fehler = aus[:300] or "nicht erreichbar"

        if erreichbar:
            proven += 1
        else:
            failed += 1

        rows.append((
            rid, ursprung, ziel, kand.get("ziel_dienst"), kand.get("ziel_pfad"),
            transport, proxyjump_via, konto, befehl, tor, darf,
            json.dumps(schritte, ensure_ascii=False) if schritte else None,
            1 if erreichbar else 0, fehler, zeit, aus[:2000],
        ))
        marke = "OK" if erreichbar else "FEHLT"
        print(f"  [{marke}] {ursprung} -> {ziel} ({transport}) konto={konto}")

    _speichern(rows)

    elapsed_ms = round((time.time() - t0) * 1000, 1)
    print(json.dumps({
        "routen_versucht": len(ROUTEN_KANDIDATEN),
        "bewiesen": proven,
        "fehlgeschlagen": failed,
        "laufzeit_ms": elapsed_ms,
    }, indent=2, ensure_ascii=False))


def _speichern(rows):
    """wiki.db lebt auf clayverse. Die Wegmessung MUSS aber vom echten
    Ursprung aus laufen (sonst ist 'ursprung' eine Erfindung) -- deshalb
    laeuft `laufen` typischerweise lokal (hier: ai-core-node-projekt-
    frankenstein, das echte Tailscale-Interface). Liegt die DB lokal nicht
    vor, werden die gemessenen Zeilen (nicht mehr, nichts hinzuerfunden)
    ueber SSH an clayverse weitergereicht, wo `_einspielen` sie mit exakt
    derselben ensure_schema()/DELETE+INSERT-Logik schreibt, die auch ein
    lokaler Lauf verwenden wuerde."""
    if Path(DB_PATH).exists():
        con = retry_locked(lambda: connect_db(readonly=False))
        try:
            _einspielen_rows(con, rows)
        finally:
            con.close()
        return
    payload = json.dumps(rows, ensure_ascii=False)
    p = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "root@31.97.117.141",
         "python3", "/opt/clayverse/werkzeug/weg.py", "_einspielen"],
        input=payload, capture_output=True, text=True, timeout=30,
    )
    if p.returncode != 0:
        print("FEHLER beim Einspielen auf clayverse:", p.stderr[:500], file=sys.stderr)
        sys.exit(1)
    print("  (auf clayverse gespeichert: " + p.stdout.strip() + ")")


def cmd_einspielen(args):
    """Interner Gegenpart zu _speichern()'s Remote-Zweig: liest die vom
    lokalen Lauf gemessenen Zeilen (JSON-Array von Tupeln) von stdin und
    schreibt sie -- unveraendert -- in die weg-Tabelle. Erfindet nichts,
    misst nichts nach; die Messung geschah bereits am echten Ursprung."""
    rows = json.loads(sys.stdin.read())
    con = retry_locked(lambda: connect_db(readonly=False))
    try:
        _einspielen_rows(con, [tuple(r) for r in rows])
    finally:
        con.close()
    print(json.dumps({"eingespielt": len(rows)}))


def _einspielen_rows(con, rows):
    ensure_schema(con)
    con.execute("BEGIN")
    con.execute("DELETE FROM weg")
    con.executemany(
        "INSERT INTO weg(id,ursprung,ziel_wirt,ziel_dienst,ziel_pfad,transport,"
        "proxyjump_via,konto,befehl,tor,darf,schritte,erreichbar,fehler,"
        "zuletzt_bewiesen,beleg) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
        rows,
    )
    con.commit()


# ---------------------------------------------------------------- zeigen

def cmd_zeigen(args):
    con = retry_locked(lambda: connect_db(readonly=True))
    try:
        rows = con.execute(
            "SELECT ursprung,ziel_wirt,transport,konto,erreichbar,zuletzt_bewiesen,fehler "
            "FROM weg ORDER BY ziel_wirt, ursprung"
        ).fetchall()
        for ursprung, ziel, transport, konto, erreichbar, bewiesen, fehler in rows:
            marke = "OK   " if erreichbar else "TOT  "
            info = f"{konto or '-'}" if erreichbar else f"FEHLER: {(fehler or '')[:60]}"
            print(f"  {marke} {ursprung:<32} -> {ziel:<32} [{transport:<18}] {info}  (bewiesen {bewiesen[:16]})")
    finally:
        con.close()


# ---------------------------------------------------------------- wie

def cmd_wie(args):
    t0 = time.time()
    con = retry_locked(lambda: connect_db(readonly=True))
    try:
        ursprung = args.von or HIER
        q = ("SELECT id,ursprung,ziel_wirt,ziel_dienst,ziel_pfad,transport,proxyjump_via,"
             "konto,befehl,tor,darf,schritte,erreichbar,fehler,zuletzt_bewiesen,beleg "
             "FROM weg WHERE ziel_wirt=? AND ursprung=? ORDER BY erreichbar DESC")
        rows = con.execute(q, (args.ziel, ursprung)).fetchall()
        if not rows:
            # kein Weg von diesem genauen Ursprung bewiesen -- das ist ein
            # Befund, keine Erfindung eines Ersatzes.
            elapsed_ms = round((time.time() - t0) * 1000, 2)
            print(json.dumps({
                "ziel": args.ziel, "von": ursprung, "gefunden": False,
                "hinweis": "kein bewiesener Weg von diesem Ursprung -- `weg.py zeigen` fuer alle bekannten Ursprung/Ziel-Paare",
                "ms": elapsed_ms,
            }, indent=2, ensure_ascii=False))
            return
        out = []
        now = datetime.now(timezone.utc)
        for (rid, u, z, zd, zp, transport, pj, konto, befehl, tor, darf, schritte,
             erreichbar, fehler, bewiesen, beleg) in rows:
            try:
                alter_s = (now - datetime.fromisoformat(bewiesen)).total_seconds()
            except Exception:
                alter_s = None
            out.append({
                "ziel_wirt": z, "ziel_dienst": zd, "ziel_pfad": zp,
                "transport": transport, "proxyjump_via": pj, "konto": konto,
                "befehl": befehl, "tor": tor, "darf": darf,
                "schritte": json.loads(schritte) if schritte else None,
                "erreichbar": bool(erreichbar), "fehler": fehler,
                "zuletzt_bewiesen": bewiesen,
                "alter_sekunden": round(alter_s) if alter_s is not None else None,
                "beleg": beleg,
            })
        elapsed_ms = round((time.time() - t0) * 1000, 2)
        print(json.dumps({
            "ziel": args.ziel, "von": ursprung, "gefunden": True,
            "anzahl_routen": len(out), "ms": elapsed_ms, "routen": out,
        }, indent=2, ensure_ascii=False))
    finally:
        con.close()


# ---------------------------------------------------------------- main

def main():
    p = argparse.ArgumentParser(description="weg.py -- Wegtabelle")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("laufen", help="jede bekannte Route tatsaechlich gehen").set_defaults(func=cmd_laufen)
    sub.add_parser("zeigen", help="alle Routen").set_defaults(func=cmd_zeigen)
    sub.add_parser("_einspielen", help="intern: Zeilen von stdin uebernehmen (Remote-Zweig von laufen)").set_defaults(func=cmd_einspielen)

    p_wie = sub.add_parser("wie", help="wie komme ich zu <ziel>")
    p_wie.add_argument("ziel")
    p_wie.add_argument("--von", default=None, help="Ursprung, Vorgabe: dieser Wirt")
    p_wie.set_defaults(func=cmd_wie)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
