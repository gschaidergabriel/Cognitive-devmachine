"""Der Paketarbeiter -- fuehrt aus, was Zero geschnuert hat. Eng eingezaeunt.

Gabriels Entscheidung 2026-08-18: "Ja, aber eng eingezaeunt."

⭐⭐ DIE TRAGENDE ENTSCHEIDUNG: KEINE SCHALE.

Der naheliegende Bau waere ein Dienst, der Schalbefehle ausfuehrt, die ein
Sprachmodell geschrieben hat. Genau den hat ein Sonett-Arbeiter heute
abgelehnt, und zu Recht: eine Schale ist kein Zaun, sondern ein Tor.

Der Arbeiter bekommt deshalb DATEIWERKZEUGE statt einer Schale -- Read, Edit,
Write, Grep, Glob -- und KEIN Bash. Fuer die tatsaechliche Arbeit
("Telefonnummer aus der Kontaktseite entfernen") reicht das vollstaendig.
Was damit unmoeglich wird, ist alles andere: kein curl, kein ssh, kein
systemctl, kein Nachladen, keine Rechteaenderung. Der Unterschied zwischen
"darf Dateien bearbeiten" und "darf Befehle ausfuehren" ist der ganze
Sicherheitsgewinn, und er kostet fuer diesen Zweck nichts.

DIE WEITEREN ZAEUNE, alle vom Kern durchgesetzt und nicht von gutem Willen:

  Arbeitsverzeichnis   ein eigener Ordner je Paket, sonst nichts beschreibbar
  wiki.db              UNERREICHBAR (InaccessiblePaths) -- der Arbeiter sieht
                       kein einziges Gespraech und kann nichts eintragen
  /etc/clayverse       UNERREICHBAR -- keine Zugangsdaten anderer Dienste
  ProtectSystem        strict; PrivateTmp; NoNewPrivileges
  Frist                hart, danach gilt das Paket als gescheitert

⭐ DER ARBEITER SCHREIBT NIE IN DIE DATENBANK. Er legt sein Ergebnis als Datei
in seinem Arbeitsordner ab; dieser Prozess hier liest sie und traegt sie ein.
Damit ist die Datenbank fuer den unsichersten Teil des Systems gar nicht
erreichbar -- statt sie ihm zu erlauben und auf Wohlverhalten zu hoffen.

⚠️ WAS DIESER ZAUN NICHT LEISTET, ehrlich benannt: der Arbeiter laeuft als
`clay` und kann damit die Anmeldedatei von Claude Code lesen -- er MUSS es, um
ueberhaupt zu starten. Ohne Schale kann er sie nirgendwohin schicken, aber sie
ist ihm nicht verborgen. Wer das schliessen will, braucht einen eigenen
Anmeldeschluessel je Arbeiter; das ist hier bewusst nicht gebaut und steht
darum hier.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
from pathlib import Path

ARBEITSWURZEL = Path("/var/lib/clay/paketarbeit")
FRIST_S = 900
MAX_JE_LAUF = 1                  # EIN Paket je Lauf: das Konto ist geteilt und endlich
ERGEBNISDATEI = "ERGEBNIS.md"
# Claude Code braucht ein beschreibbares Heimatverzeichnis, sonst startet es nicht.
# ⚠️ WIRTPFAD, nicht Containerpfad. /var/lib/clayverse/users/... gibt es nur
# IM Container; der Arbeiter laeuft auf dem Wirt. Die Verwechslung kostete zwei
# Laeufe ("Not logged in" und 226/NAMESPACE).
# Ein EIGENES Heim, nicht /var/lib/clay: dort liegt die wiki.db, und die muesste
# dann beschreibbar sein -- der Zaun waere mit einer Zeile weg.
# Die Anmeldung darin ist ein Verweis auf die eine gemeinsame Datei, damit eine
# Erneuerung nicht an zwei Stellen auseinanderlaeuft.
HEIMAT = "/var/lib/clay/paketarbeit/.heim"

# Dateiwerkzeuge, keine Schale. Das ist der Zaun.
WERKZEUGE = ("Read", "Edit", "Write", "Grep", "Glob")


def _anweisung(paket: dict) -> str:
    return f"""You work inside {ARBEITSWURZEL}/{paket['paket_id']}/. That directory is the
ONLY place you may write. You have file tools only -- no shell, no network.

TASK (caveman, from Zero):
{paket['auftrag']}

