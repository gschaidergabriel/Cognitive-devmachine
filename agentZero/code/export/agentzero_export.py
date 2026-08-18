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
    "menschen": dict(
        wieso="Eigner-Auftrag 18.08.: Menschen, Projekte und die Artikelzuordnung gehoeren sichtbar "
              "dazu -- aber das Repo ist OEFFENTLICH, deshalb gilt hier eine engere Freigabe als die "
              "sonstige Schwaerzung (die faengt nur Zugangsdaten, keine Mailadressen).",
        gehoert_zu="entityos_profil, entityos_projekte, entityos_artikel_zuordnung in der UnifiedDB.",
        hypothese="Struktur und Aggregat gehen frei raus; Profilinhalt nur wo herkunft=iar.frank.ink "
                  "(schon oeffentlich auf der Institutsseite) oder einzeln als unpersoenlich geprueft "
                  "-- das schuetzt, ohne zu verschweigen, DASS es Regeln und Zurueckgehaltenes gibt.",
        gegenhypothese="Die Eigner-Ausnahmen sind von Hand einzeln entschieden, nicht automatisch aus "
                       "einer Regel ableitbar. Ein neues privates Eigner-Feld faellt nur dann korrekt "
                       "raus, wenn niemand es versehentlich in die Ausnahmeliste eintraegt."),
    "baunotizen": dict(
        wieso="Eigner-Auftrag 18.08. woertlich: 'alle deine baunotizen werden auch teil des wiki "
              "und mit alle meine ich alle mit metadaten und alles' -- hier die oeffentliche Seite "
              "davon: Aggregat statt 2330-Zeilen-Dump, plus eine lecksuche-gepruefte Stichprobe.",
        gehoert_zu="artikel(art IN ('baunotiz','vorfall')) in der UnifiedDB, gefuellt von "
                  "clayverse/baunotizen.py aus drei Quellen (git-commit, bauverlauf.jsonl, protokoll.jsonl).",
        hypothese="Aggregatzahlen plus eine geprueft-oeffentliche Stichprobe der juengsten Eintraege "
                  "zeigen Umfang, Herkunftsmischung und Charakter des Bauverlaufs verlaesslich, ohne "
                  "den ganzen Bestand roh zu veroeffentlichen.",
        gegenhypothese="Die Stichprobe ist nach Datum sortiert, nicht nach Bedeutung -- die juengsten "
                       "Eintraege koennen einen unrepraesentativen Ausschnitt zeigen. Zeilen mit einem "
                       "Lecktreffer fehlen komplett, nicht redigiert -- die Stichprobe ist dadurch kleiner "
                       "als 25, wenn viele juengste Zeilen Adressen/IPs enthalten."),
    "wissen": dict(
        wieso="Eigner-Auftrag 18.08.: Betriebs- und Personenwissen lag nur in der gitignorierten "
              "CLAUDE.md auf einem Arbeitsrechner, vermischt mit Geheimnissen -- nirgends teilbar. "
              "clayverse/wissen.py hat es geheimnisfrei herausgeloest; hier die oeffentliche Seite.",
        gehoert_zu="artikel(art='wissen', projekt='EntityOS') in der UnifiedDB, gefuellt von "
                  "clayverse/wissen.py aus der Eigner-CLAUDE.md.",
        hypothese="Elf Artikel mit metadaten.geheimnisfrei=true genuegen, um Betriebswissen (Deploy, "
                  "Domains, Testpflicht) und Personenwissen (Rollen, Entscheidungsrecht) oeffentlich "
                  "nachvollziehbar zu machen.",
        gegenhypothese="geheimnisfrei=true ist eine Selbstauskunft des Quellprozesses, keine "
                       "unabhaengige Pruefung. Dieser Export schwaerzt zusaetzlich wie jede andere "
                       "Ablage, aber ein Fehler in wissen.py selbst wuerde hier nicht auffallen."),
    "verdichtungen": dict(
        wieso="82 Verdichtungen faszen Baunotizen-Gruppen zu Kurzartikeln zusammen -- ohne die "
              "Kompressionszahl daneben ist nicht pruefbar, ob eine 'Verdichtung' wirklich kuerzt "
              "oder nur umformuliert.",
        gehoert_zu="artikel(art='verdichtung') in der UnifiedDB, gefuellt von "
                  "clayverse/wikiverdichtung.py aus Baunotiz-Gruppen (metadaten.quellnotizen).",
        hypothese="Das gemessene Verhaeltnis zeichen_quellen/zeichen_artikel je Zeile zeigt ehrlich, "
                  "wie stark verdichtet wurde -- eine Zahl, keine Behauptung.",
        gegenhypothese="Ein Verhaeltnis < 1 heisst: der Artikel ist LAENGER als die Summe seiner "
                       "Quellen -- keine Verdichtung, eine Ausweitung. Das kommt in diesem Bestand "
                       "vor (siehe VERDICHTUNGEN.md) und ist kein Darstellungsfehler dieses Exports, "
                       "sondern ein Befund ueber den Mechanismus selbst."),
    "tresor": dict(
        wieso="Eigner-Auftrag: Zero soll wissen, WELCHE Bahnen und Zugaenge es gibt und was sie "
              "koennen (Modell, Limits, Zweck), ohne je einen Schluessel zu sehen.",
        gehoert_zu="clayverse/tresor.py, zwei AES-256-GCM-Tresore ('api', 'zugaenge') unter "
                  "/etc/entityos/tresor.",
        hypothese="katalog() wird mechanisch gegen jeden gelagerten Wert geprueft, bevor es "
                  "herausgeht -- eine Sicherung, keine Gewohnheit -- deshalb kann der Katalog "
                  "gefahrlos exportiert werden.",
        gegenhypothese="Die eingebaute Pruefung faengt nur, was WOERTLICH im gelagerten Wert steht. "
                       "Ein Geheimnis, das an anderer Stelle unverschluesselt zitiert wuerde, faellt "
                       "nicht automatisch darunter -- deshalb prueft dieser Export den Katalogtext "
                       "zusaetzlich von aussen, bevor er ihn schreibt."),
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


