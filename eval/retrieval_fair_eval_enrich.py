"""Dritter Arm: 'enrich' (Smart-Routing) neben alt/FTS und paket(), auf
DENSELBEN zwei Achsen wie retrieval_fair_eval.py (woertlich/goldsatz.json,
assoziativ/gold_assoc.json) UND auf einer REALISTISCHEN MISCHUNG beider
Achsen zusammen (213 Fragen: 120 woertlich + 93 assoziativ) -- das misst den
echten Latenz-Aufschlag im Normalbetrieb, nicht nur den Bestfall/Worstfall
je Achse fuer sich.

Baut auf retrieval_fair_eval.py auf (importiert dessen Bausteine 1:1, AENDERT
NICHTS daran -- additiv, eigene neue Datei): GOLD_A/GOLD_B, alt_lookup(),
_fts_terms(), P (udb.abruf.paket), MATCH_K, PAKET_DEFAULT_BUDGET. Der
enrich-Trigger und die Merge-Logik hier sind eine 1:1-Nachbildung von
WorldAssembler.corpus_lookup_enrich() in
/opt/entityos/the artefact/clayverse/retrieval.py (Stand 2026-08-19) --
gleicher Grund wie im Originalskript dokumentiert: WorldAssembler braucht
UnifiedDB(wiki.db), dessen __init__ bei jedem Oeffnen die meta-Tabelle
beschreibt, was die REIN-LESEND-Auflage dieses Evals verletzen wuerde. Die
Assoziativitaets-Heuristik (ASSOZIATIVE_BEGRIFFE) wird dagegen ECHT aus
clayverse.retrieval IMPORTIERT (Modul-Ebene, keine Instanziierung noetig) --
EINE Quelle fuer das Woerterset, Produktion und Eval pruefen dieselbe Regel.

NUR LESEND. Keine Schema-Aenderung, kein systemctl, kein rm.
"""
from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, "/opt/unifieddb")
sys.path.insert(0, "/opt/entityos/the artefact")

from udb.abruf import paket as P  # noqa: E402  -- _connect (rw, paket()s dok. Nebeneffekt), _ro (read-only)
from clayverse.retrieval import ASSOZIATIVE_BEGRIFFE, _ist_assoziative_frage  # noqa: E402 -- Modul-Ebene, keine DB

# Aus retrieval_fair_eval.py 1:1 wiederverwendet (gleiche Datei, gleiche Pfade,
# additiv importiert -- KEINE Aenderung an der Originaldatei).
sys.path.insert(0, str(Path(__file__).resolve().parent))
import importlib.util as _ilu
_spec = _ilu.spec_from_file_location(
    "retrieval_fair_eval", "/opt/entityos/eval/retrieval_fair_eval.py")
_fair = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_fair)

alt_lookup = _fair.alt_lookup
GOLD_A = _fair.GOLD_A
GOLD_B = _fair.GOLD_B
MATCH_K = _fair.MATCH_K
PAKET_DEFAULT_BUDGET = _fair.PAKET_DEFAULT_BUDGET
_perc = _fair._perc

HIER = Path(__file__).resolve().parent
ERGEBNIS = "/opt/entityos/eval/retrieval_fair_eval_enrich_ergebnis.json"


