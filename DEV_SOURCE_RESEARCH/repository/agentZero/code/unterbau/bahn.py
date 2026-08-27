#!/usr/bin/env python3
"""bahn.py — ClayVerse lagert Arbeit selbst aus, beobachtet sie und prueft sie.

Nicht ein Router, den jemand ruft. Ein Mechanismus, der sich Arbeit aus der
eigenen Warteschlange nimmt, sie auf eine FREIE Bahn schickt, das Ergebnis
PRUEFT und erst dann etwas davon behaelt.

    Warteschlange -> darf? -> freie Bahn -> PRUEFUNG -> behalten oder verwerfen
                                              |
                                              +-> gebucht, gemessen, protokolliert

Die Pruefung ist der Teil, der zaehlt. Ein Modellausgabe ist ein VORSCHLAG:

    model_output_is_not_authority     (ClayGraph, owner-fixed)

Was durchfaellt, wird verworfen und gezaehlt — nicht stillschweigend
uebernommen, weil ein Anbieter mit HTTP 200 geantwortet hat.
"""
import argparse
import json
import os
import sqlite3
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

DB = os.environ.get("CLAY_DB", "/var/lib/clay/wiki.db")
ENV = "/etc/clayverse/freie-zugaenge.env"
KONTINGENT = "/opt/clayverse/werkzeug/kontingent.py"

# ── DIE BAHNEN ─────────────────────────────────────────────────────────
# Reihenfolge = Vorzug. Frei zuerst, immer. Was hier nicht steht, wird
# nicht benutzt — es gibt keinen stillen Rueckfall auf etwas Teures.
BAHNEN = [
    {"name": "groq", "env": "GROQ_API_KEY", "zugang": "groq",
     "url": "https://api.groq.com/openai/v1/chat/completions",
     "modell": "llama-3.3-70b-versatile", "art": "openai"},
    {"name": "openrouter_frei", "env": "OPENROUTER_API_KEY", "zugang": "openrouter",
     "url": "https://openrouter.ai/api/v1/chat/completions",
     # ⚠️ meta-llama/llama-3.3-70b-instruct:free gibt es NICHT mehr — der
     # Aufruf gab 404 "unavailable for free". Aus der Liste der 18 echten
     # Gratismodelle gewaehlt, nicht aus dem Gedaechtnis.
     "modell": "nvidia/nemotron-3-super-120b-a12b:free", "art": "openai"},
    {"name": "mistral", "env": "MISTRAL_API_KEY", "zugang": "mistral",
     "url": "https://api.mistral.ai/v1/chat/completions",
     "modell": "mistral-small-latest", "art": "openai"},
    # ── LETZTE BAHN ────────────────────────────────────────────────────
    # Claude Code, lokal auf dem Wirt. Kostet Gabriels Kontingent und steht
    # deshalb GANZ hinten: erst wenn keine freie Bahn getragen hat.
    {"name": "claude_code", "env": None, "zugang": "claude_pro",
     "url": None, "modell": "sonnet", "art": "cli"},
]

# Cloudflare vor Groq weist "Python-urllib/3.x" ab (403, error code 1010).
# Mit curl ging derselbe Aufruf durch. Es lag nie am Schluessel.
ABSENDER = "clayverse-bahn/1.0"

SPHAEREN = ("frank_v0_1", "seimensch", "iar", "andreas", "gabriel",
            "clayverse", "fremd", "unklar")


_AUSFALL: dict[str, float] = {}
_SPERRE_S = 120.0


def _gesperrt(name: str) -> bool:
    """Eine Bahn, die eben ausfiel, wird kurz uebergangen — nicht bestraft.

    Ohne das laeuft jeder Auftrag in denselben Fehler und wartet jedes Mal
    das Zeitlimit ab. MIT dem wird der Ausfall zum Signal, das die anderen
    Prozesse sehen, statt zu einer Bremse fuer alle.
    """
    bis = _AUSFALL.get(name)
    return bool(bis and time.monotonic() < bis)


