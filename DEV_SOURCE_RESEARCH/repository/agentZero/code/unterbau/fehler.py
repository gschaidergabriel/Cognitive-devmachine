#!/usr/bin/env python3
"""fehler.py — die Fehlerhistorie als Werkzeug, nicht als Text zum Auswendiglernen.

Owner-Auftrag (Gabriel, 15.08.2026), woertlich sinngemaess: jeder Fehler und
jede Best Practice soll in ClayVerse landen, damit es ihn NIE wiederholt --
einerseits weil Werkzeuge entsprechend kalibriert sind (der falsche Weg wird
gar nicht erst angeboten), andererseits weil die vereinte Datenbank passend
zur jeweiligen Taetigkeit den relevanten vergangenen Fehler LIEFERT, ohne
dass jemand eine Checkliste liest.

Dieses Werkzeug ist der zweite Mechanismus. Es speichert nichts Neues an
Regeln -- `/var/lib/clay/CLAUDE.md` bleibt die Methode. Es speichert
GEMESSENE Fehler, jeder an ein mechanisches Ausloesemuster gebunden, und legt
bei einer Anfrage die passenden vor.

Mechanical only. No model calls, no network calls, stdlib only (sqlite3, re,
argparse). Matching ist ausschliesslich `re.search` gegen `ausloeser_muster`
-- ein Werkzeugname, eine SQL-Form, eine Tabelle, ein Dateimuster, eine
Befehlsform. Nichts Semantisches. Kann ein Ausloeser nicht mechanisch gefasst
werden, wird er NICHT aufgenommen (siehe "Verworfen" unten im Bericht).

Writes ONLY into the `fehler` table of /var/lib/clay/wiki.db (WAL,
busy_timeout, kurze Transaktionen -- dasselbe Muster wie problem.py/
folgerung.py/wiki.py, weil mehrere Agenten die Datenbank gleichzeitig
beschreiben). Alles andere in dieser Datenbank ist von hier aus nur lesend.

Kein bau.py, kein git commit/push, keine Loeschbefehle in der Shell.

CLI:
    fehler.py ernten                        die fest hinterlegte Startbelegung
                                             einfuegen (idempotent, INSERT OR IGNORE)
    fehler.py neu --id ... --art ... \\
                   --muster ... --was-passiert ... --wie-erkannt ... \\
                   --wie-vermieden ... --schwere ... --beleg ... --quelle ... \\
                   [--bestaetigt-durch ...] [--erkannt-am ...]
    fehler.py pruefen --taetigkeit "<text>"  zeigt alle treffenden Zeilen
    fehler.py stand                          Zaehlung nach art/schwere
    fehler.py zu <art>                       alle Zeilen einer art

Importierbare Schnittstelle fuer andere Werkzeuge:
    pruefen(taetigkeit: str, *, conn: Optional[sqlite3.Connection] = None,
            limit: int = 10) -> list[dict]

    Signatur bewusst an vorprozessor.py's eigene Konvention angelehnt
    (Text rein, optionale bestehende Verbindung durchreichen, own-Flag
    intern). Vorgeschlagene Einbaustelle in vorprozessor.py (NICHT hier
    vorgenommen -- eine andere Instanz besitzt diese Datei):

        Datei   /opt/clayverse/werkzeug/vorprozessor.py
        Ort     Funktion paket(), unmittelbar VOR `return result`
                (nach dem vollstaendigen Aufbau von `result = {...}`,
                d.h. nach der Zeile "latenz_us": int(elapsed_us)},
                vor dem `if lauf_id:`-Block -- die exakte Zeile haengt vom
                Stand der Datei ab, der Anker ist "vor return result").
        Aenderung (1 Zeile, von der vorprozessor.py-besitzenden Instanz
                   einzufuegen):
                result["warnungen"] = fehler.pruefen(text, conn=c)
                (dieselbe bereits offene Verbindung `c` wird durchgereicht --
                 keine zweite Verbindung noetig, kein Zusatzaufwand jenseits
                 der eigentlichen Abfrage.)
        Kosten  ~16 vorkompilierte Regex gegen einen kurzen Text, < 0.2 ms
                bei der heutigen Zeilenzahl -- gemessen unten in `_selbsttest`.

    tor_hook.py-Vorschlag: siehe Abschnitt PROPOSAL_TOR_HOOK weiter unten in
    dieser Datei (Kommentarblock, kein Code-Eingriff).
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
import time
from datetime import datetime, timezone
from typing import Optional

DB_PATH = "/var/lib/clay/wiki.db"

ART_WERTE = ("sql", "shell", "python", "daten", "provenienz", "methode")
SCHWERE_WERTE = ("hoch", "mittel", "niedrig")


def connect_db() -> sqlite3.Connection:
    con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA journal_mode=WAL")
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("PRAGMA synchronous=NORMAL")
    return con


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS fehler (
            id TEXT PRIMARY KEY,
            art TEXT NOT NULL CHECK (art IN {ART_WERTE}),
            ausloeser_muster TEXT NOT NULL,
            was_passiert TEXT NOT NULL,
            wie_erkannt TEXT NOT NULL,
            wie_vermieden TEXT NOT NULL,
            schwere TEXT NOT NULL CHECK (schwere IN {SCHWERE_WERTE}),
            beleg TEXT NOT NULL,
            quelle TEXT NOT NULL,
            erkannt_am TEXT,
            bestaetigt_durch TEXT
        )
    """)
    con.execute("CREATE INDEX IF NOT EXISTS idx_fehler_art ON fehler(art)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_fehler_schwere ON fehler(schwere)")
    con.commit()


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+0000")


# ── Einfuegen ────────────────────────────────────────────────────────────

def neu(con: sqlite3.Connection, *, id: str, art: str, ausloeser_muster: str,
        was_passiert: str, wie_erkannt: str, wie_vermieden: str, schwere: str,
        beleg: str, quelle: str, erkannt_am: Optional[str] = None,
        bestaetigt_durch: Optional[str] = None) -> None:
    if art not in ART_WERTE:
        raise ValueError(f"unbekannte art '{art}', erlaubt: {ART_WERTE}")
    if schwere not in SCHWERE_WERTE:
        raise ValueError(f"unbekannte schwere '{schwere}', erlaubt: {SCHWERE_WERTE}")
    if not beleg or not beleg.strip():
        raise ValueError(
            "REJECTED: fehler braucht --beleg (ein Fehler ohne Beleg ist eine "
            "Behauptung, keine Messung -- Regel 3)."
        )
    if not quelle or not quelle.strip():
        raise ValueError(
            "REJECTED: fehler braucht --quelle (Herkunft der Lehre -- "
            "koordinator/agent/system -- ist Pflicht, nicht Kuer)."
        )
    try:
        re.compile(ausloeser_muster)
    except re.error as e:
        raise ValueError(f"REJECTED: ausloeser_muster ist kein gueltiger regulaerer "
                          f"Ausdruck: {e}")
    con.execute(
        "INSERT INTO fehler (id, art, ausloeser_muster, was_passiert, wie_erkannt, "
        "wie_vermieden, schwere, beleg, quelle, erkannt_am, bestaetigt_durch) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (id, art, ausloeser_muster, was_passiert, wie_erkannt, wie_vermieden,
         schwere, beleg, quelle, erkannt_am or now_iso(), bestaetigt_durch),
    )
    con.commit()


