"""Faires Messgeraet: alt (FTS/corpus_lookup) vs paket() -- auf ZWEI Achsen.

WARUM
  Der vorhandene Benchmark goldsatz.json (siehe messgeraet.py) misst nur
  woertliche Titel-Wort-Treffer -- das ist FTS' Heimspiel. paket()s
  eigentliche Staerke (verknuepftes Wissen ueber den Graphen finden) wird
  von goldsatz.json GAR NICHT gemessen. Dieses Skript ergaenzt eine zweite,
  ASSOZIATIVE Achse, deren Ground Truth mechanisch aus echten Graphkanten
  abgeleitet ist (kante-Tabelle in wiki.db), nicht erfunden.

GEPRUEFTE VORHANDENE MESSGERAETE (bevor dies gebaut wurde)
  - messgeraet.py: misst NUR paket() (ankerquote/treffsicher/auffindbar/
    latenz) gegen goldsatz.json. Kein Vergleich zu alt/FTS.
  - vorprozessor.py needle_test(), beweis_verweigerung(), lese_kosten_vergleich():
    pruefen paket()s Zugriffskontrolle bzw. eine einzelne Needle-Frage, nicht
    Retrieval-Qualitaet im Vergleich zu einem zweiten Retriever.
  - goldsatz2.py: baut goldsatz.json (Achse A, wörtlich, Seltenheits-Woerter).
    Bleibt unveraendert, wird hier als Achse A WIEDERVERWENDET.
  - normal_gegenseite.py, andere abruf/*.py Skripte: eigene Diagnosen (Karte,
    Wegehierarchie, Kalibrierung), kein A/B zwischen den zwei Retrievern.
  -> Nichts davon vergleicht alt vs. paket() auf derselben Frage. Deshalb neu
     gebaut, additiv, nichts Bestehendes veraendert.

WIE DIE ASSOZIATIVE GROUND TRUTH ENTSTEHT (mechanisch, dokumentiert)
  1. Anker = Artikel mit artikel.art IN ('hypothese','gegenhypothese'), die
     UEBER MINDESTENS EINE "semantische" Kante mit einem anderen Artikel
     verbunden sind. Semantisch = kante.art IN SEM_EDGE_ARTS (siehe unten) --
     bewusst OHNE die Datei-/Versions-Buchhaltungskanten (geschwister_*,
     gleicher_inhalt, verdichtet_aus, nachfolge_version, ...), die den
     Dateibaum spiegeln, nicht Wissenszusammenhang.
  2. SEM_EDGE_ARTS = widerspricht, attacks, eltern_hypothese, stuetzt,
     related_claim_ids -- das sind genau die Kantentypen, die paket() selbst
     fuer 'codependenzen'/'gegenseite'/Hypothesen-Hop als inhaltlich
     behandelt (siehe _gegenseite_ids in paket.py: widerspricht/attacks/
     CHALLENGES/CONTRADICTS/SUPERSEDES als Gegenseite-Kantentypen).
  3. Anker deterministisch nach artikel.id sortiert (kein Zufall) -> exakt
     reproduzierbar. Stand 2026-08-19: 93 solcher Anker im Graphen -- das ist
     die volle Grundgesamtheit (kein Sampling noetig, < 120 Ziel).
  4. Frage = der Ankertitel VERBATIM (mechanisch, nichts erfunden), bei
     Ueberlaenge (>240 Zeichen) an der letzten Wortgrenze <=240 gekappt.
  5. Ground-Truth-Menge = alle ueber SEM_EDGE_ARTS direkt verbundenen
     Nachbar-Artikel-IDs (beide Kantenrichtungen), OHNE den Anker selbst.
     Die Kante IST die Wahrheit -- kein Modell hat sie geschaetzt.

GRENZEN (ehrlich benannt)
  - Setzt voraus, dass die Kanten im Graphen korrekt sind (kein Audit der
    Kantenqualitaet selbst).
  - 93 Anker sind eine kleine Stichprobe fuer seltene Kantentypen
    (widerspricht/attacks je nur 20 Paare, eltern_hypothese nur 8) --
    Konfidenzintervalle entsprechend breit, nicht als Promille-genau lesen.
  - 'stuetzt' und 'related_claim_ids' verbinden teils auch andere Artikelarten
    (begriff, forschungsergebnis) -- nur die Kanten VOM/ZUM Anker zaehlen,
    nicht Ketten ueber Zwischenartikel.
  - Anker-Titel sind oft englische Forschungspropositionen (Frank/Qwen23-
    Forschung), nicht generische Fragen -- realistischer Korpusinhalt, aber
    kein Diversitaetsanspruch ueber alle Themenbereiche des Wikis.

WARUM corpus_lookup() NEU IMPLEMENTIERT STATT INSTANZIIERT
  WorldAssembler(db) braucht ein UnifiedDB(wiki.db) -- dessen __init__ schreibt
  bei JEDEM Oeffnen in die meta-Tabelle (canonical_identity wird
  bedingungslos ueberschrieben, u.a.). Das verletzt die Auflage "REIN LESEND
  / keine DB mutieren" dieses Evals. Deshalb: SQL und Tokenisierung 1:1 aus
  corpus_lookup()/_fts_terms() in
  /opt/entityos/the artefact/clayverse/retrieval.py (Stand 2026-08-19)
  uebernommen, nur ueber eine read-only sqlite3-Verbindung ausgefuehrt.
  Semantik unveraendert, keine eigene Ranking-/Suchlogik hinzugefuegt.
  paket() dagegen wird ECHT aufgerufen (conn=_connect(), wie messgeraet.py
  es fuer den etablierten Pfad bereits tut) -- sein dokumentierter
  Nebeneffekt (vp_paket_log + Lernschritt) ist laut Auftrag Teil des Entwurfs
  und bleibt unangetastet.

LATENZ FAIR GEMESSEN
  Cache wird vor der Messung warmgelaufen (ein voller Durchlauf ueber alle
  Fragen wird verworfen), erst danach zaehlt die Zeit -- sonst waere
  paket()s Kaltstart (~2s) gegen FTS' Kaltstart (~ms) unfair vermischt.
  Ehrlich benannt: die gemessene Latenz ist der WIEDERHOLUNGSFALL (dieselbe
  Frage im Vorlauf schon einmal gestellt), nicht die Kaltstart-Erstantwort
  auf eine neue Frage -- paket()s Plan-Cache (vp_plan_cache) greift dabei.

NUR LESEND. Keine Schema-Aenderung, kein systemctl, kein rm.
"""
from __future__ import annotations