THING: {paket['womit'] or '(not named)'}
WHY:   {paket['warum'] or '(not given)'}

WHEN DONE write {ERGEBNISDATEI} in your directory, exactly this shape:

  ## ergebnis
  <what you did, plain German, short>

  ## beleg
  <the EVIDENCE: file paths and line numbers you changed, or the exact command
   output you saw. If you cannot show evidence, write NICHTS GETAN and say why.>

⚠️ Do not claim you did something you cannot show. An unverified success is
worse than an honest failure -- it looks like knowledge and is not.
If the thing you were asked to touch is not inside your directory, say so in
{ERGEBNISDATEI} and stop. Do not look for it elsewhere.
"""


def _lies_ergebnis(ordner: Path) -> tuple[str, str]:
    d = ordner / ERGEBNISDATEI
    if not d.is_file():
        return "", ""
    text = d.read_text(encoding="utf-8", errors="replace")[:4000]
    erg, beleg = "", ""
    teil = None
    for zeile in text.splitlines():
        k = zeile.strip().lower()
        if k.startswith("## ergebnis"):
            teil = "e"; continue
        if k.startswith("## beleg"):
            teil = "b"; continue
        if teil == "e":
            erg += zeile + "\n"
        elif teil == "b":
            beleg += zeile + "\n"
    return erg.strip(), beleg.strip()


def _fuehre_aus(paket: dict, ordner: Path, frist: int) -> tuple[int, str]:
    """claude -p mit Dateiwerkzeugen, im Kernzaun. Gibt (rc, stderr) zurueck."""
    einheit = f"paketwerk-{paket['paket_id']}"
    argv = [
        "systemd-run", "--unit", einheit, "--collect", "--wait", "--quiet",
        "--uid", "clay", "--gid", "clay",
        f"--property=WorkingDirectory={ordner}",
        f"--property=RuntimeMaxSec={frist}",
        "--property=ProtectSystem=strict",
        "--property=ProtectHome=yes",
        "--property=PrivateTmp=yes",
        "--property=NoNewPrivileges=yes",
        # Der Arbeitsordner ist der einzige Ort fuer NUTZDATEN. Claudes
        # Heimatverzeichnis muss zusaetzlich beschreibbar sein, sonst startet
        # das Programm nicht (ProtectSystem=strict sperrt sonst alles) --
        # gemessen: rc=1 mit leerem stderr, der undankbarste Fehler ueberhaupt.
        f"--property=ReadWritePaths={ordner} {HEIMAT}",
        # ⭐ Die Datenbank ist dem Arbeiter NICHT erlaubt, sondern UNSICHTBAR.
        # Erlauben und auf Wohlverhalten hoffen waere kein Zaun.
        "--property=InaccessiblePaths=/var/lib/clay/wiki.db /etc/clayverse",
        f"--setenv=HOME={HEIMAT}",
        "--setenv=PATH=/usr/local/bin:/usr/bin:/bin",
        "--setenv=LANG=C.UTF-8",
        "--setenv=DISABLE_UPDATES=1",
        "--",
        "claude", "-p", _anweisung(paket),
        "--allowedTools", *WERKZEUGE,
        "--permission-mode", "dontAsk",
        "--output-format", "text",
        "--no-session-persistence",
        "--max-turns", "24",
    ]
    try:
        cp = subprocess.run(argv, capture_output=True, text=True, timeout=frist + 60)
        # Ein leeres stderr ist keine Auskunft. Dann stdout mitnehmen --
        # sonst steht im Beleg "kein Beleg. stderr:" und niemand weiss mehr.
        hinweis = (cp.stderr or "").strip() or (cp.stdout or "").strip()
        return cp.returncode, hinweis[:600] or "keine Ausgabe"
    except subprocess.TimeoutExpired:
        return 124, "Frist ueberschritten"


def arbeite(db, *, frist: int = FRIST_S) -> dict:
    """Ein offenes Paket abarbeiten. Mehr nicht -- das Konto ist geteilt."""
    from . import arbeitspaket as ap
    from . import raum

    try:
        db.db.execute("SELECT 1 FROM entityos_arbeitspaket LIMIT 1")
    except Exception:
        return {"getan": 0, "grund": "Tabelle fehlt"}

    # Haengengebliebene zuerst: ein Paket, das ewig `laeuft`, sieht aus wie
    # eines, an dem gearbeitet wird. Genau das ist die Fehlerart, gegen die
    # hier gebaut wird.
    verfallen = 0
    for r in db.db.execute(
            "SELECT paket_id FROM entityos_arbeitspaket WHERE stand='laeuft' AND geaendert < ?",
            (time.time() - frist * 2,)):
        ap.stand_setzen(db, paket_id=r["paket_id"], stand="gescheitert",
                        ergebnis="kein Lebenszeichen innerhalb der Frist",
                        beleg="Frist ueberschritten, Arbeiter hat sich nicht gemeldet")
        verfallen += 1

    # Nur EINES, und nur wenn gerade keines laeuft.
    if db.db.execute("SELECT COUNT(*) FROM entityos_arbeitspaket WHERE stand='laeuft'").fetchone()[0]:
        return {"getan": 0, "verfallen": verfallen, "grund": "es laeuft bereits eines"}
    r = db.db.execute(
        "SELECT paket_id,auftrag,womit,warum,besteller FROM entityos_arbeitspaket "
        "WHERE stand='offen' ORDER BY erstellt LIMIT 1").fetchone()
    if not r:
        return {"getan": 0, "verfallen": verfallen, "grund": "nichts offen"}
    paket = dict(r)

    # Im Raum anmelden -- die anderen drei Plaetze sollen es sehen.
    stoss = None
    try:
        antwort = raum.sagen(db, session_id="paketarbeiter", mensch=paket["besteller"],
                             platz=0, was=f"work package {paket['paket_id']}",
                             womit=paket["womit"] or paket["paket_id"])
        stoss = antwort.get("kollision")
    except Exception:
        pass
    if stoss:
        return {"getan": 0, "verfallen": verfallen,
                "grund": f"kollidiert mit {stoss['haelt']}", "paket": paket["paket_id"]}

    ordner = ARBEITSWURZEL / paket["paket_id"]
    ordner.mkdir(parents=True, exist_ok=True)
    # Dem Arbeiter gehoeren: er laeuft als clay, dieser Prozess womoeglich als
    # root. Ohne das hat er im einzigen ihm erlaubten Ordner kein Schreibrecht
    # -- gemessen, und er hat es korrekt gemeldet statt daran vorbeizubauen.
    try:
        shutil.chown(ordner, user="clay", group="clay")
        for kind in ordner.iterdir():
            shutil.chown(kind, user="clay", group="clay")
    except (LookupError, PermissionError, OSError):
        pass  # laeuft dieser Prozess schon als clay, ist nichts zu tun
    ap.stand_setzen(db, paket_id=paket["paket_id"], stand="laeuft")

    rc, fehler = _fuehre_aus(paket, ordner, frist)
    erg, beleg = _lies_ergebnis(ordner)

    # stand_setzen DARF DIESEN DIENST NIE ZUM ABSTURZ BRINGEN. Ein Absturz
    # hier laesst das Paket in `laeuft` haengen, und jeder weitere Lauf meldet
    # "es laeuft bereits eines" -- die Warteschlange ist tot. Deshalb bestimmen
    # wir den Stand SELBST (mit derselben Liste, die stand_setzen prueft) und
    # fangen jeden Fehler ab.
    if not (erg or beleg):
        ziel = "gescheitert"
        e2 = f"kein Ergebnis (rc={rc})"
        b2 = f"kein Beleg. stderr: {fehler[:200]}"
    elif ap.ist_leerer_beleg(erg, beleg):
        # Ein ehrlicher Verweigerungsbericht ist KEIN Fehlschlag des Arbeiters.
        ziel, e2, b2 = "abgelehnt", erg, beleg
    else:
        ziel, e2, b2 = "fertig", erg, beleg
    try:
        ap.stand_setzen(db, paket_id=paket["paket_id"], stand=ziel, ergebnis=e2, beleg=b2)
        stand = ziel
    except Exception as ex:
        # Selbst wenn die Beweisregel den Uebergang ablehnt: das Paket muss aus
        # `laeuft` heraus, sonst blockiert es die Warteschlange fuer immer.
        grund = "Stand " + str(ziel) + " abgelehnt: " + str(ex)
        try:
            ap.stand_setzen(db, paket_id=paket["paket_id"], stand="gescheitert",
                            ergebnis=(e2 or "")[:400], beleg=grund[:400])
        except Exception:
            pass
        stand = "gescheitert"
    try:
        raum.frei(db, session_id="paketarbeiter")
    except Exception:
        pass
    return {"getan": 1, "verfallen": verfallen, "paket": paket["paket_id"],
            "stand": stand, "rc": rc}