def schreibe_markdown(pfad: Path, text: str, *, herkunft: str = "") -> dict:
    """Wie schreibe(), aber fuer Fliesstext/Markdown -- gleiche Beipackdatei-Pflicht.

    Der Vertrag gilt fuer JEDE Datei, nicht nur JSON: herkunft, wieso, gehoert_zu,
    hypothese, gegenhypothese, Zeitstempel, Generation, Pruefsumme. Ohne Beipackdatei
    ist eine Markdown-Datei in einem halben Jahr genauso undeutbar wie eine JSON-Zeile
    ohne Herkunft.
    """
    pfad.parent.mkdir(parents=True, exist_ok=True)
    pfad.write_text(text, encoding="utf-8")
    eintrag = {
        "datei": str(pfad.relative_to(REPO)),
        "zeilen": text.count("\n") + 1,
        "bytes": len(text.encode("utf-8")),
        "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest()[:16],
    }
    meta = {
        **eintrag,
        "erzeugt": jetzt(),
        "format": "markdown",
        "herkunft": herkunft or "UnifiedDB /var/lib/clay/wiki.db",
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
        # ⚠️ schwaerzen() kennt Zugangsdaten, keine Adressen. Zeros eigene
        # Antworten sind Prosa und koennen alles enthalten, was im Kontext
        # stand -- gemessen: eine Profiltabelle mit Mailadresse.
        d = schwaerzen({k: (_prosa_schwaerzen(v) if isinstance(v, str) else v)
                        for k, v in dict(r).items()})
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



_QUELL_MUSTER = (
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",     # Mailadressen
    r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b",                  # IP-Adressen
    r"\b(?:sk|gsk|hf)_[A-Za-z0-9]{16,}",                    # Schluessel
)


def _quelltext_pruefen(text: str) -> list[str]:
    """Was in einer Quelldatei steht, das dort nicht hingehoert.

    ⭐ MELDEN, NICHT SCHWAERZEN. Ein Codearchiv, das anders ist als der Code,
    ist schlimmer als keines -- es sieht wiederverwendbar aus und baut nicht.
    Der richtige Ort fuer die Reparatur ist die Quelldatei selbst.
    Gefunden am 18.08.: zwei echte Mailadressen als Literale in profile.py,
    waehrend derselbe Export sie aus PROFILE.md schwaerzte. Eine Schwaerzung,
    die nur eine von zwei Auslieferungen kennt, ist ein Ritual.
    """
    import re as _re
    treffer = []
    for muster in _QUELL_MUSTER:
        for m in _re.findall(muster, text):
            if m.endswith((".py", ".md", ".json")) or m.startswith(("0.0.0.0", "127.0.0.1")):
                continue
            treffer.append(m)
    return sorted(set(treffer))[:12]


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
    # FTS5 legt zu jeder virtuellen Tabelle Schattentabellen an (_data, _idx,
    # _content, _docsize, _config). Sie stehen in sqlite_master, gehoeren aber
    # NICHT in den Abzug: beim Wiederaufbau erzeugt die virtuelle Tabelle sie
    # selbst, und die Kopie kollidiert. Ein Abzug, der daran scheitert, sieht
    # aus wie eine Sicherung und ist keine.
    virtuelle = [r[0] for r in c.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND sql LIKE '%VIRTUAL TABLE%'")]
    SUFFIXE = ("_data", "_idx", "_content", "_docsize", "_config")
    schatten = {f"{v}{sfx}" for v in virtuelle for sfx in SUFFIXE}

    zeilen = []
    for name, sql_ in c.execute(
            "SELECT name, sql FROM sqlite_master WHERE sql IS NOT NULL "
            "AND name NOT LIKE 'sqlite_%' ORDER BY CASE type "
            "WHEN 'table' THEN 1 WHEN 'index' THEN 2 WHEN 'trigger' THEN 3 ELSE 4 END, name"):
        if name in schatten:
            continue
        zeilen.append(sql_)
    tabellen_original = c.execute(
        "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()[0] - len(schatten)
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
                "AND name NOT LIKE 'sqlite_%'").fetchone()[0] - len(schatten)
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



def _prosa_schwaerzen(text: str) -> str:
    """Mailadressen und IPs aus PROSA entfernen (Commit-Texte, Berichte).

    ⭐ Nur bei Prosa, nie bei Quelltext: eine geschwaerzte Begruendung bleibt
    lesbar, eine geschwaerzte Quelldatei baut nicht. Deshalb wird Quelltext nur
    GEMELDET (_quelltext_pruefen), Prosa aber geschwaerzt.

    Anlass: eine Commit-Begruendung, in der erklaert wurde, dass eine Adresse
    strittig sei, trug diese Adresse woertlich -- und wanderte so in den Export.
    Die Dokumentation des Lecks war das Leck.
    """
    import re as _re
    t = _re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "<adresse>", text)
    # Auch OHNE Domain: `genuinos@` ist nicht nutzbar, aber identifizierend --
    # und stand genau so in einem Commit-Text, der den Adressenstreit erklaerte.
    t = _re.sub(r"\b[A-Za-z0-9._%+-]{3,}@(?=[\s`,;)\]]|$)", "<adresse>", t)
    t = _re.sub(r"\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b", "<adresse>", t)
    return t


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
                # schwaerzen() kennt Zugangsdaten, aber keine Mailadressen -- gefunden,
                # weil MEIN eigener Commit-Text, der den Adressenstreit erklaert,
                # die Adresse woertlich trug und so in den Export wanderte.
                # Die Dokumentation des Lecks war das Leck.
                "betreff": schwaerzen(_prosa_schwaerzen(betreff)),
                "begruendung": schwaerzen(_prosa_schwaerzen(koerper.strip())),
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
                           "autor": autor, "kategorie": kat, "betreff": schwaerzen(_prosa_schwaerzen(betreff))})
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


