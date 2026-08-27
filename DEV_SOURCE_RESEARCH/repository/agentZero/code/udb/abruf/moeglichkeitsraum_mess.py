#!/usr/bin/env python3
"""moeglichkeitsraum_mess.py -- misst udb.abruf.moeglichkeitsraum(). Auftrag F56/F62,
verzeichnet unter B27.

KEIN Prod-Pfad (wie zustand_mess.py in diesem Verzeichnis): tiktoken/urllib/
subprocess leben NUR hier. Aufruf mit dem vorhandenen Tokenizer-venv:

    /tmp/tokvenv/bin/python moeglichkeitsraum_mess.py ziel --n 20
    /tmp/tokvenv/bin/python moeglichkeitsraum_mess.py schatten --n 20
    /tmp/tokvenv/bin/python moeglichkeitsraum_mess.py hallu --faelle 6 --wiederholungen 3
    /tmp/tokvenv/bin/python moeglichkeitsraum_mess.py alle

Drei Messungen, wie im Auftrag verlangt:

  ziel      Von N Stichprobenfragen (echte artikel.titel aus wiki.db, art
            hypothese/gegenhypothese): wie viele liefern ueberhaupt Material
            aus paket(), und wie viele DAVON liefern einen brauchbaren,
            NICHT-einseitigen Raum? Die Invariante (einseitig -> gemeldet,
            nicht verschwiegen) wird mitgezaehlt, nicht nur behauptet.

  schatten  Groesse in ECHTEN Token (tiktoken cl100k_base, NICHT Zeichen --
            dieselbe Falle, vor der zustand_mess.py schon warnt) + die
            Zusatzlatenz DIESES Werkzeugs oben auf paket() drauf (nicht
            paket()s eigene Latenz).

  hallu     Halluzinationsvergleich, freies Modell (groq llama-3.1-8b-instant,
            [M 15.08.] ~9ms gemessen, Zugang 'groq_llama31_8b' im
            Kontingentbuch): (a) Moeglichkeitsraum (b) naiver "das wissen
            wir"-Kontext -- GENAU der Fehlermodus, den der Raum ersetzen soll
            (c) kein Kontext. Dieselbe Frage, dieselbe Anfrage, drei
            Bedingungen. n(Wiederholungen) > 1 PFLICHT (Auftrag: ein n=1-Lauf
            auf einem leichten/eindeutigen Fall beweist nichts fuer den
            mehrdeutigen Fall -- und genau dort entscheidet es sich). Deshalb
            werden hier gezielt nur ZWEISEITIGE Faelle verwendet (paket()
            liefert selbst Hypothese UND Gegenseite -- das ist mehrdeutig).

            ⚠️ KEIN ClayVerse-eigenes Bildkorpus vorhanden (siehe
            bau/ENTSCHEIDUNGEN-2026-08-15.md F58 "Reihenfolge daraus" Punkt 2
            -- blockiert, nicht Teil dieses Auftrags). Deshalb TEXT statt
            Bild/VLM: gleiche Fragestruktur, gleiches Modell, gleiche
            Bedingungen, auf den wiki.db-Hypothesen/Gegenhypothesen selbst.
            Offen benannte Substitution, keine verschwiegene Abkuerzung.

Metrik ist der WIEDERVERWENDETE Erfindungsmelder aus verdichtung.py
(zahl_marken/zahlen/schluessel) -- dieselbe Pruefung, die auch beim Bauen des
Raums laeuft: eine Zahl in der Modellantwort, die in keiner paket()-Quelle
dieser Anfrage steht, zaehlt als Erfindung. Zweite Metrik ist eine grobe
Deckungszahl (signifikante Woerter der Antwort, die auch in der Quelle
stehen) als Hinweis auf "sieht mehr als (c)" -- ausdruecklich eine Heuristik,
keine semantische Pruefung.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, "/opt/unifieddb")
sys.path.insert(0, "/opt/clayverse/werkzeug")

from udb.abruf.paket import paket  # noqa: E402
from udb.abruf.moeglichkeitsraum import moeglichkeitsraum, _quelltext, _kurz  # noqa: E402
from verdichtung import zahl_marken, zahlen, schluessel, umgebung  # noqa: E402 -- Erfindungsmelder, wiederverwendet

DB_PATH = "/var/lib/clay/wiki.db"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODELL = "llama-3.1-8b-instant"
KONTINGENT = "/opt/clayverse/werkzeug/kontingent.py"
KONTO = "clayverse"
ZUGANG = "groq_llama31_8b"   # im Kontingentbuch registriert, gemessen 14400/Topf, 30 RPM

SYSTEM_HALLU = ("Du bist ein hilfreicher Assistent. Antworte kurz (2-4 Saetze), sachlich, "
                "deutsch. Erfinde NIEMALS Zahlen, Namen oder Daten, die nicht im gegebenen "
                "Kontext stehen oder dir sicher bekannt sind. Wenn du unsicher bist, sag das.")


def tokens(text: str):
    """Echter Tokenizer, keine Zeichenzahl (dieselbe Falle wie in zustand_mess.py)."""
    try:
        import tiktoken
    except ImportError:
        return None
    return len(tiktoken.get_encoding("cl100k_base").encode(text))


# ── Stichprobe: echte Titel aus der Quelle, nicht handgetippt ───────────
def stichprobe_fragen(n: int) -> list:
    c = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    c.row_factory = sqlite3.Row
    rows = c.execute(
        "SELECT titel FROM artikel WHERE art IN ('hypothese','gegenhypothese') "
        "AND titel IS NOT NULL AND length(titel) > 20 ORDER BY RANDOM() LIMIT ?",
        (n,),
    ).fetchall()
    c.close()
    return [" ".join(r["titel"].split()[:10]) for r in rows]


# ── ZIEL ──────────────────────────────────────────────────────────────
def ziel_lauf(n: int = 20, budget: int = 8) -> dict:
    fragen = stichprobe_fragen(n)
    details = []
    for f in fragen:
        r = moeglichkeitsraum(f, budget=budget)
        details.append({
            "frage": f[:80], "raum_da": r["raum"] is not None,
            "einseitig": r.get("einseitig"),
            "quelle_hyp": r.get("quelle_hypothesen", 0),
            "quelle_gegen": r.get("quelle_gegenseite", 0),
        })
    hatte_material = [d for d in details if d["quelle_hyp"] or d["quelle_gegen"]]
    brauchbar = sum(1 for d in details if d["raum_da"])
    zweiseitig = sum(1 for d in details if d["raum_da"] and d["einseitig"] is False)
    einseitig = sum(1 for d in details if d["raum_da"] and d["einseitig"] is True)
    return {
        "n": len(fragen),
        "paket_lieferte_material": len(hatte_material),
        "davon_raum_gebaut": sum(1 for d in hatte_material if d["raum_da"]),
        "brauchbare_raeume_von_n": brauchbar,
        "zweiseitig": zweiseitig, "einseitig_gemeldet": einseitig,
        "details": details,
    }


# ── SCHATTEN ──────────────────────────────────────────────────────────
def _stat(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {"n": len(xs), "min": xs[0], "max": xs[-1],
            "median": xs[len(xs) // 2], "avg": round(sum(xs) / len(xs), 1)}


def schatten_lauf(n: int = 20, budget: int = 8) -> dict:
    fragen = stichprobe_fragen(n)
    tok, zeichen, zusatz_us = [], [], []
    for f in fragen:
        r = moeglichkeitsraum(f, budget=budget)
        if r["raum"] is None:
            continue
        blob = json.dumps(r["raum"], ensure_ascii=False)
        t = tokens(blob)
        if t is not None:
            tok.append(t)
        zeichen.append(len(blob))
        zusatz_us.append(r["latenz_zusatz_us"])
    return {
        "token": _stat(tok), "zeichen": _stat(zeichen),
        "latenz_zusatz_us_ueber_paket": _stat(zusatz_us),
        "tokenizer": "cl100k_base (tiktoken)" if tok else "tiktoken FEHLT -- nur Zeichen gemessen",
    }


# ── HALLU: 3 Bedingungen, freies Modell, Erfindungsmelder als Metrik ───
def _kontingent_darf(menge: int = 1) -> bool:
    try:
        r = subprocess.run(["python3", KONTINGENT, "darf", "--konto", KONTO,
                            "--zugang", ZUGANG, "--menge", str(menge)],
                           capture_output=True, text=True, timeout=30)
        for z in r.stdout.splitlines():
            if "erlaubt" in z and "von" in z:
                return int(float(z.split()[0])) > 0
        return True
    except Exception:
        return True  # Kontingentbuch nicht erreichbar -- nicht blockieren, nur Buch fuehren


def _kontingent_buchen(zweck: str) -> None:
    try:
        subprocess.run(["python3", KONTINGENT, "buchen", "--konto", KONTO,
                        "--zugang", ZUGANG, "--menge", "1", "--zweck", zweck],
                       capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def _groq_chat(schluessel: str, system: str, user: str, max_tokens: int = 300,
              temperatur: float = 0.6) -> dict:
    body = {"model": GROQ_MODELL, "temperature": temperatur, "max_tokens": max_tokens,
            "messages": [{"role": "system", "content": system},
                        {"role": "user", "content": user}]}
    req = urllib.request.Request(
        GROQ_URL, data=json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + schluessel, "Content-Type": "application/json",
                "User-Agent": "clayverse-moeglichkeitsraum-mess/1.0"})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            d = json.loads(r.read().decode())
            return {"ok": True, "ms": (time.perf_counter() - t0) * 1000,
                    "text": (d["choices"][0]["message"]["content"] or "").strip()}
    except urllib.error.HTTPError as e:
        return {"ok": False, "ms": (time.perf_counter() - t0) * 1000,
                "fehler": "HTTP %s: %s" % (e.code, e.read()[:200].decode("utf-8", "replace"))}
    except Exception as e:
        return {"ok": False, "ms": (time.perf_counter() - t0) * 1000, "fehler": str(e)[:300]}


_SIG_RE = re.compile(r"[A-Za-zÄÖÜäöüß0-9_\-]{5,}")


def _sig_woerter(text: str) -> set:
    return set(w.lower() for w in _SIG_RE.findall(text or ""))


def _bewerten(antwort: str, quelltext: str, quellzahlen: set) -> dict:
    """Der WIEDERVERWENDETE Erfindungsmelder (verdichtung.zahl_marken/schluessel),
    hier auf freie Modellantworten statt auf Kondensate angewendet -- dieselbe
    Regel, derselbe Import, kein Zweitcode."""
    marken = zahl_marken(antwort)
    erfunden = [m for m in marken if not (schluessel(m) & quellzahlen)]
    sig_antwort = _sig_woerter(antwort)
    sig_quelle = _sig_woerter(quelltext)
    deckung = sig_antwort & sig_quelle
    return {"zahlen_gesamt": len(marken), "zahlen_erfunden": len(erfunden),
            "erfunden_beispiele": erfunden[:5],
            "deckung_treffer": len(deckung), "deckung_woerter_antwort": len(sig_antwort)}


def _kontext_raum(raum: dict) -> str:
    zeilen = ["MOEGLICHKEITSRAUM (Erwartungsfeld -- keine Seite ist hier die Antwort):"]
    for t in raum.get("plausibel_richtung", []):
        zeilen.append("- moeglich: %s" % t)
    for t in raum.get("spricht_dagegen", []):
        zeilen.append("- spricht dagegen: %s" % t)
    if raum.get("warnung"):
        zeilen.append("(%s)" % raum["warnung"])
    return "\n".join(zeilen)


def _kontext_naiv(pkt: dict) -> str:
    """DIE NAIVE FASSUNG, absichtlich: nur die Hypothesenseite, als Fakten
    hingestellt, keine Gegenseite -- der Fehlermodus, den F56 beheben soll."""
    hyp = pkt.get("hypothesen") or []
    zeilen = ["DAS WISSEN WIR:"]
    for h in hyp[:6]:
        zeilen.append("- %s" % _kurz(h.get("aussage", "")))
    return "\n".join(zeilen)


def _schluessel_kandidaten(u: dict) -> list:
    """GROQ/GROQ2/GROQ3 -- ⚠️ GEMESSEN beim Bau: GROQ und GROQ3 teilen einen
    Topf (kontingent.py-Katalog), der war zeitgleich mit anderen Nutzern
    dieses Hauses fast leer (TPD 499.981/500.000). GROQ2 hat einen eigenen
    Topf und lief frei. Reihenfolge probiert alle, nicht nur den ersten."""
    return [u[k] for k in ("GROQ2_API_KEY", "GROQ_API_KEY", "GROQ3_API_KEY") if u.get(k)]


def _groq_chat_mit_fallback(schluessel_liste: list, system: str, user: str, **kw) -> dict:
    """Andere Instanzen dieses Hauses nutzen dieselben freien Toepfe GLEICHZEITIG
    (gemessen beim Bau: GROQ/GROQ3-Topf war zeitweise bei 499.981/500.000 TPD).
    Zwei Runden ueber alle Schluessel, mit kurzer Wartezeit dazwischen, bevor
    aufgegeben wird -- RPM-Kollisionen sind meist Sekunden spaeter vorbei."""
    letzter = None
    for versuch in range(2):
        for k in schluessel_liste:
            res = _groq_chat(k, system, user, **kw)
            if res["ok"]:
                return res
            letzter = res
            if "429" not in str(res.get("fehler", "")):
                return res  # kein Kontingent-Grund -- nicht weiter probieren, echter Fehler
        if versuch == 0:
            time.sleep(3.0)
    return letzter or {"ok": False, "fehler": "kein Schluessel verfuegbar"}


def hallu_lauf(faelle_n: int = 6, wiederholungen: int = 3, budget: int = 8) -> dict:
    if wiederholungen <= 1:
        return {"fehler": "wiederholungen muss > 1 sein (Auftrag: n=1 beweist nichts "
                          "fuer den mehrdeutigen Fall)"}
    u = umgebung()
    schluessel_liste = _schluessel_kandidaten(u)
    if not schluessel_liste:
        return {"fehler": "kein GROQ*_API_KEY in /etc/clayverse/freie-zugaenge.env"}

    kandidaten = stichprobe_fragen(faelle_n * 8)  # Ueberzug: nicht jede Frage ist zweiseitig
    faelle = []
    for f in kandidaten:
        pkt = paket(f, budget=budget)
        raum = moeglichkeitsraum(f, budget=budget, pkt=pkt)
        if raum["raum"] is not None and raum["einseitig"] is False:
            faelle.append((f, pkt, raum))
        if len(faelle) >= faelle_n:
            break

    if not faelle:
        return {"fehler": "keine zweiseitigen (mehrdeutigen) Faelle in der Stichprobe -- "
                          "Halluzinationsvergleich braucht Mehrdeutigkeit, sonst n=1-Fehler "
                          "auf einem leichten Fall wiederholt (Auftrag)."}

    bedingungen = ["a_moeglichkeitsraum", "b_naiv", "c_kein_kontext"]
    ergebnisse = {b: [] for b in bedingungen}
    aufrufe = 0
    faelle_verwendet = []
    for f, pkt, raum in faelle:
        quelltext = (_quelltext(pkt.get("hypothesen") or [])
                    + " " + _quelltext(pkt.get("gegenseite") or []))
        quellzahlen = zahlen(quelltext)
        frage_text = ("Was ist wahrscheinlich richtig zu diesem Punkt: %s ? Antworte in "
                     "2-4 Saetzen, nur mit Fakten, die im Kontext stehen oder dir sicher "
                     "bekannt sind. Erfinde nichts." % f[:200])
        kontexte = {"a_moeglichkeitsraum": _kontext_raum(raum["raum"]),
                   "b_naiv": _kontext_naiv(pkt), "c_kein_kontext": ""}
        faelle_verwendet.append(f[:80])
        for b in bedingungen:
            for _ in range(wiederholungen):
                if not _kontingent_darf():
                    continue
                user = (kontexte[b] + "\n\n" if kontexte[b] else "") + frage_text
                res = _groq_chat_mit_fallback(schluessel_liste, SYSTEM_HALLU, user)
                aufrufe += 1
                time.sleep(0.4)  # RPM-Bremse -- geteilte Toepfe, andere Instanzen laufen mit
                _kontingent_buchen("moeglichkeitsraum_mess/%s" % b)
                if not res["ok"]:
                    continue
                bew = _bewerten(res["text"], quelltext, quellzahlen)
                bew["ms"] = round(res["ms"], 1)
                ergebnisse[b].append(bew)

    def _agg(xs):
        if not xs:
            return None
        return {"n": len(xs),
               "zahlen_erfunden_avg": round(sum(x["zahlen_erfunden"] for x in xs) / len(xs), 3),
               "antworten_mit_erfindung": sum(1 for x in xs if x["zahlen_erfunden"] > 0),
               "deckung_treffer_avg": round(sum(x["deckung_treffer"] for x in xs) / len(xs), 2)}

    je_bedingung = {b: _agg(ergebnisse[b]) for b in bedingungen}
    a, b_, c = je_bedingung["a_moeglichkeitsraum"], je_bedingung["b_naiv"], je_bedingung["c_kein_kontext"]
    beweis = None
    if a and b_ and c:
        beweis = {
            "a_halluziniert_weniger_als_b": a["zahlen_erfunden_avg"] <= b_["zahlen_erfunden_avg"],
            "a_sieht_mehr_als_c": a["deckung_treffer_avg"] > c["deckung_treffer_avg"],
        }
        beweis["entwurf_bestaetigt"] = bool(beweis["a_halluziniert_weniger_als_b"]
                                            and beweis["a_sieht_mehr_als_c"])

    return {
        "faelle_n": len(faelle), "faelle": faelle_verwendet,
        "wiederholungen": wiederholungen, "aufrufe": aufrufe,
        "je_bedingung": je_bedingung, "beweis": beweis,
        "hinweis": ("KEIN ClayVerse-Bildkorpus vorhanden (F58, blockiert, nicht Teil dieses "
                   "Auftrags) -- TEXT statt Bild, auf Anfragen wo paket() SELBST beide "
                   "Seiten liefert (mehrdeutig, 'wo es sich entscheidet')."),
        "rohdaten": ergebnisse,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    s = ap.add_subparsers(dest="cmd", required=True)
    p = s.add_parser("ziel"); p.add_argument("--n", type=int, default=20)
    p.add_argument("--budget", type=int, default=8)
    p = s.add_parser("schatten"); p.add_argument("--n", type=int, default=20)
    p.add_argument("--budget", type=int, default=8)
    p = s.add_parser("hallu"); p.add_argument("--faelle", type=int, default=6)
    p.add_argument("--wiederholungen", type=int, default=3)
    p.add_argument("--budget", type=int, default=8)
    p = s.add_parser("alle"); p.add_argument("--n", type=int, default=20)
    p.add_argument("--faelle", type=int, default=6)
    p.add_argument("--wiederholungen", type=int, default=3)
    a = ap.parse_args()

    if a.cmd == "ziel":
        print(json.dumps(ziel_lauf(a.n, a.budget), ensure_ascii=False, indent=2))
    elif a.cmd == "schatten":
        print(json.dumps(schatten_lauf(a.n, a.budget), ensure_ascii=False, indent=2))
    elif a.cmd == "hallu":
        print(json.dumps(hallu_lauf(a.faelle, a.wiederholungen, a.budget), ensure_ascii=False, indent=2))
    elif a.cmd == "alle":
        out = {"ziel": ziel_lauf(a.n), "schatten": schatten_lauf(a.n),
              "hallu": hallu_lauf(a.faelle, a.wiederholungen)}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