import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P  # _connect (rw, fuer paket()s dok. Nebeneffekt), _ro (read-only)

HIER = Path(__file__).resolve().parent
GOLD_A = "/opt/unifieddb/udb/abruf/goldsatz.json"          # Achse A, woertlich -- unveraendert wiederverwendet
GOLD_B = str(HIER / "gold_assoc.json")                      # Achse B, assoziativ -- hier erzeugt
ERGEBNIS = str(HIER / "retrieval_fair_eval_ergebnis.json")

SEM_EDGE_ARTS = ("widerspricht", "attacks", "eltern_hypothese", "stuetzt", "related_claim_ids")
ANCHOR_ARTS = ("hypothese", "gegenhypothese")
MAX_TITEL_LAENGE = 240

MATCH_K = 5          # gemeinsames K fuer den fairen Kopf-an-Kopf-Vergleich (= corpus_lookup()s CORPUS_MAX_HITS)
PAKET_DEFAULT_BUDGET = 8  # paket()s eigener Standard (CAP_RESULT_DEFAULT), zusaetzlich als Realbetrieb-Referenz


# ── Achse B: Gold-Satz aus dem Graphen ableiten (read-only) ────────────────

def _kappen(titel: str, n: int = MAX_TITEL_LAENGE) -> str:
    titel = (titel or "").strip()
    if len(titel) <= n:
        return titel
    kurz = titel[:n]
    letzte = kurz.rfind(" ")
    return kurz[:letzte] if letzte > 0 else kurz


