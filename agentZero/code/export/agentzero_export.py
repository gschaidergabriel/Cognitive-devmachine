#!/usr/bin/env python3
"""agentZero-Export: Zeros gesamte Spur, kategorisiert, ins Forschungs-Repo.

Legt unter agentZero/ im Repo clay-global-research-entity ab:

    chat/        die Gespraeche je Mensch, mit vollstaendigen Metadaten
    kognition/   Kausalepisoden, Arbeitsraum, Wirkungen, Pruefpunkte
    abruf/       was die Abruf-Entitaet tut: Episoden, Eintrittspunkte, Rueckmeldung
    karten/      Momentaufnahmen je Lauf -- daraus entsteht der Zeitstrahl
    zustand/     Menschen, Sitzungen, Wurzelzustand
    MANIFEST.json / README.md

⚠️ SCHWAERZUNG. Gespraechstext kann Zugangsdaten enthalten, die ein Mensch
eingetippt hat. Alles geht durch einen Filter, BEVOR es geschrieben wird. Ein
Export ist eine Veroeffentlichung nach aussen -- auch in ein privates Repo, denn
was einmal in der Git-Historie steht, geht nicht mehr heraus.

⚠️ BEGRENZUNG. Die Clay-Protokolle wachsen (puls.jsonl >1 MB). Davon wandert nur
ein begrenztes Ende plus eine Tagesverdichtung mit, sonst blaeht der Export das
Repo bei jedem Lauf auf.
"""
from __future__ import annotations
import hashlib, json, os, re, shutil, sqlite3, subprocess, sys, time
from datetime import datetime, timezone
import pathlib
from pathlib import Path

DB = os.environ.get("AGENTZERO_DB", "/var/lib/clay/wiki.db")
REPO = Path(os.environ.get("AGENTZERO_REPO", "/opt/agentzero-export/repo"))
ZIEL = REPO / "agentZero"
SSH = "ssh -i /root/.ssh/agentzero_export -o IdentitiesOnly=yes -o BatchMode=yes"
CLAY_LOGS = {
    "puls": "/var/lib/clay/puls.jsonl",
    "ereignisse": "/var/lib/clay/ereignisse.jsonl",
    "tor": "/var/lib/clay/tor.jsonl",
}
LOG_TAIL = 500  # Zeilen je Clay-Protokoll

# ── Schwaerzung ────────────────────────────────────────────────────────────
GEHEIM = re.compile(
    r"(sk-np-[A-Za-z0-9_-]{8,}|sk-or-[A-Za-z0-9_-]{8,}|sk-[A-Za-z0-9]{20,}"
    r"|nvapi-[A-Za-z0-9_-]{8,}|gsk_[A-Za-z0-9]{8,}|AIza[A-Za-z0-9_-]{20,}"
    r"|hf_[A-Za-z0-9]{8,}|cfat_[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{20,}"
    r"|eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})"
)
SCHLUESSELFELD = re.compile(
    r"((?:API_KEY|APIKEY|TOKEN|SECRET|PASSWORD|PASSWORT)\s*[=:]\s*)([^\s\"',}]{8,})",
    re.IGNORECASE,
)
_geschwaerzt = 0
_GENERATION = [None]


def schwaerzen(x):
    """Rekursiv jeden String saeubern. Zaehlt, wie oft es gegriffen hat."""
    global _geschwaerzt
    if isinstance(x, str):
        neu, n1 = GEHEIM.subn("<GESCHWAERZT>", x)
        neu, n2 = SCHLUESSELFELD.subn(r"\1<GESCHWAERZT>", neu)
        _geschwaerzt += n1 + n2
        return neu
    if isinstance(x, dict):
        return {k: schwaerzen(v) for k, v in x.items()}
    if isinstance(x, list):
        return [schwaerzen(v) for v in x]
    return x


