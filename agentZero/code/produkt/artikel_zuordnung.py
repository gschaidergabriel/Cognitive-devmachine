"""Artikel nach Mensch zuordnen -- aus den Metadaten, nicht aus dem Bauchgefuehl.

Der Eignerauftrag: alle Wiki-Artikel zusaetzlich in andreas / gabriel / gemeinsam
kategorisieren, "das geht ueber die metadaten wo die daten innerhalb des artikels
herkommen".

⚠️ DIE FALLE, DIE HIER GEMESSEN WURDE UND UMGANGEN WIRD

Das naheliegendste Feld ist `zuletzt_von` -- und es ist das falsche. Gemessen:

    8880 Artikel  zuletzt_von="Gabriel Gschaider"  projekt=clay-global-research-entity
     501 Artikel  zuletzt_von="Gabriel Gschaider"  projekt=Dr.-Unterweger

Die zweite Zeile ist der Beweis. 501 Artikel aus ANDREAS' Material tragen GABRIELS
Namen als Bearbeiter. Haette ich nach `zuletzt_von` zugeordnet, waeren 9751 von
14284 Artikeln (68 %) an Gabriel gegangen -- darunter Andreas' gesamter Bestand.
Das ist exakt die Regel, die der Eigner selbst benannt hat:

    "seimensch ist das projekt von andreas aber allen code habe ich gemacht"

Urheberschaft ist nicht Zugehoerigkeit. `zuletzt_von` wird deshalb NICHT als
Zuordnungssignal verwendet -- in keiner Stufe.

DIE LEITER (jede Stufe traegt ihre Sicherheit mit)

  1  sphaere ist ausdruecklich gesetzt         0.95   erklaerte Zuordnung
  2  projekt ist personengebunden              0.90   Dr.-Unterweger -> andreas
  3  Frank-Familie                             0.75   abgeleitet ueber das Projekt
  4  Institutsrepos                            0.60   beide Gruender, IAR
  5  alles andere                       unbekannt     KEINE Zuordnung

Stufe 5 ist die wichtigste. Ein Artikel ohne Signal bleibt `unbekannt` statt an
den wahrscheinlicheren Menschen zu fallen. Eine geratene Zuordnung sieht in der
Tabelle genauso aus wie eine belegte -- und waere in einem System, das
Cross-user-Trennung durchsetzt, eine stille Rechteverschiebung.
"""
from __future__ import annotations
import time

# Stufe 1: ausdrueckliche Sphaere
SPHAERE = {"andreas": "andreas", "gabriel": "gabriel"}

# Stufe 2: personengebundene Projekte
PERSOENLICH = {
    "Dr.-Unterweger": "andreas", "andreas-claude": "andreas", "Andreas-Resercher": "andreas",
    "Project-Frankenstein": "gabriel", "gabriel-claude": "gabriel",
}

# Stufe 3: Frank-Familie -- Project Frankenstein ist Gabriels Projekt (Eigner 18.08.),
# diese Baeume gehoeren inhaltlich dazu.
FRANK = {
    "digital-retina": "Ziel-VPS von Frank v0.1",
    "frank-demo": "Demomaterial zu Frank",
    "daemonweave": "traegt frank-metacognition/soma-personal-mode",
    "retina": "Retina, Frank-Umfeld",
}
FRANK_SPHAERE = "frank_v0_1"

# Stufe 4: Institutsrepos -- beide Gruender, beide ehrenamtlich, IAR.
INSTITUT = {
    "clay-global-research-entity": "Forschungsentitaet des Instituts",
    "iar": "das Institut selbst", "clay": "Clay-Unterbau",
    "clayverse-bau": "Aufbau", "clayverse-strom": "Aufbau", "kartographie": "Aufbau",
    "agentic-density-battery": "Institutsforschung", "agentic-grid": "Institutsforschung",
    "lcme": "Institutsforschung", "persona-engine-framework": "Institutsforschung",
    "qgolpu": "Institutsforschung", "roboart": "Institutsforschung",
    "Identity-Collapse-Detection-Engine": "Institutsforschung",
    "video-launch-page": "Aussendarstellung",
    "agentforge": "Plattform, traegt SeiMensch (andreas), gebaut von gabriel -- geteilte Infrastruktur",
    "EntityOS": "Institutsrepo, beide Gruender -- die Baunotizen (clayverse/baunotizen.py: "
                "protokoll.jsonl/bauverlauf.jsonl/git-commits) setzen projekt='EntityOS'.",
}
INSTITUT_SPHAEREN = {"clayverse": "Aufbau", "iar": "das Institut selbst"}


def _entscheide(sphaere, projekt):
    s = (sphaere or "").strip()
    p = (projekt or "").strip()
    if s in SPHAERE:
        return SPHAERE[s], f"sphaere={s} ausdruecklich gesetzt", 0.95
    if p in PERSOENLICH:
        return PERSOENLICH[p], f"projekt={p} ist personengebunden", 0.90
    if s == FRANK_SPHAERE or p in FRANK:
        grund = FRANK.get(p, "sphaere=frank_v0_1")
        return "gabriel", f"Frank-Familie: {grund} (Project Frankenstein gehoert gabriel)", 0.75
    if p in INSTITUT:
        return "gemeinsam", f"Institutsrepo: {INSTITUT[p]}", 0.60
    if s in INSTITUT_SPHAEREN:
        return "gemeinsam", f"Institutsrepo: {INSTITUT_SPHAEREN[s]}", 0.60
    # Kein Signal. NICHT raten -- siehe Modulkopf.
    return "unbekannt", f"kein Zuordnungssignal (projekt={p or '-'}, sphaere={s or '-'})", 0.0


def zuordnen(db, *, nur_zaehlen: bool = False) -> dict:
    zeilen, verteilung, sicher = [], {}, []
    for r in db.db.execute("SELECT id, sphaere, projekt FROM artikel"):
        gehoert, grund, sicherheit = _entscheide(r["sphaere"], r["projekt"])
        verteilung[gehoert] = verteilung.get(gehoert, 0) + 1
        sicher.append(sicherheit)
        zeilen.append((str(r["id"]), gehoert, grund, sicherheit, time.time()))
    if not nur_zaehlen:
        with db.tx() as sql:
            sql.executemany(
                "INSERT INTO entityos_artikel_zuordnung(artikel_id,gehoert,grund,sicherheit,erfasst)"
                " VALUES(?,?,?,?,?) ON CONFLICT(artikel_id) DO UPDATE SET"
                " gehoert=excluded.gehoert, grund=excluded.grund,"
                " sicherheit=excluded.sicherheit, erfasst=excluded.erfasst", zeilen)
    return {
        "artikel": len(zeilen),
        "verteilung": dict(sorted(verteilung.items(), key=lambda x: -x[1])),
        "mittlere_sicherheit": round(sum(sicher) / max(1, len(sicher)), 3),
        "ohne_signal": verteilung.get("unbekannt", 0),
    }


def bestand(db, user_id: str) -> dict:
    """Wie viel des Wikis gehoert diesem Menschen -- fuer den Sitzungsvorspann."""
    try:
        r = db.db.execute(
            "SELECT gehoert, COUNT(*) n FROM entityos_artikel_zuordnung"
            " WHERE gehoert IN (?, 'gemeinsam') GROUP BY gehoert", (user_id,)).fetchall()
    except Exception:
        return {}
    return {x["gehoert"]: x["n"] for x in r}