# ── Mailadressen-Notbremse fuer menschen/ -- unabhaengig von herkunft ───────
_MAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def profile_und_zuordnung(manifest: dict) -> None:
    """Menschen, Projekte, Artikelzuordnung -- OEFFENTLICHES Repo, echte Menschen.

    ⚠️ PRIVATSPHAERE. Dieses Repo ist oeffentlich auf GitHub. Die Profile
    beschreiben zwei echte Menschen. Struktur und Aggregat gehen frei raus --
    Schema, Zaehlungen, Verteilung, die Herkunftsregeln, die Trennung
    Eigentum/Urheberschaft. Beim INHALT der Profile gilt eine ENGERE Freigabe
    als schwaerzen() (das faengt nur Zugangsdaten, keine Mailadressen): nur
    Felder mit herkunft='iar.frank.ink' (schon oeffentlich auf der
    Institutsseite) oder einzeln geprueft klar unpersoenliche Eigner-Felder
    gehen mit. Bei Zweifel bleibt das Feld draussen und steht in PROFILE.md
    als zurueckgehalten -- nicht stillschweigend weggelassen. Zurueckhalten
    ist umkehrbar, eine veroeffentlichte Mailadresse nicht.
    """
    ordner = ZIEL / "menschen"
    ordner.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row

    ERLAUBTE_HERKUNFT = {"iar.frank.ink"}
    # Eigner-Felder, EINZELN geprueft und als unpersoenlich eingestuft -- alles
    # andere mit herkunft='eigner' (allen voran die beiden Mailadressen) bleibt draussen.
    EIGNER_AUSNAHME = {
        ("gabriel", "github"): "nennt nur das GitHub-Konto, unter dem dieses Repo selbst liegt "
                               "-- aus der Repo-URL ohnehin sichtbar.",
        ("gabriel", "rolle_technisch"): "Arbeitsrollen-Aussage (wer den Code schreibt), keine "
                                        "Kontakt- oder Privatangabe -- deckt sich mit den "
                                        "Autorennamen in bauverlauf/.",
        ("gemeinsam", "herkunft_zero"): "beschreibt die Entitaet Zero, nicht eine Person.",
    }

    profil_rows = [dict(r) for r in c.execute(
        "SELECT user_id, feld, wert, herkunft, beleg, erfasst FROM entityos_profil "
        "ORDER BY user_id, feld")]

    freigegeben, zurueckgehalten = [], []
    for row in profil_rows:
        schluessel = (row["user_id"], row["feld"])
        if row["herkunft"] in ERLAUBTE_HERKUNFT or schluessel in EIGNER_AUSNAHME:
            freigegeben.append(row)
        elif row["herkunft"] == "eigner":
            row["_grund"] = "herkunft=eigner, keine gepruefte Ausnahme -- koennte privat sein"
            zurueckgehalten.append(row)
        else:
            row["_grund"] = (f"herkunft={row['herkunft']}, nicht in ERLAUBTE_HERKUNFT -- "
                             "noch nicht einzeln geprueft, konservativ zurueckgehalten")
            zurueckgehalten.append(row)

    # Gegenprobe -- die Sache, die diese Funktion ueberhaupt rechtfertigt: egal
    # was herkunft sagt, nichts, das wie eine Mailadresse aussieht, geht mit.
    for row in list(freigegeben):
        if _MAIL.search(row["wert"]):
            freigegeben.remove(row)
            row["_grund"] = "Notbremse: sah aus wie eine Mailadresse -- automatisch zurueckgehalten"
            zurueckgehalten.append(row)

    e1 = schreibe(ordner / "profile_freigegeben.json", freigegeben, jsonl=False,
                 herkunft="entityos_profil in UnifiedDB, gefiltert auf iar.frank.ink + geprueften Eigner-Ausnahmen")
    manifest["dateien"].append(e1)

    md = ["# Menschen hinter Zero", "",
          f"Automatisch erzeugt {jetzt()}. Dieses Repo ist OEFFENTLICH -- deshalb gilt hier eine "
          "engere Freigabe als die sonstige Schwaerzung (die faengt nur Zugangsdaten). Nur Felder "
          "mit `herkunft=iar.frank.ink` (schon oeffentlich auf der Institutsseite) oder einzeln "
          "gepruefte, klar unpersoenliche Eigner-Felder stehen unten. Alles andere steht als "
          "zurueckgehalten da, nicht stillschweigend weggelassen.", "",
          "## Herkunftsregeln", "",
          "| Kuerzel | Bedeutung | frei? |", "|---|---|---|",
          "| `eigner` | vom Eigner selbst bestaetigt -- kann Privates enthalten | nur nach Einzelpruefung |",
          "| `iar.frank.ink` | steht schon oeffentlich auf der Institutsseite | ja |",
          "| `abgeleitet` | aus anderen Feldern hergeleitet | nur nach Einzelpruefung |",
          "| `gemessen` | aus dem laufenden System gemessen (z.B. Zugriffszahlen, Rechnername) | nur nach Einzelpruefung |", "",
          "## Freigegeben", ""]
    nach_mensch: dict = {}
    for r in freigegeben:
        nach_mensch.setdefault(r["user_id"], []).append(r)
    for u in sorted(nach_mensch):
        md += [f"### {u}", "", "| Feld | Wert | Herkunft | Beleg |", "|---|---|---|---|"]
        for r in sorted(nach_mensch[u], key=lambda x: x["feld"]):
            md.append(f"| {r['feld']} | {r['wert']} | {r['herkunft']} | {r['beleg'] or ''} |")
        md.append("")
    md += ["## Zurueckgehalten", "",
           f"{len(zurueckgehalten)} Feld(er) -- nur DASS es sie gibt, NICHT der Wert:", "",
           "| Mensch | Feld | Herkunft | Grund |", "|---|---|---|---|"]
    for r in zurueckgehalten:
        md.append(f"| {r['user_id']} | {r['feld']} | {r['herkunft']} | {r['_grund']} |")
    md += ["", "## Eigentum vs. Urheberschaft", "",
           "`entityos_projekte` fuehrt `gehoert` (wem das Projekt gehoert) und `gebaut_von` "
           "(wer es gebaut hat) als GETRENNTE Spalten -- ein Projekt kann dem einen gehoeren "
           "und vom anderen gebaut sein (Beispiel: SeiMensch.net gehoert Andreas, Code von "
           "Gabriel). Siehe `PROJEKTE.md`.", ""]
    # Ueber schreibe_markdown(), damit auch diese Datei ihre Beipackdatei bekommt.
    # Sie war eine von genau zwei ohne -- ein Vertrag mit zwei Ausnahmen ist keiner.
    schreibe_markdown(ordner / "PROFILE.md", "\n".join(md) + "\n",
                      herkunft="entityos_profil + iar.frank.ink, redigiert fuer ein oeffentliches Repo")
    manifest["dateien"].append({"datei": "agentZero/menschen/PROFILE.md",
                                "freigegeben": len(freigegeben), "zurueckgehalten": len(zurueckgehalten)})

    # ── Projekte: Erfolg UND Misserfolg nebeneinander, Eigner-Auftrag ──────
    projekte = [dict(r) for r in c.execute(
        "SELECT projekt, gehoert, gebaut_von, stand, erfolg, seit_zero, beschreibung, beleg, herkunft, erfasst "
        "FROM entityos_projekte ORDER BY projekt")]
    ep = schreibe(ordner / "projekte.json", projekte, jsonl=False,
                 herkunft="entityos_projekte in UnifiedDB")
    manifest["dateien"].append(ep)

    md2 = ["# Projekte", "",
           f"Automatisch erzeugt {jetzt()}. {len(projekte)} Projekte -- Erfolge UND Fehlschlaege "
           "nebeneinander. Eigner-Auftrag: 'eine Projekttabelle, die nur Gelungenes fuehrt, ist "
           "ein Werbeblatt.'", "",
           "`gehoert` = wem das Projekt gehoert. `gebaut_von` = wer es gebaut hat -- **getrennt**, "
           "weil Besitz nicht Urheberschaft ist.", "",
           "| Projekt | gehoert | gebaut_von | Stand | Erfolg | seit Zero | Beschreibung |",
           "|---|---|---|---|---|---|---|"]
    for p in projekte:
        md2.append(f"| {p['projekt']} | {p['gehoert'] or '?'} | {p['gebaut_von'] or '?'} | "
                   f"{p['stand']} | {p['erfolg'] or '?'} | {'ja' if p['seit_zero'] else 'nein'} | "
                   f"{(p['beschreibung'] or '').replace('|', '/')} |")
    schreibe_markdown(ordner / "PROJEKTE.md", "\n".join(md2) + "\n",
                      herkunft="entityos_projekte -- Zugehoerigkeit und Urheberschaft getrennt gefuehrt")
    manifest["dateien"].append({"datei": "agentZero/menschen/PROJEKTE.md", "projekte": len(projekte)})

    # ── Zuordnung: NUR Aggregat -- 14284 Einzelzeilen dumpen waere kein Aggregat ──
    gesamt = c.execute("SELECT COUNT(*) FROM entityos_artikel_zuordnung").fetchone()[0]
    nach_gehoert = [dict(r) for r in c.execute(
        "SELECT gehoert, COUNT(*) AS anzahl, AVG(sicherheit) AS mittel_sicherheit "
        "FROM entityos_artikel_zuordnung GROUP BY gehoert ORDER BY anzahl DESC")]
    nach_grund = [dict(r) for r in c.execute(
        "SELECT grund, COUNT(*) AS anzahl, AVG(sicherheit) AS mittel_sicherheit "
        "FROM entityos_artikel_zuordnung GROUP BY grund ORDER BY anzahl DESC")]
    mittel_gesamt = c.execute("SELECT AVG(sicherheit) FROM entityos_artikel_zuordnung").fetchone()[0]
    histogramm = [dict(r) for r in c.execute(
        "SELECT CAST(MIN(sicherheit * 10, 9) AS INT) AS zehntel, COUNT(*) AS anzahl "
        "FROM entityos_artikel_zuordnung GROUP BY zehntel ORDER BY zehntel")]
    zuordnung = {
        "gesamt_artikel": gesamt,
        "nach_gehoert": nach_gehoert,
        "nach_grund": nach_grund,
        "mittlere_sicherheit": mittel_gesamt,
        "histogramm_sicherheit_zehntel": histogramm,
        "hinweis": ("NUR Aggregat -- keine der 14284 Einzelzuordnungen steht hier. Wer eine "
                   "Einzelzuordnung braucht, fragt die laufende UnifiedDB, nicht dieses Repo."),
    }
    ez = schreibe(ordner / "zuordnung.json", zuordnung, jsonl=False,
                 herkunft="entityos_artikel_zuordnung in UnifiedDB, AGGREGIERT -- keine Einzelzeilen",
                 felder=["gesamt_artikel", "nach_gehoert", "nach_grund", "mittlere_sicherheit",
                        "histogramm_sicherheit_zehntel"])
    manifest["dateien"].append(ez)
    manifest["menschen"] = {"profile_freigegeben": len(freigegeben),
                            "profile_zurueckgehalten": len(zurueckgehalten),
                            "projekte": len(projekte), "artikel_zugeordnet": gesamt}
    c.close()