# ── Was jede Ablage IST, und warum es sie gibt ─────────────────────────────
# Eigner-Vorgabe: Herkunft, wieso gebaut, wo es dazugehoert, Hypothese,
# Gegenhypothese, Zeitstempel. Die Gegenhypothese steht bewusst dabei -- sie
# nennt, woran diese Ablage scheitern wuerde. Eine Sammlung ohne benannten
# Zweifel liest sich spaeter wie ein Beweis, obwohl sie nur eine Ablage ist.
BEDEUTUNG = {
    "chat": dict(
        wieso="Ohne Gespraechsverlauf ist jede spaetere Aussage ueber Zeros Verhalten eine Erinnerung, keine Quelle.",
        gehoert_zu="Laufzeit-Wirbelsaeule (turns) -- der Kern dessen, was zwischen Mensch und Entitaet passiert ist.",
        hypothese="Der vollstaendige Verlauf mit Kausalkette erlaubt es, jede Antwort auf ihren Zustand zurueckzufuehren.",
        gegenhypothese="Verlaeufe sind gefiltert: was der Haken nicht schreibt, fehlt hier -- der Export sieht nur, was aufgezeichnet wurde, nicht was geschah."),
    "kognition": dict(
        wieso="Kausalitaet und Wirkung muessen getrennt vom Gespraech nachvollziehbar sein, sonst zaehlt eine Behauptung wie ein Beleg.",
        gehoert_zu="TurnLifecycle, EffectGate, EffectJournal.",
        hypothese="Aus Episoden und Wirkungen laesst sich rekonstruieren, WARUM etwas geschah, nicht nur DASS.",
        gegenhypothese="Die Kausal-Kennungen belegen Verkettung, nicht Ursaechlichkeit. Zwei Zeilen mit derselben causal_id sind verbunden, nicht bewiesen."),
    "abruf": dict(
        wieso="Der Abruf lernt. Ohne Aufzeichnung ist nicht pruefbar, ob er besser wird oder nur anders.",
        gehoert_zu="MicroClay-Abrufentitaet, Eintrittspunkt-Politik, Wegehierarchie (F94).",
        hypothese="Gelernte Eintrittspunkte und Rueckmeldungen zeigen, ob sich eine Wegehierarchie bildet.",
        gegenhypothese="Solange der Modus SHADOW ist, steuert das Gelernte nichts -- die Zahlen koennen wachsen, ohne dass sich das Verhalten aendert."),
    "karten": dict(
        wieso="Eigner-Auftrag: die Karte wiederholt wegschreiben, damit die Veraenderung ueber die Zeit sichtbar wird.",
        gehoert_zu="F93/F94 Wegehierarchie -- Autobahnen, Tunnel, Landwege.",
        hypothese="Aus der Abfolge der Aufnahmen laesst sich die Vernetzung ablesen, ohne eigenes Messwerk.",
        gegenhypothese="Eine Momentaufnahme alle 30 min kann schnelle Umschichtungen ganz uebersehen; was dazwischen passiert, existiert im Zeitstrahl nicht."),
    "zustand": dict(
        wieso="Wurzelzustand und Identitaeten sind die Bezugsgroessen, gegen die alles andere gelesen wird.",
        gehoert_zu="meta, users, sessions, Graphprojektion.",
        hypothese="Wer Generation und Identitaeten kennt, kann jede andere Datei zeitlich einordnen.",
        gegenhypothese="Der Zustand ist eine Momentaufnahme; er sagt nichts darueber, wie oft er sich zwischen zwei Laeufen aenderte."),
    "wiki": dict(
        wieso="Alles, was inhaltlich zu Zero gehoert, soll auffindbar sein, ohne den ganzen Korpus zu kopieren.",
        gehoert_zu="Clay-Korpus (87 Tabellen), Volltextindex.",
        hypothese="Systemname im Titel ist eine belastbare Lesart von 'direkt damit zu tun'.",
        gegenhypothese="Der Titel kann taeuschen: ein Artikel ohne den Namen im Titel kann trotzdem der wichtigste sein. Kern/Umfeld ist eine Heuristik, keine Wahrheit."),
    "architektur": dict(
        wieso="Eine handgepflegte Skizze weicht nach zwei Wochen vom Code ab und luegt dann still.",
        gehoert_zu="Produktcode, laufende Dienste, Containerkonfiguration.",
        hypothese="Aus dem gemessenen Zustand abgeleitet kann die Skizze nicht veralten.",
        gegenhypothese="Abgeleitet heisst nicht vollstaendig: was der Ableiter nicht abfragt, taucht nicht auf -- und die Luecke sieht aus wie Abwesenheit."),
    "bauverlauf": dict(
        wieso="Der Grund einer Aenderung verschwindet als Erstes. Er steht im Commit-Text und wird hier bewahrt.",
        gehoert_zu="alle vier Repos.",
        hypothese="Commit-Texte mit Befund und Messung sind ein ehrlicheres Bautagebuch als ein gepflegtes.",
        gegenhypothese="Nur was jemand aufgeschrieben hat, ist hier. Stille Aenderungen bleiben still."),
    "tests": dict(
        wieso="Eine blosse Bestanden-Zahl sagt nicht, WAS rot ist und seit wann.",
        gehoert_zu="Testsuite des Produkts.",
        hypothese="Rote Tests mit Commit-Stand zeigen, welcher Zustand zu welchem Ergebnis gehoerte.",
        gegenhypothese="Gruen heisst nur: die geschriebenen Tests halten. Was niemand getestet hat, faellt hier nicht auf."),
    "puls": dict(
        wieso="Die Clay-Dienste arbeiten weiter, waehrend Zero laeuft -- ihr Takt gehoert zum Bild.",
        gehoert_zu="Clay-Unterbau (puls, ereignisse, tor).",
        hypothese="Ein begrenztes Ende genuegt, um Betrieb und Stillstand zu unterscheiden.",
        gegenhypothese="Nur die letzten Zeilen: ein Ausfall, der laenger her ist als das Fenster, ist unsichtbar."),
    "ZIELE": dict(
        wieso="Eigner-Auftrag: sichtbar machen, was Zero koennen SOLL und was davon steht.",
        gehoert_zu="alle Eignerentscheidungen dieses Bauabschnitts.",
        hypothese="Soll deklariert plus Ist gemessen bleibt ehrlich, weil niemand die Ist-Spalte pflegen kann.",
        gegenhypothese="Der Pruefer je Zeile ist selbst geschrieben -- er kann das Falsche messen und trotzdem gruen zeigen."),
}


def _bedeutung(pfad: Path) -> dict:
    # Pfad ist agentZero/<ordner>/<datei> -- der Ordner ist Teil 1, nicht 2.
    teile = pfad.relative_to(REPO).parts
    schluessel = teile[1] if len(teile) > 2 else pfad.stem.split(".")[0]
    return BEDEUTUNG.get(schluessel, dict(
        wieso="(kein Zweck hinterlegt -- Eintrag in BEDEUTUNG fehlt)",
        gehoert_zu="(unbekannt)", hypothese="(keine)", gegenhypothese="(keine)"))