# ── Pruefen: DIE Schnittstelle, die andere Werkzeuge importieren ──────────

def pruefen(taetigkeit: str, *, conn: Optional[sqlite3.Connection] = None,
            limit: int = 10) -> list[dict]:
    """Mechanisches Matching, keine Semantik. `taetigkeit` ist ein beliebiger
    Text, der die aktuelle Aktivitaet beschreibt -- ein Bash-Befehl, ein
    SQL-Fragment, ein Dateipfad, ein Stueck Quellcode, was auch immer die
    aufrufende Stelle gerade anfasst. Jede Zeile der `fehler`-Tabelle wird
    per re.search (IGNORECASE) gegen `ausloeser_muster` geprueft; Treffer
    kommen zurueck, sortiert schwere (hoch>mittel>niedrig) dann id.

    Ein ungueltiges gespeichertes Muster wird uebersprungen, nicht geworfen
    -- ein kaputter Ausloeser darf nie den Aufrufer zum Absturz bringen.
    """
    own = conn is None
    c = conn or connect_db()
    try:
        rows = c.execute(
            "SELECT id, art, ausloeser_muster, was_passiert, wie_vermieden, "
            "schwere, beleg FROM fehler"
        ).fetchall()
    finally:
        if own:
            c.close()

    rang = {"hoch": 0, "mittel": 1, "niedrig": 2}
    treffer = []
    for (fid, art, muster, was_passiert, wie_vermieden, schwere, beleg) in rows:
        try:
            if re.search(muster, taetigkeit, re.IGNORECASE):
                treffer.append({
                    "id": fid, "art": art, "was_passiert": was_passiert,
                    "wie_vermieden": wie_vermieden, "schwere": schwere,
                    "beleg": beleg,
                })
        except re.error:
            continue  # kaputtes Muster: ueberspringen, nicht werfen
    treffer.sort(key=lambda t: (rang.get(t["schwere"], 9), t["id"]))
    return treffer[:limit]


# ── Auflistung ───────────────────────────────────────────────────────────

def stand(con: sqlite3.Connection) -> None:
    print("-- nach art --")
    for row in con.execute("SELECT art, COUNT(*) FROM fehler GROUP BY art ORDER BY art"):
        print(f"  {row[0]:12s} {row[1]}")
    print("-- nach schwere --")
    for row in con.execute("SELECT schwere, COUNT(*) FROM fehler GROUP BY schwere ORDER BY schwere"):
        print(f"  {row[0]:8s} {row[1]}")
    total = con.execute("SELECT COUNT(*) FROM fehler").fetchone()[0]
    ohne_beleg = con.execute(
        "SELECT COUNT(*) FROM fehler WHERE beleg IS NULL OR trim(beleg)=''"
    ).fetchone()[0]
    print(f"gesamt: {total}, ohne Beleg (sollte immer 0 sein): {ohne_beleg}")


def zu(con: sqlite3.Connection, art: str) -> None:
    rows = con.execute(
        "SELECT id, schwere, erkannt_am, was_passiert FROM fehler WHERE art=? ORDER BY id",
        (art,),
    ).fetchall()
    for r in rows:
        print(f"[{r[1]:8s}] {r[2]}  {r[0]}")
        print(f"    {r[3]}")
    print(f"({len(rows)} Zeilen fuer art='{art}')")


# ── Startbelegung: geerntet aus bau/protokoll.jsonl, bau/MESSFEHLER.md,   ─
#    var/lib/clay/CLAUDE.md und dem Owner-Auftrag selbst. Jede Zeile     ─
#    einzeln gepruefte Herkunft, siehe `quelle`/`beleg` je Eintrag.       ─