def bilanz_erfolge(manifest: dict) -> None:
    """Erfolge UND Fehlschlaege seit Zero -- BEIDE Haelften oder keine.

    Eigner-Auftrag: eine Tabelle, die nur Gelungenes fuehrt, ist ein Werbeblatt.
    Quelle: entityos_erfolge, ueber clayverse/erfolge.py:bilanz() -- dieselbe
    Funktion, die auch Zero selbst befragt, nicht eine zweite Ableitung.

    ⚠️ Zero laeuft seit 2026-08-18 -- EINEM Tag. Jede seit_zero=1-Zeile stammt aus
    diesem einen Tag. Das steht hier oben in Fettschrift, nicht klein gedruckt unten --
    sonst liest sich eine Ein-Tage-Liste wie eine lange Erfolgsgeschichte.
    """
    ordner = ZIEL / "menschen"
    ordner.mkdir(parents=True, exist_ok=True)
    try:
        sys.path.insert(0, "/opt/entityos/the artefact")
        import importlib
        from clayverse import erfolge
        importlib.reload(erfolge)
    except Exception as e:
        manifest["dateien"].append({"datei": "agentZero/menschen/BILANZ.md",
                                    "_fehler": f"{type(e).__name__}: {e}"})
        return

    class _NurLeseHuelle:
        """bilanz() will nur ein Objekt mit .db.execute() -- mehr braucht es nicht,
        und diese Huelle kann nichts schreiben (verbindet sich read-only)."""
        pass

    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    huelle = _NurLeseHuelle()
    huelle.db = c
    try:
        b = erfolge.bilanz(huelle)
    except Exception as e:
        c.close()
        manifest["dateien"].append({"datei": "agentZero/menschen/BILANZ.md",
                                    "_fehler": f"{type(e).__name__}: {e}"})
        return
    c.close()

    if b.get("stand") == "NOCH_NICHT_ERFASST":
        manifest["dateien"].append({"datei": "agentZero/menschen/BILANZ.md",
                                    "hinweis": "entityos_erfolge noch nicht befuellt -- nichts exportiert"})
        return

    # entityos_erfolge ist Eigner-Text, nicht erfunden -- aber Eigner-Text kann
    # trotzdem einen privaten Rechnernamen nennen (f-blind zitiert woertlich eine
    # Testfrage "wem gehoert andreas-MACO?"). Das Repo ist OEFFENTLICH: derselbe
    # Rechnername-Schutz wie fuer die Baunotizen greift hier genauso, bevor
    # irgendetwas geschrieben wird.
    b = schwaerzen(_RECHNERNAME.sub("<GESCHWAERZT: Rechnername>", json.dumps(
        b, ensure_ascii=False, sort_keys=True)))
    b = json.loads(b)

    eb = schreibe(ordner / "bilanz.json", b, jsonl=False,
                 herkunft="entityos_erfolge in UnifiedDB, ueber clayverse/erfolge.py:bilanz()")
    manifest["dateien"].append(eb)

    def zeile(e):
        return (f"| {e['datum']} | {e['titel']} | {(e['wirkung'] or '').replace('|', '/')} | "
               f"{e['beleg'].replace('|', '/')} | {e['gehoert'] or '?'} | "
               f"{'ja' if e['seit_zero'] else 'nein'} |")

    md = ["# Bilanz -- Erfolge UND Fehlschlaege seit Zero", "",
          f"Automatisch erzeugt {jetzt()} aus `entityos_erfolge`.", "",
          f"> ⚠️ {b['zeitraum']}", "",
          f"> ⚠️ {b['warum_fehlschlaege']}", "",
          "Beide Haelften stehen hier gleichrangig: gleiche Tabellenform, gleiche Spalten, "
          "Erfolge zuerst nur weil das Alphabet so will -- keine Haelfte ist Fussnote der "
          "anderen. Eigner-Auftrag woertlich: eine Tabelle mit nur Gelungenem ist ein "
          "Werbeblatt.", "",
          f"## Erfolge ({len(b['erfolge'])})", "",
          "| Datum | Titel | Wirkung | Beleg | gehoert | seit Zero |",
          "|---|---|---|---|---|---|"]
    md += [zeile(e) for e in b["erfolge"]]
    md += ["", f"## Fehlschlaege ({len(b['fehlschlaege'])})", "",
          "| Datum | Titel | Wirkung | Beleg | gehoert | seit Zero |",
          "|---|---|---|---|---|---|"]
    md += [zeile(e) for e in b["fehlschlaege"]]
    md.append("")
    em = schreibe_markdown(ordner / "BILANZ.md", "\n".join(md) + "\n",
                           herkunft="entityos_erfolge in UnifiedDB, ueber clayverse/erfolge.py:bilanz()")
    manifest["dateien"].append({**em, "erfolge": len(b["erfolge"]), "fehlschlaege": len(b["fehlschlaege"])})
    manifest["bilanz"] = {"erfolge": len(b["erfolge"]), "fehlschlaege": len(b["fehlschlaege"])}


# ── Rechnernamen der zwei privaten Maschinen -- oeffentliches Repo, private Kisten ─
_RECHNERNAME = re.compile(r"andreas-MACO|ai-core-node(?:-[A-Za-z0-9]+)*", re.IGNORECASE)


# ── Leck-Muster fuer die Baunotizen-Stichprobe -- dasselbe Muster, mit dem   ─
# hinterher verifiziert wird. Ein Treffer wirft die GANZE Zeile aus der       │
# Stichprobe, nicht nur das Feld -- Zurueckhalten ist umkehrbar, eine         │
# veroeffentlichte Adresse nicht.                                            │
_BAUNOTIZ_LECK = re.compile(
    r"@gmail|@frank\.ink|andreas-MACO|ai-core-node|password|passwort|api[_-]?key"
    r"|[0-9]{1,3}(?:\.[0-9]{1,3}){3}"
    r"|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
    re.IGNORECASE,
)