def enrich_lookup(c_rw, c_ro, query: str, budget_paket: int, k_alt: int = MATCH_K):
    """1:1-Nachbildung von WorldAssembler.corpus_lookup_enrich(): FTS zuerst,
    paket() nur dazu, wenn FTS leer war ODER die Frage assoziativ heisst.
    Merge: FTS zuerst, paket() fuellt Luecken (dedupe per id), Budget=k_alt
    (== CORPUS_MAX_HITS in Produktion). Gibt (ids, feuerte_paket, grund) zurueck
    -- ids ist die einzige fuer Recall/Praezision relevante Groesse hier, die
    Zusatz-Hypothesen/Gegenseite-Eintraege aus corpus_lookup_enrich sind reiner
    Text-Kontext ohne artikel_id und wuerden die Metrik nicht veraendern."""
    fts_rows = alt_lookup(c_ro, query, max_hits=k_alt)
    fts_ids = [r["artikel_id"] for r in fts_rows]

    grund = None
    if not fts_rows:
        grund = "fts_leer"
    elif _ist_assoziative_frage(query):
        grund = "assoziative_absicht"

    if grund is None:
        return fts_ids, False, None

    pk = P.paket(query, budget=budget_paket, conn=c_rw)
    v2_ids = [t.get("id") for t in pk.get("treffer", []) if isinstance(t, dict)]

    merged = list(fts_ids)
    gesehen = set(merged)
    for aid in v2_ids:
        if len(merged) >= k_alt:
            break
        if aid in gesehen:
            continue
        gesehen.add(aid)
        merged.append(aid)
    return merged, True, grund


def _feuerrate_latenz(c_rw, c_ro, satz: list[dict], budget_paket: int, k_alt: int = MATCH_K) -> dict:
    """Schema-unabhaengig (braucht nur e['frage']) -- fuer die realistische
    Mischung aus BEIDEN Achsen. Berichtet NUR Feuerrate + Latenz, KEINE
    Recall/Praezision: goldsatz.json (erwartet=eine ID) und gold_assoc.json
    (erwartet=eine Menge, anchor_id separat) haben unterschiedliche Ground-
    Truth-Formen -- ein gemeinsamer Trefferwert ueber beide waere eine
    erfundene Kennzahl ohne saubere Definition, deshalb bewusst weggelassen."""
    for e in satz:
        enrich_lookup(c_rw, c_ro, e["frage"], budget_paket, k_alt)  # Warmlauf, verworfen

    zeiten, feuer_n, gruende = [], 0, {}
    for e in satz:
        t0 = time.perf_counter()
        _ids, feuerte, grund = enrich_lookup(c_rw, c_ro, e["frage"], budget_paket, k_alt)
        zeiten.append((time.perf_counter() - t0) * 1000)
        if feuerte:
            feuer_n += 1
            gruende[grund] = gruende.get(grund, 0) + 1

    n = len(satz)
    zsort = sorted(zeiten)
    return {
        "n": n,
        "feuerrate_pct": round(100 * feuer_n / n, 1),
        "feuergruende": gruende,
        "latenz_median_ms": round(statistics.median(zeiten), 2),
        "latenz_p95_ms": round(_perc(zsort, 0.95), 2),
        "latenz_mean_ms": round(statistics.mean(zeiten), 2),
    }


def _achse(c_rw, c_ro, satz: list[dict], achse: str, budget_paket: int, k_alt: int = MATCH_K) -> dict:
    # Warmlauf (verworfen) -- exakt wie im Originalskript, sonst waere
    # paket()s Kaltstart unfair in die Messung gemischt.
    for e in satz:
        enrich_lookup(c_rw, c_ro, e["frage"], budget_paket, k_alt)

    zeiten, feuer_n = [], 0
    if achse == "a":
        treffer_n, praez_werte = 0, []
    else:
        recall_fracs, any_hit, full_hit = [], 0, 0
        praez_werte, deckung, anker_selbstfund = [], 0, 0

    for e in satz:
        t0 = time.perf_counter()
        ids, feuerte, grund = enrich_lookup(c_rw, c_ro, e["frage"], budget_paket, k_alt)
        zeiten.append((time.perf_counter() - t0) * 1000)
        if feuerte:
            feuer_n += 1

        if achse == "a":
            erwartet = e["erwartet"]
            if erwartet in ids:
                treffer_n += 1
                praez_werte.append(1.0 / len(ids))
            elif ids:
                praez_werte.append(0.0)
        else:
            anchor = e["anchor_id"]
            truth = set(e["erwartet"])
            if anchor in ids:
                anker_selbstfund += 1
            got = set(ids) - {anchor}
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
    zsort = sorted(zeiten)
    basis = {
        "n": n,
        "feuerrate_pct": round(100 * feuer_n / n, 1),
        "latenz_median_ms": round(statistics.median(zeiten), 2),
        "latenz_p95_ms": round(_perc(zsort, 0.95), 2),
        "latenz_mean_ms": round(statistics.mean(zeiten), 2),
    }
    if achse == "a":
        basis.update({
            "recall_pct": round(100 * treffer_n / n, 1),
            "praezision_macro": round(statistics.mean(praez_werte), 4) if praez_werte else None,
        })
    else:
        basis.update({
            "recall_macro_pct": round(100 * statistics.mean(recall_fracs), 1),
            "any_hit_rate_pct": round(100 * any_hit / n, 1),
            "full_hit_rate_pct": round(100 * full_hit / n, 1),
            "praezision_macro": round(statistics.mean(praez_werte), 4) if praez_werte else None,
            "deckung_nichtleer_pct": round(100 * deckung / n, 1),
            "anker_selbstfund_pct": round(100 * anker_selbstfund / n, 1),
        })
    return basis


