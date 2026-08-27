#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
benchmark_recall_wikidb.py -- LoCoMo-Methodik gegen wiki.db adaptiert
========================================================================

Auftrag Abschnitt 3: "External benchmark harnesses ... Adapt at least ONE
to run against wiki.db." Referenz: mempalace-main/benchmarks/locomo_bench.py
(MIT-Lizenz, lokal unter ~/Downloads/mempalace-main.zip).

Was uebernommen wurde: NUR die Retrieval-Recall-Metrik
    recall = |retrieved ∩ evidence| / |evidence|
(compute_retrieval_recall() in locomo_bench.py, Zeile ~975) -- das ist
reine Mengenlehre, KEIN Modellaufruf. Der Rest von locomo_bench.py
(Ingest von LoCoMo-Konversationen in eine frische mempalace-Palace,
optionales --llm-rerank, optionaler F1-Score per LLM) entfaellt: wir
haben weder den LoCoMo-Datensatz noch mempalace/ChromaDB hier, und der
Auftrag verbietet Modellaufrufe.

Was hier neu ist: die "Konversation + Belege" von LoCoMo wird durch
echte, im Graphen bereits vorhandene Wahrheit ersetzt -- kante-Zeilen
vom Typ 'stuetzt' oder 'evidence' (230 + 116 = 346 Kanten, gemessen).
Jede solche Kante sagt: Artikel `von` wird durch Artikel `nach` gestuetzt/
belegt. Das ist unser Ground-Truth-QA-Paar: Frage = Artikel `von`
(genauer: sein Titel als Suchanfrage), Beleg = Artikel `nach`.

Retrieval-Mechanismus zum Testen: SQLite FTS5 `fts_index_artikel`
(bereits vorhanden, wird von wiki.py selbst gepflegt) -- Volltextsuche
nach dem Titel des Fragen-Artikels, Top-K nach FTS5-Rang, minus den
Fragen-Artikel selbst. KEIN Embedding, KEIN Modell -- reine BM25-artige
FTS5-Rangfolge, exakt im Sinne von locomo_bench.py --mode raw (kein
--llm-rerank, kein --mode palace).

Nutzung:
    python3 benchmark_recall_wikidb.py [--top-k 10] [--db /var/lib/clay/wiki.db]
