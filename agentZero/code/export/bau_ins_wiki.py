#!/usr/bin/env python3
"""Bauschritte werden Wiki-Artikel -- und zwar AUFFINDBARE.

Eignerauftrag woertlich (18.08.): "alle deine baunotizen werden auch teil des
wiki und mit alle meine ich alle mit metadaten und alles".

⭐ DER BEFUND, DER DIESES SKRIPT AUSLOEST (gemessen, nicht vermutet)
-------------------------------------------------------------------
In `artikel` standen 2536 Zeilen mit art in ('baunotiz','vorfall') -- die
Bauschritte SIND also eingetragen. Aber nur 38 davon hatten eine Zeile in
`artikel_suchtext` und damit einen Eintrag im Volltextindex
`fts_index_artikel`. 2498 Bauschritte waren in der Datenbank und trotzdem
fuer NIEMANDEN auffindbar.

Ursache: clayverse/baunotizen.py schreibt sauber nach `artikel` (volle
Metadaten, Idempotenz, keine erfundenen Hypothesen) -- fasst aber
`artikel_suchtext` und `fts_index_artikel` nie an. Ein Artikel, den die Suche
nicht findet, ist kein Wiki-Artikel, sondern eine Zeile in einer Tabelle.
Genau das ist die Falle, die hier geschlossen wird.

WAS DIESES SKRIPT TUT -- drei Durchgaenge
------------------------------------------
1. NACHTRAGEN: clayverse.baunotizen.aufnehmen() laufen lassen, damit kein
   Bauschritt der Nacht fehlt. Kein neuer Aufnahmeweg -- der bestehende wird
   benutzt, nicht nachgebaut.

2. BAUSCHRITTE ALS LESBARE ARTIKEL (`bau-<repo>-<sha12>`, art='bau'):
   eine Zeile je Commit aus bauverlauf.jsonl -- der Quelle, die alle vier
   Repos zusammenfasst. Diese Schicht ist eine ZUSAMMENFUEHRUNG, keine
   Verdopplung: derselbe Commit liegt im Bestand zweimal als Rohnotiz
   (`baunotiz-git-<sha40>` UND `baunotiz-bauverlauf-<hash>`); der bau-Artikel
   nennt beide in `metadaten.deckt_ab` und ist der eine lesbare Ort dafuer.

3. AUFFINDBAR MACHEN: fuer JEDEN baunotiz-/vorfall-/bau-Artikel eine Zeile in
   `artikel_suchtext` plus den passenden Eintrag im FTS-Index.

⚠️ NICHTS WIRD ERFUNDEN
-----------------------
Der Artikeltext besteht aus Betreff und Commit-Text VERBATIM. Wo ein Commit
keine Begruendung traegt, steht das als Luecke im Artikel -- ausgeschrieben,
nicht aufgefuellt. `hypothese`/`gegenhypothese` nur bei woertlicher Zeile
"^Hypothese:" bzw. "^Gegenhypothese:", mechanisch extrahiert (gemessen: im
Bestand kommt das nie vor -- das ist der Befund, kein Extraktorfehler).

⚠️ DIE FTS-FALLE
----------------
`fts_index_artikel` ist FTS5 mit content='artikel_suchtext'. Eine solche
Tabelle kennt kein UPSERT. Aendern heisst: alten Eintrag mit den ALTEN Werten
loeschen (Kommandoform `INSERT INTO fts(fts,rowid,...) VALUES('delete',...)`),
dann neu einfuegen. Loescht man mit den NEUEN Werten, bleiben die alten Terme
als Leichen im Index stehen und die Suche liefert Treffer auf Text, der
nirgends mehr steht.

IDEMPOTENZ
----------
Stabile ids (Commit-SHA ist selbst ein Inhalts-Hash). Unveraenderter Suchtext
wird uebersprungen -- kein Index-Umbau ohne Anlass. Zweiter Lauf = 0 neu,
0 geaendert.
"""
import json
import hashlib
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, "/opt/entityos/the artefact")
from clayverse.store import UnifiedDB                      # noqa: E402

# ⚠️ Umlenkbar fuer Probelaeufe. Beim ersten Bau war genau diese Zeile fest
# verdrahtet und ein "Probelauf auf einer Kopie" lief in Wahrheit auf der
# echten Datenbank -- der Umweg war da, die Wirkung nicht.
WIKI = os.environ.get("BAU_WIKI", "/var/lib/clay/wiki.db")
BAUVERLAUF = Path("/opt/agentzero-export/repo/agentZero/bauverlauf/bauverlauf.jsonl")