def baunotizen_export(manifest: dict) -> None:
    """Baunotizen aus dem Wiki -- AGGREGAT + gepruefte Stichprobe, kein 2330-Zeilen-Dump.

    Quelle: artikel(art IN ('baunotiz','vorfall')), gefuellt von clayverse/baunotizen.py.

    ⚠️ Kein einziger Commit traegt eine 'Hypothese:'-Zeile -- hypothese/gegenhypothese
    werden NUR mechanisch aus einer Zeile im Muster '^Hypothese:' extrahiert, nie
    erfunden. Praktisch alle Zeilen haben deshalb hypothese=null. Das ist der Befund
    ueber den Bestand, kein Fehler in diesem Export -- siehe Modulkopf von baunotizen.py.

    ⚠️ artikel.herkunft ist CHECK-constrained auf ('gemessen','nutzer'). Alle Zeilen
    hier stehen mit herkunft=gemessen -- korrekt, das sind aufgezeichnete Fakten, keine
    Behauptung -- aber das sagt NICHTS ueber die Quellenart aus. Die steht stattdessen
    in von_quelle (git-commit | bauverlauf.jsonl | strom) und zusaetzlich, mit dem
    woertlichen Feldnamen, in metadaten.herkunft (JSON).

    ⚠️ PRIVATSPHAERE. Dieses Repo ist OEFFENTLICH. Commit-Texte koennen Zugangsdaten,
    IP-Adressen, Mailadressen oder Rechnernamen der zwei privaten Maschinen enthalten --
    zusaetzlich zur allgemeinen schwaerzen()-Schwaerzung wird jede Stichprobenzeile vor
    dem Schreiben gegen _BAUNOTIZ_LECK geprueft. Ein Treffer wirft die ganze Zeile raus.
    """
    ordner = ZIEL / "baunotizen"
    ordner.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row

    gesamt = c.execute(
        "SELECT COUNT(*) FROM artikel WHERE art IN ('baunotiz','vorfall')").fetchone()[0]
    if not gesamt:
        c.close()
        manifest["dateien"].append({"datei": "agentZero/baunotizen/",
                                    "hinweis": "keine Baunotizen in der artikel-Tabelle"})
        return

    nach_art = [dict(r) for r in c.execute(
        "SELECT art, COUNT(*) AS anzahl FROM artikel WHERE art IN ('baunotiz','vorfall') "
        "GROUP BY art ORDER BY anzahl DESC")]
    nach_quelle = [dict(r) for r in c.execute(
        "SELECT art, von_quelle, COUNT(*) AS anzahl FROM artikel "
        "WHERE art IN ('baunotiz','vorfall') GROUP BY art, von_quelle ORDER BY art, anzahl DESC")]
    zeitraum = dict(c.execute(
        "SELECT MIN(datum) AS von, MAX(datum) AS bis FROM artikel "
        "WHERE art IN ('baunotiz','vorfall')").fetchone())

    alle = c.execute(
        "SELECT metadaten FROM artikel WHERE art IN ('baunotiz','vorfall')").fetchall()
    mit_hyp = mit_gegenhyp = 0
    for r in alle:
        try:
            m = json.loads(r["metadaten"]) if r["metadaten"] else {}
        except Exception:
            m = {}
        if m.get("hypothese"):
            mit_hyp += 1
        if m.get("gegenhypothese"):
            mit_gegenhyp += 1

    # Stichprobe: juengste zuerst, aber nur was die Lecksuche uebersteht.
    kandidaten = c.execute(
        "SELECT id, art, titel, datum, metadaten, von_quelle FROM artikel "
        "WHERE art IN ('baunotiz','vorfall') ORDER BY datum DESC LIMIT 400").fetchall()
    c.close()

    stichprobe, verworfen = [], 0
    for r in kandidaten:
        if len(stichprobe) >= 25:
            break
        try:
            m = json.loads(r["metadaten"]) if r["metadaten"] else {}
        except Exception:
            m = {}
        titel = schwaerzen(r["titel"] or "")
        wieso = schwaerzen(m.get("wieso") or "")
        autor = schwaerzen(m.get("autor") or "")
        pruefblock = json.dumps([titel, wieso, autor, r["von_quelle"], r["id"]], ensure_ascii=False)
        if _BAUNOTIZ_LECK.search(pruefblock):
            verworfen += 1
            continue
        stichprobe.append({
            "id": r["id"], "art": r["art"], "datum": r["datum"], "von_quelle": r["von_quelle"],
            "titel": titel, "autor": autor, "wieso": wieso[:1500],
            "hypothese": m.get("hypothese"), "gegenhypothese": m.get("gegenhypothese"),
        })

    ej = schreibe(ordner / "aggregat.json", {
        "gesamt": gesamt, "nach_art": nach_art, "nach_von_quelle": nach_quelle,
        "zeitraum": zeitraum, "mit_hypothese": mit_hyp, "mit_gegenhypothese": mit_gegenhyp,
        "ohne_hypothese": gesamt - mit_hyp,
        "stichprobe_kandidaten_geprueft": len(kandidaten),
        "stichprobe_verworfen_wegen_privatsphaere": verworfen,
    }, jsonl=False, herkunft="artikel(art IN ('baunotiz','vorfall')) in UnifiedDB, AGGREGIERT")
    manifest["dateien"].append(ej)

    es = schreibe(ordner / "stichprobe-juengste25.jsonl", stichprobe, jsonl=True,
                 herkunft="artikel(art IN ('baunotiz','vorfall')), juengste zuerst, lecksuche-geprueft")
    manifest["dateien"].append(es)

    md = ["# Baunotizen -- Aggregat und Stichprobe", "",
          f"Automatisch erzeugt {jetzt()}. **{gesamt} Zeilen** insgesamt in `artikel` "
          "(art baunotiz/vorfall) -- hier NICHT als Volldump, sondern Aggregat plus die "
          "juengsten, lesbar aufbereitet und einzeln lecksuche-geprueft.", "",
          f"Zeitraum: `{zeitraum['von']}` bis `{zeitraum['bis']}`.", "",
          "## Nach Art", "", "| Art | Anzahl |", "|---|---|"]
    md += [f"| {r['art']} | {r['anzahl']} |" for r in nach_art]
    md += ["", "## Nach Quelle (`von_quelle`)", "", "| Art | von_quelle | Anzahl |", "|---|---|---|"]
    md += [f"| {r['art']} | {r['von_quelle']} | {r['anzahl']} |" for r in nach_quelle]
    md += ["",
          f"## Hypothese: {mit_hyp} von {gesamt} · Gegenhypothese: {mit_gegenhyp} von {gesamt}", "",
          "> ⚠️ **Kein einziger Commit seit dem Stichtag traegt eine `Hypothese:`-Zeile.** "
          "`hypothese`/`gegenhypothese` werden NUR aus einer Zeile im Muster `^Hypothese:` "
          "bzw. `^Gegenhypothese:` mechanisch extrahiert -- nie erfunden. Die Zahlen oben "
          "sind deshalb praktisch immer 0. Das ist der Befund ueber den Bestand, kein Fehler "
          "im Export.", "",
          "> ⚠️ **`artikel.herkunft` ist CHECK-constrained auf `('gemessen','nutzer')`.** "
          "Alle Zeilen hier stehen mit `herkunft=gemessen` -- korrekt, es sind aufgezeichnete "
          "Fakten aus Log/Git, keine Behauptung -- aber das sagt nichts ueber die QUELLENART "
          "aus. Die steht in `von_quelle` (`git-commit` | `bauverlauf.jsonl` | `strom`) und "
          "zusaetzlich in `metadaten.herkunft` im JSON.", "",
          "## Privatsphaere-Filter", "",
          f"Von **{len(kandidaten)}** gepruefte juengste Kandidaten wurden **{verworfen}** "
          "verworfen -- Treffer im Lecksuche-Muster (Mailadresse, IP-aehnliches Muster, "
          "Zugangsdaten-Schluesselwort, Rechnername einer der zwei privaten Maschinen). "
          "Verworfen heisst: die GANZE Zeile fehlt in der Stichprobe unten, nicht nur das "
          "betroffene Feld. Das Repo ist OEFFENTLICH.", "",
          f"## Die {len(stichprobe)} juengsten (gepruefte) Baunotizen", ""]
    for s in stichprobe:
        md += [f"### {s['titel'] or s['id']}", "",
              f"`{s['id']}` · {s['art']} · {s['von_quelle']} · {s['datum']}"
              + (f" · {s['autor']}" if s['autor'] else ""), "",
              f"Hypothese: {s['hypothese'] or '_(keine -- s.o.)_'} · "
              f"Gegenhypothese: {s['gegenhypothese'] or '_(keine -- s.o.)_'}", "",
              (s['wieso'] or '_(kein Text)_'), ""]
    em = schreibe_markdown(ordner / "UEBERSICHT.md", "\n".join(md) + "\n",
                           herkunft="artikel(art IN ('baunotiz','vorfall')) in UnifiedDB")
    manifest["dateien"].append({**em, "gesamt": gesamt, "stichprobe": len(stichprobe),
                                "verworfen": verworfen})
    manifest["baunotizen"] = {"gesamt": gesamt, "stichprobe": len(stichprobe), "verworfen": verworfen}