def _melde_ausfall(c, bahn: dict, res: dict) -> None:
    _AUSFALL[bahn["name"]] = time.monotonic() + _SPERRE_S
    try:
        c.execute("INSERT INTO bahn_lauf(zeit,art,bahn,modell,dauer_ms,http,"
                  "ergebnis,pruefung) VALUES (?,?,?,?,?,?,?,?)",
                  (jetzt(), "ausfall", bahn["name"], bahn["modell"],
                   round(res.get("ms", 0), 1), res.get("http"), "fehler",
                   str(res.get("fehler", ""))[:160]))
        c.commit()
    except Exception:
        pass


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def umgebung() -> dict:
    """Liest die Schluessel. Gibt sie NIE aus und legt sie NIE in argv."""
    d = {}
    try:
        for z in open(ENV, encoding="utf-8"):
            z = z.strip()
            if z and not z.startswith("#") and "=" in z:
                k, v = z.split("=", 1)
                d[k.strip()] = v.strip()
    except OSError:
        pass
    return d


def tabellen(c: sqlite3.Connection) -> None:
    c.execute("""CREATE TABLE IF NOT EXISTS bahn_lauf (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit TEXT NOT NULL, art TEXT NOT NULL, bahn TEXT, modell TEXT,
        ziel_id TEXT, dauer_ms REAL, http INTEGER,
        token_ein INTEGER, token_aus INTEGER,
        ergebnis TEXT NOT NULL,        -- angenommen | verworfen | fehler
        pruefung TEXT,                 -- warum verworfen
        antwort TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS bahn_lage (
        schluessel TEXT PRIMARY KEY, wert TEXT NOT NULL, zeit TEXT NOT NULL)""")
    c.commit()


def darf(konto: str, zugang: str, menge: int) -> tuple[int, str]:
    """Fragt das Kontingentbuch. Ohne diese Frage kein Aufruf."""
    try:
        r = subprocess.run(
            ["python3", KONTINGENT, "darf", "--konto", konto,
             "--zugang", zugang, "--menge", str(menge)],
            capture_output=True, text=True, timeout=30)
        for z in r.stdout.splitlines():
            if "erlaubt" in z and "von" in z:
                return int(float(z.split()[0])), z.strip()
        return menge, "keine Antwort vom Kontingentbuch — vorsichtshalber erlaubt"
    except Exception as e:
        return 0, f"Kontingentbuch nicht erreichbar: {e}"


def buchen(konto: str, zugang: str, menge: float, zweck: str) -> None:
    try:
        subprocess.run(["python3", KONTINGENT, "buchen", "--konto", konto,
                        "--zugang", zugang, "--menge", str(menge),
                        "--zweck", zweck],
                       capture_output=True, text=True, timeout=30)
    except Exception:
        pass