def run_eval() -> dict:
    satz_a = json.load(open(GOLD_A, encoding="utf-8"))
    satz_b = json.load(open(GOLD_B, encoding="utf-8"))

    c_rw = P._connect()
    P._ensure_vp_tables(c_rw)
    c_ro = P._ro()

    ergebnis = {
        "stand": "2026-08-19",
        "trigger": {
            "beschreibung": "paket() feuert, wenn FTS 0 Treffer lieferte ODER die Frage "
                             "gegen ASSOZIATIVE_BEGRIFFE (clayverse.retrieval, Modul-Ebene) trifft.",
            "begriffe_anzahl": len(ASSOZIATIVE_BEGRIFFE),
        },
        "achse_a_woertlich_enrich": {
            "beschreibung": "goldsatz.json (120 Fragen), enrich-Pfad, Budget=MATCH_K(5)",
            **_achse(c_rw, c_ro, satz_a, "a", budget_paket=MATCH_K),
        },
        "achse_b_assoziativ_enrich": {
            "beschreibung": f"gold_assoc.json ({len(satz_b)} Anker), enrich-Pfad, Budget=MATCH_K(5)",
            **_achse(c_rw, c_ro, satz_b, "b", budget_paket=MATCH_K),
        },
        "achse_b_assoziativ_enrich_paket_budget8": {
            "beschreibung": "wie oben, aber paket() wird mit seinem eigenen Default-Budget (8) "
                             "aufgerufen, wenn es feuert -- Realbetrieb-Referenz wie im Originalskript.",
            **_achse(c_rw, c_ro, satz_b, "b", budget_paket=PAKET_DEFAULT_BUDGET),
        },
        "realistische_mischung": {
            "beschreibung": (
                f"Alle {len(satz_a)} woertlichen + {len(satz_b)} assoziativen Fragen zusammen "
                f"({len(satz_a) + len(satz_b)} gesamt) durch denselben enrich-Pfad -- das ist der "
                "Latenz-Aufschlag, den ein Normalbetrieb mit gemischten Fragen tatsaechlich traegt, "
                "nicht der Bestfall (nur woertlich) oder der Worstfall (nur assoziativ). NUR "
                "Feuerrate/Latenz (siehe _feuerrate_latenz-Docstring, warum keine Recall-Zahl)."
            ),
            **_feuerrate_latenz(c_rw, c_ro, satz_a + satz_b, budget_paket=MATCH_K),
        },
    }

    c_rw.close()
    c_ro.close()
    return ergebnis


if __name__ == "__main__":
    erg = run_eval()
    print(json.dumps(erg, ensure_ascii=False, indent=2))
    json.dump(erg, open(ERGEBNIS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n-> {ERGEBNIS}")
