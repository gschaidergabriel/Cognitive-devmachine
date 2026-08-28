#!/usr/bin/env python3
"""governor.py -- der COGNITIVE GOVERNOR (F67, ENTSCHEIDUNGEN-2026-08-15.md).

Kein Antwort-Generator. Sein erstes Erzeugnis ist ein TEMPORAeRES
AUSFUEHRUNGSGENOM fuer genau EINEN Request:

    IN   Nutzerabsicht + ClayMachine-Realitaet (moeglichkeitsraum() ->
         paket() -> was der Bestand JETZT weiss/nicht weiss)
    OUT  dichtes ClayCode-Paket: Hypothesen + Gegenhypothesen mit Gewicht,
         Codependenzen, gewaehlte Organe, Ausfuehrungsreihenfolge,
         Erfolgskriterium -- 300-1500 Token, PARSEABLE (json_schema strict),
         niemals Prosa.

⭐⭐ EIGNER-ENTSCHEIDUNG 15.08.: testweise mit MISTRAL bauen (frei, bereits in
freie-zugaenge.env), Cerebras GPT-OSS-120B kommt SPAETER. Deshalb ist das
Modell hier ein KONFIGWERT (ENGINES-Dict + GOVERNOR_ENGINE), kein Bestandteil
des Codes -- Tausch Mistral->Cerebras = EINE Zeile, kein Umbau (F21/F52: das
Modell ist ein austauschbares Rechenorgan, die Identitaet liegt in der
persistenten Schicht -- hier: in moeglichkeitsraum()/paket()/wiki.db).

⚠️ INVARIANTE (F67, hart): der Governor schreibt NICHTS in die kanonische
UnifiedDB. Sein Erzeugnis geht als CANDIDATE DELTA + PROVENANCE + EVIDENZ in
eine eigene Warteschlange (bau/governor-kandidaten.jsonl) -- niemals direkt in
artikel/kante/folgerung. Ein Governor, der ungeprueft in den Bestand
schreibt, ist F43 mit Motor (siehe kandidat_schreiben()).

Baut auf Bestehendem, aendert nichts daran:
  * udb.abruf.moeglichkeitsraum.moeglichkeitsraum() -- die "ClayMachine
    reality" aus F67s IN-Zeile (importiert, nicht kopiert).
  * werkzeug/bahn.py::umgebung()/darf()/buchen() -- Schluesselverwaltung und
    Kontingentbuch wiederverwendet, bahn.py selbst NICHT angefasst (eigene
    rufen()-Variante hier, weil bahn.rufen() kein response_format kennt).

Live gemessen 15.08.: mistral-small-latest, response_format=json_schema mit
strict=True/additionalProperties=False liefert HTTP 200 und syntaktisch
gueltiges JSON nach Schema (Testaufruf, siehe Baueintrag). Usage-Zahlen sind
die vom Provider GEMESSENEN Token, nicht geschaetzt.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, "/opt/unifieddb")
sys.path.insert(0, "/opt/clayverse/werkzeug")

from udb.abruf.moeglichkeitsraum import moeglichkeitsraum  # noqa: E402
import bahn  # noqa: E402 -- nur umgebung()/darf()/buchen() wiederverwendet, nichts geaendert

REPO = Path("/opt/clayverse")
KANDIDATEN = REPO / "bau" / "governor-kandidaten.jsonl"

# ── ENGINES: DAS ist die eine Stelle, die den Motor bestimmt. ──────────────
# Ein Feld aendern (oder GOVERNOR_ENGINE exportieren) = Motorwechsel. Sonst
# nichts im Code. Preise sind [B] (Herstellerangaben/Aggregatoren, hier NICHT
# selbst durchgemessen) -- wo unbekannt, steht None, nicht geraten.
ENGINES = {
    "mistral": {
        "env": "MISTRAL_API_KEY",
        "url": "https://api.mistral.ai/v1/chat/completions",
        "modell": "mistral-small-latest",
        "art": "openai_json_schema",
        "reasoning_effort": None,          # Mistral small: kein eigener Reasoning-Kanal
        "unterstuetzt_schema": True,        # [M 15.08.] live gemessen, HTTP 200
        "zugang_kontingentbuch": "mistral",  # Name in bahn.BAHNEN / kontingent.py
        "preis_ein_je_mio": 0.10,           # [B] https://www.aipricing.guru/mistral-pricing/ (Aggregator, nicht Mistral selbst)
        "preis_aus_je_mio": 0.30,           # [B] dito
        "kostenlos_hier": True,             # laeuft ueber die freie Bahn, $0 fuer uns heute
    },
    "cerebras": {
        "env": "CEREBRAS_API_KEY",          # ⚠️ NICHT in freie-zugaenge.env -- noch NICHT verdrahtet
        "url": "https://api.cerebras.ai/v1/chat/completions",
        "modell": "gpt-oss-120b",
        "art": "openai_json_schema",
        "reasoning_effort": "high",         # F67: reasoning=high, sucht INTERN breit
        "unterstuetzt_schema": True,        # [B] laut F67-Quelle, hier NICHT selbst geprueft
        "zugang_kontingentbuch": "cerebras",
        "preis_ein_je_mio": 0.35,           # [B] F67 (ENTSCHEIDUNGEN-2026-08-15.md)
        "preis_aus_je_mio": 0.75,           # [B] dito
        "kostenlos_hier": False,
        "hinweis": "Platzhalter. Kein Schluessel hinterlegt, kein Live-Aufruf moeglich, "
                    "bis der Owner ihn eintraegt -- dann NUR GOVERNOR_ENGINE=cerebras setzen.",
    },
}
GOVERNOR_ENGINE = os.environ.get("GOVERNOR_ENGINE", "mistral")

CAP_MIN, CAP_MAX = 300, 1500   # F67: harte Deckelung, hier GEMESSEN, nicht erzwungen-getrimmt
MAX_TOKENS_ANFRAGE = 3000       # grosszuegiger als der Deckel -- wir wollen MESSEN ob das
                                 # Modell sich selbst deckelt (F67 Frage 3), nicht per Wand kappen

SCHEMA = {
    "type": "object",
    "properties": {
        "hypothesen": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "gewicht": {"type": "number"}},
            "required": ["text", "gewicht"], "additionalProperties": False}},
        "gegenhypothesen": {"type": "array", "items": {
            "type": "object",
            "properties": {"text": {"type": "string"}, "gewicht": {"type": "number"}},
            "required": ["text", "gewicht"], "additionalProperties": False}},
        "codependenzen": {"type": "array", "items": {"type": "string"}},
        "organe": {"type": "array", "items": {"type": "string"}},
        "ausfuehrungsreihenfolge": {"type": "array", "items": {"type": "string"}},
        "erfolgskriterium": {"type": "string"},
        "konfidenz": {"type": "number"},
    },
    "required": ["hypothesen", "gegenhypothesen", "codependenzen", "organe",
                 "ausfuehrungsreihenfolge", "erfolgskriterium", "konfidenz"],
    "additionalProperties": False,
}

# Caveman im System-Teil -- Auftrag + repo-eigene Messung (bahn.py: -28,9%).
SYSTEM = (
    "you are compiler. not chat. you get: user want + what stock already know "
    "(hypothesis side + counter side, may be empty). you think wide inside head "
    "first. then you STOP thinking when space small enough. you output ONLY "
    "packet, no words outside json. packet must have: hypothesis list (text+"
    "weight 0-1), counter-hypothesis list (text+weight 0-1) -- counter side "
    "NEVER empty if you can make even weak one, this the whole point. "
    "codependency list (short strings, what depend on what). organ list (which "
    "tool-entity should run: GitClay WebClay CodeClay DatabaseClay VisionClay "
    "ResearchClay -- pick only what fit, can be empty). execution order (short "
    "strings, sequence). success criterion (one short string, how you know it "
    "worked). confidence 0-1. TOTAL OUTPUT TARGET 300-1500 token -- dense, not "
    "long. never invent number/fact that not in given stock material or plain "
    "logic from the request itself."
)


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def _prompt_material(raum: dict) -> str:
    """Was aus moeglichkeitsraum() (F67 IN) an den Governor geht -- woertlich,
    keine eigene Paraphrase vor dem Modellaufruf (dieselbe Regel wie in
    moeglichkeitsraum.py selbst: Verdichtung ist deterministisch)."""
    if not raum.get("raum"):
        return "stock material: NONE (%s). reason from request text alone." % (
            raum.get("befund") or "kein Befund")
    r = raum["raum"]
    teile = ["stock hypothesis side (existing, may be thin):"]
    teile += ["  - " + t for t in r.get("plausibel_richtung", [])] or ["  (none)"]
    teile.append("stock counter side (existing, may be thin):")
    teile += ["  - " + t for t in r.get("spricht_dagegen", [])] or ["  (none)"]
    if raum.get("einseitig"):
        teile.append("NOTE: stock is ONE-SIDED (%s) -- exactly what governor must fix." %
                     r.get("warnung", ""))
    return "\n".join(teile)


def _rufen(engine: dict, schluessel: str, user: str) -> dict:
    """Eigener Aufruf (nicht bahn.rufen()): braucht response_format, das
    bahn.py nicht kennt. Sonst dieselbe Form (urllib, Provider-Usage als
    einzige Tokenwahrheit)."""
    body = {
        "model": engine["modell"],
        "messages": [{"role": "system", "content": SYSTEM},
                     {"role": "user", "content": user}],
        "max_tokens": MAX_TOKENS_ANFRAGE,
        "temperature": 0.2,
        "response_format": {"type": "json_schema",
                             "json_schema": {"name": "governor_paket", "schema": SCHEMA,
                                             "strict": True}},
    }
    if engine.get("reasoning_effort"):
        body["reasoning_effort"] = engine["reasoning_effort"]
    req = urllib.request.Request(
        engine["url"], data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {schluessel}",
                 "Content-Type": "application/json",
                 "User-Agent": "clayverse-governor/1.0"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            roh = json.loads(r.read().decode())
            ms = (time.perf_counter() - t0) * 1000
            u = roh.get("usage") or {}
            return {"ok": True, "http": r.status, "ms": ms,
                    "text": roh["choices"][0]["message"]["content"],
                    "ein": u.get("prompt_tokens"), "aus": u.get("completion_tokens")}
    except urllib.error.HTTPError as e:
        return {"ok": False, "http": e.code, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": e.read()[:300].decode("utf-8", "replace")}
    except Exception as e:
        return {"ok": False, "http": 0, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": str(e)[:300]}


def kandidat_schreiben(eintrag: dict) -> None:
    """Schreibt NIE in wiki.db/UnifiedDB. Nur diese eigene Warteschlange --
    ClayMachine (nicht der Governor) entscheidet spaeter, ob/was davon in den
    kanonischen Bestand geht (F67-Invariante)."""
    KANDIDATEN.parent.mkdir(parents=True, exist_ok=True)
    with KANDIDATEN.open("a", encoding="utf-8") as f:
        f.write(json.dumps(eintrag, ensure_ascii=False) + "\n")


def governor(anfrage: str, *, budget: int = 8, wirt=None, engine_name: str = None,
             konto: str = "clayverse", schreiben: bool = True) -> dict:
    """DIE Schnittstelle. Nutzerabsicht rein, Ausfuehrungsgenom raus -- oder
    ein expliziter Fehlbefund (STOP, kein Kaschieren, Auftrag F67)."""
    engine_name = engine_name or GOVERNOR_ENGINE
    if engine_name not in ENGINES:
        return {"ok": False, "fehler": f"unbekannte engine {engine_name!r}, "
                 f"bekannt: {list(ENGINES)}"}
    engine = ENGINES[engine_name]

    u = bahn.umgebung()
    schluessel = u.get(engine["env"])
    if not schluessel:
        return {"ok": False, "fehler": f"kein Schluessel fuer {engine['env']} "
                 f"in /etc/clayverse/freie-zugaenge.env -- {engine.get('hinweis', '')}"}

    erlaubt, grund = bahn.darf(konto, engine["zugang_kontingentbuch"], 1)
    if erlaubt <= 0:
        return {"ok": False, "fehler": f"Kontingentbuch verweigert: {grund}"}

    t_gesamt0 = time.perf_counter()
    raum = moeglichkeitsraum(anfrage, budget=budget, wirt=wirt)
    material = _prompt_material(raum)
    user = "user request:\n%s\n\n%s" % (anfrage.strip(), material)

    res = _rufen(engine, schluessel, user)
    bahn.buchen(konto, engine["zugang_kontingentbuch"], 1, "governor")
    latenz_gesamt_ms = (time.perf_counter() - t_gesamt0) * 1000

    lauf_id = str(uuid.uuid4())
    basis = {
        "ok": None, "lauf_id": lauf_id, "engine": engine_name, "modell": engine["modell"],
        "zeit": jetzt(), "anfrage": anfrage,
        "moeglichkeitsraum_paket_id": raum.get("paket_id"),
        "moeglichkeitsraum_einseitig": raum.get("einseitig"),
        "http": res.get("http"), "latenz_governor_ms": round(res["ms"], 1),
        "latenz_gesamt_ms": round(latenz_gesamt_ms, 1),
        "token_ein": res.get("ein"), "token_aus": res.get("aus"),
    }

    if not res["ok"]:
        basis["ok"] = False
        basis["fehler"] = res.get("fehler", "")
        return basis

    try:
        paket_json = json.loads(res["text"])
    except json.JSONDecodeError as e:
        # ⚠️ Auftrag: NICHT kaschieren. Kein Nachreparieren, kein Best-Effort-
        # Parsing -- wenn das Modell trotz strict-schema kein valides JSON
        # liefert, ist das ein STOP-Befund, kein Detail.
        basis["ok"] = False
        basis["fehler"] = f"NICHT PARSEABLE trotz response_format=json_schema strict: {e}"
        basis["rohtext"] = res["text"][:500]
        return basis

    fehlend = [k for k in SCHEMA["required"] if k not in paket_json]
    if fehlend:
        basis["ok"] = False
        basis["fehler"] = f"Schema-Felder fehlen: {fehlend}"
        basis["paket"] = paket_json
        return basis

    token_aus = res.get("aus") or 0
    cap_eingehalten = CAP_MIN <= token_aus <= CAP_MAX

    basis.update({
        "ok": True,
        "paket": paket_json,
        "n_hypothesen": len(paket_json.get("hypothesen") or []),
        "n_gegenhypothesen": len(paket_json.get("gegenhypothesen") or []),
        "zweiseitig": bool((paket_json.get("hypothesen") or []) and
                            (paket_json.get("gegenhypothesen") or [])),
        "cap_min": CAP_MIN, "cap_max": CAP_MAX, "cap_eingehalten": cap_eingehalten,
        "kosten_usd": (None if engine.get("kostenlos_hier") else
                       round((res.get("ein") or 0) * engine["preis_ein_je_mio"] / 1e6 +
                             token_aus * engine["preis_aus_je_mio"] / 1e6, 6)),
        "kosten_hinweis": ("laeuft ueber freie Bahn, $0 fuer uns heute -- "
                            "preis_ein_je_mio/preis_aus_je_mio [B] nur fuer spaeteren "
                            "Vergleich mit einem bezahlten Organ (z.B. Cerebras)"
                            if engine.get("kostenlos_hier") else ""),
    })

    if schreiben:
        kandidat_schreiben({
            "kind": "governor_candidate", "lauf_id": lauf_id, "zeit": basis["zeit"],
            "provenance": {"quelle": "governor", "engine": engine_name,
                            "modell": engine["modell"],
                            "moeglichkeitsraum_paket_id": raum.get("paket_id")},
            "evidenz": {"anfrage": anfrage, "moeglichkeitsraum_einseitig": raum.get("einseitig")},
            "hypothesen": paket_json.get("hypothesen"),
            "gegenhypothesen": paket_json.get("gegenhypothesen"),
            "codependenzen": paket_json.get("codependenzen"),
            "organe": paket_json.get("organe"),
            "ausfuehrungsreihenfolge": paket_json.get("ausfuehrungsreihenfolge"),
            "erfolgskriterium": paket_json.get("erfolgskriterium"),
            "konfidenz": paket_json.get("konfidenz"),
            "status": "KANDIDAT -- nicht in UnifiedDB, wartet auf ClayMachine-Pruefung",
        })
        basis["kandidat_geschrieben"] = str(KANDIDATEN)

    return basis


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("anfrage")
    ap.add_argument("--budget", type=int, default=8)
    ap.add_argument("--wirt", default=None)
    ap.add_argument("--engine", default=None, help="ueberschreibt GOVERNOR_ENGINE")
    ap.add_argument("--konto", default="clayverse")
    ap.add_argument("--trocken", action="store_true", help="keinen Kandidaten schreiben")
    a = ap.parse_args()
    r = governor(a.anfrage, budget=a.budget, wirt=a.wirt, engine_name=a.engine,
                 konto=a.konto, schreiben=not a.trocken)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("ok") else 1


if __name__ == "__main__":
    sys.exit(main())
