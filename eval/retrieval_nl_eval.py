"""Vierter Arm: NATUERLICHSPRACHIGER Frage-Test auf denselben 93 assoziativen
Ankern wie gold_assoc.json -- misst, ob enrichs mechanischer "FTS leer"-
Trigger und die Stichwort-Heuristik bei ECHTEM, natuerlichsprachigem Verkehr
ueberhaupt feuern, statt nur bei woertlichen Titel-Fragen.

WARUM (Befund vor diesem Skript)
  retrieval_fair_eval.py / retrieval_fair_eval_enrich.py messen Achse B
  (assoziativ, gold_assoc.json) mit frage == anchor_titel_voll VERBATIM
  (siehe dortiges build_gold_assoc(): "frage": _kappen(atitel) -- nur bei
  Ueberlaenge gekappt, sonst der volle Titel). Eine Frage, die WORTWOERTLICH
  der Artikeltext ist, ist FTS' Heimspiel: alt_fts findet in Achse B den
  Anker selbst zu 98,9% (anker_selbstfund_pct, siehe
  retrieval_fair_eval_ergebnis.json) -- FTS liefert dort also so gut wie NIE
  wirklich leer zurueck. corpus_lookup_enrich()s mechanischer "fts_leer"-
  Trigger (WorldAssembler.corpus_lookup_enrich() in clayverse/retrieval.py)
  wurde in retrieval_fair_eval_enrich_ergebnis.json entsprechend NIE ueber
  diesen Pfad ausgeloest (feuergruende zeigt in der realistischen Mischung
  nur "assoziative_absicht": 17, kein einziges "fts_leer"). Ob der fuer den
  ECHTEN Produktivverkehr wichtigste Trigger (Nutzerfrage, FTS findet
  nichts) ueberhaupt greift, ist damit UNGEPRUEFT. Dieses Skript schliesst
  genau diese Luecke -- additiv, aendert nichts an den drei vorhandenen
  Dateien (retrieval_fair_eval.py, retrieval_fair_eval_enrich.py,
  gold_assoc.json).

WIE DIE NL-FRAGE ENTSTEHT (mechanisch, dokumentiert, NICHTS ERFINDET)
  Die Ground Truth (erwartet/erwartet_meta/anchor_id) ist UNVERAENDERT aus
  gold_assoc.json uebernommen -- die Kante bleibt die Wahrheit. Nur die
  FRAGE wird neu gebaut:
   1. THEMA = Ankertitel, Anfuehrungszeichen/Satzzeichen am Rand entfernt,
      dann wortweise gegen dieselbe (erweiterte) Stopwortliste wie
      corpus_lookup()/_fts_terms() gefiltert (Artikel/Praepositionen/
      Hilfsverben DE+EN), auf max. 12 verbleibende Inhaltswoerter gekappt.
      Das ist eine KUERZUNG durch Subtraktion (Stoppwoerter raus), keine
      Umformulierung -- jedes verbleibende Wort stammt woertlich aus dem
      Titel. "NICHT der ganze Titel" (Auftrag) ist damit erfuellt, ohne
      etwas hinzuzudichten.
   2. KATEGORIE = aus den echten Kantentypen des Ankers (edge_arten in
      gold_assoc.json) abgeleitet, Prioritaet wie SEM_EDGE_ARTS in
      retrieval_fair_eval.py deklariert (widerspricht/attacks > eltern_
      hypothese > stuetzt > related_claim_ids) -- deterministisch, nicht
      von Hand ausgesucht: 29 Anker haben widerspricht+attacks GEMEINSAM
      (attacks kommt im Datensatz nie ohne widerspricht vor, geprueft).
   3. FRAGE = KATEGORIE-Vorlage(THEMA), EINE feste Vorlage je Kategorie,
      keine KI-Umformulierung, kein Zufall:
        gegenposition   (widerspricht/attacks)  -> "Was spricht gegen {THEMA}?"
        elternhypothese (eltern_hypothese)       -> "Worauf baut {THEMA} auf?"
        stuetzung       (stuetzt)                -> "Was stuetzt {THEMA}?"
        zusammenhang    (related_claim_ids)      -> "Womit steht {THEMA} im Zusammenhang?"
      Die ersten drei Vorlagen sind woertlich die im Auftrag vorgeschlagenen
      Formulierungen; "zusammenhang" ist eine vierte, im selben Stil
      ergaenzte Vorlage fuer den einzigen im Datensatz vorkommenden
      Kantentyp, den der Auftrag nicht selbst vorformuliert hat.
      WICHTIG, ehrlich benannt: "Was spricht gegen" und "Worauf baut ... auf"
      TREFFEN KEIN Stichwort aus ASSOZIATIVE_BEGRIFFE (clayverse/retrieval.py)
      woertlich -- "gegen"/"spricht"/"baut"/"auf" stehen dort nicht. Nur
      "stuetzt" und "zusammenhang" (exakt so geschrieben, ASCII-transliteriert
      ohne Umlaut im Woerterset) treffen. Diese Skript-Datei schreibt die
      Vorlagen bewusst NICHT auf die Heuristik-Woerter hin -- Ziel ist zu
      MESSEN, ob die Heuristik natuerliche Formulierungen erkennt, nicht sie
      zu bestehen.
   4. Kein LLM-Paraphrasieren eingesetzt (im Auftrag als optional markiert).
      Begruendung: die Auflage dieses Evals ist REIN LESEND/keine neuen
      Seiteneffekte; ein zusaetzlicher externer LLM-Aufruf waere ein neuer,
      nicht rein lesender Pfad (Netzwerk, Kosten, Fehlerflaeche) fuer einen
      Eval, dessen verlaessliche Basis laut Auftrag ohnehin die Vorlage ist.
      Die vier mechanischen Vorlagen liefern bereits eine echte, von
      Titelwoertern verschiedene Formulierung je Kantentyp.

GRENZEN (ehrlich benannt)
  - EIN Template je Kategorie, keine Formulierungsvielfalt -- ein zweites
    Frage-Sample (z.B. "Warum widerspricht man {THEMA}?") wuerde vermutlich
    andere Heuristik-Trefferquoten liefern; hier bewusst deterministisch
    und reproduzierbar gehalten statt breit gesampelt.
  - THEMA bleibt oft eine Wortkette, kein grammatisch glatter Nominalsatz
    (Titel sind selbst oft vollstaendige Aussagesaetze/Code-Identifier,
    z.B. "gate_latency_us describes..." -> "gate_latency_us describes
    latency effect authority gate") -- mechanisch subtrahiert, nicht
    umformuliert; einzelne Fragen lesen sich holprig, das ist der Preis
    fuer "nichts erfunden".
  - Deckt nur die 93 assoziativen Anker ab (Achse B), nicht Achse A
    (goldsatz.json hat mit "Was ist zu X bekannt?" bereits eine eigene,
    andere NL-Vorlage und bleibt hier unangetastet).

NUR LESEND. Keine Schema-Aenderung, kein systemctl, kein rm. paket()s
dokumentierter Nebeneffekt (vp_paket_log) bleibt wie in den beiden
bestehenden Fair-Eval-Skripten unangetastet Teil des Entwurfs.
"""
from __future__ import annotations