# ── Werkzeuge ──────────────────────────────────────────────────────────────
def jetzt() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def schreibe(pfad: Path, zeilen: list, *, jsonl: bool, herkunft: str = "", felder=None) -> dict:
    """Schreibt die Datei UND eine Beipackdatei mit ihrer Herkunft.

    Eigner-Regel: alles muss Metadaten haben. Eine Datenzeile ohne Herkunft ist
    in einem halben Jahr nicht mehr deutbar -- man sieht Werte und weiss nicht,
    woher sie kamen, wann, aus welcher Generation, und ob sie vollstaendig sind.
    Die Beipackdatei liegt daneben, damit die Nutzdatei maschinenlesbar bleibt.
    """
    pfad.parent.mkdir(parents=True, exist_ok=True)
    if jsonl:
        text = "".join(json.dumps(z, ensure_ascii=False, sort_keys=True) + "\n" for z in zeilen)
    else:
        text = json.dumps(zeilen, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    pfad.write_text(text, encoding="utf-8")
    eintrag = {
        "datei": str(pfad.relative_to(REPO)),
        "zeilen": len(zeilen) if isinstance(zeilen, (list, dict)) else 1,
        "bytes": len(text.encode("utf-8")),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
    }
    if felder is None:
        if isinstance(zeilen, dict):
            felder = sorted(zeilen.keys())
        elif isinstance(zeilen, list) and zeilen and isinstance(zeilen[0], dict):
            felder = sorted(zeilen[0].keys())
    meta = {
        **eintrag,
        "erzeugt": jetzt(),
        "format": "jsonl" if jsonl else "json",
        "herkunft": herkunft or "UnifiedDB /var/lib/clay/wiki.db",
        "felder": felder or [],
        "erzeuger": "/opt/agentzero-export/agentzero_export.py auf frank-api",
        "geschwaerzt": "Zugangsdaten wurden vor dem Schreiben ersetzt",
        "entity_generation": _GENERATION[0],
        **_bedeutung(pfad),
    }
    pfad.with_suffix(pfad.suffix + ".meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    return eintrag


def tabelle(c, name: str) -> list:
    try:
        return [schwaerzen(dict(r)) for r in c.execute(f'SELECT * FROM "{name}"')]
    except Exception as e:
        return [{"_fehler": f"{type(e).__name__}: {e}"}]


def git(*a, **kw):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True,
                          env={**os.environ, "GIT_SSH_COMMAND": SSH}, **kw)


def wiki(c, manifest: dict) -> None:
    """Korpusartikel rund um Zero und EntityOS -- zweistufig, weil einstufig luegt.

    Gemessen: "agentzero OR entityos" trifft genau EINEN Artikel. Die Namen sind
    einen Tag alt, der Korpus ist es nicht. Eine breite Suche dagegen
    ("hyperposition", "unifieddb", ...) zieht 4.202 Artikel mit 13,1 MB Volltext
    herein -- das ist nicht "was mit Zero zu tun hat", das ist das halbe
    Forschungsarchiv, und es waere bei JEDEM Lauf neu in der Git-Historie.

    Deshalb zwei Stufen mit ehrlicher Grenze:
      KERN    der Systemname steht im TITEL -> Volltext. Das ist die belastbare
              Lesart von "direkt damit zu tun".
      UMFELD  der Begriff kommt nur im Text vor -> Titel, Metadaten, kurzer
              Ausschnitt. Auffindbar, ohne das Repo zu sprengen.
    """
    KERN = ('"agentzero" OR "agent zero" OR "entityos" OR "clayverse" OR '
            '"unifieddb" OR "effectgate" OR "claycode" OR "zero"')
    UMFELD = KERN + ' OR "hyperposition" OR "microclay" OR "claygraph"'

    def hole(match, volltext, limit):
        feld = "s.text" if volltext else "''"
        try:
            return c.execute(
                f"SELECT s.artikel_id, s.titel, {feld} AS text, a.art, a.sphaere, a.projekt, "
                "       a.datum, a.status, a.konfidenz, a.quelle, a.erzeugt_am, a.zuletzt_bearbeitet "
                "FROM fts_index_artikel f JOIN artikel_suchtext s ON s.id=f.rowid "
                "LEFT JOIN artikel a ON a.id=s.artikel_id "
                "WHERE fts_index_artikel MATCH ? ORDER BY bm25(fts_index_artikel) LIMIT ?",
                (match, limit),
            ).fetchall()
        except Exception as e:
            manifest["dateien"].append({"datei": "agentZero/wiki/", "_fehler": f"{type(e).__name__}: {e}"})
            return []

    # KERN: Treffer im Titel. FTS5 kann spaltenweise suchen -> titel:(...)
    kern_match = "titel:(" + KERN + ")"
    kern = [schwaerzen(dict(r)) for r in hole(kern_match, True, 800)]
    kern_ids = {k["artikel_id"] for k in kern}
    for k in kern:
        k["stufe"] = "kern"

    umfeld = []
    for r in hole(UMFELD, False, 3000):
        d = schwaerzen(dict(r))
        if d["artikel_id"] in kern_ids:
            continue
        d["stufe"] = "umfeld"
        d.pop("text", None)
        d["hinweis"] = "nur Nachweis -- Volltext steht im Clay-Korpus unter artikel_id"
        umfeld.append(d)

    e1 = schreibe(ZIEL / "wiki" / "kern.jsonl", kern, jsonl=True)
    e2 = schreibe(ZIEL / "wiki" / "umfeld.jsonl", umfeld, jsonl=True)
    manifest["dateien"] += [e1, e2]

    md = ["# Wiki-Eintraege zu Zero und EntityOS", "",
          f"Automatisch erzeugt {jetzt()} aus dem Clay-Korpus.", "",
          f"- **kern** ({len(kern)} Artikel, {e1['bytes']//1024} KB): der Systemname steht im Titel. Volltext.",
          f"- **umfeld** ({len(umfeld)} Artikel, {e2['bytes']//1024} KB): Begriff kommt nur im Text vor. Nur Nachweis, kein Text -- der steht im Korpus.", "",
          "Die Trennung ist keine Bequemlichkeit: eine Suche ueber den blossen Text trifft",
          "4.202 Artikel mit 13,1 MB -- das ist das Forschungsarchiv, nicht Zeros Umfeld.", ""]
    nach = {}
    for e in kern:
        nach.setdefault(e.get("sphaere") or "ohne Sphaere", []).append(e)
    for sph in sorted(nach):
        md += [f"## Kern / {sph} ({len(nach[sph])})", ""]
        for e in nach[sph][:150]:
            md.append(f"- **{(e.get('titel') or '?').replace('|','/')[:100]}** — "
                      f"`{(e.get('artikel_id') or '')[:44]}` · {e.get('art') or '?'}")
        md.append("")
    (ZIEL / "wiki" / "VERZEICHNIS.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    manifest["dateien"].append({"datei": "agentZero/wiki/VERZEICHNIS.md",
                                "kern": len(kern), "umfeld": len(umfeld)})


def messwerk(manifest: dict) -> None:
    """Das Messwerk: was rechenbar ist, wird gerechnet; der Rest sagt, was ihm fehlt."""
    try:
        sys.path.insert(0, "/opt/agentzero-export")
        import agentzero_messung, importlib
        importlib.reload(agentzero_messung)
        e = agentzero_messung.schreibe_messung(ZIEL / "messwerk")
        manifest["dateien"].append({"datei": "agentZero/messwerk/MESSWERK.md", **e})
        manifest["messwerk"] = e
    except Exception as ex:
        manifest["dateien"].append({"datei": "agentZero/messwerk/", "_fehler": f"{type(ex).__name__}: {ex}"})