SEED_ROWS = [
    dict(
        id="insert-or-replace-feste-spalten", art="sql",
        ausloeser_muster=r"INSERT\s+OR\s+REPLACE\s+INTO\s+\w+\s*\(",
        was_passiert=(
            "INSERT OR REPLACE mit fester Spaltenliste loescht die Zeile und legt "
            "sie neu an; jede NICHT genannte Spalte faellt auf ihren DEFAULT-Wert "
            "zurueck. In wiki.py cmd_bauen fehlte die Spalte 'herkunft' -- jede von "
            "Hand gesetzte Bearbeitung (Titel, Sphaere, Projekt) waere beim naechsten "
            "automatischen Bauen-Lauf spurlos ueberschrieben worden."
        ),
        wie_erkannt=(
            "In isolierter Testdatenbank mit der echten DDL nachgestellt: Titel von "
            "Hand gesetzt, herkunft=nutzer gesetzt, ein voller bauen()-Lauf "
            "ausgefuehrt -- danach stand herkunft wieder auf 'gemessen' und der "
            "Titel auf dem Quellwert. Zwillingsfehler bei projekt/projekt_art/"
            "sphaere vom selben Agenten selbst gefunden."
        ),
        wie_vermieden=(
            "INSERT OR REPLACE nie mit fester Spaltenliste gegen eine Tabelle mit "
            "von Hand gepflegten Feldern verwenden. Entweder UPDATE mit expliziten "
            "SET-Klauseln, oder vor dem Neuaufbau einen Schnappschuss der "
            "Hand-Felder ziehen und danach ueber eine aus echten Spalten gebaute "
            "Weissliste zurueckspielen (reapply_owner_edits-Muster)."
        ),
        schwere="hoch",
        beleg="bau/protokoll.jsonl Zeile 47 (B13, 'Schwerer Fehler behoben und "
              "bewiesen'); wiki.py cmd_bauen ~Zeile 1148",
        quelle=(
            "Fehlerursprung: Agent 'wiki' (schrieb cmd_bauen). Gefunden von: Agent "
            "'kommentar' beim Bau der Nutzerebene (B13), vor Inbetriebnahme."
        ),
        erkannt_am="2026-08-14T20:37:53+0000",
        bestaetigt_durch="isolierte Testdatenbank, 2. Lauf nach Fix: 5 Felder "
                         "ueberleben unveraendert",
    ),
    dict(
        id="regex-wortgrenze-nach-symbol", art="python",
        ausloeser_muster=r"(?:%[^\n]{0,30}\\b|\\b[^\n]{0,30}%)",
        was_passiert=(
            "\\b verlangt einen Wort/Nicht-Wort-Uebergang. Ein Symbol wie % hat "
            "keinen -- jede Prozentangabe wurde dadurch STILL aus der Extraktion "
            "verschluckt. 11 von den gefundenen Zeilen betroffen, der groesste "
            "einzelne Fehler-Eimer der ganzen Session."
        ),
        wie_erkannt=(
            "messung.py: Abgleich ALLER im Rohtext gefundenen Zahlen gegen ALLE "
            "tatsaechlich in die Datenbank geschriebenen Zahlen, VOR dem ersten "
            "INSERT. Die Differenz zeigte exakt die 11 Prozent-Zeilen."
        ),
        wie_vermieden=(
            "Bei Einheiten, die auch als Symbol vorkommen (%, $, /), \\b NICHT "
            "verwenden -- stattdessen explizite Alternation der erlaubten Vor-/"
            "Nachzeichen (Leerzeichen, Satzzeichen, Zeilenanfang/-ende) oder ein "
            "Lookaround ohne \\b."
        ),
        schwere="mittel",
        beleg="bau/protokoll.jsonl Zeile 42 (B27, 'Messungen werden live verdichtet')",
        quelle=(
            "Agent 'messung' -- selbst gefunden, vor dem ersten Schreiben in die "
            "Datenbank, durch Gegenpruefung des eigenen Ergebnisses."
        ),
        erkannt_am="2026-08-14T20:01:46+0000",
        bestaetigt_durch="Abgleich gefundene vs. getroffene Zahlen vor jedem "
                         "produktiven Lauf",
    ),
    dict(
        id="fts5-join-falsche-content-tabelle", art="sql",
        ausloeser_muster=r"fts_\w+.*\.rowid|\.rowid.*fts_\w+",
        was_passiert=(
            "FTS5-External-Content-Join gegen artikel.rowid statt gegen die echte "
            "Content-Tabelle (artikel_suchtext.id) laeuft durch, meldet aber STILL "
            "0 Treffer -- kein Fehler, keine Exception, nur ein leeres Ergebnis."
        ),
        wie_erkannt=(
            "Eigenes Messwerkzeug lieferte 0 Treffer fuer FTS und Vollabruf; vor "
            "dem Melden als eigener Fehler erkannt und auf artikel_suchtext "
            "umgestellt."
        ),
        wie_vermieden=(
            "Vor jedem Join gegen eine fts_*-Tabelle die echte content=-Referenz "
            "aus der CREATE VIRTUAL TABLE-Anweisung nachsehen (sqlite_master), nie "
            "das naheliegende *.rowid der Basistabelle annehmen."
        ),
        schwere="mittel",
        beleg="bau/protokoll.jsonl Zeile 48 (B27, 'Messung: unbefangene Sitzung "
              "ohne Mechanismus')",
        quelle=(
            "Agent 'messung' -- woertlich 'MEIN EIGENES MESSGERAET WAR ZUERST "
            "KAPUTT', als eigener Fehler benannt, Regel 8 in eigener Sache."
        ),
        erkannt_am="2026-08-14T20:34:01+0000",
        bestaetigt_durch="zweiter Lauf nach Fix lieferte 95 (FTS) bzw. 472 (voll) "
                         "belegte Fakten statt 0",
    ),
    dict(
        id="verschachtelte-anfuehrung-ssh", art="shell",
        ausloeser_muster=r"'[^']*\bssh\b[^']*'",
        was_passiert=(
            "Ein Doppelsprung-SSH-Befehl haengt den inneren ssh-Aufruf als EINEN "
            "einfach gequoteten String an. Enthaelt der eingebettete Remote-Befehl "
            "selbst ein einfaches Anfuehrungszeichen (z.B. SQL mit LIKE "
            "'%...%'), terminiert das aeussere Quoting vorzeitig -- der Rest wird "
            "als eigener Shell-Befehl interpretiert."
        ),
        wie_erkannt=(
            "Strukturell im Code gefunden (werkzeug/weg.py:170 und :289-292 bauen "
            "genau dieses Muster); als generelles Risiko benannt, bevor es an "
            "einem echten Befehl auftrat."
        ),
        wie_vermieden=(
            "Keine von Hand verschachtelten Shell-Quotes ueber mehrere "
            "ssh-Sprungebenen. Gebundene Parameter (subprocess-Listen, nie "
            "f-String-Konkatenation) verwenden, oder eine Datei uebertragen und "
            "entfernt ausfuehren statt einen String zu verschachteln."
        ),
        schwere="mittel",
        beleg="werkzeug/weg.py Zeilen 170 und 289-292 (Code-Fundstelle); "
              "Beschreibung durch den Koordinator, 2026-08-15",
        quelle=(
            "Koordinator -- als generisches Risiko benannt. Im Bauprotokoll bisher "
            "KEINE dokumentierte tatsaechliche Fehlausloesung, nur die anfaellige "
            "Codestelle -- ehrlich als Verdacht, nicht als bewiesenen Vorfall "
            "gefuehrt."
        ),
        erkannt_am="2026-08-15",
        bestaetigt_durch="NICHT unabhaengig durch einen aufgetretenen Vorfall "
                         "bestaetigt -- nur durch Code-Lesen.",
    ),
    dict(
        id="mtime-als-herkunftsdatum", art="provenienz",
        ausloeser_muster=r"st_mtime|getmtime|--depth[= ]1|shallow.?clone|depth[= ]1",
        was_passiert=(
            "Dateisystem-mtime in einem geklonten Baum zeigt die KLON-Zeit, nicht "
            "die Arbeits-/Entstehungszeit. Ebenso zeigt `git log` bei einem "
            "Flachklon (--depth 1) nur die IMPORT-Zeit, nicht die echte "
            "Commit-Historie -- beide Werte sehen gueltig aus, sind es aber nicht."
        ),
        wie_erkannt=(
            "provenienz_reparieren gegen echte (nicht flache) Klone bewusst "
            "geprueft: 9209 von 9209 Zeilen aufgeloest, ausdruecklich 0 "
            "Ruecksfaelle auf das Importdatum gemessen und als Erfolgskriterium "
            "gefuehrt."
        ),
        wie_vermieden=(
            "Fuer Provenienz IMMER `git log --follow` gegen einen VOLLEN Klon "
            "(kein --depth) verwenden, nie mtime. Ist nur ein Flachklon "
            "verfuegbar, Provenienz explizit als 'unbekannt' eintragen, nie als "
            "geratenes Datum."
        ),
        schwere="mittel",
        beleg="bau/protokoll.jsonl Zeile 41 (B27, 'Provenienz aus echter "
              "Historie')",
        quelle=(
            "Agent 'wiki' -- eigene korrigierte Erwartung ('MEINE ERWARTUNG WAR "
            "FALSCH'), als Erfolgskriterium mitgefuehrt statt nur erwaehnt."
        ),
        erkannt_am="2026-08-14T20:00:00+0000",
        bestaetigt_durch="9209/9209 aufgeloest, 0 Ruecksfaelle auf Importdatum, "
                         "gegen 21 Repo-Namen stichprobengeprueft",
    ),
    dict(
        id="erfundene-eigene-metrik", art="methode",
        ausloeser_muster=r"^\s*\w*(SCHWELLE|THRESHOLD|GEWICHT|WEIGHT)\s*=\s*[\d.]+",
        was_passiert=(
            "Jede Kennzahl, die von der Partei erfunden wird, die daran gemessen "
            "wird, ist keine Kennzahl mehr, sondern ein verschobener Massstab -- "
            "unabhaengig von Absicht. Regel 8: wer misst und das Messgeraet baut, "
            "kann eine Verbesserung nicht mehr von einer Veraenderung des "
            "Massstabs unterscheiden."
        ),
        wie_erkannt=(
            "eichung.py: Eichnormale liegen root-only, fuer die messende Instanz "
            "nur lesend. verdacht fing beim ersten echten Einsatz den Bauenden "
            "selbst -- ein geaenderter Normal-Befehl kippte False auf True und "
            "wurde als 'ungeklaert' statt als Fortschritt gefuehrt."
        ),
        wie_vermieden=(
            "Neue Schwellen-/Gewichtskonstanten IMMER gegen ein externes, fuer die "
            "messende Instanz nicht schreibbares Normal fuehren "
            "(eichung.py-Muster). Ohne externen Bezug: als Vorschlag an einen "
            "Menschen, nicht als eigene Entscheidung einfuehren."
        ),
        schwere="hoch",
        beleg="var/lib/clay/CLAUDE.md Abschnitt 8 ('Pruefe den Massstab, nicht "
              "nur die Messung'); bau/protokoll.jsonl Zeilen 26/28 (Eichnormale)",
        quelle=(
            "Koordinator/System -- Hausregel 8, direkt aus Gabriels Vorgabe; am "
            "15.08. am eigenen Bau bestaetigt (verdacht fing den Bauenden selbst)."
        ),
        erkannt_am="2026-08-14T18:03:11+0000",
        bestaetigt_durch="verdacht-Lauf: 5/6 bzw. 13/14 belegt, 1 ungeklaert "
                         "korrekt nicht als bestanden gerundet",
    ),
    dict(
        id="geteilte-claude-md-kopien", art="daten",
        ausloeser_muster=r"CLAUDE\.md",
        was_passiert=(
            "/opt/clayverse/CLAUDE.md (Repo) und /var/lib/clay/CLAUDE.md (laufende "
            "Sitzung) sind zwei Dateien, keine eine. Sie liefen auseinander: "
            "Regel 8 stand NUR im Repo und erreichte die laufende Sitzung nie."
        ),
        wie_erkannt=(
            "md5sum beider Pfade verglichen -- verschieden. Nach dem Fix: "
            "identisch, 1 gemeinsame Pruefsumme."
        ),
        wie_vermieden=(
            "Bei jeder Aenderung an CLAUDE.md sofort "
            "`md5sum /opt/clayverse/CLAUDE.md /var/lib/clay/CLAUDE.md` "
            "gegenpruefen, oder besser: ein Symlink statt zweier Kopien (im "
            "Protokoll selbst als sauberere Loesung benannt, aber noch offen)."
        ),
        schwere="hoch",
        beleg="bau/protokoll.jsonl Zeile 32 (B5, 'CLAUDE.md: geteilte Wahrheit "
              "zusammengefuehrt')",
        quelle=(
            "Agent 'kern' -- gefunden waehrend der ersten echten Kern-Sitzung, die "
            "die eigene Ausstattung selbst befragte."
        ),
        erkannt_am="2026-08-14T18:53:40+0000",
        bestaetigt_durch="md5sum beider Dateien identisch nach dem Fix; "
                         "git-Commit 64ba736 auf master",
    ),
    dict(
        id="repo-nicht-auf-github", art="daten",
        ausloeser_muster=r"git\s+init\s+--bare|/srv/git/\w[\w.-]*\.git",
        was_passiert=(
            "baeume.py zieht das Gehirn AUSSCHLIESSLICH aus GitHub. Ein Repo, das "
            "nur als Bare-Repo unter /srv/git liegt (das bestehende "
            "Vier-Repo-Muster), erreicht das Gehirn NIE -- und nichts meldet das "
            "als Luecke."
        ),
        wie_erkannt=(
            "Vom Auftraggeber (Gabriel) direkt bemerkt: zwei neue Repos (microclay, "
            "unifieddb) waren nur als Bare-Repos angelegt worden, dem alten Muster "
            "folgend, ohne GitHub-Kopie."
        ),
        wie_vermieden=(
            "Jedes neue Repo, das ins Gehirn soll, IMMER auch per GitHub-API "
            "anlegen und pushen -- nie nur als Bare-Repo unter /srv/git. "
            "baeume.py holen danach laufen lassen und die neue Kennung in der "
            "Ausgabe bestaetigen."
        ),
        schwere="hoch",
        beleg="bau/protokoll.jsonl Zeile 57 (B3, 'Beide neuen Repos auf GitHub "
              "und im Gehirn')",
        quelle=(
            "Koordinator -- woertlich 'MEIN VERSAEUMNIS, vom Auftraggeber "
            "bemerkt'. Eigener Fehler, von Gabriel gefunden, nicht selbst."
        ),
        erkannt_am="2026-08-14T21:21:13+0000",
        bestaetigt_durch="GitHub-API-Antwort je Repo (HTTP 201), baeume.py holen "
                         "zeigte beide danach als aktualisiert",
    ),
    dict(
        id="freitext-feld-sieht-aus-wie-referenz", art="daten",
        ausloeser_muster=r"\b(falsifier|counterhypothesis|claim)\b\s*[:=]",
        was_passiert=(
            "Freitextfelder wie falsifier (1225 Vorkommen), claim (810), "
            "counterhypothesis (295) sehen wie Verweise aus, sind aber zu 0 "
            "Prozent aufloesbar -- reine Prosa. Kanten aus ihnen zu bauen haette "
            "einen dicht verknuepft aussehenden, aber komplett erfundenen "
            "Graphen erzeugt."
        ),
        wie_erkannt=(
            "Jedes Feld der Hypothesenaufzeichnungen EINZELN auf "
            "Aufloesungsquote geprueft, bevor eine einzige Kante daraus gebaut "
            "wurde. Nur parent, packet_id, run_id trugen echte Verweise."
        ),
        wie_vermieden=(
            "Vor dem Bau von Kanten aus einem Feld IMMER zuerst die "
            "Aufloesungsquote gegen den echten Bestand messen (Stichprobe: wie "
            "viele Werte treffen auf eine existierende ID?). Unter einer "
            "sinnvollen Schwelle: Feld bleibt Text, keine Kante."
        ),
        schwere="mittel",
        beleg="bau/protokoll.jsonl Zeile 59 (B6, 'Kanten gebaut - Waisen 93 auf "
              "4 Prozent')",
        quelle="Agent 'kanten' -- eigenstaendig gepruefter Nebenbefund, nicht vom "
               "Auftrag verlangt.",
        erkannt_am="2026-08-14T21:42:26+0000",
        bestaetigt_durch="Aufloesungsquote gemessen: falsifier/claim/"
                         "counterhypothesis/family/cluster/support/evidence = "
                         "0% aufloesbar",
    ),
    dict(
        id="index-nur-ein-wirt", art="daten",
        ausloeser_muster=r"group\s+by\s+wirt|SELECT\s+wirt\s*,\s*COUNT",
        was_passiert=(
            "Ein Index/eine Kartographie, die nur EINEN Wirt kennt, beantwortet "
            "Fragen ueber andere Maschinen nicht -- und nichts meldet die Luecke "
            "von selbst. 92.715 Fundorte, alle auf 'clayverse', 0 auf den beiden "
            "Arbeitsrechnern."
        ),
        wie_erkannt=(
            "An einer echten Frage aufgedeckt (wo liegen die Needle-Gewichte); "
            "`select wirt, count(*) from fundort group by wirt` zeigte genau "
            "einen Wirt."
        ),
        wie_vermieden=(
            "Bei jedem Index/Inventar mit einer Wirt-/Host-Spalte routinemaessig "
            "`GROUP BY wirt` gegenpruefen: mehr als 1 verschiedener Wert? "
            "Erwartungswert (alle bekannten, per wirte.py ermittelten Wirte) "
            "explizit gegenrechnen, nicht nur zaehlen."
        ),
        schwere="mittel",
        beleg="bau/protokoll.jsonl Zeile 51 (B6, 'Abdeckungsluecke: das Gehirn "
              "kennt nur den Server')",
        quelle="Agent 'suche' -- aufgedeckt durch eine echte Frage des "
               "Auftraggebers, nicht durch Routine-Pruefung.",
        erkannt_am="2026-08-14T20:43:31+0000",
        bestaetigt_durch="nach Fix: 3 Wirte messbar (ai-core-node 356.983, "
                         "clayverse 92.715, andreas-MACO 9.239 Fundorte)",
    ),
    dict(
        id="ausschluss-per-name-statt-marker", art="python",
        ausloeser_muster=r"['\"]venv['\"]\s*(?:==|in|,)|name\s*==\s*['\"]venv['\"]",
        was_passiert=(
            "Eine Ausschlussregel, die nach dem NAMEN 'venv' sucht, uebersieht "
            "anders benannte virtuelle Umgebungen (v7-training-venv, Forge/venv) "
            "-- rund 43 GB waeren so uebersehen worden."
        ),
        wie_erkannt=(
            "Umstellung auf die Markierungsdatei pyvenv.cfg (die JEDE venv "
            "unabhaengig vom Namen traegt) fand alle Umgebungen; Ausschlusszahlen "
            "vollstaendig gegengezaehlt und gemeldet statt still geglaettet "
            "(venv 328.338 Dateien / 43,16 GB)."
        ),
        wie_vermieden=(
            "Aus-/Einschlussregeln fuer eine Objektklasse IMMER ueber eine "
            "Markierungsdatei/ein strukturelles Merkmal der Klasse fuehren, nie "
            "ueber den ueblichen Namen. Bei venv: pyvenv.cfg. Analog fuer andere "
            "Klassen die jeweilige Markerdatei suchen, nicht raten."
        ),
        schwere="mittel",
        beleg="bau/protokoll.jsonl Zeile 61 (B6, 'Beide Arbeitsrechner "
              "indiziert')",
        quelle="Agent 'suche' -- als eigener frueherer Ansatz explizit benannt "
               "und korrigiert, bevor der produktive Lauf stattfand.",
        erkannt_am="2026-08-14T22:03:13+0000",
        bestaetigt_durch="Ausschluesse vollstaendig gegengezaehlt (venv 43,16 GB, "
                         ".cache 85,07 GB, snap 142,66 GB) statt geschaetzt",
    ),
    dict(
        id="oswalk-uebergeht-lose-dateien", art="python",
        ausloeser_muster=r"os\.walk\(",
        was_passiert=(
            "os.walk() erwartet ein Verzeichnis. Steht in einer Scope-Liste ein "
            "Pfad, der eine DATEI ist (kein Verzeichnis), liefert os.walk() dafuer "
            "STILL nichts -- kein Fehler, keine Warnung, der Eintrag wird einfach "
            "uebersprungen. Heimatverzeichnisse haben aber dutzende loser "
            "Dateien direkt obenauf."
        ),
        wie_erkannt=(
            "werkzeug/suche.py: SCOPE ist eine Liste von Path-Objekten, "
            "os.walk(wurzel) laeuft ueber jeden Eintrag einzeln (Zeilen 67, "
            "327-330) -- ein Datei-Eintrag in SCOPE wuerde dort lautlos leer "
            "bleiben. Zusaetzlich vom Koordinator berichtet: ein echter Lauf "
            "uebersah so Dateien in einem Heimatverzeichnis."
        ),
        wie_vermieden=(
            "Vor jedem os.walk(pfad) in einer Schleife ueber eine Pfad-Liste: "
            "erst `if pfad.is_file(): <eigene Behandlung>; continue`, danach erst "
            "os.walk fuer Verzeichnisse. Nie annehmen, dass ein Scope-Eintrag ein "
            "Verzeichnis ist."
        ),
        schwere="mittel",
        beleg="werkzeug/suche.py Zeilen 67, 327-330 (Code-Fund, unabhaengig "
              "verifiziert); Koordinator-Bericht 2026-08-15 zu einem echten Lauf",
        quelle=(
            "Koordinator-Bericht 2026-08-15 (waehrend Ausfall dieser "
            "fehler.py-Instanz von anderer Arbeit gemeldet); die Codestelle "
            "selbst unabhaengig im Bestand gefunden und bestaetigt."
        ),
        erkannt_am="2026-08-15",
        bestaetigt_durch="Codestelle unabhaengig verifiziert (suche.py); der "
                         "beschriebene konkrete Lauf liegt ausserhalb des "
                         "einsehbaren Protokolls.",
    ),
    dict(
        id="stiller-tod-hintergrundlauf", art="methode",
        ausloeser_muster=r"\bnohup\b|&\s*$|run_in_background|\bdisown\b",
        was_passiert=(
            "Ein Hintergrundlauf/Agent stirbt (API-Fehler wie HTTP 500, "
            "Netzwerkabbruch, OOM, kill) und NIEMAND wird benachrichtigt. Der "
            "Aufrufer wartet ewig oder geht davon aus, dass alles laeuft. "
            "Ergebnis: stille Nichtzustellung -- kein Alarm, kein Retry, kein "
            "Luecken-Bericht, das System sieht ruhig aus. Am 15.08. ZWEIMAL "
            "gemessen: ein Indexier-Agent starb mitten in einer Reparatur an "
            "einem API-Fehler (von Hand fortgesetzt), und diese "
            "fehler.py-Instanz selbst starb an einem serverseitigen 500 (von "
            "Hand fortgesetzt) -- beide Male nur bemerkt, weil ein Koordinator "
            "Benachrichtigungen las. Verwandter Einzelfall: ein "
            "Hintergrundlauf, der sich von seiner Ausgabedatei loeste -- die "
            "leere Datei sah wie ein sauberer Abschluss aus, war aber "
            "abgerissen; erst /proc/<pid>/io unterschied die beiden Faelle."
        ),
        wie_erkannt=(
            "Beide Hauptvorfaelle ausschliesslich durch einen Menschen/"
            "Koordinator, der Benachrichtigungen las -- kein automatischer "
            "Alarm, kein Retry, keine Luecken-Meldung."
        ),
        wie_vermieden=(
            "PRIOR ART, nicht neu erfunden (Regel 4): tavern-wache.service + "
            "swarm/ablauf/wache auf Gabriels Rechner loesen genau das, seit "
            "vor diesem Tag. Ein Timer alle 5 Minuten prueft JEDE Instanz auf "
            "ZWEI GETRENNTE Arten: (1) TOD -- Prozess-PID existiert nicht mehr "
            "unter /proc/<pid> und kein legitimes Abschieds-Signal (STAND/"
            "UEBERGABE/ABSCHIED) wurde gesetzt; (2) STILLES STEHEN -- die "
            "Fortschrittsdatei (Transkript) hat sich laenger als eine Schwelle "
            "(Standard 20 min) nicht mehr veraendert, ebenfalls ohne "
            "Abschieds-Signal. Beide Funde werden append-only protokolliert "
            "(wache.tsv); TOD zusaetzlich sofort auf die geteilte Tafel "
            "gemeldet, STILLES STEHEN bewusst NICHT automatisch eskaliert "
            "(Fuehrungsentscheidung, kein Automatenlaerm), aber mit fertigem "
            "Wiederaufnahme-Kommando vorgelegt. Uebertragbares Muster fuer "
            "ClayVerse: ein Watchdog auf einem Timer prueft Liveness UND "
            "Fortschritt GETRENNT, meldet append-only, und die Arbeit selbst "
            "muss idempotent/wiederaufnehmbar sein, damit ein Neustart weder "
            "doppelt noch beschaedigt. Ein Tod muss einen EINTRAG erzeugen, "
            "keine Stille."
        ),
        schwere="hoch",
        beleg=(
            "Koordinator-Bericht 2026-08-15 (zwei Vorfaelle: Indexier-Agent an "
            "API-Fehler, diese fehler.py-Instanz an HTTP 500); Vorbild-Quelltext "
            "gelesen: /home/ai-core-node/.config/systemd/user/tavern-wache."
            "{service,timer} + /home/ai-core-node/swarm/ablauf/wache "
            "(Zeilen 52-121)"
        ),
        quelle=(
            "Koordinator (beide Vorfaelle direkt beobachtet, keine "
            "Sekundaerquelle). Der Loesungsansatz ist NICHT neu erfunden, "
            "sondern aus dem tAvern-System (F5, Gabriel) uebernommen -- vor "
            "dem Bau geprueft, nicht nachgebaut (Regel 4)."
        ),
        erkannt_am="2026-08-15",
        bestaetigt_durch=(
            "Prior-Art-Quelltext gelesen und Funktionsweise gegen die "
            "Beschreibung geprueft (Tod: /proc/<pid>-Existenz plus fehlendes "
            "Abschieds-Signal; Stilles Stehen: Transkript-mtime-Schwelle 20 "
            "min, Dedup 30 min, Tafel nur bei Tod). Fuer ClayVerse selbst "
            "NICHT gebaut -- eine eigene Watchdog-Komponente liegt ausserhalb "
            "der Zustaendigkeit von fehler.py (das hier ist ein "
            "Text-Muster-Werkzeug, kein Prozess-/Zeitwaechter); hier nur als "
            "Lehre + Fundstelle hinterlegt."
        ),
    ),
    dict(
        id="stilles-stehen-leeres-schreibziel", art="daten",
        ausloeser_muster=r"0\s*Zeilen.{0,20}(?:gebaut|verdrahtet|angebunden|"
                          r"eingehaengt)|(?:gebaut|verdrahtet|angebunden|"
                          r"eingehaengt).{0,20}0\s*Zeilen",
        was_passiert=(
            "Die haertere Haelfte von 'stiller Tod': ein Schreibpfad ist "
            "gebaut, verdrahtet und eingehaengt -- der Prozess LEBT, meldet "
            "nichts Falsches -- aber seine Zieltabelle bleibt leer, weil ihn "
            "niemand tatsaechlich aufruft. vp_edge_lern (Lernmechanik fuer "
            "Kantengewichte): gebaut, verdrahtet, 0 Zeilen. titan "
            "rwl_feedback: Schreibpfad verdrahtet, 0 Zeilen, kein Pruefpunkt "
            "irgendwo auf der Platte. Beide sahen beim Betrachten des Codes "
            "fertig aus."
        ),
        wie_erkannt=(
            "Nur durch EXPLIZITES Nachzaehlen der Zielzeilen gefunden "
            "('Organe vermessen', B9) -- nicht durch irgendeinen Fehlerpfad, "
            "weil keiner ausgeloest wurde. Ohne die gezielte Nachfrage waere "
            "die Luecke unsichtbar geblieben."
        ),
        wie_vermieden=(
            "Fuer jeden neu verdrahteten Schreibpfad: nicht nur 'gebaut und "
            "eingehaengt' als Fertigmeldung akzeptieren, sondern den "
            "Zeilenstand der Zieltabelle in die Abnahme aufnehmen UND nach "
            "einer angemessenen Frist erneut pruefen (analog Eichnormale, "
            "woechentlich). Eine Tabelle, die laenger als eine Schwelle leer "
            "bleibt, obwohl ihr Schreiber als 'aktiv' gilt, ist strukturell "
            "derselbe Befund wie ein 'stilles Stehen' bei einer Instanz "
            "(siehe tavern-wache) -- nur dass hier das Schreibziel misst statt "
            "die Transkript-mtime. Ein eigenstaendiger periodischer Zaehler "
            "(kein Text-Trigger) waere die technisch richtige Loesung; dieses "
            "fehler.py-Werkzeug kann das nur ALS LEHRE vorlegen, wenn ein "
            "Baubericht selbst schon '0 Zeilen' neben 'gebaut/verdrahtet' "
            "nennt -- es ersetzt keinen echten periodischen Zaehler."
        ),
        schwere="hoch",
        beleg=(
            "bau/protokoll.jsonl Zeile 54 (B9, 'Organe vermessen - fast "
            "nichts davon ist neural': vp_edge_lern und rwl_feedback); "
            "Koordinator-Einordnung 2026-08-15 nach tavern-wache-Vorbild"
        ),
        quelle=(
            "Agent 'forschung' fand beide Faelle beim Vermessen der Organe "
            "(B9); Koordinator ordnete sie am 15.08. explizit als dieselbe "
            "Fehlerklasse wie 'stiller Tod' ein, nur eine Stufe hoeher (der "
            "Schreiber lebt, das Ziel nicht)."
        ),
        erkannt_am="2026-08-15",
        bestaetigt_durch=(
            "0 Zeilen fuer beide Tabellen direkt per Abfrage bestaetigt "
            "(vp_edge_lern, titan rwl_feedback). Dies ist eine von zwei "
            "Zeilen im Bestand, deren Ausloeser bewusst KEINE echte "
            "Liveness-/Zeilenzahl-Pruefung ist, sondern nur ein Text-Hinweis "
            "auf Berichte, die das Symptom selbst schon benennen -- ehrlich "
            "als Grenze des Werkzeugs dokumentiert, nicht verschwiegen."
        ),
    ),
    dict(
        id="gh-repo-privat-sterne-verlust", art="shell",
        ausloeser_muster=r"gh\s+repo\s+edit\s+.*--visibility\s+private",
        was_passiert=(
            "Ein GitHub-Repo auf privat schalten loescht die Sterne und Forks "
            "ENDGUELTIG -- GitHub blendet sie nicht nur aus, die "
            "Stargazer-Liste liefert danach 0. Zurueckschalten auf oeffentlich "
            "bringt sie NICHT zurueck."
        ),
        wie_erkannt=(
            "lcme: 15 Sterne, 4 Forks vor dem Umschalten. Nach Ruecknahme auf "
            "oeffentlich: Stargazer-API liefert weiterhin 0. Verlust bestaetigt, "
            "nicht nur vermutet."
        ),
        wie_vermieden=(
            "Vor JEDEM Umschalten eines Repos auf privat: Sterne-/Fork-Zahl "
            "vorher festhalten und wissen, dass dies eine EINWEG-Handlung ist. "
            "Ein Repo mit Sternen/Forks, die erhalten bleiben sollen, nicht "
            "privat schalten -- oder den Verlust vorher explizit als hinnehmbar "
            "bestaetigen."
        ),
        schwere="hoch",
        beleg="bau/MESSFEHLER.md Abschnitt A2; bau/protokoll.jsonl Zeile 20 (B3, "
              "'lcme wieder oeffentlich - Sterne sind verloren')",
        quelle=(
            "Koordinator -- als eigene falsche Erinnerung dokumentiert ('Die "
            "Sterne kommen beim Zurueckschalten wieder' war die Annahme, GitHub "
            "loescht sie tatsaechlich)."
        ),
        erkannt_am="2026-08-14T17:16:48+0000",
        bestaetigt_durch="Stargazer-API liefert 0 nach Ruecknahme, unabhaengig "
                         "von der Zaehlung geprueft",
    ),
    dict(
        id="sshd-drop-in-reihenfolge", art="shell",
        ausloeser_muster=r"sshd_config\.d/\d+-|conf\.d/\d\d-[\w.-]+\.conf",
        was_passiert=(
            "sshd wertet Drop-in-Dateien in sortierter Reihenfolge aus und der "
            "ERSTE Treffer je Einstellung gewinnt -- nicht der letzte. Eine neue "
            "Haertungsdatei '99-clayverse.conf' wurde von einer vorhandenen "
            "'50-cloud-init.conf' (die PasswordAuthentication yes setzte) "
            "einfach ignoriert; das Passwort blieb an, obwohl die neue Datei "
            "korrekt geschrieben war."
        ),
        wie_erkannt=(
            "`sshd -T` (die WIRKUNG, nicht die Datei) nach dem Schreiben "
            "abgefragt -- meldete weiterhin passwordauthentication yes trotz "
            "korrekt geschriebener Haertungsdatei."
        ),
        wie_vermieden=(
            "Bei jeder neuen Datei in einem sortierten Drop-in-Verzeichnis "
            "(sshd_config.d, viele conf.d-Muster): zuerst die vorhandenen "
            "Dateien auflisten, neue Datei so benennen, dass sie VOR den "
            "bestehenden mit widerspruechlichem Inhalt sortiert (niedrigere "
            "Nummer) -- und danach IMMER die Wirkung pruefen (`sshd -T`), nie "
            "nur den Schreibvorgang."
        ),
        schwere="hoch",
        beleg="bau/MESSFEHLER.md Abschnitt C1; bau/protokoll.jsonl Zeile 7 (B1, "
              "'SSH gehaertet auf beiden Maschinen')",
        quelle=(
            "Koordinator -- eigener Fehler beim Haerten, durch `sshd -T` "
            "(Wirkungspruefung, Regel 1) selbst gefunden und korrigiert."
        ),
        erkannt_am="2026-08-14T16:29:57+0000",
        bestaetigt_durch="sshd -T nach Umbenennung auf 01- meldet korrekt "
                         "passwordauthentication no",
    ),
    dict(
        id="nginx-t-warnung-ignoriert", art="shell",
        ausloeser_muster=r"nginx\s+-t\b",
        was_passiert=(
            "`nginx -t` mit Exit-Code 0 ('syntax is ok') wurde als vollstaendig "
            "bestanden gelesen, obwohl in derselben Ausgabe eine echte Warnung "
            "stand ('conflicting server name www.frank.ink'). Eine Warnung ist "
            "ein Befund, kein Rauschen -- wurde aber wie Rauschen behandelt."
        ),
        wie_erkannt=(
            "Warnzeile in der stderr-Ausgabe von nginx -t nachtraeglich als "
            "echter, wirkender Konfigurationsfehler erkannt, nicht als "
            "kosmetisch."
        ),
        wie_vermieden=(
            "Nach `nginx -t` NIE nur den Exit-Code pruefen -- die volle Ausgabe "
            "(stdout+stderr) nach 'conflict', 'warn', 'duplicate' durchsuchen. "
            "Jede Warnzeile einzeln bewerten, nie pauschal als unschaedlich "
            "einstufen."
        ),
        schwere="niedrig",
        beleg="bau/MESSFEHLER.md Abschnitt C2",
        quelle="Koordinator -- eigener Fehler (Konfiguration statt Wirkung "
               "gemessen, siehe Regel 1).",
        erkannt_am="2026-08-15",
        bestaetigt_durch="NICHT explizit im Protokoll als behoben vermerkt -- "
                         "nur in MESSFEHLER.md als Lehre festgehalten",
    ),
]