def wissensartikel(manifest: dict) -> None:
    """Wissensartikel -- Betriebs- und Personenwissen, geheimnisfrei aus der Eigner-CLAUDE.md.

    Quelle: artikel(art='wissen', projekt='EntityOS') in der UnifiedDB, gefuellt von
    clayverse/wissen.py. Jede Zeile traegt metadaten.geheimnisfrei=true als Selbstauskunft
    des Quellprozesses -- diese Funktion verlaesst sich NICHT allein darauf, sondern
    schwaerzt zusaetzlich wie jeder andere Export, und laesst jede Zeile OHNE das Feld
    einfach draussen (Zurueckhalten ist umkehrbar, ein veroeffentlichter Satz nicht).

    ⚠️ Personenwissen nennt zwei echte Menschen -- deshalb laeuft jeder Text zusaetzlich
    durch _RECHNERNAME (dieselbe Sperre, die menschen/BILANZ.md schon schuetzt): 'geheimnisfrei'
    heisst kein API-Schluessel, sagt aber nichts ueber Rechnernamen der zwei privaten Maschinen.
    """
    ordner = ZIEL / "wissen"
    ordner.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT id, titel, projekt, sphaere, datum, quelle, metadaten FROM artikel "
        "WHERE art='wissen' ORDER BY id").fetchall()
    c.close()

    def saeubern(txt):
        return schwaerzen(_RECHNERNAME.sub("<GESCHWAERZT: Rechnername>", txt or ""))

    zeilen, ohne_freigabe = [], 0
    for r in rows:
        try:
            m = json.loads(r["metadaten"]) if r["metadaten"] else {}
        except Exception:
            m = {}
        if not m.get("geheimnisfrei"):
            ohne_freigabe += 1
            continue
        zeilen.append({
            "id": r["id"], "titel": saeubern(r["titel"]),
            "projekt": r["projekt"], "sphaere": r["sphaere"], "datum": r["datum"],
            "quelle": saeubern(r["quelle"]),
            "herkunft": m.get("herkunft"), "wieso": saeubern(m.get("wieso")),
            "gehoert_zu": saeubern(m.get("gehoert_zu")),
            "hypothese": m.get("hypothese"), "gegenhypothese": m.get("gegenhypothese"),
            "text": saeubern(m.get("text")),
        })

    ej = schreibe(ordner / "artikel.jsonl", zeilen, jsonl=True,
                 herkunft="artikel(art='wissen') in UnifiedDB, gefuellt von clayverse/wissen.py")
    manifest["dateien"].append(ej)

    md = ["# Wissensartikel", "",
          f"Automatisch erzeugt {jetzt()}. {len(zeilen)} Artikel -- Betriebswissen "
          "(wie deployt wird, Domains, Testpflicht) und Personenwissen (Rollen, wer "
          "entscheidet, wo Geheimnisse liegen) aus der gitignorierten Eigner-CLAUDE.md, "
          "geheimnisfrei uebertragen durch `clayverse/wissen.py`.", ""]
    if ohne_freigabe:
        md += [f"> ⚠️ {ohne_freigabe} Zeile(n) ohne `geheimnisfrei=true` -- zurueckgehalten, "
              "nicht exportiert.", ""]
    for z in zeilen:
        md += [f"## {z['titel']}", "",
              f"`{z['id']}` · {z['projekt']}/{z['sphaere']} · {z['datum']}", "",
              f"**Wieso:** {z['wieso']}", "",
              f"**Gehoert zu:** {z['gehoert_zu']}", "",
              z["text"], ""]
    em = schreibe_markdown(ordner / "WISSEN.md", "\n".join(md) + "\n",
                           herkunft="artikel(art='wissen') in UnifiedDB")
    manifest["dateien"].append({**em, "artikel": len(zeilen), "ohne_freigabe": ohne_freigabe})
    manifest["wissen"] = {"artikel": len(zeilen), "ohne_freigabe": ohne_freigabe}