# Aus /opt/agentzero-export/agentzero_export.py abgelesen (Zeile 646 f.),
# nicht geraten: welcher Kurzname welchem Arbeitsverzeichnis entspricht.
REPO_PFAD = {
    "entityos": "/opt/entityos",
    "unifieddb": "/opt/unifieddb",
    "clay": "/opt/clayverse",
    "agentzero-export": "/opt/agentzero-export/repo",
}

# Spaltenprotokoll -- identisch zu clayverse/baunotizen.py (_SPALTEN_BAUNOTIZ),
# ergaenzt um die Felder, die migration.py fuer lesbare Artikel setzt.
SPALTEN = [
    "id", "art", "titel", "quelle", "quell_hash", "datum", "metadaten",
    "belegt", "erzeugt_am", "wirt", "zuletzt_von", "von_quelle", "status",
    "konfidenz", "projekt", "projekt_art", "sphaere", "herkunft",
]
UPSERT = (
    "INSERT INTO artikel(" + ",".join(SPALTEN) + ") VALUES("
    + ",".join("?" for _ in SPALTEN) + ") ON CONFLICT(id) DO UPDATE SET "
    + ",".join(f"{c}=excluded.{c}" for c in SPALTEN if c != "id")
)


def jetzt_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S+0000", time.gmtime())


def hypothesen(text: str):
    """Nur woertliche Zeilen. Keine Interpretation, keine Vermutung."""
    hyp = geg = None
    for zeile in (text or "").splitlines():
        s = zeile.strip()
        if s.startswith("Hypothese:") and hyp is None:
            hyp = s[len("Hypothese:"):].strip() or None
        elif s.startswith("Gegenhypothese:") and geg is None:
            geg = s[len("Gegenhypothese:"):].strip() or None
    return hyp, geg


def artikeltext(d: dict) -> str:
    """Der Artikelkoerper -- Quelltext verbatim, Luecken benannt."""
    repo = d.get("repo") or "?"
    begr = (d.get("begruendung") or "").strip()
    teile = [d.get("betreff") or "(ohne Betreff)", ""]
    if begr:
        teile += ["BEGRUENDUNG (verbatim aus dem Commit-Text)", begr, ""]
    else:
        teile += [
            "BEGRUENDUNG",
            "⚠️ KEINE BEGRUENDUNG DOKUMENTIERT. Der Commit traegt nur eine",
            "Betreffzeile. Diese Luecke steht hier absichtlich offen -- was in",
            "der Quelle fehlt, wird nicht ergaenzt.",
            "",
        ]
    teile += [
        "HERKUNFT",
        f"Repo: {repo} ({REPO_PFAD.get(repo, 'Pfad nicht hinterlegt')})",
        f"Commit: {d.get('commit') or '?'}",
        f"Autor: {d.get('autor') or '?'}",
        f"Zeit: {d.get('zeit') or '?'}",
        "Quelle: agentZero/bauverlauf/bauverlauf.jsonl (aus git log auf frank-api)",
    ]
    hyp, geg = hypothesen(begr)
    teile += [
        "",
        "HYPOTHESE / GEGENHYPOTHESE",
        f"Hypothese: {hyp or '(keine im Commit-Text)'}",
        f"Gegenhypothese: {geg or '(keine im Commit-Text)'}",
    ]
    return "\n".join(teile)


def suchtext_aus_metadaten(titel: str, meta_roh: str) -> str:
    """Suchbarer Koerper fuer Bestandszeilen.

    ⚠️ Es wird JEDER Zeichenketten-Wert aus den Metadaten aufgenommen, auch aus
    verschachtelten Strukturen -- keine Feldauswahl. Eine Auswahlliste laesst
    genau die Felder liegen, die eine fremde Quelle anders benennt (gemessen:
    die vorfall-Zeilen tragen ihren Inhalt in `ergebnis`, das in keiner
    naheliegenden Liste steht -- und waeren so wieder unauffindbar geblieben).
    """
    stuecke = [titel or ""]

    def ernten(wert):
        if isinstance(wert, str):
            if wert.strip():
                stuecke.append(wert.strip())
        elif isinstance(wert, dict):
            for schluessel, unterwert in wert.items():
                stuecke.append(str(schluessel))
                ernten(unterwert)
        elif isinstance(wert, (list, tuple)):
            for unterwert in wert:
                ernten(unterwert)

    try:
        ernten(json.loads(meta_roh) if meta_roh else {})
    except Exception:
        stuecke.append(meta_roh or "")
    return "\n".join(dict.fromkeys(s for s in stuecke if s))