import importlib.util as _ilu
import json
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, "/opt/unifieddb")
sys.path.insert(0, "/opt/entityos/the artefact")

from udb.abruf import paket as P  # noqa: E402  -- _connect (rw), _ro (read-only)
from clayverse.retrieval import ASSOZIATIVE_BEGRIFFE, _ist_assoziative_frage  # noqa: E402 -- Modul-Ebene, keine DB

HIER = Path(__file__).resolve().parent

# additiv 1:1 aus retrieval_fair_eval.py wiederverwendet (unveraendert) --
# gleiche Technik wie retrieval_fair_eval_enrich.py.
_spec = _ilu.spec_from_file_location("retrieval_fair_eval", str(HIER / "retrieval_fair_eval.py"))
_fair = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(_fair)

alt_lookup = _fair.alt_lookup
GOLD_A = _fair.GOLD_A            # goldsatz.json, 120, woertlich/Achse A -- unveraendert
GOLD_B = _fair.GOLD_B            # gold_assoc.json, 93, assoziativ/Achse B -- unveraendert, Ground Truth
MATCH_K = _fair.MATCH_K
PAKET_DEFAULT_BUDGET = _fair.PAKET_DEFAULT_BUDGET
_perc = _fair._perc

# additiv 1:1 aus retrieval_fair_eval_enrich.py wiederverwendet (unveraendert).
_spec2 = _ilu.spec_from_file_location("retrieval_fair_eval_enrich", str(HIER / "retrieval_fair_eval_enrich.py"))
_enrich_mod = _ilu.module_from_spec(_spec2)
_spec2.loader.exec_module(_enrich_mod)
enrich_lookup = _enrich_mod.enrich_lookup