def ernten(con: sqlite3.Connection, verbose: bool = True) -> dict:
    inserted, already, rejected = 0, 0, []
    cur = con.cursor()
    for row in SEED_ROWS:
        try:
            re.compile(row["ausloeser_muster"])
        except re.error as e:
            rejected.append((row["id"], str(e)))
            continue
        cur.execute(
            "INSERT OR IGNORE INTO fehler (id, art, ausloeser_muster, "
            "was_passiert, wie_erkannt, wie_vermieden, schwere, beleg, quelle, "
            "erkannt_am, bestaetigt_durch) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (row["id"], row["art"], row["ausloeser_muster"], row["was_passiert"],
             row["wie_erkannt"], row["wie_vermieden"], row["schwere"],
             row["beleg"], row["quelle"], row.get("erkannt_am") or now_iso(),
             row.get("bestaetigt_durch")),
        )
        if cur.rowcount == 1:
            inserted += 1
        else:
            already += 1
    con.commit()
    if verbose:
        print(f"Startbelegung: {len(SEED_ROWS)} Zeilen definiert")
        print(f"neu eingefuegt: {inserted}, bereits vorhanden (idempotent): {already}")
        if rejected:
            print(f"VERWORFEN (ungueltiges Muster, nicht eingefuegt): {rejected}")
    return {"defined": len(SEED_ROWS), "inserted": inserted, "already": already,
            "rejected": rejected}