"""

import argparse
import json
import re
import sqlite3
import sys
from collections import defaultdict

# Modulgrenze: dieses Werkzeug oeffnet die Datenbank NICHT mehr selbst.
# udb ist die Vordertuer -- busy_timeout, query_only und Wiederholung
# stehen dort an EINER Stelle statt hier noch einmal. Rein lesend --
# passt zu udb.verbindung(), das ebenfalls nur-lesend ist.
sys.path.insert(0, "/opt/unifieddb")
import udb

DB_PATH = "/var/lib/clay/wiki.db"
EVIDENCE_ARTS = ("stuetzt", "evidence")


def connect(path):
    conn = udb.verbindung(path)
    conn.row_factory = sqlite3.Row
    return conn


def build_qa_pairs(conn):
    """Ground truth: {frage_artikel_id: {beleg_artikel_id, ...}}"""
    pairs = defaultdict(set)
    kinds = {}
    placeholders = ",".join("?" for _ in EVIDENCE_ARTS)
    for r in conn.execute(
        f"""SELECT k.von, k.nach, k.art FROM kante k
            JOIN artikel av ON av.id = k.von
            JOIN artikel an ON an.id = k.nach
            WHERE k.art IN ({placeholders})""",
        EVIDENCE_ARTS,
    ):
        pairs[r["von"]].add(r["nach"])
        kinds[r["von"]] = r["art"]
    return pairs, kinds


def fts_query_terms(titel: str) -> str:
    """Sanitize a titel into a safe FTS5 MATCH expression: jedes
    Wort-Token einzeln gequotet, mit OR verbunden (findet Artikel, die
    IRGENDEIN Titelwort enthalten, FTS5 rankt nach Relevanz)."""
    tokens = re.findall(r"[A-Za-z0-9À-ɏ]+", titel or "")
    tokens = [t for t in tokens if len(t) >= 3][:12]
    if not tokens:
        return ""
    return " OR ".join(f'"{t}"' for t in tokens)


def retrieve_top_k(conn, query_artikel_id: str, titel: str, top_k: int) -> list[str]:
    expr = fts_query_terms(titel)
    if not expr:
        return []
    try:
        rows = conn.execute(
            """
            SELECT a.id, bm25(fts_index_artikel) AS rang
            FROM fts_index_artikel f
            JOIN artikel_suchtext s ON s.id = f.rowid
            JOIN artikel a ON a.id = s.artikel_id
            WHERE fts_index_artikel MATCH ?
              AND a.id != ?
            ORDER BY rang LIMIT ?
            """,
            (expr, query_artikel_id, top_k),
        ).fetchall()
    except sqlite3.OperationalError:
        return []
    return [r["id"] for r in rows]


def compute_retrieval_recall(retrieved_ids, evidence_ids) -> float:
    """1:1 aus locomo_bench.py uebernommen (reine Mengenlehre)."""
    if not evidence_ids:
        return 1.0
    found = sum(1 for eid in evidence_ids if eid in retrieved_ids)
    return found / len(evidence_ids)


def run(db_path: str, top_k: int):
    conn = connect(db_path)
    # artikel_suchtext.artikel_id herausfinden (Spaltenname pruefen)
    cols = {r["name"] for r in conn.execute("PRAGMA table_info(artikel_suchtext)")}
    if "artikel_id" not in cols:
        # Fallback: FTS content_rowid war 'id' -> artikel_suchtext.id koennte
        # direkt = artikel.rowid/id sein statt einer artikel_id-Spalte.
        print(f"WARNUNG: artikel_suchtext hat keine 'artikel_id'-Spalte, gefunden: {cols}")
        conn.close()
        return

    pairs, kinds = build_qa_pairs(conn)
    print(f"Ground-Truth-QA-Paare (kante.art in {EVIDENCE_ARTS}): {len(pairs)} Fragen-Artikel, "
          f"{sum(len(v) for v in pairs.values())} Beleg-Kanten insgesamt")

    titles = {}
    for r in conn.execute("SELECT id, titel FROM artikel WHERE id IN ({})".format(
        ",".join("?" for _ in pairs)
    ), tuple(pairs)):
        titles[r["id"]] = r["titel"]

    all_recall = []
    zero = 0
    by_kind = defaultdict(list)
    log = []
    for qid, evidence in pairs.items():
        titel = titles.get(qid)
        retrieved = retrieve_top_k(conn, qid, titel, top_k)
        recall = compute_retrieval_recall(retrieved, evidence)
        all_recall.append(recall)
        by_kind[kinds[qid]].append(recall)
        if recall == 0.0:
            zero += 1
        log.append({"frage": qid, "titel": titel, "beleg": sorted(evidence),
                     "retrieved_top_k": retrieved, "recall": recall})

    conn.close()

    if not all_recall:
        print("Keine QA-Paare gefunden -- Benchmark kann nicht laufen.")
        return

    avg = sum(all_recall) / len(all_recall)
    print(f"\n{'=' * 60}")
    print(f"Retrieval Recall@{top_k} (FTS5, adaptiert aus locomo_bench.py, 0 Modellaufrufe)")
    print(f"{'=' * 60}")
    print(f"  Fragen insgesamt : {len(all_recall)}")
    print(f"  Durchschnitt     : {avg:.3f}")
    print(f"  Recall = 0       : {zero} ({zero / len(all_recall) * 100:.1f}%)")
    for kind, vals in by_kind.items():
        print(f"  Kategorie '{kind}': n={len(vals)} avg_recall={sum(vals)/len(vals):.3f}")
    print(f"{'=' * 60}\n")

    out = "/opt/clayverse/werkzeug/batches/benchmark_recall_wikidb_result.json"
    try:
        with open(out, "w") as f:
            json.dump({"top_k": top_k, "avg_recall": avg, "n": len(all_recall),
                       "zero_recall_count": zero, "by_kind": {k: sum(v)/len(v) for k, v in by_kind.items()},
                       "log": log}, f, indent=2, ensure_ascii=False)
        print(f"Ergebnis gespeichert: {out}")
    except Exception as e:
        print(f"(Ergebnis-Datei nicht geschrieben: {e})")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--top-k", type=int, default=10)
    p.add_argument("--db", default=DB_PATH)
    ns = p.parse_args()
    run(ns.db, ns.top_k)