def auffindbar(sql, artikel_id: str, titel: str, text: str, blase: str) -> str:
    """Suchtext + FTS-Eintrag setzen. Rueckgabe: neu | geaendert | unveraendert.

    ⚠️ Reihenfolge ist hier nicht Geschmack: erst den FTS-Eintrag mit den ALTEN
    Werten loeschen, dann die Inhaltszeile aendern, dann neu indizieren.
    """
    alt = sql.execute(
        "SELECT id, titel, text FROM artikel_suchtext WHERE artikel_id=?",
        (artikel_id,),
    ).fetchone()
    if alt is None:
        zeile = sql.execute(
            "INSERT INTO artikel_suchtext(artikel_id,titel,text,blase,indiziert) "
            "VALUES(?,?,?,?,1)", (artikel_id, titel, text, blase),
        ).lastrowid
        sql.execute(
            "INSERT INTO fts_index_artikel(rowid,titel,text) VALUES(?,?,?)",
            (zeile, titel, text),
        )
        return "neu"
    if (alt["titel"] or "") == titel and (alt["text"] or "") == text:
        return "unveraendert"
    sql.execute(
        "INSERT INTO fts_index_artikel(fts_index_artikel,rowid,titel,text) "
        "VALUES('delete',?,?,?)", (alt["id"], alt["titel"], alt["text"]),
    )
    sql.execute(
        "UPDATE artikel_suchtext SET titel=?, text=?, blase=? WHERE id=?",
        (titel, text, blase, alt["id"]),
    )
    sql.execute(
        "INSERT INTO fts_index_artikel(rowid,titel,text) VALUES(?,?,?)",
        (alt["id"], titel, text),
    )
    return "geaendert"


# ---------------------------------------------------------------------------
# Durchgang 1 -- bestehenden Aufnahmeweg laufen lassen, nicht nachbauen
# ---------------------------------------------------------------------------
def nachtragen(db) -> dict:
    try:
        from clayverse import baunotizen
        return baunotizen.aufnehmen(db) or {}
    except Exception as fehler:                    # nie den Rest blockieren
        return {"fehler": f"{type(fehler).__name__}: {fehler}"}


# ---------------------------------------------------------------------------
# Durchgang 2 -- Bauschritte als lesbare Artikel
# ---------------------------------------------------------------------------
def bauschritte(db) -> dict:
    if not BAUVERLAUF.exists():
        return {"fehler": f"{BAUVERLAUF} fehlt"}
    zaehler = {"gelesen": 0, "geschrieben": 0, "mit_begruendung": 0,
               "ohne_begruendung": 0, "suchtext_neu": 0, "suchtext_geaendert": 0,
               "suchtext_unveraendert": 0}
    jetzt = jetzt_iso()
    with db.tx() as sql:
        for rohzeile in BAUVERLAUF.read_text(encoding="utf-8").splitlines():
            rohzeile = rohzeile.strip()
            if not rohzeile:
                continue
            try:
                d = json.loads(rohzeile)
            except Exception:
                continue
            zaehler["gelesen"] += 1
            repo = d.get("repo") or "unbekannt"
            commit = (d.get("commit") or "").strip()
            if not commit:
                continue
            aid = f"bau-{repo}-{commit[:12]}"
            titel = (d.get("betreff") or "(ohne Betreff)").strip()
            text = artikeltext(d)
            begr = (d.get("begruendung") or "").strip()
            zaehler["mit_begruendung" if begr else "ohne_begruendung"] += 1
            hyp, geg = hypothesen(begr)
            # Welche Rohnotizen dieser Artikel zusammenfasst -- gemessen, nicht geraten.
            deckt_ab = [
                r["id"] for r in sql.execute(
                    "SELECT id FROM artikel WHERE art='baunotiz' AND "
                    "(id LIKE ? OR quell_hash=?)", (f"baunotiz-git-{commit}%", commit),
                )
            ]
            meta = {
                "herkunft": "bauverlauf.jsonl (git log, vier Repos)",
                "wieso": begr or None,
                "gehoert_zu": f"{repo} ({REPO_PFAD.get(repo, 'Pfad nicht hinterlegt')})",
                "hypothese": hyp,
                "gegenhypothese": geg,
                "erzeugt_von": "bau_ins_wiki.py",
                "timestamp": d.get("zeit"),
                "eingetragen_am": jetzt,
                "autor": d.get("autor"),
                "commit": commit,
                "repo": repo,
                "hat_begruendung": bool(begr),
                "deckt_ab": deckt_ab,
                "text": text,
            }
            sql.execute(UPSERT, (
                aid, "bau", titel,
                f"bauverlauf.jsonl · {repo}",
                hashlib.sha256(rohzeile.encode("utf-8")).hexdigest(),
                d.get("zeit"), json.dumps(meta, ensure_ascii=False),
                1, jetzt, "clayverse", d.get("autor") or "EntityOS",
                "bauverlauf.jsonl", None, None, "EntityOS", "eigen",
                "entityos", "gemessen",
            ))
            zaehler["geschrieben"] += 1
            zaehler["suchtext_" + auffindbar(sql, aid, titel, text, "entityos")] += 1
    return zaehler