def build_gold_assoc(limit: int = 120) -> list[dict]:
    c = P._ro()
    qm_sem = ",".join("?" for _ in SEM_EDGE_ARTS)
    qm_anchor = ",".join("?" for _ in ANCHOR_ARTS)

    anker_rows = c.execute(
        f"""SELECT DISTINCT a.id AS id, a.art AS art, a.titel AS titel
            FROM artikel a
            JOIN kante k ON (k.von = a.id OR k.nach = a.id)
            WHERE a.art IN ({qm_anchor}) AND k.art IN ({qm_sem})
            ORDER BY a.id ASC""",
        list(ANCHOR_ARTS) + list(SEM_EDGE_ARTS),
    ).fetchall()

    satz = []
    for row in anker_rows[:limit]:
        aid, aart, atitel = row["id"], row["art"], row["titel"]
        kanten = c.execute(
            f"""SELECT von, nach, art FROM kante
                WHERE (von = ? OR nach = ?) AND art IN ({qm_sem})""",
            [aid, aid] + list(SEM_EDGE_ARTS),
        ).fetchall()

        nachbarn: dict[str, list[str]] = defaultdict(list)
        for k in kanten:
            nid = k["nach"] if k["von"] == aid else k["von"]
            if nid == aid:
                continue
            nachbarn[nid].append(k["art"])
        if not nachbarn:
            continue

        nid_list = sorted(nachbarn.keys())
        qm_n = ",".join("?" for _ in nid_list)
        titel_by_id = {r["id"]: (r["titel"], r["art"]) for r in c.execute(
            f"SELECT id, titel, art FROM artikel WHERE id IN ({qm_n})", nid_list
        )}

        satz.append({
            "anchor_id": aid,
            "anchor_art": aart,
            "anchor_titel_voll": atitel,
            "frage": _kappen(atitel),
            "erwartet": nid_list,
            "erwartet_meta": [
                {"id": nid, "titel": (titel_by_id.get(nid, ("", ""))[0] or "")[:80],
                 "art": titel_by_id.get(nid, ("", ""))[1], "edge_arten": sorted(set(nachbarn[nid]))}
                for nid in nid_list
            ],
        })
    c.close()
    return satz


# ── alt/FTS: SQL+Tokenisierung 1:1 aus retrieval.py corpus_lookup()/_fts_terms() ──

_STOPWORDS = frozenset("""
    aber alle als also andere auch auf aus bei bin bis das dass dein den der des
    dem die dies diese doch dort durch ein eine einem einen einer eines etwas fuer
    hat hier ich ihr ist jetzt kann kein mehr mein mit muss nach nicht noch nur
    oder ohne sehr sein sich sind soll ueber und uns unter viel vom von war was
    wenn wer wie wir wird wo zum zur
    the and for are but not you all any can her was one our out has had his how
    its who did yes with this that from they what when will your
""".split())


def _fts_terms(query: str) -> list[str]:
    raw = "".join(ch if ch.isalnum() else " " for ch in (query or "")).split()
    seen, out = set(), []
    for t in raw:
        low = t.lower()
        if len(low) < 3 or low in _STOPWORDS or low in seen:
            continue
        seen.add(low)
        out.append('"' + low + '"')
        if len(out) >= 8:
            break
    return out


def alt_lookup(c, query: str, max_hits: int = MATCH_K) -> list[dict]:
    """Reimplementierung von WorldAssembler.corpus_lookup() -- reiner SELECT,
    identische SQL/Reihenfolge/AND-dann-OR-Fallback, nur ueber eine
    read-only Verbindung statt UnifiedDB (siehe Modul-Docstring)."""
    terms = _fts_terms(query)
    if not terms:
        return []
    for mode, match in (("AND", " AND ".join(terms)), ("OR", " OR ".join(terms))):
        try:
            rows = c.execute(
                "SELECT s.artikel_id AS artikel_id, s.titel AS titel, "
                "       substr(s.text,1,260) AS ausschnitt "
                "FROM fts_index_artikel f "
                "JOIN artikel_suchtext s ON s.id = f.rowid "
                "WHERE fts_index_artikel MATCH ? "
                "ORDER BY bm25(fts_index_artikel) LIMIT ?",
                (match, max_hits),
            ).fetchall()
        except Exception:
            return []
        if rows:
            return [{"artikel_id": r["artikel_id"], "titel": r["titel"], "treffer_art": mode} for r in rows]
    return []