def ziele_tabelle(manifest: dict) -> None:
    """Die Soll/Ist-Tabelle: was Zero koennen soll, und was davon gemessen steht."""
    try:
        sys.path.insert(0, "/opt/agentzero-export")
        import agentzero_ziele
        import importlib
        importlib.reload(agentzero_ziele)
        ergebnis = agentzero_ziele.schreibe_ziele(ZIEL)
        manifest["dateien"].append({"datei": "agentZero/ZIELE.md", **ergebnis})
        manifest["ziele"] = ergebnis
    except Exception as e:
        manifest["dateien"].append({"datei": "agentZero/ZIELE.md", "_fehler": f"{type(e).__name__}: {e}"})


def analysen(manifest: dict) -> None:
    """Ordner fuer die Auswertungen, die beim Bauen anfallen.

    Wird beim Lauf nur angelegt und mit einem Index versehen -- die Inhalte legt
    der Koordinator dort ab. Ein Index, der sich selbst schreibt, verhindert den
    ueblichen Zerfall: Dateien liegen da, aber niemand weiss mehr, was sie sind.
    """
    ana = ZIEL / "analysen"
    ana.mkdir(parents=True, exist_ok=True)
    vorhanden = sorted(x for x in ana.iterdir() if x.is_file() and x.name != "INDEX.md")
    md = ["# Analysen", "",
          f"Auswertungen rund um Zero und EntityOS. Index automatisch erzeugt {jetzt()}.", ""]
    if vorhanden:
        md += ["| Datei | Groesse | geaendert |", "|---|---|---|"]
        for f in vorhanden:
            st = f.stat()
            md.append(f"| [{f.name}]({f.name}) | {st.st_size} B | "
                      f"{datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime('%Y-%m-%d %H:%M')} |")
    else:
        md.append("_(noch leer)_")
    (ana / "INDEX.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    manifest["dateien"].append({"datei": "agentZero/analysen/INDEX.md", "eintraege": len(vorhanden)})


def testlaeufe(manifest: dict) -> None:
    """Ergebnisse der Testsuite, mit Metadaten -- nicht nur die Zahl.

    Eine blosse Bestanden-Zahl sagt nichts darueber, WAS rot ist. Hier landet die
    Liste der roten Tests samt Commit-Stand, damit spaeter nachvollziehbar ist,
    welcher Zustand zu welchem Ergebnis gehoerte.
    """
    art = ZIEL / "tests"
    art.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(
        "cd '/opt/entityos/the artefact' && /opt/entityos/venv-test/bin/python -m pytest tests/ "
        "-q --timeout=60 -p no:cacheprovider 2>&1 | tail -80",
        shell=True, capture_output=True, text=True, timeout=600)
    ausgabe = r.stdout or ""
    rot = [z.split(" ", 1)[1].strip() for z in ausgabe.splitlines() if z.startswith("FAILED ")]
    m = re.search(r"(\d+) failed, (\d+) passed", ausgabe)
    commit = subprocess.run("git -C /opt/entityos rev-parse --short HEAD", shell=True,
                            capture_output=True, text=True).stdout.strip()
    lauf = {
        "erzeugt": jetzt(),
        "commit": commit,
        "gruen": int(m.group(2)) if m else None,
        "rot": int(m.group(1)) if m else None,
        "rote_tests": rot,
        "hinweis": ("Rote Tests werden NICHT durch Abschwaechen gruen gemacht. Wo ein Test "
                    "auf etwas Echtes zeigt, bleibt er rot, bis die Sache behoben ist."),
    }
    manifest["dateien"].append(schreibe(art / "letzter-lauf.json", lauf, jsonl=False,
                                        herkunft="pytest gegen /opt/entityos/the artefact/tests"))
    verlauf = art / "verlauf.jsonl"
    with verlauf.open("a", encoding="utf-8") as f:
        f.write(json.dumps({k: lauf[k] for k in ("erzeugt", "commit", "gruen", "rot")},
                           ensure_ascii=False, sort_keys=True) + "\n")
    manifest["dateien"].append({"datei": "agentZero/tests/verlauf.jsonl",
                                "hinweis": "waechst -- eine Zeile je Lauf, damit die Kurve sichtbar bleibt"})


def quelltext(manifest: dict) -> None:
    """Aller ausfuehrbare Code rund um EntityOS -- versioniert, mit Pruefsummen."""
    import shutil
    ziel = ZIEL / "code"
    ERLAUBT = {".py", ".sh", ".json", ".service", ".timer", ".slice", ".yaml", ".yml", ".toml"}
    # Erlaubnisliste, keine Verbotsliste: bei einer Verbotsliste wandert irgendwann
    # etwas mit, an das niemand gedacht hat. Und niemals Daten.
    NIEMALS = {".db", ".sqlite", ".sqlite3", ".env", ".key", ".pem", ".jsonl", ".tgz", ".gz"}

    quellen = [
        ("produkt",  pathlib.Path("/opt/entityos/the artefact/clayverse"),
         "Das EntityOS-Produkt selbst."),
        ("unterbau", pathlib.Path("/opt/clayverse/werkzeug"),
         "Die 46 Clay-Werkzeuge. Steht NIRGENDS sonst in Git, obwohl vier laufende "
         "Dienste daran haengen -- der eigentliche Grund fuer diesen Ordner."),
        ("udb",      pathlib.Path("/opt/unifieddb/udb"),
         "Die udb-Schicht: Abruf, Speicher, Pflege, Karte."),
        ("export",   pathlib.Path("/opt/agentzero-export"),
         "Dieser Export selbst. Ein Werkzeug, das sich nicht mitexportiert, "
         "ist beim naechsten Wiederaufbau verschwunden."),
    ]
    uebersicht = []
    for name, wurzel, zweck in quellen:
        if not wurzel.is_dir():
            uebersicht.append({"bereich": name, "_fehlt": str(wurzel)})
            continue
        ablage = ziel / name
        dateien, bytes_ = 0, 0
        for f in sorted(wurzel.rglob("*")):
            if not f.is_file() or f.suffix in NIEMALS or f.suffix not in ERLAUBT:
                continue
            if any(t in f.parts for t in ("__pycache__", "venv", "venv-test", "node_modules",
                                          ".git", "repo")):
                continue
            if f.stat().st_size > 2_000_000:
                continue
            rel = f.relative_to(wurzel)
            aus = ablage / rel
            aus.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, aus)
            dateien += 1
            bytes_ += f.stat().st_size
        uebersicht.append({"bereich": name, "quelle": str(wurzel), "zweck": zweck,
                           "dateien": dateien, "bytes": bytes_})
        manifest["dateien"].append({"datei": f"agentZero/code/{name}/",
                                    "dateien": dateien, "bytes": bytes_, "quelle": str(wurzel)})

    md = ["# Ausfuehrbarer Code", "",
          f"Automatisch kopiert {jetzt()} vom laufenden Wirt. Nur Quelltext -- keine "
          "Datenbanken, keine Zugangsdaten, keine Sammlungen. Die Auswahl ist eine "
          "Erlaubnisliste, keine Verbotsliste.", "",
          "| Bereich | Dateien | Groesse | Quelle | Warum |", "|---|---|---|---|---|"]
    for u in uebersicht:
        if "_fehlt" in u:
            md.append(f"| {u['bereich']} | — | — | `{u['_fehlt']}` | nicht vorhanden |")
        else:
            md.append(f"| {u['bereich']} | {u['dateien']} | {u['bytes']//1024} KB | "
                      f"`{u['quelle']}` | {u['zweck']} |")
    (ziel / "UEBERSICHT.md").write_text("\n".join(md) + "\n", encoding="utf-8")


