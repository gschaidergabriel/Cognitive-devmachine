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

def _git_seit(db) -> str:
    """Fensterstart: fixer Eigner-Cutoff, oder (falls spaeter) letzter
    verarbeiteter Commit minus 1 Tag Puffer. Ohne Fenster wuerde jeder Lauf
    das komplette, staendig wachsende Since-Fenster neu scannen -- mit
    Fenster bleibt der `git log`-Aufruf auf die letzten Tage begrenzt."""
    seit = GIT_CUTOFF
    row = db.db.execute(
        "SELECT MAX(datum) FROM artikel WHERE art='baunotiz' AND von_quelle='git-commit'"
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


def _git_commits(db, zaehler: dict) -> None:
    if not GIT_REPO.is_dir():
        return
    seit = _git_seit(db)
    RS, FS = "\x1e", "\x1f"
    fmt = f"%H{FS}%an{FS}%ae{FS}%aI{FS}%B{RS}"
    try:
        proc = subprocess.run(
            ["git", "-c", f"safe.directory={GIT_TOPLEVEL}", "log",
             f"--since={seit}", f"--format={fmt}"],
            cwd=str(GIT_REPO), capture_output=True, text=True, timeout=180, check=True,
        )
    except Exception as exc:
        zaehler.setdefault("_fehler", []).append(f"git log seit={seit}: {type(exc).__name__}: {exc}")
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
            "wo_dazugehoert": str(GIT_REPO),
            "hypothese": hyp,
            "gegenhypothese": gegenhyp,
            "timestamp": datum,
            "commit_sha": sha,
            "autor": autor,
            "autor_email": autor_mail,
            "betreff": betreff,
        }
        _schreibe(db, _UPSERT_BAUNOTIZ, _zeile_baunotiz(
            id=id_, art="baunotiz", titel=betreff, quelle=str(GIT_REPO),
            quell_hash=sha, datum=datum,
            metadaten=json.dumps(meta, ensure_ascii=False, sort_keys=True),
            belegt=1, erzeugt_am=jetzt, wirt="clayverse", zuletzt_von=autor,
            von_quelle="git-commit", status=None, konfidenz=None,
            projekt="EntityOS", projekt_art="eigen", sphaere="entityos",
            herkunft="gemessen",
        ))
        vorhandene[id_] = sha
        zaehler["neu"] += 1


# ---------------------------------------------------------------------------
# Oeffentlicher Einstieg
# ---------------------------------------------------------------------------

def aufnehmen(db, quelle: str | None = None) -> dict:
    """Baunotizen aus bis zu drei Quellen ins Wiki heben.

    quelle=None laeuft alle drei; sonst genau eine ('protokoll'|'bauverlauf'|
    'git') -- fuer gezieltes Nachziehen/Testen einer einzelnen Quelle.
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
    return zaehler