def verdichtungen(manifest: dict) -> None:
    """Verdichtungen -- Bauverlauf komprimiert zu Kurzartikeln, MIT Kompressionszahl.

    Quelle: artikel(art='verdichtung') in der UnifiedDB, gefuellt von
    clayverse/wikiverdichtung.py aus Gruppen von Baunotizen (metadaten.quellnotizen).

    ⚠️ 'Verdichtung' ist eine Behauptung, kein Etikett. Jede Zeile traegt
    metadaten.kompression = {zeichen_artikel, zeichen_quellen, verhaeltnis}. Ein
    Verhaeltnis < 1 heisst: der Artikel ist LAENGER als die Summe seiner Quellen --
    keine Verdichtung, eine Ausweitung. Dieser Export zeigt beide Faelle nebeneinander,
    denn eine Kompression, die ihren Input nicht schrumpft, ist eine Kopie.
    """
    ordner = ZIEL / "verdichtungen"
    ordner.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT id, titel, datum, metadaten FROM artikel WHERE art='verdichtung' "
        "ORDER BY datum DESC").fetchall()
    c.close()

    gesamt = len(rows)
    if not gesamt:
        manifest["dateien"].append({"datei": "agentZero/verdichtungen/",
                                    "hinweis": "keine Verdichtungen in der artikel-Tabelle"})
        return

    geparst = []
    for r in rows:
        try:
            m = json.loads(r["metadaten"]) if r["metadaten"] else {}
        except Exception:
            m = {}
        geparst.append((r, m))

    za_summe = zq_summe = expansion = 0
    verhaeltnisse = []
    nach_erzeuger: dict = {}
    for r, m in geparst:
        k = m.get("kompression") or {}
        za, zq = k.get("zeichen_artikel"), k.get("zeichen_quellen")
        if isinstance(za, int) and isinstance(zq, int) and za > 0:
            za_summe += za
            zq_summe += zq
            verh = zq / za
            verhaeltnisse.append(verh)
            if verh < 1.0:
                expansion += 1
        erz = m.get("erzeugt_von") or "?"
        nach_erzeuger[erz] = nach_erzeuger.get(erz, 0) + 1
    verhaeltnisse.sort()

    aggregat = {
        "gesamt": gesamt,
        "zeichen_artikel_summe": za_summe,
        "zeichen_quellen_summe": zq_summe,
        "gesamtverhaeltnis_quellen_je_artikel": round(zq_summe / za_summe, 3) if za_summe else None,
        "mittleres_verhaeltnis_je_zeile": (round(sum(verhaeltnisse) / len(verhaeltnisse), 3)
                                           if verhaeltnisse else None),
        "min_verhaeltnis": round(verhaeltnisse[0], 3) if verhaeltnisse else None,
        "max_verhaeltnis": round(verhaeltnisse[-1], 3) if verhaeltnisse else None,
        "zeilen_ausgeweitet_statt_verdichtet": expansion,
        "nach_erzeuger": nach_erzeuger,
        "hinweis": ("verhaeltnis = zeichen_quellen / zeichen_artikel. > 1 heisst echte "
                    "Verdichtung (Quellen groesser als Artikel). < 1 heisst Ausweitung: "
                    f"{expansion} von {gesamt} Zeilen "
                    f"({round(100 * expansion / gesamt) if gesamt else 0} %) sind laenger "
                    "als ihre eigenen Quellen."),
    }
    ea = schreibe(ordner / "aggregat.json", aggregat, jsonl=False,
                 herkunft="artikel(art='verdichtung') in UnifiedDB, AGGREGIERT")
    manifest["dateien"].append(ea)

    # Verdichtungstexte fassen Baunotizen zusammen -- dieselbe Rechnername-Sperre wie bei
    # menschen/ und baunotizen/, denn eine Verdichtung kann woertlich zitieren.
    def saeubern(txt):
        return schwaerzen(_RECHNERNAME.sub("<GESCHWAERZT: Rechnername>", txt or ""))

    juengste = []
    for r, m in geparst[:15]:
        juengste.append({
            "id": r["id"], "titel": saeubern(r["titel"]), "datum": r["datum"],
            "thema": m.get("thema"), "tag": m.get("tag"),
            "erzeugt_von": m.get("erzeugt_von"), "modell": m.get("modell"),
            "notizen_in_gruppe": m.get("notizen_in_gruppe"),
            "quellnotizen": m.get("quellnotizen") or [],
            "kompression": m.get("kompression"),
            "hypothese": m.get("hypothese"), "gegenhypothese": m.get("gegenhypothese"),
            "text": saeubern(m.get("text")),
        })
    ej = schreibe(ordner / "juengste15.jsonl", juengste, jsonl=True,
                 herkunft="artikel(art='verdichtung') in UnifiedDB, 15 juengste nach datum")
    manifest["dateien"].append(ej)

    md = ["# Verdichtungen", "",
          f"Automatisch erzeugt {jetzt()}. **{gesamt} Verdichtungen** fassen Baunotizen-Gruppen "
          "zu Kurzartikeln zusammen (`clayverse/wikiverdichtung.py`). Jede Zeile traegt ihre "
          "eigene Kompressionszahl -- eine gemessene, keine geschaetzte.", "",
          "## Kompression, gesamt", "",
          f"- Quellenzeichen gesamt: **{zq_summe}** · Artikelzeichen gesamt: **{za_summe}**",
          f"- **Gesamtverhaeltnis: {aggregat['gesamtverhaeltnis_quellen_je_artikel']}x** "
          "(Quellen je Artikelzeichen, ueber den ganzen Bestand)",
          f"- Mittleres Verhaeltnis je Zeile: {aggregat['mittleres_verhaeltnis_je_zeile']}x "
          f"(min {aggregat['min_verhaeltnis']}x, max {aggregat['max_verhaeltnis']}x)",
          f"- Nach Erzeuger: " + ", ".join(f"{k}={v}" for k, v in nach_erzeuger.items()), "",
          f"> ⚠️ **{expansion} von {gesamt} Zeilen ({round(100 * expansion / gesamt) if gesamt else 0} %) "
          "sind LAENGER als ihre eigenen Quellen** -- Verhaeltnis < 1, also Ausweitung statt "
          "Verdichtung. Das ist kein Darstellungsfehler dieses Exports, sondern ein Befund ueber "
          "den Mechanismus: mechanisch erzeugte Gruppentexte (Beispieltitel-Aufzaehlung) koennen "
          "laenger geraten als sehr kurze Rohnotizen.", "",
          f"## Die {len(juengste)} juengsten Verdichtungen (voller Text)", ""]
    for j in juengste:
        k = j["kompression"] or {}
        md += [f"### {j['titel'] or j['id']}", "",
              f"`{j['id']}` · {j['tag']} · {j['thema']} · {j['erzeugt_von']}"
              + (f" ({j['modell']})" if j.get("modell") else ""), "",
              f"Verhaeltnis: **{k.get('verhaeltnis')}x** "
              f"({k.get('zeichen_quellen')} Quellenzeichen -> {k.get('zeichen_artikel')} "
              "Artikelzeichen) · "
              f"{j['notizen_in_gruppe']} Quellnotizen: "
              + ", ".join(f"`{q}`" for q in j["quellnotizen"][:12]), "",
              (j["text"] or "_(kein Text)_"), ""]
    em = schreibe_markdown(ordner / "VERDICHTUNGEN.md", "\n".join(md) + "\n",
                           herkunft="artikel(art='verdichtung') in UnifiedDB")
    manifest["dateien"].append({**em, "gesamt": gesamt, "juengste_voll": len(juengste),
                                "gesamtverhaeltnis": aggregat["gesamtverhaeltnis_quellen_je_artikel"],
                                "ausgeweitet": expansion})
    manifest["verdichtungen"] = {"gesamt": gesamt,
                                 "gesamtverhaeltnis": aggregat["gesamtverhaeltnis_quellen_je_artikel"],
                                 "ausgeweitet": expansion}


def tresor_kataloge(manifest: dict) -> None:
    """Tresor-Kataloge -- WAS es an Zugaengen gibt und was sie koennen, NIE der Wert.

    Quelle: clayverse/tresor.py:katalog() fuer die zwei Tresore 'api' und 'zugaenge'.
    katalog() ist die EINZIGE Funktion dieses Moduls, die dieser Export je aufruft --
    oeffnen()/wert() liefern Klartext und werden hier NIE aufgerufen. katalog() prueft
    sein eigenes Ergebnis mechanisch gegen jeden gelagerten Wert, bevor es ihn
    herausgibt; dieser Export prueft zusaetzlich von aussen (Notbremse), weil eine
    einzelne Sicherung keine ist.
    """
    ordner = ZIEL / "tresor"
    ordner.mkdir(parents=True, exist_ok=True)
    try:
        sys.path.insert(0, "/opt/entityos/the artefact")
        import importlib
        from clayverse import tresor
        importlib.reload(tresor)
    except Exception as e:
        manifest["dateien"].append({"datei": "agentZero/tresor/", "_fehler": f"{type(e).__name__}: {e}"})
        return

    # Notbremse von aussen -- unabhaengig von katalog()s eigener Pruefung.
    AUSSEN_MUSTER = re.compile(
        r"sk-[A-Za-z0-9]{10,}|gsk_[A-Za-z0-9]{6,}|hf_[A-Za-z0-9]{10,}|Bearer\s|"
        r"AIza[A-Za-z0-9_-]{20,}|eyJ[A-Za-z0-9_-]{20,}|[A-Za-z0-9]{28,}")

    kataloge, verworfen = {}, []
    for name in ("api", "zugaenge"):
        try:
            k = tresor.katalog(name)
        except Exception as e:
            kataloge[name] = {"_fehler": f"{type(e).__name__}: {e}"}
            continue
        text = json.dumps(k, ensure_ascii=False)
        if AUSSEN_MUSTER.search(text):
            verworfen.append(name)
            continue
        kataloge[name] = k

    ej = schreibe(ordner / "kataloge.json", kataloge, jsonl=False,
                 herkunft="clayverse/tresor.py:katalog('api'|'zugaenge') -- NIE oeffnen()/wert()",
                 felder=["api", "zugaenge"])
    manifest["dateien"].append(ej)

    md = ["# Tresor-Kataloge", "",
          f"Automatisch erzeugt {jetzt()}. Zwei AES-256-GCM-Tresore unter "
          "`/etc/entityos/tresor` -- `katalog()` zeigt WAS es gibt und WAS es KANN "
          "(Modell, Limits je Minute/Tag, Zweck), nie den Wert selbst. `oeffnen()`/`wert()` "
          "liefern den Klartext und werden von diesem Export nie aufgerufen.", ""]
    if verworfen:
        md += [f"> ⚠️ {len(verworfen)} Tresor(e) verworfen -- Katalogtext bestand die Notbremse "
              f"nicht: {', '.join(verworfen)}.", ""]
    for name, k in kataloge.items():
        if "_fehler" in k:
            md += [f"## {name}", "", f"_Fehler: {k['_fehler']}_", ""]
            continue
        md += [f"## {name} ({k['anzahl']} Eintraege)", "",
              "| Kennung | Art/Anbieter | Zweck | Quelle | Sonstiges |",
              "|---|---|---|---|---|"]
        for e in k["eintraege"]:
            fae = e.get("faehigkeiten")
            if isinstance(fae, list):
                sonstiges = "; ".join(
                    f"{f.get('zugang', '?')}: {f.get('modell') or '-'} "
                    f"({f.get('minute_limit') or '-'}/min, {f.get('tag_limit') or '-'}/Tag)"
                    for f in fae)
            elif fae:
                sonstiges = str(fae)
            else:
                flags = []
                if "geheim" in e:
                    flags.append("geheim" if e["geheim"] else "nicht geheim")
                if "oeffentlich" in e:
                    flags.append("oeffentlich" if e["oeffentlich"] else "nicht oeffentlich")
                sonstiges = ", ".join(flags)
            md.append(f"| {e.get('kennung', '?')} | {e.get('anbieter') or e.get('art', '?')} | "
                      f"{e.get('zweck') or ''} | {e.get('quelle') or ''} | {sonstiges[:200]} |")
        md.append("")
    em = schreibe_markdown(ordner / "TRESOR.md", "\n".join(md) + "\n",
                           herkunft="clayverse/tresor.py:katalog()")
    manifest["dateien"].append({**em, "tresore": list(kataloge.keys()), "verworfen": verworfen})
    manifest["tresor"] = {"tresore": len(kataloge), "verworfen": len(verworfen)}