GOLD_NL = str(HIER / "gold_assoc_nl.json")
ERGEBNIS = str(HIER / "retrieval_nl_eval_ergebnis.json")


# ── NL-Frage mechanisch aus dem Anker ableiten (reine Berechnung, kein DB-Zugriff) ──

_STOP_THEMA = frozenset("""
    aber alle als also andere auch auf aus bei bin bis das dass dein den der des
    dem die dies diese doch dort durch ein eine einem einen einer eines etwas fuer
    hat hier ich ihr ist jetzt kann kein mehr mein mit muss nach nicht noch nur
    oder ohne sehr sein sich sind soll ueber und uns unter viel vom von war was
    wenn wer wie wir wird wo zum zur
    the and for are but not you all any can her was one our out has had his how
    its who did yes with this that from they what when will your a an of to is
    be as it may should could would must into onto than then such
""".split())  # DE+EN, identisch im Geist zu WorldAssembler.STOPWORDS -- hier zusaetzlich
              # a/an/of/to/is/be/as/it/may/should/could/would/must/into/onto/than/then/such
              # ergaenzt, weil THEMA aus Volltitelsaetzen (nicht Suchbegriffen) gebaut wird.

_WORT_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9_]+(?:[-'][A-Za-zÄÖÜäöüß0-9_]+)*")
MAX_THEMA_WOERTER = 12

KATEGORIE_PRIORITAET = ("gegenposition", "elternhypothese", "stuetzung", "zusammenhang")

TEMPLATES = {
    "gegenposition": "Was spricht gegen {thema}?",
    "elternhypothese": "Worauf baut {thema} auf?",
    "stuetzung": "Was stuetzt {thema}?",
    "zusammenhang": "Womit steht {thema} im Zusammenhang?",
}


def _thema(titel: str, max_woerter: int = MAX_THEMA_WOERTER) -> str:
    t = (titel or "").strip().strip("\"'“”„»«")
    t = t.rstrip(".!?;: ")
    out = []
    for tok in _WORT_RE.findall(t):
        if tok.lower() in _STOP_THEMA:
            continue
        out.append(tok)
        if len(out) >= max_woerter:
            break
    thema = " ".join(out).strip()
    return thema if thema else _fair._kappen(t, 80)


def _kategorie(edge_arten: set) -> str:
    if "widerspricht" in edge_arten or "attacks" in edge_arten:
        return "gegenposition"
    if "eltern_hypothese" in edge_arten:
        return "elternhypothese"
    if "stuetzt" in edge_arten:
        return "stuetzung"
    if "related_claim_ids" in edge_arten:
        return "zusammenhang"
    return "unbekannt"  # sollte bei SEM_EDGE_ARTS-Grundgesamtheit nie vorkommen


def build_gold_nl() -> list[dict]:
    satz_b = json.load(open(GOLD_B, encoding="utf-8"))
    out = []
    for e in satz_b:
        edge_arten = set()
        for m in e["erwartet_meta"]:
            edge_arten |= set(m["edge_arten"])
        kat = _kategorie(edge_arten)
        thema = _thema(e["anchor_titel_voll"])
        vorlage = TEMPLATES.get(kat, "Was hat mit {thema} zu tun?")
        frage_nl = vorlage.format(thema=thema)
        out.append({
            "anchor_id": e["anchor_id"],
            "anchor_art": e["anchor_art"],
            "anchor_titel_voll": e["anchor_titel_voll"],
            "frage_titel_verbatim": e["frage"],   # == gold_assoc.json Original, fuer den Vergleich
            "kategorie": kat,
            "edge_arten": sorted(edge_arten),
            "thema": thema,
            "vorlage": vorlage,
            "frage_nl": frage_nl,
            "erwartet": e["erwartet"],             # Ground Truth UNVERAENDERT
            "erwartet_meta": e["erwartet_meta"],   # Ground Truth UNVERAENDERT
        })
    return out


# ── Messung: ein generischer Lauf pro Arm, sammelt Rohdaten, aggregiert danach ──

def _lauf(satz: list[dict], frage_key: str, get_ids_fn) -> list[dict]:
    """Fuehrt get_ids_fn(frage) fuer jeden Eintrag aus, EINMAL warmgelaufen
    (verworfen), einmal gemessen. Gibt Rohdaten je Eintrag zurueck, damit
    Gesamt- UND Kategorie-Aufschluesselung aus DEMSELBEN Lauf entstehen
    (kein zweiter paket()-Aufruf fuer die Kategorie-Sicht noetig)."""
    for e in satz:
        get_ids_fn(e[frage_key])  # Warmlauf, verworfen
    roh = []
    for e in satz:
        t0 = time.perf_counter()
        r = get_ids_fn(e[frage_key])
        ms = (time.perf_counter() - t0) * 1000
        roh.append({
            "anchor_id": e["anchor_id"],
            "kategorie": e.get("kategorie"),
            "anchor": e["anchor_id"],
            "truth": set(e["erwartet"]),
            "ids": r["ids"],
            "raw_empty": r.get("raw_empty", len(r["ids"]) == 0),
            "feuerte": r.get("feuerte"),
            "grund": r.get("grund"),
            "latenz_ms": ms,
        })
    return roh


def _aggregiere(roh: list[dict]) -> dict:
    n = len(roh)
    if n == 0:
        return {"n": 0}
    recall_fracs, any_hit, full_hit = [], 0, 0
    praez_werte, deckung, anker_selbstfund = [], 0, 0
    raw_empty_n, feuer_n = 0, 0
    gruende: dict = defaultdict(int)
    zeiten = []
    for r in roh:
        zeiten.append(r["latenz_ms"])
        if r["raw_empty"]:
            raw_empty_n += 1
        if r["feuerte"]:
            feuer_n += 1
            gruende[r["grund"]] += 1
        anchor = r["anchor"]
        truth = r["truth"]
        ids = r["ids"]
        if anchor in ids:
            anker_selbstfund += 1
        got = set(ids) - {anchor}
        hit = truth & got
        recall_fracs.append(len(hit) / len(truth) if truth else 0.0)
        if hit:
            any_hit += 1
        if truth and hit == truth:
            full_hit += 1
        if got:
            deckung += 1
            praez_werte.append(len(hit) / len(got))
    zsort = sorted(zeiten)
    out = {
        "n": n,
        "recall_macro_pct": round(100 * statistics.mean(recall_fracs), 1),
        "any_hit_rate_pct": round(100 * any_hit / n, 1),
        "full_hit_rate_pct": round(100 * full_hit / n, 1),
        "praezision_macro": round(statistics.mean(praez_werte), 4) if praez_werte else None,
        "deckung_nichtleer_pct": round(100 * deckung / n, 1),
        "anker_selbstfund_pct": round(100 * anker_selbstfund / n, 1),
        "kein_treffer_n": raw_empty_n,
        "kein_treffer_pct": round(100 * raw_empty_n / n, 1),
        "latenz_median_ms": round(statistics.median(zeiten), 2),
        "latenz_p95_ms": round(_perc(zsort, 0.95), 2),
        "latenz_mean_ms": round(statistics.mean(zeiten), 2),
    }
    if any(r["feuerte"] is not None for r in roh):
        out["feuerrate_pct"] = round(100 * feuer_n / n, 1)
        out["feuergruende"] = dict(gruende)
        out["feuergrund_mechanisch_fts_leer_n"] = gruende.get("fts_leer", 0)
        out["feuergrund_heuristik_assoziativ_n"] = gruende.get("assoziative_absicht", 0)
    return out


def _kategorie_aufschluesselung(roh: list[dict]) -> dict:
    nach_kat: dict = defaultdict(list)
    for r in roh:
        nach_kat[r["kategorie"] or "unbekannt"].append(r)
    return {kat: _aggregiere(rs) for kat, rs in sorted(nach_kat.items())}


def run_eval() -> dict:
    satz_nl = build_gold_nl()
    json.dump(satz_nl, open(GOLD_NL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)

    c_rw = P._connect()
    P._ensure_vp_tables(c_rw)
    c_ro = P._ro()

    def get_alt(k_alt=MATCH_K):
        def f(query):
            rows = alt_lookup(c_ro, query, max_hits=k_alt)
            ids = [row["artikel_id"] for row in rows]
            return {"ids": ids, "raw_empty": len(rows) == 0}
        return f

    def get_paket(budget):
        def f(query):
            pk = P.paket(query, budget=budget, conn=c_rw)
            ids = [t.get("id") for t in pk.get("treffer", []) if isinstance(t, dict)]
            return {"ids": ids, "raw_empty": len(ids) == 0}
        return f

    def get_enrich(budget, k_alt=MATCH_K):
        def f(query):
            ids, feuerte, grund = enrich_lookup(c_rw, c_ro, query, budget, k_alt)
            return {"ids": ids, "raw_empty": len(ids) == 0, "feuerte": feuerte, "grund": grund}
        return f

    # ── 1) FTS-Leer-Vergleich: Titel-verbatim vs. NL, SELBER Code-Pfad ──
    roh_alt_titel = _lauf(satz_nl, "frage_titel_verbatim", get_alt())
    roh_alt_nl = _lauf(satz_nl, "frage_nl", get_alt())

    # ── 2) Drei Arme auf der NL-Frage ──
    roh_paket_nl_b8 = _lauf(satz_nl, "frage_nl", get_paket(PAKET_DEFAULT_BUDGET))
    roh_enrich_nl_b5 = _lauf(satz_nl, "frage_nl", get_enrich(MATCH_K))
    roh_enrich_nl_b8 = _lauf(satz_nl, "frage_nl", get_enrich(PAKET_DEFAULT_BUDGET))
    # Referenz: derselbe enrich-Pfad auf der ALTEN Titel-verbatim-Frage, damit
    # die Feuerrate/-gruende direkt (gleicher Code, gleiche 93 Anker) verglichen
    # werden koennen, nicht nur gegen die alte JSON-Datei rueckgerechnet.
    roh_enrich_titel_b5 = _lauf(satz_nl, "frage_titel_verbatim", get_enrich(MATCH_K))

    # ── 3) Realistische Mischung: 120 woertliche (Achse A) + 93 NL (Achse B) ──
    satz_a = json.load(open(GOLD_A, encoding="utf-8"))
    mix = [{"frage_mix": e["frage"], "kategorie": "achse_a_woertlich",
            "anchor_id": e["erwartet"], "erwartet": [e["erwartet"]]} for e in satz_a] + \
          [{"frage_mix": e["frage_nl"], "kategorie": e["kategorie"],
            "anchor_id": e["anchor_id"], "erwartet": e["erwartet"]} for e in satz_nl]
    roh_mix_enrich = _lauf(mix, "frage_mix", get_enrich(MATCH_K))
    # Achse A hat eine andere Ground-Truth-Form (ein einzelnes id statt Menge) --
    # wie im Original-Enrich-Skript dokumentiert wird fuer die Mischung deshalb
    # NUR Feuerrate/Latenz ausgewiesen, keine erfundene gemeinsame Recall-Zahl.
    def _feuer_latenz_only(roh):
        agg = _aggregiere(roh)
        return {k: v for k, v in agg.items()
                if k in ("n", "feuerrate_pct", "feuergruende",
                         "feuergrund_mechanisch_fts_leer_n", "feuergrund_heuristik_assoziativ_n",
                         "latenz_median_ms", "latenz_p95_ms", "latenz_mean_ms")}

    c_rw.close()
    c_ro.close()

    ergebnis = {
        "stand": "2026-08-19",
        "n_anker": len(satz_nl),
        "kategorie_verteilung": {k: sum(1 for e in satz_nl if e["kategorie"] == k)
                                  for k in KATEGORIE_PRIORITAET},
        "vorlagen": TEMPLATES,
        "fts_leer_vergleich_titel_vs_nl": {
            "beschreibung": ("Wie oft liefert alt_fts() ECHT 0 Treffer zurueck (kein_treffer_pct) -- "
                              "SELBE 93 Anker, SELBER alt_lookup()-Code, nur die Frage wechselt."),
            "titel_verbatim": {k: v for k, v in _aggregiere(roh_alt_titel).items()
                                if k in ("n", "kein_treffer_n", "kein_treffer_pct",
                                          "deckung_nichtleer_pct", "anker_selbstfund_pct")},
            "nl_frage": {k: v for k, v in _aggregiere(roh_alt_nl).items()
                         if k in ("n", "kein_treffer_n", "kein_treffer_pct",
                                   "deckung_nichtleer_pct", "anker_selbstfund_pct")},
        },
        "drei_arme_nl": {
            "alt_fts": _aggregiere(roh_alt_nl),
            "paket_budget8": _aggregiere(roh_paket_nl_b8),
            "enrich_budget5": _aggregiere(roh_enrich_nl_b5),
            "enrich_budget8": _aggregiere(roh_enrich_nl_b8),
        },
        "enrich_feuerrate_titel_vs_nl": {
            "beschreibung": "enrich_lookup(), SELBE 93 Anker, Budget=5 -- Feuerrate + Grund, Titel vs. NL.",
            "titel_verbatim": {k: v for k, v in _aggregiere(roh_enrich_titel_b5).items()
                                if k.startswith("feuer") or k == "n"},
            "nl_frage": {k: v for k, v in _aggregiere(roh_enrich_nl_b5).items()
                         if k.startswith("feuer") or k == "n"},
        },
        "kategorie_aufschluesselung_nl_enrich_budget5": _kategorie_aufschluesselung(roh_enrich_nl_b5),
        "realistische_mischung_a_woertlich_plus_b_nl": {
            "beschreibung": (f"{len(satz_a)} woertliche (Achse A, unveraendert) + {len(satz_nl)} NL-Fragen "
                              f"(Achse B neu) = {len(mix)} gesamt, durch denselben enrich-Pfad, Budget=5. "
                              "Vergleichswert zur alten Mischung in retrieval_fair_eval_enrich_ergebnis.json "
                              "(213 Fragen, dort ABER Achse B == Titel-verbatim: feuerrate 8,0%, "
                              "feuergruende nur assoziative_absicht:17, KEIN fts_leer)."),
            **_feuer_latenz_only(roh_mix_enrich),
        },
    }
    return ergebnis


if __name__ == "__main__":
    modus = sys.argv[1] if len(sys.argv) > 1 else "eval"
    if modus == "build":
        satz = build_gold_nl()
        print(f"{len(satz)} NL-Fragen -> {GOLD_NL}")
        json.dump(satz, open(GOLD_NL, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        for e in satz[:8]:
            print(f"[{e['kategorie']:14s}] {e['frage_nl']}")
    else:
        erg = run_eval()
        print(json.dumps(erg, ensure_ascii=False, indent=2))
        json.dump(erg, open(ERGEBNIS, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print(f"\n-> {ERGEBNIS}\n-> {GOLD_NL}")