# ── Selbsttest: Beweis, dass echte Treffer treffen und ein sauberer      ─
#    Nicht-Treffer nichts zurueckgibt (ein Warner, der immer warnt, ist   ─
#    Rauschen -- Gabriels Bedingung).                                    ─

_SELBSTTEST_FAELLE = [
    ("INSERT OR REPLACE INTO artikel (id, titel, herkunft) VALUES (?,?,?)",
     "insert-or-replace-feste-spalten"),
    (r'EINHEIT_RE = re.compile(r"(\d+)\s*%\s*\b")', "regex-wortgrenze-nach-symbol"),
    ("SELECT a.id FROM fts_index_artikel f JOIN artikel a ON a.rowid = f.rowid",
     "fts5-join-falsche-content-tabelle"),
    ("ssh root@31.97.117.141 'ssh clay@100.71.48.1 \"echo test\"'",
     "verschachtelte-anfuehrung-ssh"),
    ("gh repo edit gschaidergabriel/microclay --visibility private",
     "gh-repo-privat-sterne-verlust"),
    ("python3 lang_lauf.py --input x --output out.jsonl > lauf.log 2>&1 &",
     "stiller-tod-hintergrundlauf"),
    ("vp_edge_lern EXISTIERT BEREITS in wiki.db, gebaut vom Vorprozessor-Agenten "
     "-- eingehaengt in den Live-Abrufpfad. 0 Zeilen - gebaut, verdrahtet, nie "
     "benutzt.", "stilles-stehen-leeres-schreibziel"),
]
_SELBSTTEST_LEER = ["git status", "ls -la /home/clay", "SELECT COUNT(*) FROM problem"]