# ---------------------------------------------------------------------------
# Durchgang 3 -- ALLE Bauaufzeichnungen auffindbar machen
# ---------------------------------------------------------------------------
# Quellen, deren Bauaufzeichnungen aus Git/GitHub stammen -- die schreibt
# dieses Skript, also darf es sie auch verbessern. Alles andere (vorfall aus
# `strom`/`journal`) gehoert der fremden Pipeline: dort nur Luecken fuellen.
EIGENE_QUELLEN = ("git-commit", "bauverlauf.jsonl", "github-ereignis",
                  "github-ereignis-tag")


def sichtbar_machen(db) -> dict:
    """Jede Bauaufzeichnung auffindbar machen.

    ⚠️ ZWEI REGIME, und der Unterschied ist keine Feinheit: bei den eigenen
    Quellen wird der Suchtext neu gesetzt, bei fremden nur eine FEHLENDE Zeile
    ergaenzt. Beim ersten Lauf fehlte diese Trennung -- 38 vorfall-Zeilen einer
    anderen Pipeline bekamen einen duerftigeren Suchtext ueberbuegelt (aus
    "…Tailscale… ergebnis: clayverse-alt = 100.116.119.67 im Tailnet…" wurde
    "…Tailscale…\nB0"). Wer eine Zeile zuerst schreibt, besitzt sie.
    """
    zaehler = {"eigene_gesetzt": 0, "eigene_unveraendert": 0,
               "fremde_luecke_gefuellt": 0, "fremde_unangetastet": 0}
    zeilen = list(db.db.execute(
        "SELECT a.id, a.titel, a.metadaten, a.sphaere, a.von_quelle, "
        "       s.artikel_id IS NOT NULL AS hat_suchtext "
        "FROM artikel a LEFT JOIN artikel_suchtext s ON s.artikel_id = a.id "
        "WHERE a.art IN ('baunotiz','vorfall')"))
    for anfang in range(0, len(zeilen), 500):          # Stueckweise, damit keine
        haufen = zeilen[anfang:anfang + 500]           # Transaktion ewig sperrt
        with db.tx() as sql:
            for r in haufen:
                eigen = (r["von_quelle"] or "") in EIGENE_QUELLEN
                if not eigen and r["hat_suchtext"]:
                    zaehler["fremde_unangetastet"] += 1
                    continue
                titel = r["titel"] or r["id"]
                text = suchtext_aus_metadaten(titel, r["metadaten"])
                lage = auffindbar(sql, r["id"], titel, text,
                                  r["sphaere"] or "entityos")
                if not eigen:
                    zaehler["fremde_luecke_gefuellt"] += 1
                elif lage == "unveraendert":
                    zaehler["eigene_unveraendert"] += 1
                else:
                    zaehler["eigene_gesetzt"] += 1
    return zaehler


def zaehle(db) -> dict:
    e = db.db.execute
    return {
        "bau_wissen_praefix": e("SELECT count(*) FROM artikel WHERE id LIKE 'bau-%' "
                                "OR id LIKE 'wissen-%'").fetchone()[0],
        "bauaufzeichnungen": e("SELECT count(*) FROM artikel WHERE art IN "
                               "('baunotiz','vorfall','bau')").fetchone()[0],
        "davon_auffindbar": e("SELECT count(*) FROM artikel a JOIN artikel_suchtext s "
                              "ON s.artikel_id=a.id WHERE a.art IN "
                              "('baunotiz','vorfall','bau')").fetchone()[0],
        "fts_zeilen": e("SELECT count(*) FROM fts_index_artikel").fetchone()[0],
    }


def main() -> None:
    db = UnifiedDB(WIKI)
    try:
        vorher = zaehle(db)
        print("VORHER  ", json.dumps(vorher, ensure_ascii=False))
        print("1 nachtragen   ", json.dumps(nachtragen(db), ensure_ascii=False)[:400])
        print("2 bauschritte  ", json.dumps(bauschritte(db), ensure_ascii=False))
        print("3 auffindbar   ", json.dumps(sichtbar_machen(db), ensure_ascii=False))
        nachher = zaehle(db)
        print("NACHHER ", json.dumps(nachher, ensure_ascii=False))
    finally:
        db.close()


if __name__ == "__main__":
    main()