def wegehierarchie_export(manifest: dict) -> None:
    """F94 Wegehierarchie -- Verdikt und Verteilung, WOERTLICH auch wenn es 'zu wenig' sagt.

    Quelle: udb/abruf/wegehierarchie.py:pruefung()/lage() gegen dieselbe UnifiedDB.
    Bei weniger als zehn Wegen liefert pruefung() bewusst KEIN Urteil ueber
    Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung:
    ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht
    pruefbar. Dieser Export wartet NICHT auf eine groessere Zahl.
    """
    ordner = ZIEL / "abruf"
    ordner.mkdir(parents=True, exist_ok=True)
    try:
        sys.path.insert(0, "/opt/unifieddb")
        import importlib
        from udb.abruf import wegehierarchie as wh
        importlib.reload(wh)
    except Exception as e:
        manifest["dateien"].append({"datei": "agentZero/abruf/wegehierarchie.json",
                                    "_fehler": f"{type(e).__name__}: {e}"})
        return

    class _NurLeseHuelle:
        pass

    c = sqlite3.connect(f"file:{DB}?mode=ro", uri=True, timeout=60)
    c.row_factory = sqlite3.Row
    huelle = _NurLeseHuelle()
    huelle.db = c
    try:
        pruefung = wh.pruefung(huelle)
        lage = wh.lage(huelle)
    except Exception as e:
        c.close()
        manifest["dateien"].append({"datei": "agentZero/abruf/wegehierarchie.json",
                                    "_fehler": f"{type(e).__name__}: {e}"})
        return
    c.close()

    ausgabe = {"erzeugt": jetzt(), "pruefung": pruefung, "lage": lage}
    ej = schreibe(ordner / "wegehierarchie.json", ausgabe, jsonl=False,
                 herkunft="udb/abruf/wegehierarchie.py:pruefung()+lage() gegen vp_weg in UnifiedDB")
    manifest["dateien"].append(ej)

    md = ["# Wegehierarchie (F94)", "",
          f"Automatisch erzeugt {jetzt()} aus `udb/abruf/wegehierarchie.py`.", "",
          "## Verdikt", "",
          f"> **{pruefung.get('urteil')}**", "",
          pruefung.get("hinweis", ""), "",
          f"Wege gesamt: **{pruefung.get('wege')}**", ""]
    if "raenge" in pruefung:
        md += ["## Verteilung nach Rang", "", "| Rang | Anzahl |", "|---|---|"]
        for rang_, n in pruefung["raenge"].items():
            md.append(f"| {rang_} | {n} |")
        md += ["", f"Oberes Zehntel haelt {pruefung.get('oberes_zehntel_haelt')} der Gesamtguete "
              f"(bei Gleichverteilung waeren es {pruefung.get('bei_gleichverteilung')}).", ""]
    if lage.get("wege"):
        md += ["## Staerkste Wege", "",
              "| von | nach | Art | Rang | Guete | Nutzung | getragen |",
              "|---|---|---|---|---|---|---|"]
        for w in lage["wege"]:
            md.append(f"| {w['von']} | {w['nach']} | {w['art']} | {w['rang']} | "
                      f"{w['guete']} | {w['nutzung']} | {w['getragen']} |")
        md.append("")
    md += ["## Warum das Verdikt so bleibt, wie es ist", "",
          "`pruefung()` liefert bei weniger als zehn Wegen bewusst KEIN Urteil ueber "
          "Hierarchiebildung -- das ist die im Modulkopf selbst genannte Falsifikationspruefung: "
          "ein Mechanismus, der seine eigene Datenknappheit nicht anzeigen kann, ist nicht "
          "pruefbar. Dieser Export wartet nicht auf eine groessere Zahl, sondern zeigt den "
          "aktuellen Stand so, wie er ist.", ""]
    em = schreibe_markdown(ordner / "WEGEHIERARCHIE.md", "\n".join(md) + "\n",
                           herkunft="udb/abruf/wegehierarchie.py")
    manifest["dateien"].append({**em, "wege": pruefung.get("wege"), "urteil": pruefung.get("urteil")})
    manifest["wegehierarchie"] = {"wege": pruefung.get("wege"), "urteil": pruefung.get("urteil")}


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
    profile_und_zuordnung(manifest)
    bilanz_erfolge(manifest)
    baunotizen_export(manifest)
    wissensartikel(manifest)
    verdichtungen(manifest)
    tresor_kataloge(manifest)
    wegehierarchie_export(manifest)
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
| `abruf/` | was die Abruf-Entitaet tut: Episoden, gelernte Eintrittspunkte, Rueckmeldungen, plus **F94-Wegehierarchie** (`wegehierarchie.json`/`WEGEHIERARCHIE.md`) -- Verdikt und Verteilung, auch wenn das Verdikt "zu wenige Wege" heisst |
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
| `menschen/` | **Profile der zwei Menschen hinter Zero, redigiert** (nur `iar.frank.ink` + gepruefte Ausnahmen), Projekttabelle mit Erfolg UND Fehlschlag, Artikelzuordnung NUR als Aggregat, **Bilanz** (`BILANZ.md`) mit Erfolgen UND Fehlschlaegen seit Zero, gleichrangig -- Repo ist oeffentlich, Details siehe `menschen/PROFILE.md` |
| `baunotizen/` | **Aggregat der Bauaufzeichnungen** aus dem Wiki (art baunotiz/vorfall), plus eine lecksuche-gepruefte Stichprobe der juengsten -- kein Volldump von 2330+ Zeilen |
| `wissen/` | **Betriebs- und Personenwissen** aus der gitignorierten Eigner-CLAUDE.md, geheimnisfrei uebertragen (`clayverse/wissen.py`) -- nur Zeilen mit `geheimnisfrei=true` |
| `verdichtungen/` | **Bauverlauf, verdichtet zu Kurzartikeln** (`clayverse/wikiverdichtung.py`), MIT gemessenem Kompressionsverhaeltnis je Zeile und im Aggregat -- inklusive der Zeilen, die ihren Input NICHT geschrumpft haben |
| `tresor/` | **Zwei Tresor-Kataloge** (`clayverse/tresor.py:katalog()`): WAS es an API-Zugaengen/Anmeldungen gibt und was sie koennen (Modell, Limits, Zweck) -- NIE ein Wert |
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
