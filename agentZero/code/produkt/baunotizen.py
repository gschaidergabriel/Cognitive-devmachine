"""Baunotizen -- alle Bauaufzeichnungen als Wiki-Artikel, mit voller Herkunft.

Eignerauftrag woertlich (18.08.): "alle deine baunotizen werden auch teil des
wiki und mit alle meine ich alle mit metadaten und alles". Metadaten-Pflicht
dazu, woertlich: herkunft, wieso es gebaut wurde, wo es dazu gehoert,
hypothesen, gegenhypothesen, timestamp -- alles.

DREI QUELLEN, DREI BEHANDLUNGEN
--------------------------------

1. protokoll.jsonl (/opt/clayverse/bau/protokoll.jsonl) -- art='vorfall' ist
   HIER SCHON VERGEBEN. Eine andere, bestehende Pipeline (clayverse/werkzeug/
   wiki.py, ausserhalb DIESES Repos, build_vorfall()) fuellt diese Zeilen
   schon -- mit eigener, komplexer Feld-Ableitung (projekt/sphaere/zuletzt_von
   je nach Quelle unterschiedlich; gemessen 18.08.: 47/63 vorhandene Zeilen
   projekt=clayverse-bau, Rest NULL, 19 verschiedene zuletzt_von-Werte, nicht
   aus den Metadaten ablesbar). Dieses Modul repliziert deshalb NUR das
   ID-Schema jener Pipeline (aus ihrem Quellcode gelesen, nicht geraten:
   slugify(f"{bauteil}-{zeit}") mit -1/-2/…-Suffix bei Kollision, in
   Dateireihenfolge) und schreibt NIE in eine ID, die schon existiert --
   Luecken auffuellen, nicht ueberschreiben. Wer eine Zeile zuerst schreibt,
   besitzt sie. Damit "STALE. Fix." ohne Kollision mit der fremden Pipeline.

2. bauverlauf.jsonl (/opt/agentzero-export/repo/agentZero/bauverlauf/
   bauverlauf.jsonl) -- kein bestehender art-Wert dafuer. Bekommt
   art='baunotiz', projekt='EntityOS', sphaere='entityos' (Eigner-Vorgabe).

3. Git-Commits in DIESEM Repo (/opt/entityos/the artefact) -- ab GIT_CUTOFF
   (Eigner-Vorgabe: der Ausschnitt, der zaehlt; die volle Historie beginnt am
   2026-08-08 mit >12000 Commits, das waere kein "Ausschnitt" mehr). Ebenfalls
   art='baunotiz', projekt='EntityOS', sphaere='entityos'. Die lange
   Commit-Nachricht IST die Baunotiz -- volle Begruendung, Hypothese,
   gemessene Belege, verbatim uebernommen, nicht zusammengefasst.

DIE HERKUNFT-FALLE (gemessen, nicht geraten)
---------------------------------------------
artikel.herkunft ist CHECK-constrained auf ('gemessen','nutzer') -- ALLE
14284 Bestandszeilen sind 'gemessen', 'nutzer' kommt nirgends vor. Ein
INSERT mit herkunft='git-commit' schlaegt mechanisch fehl (IntegrityError,
selbst getestet). Geloest: artikel.herkunft bleibt 'gemessen' -- das stimmt
auch inhaltlich, es sind aufgezeichnete Fakten aus Log/Git, keine Behauptung.
Die Quellenart (das, was der Eigner mit "herkunft" meint) steht STATTDESSEN
in von_quelle (git-commit | protokoll.jsonl | bauverlauf.jsonl -- Spalte ohne
CHECK, im Bestand fuer sowas schon verwendet: 'strom'/'git'/'beleg-byline')
UND zusaetzlich, mit dem woertlichen Feldnamen des Eigners, in
metadaten.herkunft (JSON, durchsuchbar). Beides zeigt auf dieselbe Wahrheit.

NIE ERFUNDEN
------------
hypothese/gegenhypothese werden NUR gesetzt, wenn der Quelltext eine Zeile im
Muster "^Hypothese:" bzw. "^Gegenhypothese:" enthaelt -- mechanische
Extraktion, keine Interpretation. Gemessen (18.08.): kein einziger Commit seit
GIT_CUTOFF traegt so eine Zeile; "Hypothese"/"Gegenhypothese" kommen nur als
Fliesstext vor (z. B. "52 unverifizierte Gegenhypothesen"). ohne_hypothese
wird deshalb bei praktisch jeder neuen Zeile mitzaehlen -- das ist der Befund
ueber den Bestand, kein Bug im Extraktor. Eine geratene Hypothese waere Gift
in einem Forschungswiki: sie sieht identisch aus wie eine belegte.

IDEMPOTENZ
----------
Jede Quelle hat eine deterministische id (git: Commit-SHA direkt -- SHA IST
schon ein Inhalts-Hash, ein Commit kann sich nicht "aendern" ohne eine neue
SHA zu bekommen, darum bei git realistisch nie "aktualisiert", nur "neu" oder
"uebersprungen"; bauverlauf: Hash aus commit+zeit als Identitaet, quell_hash
separat aus der Rohzeile fuer echte Aenderungserkennung; protokoll: das
fremde slugify-Schema, insert-only). Zweiter Lauf mit unveraendertem Quelltext
= neu 0 ueberall.

ERWEITERT 18.08. -- Eigner woertlich: "alles was passiert muss in das
zentrale wiki auf dem vps auch rein". Drei weitere Quellen, gleiche Disziplin:

4. Git-Commits in WEITEREN Repos auf diesem VPS (_WEITERE_GIT_REPOS), nicht
   nur "the artefact". Gemessen 18.08. per `find /opt -maxdepth 5 -name .git`:
   /opt/agentzero-export/repo, /opt/unifieddb, /opt/clayverse, /opt/microclay
   sind eigene Repos mit eigener Historie (kein Symlink, keine Kopie -- per
   `git log -1` verglichen, unterschiedliche HEADs). Alle klein genug (3-222
   Commits total, siehe Kommentar bei _WEITERE_GIT_REPOS) um denselben
   GIT_CUTOFF wie Quelle 3 zu benutzen, statt eine neue Cutoff-Politik zu
   erfinden. _git_commits_fuer() ist die Verallgemeinerung von Quelle 3 auf
   pfad/toplevel/projekt/sphaere als Parameter; Quelle 3 selbst ruft sie nur
   noch mit den alten Konstanten auf -- keine Verhaltensaenderung fuer den
   Bestand.

5. GitHub-Konto-Ereignisse aus /var/lib/clay/ereignisse.jsonl. Diese Datei
   wird schon stuendlich von clayverse-github.service (eigener Dienst, GH_TOKEN
   mit echtem User-Scope -- geprueft: authentifiziert als gschaidergabriel,
   scopes gist/read:org/repo/workflow/write:packages, nicht der auf EIN Repo
   beschraenkte Deploy-Key unter /root/.ssh/agentzero_export) befuellt, aber
   NIE ins Wiki gehoben -- gemessen: kein von_quelle='github-ereignis*' im
   Bestand. Zwei Fallen umgangen:
     a) Doppelt zu Quelle 3/4: 5495 von 5676 Zeilen sind wirt='github', und
        86 % davon (3058+288+3 von 5676) betreffen Repos, die schon als
        lokaler Git-Klon ueber Quelle 3/4 laufen (clay-global-research-entity,
        clay-machine, microclay -- per `git remote -v` verifiziert, nicht
        geraten). _GITHUB_SKIP_REPOS filtert die raus, sonst stuenden dieselben
        Commits doppelt und duenner (nur SHA+erste Zeile) im Wiki.
     b) Drownen: nach dem Filter bleibt u.a. Dr.-Unterweger mit 2107
        Ereignissen/4 Tagen uebrig -- fast nur {repo,sha} ohne Text. Repos
        mit mehr als _GITHUB_AGGREGAT_SCHWELLE Ereignissen in der Datei werden
        DESHALB pro Tag aggregiert (Zaehlung je art-Wert + bis zu 10 Titel),
        nicht einzeln geschrieben. Repos darunter (die meisten: 1-12 Ereignisse)
        werden einzeln geschrieben, insert-only per Zeilen-Hash.
     projekt=Repo-Name direkt -- landet ohne neue Regeln in artikel_zuordnung.py
     in der bestehenden Leiter (Dr.-Unterweger/andreas-claude/... sind schon
     in PERSOENLICH gelistet).

6. Fehlgeschlagene Laeufe der eigenen Timer (systemd-Journal, entityos-*/
   clayverse-*, Prioritaet err). art='vorfall' -- das IST ein Vorfall im
   woertlichen Sinn, nicht bloss eine weitere Baunotiz. Gemessen 18.08. ueber
   30 Tage Journal: nur 6 Fehlschlaege total (GH_TOKEN fehlte einmalig,
   kaputtes JSON von der GitHub-API, HTTP 503, "database is locked" x2,
   ein fehlender Pfad) -- klein genug fuer 1:1, keine Aggregation noetig.
   id = Hash aus (Einheit, Zeitstempel, echter Fehlertext aus dem zweiten,
   engeren journalctl-Aufruf um die vom ersten gefundene Fehlerzeile) --
   insert-only, dasselbe Fenster beim naechsten Lauf ergibt denselben Hash.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Quellen
# ---------------------------------------------------------------------------
PROTOKOLL = Path("/opt/clayverse/bau/protokoll.jsonl")
BAUVERLAUF = Path("/opt/agentzero-export/repo/agentZero/bauverlauf/bauverlauf.jsonl")
GIT_REPO = Path("/opt/entityos/the artefact")
GIT_TOPLEVEL = "/opt/entityos"  # tatsaechliche Repo-Wurzel; "the artefact" ist ein Unterordner darin
GIT_CUTOFF = "2026-08-17T00:00:00+00:00"  # Eigner-Vorgabe: ab hier zaehlt's

# Quelle 4: weitere Repos auf dem VPS, per `find /opt -maxdepth 5 -name .git`
# gefunden und einzeln per `git remote -v`/`git log -1` geprueft (kein
# Symlink, kein Duplikat von GIT_REPO). Alle klein genug fuer denselben
# GIT_CUTOFF (Gesamthistorie 18.08. gemessen): agentzero-export/repo 53,
# unifieddb 70, clayverse 222, microclay 3 Commits total -- keins davon in
# der Groessenordnung, die einen eigenen Cutoff rechtfertigen wuerde.
# projekt/sphaere sind keine neuen Kategorien: EntityOS/entityos ist die
# bestehende Konvention aus Quelle 2/3, clayverse-bau/clayverse steht schon
# im Bestand (Quelle-1-Zeilen), microclay hat noch keinen INSTITUT-Eintrag
# und wird deshalb in artikel_zuordnung.py ergaenzt (README gelesen, nicht
# geraten: "ClayVerse ist ihr erster Benutzer, nicht ihr Zweck").
_WEITERE_GIT_REPOS = [
    {"pfad": Path("/opt/agentzero-export/repo"), "toplevel": "/opt/agentzero-export/repo",
     "projekt": "EntityOS", "sphaere": "entityos"},
    {"pfad": Path("/opt/unifieddb"), "toplevel": "/opt/unifieddb",
     "projekt": "EntityOS", "sphaere": "entityos"},
    {"pfad": Path("/opt/clayverse"), "toplevel": "/opt/clayverse",
     "projekt": "clayverse-bau", "sphaere": "clayverse"},
    {"pfad": Path("/opt/microclay"), "toplevel": "/opt/microclay",
     "projekt": "microclay", "sphaere": None},
]

# Quelle 5: GitHub-Konto-Ereignisse -- von clayverse-github.service schon
# stuendlich mit echtem GH_TOKEN (User-Scope, siehe Modulkopf) gesammelt,
# bisher nirgends ins Wiki gehoben.
GITHUB_STROM = Path("/var/lib/clay/ereignisse.jsonl")
# Repos, die schon als lokaler Klon ueber Quelle 3/4 laufen -- per
# `git remote -v` verifiziert (nicht geraten), sonst doppelt und duenner.
_GITHUB_SKIP_REPOS = {"clay-global-research-entity", "clay-machine", "microclay"}
# Ab wie vielen Ereignissen IN DER DATEI wird ein Repo pro Tag aggregiert
# statt einzeln geschrieben (gemessen 18.08.: Dr.-Unterweger 2107, alle
# anderen ungefilterten Repos <=12 -- 30 trennt die beiden Gruppen klar).
_GITHUB_AGGREGAT_SCHWELLE = 30

# Quelle 6: fehlgeschlagene Laeufe der eigenen Timer, aus dem systemd-Journal.
_JOURNAL_EINHEITEN = ["entityos-*", "clayverse-*"]
_JOURNAL_FENSTER_TAGE = 30  # gemessen 18.08.: 6 Fehlschlaege in 30 Tagen -- klein, insert-only reicht

_HYP_RE = re.compile(r"(?im)^[ \t]*Hypothese[ \t]*:[ \t]*(.+?)[ \t]*$")
_GEGENHYP_RE = re.compile(r"(?im)^[ \t]*Gegenhypothese[ \t]*:[ \t]*(.+?)[ \t]*$")

# ---------------------------------------------------------------------------
# Schema/Index -- Startaufgabe, keine Lesefunktion (Lehre aus profile.py:
# executescript() committet implizit und reisst eine laufende Transaktion
# auseinander -- das hat dort schon 77 rote Tests gekostet).
# ---------------------------------------------------------------------------
_INDEX_SQL = (
    "CREATE INDEX IF NOT EXISTS idx_artikel_baunotiz_lookup "
    "ON artikel(art, von_quelle, datum)"
)


def _hat_artikel_tabelle(db) -> bool:
    return bool(db.db.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='artikel'"
    ).fetchone())


def sicherstellen(db) -> None:
    """Nur Index anlegen -- artikel selbst gehoert nicht zu UnifiedDB.SCHEMA.

    artikel ist Altbestand in wiki.db (87 vorbestehende Tabellen, siehe
    store.py-Kommentar). Auf einer frischen Test-DB (UnifiedDB(tmp_path))
    gibt es die Tabelle nicht -- dann ist hier nichts zu tun, statt
    "no such table: artikel" zu werfen.
    """
    if not _hat_artikel_tabelle(db):
        return
    db.db.executescript(_INDEX_SQL)


# ---------------------------------------------------------------------------
# Kleinkram
# ---------------------------------------------------------------------------

def _slugify(s: str) -> str:
    """Exakt das Schema aus clayverse/werkzeug/wiki.py:slugify() -- fremde
    Pipeline, gelesen, nicht geraten. Muss bitidentisch sein, sonst
    kollidieren oder verdoppeln sich IDs zwischen den beiden Systemen."""
    s = str(s).strip()
    s = re.sub(r"[^A-Za-z0-9._-]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s or "unbekannt"


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _jetzt_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _extrahiere_hypothesen(text: str) -> tuple[str | None, str | None]:
    """Mechanische Extraktion, NIE Erfindung -- nur explizit beschriftete
    Zeilen. Siehe Modulkopf: das ist der Normalfall -> beide None."""
    h = _HYP_RE.search(text or "")
    g = _GEGENHYP_RE.search(text or "")
    return (h.group(1) if h else None, g.group(1) if g else None)


# ---------------------------------------------------------------------------
# Zeilen-Bauer -- feste Spaltenreihenfolge, kwargs statt Positions-Zaehlen
# (ein verzaehltes "?" in einer 18-19-spaltigen INSERT-Liste ist der
# klassische stille Bug; mit Namen kann das nicht mehr passieren).
# ---------------------------------------------------------------------------
_SPALTEN_BAUNOTIZ = [
    "id", "art", "titel", "quelle", "quell_hash", "datum", "metadaten",
    "belegt", "erzeugt_am", "wirt", "zuletzt_von", "von_quelle", "status",
    "konfidenz", "projekt", "projekt_art", "sphaere", "herkunft",
]
_UPSERT_BAUNOTIZ = (
    "INSERT INTO artikel(" + ",".join(_SPALTEN_BAUNOTIZ) + ") VALUES("
    + ",".join("?" for _ in _SPALTEN_BAUNOTIZ) + ") "
    "ON CONFLICT(id) DO UPDATE SET " + ",".join(
        f"{c}=excluded.{c}" for c in _SPALTEN_BAUNOTIZ if c != "id"
    )
)


def _zeile_baunotiz(**kw) -> tuple:
    fehl = set(kw) - set(_SPALTEN_BAUNOTIZ)
    assert not fehl, f"unbekannte Spalte(n) in _zeile_baunotiz: {fehl}"
    return tuple(kw.get(c) for c in _SPALTEN_BAUNOTIZ)


_SPALTEN_VORFALL = [
    "id", "art", "titel", "quelle", "quell_hash", "datum", "metadaten",
    "offene_fragen", "belegt", "erzeugt_am", "wirt", "zuletzt_von",
    "von_quelle", "status", "projekt", "projekt_art", "sphaere", "herkunft",
]
_INSERT_ONLY_VORFALL = (
    "INSERT INTO artikel(" + ",".join(_SPALTEN_VORFALL) + ") VALUES("
    + ",".join("?" for _ in _SPALTEN_VORFALL) + ") ON CONFLICT(id) DO NOTHING"
)


def _zeile_vorfall(**kw) -> tuple:
    fehl = set(kw) - set(_SPALTEN_VORFALL)
    assert not fehl, f"unbekannte Spalte(n) in _zeile_vorfall: {fehl}"
    return tuple(kw.get(c) for c in _SPALTEN_VORFALL)


def _schreibe(db, sql: str, zeile: tuple) -> None:
    with db.tx() as sql_db:
        sql_db.execute(sql, zeile)


def _vorhandene(db, art: str, von_quelle: str, seit: str | None = None) -> dict:
    """id -> quell_hash, fuer den Idempotenz-Check ohne Volltabellenscan."""
    if seit:
        rows = db.db.execute(
            "SELECT id, quell_hash FROM artikel WHERE art=? AND von_quelle=? AND datum>=?",
            (art, von_quelle, seit),
        )
    else:
        rows = db.db.execute(
            "SELECT id, quell_hash FROM artikel WHERE art=? AND von_quelle=?",
            (art, von_quelle),
        )
    return {r[0]: r[1] for r in rows}


# ---------------------------------------------------------------------------
# Quelle 1: protokoll.jsonl -- Luecken fuellen, art='vorfall', NIE ueberschreiben
# ---------------------------------------------------------------------------

def _protokoll(db, zaehler: dict) -> None:
    if not PROTOKOLL.is_file():
        return
    rohtext = PROTOKOLL.read_text(encoding="utf-8")
    datei_hash = _sha256(rohtext)
    vorhandene_ids = {
        r[0] for r in db.db.execute(
            "SELECT id FROM artikel WHERE art='vorfall' AND quelle=?", (str(PROTOKOLL),)
        )
    }
    gesehen: dict[str, int] = {}
    jetzt = _jetzt_iso()
    for zeile in rohtext.splitlines():
        zeile = zeile.strip()
        if not zeile:
            continue
        try:
            meta = json.loads(zeile)
        except Exception:
            continue
        bauteil = meta.get("bauteil") or "UNBEKANNT"
        zeit = meta.get("zeit") or ""
        base = _slugify(f"{bauteil}-{zeit}")
        if base in gesehen:
            gesehen[base] += 1
            id_ = f"{base}-{gesehen[base]}"
        else:
            gesehen[base] = 0
            id_ = base
        if id_ in vorhandene_ids:
            zaehler["uebersprungen"] += 1
            continue  # eine andere Pipeline besitzt diese Zeile schon -- nicht anfassen
        offene = []
        if meta.get("offen"):
            offene.append({"feld": "offen", "text": str(meta["offen"])})
        ergebnis_text = str(meta.get("ergebnis") or "")
        hyp, gegenhyp = _extrahiere_hypothesen(ergebnis_text)
        if hyp is None and gegenhyp is None:
            zaehler["ohne_hypothese"] += 1
        meta_voll = dict(meta)  # verbatim -- Bestandskonvention der fremden Pipeline
        meta_voll["herkunft"] = "protokoll.jsonl"
        meta_voll["wieso"] = meta.get("ergebnis") or None
        meta_voll["wo_dazugehoert"] = meta.get("wirt") or None
        meta_voll["hypothese"] = hyp
        meta_voll["gegenhypothese"] = gegenhyp
        meta_voll["timestamp"] = meta.get("zeit")
        _schreibe(db, _INSERT_ONLY_VORFALL, _zeile_vorfall(
            id=id_, art="vorfall", titel=meta.get("titel") or bauteil,
            quelle=str(PROTOKOLL), quell_hash=datei_hash, datum=meta.get("zeit"),
            metadaten=json.dumps(meta_voll, ensure_ascii=False, sort_keys=True),
            offene_fragen=json.dumps(offene, ensure_ascii=False) if offene else None,
            belegt=1, erzeugt_am=jetzt, wirt="clayverse", zuletzt_von="clayverse-bau",
            von_quelle="strom", status=meta.get("status"), projekt="clayverse-bau",
            projekt_art="eigen", sphaere="clayverse", herkunft="gemessen",
        ))
        vorhandene_ids.add(id_)
        zaehler["neu"] += 1


# ---------------------------------------------------------------------------
# Quelle 2: bauverlauf.jsonl -- art='baunotiz', volles Upsert (echte Aenderung
# an derselben commit+zeit-Identitaet ist moeglich und soll als
# "aktualisiert" zaehlen).
# ---------------------------------------------------------------------------

def _bauverlauf(db, zaehler: dict) -> None:
    if not BAUVERLAUF.is_file():
        return
    vorhandene = _vorhandene(db, "baunotiz", "bauverlauf.jsonl")
    jetzt = _jetzt_iso()
    for rohzeile in BAUVERLAUF.read_text(encoding="utf-8").splitlines():
        rohzeile = rohzeile.strip()
        if not rohzeile:
            continue
        try:
            e = json.loads(rohzeile)
        except Exception:
            continue
        quell_hash = _sha256(rohzeile)
        zeit_feld = e.get("zeit") or ""
        identitaet = e.get("commit") or quell_hash[:16]
        id_ = "baunotiz-bauverlauf-" + _sha256(identitaet + "|" + zeit_feld)[:20]

        bisher = vorhandene.get(id_)
        if bisher == quell_hash:
            zaehler["uebersprungen"] += 1
            continue

        text = (e.get("betreff") or "") + "\n\n" + (e.get("begruendung") or "")
        hyp, gegenhyp = _extrahiere_hypothesen(text)
        if hyp is None and gegenhyp is None:
            zaehler["ohne_hypothese"] += 1

        meta = {
            "herkunft": "bauverlauf.jsonl",
            "wieso": e.get("begruendung") or None,
            "wo_dazugehoert": e.get("repo"),
            "hypothese": hyp,
            "gegenhypothese": gegenhyp,
            "timestamp": e.get("zeit"),
            "commit": e.get("commit"),
            "betreff": e.get("betreff"),
            "autor": e.get("autor"),
            "hat_begruendung": e.get("hat_begruendung"),
            "rohzeile_sha256": quell_hash,
        }
        _schreibe(db, _UPSERT_BAUNOTIZ, _zeile_baunotiz(
            id=id_, art="baunotiz", titel=e.get("betreff") or identitaet,
            quelle=str(BAUVERLAUF), quell_hash=quell_hash, datum=e.get("zeit"),
            metadaten=json.dumps(meta, ensure_ascii=False, sort_keys=True),
            belegt=1, erzeugt_am=jetzt, wirt="clayverse",
            zuletzt_von=e.get("autor") or None, von_quelle="bauverlauf.jsonl",
            status=None, konfidenz=None, projekt="EntityOS", projekt_art="eigen",
            sphaere="entityos", herkunft="gemessen",
        ))
        vorhandene[id_] = quell_hash
        if bisher is None:
            zaehler["neu"] += 1
        else:
            zaehler["aktualisiert"] += 1


# ---------------------------------------------------------------------------
# Quelle 3: Git-Commits in DIESEM Repo -- art='baunotiz'. SHA ist die id,
# darum in der Praxis nie "aktualisiert" (eine SHA aendert sich nicht ohne
# neue SHA zu werden).
# ---------------------------------------------------------------------------

def _git_seit(db, quelle: str) -> str:
    """Fensterstart: fixer Eigner-Cutoff, oder (falls spaeter) letzter
    verarbeiteter Commit DIESES Repos minus 1 Tag Puffer. Ohne Fenster wuerde
    jeder Lauf das komplette, staendig wachsende Since-Fenster neu scannen --
    mit Fenster bleibt der `git log`-Aufruf auf die letzten Tage begrenzt.
    Nach quelle (Repo-Pfad) gefiltert, sonst wuerde ein schnell laufendes
    Repo das Fenster fuer ein langsameres mitverschieben und Commits
    ueberspringen, die dort noch nie gelaufen sind."""
    seit = GIT_CUTOFF
    row = db.db.execute(
        "SELECT MAX(datum) FROM artikel WHERE art='baunotiz' AND von_quelle='git-commit' AND quelle=?",
        (quelle,),
    ).fetchone()
    if row and row[0]:
        try:
            letzter = datetime.fromisoformat(str(row[0]).replace("Z", "+00:00"))
            gepolstert = (letzter - timedelta(days=1)).isoformat()
            if gepolstert > GIT_CUTOFF:
                seit = gepolstert
        except Exception:
            pass
    return seit


def _git_commits_fuer(db, zaehler: dict, *, pfad: Path, toplevel: str,
                       projekt: str, sphaere: str | None) -> None:
    """Verallgemeinerung von Quelle 3 auf ein beliebiges Repo -- gleiche
    Logik (SHA ist die id, seit-Fenster, Upsert), nur pfad/toplevel/
    projekt/sphaere als Parameter statt Modulkonstanten."""
    if not pfad.is_dir():
        zaehler.setdefault("_fehler", []).append(f"git-repo fehlt: {pfad}")
        return
    quelle = str(pfad)
    seit = _git_seit(db, quelle)
    RS, FS = "\x1e", "\x1f"
    fmt = f"%H{FS}%an{FS}%ae{FS}%aI{FS}%B{RS}"
    try:
        proc = subprocess.run(
            ["git", "-c", f"safe.directory={toplevel}", "log",
             f"--since={seit}", f"--format={fmt}"],
            cwd=quelle, capture_output=True, text=True, timeout=180, check=True,
        )
    except Exception as exc:
        zaehler.setdefault("_fehler", []).append(f"git log {quelle} seit={seit}: {type(exc).__name__}: {exc}")
        return

    saetze = [r for r in proc.stdout.split(RS) if r.strip("\n")]
    if not saetze:
        return

    vorhandene = _vorhandene(db, "baunotiz", "git-commit", seit=seit)
    jetzt = _jetzt_iso()
    for satz in saetze:
        satz = satz.lstrip("\n")
        teile = satz.split(FS, 4)
        if len(teile) < 5:
            continue
        sha, autor, autor_mail, datum, nachricht = teile
        nachricht = nachricht.rstrip("\n")
        id_ = f"baunotiz-git-{sha}"

        if id_ in vorhandene:
            zaehler["uebersprungen"] += 1
            continue

        betreff = nachricht.split("\n", 1)[0]
        hyp, gegenhyp = _extrahiere_hypothesen(nachricht)
        if hyp is None and gegenhyp is None:
            zaehler["ohne_hypothese"] += 1

        meta = {
            "herkunft": "git-commit",
            "wieso": nachricht or None,
            "wo_dazugehoert": quelle,
            "hypothese": hyp,
            "gegenhypothese": gegenhyp,
            "timestamp": datum,
            "commit_sha": sha,
            "autor": autor,
            "autor_email": autor_mail,
            "betreff": betreff,
        }
        _schreibe(db, _UPSERT_BAUNOTIZ, _zeile_baunotiz(
            id=id_, art="baunotiz", titel=betreff, quelle=quelle,
            quell_hash=sha, datum=datum,
            metadaten=json.dumps(meta, ensure_ascii=False, sort_keys=True),
            belegt=1, erzeugt_am=jetzt, wirt="clayverse", zuletzt_von=autor,
            von_quelle="git-commit", status=None, konfidenz=None,
            projekt=projekt, projekt_art="eigen", sphaere=sphaere,
            herkunft="gemessen",
        ))
        vorhandene[id_] = sha
        zaehler["neu"] += 1


def _git_commits(db, zaehler: dict) -> None:
    """Quelle 3 (unveraendertes Verhalten fuer den Bestand) + Quelle 4
    (_WEITERE_GIT_REPOS) -- dieselbe Funktion, andere Parameter."""
    _git_commits_fuer(db, zaehler, pfad=GIT_REPO, toplevel=GIT_TOPLEVEL,
                       projekt="EntityOS", sphaere="entityos")
    for repo in _WEITERE_GIT_REPOS:
        _git_commits_fuer(db, zaehler, pfad=repo["pfad"], toplevel=repo["toplevel"],
                           projekt=repo["projekt"], sphaere=repo["sphaere"])


# ---------------------------------------------------------------------------
# Quelle 5: GitHub-Konto-Ereignisse aus ereignisse.jsonl -- kleine Repos
# einzeln (insert-only, Zeilen-Hash als id), grosse Repos (> Schwelle)
# pro Tag aggregiert (Upsert, quell_hash aus der Zaehlung).
# ---------------------------------------------------------------------------

def _github_ereignisse(db, zaehler: dict) -> None:
    if not GITHUB_STROM.is_file():
        return
    zeilen: list[tuple[str, dict]] = []
    for rohzeile in GITHUB_STROM.read_text(encoding="utf-8").splitlines():
        rohzeile = rohzeile.strip()
        if not rohzeile:
            continue
        try:
            e = json.loads(rohzeile)
        except Exception:
            continue
        if e.get("wirt") != "github":
            continue  # ereignisse.jsonl traegt auch clayverse-interne Zeilen -- nicht diese Quelle
        repo = e.get("repo")
        if not repo or repo in _GITHUB_SKIP_REPOS:
            continue  # schon als lokaler Git-Klon ueber Quelle 3/4 drin -- siehe Modulkopf
        zeilen.append((rohzeile, e))

    zaehlung_je_repo: dict[str, int] = {}
    for _, e in zeilen:
        zaehlung_je_repo[e["repo"]] = zaehlung_je_repo.get(e["repo"], 0) + 1

    einzeln = [(r, e) for r, e in zeilen if zaehlung_je_repo[e["repo"]] <= _GITHUB_AGGREGAT_SCHWELLE]
    aggregiert = [(r, e) for r, e in zeilen if zaehlung_je_repo[e["repo"]] > _GITHUB_AGGREGAT_SCHWELLE]

    _github_einzeln(db, zaehler, einzeln)
    _github_aggregiert(db, zaehler, aggregiert)


def _github_einzeln(db, zaehler: dict, zeilen: list) -> None:
    if not zeilen:
        return
    vorhandene_ids = {
        r[0] for r in db.db.execute(
            "SELECT id FROM artikel WHERE art='baunotiz' AND von_quelle='github-ereignis'"
        )
    }
    jetzt = _jetzt_iso()
    for rohzeile, e in zeilen:
        id_ = "baunotiz-github-" + _sha256(rohzeile)[:20]
        if id_ in vorhandene_ids:
            zaehler["uebersprungen"] += 1
            continue
        titel = e.get("titel") or f"{e.get('art')}: {e.get('repo')}"
        hyp, gegenhyp = _extrahiere_hypothesen(titel)
        if hyp is None and gegenhyp is None:
            zaehler["ohne_hypothese"] += 1
        meta = {
            "herkunft": "github-ereignis", "wieso": titel or None,
            "wo_dazugehoert": e.get("repo"), "hypothese": hyp, "gegenhypothese": gegenhyp,
            "timestamp": e.get("zeit"), "github_art": e.get("art"), "sha": e.get("sha"),
            "nummer": e.get("nummer"), "ref_typ": e.get("ref_typ"),
            "rohzeile_sha256": _sha256(rohzeile),
        }
        # _UPSERT_BAUNOTIZ statt eigenem INSERT-ONLY: id traegt schon den
        # Zeilen-Hash, ein Konflikt kann nur bei identischem Inhalt
        # entstehen -- der wird oben schon per vorhandene_ids uebersprungen.
        _schreibe(db, _UPSERT_BAUNOTIZ, _zeile_baunotiz(
            id=id_, art="baunotiz", titel=titel, quelle=str(GITHUB_STROM),
            quell_hash=_sha256(rohzeile), datum=e.get("zeit"),
            metadaten=json.dumps(meta, ensure_ascii=False, sort_keys=True),
            belegt=1, erzeugt_am=jetzt, wirt="github", zuletzt_von=None,
            von_quelle="github-ereignis", status=None, konfidenz=None,
            projekt=e.get("repo"), projekt_art="fremd", sphaere=None,
            herkunft="gemessen",
        ))
        vorhandene_ids.add(id_)
        zaehler["neu"] += 1


def _github_aggregiert(db, zaehler: dict, zeilen: list) -> None:
    if not zeilen:
        return
    eimer: dict[tuple[str, str], dict] = {}
    for rohzeile, e in zeilen:
        repo = e["repo"]
        tag = (e.get("zeit") or "")[:10] or "unbekannt"
        b = eimer.setdefault((repo, tag), {"arten": {}, "titel": [], "shas": []})
        b["arten"][e.get("art")] = b["arten"].get(e.get("art"), 0) + 1
        if e.get("titel") and len(b["titel"]) < 10:
            b["titel"].append(e["titel"])
        if e.get("sha"):
            b["shas"].append(e["sha"])

    vorhandene = _vorhandene(db, "baunotiz", "github-ereignis-tag")
    jetzt = _jetzt_iso()
    for (repo, tag), b in sorted(eimer.items()):
        id_ = "baunotiz-github-tag-" + _slugify(repo) + "-" + tag
        gesamt = sum(b["arten"].values())
        arten_sortiert = dict(sorted(b["arten"].items(), key=lambda x: -x[1]))
        payload = {"arten": arten_sortiert, "titel": b["titel"],
                   "anzahl_shas": len(b["shas"]), "gesamt": gesamt}
        quell_hash = _sha256(json.dumps(payload, sort_keys=True))
        bisher = vorhandene.get(id_)
        if bisher == quell_hash:
            zaehler["uebersprungen"] += 1
            continue
        kurz = ", ".join(f"{v}x{k}" for k, v in arten_sortiert.items())
        titel = f"{repo}: {gesamt} GitHub-Ereignisse am {tag} ({kurz})"
        meta = {
            "herkunft": "github-ereignis-tag",
            "wieso": f"aggregiert -- {gesamt} Ereignisse an diesem Tag, ueber der "
                     f"Schwelle von {_GITHUB_AGGREGAT_SCHWELLE}/Datei (siehe Modulkopf, "
                     f"Falle b: einzeln geschrieben haette das Wiki geflutet)",
            "wo_dazugehoert": repo, "hypothese": None, "gegenhypothese": None,
            "timestamp": tag, "arten": arten_sortiert, "beispiel_titel": b["titel"],
        }
        _schreibe(db, _UPSERT_BAUNOTIZ, _zeile_baunotiz(
            id=id_, art="baunotiz", titel=titel, quelle=str(GITHUB_STROM),
            quell_hash=quell_hash, datum=f"{tag}T00:00:00+00:00",
            metadaten=json.dumps(meta, ensure_ascii=False, sort_keys=True),
            belegt=1, erzeugt_am=jetzt, wirt="github", zuletzt_von=None,
            von_quelle="github-ereignis-tag", status=None, konfidenz=None,
            projekt=repo, projekt_art="fremd", sphaere=None, herkunft="gemessen",
        ))
        vorhandene[id_] = quell_hash
        zaehler["ohne_hypothese"] += 1  # aggregiert -- nie mechanisch aus Titeln extrahiert
        if bisher is None:
            zaehler["neu"] += 1
        else:
            zaehler["aktualisiert"] += 1


# ---------------------------------------------------------------------------
# Quelle 6: fehlgeschlagene Timer-Laeufe aus dem systemd-Journal -- art='vorfall',
# insert-only. VPS-Zeitzone ist Etc/UTC (gemessen, timedatectl) -- die
# --since/--until-Strings unten sind deshalb absichtlich naiv-UTC.
# ---------------------------------------------------------------------------

_JOURNAL_FAIL_RE = re.compile(r"^Failed to start (\S+) - (.*)\.$")


def _journal_kontext(einheit: str, ts_usec: int) -> str:
    """Zweiter, engerer journalctl-Aufruf um die Fehlerzeile herum: die
    echten Fehlermeldungen der Anwendung (ihr eigenes stdout/stderr), nicht
    nur die von systemd selbst erzeugte 'Failed to start'-Zeile."""
    ts_s = ts_usec / 1_000_000
    seit = datetime.fromtimestamp(ts_s - 5, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    bis = datetime.fromtimestamp(ts_s + 1, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    try:
        proc = subprocess.run(
            ["journalctl", "-u", einheit, "--since", seit, "--until", bis,
             "-o", "cat", "--no-pager"],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except Exception as exc:
        return f"(Kontext nicht lesbar: {type(exc).__name__}: {exc})"
    return "\n".join(z for z in proc.stdout.splitlines() if z.strip())


def _journal_vorfaelle(db, zaehler: dict) -> None:
    einheiten_args: list[str] = []
    for muster in _JOURNAL_EINHEITEN:
        einheiten_args += ["-u", muster]
    try:
        proc = subprocess.run(
            ["journalctl", *einheiten_args, "-p", "err",
             "--since", f"-{_JOURNAL_FENSTER_TAGE} days", "-o", "json", "--no-pager"],
            capture_output=True, text=True, timeout=60, check=False,
        )
    except Exception as exc:
        zaehler.setdefault("_fehler", []).append(f"journalctl: {type(exc).__name__}: {exc}")
        return

    vorhandene_ids = {
        r[0] for r in db.db.execute(
            "SELECT id FROM artikel WHERE art='vorfall' AND von_quelle='journal'"
        )
    }
    jetzt = _jetzt_iso()
    for zeile in proc.stdout.splitlines():
        zeile = zeile.strip()
        if not zeile:
            continue
        try:
            e = json.loads(zeile)
        except Exception:
            continue
        nachricht = (e.get("MESSAGE") or "").strip()
        treffer = _JOURNAL_FAIL_RE.match(nachricht)
        if not treffer:
            continue  # nur die "Failed to start"-Zeile ist der verlaessliche Anker (siehe Modulkopf)
        einheit, beschreibung = treffer.group(1), treffer.group(2)
        try:
            ts_usec = int(e.get("__REALTIME_TIMESTAMP") or 0)
        except (TypeError, ValueError):
            ts_usec = 0
        if not ts_usec:
            continue
        datum = datetime.fromtimestamp(ts_usec / 1_000_000, tz=timezone.utc).isoformat()
        kontext = _journal_kontext(einheit, ts_usec)

        id_ = "vorfall-journal-" + _sha256(einheit + "|" + datum + "|" + kontext)[:20]
        if id_ in vorhandene_ids:
            zaehler["uebersprungen"] += 1
            continue

        hyp, gegenhyp = _extrahiere_hypothesen(kontext)
        if hyp is None and gegenhyp is None:
            zaehler["ohne_hypothese"] += 1

        meta = {
            "herkunft": "journal", "wieso": kontext or nachricht,
            "wo_dazugehoert": einheit, "hypothese": hyp, "gegenhypothese": gegenhyp,
            "timestamp": datum, "einheit": einheit, "beschreibung": beschreibung,
            "journal_kontext": kontext,
        }
        _schreibe(db, _INSERT_ONLY_VORFALL, _zeile_vorfall(
            id=id_, art="vorfall", titel=f"{einheit}: Fehlschlag {datum}",
            quelle="systemd-journal", quell_hash=_sha256(kontext), datum=datum,
            metadaten=json.dumps(meta, ensure_ascii=False, sort_keys=True),
            offene_fragen=None, belegt=1, erzeugt_am=jetzt, wirt="clayverse",
            zuletzt_von="systemd", von_quelle="journal", status="failed",
            projekt="clayverse-bau", projekt_art="eigen", sphaere="clayverse",
            herkunft="gemessen",
        ))
        vorhandene_ids.add(id_)
        zaehler["neu"] += 1


# ---------------------------------------------------------------------------
# Oeffentlicher Einstieg
# ---------------------------------------------------------------------------

def aufnehmen(db, quelle: str | None = None) -> dict:
    """Baunotizen aus bis zu sechs Quellen ins Wiki heben.

    quelle=None laeuft alle; sonst genau eine ('protokoll'|'bauverlauf'|'git'|
    'github'|'journal') -- fuer gezieltes Nachziehen/Testen einer einzelnen
    Quelle. 'git' deckt sowohl Quelle 3 (GIT_REPO) als auch Quelle 4
    (_WEITERE_GIT_REPOS) ab -- eine Funktion, mehrere Repos als Parameter.
    Idempotent: unveraenderter Quelltext -> zweiter Lauf liefert neu=0.
    """
    sicherstellen(db)
    if not _hat_artikel_tabelle(db):
        return {"neu": 0, "aktualisiert": 0, "uebersprungen": 0, "ohne_hypothese": 0,
                "hinweis": "keine artikel-Tabelle auf dieser DB (Testinstanz?) -- nichts zu tun"}

    zaehler = {"neu": 0, "aktualisiert": 0, "uebersprungen": 0, "ohne_hypothese": 0}
    if quelle in (None, "protokoll"):
        _protokoll(db, zaehler)
    if quelle in (None, "bauverlauf"):
        _bauverlauf(db, zaehler)
    if quelle in (None, "git"):
        _git_commits(db, zaehler)
    if quelle in (None, "github"):
        _github_ereignisse(db, zaehler)
    if quelle in (None, "journal"):
        _journal_vorfaelle(db, zaehler)
    return zaehler