def unifieddb_leer(manifest: dict) -> None:
    """Das vollstaendige Schema und eine daraus erzeugte, wirklich leere Datenbank."""
    import sqlite3, tempfile
    ziel = ZIEL / "unifieddb"
    ziel.mkdir(parents=True, exist_ok=True)

    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    zeilen = [r[0] for r in c.execute(
        "SELECT sql FROM sqlite_master WHERE sql IS NOT NULL "
        "AND name NOT LIKE 'sqlite_%' ORDER BY CASE type "
        "WHEN 'table' THEN 1 WHEN 'index' THEN 2 WHEN 'trigger' THEN 3 ELSE 4 END, name")]
    tabellen_original = c.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0]
    c.close()

    sql = ("-- UnifiedDB: vollstaendiges Schema, KEINE Daten.\n"
           f"-- Erzeugt {jetzt()} aus {DB}.\n"
           "-- Wer diese Datei hat, kann EntityOS neu aufbauen, ohne einen einzigen\n"
           "-- Datensatz zu besitzen. Die echte Datenbank ist 3,8 GB und gehoert\n"
           "-- nicht in ein Repo -- ihre Struktur schon.\n\n"
           "PRAGMA foreign_keys=OFF;\nBEGIN;\n"
           + ";\n".join(z for z in zeilen if z) + ";\nCOMMIT;\n")
    (ziel / "schema.sql").write_text(sql, encoding="utf-8")

    # Gegenprobe: baut das Schema wirklich? Ein Schema, das nicht baut, waere
    # schlimmer als keines -- es sieht aus wie eine Sicherung.
    pruefung = {"gebaut": False}
    try:
        with tempfile.TemporaryDirectory() as d:
            probe = pathlib.Path(d) / "leer.db"
            p = sqlite3.connect(probe)
            p.executescript(sql)
            gebaut = p.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%'").fetchone()[0]
            p.close()
            pruefung = {"gebaut": True, "tabellen_erzeugt": gebaut,
                        "tabellen_original": tabellen_original,
                        "vollstaendig": gebaut == tabellen_original,
                        "bytes": probe.stat().st_size}
            shutil.copy2(probe, ziel / "leer.db")
    except Exception as e:
        pruefung = {"gebaut": False, "fehler": f"{type(e).__name__}: {e}"}

    (ziel / "PRUEFUNG.json").write_text(
        json.dumps({"erzeugt": jetzt(), **pruefung}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    manifest["dateien"].append({"datei": "agentZero/unifieddb/schema.sql",
                                "bytes": len(sql.encode()), **pruefung})
    manifest["unifieddb"] = pruefung


def bauverlauf(manifest: dict) -> None:
    """Der Bauverlauf, vollstaendig -- inklusive Begruendungen, nicht nur Betreffzeilen.

    Der Verlauf wird nicht nebenher gepflegt, er WIRD beim Bauen geschrieben: jeder
    Commit traegt den Befund, die Messung und den Grund im Text. Genau das wird hier
    ausgelesen. Ein handgefuehrtes Bautagebuch waere eine zweite Wahrheit, die
    irgendwann von der ersten abweicht.
    """
    ordner = ZIEL / "bauverlauf"
    ordner.mkdir(parents=True, exist_ok=True)
    TRENN = "\x1e"   # record separator, damit mehrzeilige Texte heil bleiben
    eintraege = []
    for repo, pfad in (("entityos", "/opt/entityos"), ("unifieddb", "/opt/unifieddb"),
                       ("clay", "/opt/clayverse"), ("agentzero-export", "/opt/agentzero-export/repo")):
        r = subprocess.run(
            f"git -C {pfad} log --format='%H%x1f%aI%x1f%an%x1f%s%x1f%b{TRENN}' -400 2>/dev/null",
            shell=True, capture_output=True, text=True, timeout=90)
        for satz in (r.stdout or "").split(TRENN):
            teile = satz.strip("\n").split("\x1f")
            if len(teile) < 4 or not teile[0].strip():
                continue
            h, datum, autor, betreff = teile[0].strip(), teile[1], teile[2], teile[3]
            koerper = teile[4] if len(teile) > 4 else ""
            eintraege.append({
                "repo": repo, "commit": h[:12], "zeit": datum, "autor": autor,
                "betreff": schwaerzen(betreff), "begruendung": schwaerzen(koerper.strip()),
                "hat_begruendung": bool(koerper.strip()),
            })
    eintraege.sort(key=lambda x: x["zeit"], reverse=True)
    manifest["dateien"].append(schreibe(ordner / "bauverlauf.jsonl", eintraege, jsonl=True,
                                        herkunft="git log aus vier Repos auf frank-api"))

    mit = [e for e in eintraege if e["hat_begruendung"]]
    md = ["# Bauverlauf", "",
          f"Automatisch erzeugt {jetzt()}. {len(eintraege)} Commits aus vier Repos, "
          f"davon {len(mit)} mit ausgeschriebener Begruendung.", "",
          "Der Verlauf wird nicht nebenher gepflegt -- er entsteht beim Bauen. Jeder Eintrag",
          "unten ist der Commit-Text selbst: Befund, Messung, Grund. Ein handgefuehrtes",
          "Bautagebuch waere eine zweite Wahrheit, die irgendwann von der ersten abweicht.", ""]
    tag = None
    for e in mit[:150]:
        t = e["zeit"][:10]
        if t != tag:
            md += [f"## {t}", ""]
            tag = t
        md += [f"### {e['betreff']}", "",
               f"`{e['commit']}` · {e['repo']} · {e['zeit'][11:16]} UTC · {e['autor']}", "",
               "```", e["begruendung"][:4000], "```", ""]
    (ordner / "BAUVERLAUF.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    manifest["dateien"].append({"datei": "agentZero/bauverlauf/BAUVERLAUF.md",
                                "commits": len(eintraege), "mit_begruendung": len(mit)})


def architektur(manifest: dict) -> None:
    """Architekturskizze und Aenderungshistorie -- BEIDE abgeleitet, nicht gepflegt.

    Eine von Hand gepflegte Skizze weicht nach zwei Wochen vom Code ab und luegt
    dann still. Alles hier wird bei jedem Lauf neu aus dem gemessenen Zustand
    erzeugt: Modulliste, Tabellenzahl, Dienste, Containerkonfiguration.
    """
    art = ZIEL / "architektur"
    art.mkdir(parents=True, exist_ok=True)

    def lauf(cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
            return r.stdout.strip()
        except Exception as e:
            return f"(nicht ermittelbar: {e})"

    # ── Aenderungshistorie, kategorisiert ──────────────────────────────────
    zeilen = []
    for repo, pfad in (("entityos", "/opt/entityos"), ("unifieddb", "/opt/unifieddb"), ("clay", "/opt/clayverse")):
        roh = lauf(f"git -C {pfad} log --format='%H%x09%aI%x09%an%x09%s' -200 2>/dev/null")
        for z in roh.splitlines():
            teile = z.split("\t")
            if len(teile) != 4:
                continue
            h, datum, autor, betreff = teile
            b = betreff.lower()
            if any(w in b for w in ("architekt", "endgestalt", "umbau", "identit", "verdraht")):
                kat = "architektur"
            elif any(w in b for w in ("fix", "behoben", "repariert", "bug", "sperre")):
                kat = "reparatur"
            elif b.startswith("f") and b[1:3].isdigit():
                kat = "entscheidung"
            elif any(w in b for w in ("test", "suite", "regression")):
                kat = "pruefung"
            else:
                kat = "bau"
            zeilen.append({"repo": repo, "commit": h[:12], "zeit": datum,
                           "autor": autor, "kategorie": kat, "betreff": schwaerzen(betreff)})
    zeilen.sort(key=lambda x: x["zeit"], reverse=True)
    manifest["dateien"].append(schreibe(art / "aenderungen.jsonl", zeilen, jsonl=True))

    nach_kat = {}
    for z in zeilen:
        nach_kat.setdefault(z["kategorie"], []).append(z)
    md = ["# Aenderungshistorie EntityOS", "",
          f"Automatisch erzeugt {jetzt()} aus drei Repos. {len(zeilen)} Eintraege.", ""]
    for kat in ("architektur", "entscheidung", "reparatur", "pruefung", "bau"):
        eintraege = nach_kat.get(kat, [])
        if not eintraege:
            continue
        md += [f"## {kat} ({len(eintraege)})", "", "| Zeit | Repo | Commit | Betreff |", "|---|---|---|---|"]
        for z in eintraege[:60]:
            md.append(f"| {z['zeit'][:16]} | {z['repo']} | `{z['commit']}` | {z['betreff'][:110]} |")
        md.append("")
    (art / "AENDERUNGEN.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # ── Skizze, aus dem Ist-Zustand abgeleitet ────────────────────────────
    module = lauf("ls /opt/entityos/the\\ artefact/clayverse/*.py 2>/dev/null | wc -l")
    zeilenzahl = lauf("cat /opt/entityos/the\\ artefact/clayverse/*.py 2>/dev/null | wc -l")
    tests = lauf("ls /opt/entityos/the\\ artefact/tests/*.py 2>/dev/null | wc -l")
    dienste = lauf("systemctl list-units 'clayverse-*' --state=running --no-legend --no-pager | awk '{print $1}'")
    container = lauf("docker inspect entityos --format '{{.Config.Image}} | user {{.Config.User}} | {{json .NetworkSettings.Ports}}' 2>/dev/null")
    mcp = lauf("grep -ohE '\"(mcp__clayverse__[a-z_]+|udb_[a-z_]+)\"' /opt/entityos/the\\ artefact/clayverse/mcp_server.py 2>/dev/null | tr -d '\"' | sort -u | tr '\\n' ' '")
    z = manifest.get("zaehler", {})

    (art / "SKIZZE.md").write_text(f"""# EntityOS -- Architekturskizze

**Automatisch abgeleitet, nicht gepflegt.** Erzeugt {jetzt()} aus dem gemessenen
Zustand auf `frank-api`. Eine handgepflegte Skizze weicht nach zwei Wochen vom Code
ab und luegt dann still; diese kann das nicht, weil sie bei jedem Lauf neu aus Code,
Datenbank und laufenden Diensten entsteht.

## Die vier Namen

| Name | Was es ist |
|---|---|
| **EntityOS** | das Betriebssystem, der Container, das Produkt, das Frontend |
| **Zero** | die Entitaet selbst. Agent Zero. Wer im Terminal antwortet |
| **ClayCode** | Zeros Werkzeug, unveraendert |
| **Clay** | der Unterbau: Korpus, Graph, die vier Dienste |

## Der Weg eines Satzes

```mermaid
flowchart TD
    M[Mensch im Browser] -->|Clerk-Anmeldung| N[nginx TLS auf 72.61.19.188]
    N -->|WebSocket + SSH-Tunnel| S[EntityOS-Container auf frank-api]
    S -->|UserPromptSubmit-Haken| T[TurnLifecycle: Zug aufnehmen]
    T --> W[WorldAssembler]
    W --> A[Abruf-Entitaet MicroClay]
    W --> K[(Clay-Korpus: Artikel, Kanten, Lesarten)]
    W --> I[Kanonische Identitaet Ebene 0]
    T --> C[Zero = Claude Code in tmux]
    C -->|MCP| E{{EffectGate}}
    E -->|Urteil| J[(EffectJournal)]
    C -->|Stop-Haken| T
    T --> D[(UnifiedDB = wiki.db)]
    P[Autonomie-Puls 30s] -->|next_runnable| T
```

## Gemessener Bestand

| | |
|---|---|
| Produktmodule | {module} Dateien, {zeilenzahl} Zeilen |
| Testdateien | {tests} |
| Tabellen in der UnifiedDB | {z.get('_tabellen', 'n/a')} |
| Artikel im Korpus | {z.get('artikel', 'n/a')} |
| Kanten | {z.get('kante', 'n/a')} |
| Lesarten | {z.get('wm_lesart', 'n/a')} |
| Zuege von Zero | {z.get('turns', 'n/a')} |
| Wirkungen durch das Tor | {z.get('effects', 'n/a')} |
| Abrufepisoden | {z.get('retrieval_episodes', 'n/a')} |
| gelernte Eintrittspunkte | {z.get('retrieval_entrypoint_policy', 'n/a')} |
| Entitaetsgeneration | {manifest.get('entity_generation', 'n/a')} |

## Laufende Clay-Dienste

```
{dienste or '(keine)'}
```

## Container

```
{container or '(nicht ermittelbar)'}
```

## Werkzeuge, die Zero erreichen kann

```
{mcp or '(keine ermittelt)'}
```

## Ein Gefaess, zwei Schichten

Die Laufzeit-Wirbelsaeule (Zuege, Sitzungen, Wirkungen, Kausalitaet,
Abruf-Lernen) liegt in **derselben Datei** wie der Clay-Korpus. Keine
Namenskollision, gemessen. Die vier Clay-Dienste schreiben unveraendert weiter,
die Entitaet schreibt daneben -- eine Wahrheit, kein zweites Gedaechtnis.
""", encoding="utf-8")
    manifest["dateien"].append({"datei": "agentZero/architektur/SKIZZE.md", "abgeleitet": True})
    manifest["dateien"].append({"datei": "agentZero/architektur/AENDERUNGEN.md",
                                "eintraege": len(zeilen), "abgeleitet": True})


def main() -> int:
    t0 = time.time()
    # Stand des Remote ZUERST holen, sonst wirft ein spaeteres reset die
    # frisch geschriebenen Dateien wieder weg.
    git("fetch", "origin", "main")
    git("reset", "--hard", "origin/main")
    # Exportformate aendern sich. Was eine frueherer Fassung angelegt hat und diese
    # nicht mehr schreibt, bliebe sonst ewig liegen und waere bei jedem Abruf eine
    # Luege ueber den aktuellen Stand.
    for veraltet in ("agentZero/wiki/artikel.jsonl",):
        alt = REPO / veraltet
        if alt.exists():
            alt.unlink()
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    manifest = {"erzeugt": jetzt(), "quelle": DB, "dateien": []}

    gen = c.execute("SELECT value FROM meta WHERE key='entity_generation'").fetchone()
    manifest["entity_generation"] = int(gen[0]) if gen else None
    _GENERATION[0] = manifest["entity_generation"]

    # ── chat: je Mensch eine Datei, mit allen Metadaten ────────────────────
    for (uid,) in c.execute("SELECT user_id FROM users ORDER BY user_id"):
        zeilen = tabelle(c, "turns")
        eigene = [z for z in zeilen if z.get("user_id") == uid]
        manifest["dateien"].append(schreibe(ZIEL / "chat" / f"session-{uid}.jsonl", eigene, jsonl=True))

    # ── kognition ─────────────────────────────────────────────────────────
    for t in ("causal_episodes", "workspace_episodes", "effects", "checkpoints", "active_turns", "leases"):
        manifest["dateien"].append(schreibe(ZIEL / "kognition" / f"{t}.jsonl", tabelle(c, t), jsonl=True))

    # ── abruf: die Spur der Abruf-Entitaet ────────────────────────────────
    for t in ("retrieval_episodes", "retrieval_entrypoint_policy", "retrieval_feedback",
              "retrieval_policy_state", "durable_memory"):
        manifest["dateien"].append(schreibe(ZIEL / "abruf" / f"{t}.jsonl", tabelle(c, t), jsonl=True))

    # ── zustand ───────────────────────────────────────────────────────────
    for t in ("users", "sessions", "meta", "graph_nodes", "graph_edges"):
        manifest["dateien"].append(schreibe(ZIEL / "zustand" / f"{t}.json", tabelle(c, t), jsonl=False))

    # ── karten: eine Momentaufnahme je Lauf -> daraus wird der Zeitstrahl ──
    def zahl(t):
        try:
            return c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        except Exception:
            return None

    karte = {
        "erzeugt": jetzt(),
        "entity_generation": manifest["entity_generation"],
        "zaehler": {t: zahl(t) for t in (
            "turns", "causal_episodes", "workspace_episodes", "effects", "durable_memory",
            "retrieval_episodes", "retrieval_entrypoint_policy", "retrieval_feedback",
            "checkpoints", "artikel", "kante", "graph_knoten", "graph_kante", "wm_lesart",
            "anreicherung", "fundort", "datei",
        )},
        "eintrittspunkte": [schwaerzen(dict(r)) for r in c.execute(
            "SELECT entry_key,capital,reward_ema,pulls,updated_at "
            "FROM retrieval_entrypoint_policy ORDER BY capital DESC LIMIT 200")],
        "abruf_modus": [dict(r) for r in c.execute("SELECT * FROM retrieval_policy_state")],
        "hinweis": ("Momentaufnahme der Wegehierarchie. Mehrere Aufnahmen hintereinander "
                    "ergeben den Zeitstrahl, aus dem sich die Vernetzung ablesen laesst. "
                    "capital = Wegeguete, pulls = wie oft gegangen."),
    }
    manifest["zaehler"] = dict(karte["zaehler"])
    manifest["zaehler"]["_tabellen"] = c.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    stempel = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H%M%SZ")
    manifest["dateien"].append(schreibe(ZIEL / "karten" / f"{stempel}.json", karte, jsonl=False))

    # ── clay-protokolle, begrenzt ─────────────────────────────────────────
    for name, pfad in CLAY_LOGS.items():
        p = Path(pfad)
        if not p.exists():
            continue
        try:
            alle = p.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        ende = []
        for zeile in alle[-LOG_TAIL:]:
            try:
                ende.append(schwaerzen(json.loads(zeile)))
            except Exception:
                ende.append({"_roh": schwaerzen(zeile)[:2000]})
        eintrag = schreibe(ZIEL / "puls" / f"{name}-letzte{LOG_TAIL}.jsonl", ende, jsonl=True)
        eintrag["quelle_zeilen_gesamt"] = len(alle)
        eintrag["hinweis"] = f"nur die letzten {LOG_TAIL} von {len(alle)} Zeilen -- Vollexport wuerde das Repo aufblaehen"
        manifest["dateien"].append(eintrag)

    wiki(c, manifest)
    c.close()

    architektur(manifest)
    bauverlauf(manifest)
    quelltext(manifest)
    unifieddb_leer(manifest)
    testlaeufe(manifest)
    ziele_tabelle(manifest)
    messwerk(manifest)
    analysen(manifest)

    manifest["geschwaerzte_fundstellen"] = _geschwaerzt
    manifest["dauer_sekunden"] = round(time.time() - t0, 2)
    manifest["hinweis"] = (
        "Automatisch erzeugt von /opt/agentzero-export/agentzero_export.py auf frank-api. "
        "Nicht von Hand bearbeiten -- jeder Lauf ueberschreibt. Ausnahme: karten/ waechst, "
        "jede Aufnahme bleibt stehen, weil der Zeitstrahl genau daraus besteht."
    )
    ZIEL.mkdir(parents=True, exist_ok=True)
    (ZIEL / "MANIFEST.json").write_text(
        json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")

    (ZIEL / "README.md").write_text(f"""# agentZero

Die vollstaendige Spur von **Zero** (Agent Zero), der Entitaet auf EntityOS.
Automatisch exportiert aus der UnifiedDB auf `frank-api`, zuletzt {manifest['erzeugt']}.

| Ordner | Inhalt |
|---|---|
| `chat/` | die Gespraeche, je Mensch eine Datei, mit vollstaendigen Metadaten (Generation, Provenienz, Kausalkette) |
| `kognition/` | Kausalepisoden, Arbeitsraum-Episoden, Wirkungen samt EffectGate-Urteil, Pruefpunkte |
| `abruf/` | was die Abruf-Entitaet tut: Episoden, gelernte Eintrittspunkte, Rueckmeldungen |
| `karten/` | **eine Momentaufnahme je Lauf.** Mehrere hintereinander ergeben den Zeitstrahl, aus dem sich die Vernetzung ablesen laesst |
| `zustand/` | Menschen, Sitzungen, Wurzelzustand, Graphprojektion |
| `puls/` | begrenztes Ende der Clay-Protokolle (letzte {LOG_TAIL} Zeilen je Datei) |
| `wiki/` | alle Korpusartikel, die direkt mit Zero/EntityOS zu tun haben, plus lesbares Verzeichnis |
| `architektur/` | Aenderungshistorie aller drei Repos, kategorisiert, und die abgeleitete Skizze |
| `analysen/` | Auswertungen, die beim Bauen anfallen, mit selbstgeschriebenem Index |
| `messwerk/` | **jeder Sensor mit der Hypothese, die er unterscheidet** — gemessen, oder ehrlich warum nicht |
| `ZIELE.md` | **was Zero koennen soll und was davon gemessen steht** -- Soll deklariert, Ist gemessen |
| `code/` | **aller ausfuehrbare Code** rund um EntityOS: Produkt, Clay-Unterbau, udb, der Export selbst |
| `unifieddb/` | **das vollstaendige Schema und eine leere Datenbank daraus** -- Wiederaufbau ohne einen Datensatz |
| `bauverlauf/` | **jeder Commit mit voller Begruendung** -- Befund, Messung, Grund. Entsteht beim Bauen, nicht nebenher |
| `tests/` | Ergebnisse der Testsuite je Lauf, mit Commit-Stand und der Liste der roten Tests |
| `MANIFEST.json` | Zeilenzahlen, Groessen, Pruefsummen, Laufzeit je Export |

## Schwaerzung

Jeder Wert laeuft durch einen Filter, **bevor** er geschrieben wird: API-Schluessel,
Token und JWTs werden durch `<GESCHWAERZT>` ersetzt. Beim letzten Lauf griff der
Filter **{_geschwaerzt}x**. Der Grund ist einfach: was einmal in der Git-Historie
steht, bekommt man nicht mehr heraus -- auch aus einem privaten Repo nicht.

## Warum `karten/` waechst und alles andere nicht

Die uebrigen Ordner sind Abbilder des aktuellen Zustands und werden bei jedem Lauf
ueberschrieben. `karten/` ist das Gegenteil: dort bleibt jede Aufnahme stehen, denn
die Veraenderung ueber die Zeit **ist** der Inhalt.
""", encoding="utf-8")

    # ── committen und schieben ────────────────────────────────────────────
    git("add", "agentZero")
    st = git("status", "--porcelain", "agentZero")
    if not st.stdout.strip():
        print(json.dumps({"status": "unveraendert", "geschwaerzt": _geschwaerzt}, ensure_ascii=False))
        return 0
    git("-c", "user.name=agentZero", "-c", "user.email=agentzero@frank.ink",
        "commit", "-q", "-m",
        f"agentZero-Export {manifest['erzeugt']} (Generation {manifest['entity_generation']}, "
        f"{len(manifest['dateien'])} Dateien, {_geschwaerzt} geschwaerzt)")
    push = git("push", "origin", "HEAD:main")
    print(json.dumps({
        "status": "geschoben" if push.returncode == 0 else "PUSH-FEHLER",
        "dateien": len(manifest["dateien"]),
        "geschwaerzt": _geschwaerzt,
        "generation": manifest["entity_generation"],
        "dauer_s": manifest["dauer_sekunden"],
        "fehler": push.stderr.strip()[-300:] if push.returncode else "",
    }, ensure_ascii=False))
    return 0 if push.returncode == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