def _selbsttest(con: sqlite3.Connection) -> bool:
    ok = True
    print("-- Treffertest (5 echte Aktivitaeten) --")
    for taetigkeit, erwartet_id in _SELBSTTEST_FAELLE:
        start = time.perf_counter_ns()
        treffer = pruefen(taetigkeit, conn=con)
        us = (time.perf_counter_ns() - start) // 1000
        ids = [t["id"] for t in treffer]
        passt = erwartet_id in ids
        ok = ok and passt
        print(f"  {'OK' if passt else 'FEHLT'}  ({us} us, {len(ids)} Treffer) "
              f"erwartet={erwartet_id}  gefunden={ids}  <- {taetigkeit[:70]!r}")
    print("-- Leertest (Aktivitaeten, die NICHTS treffen sollen) --")
    for taetigkeit in _SELBSTTEST_LEER:
        treffer = pruefen(taetigkeit, conn=con)
        passt = len(treffer) == 0
        ok = ok and passt
        print(f"  {'OK' if passt else 'FALSCH-POSITIV'}  {len(treffer)} Treffer "
              f"<- {taetigkeit!r}  {[t['id'] for t in treffer] if treffer else ''}")
    return ok


# ── CLI ──────────────────────────────────────────────────────────────────

def main() -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("ernten")
    sub.add_parser("stand")
    sub.add_parser("selbsttest")

    p_neu = sub.add_parser("neu")
    p_neu.add_argument("--id", required=True)
    p_neu.add_argument("--art", required=True, choices=ART_WERTE)
    p_neu.add_argument("--muster", required=True, dest="ausloeser_muster")
    p_neu.add_argument("--was-passiert", required=True, dest="was_passiert")
    p_neu.add_argument("--wie-erkannt", required=True, dest="wie_erkannt")
    p_neu.add_argument("--wie-vermieden", required=True, dest="wie_vermieden")
    p_neu.add_argument("--schwere", required=True, choices=SCHWERE_WERTE)
    p_neu.add_argument("--beleg", required=True)
    p_neu.add_argument("--quelle", required=True)
    p_neu.add_argument("--erkannt-am", default=None, dest="erkannt_am")
    p_neu.add_argument("--bestaetigt-durch", default=None, dest="bestaetigt_durch")

    p_pruefen = sub.add_parser("pruefen")
    p_pruefen.add_argument("--taetigkeit", required=True)

    p_zu = sub.add_parser("zu")
    p_zu.add_argument("art", choices=ART_WERTE)

    args = ap.parse_args()
    con = connect_db()
    ensure_schema(con)

    if args.cmd == "ernten":
        ernten(con)
    elif args.cmd == "stand":
        stand(con)
    elif args.cmd == "selbsttest":
        ok = _selbsttest(con)
        if not ok:
            con.close()
            return 1
    elif args.cmd == "neu":
        try:
            neu(con, id=args.id, art=args.art, ausloeser_muster=args.ausloeser_muster,
                was_passiert=args.was_passiert, wie_erkannt=args.wie_erkannt,
                wie_vermieden=args.wie_vermieden, schwere=args.schwere,
                beleg=args.beleg, quelle=args.quelle, erkannt_am=args.erkannt_am,
                bestaetigt_durch=args.bestaetigt_durch)
            print(f"fehler '{args.id}' angelegt.")
        except ValueError as e:
            print(str(e), file=sys.stderr)
            con.close()
            return 1
    elif args.cmd == "pruefen":
        treffer = pruefen(args.taetigkeit, conn=con)
        if not treffer:
            print("keine Treffer.")
        for t in treffer:
            print(f"[{t['schwere']:8s}] {t['id']}  ({t['art']})")
            print(f"    was: {t['was_passiert']}")
            print(f"    vermeiden: {t['wie_vermieden']}")
            print(f"    beleg: {t['beleg']}")
    elif args.cmd == "zu":
        zu(con, args.art)

    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())