# ── Messung ──────────────────────────────────────────────────────────────

def _perc(sorted_vals: list[float], p: float) -> float:
    if not sorted_vals:
        return 0.0
    idx = min(len(sorted_vals) - 1, int(p * len(sorted_vals)))
    return sorted_vals[idx]


def _achse_a(c_rw, c_ro, satz: list[dict], budget_paket: int, k_alt: int = MATCH_K) -> dict:
    """Achse A (woertlich): erwartet ist ein einzelnes id. Recall + Praezision
    (1/|Treffer| falls Treffer dabei) + Latenz, je Retriever."""
    out = {}
    for retr in ("alt_fts", "paket"):
        # Warmlauf (verworfen)
        for e in satz:
            if retr == "paket":
                P.paket(e["frage"], budget=budget_paket, conn=c_rw)
            else:
                alt_lookup(c_ro, e["frage"], max_hits=k_alt)

        treffer_n = 0
        praez_werte = []
        zeiten = []
        for e in satz:
            t0 = time.perf_counter()
            if retr == "paket":
                pk = P.paket(e["frage"], budget=budget_paket, conn=c_rw)
                ids = [t.get("id") for t in pk.get("treffer", []) if isinstance(t, dict)]
            else:
                rows = alt_lookup(c_ro, e["frage"], max_hits=k_alt)
                ids = [r["artikel_id"] for r in rows]
            zeiten.append((time.perf_counter() - t0) * 1000)

            erwartet = e["erwartet"]
            if erwartet in ids:
                treffer_n += 1
                praez_werte.append(1.0 / len(ids))
            elif ids:
                praez_werte.append(0.0)

        n = len(satz)
        zeiten_sortiert = sorted(zeiten)
        out[retr] = {
            "n": n,
            "recall_pct": round(100 * treffer_n / n, 1),
            "praezision_macro": round(statistics.mean(praez_werte), 4) if praez_werte else None,
            "latenz_median_ms": round(statistics.median(zeiten), 2),
            "latenz_p95_ms": round(_perc(zeiten_sortiert, 0.95), 2),
        }
    return out


def _achse_b(c_rw, c_ro, satz: list[dict], budget_paket: int, k_alt: int = MATCH_K) -> dict:
    """Achse B (assoziativ): erwartet ist eine MENGE verlinkter Nachbarn.
    Der Anker selbst wird aus den Treffern entfernt, bevor gemessen wird --
    ihn wiederzufinden ist trivialer Wortabgleich, nicht das Verknuepfte."""
    out = {}
    for retr in ("alt_fts", "paket"):
        for e in satz:
            if retr == "paket":
                P.paket(e["frage"], budget=budget_paket, conn=c_rw)
            else:
                alt_lookup(c_ro, e["frage"], max_hits=k_alt)

        recall_fracs, any_hit, full_hit = [], 0, 0
        praez_werte, deckung = [], 0
        anker_selbstfund = 0
        zeiten = []
        for e in satz:
            anchor = e["anchor_id"]
            truth = set(e["erwartet"])
            t0 = time.perf_counter()
            if retr == "paket":
                pk = P.paket(e["frage"], budget=budget_paket, conn=c_rw)
                ids_roh = [t.get("id") for t in pk.get("treffer", []) if isinstance(t, dict)]
            else:
                rows = alt_lookup(c_ro, e["frage"], max_hits=k_alt)
                ids_roh = [r["artikel_id"] for r in rows]
            zeiten.append((time.perf_counter() - t0) * 1000)

            if anchor in ids_roh:
                anker_selbstfund += 1
            got = set(ids_roh) - {anchor}

            hit = truth & got
            recall_fracs.append(len(hit) / len(truth))
            if hit:
                any_hit += 1
            if hit == truth:
                full_hit += 1
            if got:
                deckung += 1
                praez_werte.append(len(hit) / len(got))

        n = len(satz)
        zeiten_sortiert = sorted(zeiten)
        out[retr] = {
            "n": n,
            "recall_macro_pct": round(100 * statistics.mean(recall_fracs), 1),
            "any_hit_rate_pct": round(100 * any_hit / n, 1),
            "full_hit_rate_pct": round(100 * full_hit / n, 1),
            "praezision_macro": round(statistics.mean(praez_werte), 4) if praez_werte else None,
            "deckung_nichtleer_pct": round(100 * deckung / n, 1),
            "anker_selbstfund_pct": round(100 * anker_selbstfund / n, 1),
            "latenz_median_ms": round(statistics.median(zeiten), 2),
            "latenz_p95_ms": round(_perc(zeiten_sortiert, 0.95), 2),
        }
    return out


