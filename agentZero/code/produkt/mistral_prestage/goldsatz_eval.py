"""Uebersetzer-Eval gegen den ECHTEN Produktions-Goldsatz.

Ziel #4 (Eigner): "Uebersetzer Caveman -> Deutsch, 95 %", gemessen an TREUE
und LESBARKEIT durch einen unabhaengigen Richter, PLUS (Zusatz 2026-08-19)
MENSCHLICHKEIT -- klingt es nach einem Menschen, nicht nach einer Maschine.

Zwei unabhaengige Messungen kombiniert, beide auf denselben 26 echten
Produktionszuegen aus uebersetzer_gold.json (mv_translation_log, turn_id
gesetzt -- keine handgeschriebenen Beispiele):

  1. MECHANISCH (uebersetzer_messen.py, read-only importiert -- diese Datei
     wird NICHT verändert, sie gehoert einem anderen Agenten): zaehlt Zahlen,
     Pfade, Dateien, Bezeichner. Kein Modell bewertet ein Modell, also keine
     geteilten blinden Flecken. Miss NUR Treue (Fakten gehalten/verloren/
     erfunden), keine Lesbarkeit/Waerme -- das kann eine Regex nicht.

  2. RICHTER (judge.py, Gemini -- andere Anbieterfamilie als der Uebersetzer
     Mistral): bewertet faithfulness/readability/menschlichkeit auf derselben
     live uebersetzten Antwort. Das ist die einzige Quelle fuer Lesbarkeit
     und Menschlichkeit -- die mechanische Pruefung kann das nicht.

Die live-uebersetzte deutsche Antwort ist in beiden Messungen IDENTISCH (ein
Uebersetzungsaufruf pro Probe, beide Messgeraete laufen darueber), damit die
zwei Zahlen wirklich zur selben Uebersetzung gehoeren und nicht zu zwei
verschiedenen Zufallsziehungen.

Aufruf NUR im Container (Schluessel sind dort erreichbar):
    docker exec entityos python3 /workspace/goldsatz_eval.py [--grenze N]
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, "/opt/clayverse")
from clayverse.mistral_prestage import judge as judge_mod  # noqa: E402
from clayverse.mistral_prestage import translator as translator_mod  # noqa: E402

GOLD_PATH = Path("/opt/unifieddb/udb/abruf/uebersetzer_gold.json")
MESSEN_PATH = Path("/opt/unifieddb/udb/abruf/uebersetzer_messen.py")

# Gleiche Bar wie eval_harness.py (READABILITY_MIN/MENSCHLICHKEIT_MIN=70,
# FAITHFULNESS_MIN=90) -- ein Uebersetzer hat nicht zwei verschiedene
# Massstaebe, nur weil das eine der handgeschriebene und das andere der
# echte Satz ist.
FAITHFULNESS_MIN = 90
READABILITY_MIN = 70
MENSCHLICHKEIT_MIN = 70
ZIEL = 0.95

RETRY_ATTEMPTS = 5
RETRY_BASE_SECONDS = 5.0


def _mit_wiederholung(fn, *args, **kwargs):
    letzter = None
    for versuch in range(RETRY_ATTEMPTS):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 -- Transportschicht, keine Bewertungslogik
            letzter = exc
            if versuch < RETRY_ATTEMPTS - 1:
                time.sleep(RETRY_BASE_SECONDS * (2**versuch))
    raise letzter


def _lade_messen():
    spec = importlib.util.spec_from_file_location("uebersetzer_messen", MESSEN_PATH)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def laufen(*, grenze: int | None = None, prompt_version: str | None = None) -> dict:
    um = _lade_messen()
    daten = um.lade_gold(GOLD_PATH)
    proben = daten["proben"][:grenze] if grenze else daten["proben"]
    prompt_version = prompt_version or translator_mod.PROMPT_VERSION

    ergebnisse = []
    for p in proben:
        caveman = p["caveman"]
        ausfall = None
        try:
            out = _mit_wiederholung(translator_mod.translate_to_german, caveman)
            deutsch = out["german_translation"]
        except Exception as exc:  # noqa: BLE001
            ausfall = f"{type(exc).__name__}: {exc}"[:200]
            deutsch = ""

        mech = um.bewerte(caveman, deutsch) if not ausfall else {
            "treue": 0.0, "bestanden": False, "verloren": [], "erfunden": [],
            "fakten_gesamt": 0, "gehalten": 0,
        }
        if ausfall:
            mech["bestanden"] = False

        if deutsch:
            verdict = _mit_wiederholung(judge_mod.judge_translation, caveman, deutsch)
        else:
            verdict = {"faithfulness": 0, "readability": 0, "menschlichkeit": 0,
                       "fabrication": True, "reason": f"Uebersetzung ausgefallen: {ausfall}"}

        fabrication = bool(verdict.get("fabrication"))
        faithfulness = 0 if fabrication else int(verdict.get("faithfulness", 0))
        readability = int(verdict.get("readability", 0))
        menschlichkeit = int(verdict.get("menschlichkeit", 0))

        richter_bestanden = (
            not fabrication
            and faithfulness >= FAITHFULNESS_MIN
            and readability >= READABILITY_MIN
        )
        menschlich_bestanden = menschlichkeit >= MENSCHLICHKEIT_MIN
        gesamt_bestanden = bool(mech["bestanden"]) and richter_bestanden and menschlich_bestanden

        ergebnisse.append({
            "id": p["id"],
            "ausfall": ausfall,
            "deutsch": deutsch,
            "mech_treue": mech["treue"],
            "mech_bestanden": bool(mech["bestanden"]),
            "mech_verloren": mech.get("verloren", []),
            "mech_erfunden": mech.get("erfunden", []),
            "richter_faithfulness": faithfulness,
            "richter_readability": readability,
            "richter_menschlichkeit": menschlichkeit,
            "richter_fabrication": fabrication,
            "richter_reason": verdict.get("reason", ""),
            "richter_bestanden": richter_bestanden,
            "menschlich_bestanden": menschlich_bestanden,
            "bestanden": gesamt_bestanden,
        })

    n = len(ergebnisse)
    zusammenfassung = {
        "prompt_version": prompt_version,
        "proben": n,
        "bestanden": sum(r["bestanden"] for r in ergebnisse),
        "bestehensquote": round(sum(r["bestanden"] for r in ergebnisse) / n, 4) if n else 0.0,
        "mech_faktentreue": round(
            sum(r["mech_treue"] for r in ergebnisse) / n, 4) if n else 0.0,
        "mech_bestehensquote": round(
            sum(r["mech_bestanden"] for r in ergebnisse) / n, 4) if n else 0.0,
        "avg_richter_faithfulness": round(
            statistics.mean(r["richter_faithfulness"] for r in ergebnisse), 2) if n else 0.0,
        "avg_richter_readability": round(
            statistics.mean(r["richter_readability"] for r in ergebnisse), 2) if n else 0.0,
        "avg_richter_menschlichkeit": round(
            statistics.mean(r["richter_menschlichkeit"] for r in ergebnisse), 2) if n else 0.0,
        "richter_bestehensquote": round(
            sum(r["richter_bestanden"] for r in ergebnisse) / n, 4) if n else 0.0,
        "menschlich_bestehensquote": round(
            sum(r["menschlich_bestanden"] for r in ergebnisse) / n, 4) if n else 0.0,
        "ausfaelle": sum(1 for r in ergebnisse if r["ausfall"]),
        "ziel": ZIEL,
        "ergebnisse": ergebnisse,
    }
    return zusammenfassung


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Uebersetzer gegen den echten Produktions-Goldsatz messen")
    ap.add_argument("--grenze", type=int, default=None)
    ap.add_argument("--fehler-zeigen", action="store_true")
    a = ap.parse_args()
    z = laufen(grenze=a.grenze)
    kurz = {k: v for k, v in z.items() if k != "ergebnisse"}
    print(json.dumps(kurz, indent=2, ensure_ascii=False))
    if a.fehler_zeigen:
        for r in z["ergebnisse"]:
            if r["bestanden"]:
                continue
            print("---", r["id"])
            print("  mech_treue:", r["mech_treue"], "verloren:", r["mech_verloren"][:8], "erfunden:", r["mech_erfunden"][:8])
            print("  richter: faithfulness=", r["richter_faithfulness"], "readability=", r["richter_readability"],
                  "menschlichkeit=", r["richter_menschlichkeit"], "fabrication=", r["richter_fabrication"])
            print("  reason:", r["richter_reason"])