# ── PROPOSAL_TOR_HOOK (Kommentar, kein Code-Eingriff -- siehe Auftrag:    ─
#    "propose, do not install") ───────────────────────────────────────── ─
#
# Vorschlag: tor_hook.py koennte VOR seiner Rueckgabe (main(), kurz vor
# `if u["urteil"].startswith("durch"): return 0`) einen Aufruf
#     treffer = fehler.pruefen(befehl, conn=<kurzlebige RO-Verbindung>)
# einfuegen und bei Treffern eine ZUSAETZLICHE, klar als Hinweis markierte
# Zeile nach stderr schreiben ("HINWEIS (fehler.py): ...") -- OHNE den
# Rueckgabewert zu aendern. Ein fehler-Treffer ist NIE ein Grund fuer
# exit 2; das wuerde die Bedeutung von exit 2 (Rechteeingriff/keine
# Ruecknahme) mit "sieht aus wie ein frueherer Fehler" vermischen -- zwei
# verschiedene Fragen, die im ganzen Bestand bisher bewusst getrennt
# gehalten wurden (tor.py entscheidet NUR ueber Reversibilitaet/Rechte).
#
# NICHT installiert, aus drei gemessenen/begruendeten Risiken:
#
# 1. LEISTUNG: tor_hook.py laeuft vor JEDEM Bash/Write/Edit jeder Sitzung,
#    als frischer Prozess (kein Dauerlauf, kein Cache zwischen Aufrufen).
#    Eine zusaetzliche SQLite-Verbindung gegen die (mehrere GB grosse,
#    von vier Agenten gleichzeitig beschriebene) wiki.db je Aufruf ist
#    nicht gratis -- andere Werkzeuge im Bestand melden 1-4 ms allein fuer
#    den WAL-Verbindungsaufbau unter gleichzeitigen Schreibern. Das Tor
#    selbst hat bisher keinen DB-Zugriff und ist dadurch besonders billig;
#    diese Eigenschaft ginge verloren.
#
# 2. RAUSCHEN: mehrere der 16 Startmuster sind bewusst breit (os.walk(,
#    nohup/&$, CLAUDE\.md, nginx -t) -- das ist im Kontext von `pruefen()`
#    als Kontext-Beipack fuer eine EXPLIZITE Abfrage gewollt (Regel:
#    lieber ein Treffer zu viel als ein blinder Fleck). Vor JEDEM
#    Bash-Aufruf ungefragt eingeblendet, wuerden dieselben Muster staendig
#    feuern (z. B. jede `ls`-Pipeline mit trailendem `&`) und das Tor
#    selbst zu Rauschen machen -- exakt das Gegenteil dessen, was Gabriel
#    verlangt hat ("ein Warner, der immer warnt, ist Rauschen").
#
# 3. ZUSTAENDIGKEIT: tor.py trifft GENAU EINE Entscheidung (durch /
#    bestaetigung / vorschlag), rein aus Reversibilitaet und Rechten. Der
#    ganze Bestand haelt Zustaendigkeiten bewusst auseinander (problem.py
#    schreibt nie in folgerung, eichung.py bleibt getrennt von tor.py
#    trotz aehnlicher "Wache"-Rolle). Eine zweite, andersartige Beurteilung
#    (Mustergleichheit mit einem fruehenren Fehler, keine
#    Rechte-/Reversibilitaetsfrage) in denselben Hook zu legen, verwischt
#    diese Trennung und macht spaetere Fehlbedienung wahrscheinlicher (z.B.
#    "einfach mitblocken lassen" als bequeme Abkuerzung).
#
# Wenn Gabriel den Einbau trotzdem will: als eigener, SEPARATER
# PostToolUse- oder Zusammenfassungs-Hook (nicht PreToolUse, nicht
# blockierend), der NACH getaner Arbeit einmal je Sitzungsabschnitt
# prueft statt vor jedem einzelnen Werkzeugaufruf -- das haelt Kosten und
# Zustaendigkeit getrennt vom Tor.