def rufen_cli(bahn: dict, system: str, frage: str, max_token: int = 200) -> dict:
    """Die letzte Bahn: Claude Code lokal. Kostet Gabriels Kontingent."""
    t0 = time.perf_counter()
    try:
        r = subprocess.run(
            ["sudo", "-u", "clay", "bash", "-lc",
             "cd /var/lib/clay/arbeit && timeout 120 claude -p "
             "--model sonnet --dangerously-skip-permissions"],
            input=system + "\n\n" + frage, capture_output=True, text=True, timeout=150)
        ms = (time.perf_counter() - t0) * 1000
        if r.returncode == 0 and r.stdout.strip():
            return {"ok": True, "http": 200, "ms": ms, "text": r.stdout.strip(),
                    "ein": None, "aus": None}
        return {"ok": False, "http": r.returncode, "ms": ms, "text": "",
                "fehler": (r.stderr or "leere Antwort")[:200]}
    except Exception as e:
        return {"ok": False, "http": 0, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": str(e)[:200]}


def rufen(bahn: dict, schluessel: str, system: str, frage: str,
          max_token: int = 200) -> dict:
    """Ein Aufruf auf einer Bahn. Caveman im System-Teil — gemessen -28,9 %."""
    if bahn["art"] == "cli":
        return rufen_cli(bahn, system, frage, max_token)
    daten = json.dumps({
        "model": bahn["modell"],
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": frage}],
        "max_tokens": max_token, "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        bahn["url"], data=daten,
        headers={"Authorization": f"Bearer {schluessel}",
                 "Content-Type": "application/json",
                 "User-Agent": ABSENDER})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            roh = json.loads(r.read().decode())
            ms = (time.perf_counter() - t0) * 1000
            u = roh.get("usage") or {}
            return {"ok": True, "http": r.status, "ms": ms,
                    "text": (roh["choices"][0]["message"]["content"] or "").strip(),
                    "ein": u.get("prompt_tokens"), "aus": u.get("completion_tokens")}
    except urllib.error.HTTPError as e:
        return {"ok": False, "http": e.code, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": e.read()[:200].decode("utf-8", "replace")}
    except Exception as e:
        return {"ok": False, "http": 0, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": str(e)[:200]}


# ── DIE PRUEFUNG ───────────────────────────────────────────────────────
# Hier entscheidet sich, ob Auslagerung etwas taugt. Eine Antwort mit
# HTTP 200 ist kein Ergebnis, sondern ein Vorschlag.

def pruefe_sphaere(text: str, erlaubt=SPHAEREN) -> tuple[bool, str, str]:
    """Die Antwort MUSS genau eine der erlaubten Sphaeren sein.

    Kein Aufraeumen, kein Zurechtbiegen: wer etwas anderes sagt, faellt
    durch. Ein Modell, das sich nicht an eine Liste von acht Woertern haelt,
    hat bei einer Zuordnung nichts verloren.
    """
    t = (text or "").strip().strip(".").strip('"').lower()
    t = t.split()[0] if t else ""
    if t in erlaubt:
        if t == "unklar":
            return False, t, "Modell sagt selbst unklar — richtig, wird nicht gesetzt"
        return True, t, ""
    return False, t, f"Antwort ausserhalb der erlaubten Menge: {text[:60]!r}"


def cmd_pruefen(a) -> None:
    """Welche Bahnen antworten gerade wirklich?"""
    u = umgebung()
    for b in BAHNEN:
        k = u.get(b["env"]) if b["env"] else "-"
        if not k:
            print(f"  {b['name']:18} kein Schluessel hinterlegt")
            continue
        r = rufen(b, k, "answer with one word only", "say: bereit", 10)
        if r["ok"]:
            print(f"  {b['name']:18} HTTP {r['http']}  {r['ms']:6.0f} ms  "
                  f"Modell {b['modell'][:34]}  Antwort {r['text'][:20]!r}")
        else:
            print(f"  {b['name']:18} FEHLER {r['http']}  {r.get('fehler','')[:70]}")


def cmd_sphaere(a) -> None:
    """Der erste echte Auftrag: unentschiedene Sphaeren zuordnen.

    Warum dieser zuerst: die Antwort ist auf acht Woerter beschraenkt und
    damit MECHANISCH pruefbar. Wo die Pruefung nicht mechanisch geht, ist
    Auslagerung nicht messbar — und was nicht messbar ist, wird nicht
    ausgelagert.
    """
    c = sqlite3.connect(DB, timeout=30)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA busy_timeout=30000")
    tabellen(c)
    u = umgebung()

    erlaubt, grund = darf("clayverse", BAHNEN[0]["zugang"], a.anzahl)
    print(f"Kontingentbuch: {erlaubt} von {a.anzahl} — {grund}")
    if erlaubt <= 0:
        print("nichts erlaubt, kein Aufruf.")
        return
    n = min(a.anzahl, erlaubt)

    kand = c.execute(
        "SELECT id, titel, projekt, art FROM artikel "
        "WHERE sphaere IS NULL AND titel IS NOT NULL AND length(titel) > 12 "
        "ORDER BY random() LIMIT ?", (n,)).fetchall()
    print(f"Kandidaten: {len(kand)}\n")

    system = ("you sort. answer ONE word from this list, nothing else:\n"
              + " ".join(SPHAEREN) + "\n"
              "frank_v0_1=frank the entity. seimensch=the association website.\n"
              "iar=research institute. andreas / gabriel=that person own work.\n"
              "clayverse=the server itself. fremd=third party. unklar=you not sure.\n"
              "if not clear, say unklar. never invent.")

    an = ver = fe = 0
    for r in kand:
        frage = f"projekt={r['projekt']} art={r['art']} titel={r['titel'][:140]}"
        gelaufen = None
        # ⚠️ KEINE Kette. Der Auftrag sucht sich einen Weg: jede Bahn, die
        # gerade traegt, kann ihn bedienen. Faellt eine aus, merkt der
        # Auftrag es nicht als Bruch — er geht weiter. Traegt keine, bleibt
        # er UNBEDIENT in der Warteschlange, statt verloren zu gehen.
        for b in BAHNEN:
            k = u.get(b["env"]) if b["env"] else "-"
            if not k or _gesperrt(b["name"]):
                continue
            res = rufen(b, k, system, frage, 8)
            if not res["ok"]:
                _melde_ausfall(c, b, res)
                continue
            if res["ok"]:
                gelaufen = (b, res)
                break
        if not gelaufen:
            fe += 1
            continue
        b, res = gelaufen
        gut, wert, warum = pruefe_sphaere(res["text"])
        if gut:
            an += 1
            if not a.trocken:
                # ⚠️ NICHT in artikel.sphaere. Ein Modellvorschlag ist keine
                # Tatsache. Er landet als Anreicherung mit Herkunft.
                c.execute(
                    "INSERT INTO anreicherung(artikel_id,quelle_url,art,auszug,"
                    "geholt_am,hash) VALUES (?,?,?,?,?,?)",
                    (r["id"], f"bahn://{b['name']}/{b['modell']}", "ergaenzt",
                     json.dumps({"feld": "sphaere", "vorschlag": wert}),
                     jetzt(), ""))
        else:
            ver += 1
        c.execute("INSERT INTO bahn_lauf(zeit,art,bahn,modell,ziel_id,dauer_ms,"
                  "http,token_ein,token_aus,ergebnis,pruefung,antwort) "
                  "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                  (jetzt(), "sphaere", b["name"], b["modell"], r["id"],
                   round(res["ms"], 1), res["http"], res.get("ein"), res.get("aus"),
                   "angenommen" if gut else "verworfen", warum or None,
                   res["text"][:120]))
        buchen("clayverse", b["zugang"], 1, "sphaere")
        c.commit()

    print(f"angenommen {an} · verworfen {ver} · Bahn-Fehler {fe}")
    if an + ver:
        print(f"Annahmequote {100*an/(an+ver):.0f} %")
    z = c.execute("SELECT bahn, count(*), avg(dauer_ms), sum(token_ein), sum(token_aus) "
                  "FROM bahn_lauf WHERE art='sphaere' GROUP BY bahn").fetchall()
    for b, k, d, te, ta in z:
        print(f"  {b:18} {k:4} Aufrufe  {d:6.0f} ms  Token ein {te} aus {ta}")
    c.close()


def cmd_stand(a) -> None:
    c = sqlite3.connect(DB, timeout=30)
    c.execute("PRAGMA busy_timeout=30000")
    tabellen(c)
    print("Laeufe je Ergebnis:")
    for e, n in c.execute("SELECT ergebnis, count(*) FROM bahn_lauf GROUP BY ergebnis"):
        print(f"   {e:14} {n}")
    print("\nJe Bahn:")
    for b, n, d, te, ta in c.execute(
            "SELECT bahn, count(*), avg(dauer_ms), sum(token_ein), sum(token_aus) "
            "FROM bahn_lauf GROUP BY bahn"):
        print(f"   {b:18} {n:5} Aufrufe  {d or 0:6.0f} ms  ein {te or 0} aus {ta or 0}")
    print("\nHaeufigste Verwerfungsgruende:")
    for g, n in c.execute("SELECT pruefung, count(*) FROM bahn_lauf "
                          "WHERE ergebnis='verworfen' GROUP BY pruefung "
                          "ORDER BY 2 DESC LIMIT 5"):
        print(f"   {n:4}x {str(g)[:70]}")
    c.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="b", required=True)
    s.add_parser("pruefen")
    q = s.add_parser("sphaere")
    q.add_argument("--anzahl", type=int, default=20)
    q.add_argument("--trocken", action="store_true")
    s.add_parser("stand")
    a = p.parse_args()
    {"pruefen": cmd_pruefen, "sphaere": cmd_sphaere, "stand": cmd_stand}[a.b](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