def run_eval() -> dict:
    satz_a = json.load(open(GOLD_A, encoding="utf-8"))
    satz_b = json.load(open(GOLD_B, encoding="utf-8"))

    c_rw = P._connect()
    P._ensure_vp_tables(c_rw)
    c_ro = P._ro()

    ergebnis = {
        "stand": "2026-08-19",
        "achse_a_woertlich": {
            "beschreibung": "goldsatz.json (120 Fragen, aus seltenen Titelwoertern gebaut, unveraendert)",
            "matched_k5": _achse_a(c_rw, c_ro, satz_a, budget_paket=MATCH_K),
            "paket_eigener_default_budget8": _achse_a(c_rw, c_ro, satz_a, budget_paket=PAKET_DEFAULT_BUDGET)["paket"],
        },
        "achse_b_assoziativ": {
            "beschreibung": f"gold_assoc.json ({len(satz_b)} Anker, graph-abgeleitet ueber {SEM_EDGE_ARTS})",
            "matched_k5": _achse_b(c_rw, c_ro, satz_b, budget_paket=MATCH_K),
            "paket_eigener_default_budget8": _achse_b(c_rw, c_ro, satz_b, budget_paket=PAKET_DEFAULT_BUDGET)["paket"],
            "alt_fts_bei_k8_diagnostisch": {
                "hinweis": "CORPUS_MAX_HITS ist in retrieval.py auf 5 hartcodiert -- k=8 ist hier NUR eine Diagnose, ob mehr Treffer allein die Luecke schliessen wuerde, kein realer Produktionspfad.",
                **_achse_b(c_rw, c_ro, satz_b, budget_paket=PAKET_DEFAULT_BUDGET, k_alt=PAKET_DEFAULT_BUDGET)["alt_fts"],
            },
        },
    }

    c_rw.close()
    c_ro.close()
    return ergebnis


if __name__ == "__main__":
    modus = sys.argv[1] if len(sys.argv) > 1 else "eval"
    if modus == "build":
        satz = build_gold_assoc()
        json.dump(satz, open(GOLD_B, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{len(satz)} assoziative Anker -> {GOLD_B}")
        kanten_verteilung = defaultdict(int)
        for e in satz:
            for m in e["erwartet_meta"]:
                for art in m["edge_arten"]:
                    kanten_verteilung[art] += 1
        print("Kantenarten in der Ground Truth:", dict(sorted(kanten_verteilung.items(), key=lambda x: -x[1])))
        groessen = [len(e["erwartet"]) for e in satz]
        print(f"Nachbarn je Anker: min={min(groessen)} max={max(groessen)} median={statistics.median(groessen)}")
    else:
        erg = run_eval()
        print(json.dumps(erg, ensure_ascii=False, indent=2))
        json.dump(erg, open(ERGEBNIS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\n-> {ERGEBNIS}")
