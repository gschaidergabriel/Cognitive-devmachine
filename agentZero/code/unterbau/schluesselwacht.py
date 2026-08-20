#!/usr/bin/env python3
"""schluesselwacht.py — taegliche, autonome Wacht ueber alle 21 freien Zugaenge.

Owner-Auftrag: "sowas soll autonom ueberwacht werden bei allen keys und es soll
ein festes kontingent an mistral oder nvidia modellen geben die taeglich die
keys pruefen und alle fehlermeldungen die mit den keys zu tun haben auswerten".

Vorbild gelesen vor dem Bau: wache.py (Zweiteilung tot/still, append-only
Historie, "die Wache berichtet, sie greift nicht ein"), bahn.py (umgebung(),
ABSENDER-Header, darf/buchen ueber kontingent.py, model_output_is_not_authority).

    21 Schluessel -> 13 Sonden -> MECHANISCHE Einordnung -> Sondenwache
                                                                |
                          was durch ALLE Regeln faellt (Rest) -> Modell
                                                                |
                          Modell-Antwort landet in modell_meinung, NIE
                          in einordnung.

═══════════════════════════════════════════════════════════════════════
 DAS GESETZ DIESER DATEI
═══════════════════════════════════════════════════════════════════════
  ⚠️ EINE SONDE, DIE NIE GEGEN EINEN BEKANNT GUTEN **UND** EINEN BEKANNT
     TOTEN SCHLUESSEL GEPRUEFT WURDE, DARF NICHT UEBER LEBEN UND TOD
     URTEILEN. Von aussen sehen ein toter Schluessel und eine falsche
     Sonde exakt gleich aus.

Das ist keine Theorie, das ist an drei Stellen gemessen worden:

  (1) FALSCH ROT. Cloudflares /client/v4/user/tokens/verify antwortet auf
      unseren GESUNDEN Token mit 401 "Invalid API Token" (code 1000) — der
      Endpunkt gilt nur fuer Nutzer-Token, nicht fuer kontogebundene. Ein
      Agent hatte den Schluessel daraufhin fuer tot erklaert. /accounts
      liefert mit demselben Token 200.
  (2) FALSCH GRUEN, schlimmer. NVIDIAs GET /v1/models antwortet mit
      200 AUCH AUF EINEN FREI ERFUNDENEN SCHLUESSEL (am 2026-08-15
      gegengeprueft). Die erste Fassung dieser Wacht hat NVIDIA damit
      geprueft und haette drei tote NVIDIA-Schluessel ewig als gesund
      gemeldet. Nur der Chat-Endpunkt authentifiziert wirklich (403
      "Authorization failed").
  (3) NICHT UNTERSCHEIDBAR. RapidAPI antwortet auf einen toten Schluessel
      mit exakt demselben 403 "You are not subscribed to this API." wie auf
      ein fehlendes Abo. Diese Sonde kann Leben BEWEISEN (200), aber Tod
      nicht DIAGNOSTIZIEREN. Sie sagt deshalb nie SCHLUESSEL_TOT.

Darum traegt jede Sonde unten zwei Felder: 'bestaetigt' (wann und WIE sie
gegen bekannt gute/tote Schluessel geprueft wurde) und 'tot_erkennbar'.
Fehlt die Bestaetigung, wird aus SCHLUESSEL_TOT ein SONDE_UNBESTAETIGT — und
das geht an einen Menschen, nicht in die Statistik und nicht an ein Modell
(ein Modell kann eine Sonde nicht bestaetigen, es kann nur raten).

═══════════════════════════════════════════════════════════════════════
 JEDER SCHLUESSEL IST EINE EIGENE ZEILE
═══════════════════════════════════════════════════════════════════════
Drei Groq-Schluessel sind DREI Zustaende. Faellt Nr. 2 aus, waehrend 1 und 3
leben, darf hier nie "GROQ gesund" stehen. Gemessen und belegt: OpenRouter
Nr. 1 gab 429, waehrend Nr. 2 gleichzeitig 200 gab.

KEIN SCHLUESSELWERT WIRD JE AUSGEGEBEN ODER GESPEICHERT. Nur Laenge und die
ersten 4 Zeichen. Fehlertexte laufen vor dem Speichern durch _ohne_schluessel.
"""
from __future__ import annotations

import argparse
import json
import os
import re
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

# Cloudflare vor Groq wirft "Python-urllib/3.x" mit 403/1010 raus (bahn.py).
ABSENDER = "clayverse-schluesselwacht/1.0"

# Katalogname ist 'clayverse' (Anzeige "ClayVerse selbst (Grundlast)").
# 'clayverse_grundlast' existiert NICHT — kontingent.py bricht darauf hart ab.
KONTO = "clayverse"

ZEITLIMIT_S = 25
PLATZ = "__SCHLUESSEL__"


# ═══════════════════════════════════════════════════════════════════════
#  DIE SONDEN — jede am 2026-08-15 mit curl BEIDSEITIG gemessen
# ═══════════════════════════════════════════════════════════════════════
# 'bestaetigt' ist kein Kommentar, sondern Wirkstoff: fehlt der Wert, darf
# die Sonde kein Todesurteil faellen (siehe sondenwache()).
#
# 'rest' sagt, woher der Restkontingent-Wert kommt:
#   kopf    — der Anbieter sendet ihn als Kopfzeile der Sonde selbst (gratis)
#   koerper — er steht im Antwortkoerper der Sonde (gratis)
#   chat    — er kommt NUR am Chat-Endpunkt; kostet 1 Aufruf, siehe REST_CHAT
#   None    — der Anbieter sendet ueberhaupt keinen (gemessen, nicht vermutet)

SONDEN = {
    "groq/models": {
        "methode": "GET", "url": "https://api.groq.com/openai/v1/models",
        "kopf": {"Authorization": f"Bearer {PLATZ}"},
        "bestaetigt": "2026-08-15 beidseitig: guter Schluessel 200, erfundener "
                      "401 {\"code\":\"invalid_api_key\"}",
        "tot_erkennbar": True,
        "rest": "chat",   # /models sendet KEINE Ratelimit-Kopfzeilen, /chat schon
    },
    "gemini/models": {
        "methode": "GET",
        "url": "https://generativelanguage.googleapis.com/v1beta/models",
        # Schluessel im Header, NICHT als ?key= — URLs landen in Proxy-Logs.
        "kopf": {"x-goog-api-key": PLATZ},
        "bestaetigt": "2026-08-15 beidseitig: guter Schluessel 200, erfundener "
                      "400 'API key not valid'  ⚠️ 400, nicht 401 — deshalb "
                      "steht 400 in der Auth-Regel",
        "tot_erkennbar": True, "rest": None,
    },
    "deepseek/models": {
        "methode": "GET", "url": "https://api.deepseek.com/models",
        "kopf": {"Authorization": f"Bearer {PLATZ}"},
        "bestaetigt": "2026-08-15 beidseitig: gut 200, erfunden 401 "
                      "'Authentication Fails'",
        "tot_erkennbar": True, "rest": None,
    },
    "openrouter/key": {
        "methode": "GET", "url": "https://openrouter.ai/api/v1/key",
        "kopf": {"Authorization": f"Bearer {PLATZ}"},
        # /api/v1/models ist bei OpenRouter OEFFENTLICH und antwortet auch
        # ohne Schluessel mit 200 — als Pruefung wertlos. /key verlangt ihn.
        "bestaetigt": "2026-08-15 beidseitig: gut 200, erfunden 401 "
                      "'User not found'",
        "tot_erkennbar": True, "rest": "koerper",
    },
    "nvidia/chat": {
        # ⚠️ NICHT /v1/models. Das antwortet mit 200 auf JEDEN erfundenen
        # Schluessel (gemessen) und ist als Sonde damit wertlos — die erste
        # Fassung dieser Wacht hatte genau diesen Fehler. Nur der
        # Chat-Endpunkt authentifiziert. Kostet 1 Token je Schluessel und Tag.
        "methode": "POST", "url": "https://integrate.api.nvidia.com/v1/chat/completions",
        "kopf": {"Authorization": f"Bearer {PLATZ}",
                 "Content-Type": "application/json"},
        "koerper": {"model": "meta/llama-3.1-8b-instruct",
                    "messages": [{"role": "user", "content": "hi"}],
                    "max_tokens": 1},
        "bestaetigt": "2026-08-15 beidseitig: gut 200, erfunden 403 "
                      "'Authorization failed'",
        "tot_erkennbar": True,
        "rest": None,      # NVIDIA sendet nirgends Ratelimit-Kopfzeilen (gemessen)
        "kostet": ("nvidia", 1),
    },
    "cloudflare/accounts": {
        "methode": "GET", "url": "https://api.cloudflare.com/client/v4/accounts",
        "kopf": {"Authorization": f"Bearer {PLATZ}"},
        # ⚠️ /user/tokens/verify NICHT verwenden: er meldet unseren gesunden
        # kontogebundenen Token als 401 'Invalid API Token'. Genau daran ist
        # ein anderer Agent hier schon gescheitert.
        "bestaetigt": "2026-08-15 beidseitig: gut 200, erfunden 400 "
                      "'Invalid format for Authorization header'",
        "tot_erkennbar": True, "rest": "kopf",
    },
    "hf/whoami": {
        "methode": "GET", "url": "https://huggingface.co/api/whoami-v2",
        "kopf": {"Authorization": f"Bearer {PLATZ}"},
        "bestaetigt": "2026-08-15 beidseitig: gut 200, erfunden 401 "
                      "'Invalid username or password'",
        "tot_erkennbar": True, "rest": "kopf",
    },
    "mistral/models": {
        "methode": "GET", "url": "https://api.mistral.ai/v1/models",
        "kopf": {"Authorization": f"Bearer {PLATZ}"},
        "bestaetigt": "2026-08-15 beidseitig: gut 200, erfunden 401 "
                      "'Invalid API Key'",
        "tot_erkennbar": True,
        "rest": "chat",   # /models ohne Kopfzeilen, /chat mit
    },
    "tavily/usage": {
        # Der beste Endpunkt im ganzen Feld: kostet KEINE Suche und liefert
        # Verbrauch und Deckel gleich mit.
        "methode": "GET", "url": "https://api.tavily.com/usage",
        "kopf": {"Authorization": f"Bearer {PLATZ}"},
        "bestaetigt": "2026-08-15 beidseitig: gut 200 mit Verbrauchszaehler, "
                      "erfunden 401 'Unauthorized: missing or invalid API key'",
        "tot_erkennbar": True, "rest": "koerper",
    },
    "exa/websets": {
        # POST /search wuerde eine Suche kosten. Dieser GET kostet nichts und
        # unterscheidet trotzdem sauber — aber NUR am Antwortkoerper, beide
        # Faelle sind 401:
        #   guter Schluessel ohne Pro-Tarif -> "does not have access ... Upgrade"
        #   erfundener Schluessel           -> "Invalid API key"
        # Deshalb die ABO_FEHLT-Regel VOR der Auth-Regel.
        "methode": "GET", "url": "https://api.exa.ai/websets/v0/websets",
        "kopf": {"x-api-key": PLATZ},
        "bestaetigt": "2026-08-15 beidseitig: guter Schluessel 401 'Upgrade to "
                      "a Pro plan' (lebt!), erfundener 401 'Invalid API key'",
        "tot_erkennbar": True, "rest": None,
    },
    "e2b/sandboxes": {
        "methode": "GET", "url": "https://api.e2b.dev/sandboxes",
        "kopf": {"X-API-KEY": PLATZ},   # Bearer geht NICHT (401), gemessen
        "bestaetigt": "2026-08-15 beidseitig: gut 200 [], erfunden 401 "
                      "'Invalid API key'",
        "tot_erkennbar": True, "rest": None,
    },
    "rapidapi/jokeapi": {
        # RapidAPI hat keinen allgemeinen Pruefendpunkt — ein Schluessel gilt
        # je gebuchtem Host. Ein Host, den wir gebucht haben, ist der einzige
        # Weg. 200 beweist: Schluessel lebt UND Abo steht.
        "methode": "GET",
        "url": "https://jokeapi-v2.p.rapidapi.com/joke/Any?type=single",
        "kopf": {"X-RapidAPI-Key": PLATZ,
                 "X-RapidAPI-Host": "jokeapi-v2.p.rapidapi.com"},
        "bestaetigt": "2026-08-15 beidseitig gemessen, ABER nicht trennscharf: "
                      "guter Schluessel 200, erfundener 403 'You are not "
                      "subscribed to this API.' — identisch zum fehlenden Abo",
        # ⚠️ Genau deshalb False: 403 kann Tod ODER fehlendes Abo heissen.
        "tot_erkennbar": False, "rest": None,
    },
    "openalex/apikey": {
        # OpenAlex ist OHNE Schluessel offen (GET /works gibt 200). Der
        # Schluessel gilt nur dem Premium-Weg ?api_key=. Der Wert im Tresor
        # wird dort abgewiesen — genau wie ein frei erfundener.
        "methode": "GET",
        "url": f"https://api.openalex.org/works?per-page=1&api_key={PLATZ}",
        "kopf": {"Accept": "application/json"},
        # ⚠️ EIGENER MESSFEHLER, hier festgehalten damit er nicht wiederkommt:
        # die erste Messung gab 401 "API key not found" und ich hielt den
        # Schluessel fuer ungueltig. Ursache war MEIN Pruefskript — es ersetzte
        # den Platzhalter nur in den Kopfzeilen, nicht in der URL, und schickte
        # damit das Wort "__SCHLUESSEL__" als api_key. Sauber gemessen liefert
        # derselbe Schluessel 200 samt Kreditzaehlern. Erst das Messgeraet
        # pruefen, dann dem Ergebnis glauben.
        "bestaetigt": "2026-08-15 beidseitig: guter Schluessel 200 mit "
                      "X-RateLimit-Credits-Used, erfundener 401 'Invalid or "
                      "missing API key'",
        "tot_erkennbar": True,
        # OpenAlex sendet die Zaehler als Kopfzeilen der Sonde selbst.
        "rest": "kopf",
    },
}

# Wo der Restkontingent-Wert nur am Chat-Endpunkt haengt (gemessen: Groq und
# Mistral senden an /models NICHTS, an /chat/completions alles). 1 Token je
# Schluessel und Tag — das ist der Preis fuer die Antwort auf die Frage
# "teilen sich zwei Schluessel einen Topf".
REST_CHAT = {
    "groq/models": {"url": "https://api.groq.com/openai/v1/chat/completions",
                    "modell": "llama-3.3-70b-versatile", "zugang": "groq"},
    "mistral/models": {"url": "https://api.mistral.ai/v1/chat/completions",
                       "modell": "mistral-small-latest", "zugang": "mistral"},
}


# ═══════════════════════════════════════════════════════════════════════
#  DIE 21 SCHLUESSEL — je eine Zeile, nie zusammengefasst
# ═══════════════════════════════════════════════════════════════════════
SCHLUESSEL = [
    ("GROQ",       "GROQ_API_KEY",       "groq/models",         "groq"),
    ("GROQ2",      "GROQ2_API_KEY",      "groq/models",         "groq"),
    ("GROQ3",      "GROQ3_API_KEY",      "groq/models",         "groq"),
    ("GEMINI",     "GEMINI_API_KEY",     "gemini/models",       "gemini_frei"),
    ("GEMINI2",    "GEMINI2_API_KEY",    "gemini/models",       "gemini_frei"),
    ("DEEPSEEK",   "DEEPSEEK_API_KEY",   "deepseek/models",     "deepseek"),
    ("OPENROUTER", "OPENROUTER_API_KEY", "openrouter/key",      "openrouter"),
    ("OPENROUTER2", "OPENROUTER2_API_KEY", "openrouter/key",    "openrouter"),
    ("NVIDIA_NIM", "NVIDIA_NIM_API_KEY", "nvidia/chat",         "nvidia"),
    ("NVIDIA2",    "NVIDIA2_API_KEY",    "nvidia/chat",         "nvidia"),
    ("NVIDIA3",    "NVIDIA3_API_KEY",    "nvidia/chat",         "nvidia"),
    ("CLOUDFLARE", "CLOUDFLARE_API_KEY", "cloudflare/accounts", "cloudflare"),
    ("HF",         "HF_TOKEN",           "hf/whoami",           "hf"),
    ("MISTRAL",    "MISTRAL_API_KEY",    "mistral/models",      "mistral"),
    ("MISTRAL2",   "MISTRAL2_API_KEY",   "mistral/models",      "mistral"),
    ("MISTRAL3",   "MISTRAL3_API_KEY",   "mistral/models",      "mistral"),
    ("TAVILY",     "TAVILY_API_KEY",     "tavily/usage",        None),
    ("EXA",        "EXA_API_KEY",        "exa/websets",         None),
    ("OPENALEX",   "OPENALEX_API_KEY",   "openalex/apikey",     None),
    ("E2B",        "E2B_API_KEY",        "e2b/sandboxes",       None),
    ("RAPIDAPI",   "RAPIDAPI_KEY",       "rapidapi/jokeapi",    None),
]
# zugang=None: dieser Anbieter steht (noch) nicht im Kontingent-Katalog von
# kontingent.py. Nicht erfinden — kontingent.py bricht bei unbekannten
# Zugaengen hart ab. Solche Sonden kosten hier ohnehin nichts.


# ── Auswerter fuer den Rest: festes Kontingent, Mistral zuerst ─────────
AUSWERTER = [
    {"name": "mistral", "zugang": "mistral",
     "envs": ["MISTRAL_API_KEY", "MISTRAL2_API_KEY", "MISTRAL3_API_KEY"],
     "url": "https://api.mistral.ai/v1/chat/completions",
     "modell": "mistral-small-latest"},
    {"name": "nvidia_nim", "zugang": "nvidia",
     "envs": ["NVIDIA_NIM_API_KEY", "NVIDIA2_API_KEY", "NVIDIA3_API_KEY"],
     "url": "https://integrate.api.nvidia.com/v1/chat/completions",
     "modell": "meta/llama-3.1-8b-instruct"},
]
MODELL_AUFRUFE_PRO_TAG = 2
MODELL_MAX_TOKEN = 400
MODELL_MARKER = "#modell"


# ═══════════════════════════════════════════════════════════════════════
#  Klassen
# ═══════════════════════════════════════════════════════════════════════
GESUND = "GESUND"
SCHLUESSEL_TOT = "SCHLUESSEL_TOT"
KONTINGENT_LEER = "KONTINGENT_LEER"
MODELL_WEG = "MODELL_WEG"
ABSENDER_GEBLOCKT = "ABSENDER_GEBLOCKT"
ANBIETER_KAPUTT = "ANBIETER_KAPUTT"
NETZ = "NETZ"
ABO_FEHLT = "ABO_FEHLT"
SONDE_UNBESTAETIGT = "SONDE_UNBESTAETIGT"
UNKLAR = "UNKLAR"

# Klassen, die BEWEISEN, dass der Schluessel lebt. ABO_FEHLT gehoert dazu:
# der Exa-Schluessel sucht einwandfrei, nur das Websets-Produkt ist nicht
# gebucht. KONTINGENT_LEER auch — ein leerer Topf setzt einen gueltigen
# Schluessel voraus.
LEBT = (GESUND, ABO_FEHLT, KONTINGENT_LEER)

# Was einen Menschen braucht und NICHT an ein Modell geht.
FUER_MENSCHEN = (SCHLUESSEL_TOT, SONDE_UNBESTAETIGT)


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def heute() -> str:
    return datetime.now(timezone.utc).date().isoformat()


def umgebung() -> dict:
    """Liest /etc/clayverse/freie-zugaenge.env (600 root:root) selbst.

    BEWUSST nicht ueber EnvironmentFile= in der Unit: dort stuenden alle 21
    Schluessel in /proc/<pid>/environ und in 'systemctl show'.
    """
    d = {}
    try:
        for z in open(ENV, encoding="utf-8"):
            z = z.strip()
            if z and not z.startswith("#") and "=" in z:
                k, v = z.split("=", 1)
                d[k.strip()] = v.strip()
    except OSError as e:
        print(f"Zugangsdatei nicht lesbar: {e}", file=sys.stderr)
    return d


def _db() -> sqlite3.Connection:
    c = sqlite3.connect(DB, timeout=30)
    c.execute("PRAGMA journal_mode=WAL")
    c.execute("PRAGMA busy_timeout=30000")
    return c


def _retry(fn, *a, **kw):
    for versuch in range(5):
        try:
            return fn(*a, **kw)
        except sqlite3.OperationalError as e:
            if "locked" not in str(e).lower() and "busy" not in str(e).lower():
                raise
            if versuch == 4:
                raise
            time.sleep(0.4 * (versuch + 1))


def tabellen(c: sqlite3.Connection) -> None:
    c.execute("""CREATE TABLE IF NOT EXISTS schluessel_lage (
        schluessel      TEXT PRIMARY KEY,
        zuletzt_geprueft TEXT,
        http            INTEGER,
        ms              REAL,
        einordnung      TEXT,      -- MECHANISCH, nur hier steht die Wahrheit
        seit            TEXT,      -- wann dieser Zustand begann
        fehlertext      TEXT,
        modell_meinung  TEXT,      -- VORSCHLAG eines Modells, keine Tatsache
        geprueft_gesamt INTEGER DEFAULT 0,
        gesund_gesamt   INTEGER DEFAULT 0
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS schluessel_lauf (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit TEXT NOT NULL, schluessel TEXT NOT NULL,
        http INTEGER, ms REAL, einordnung TEXT, fehlertext TEXT
    )""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_schluessel_lauf_zeit "
              "ON schluessel_lauf(zeit)")
    # Nachruesten statt neu bauen: die Tabellen tragen schon echte Historie.
    for tab, spalte, typ in (("schluessel_lage", "sonde", "TEXT"),
                             ("schluessel_lage", "rest_kontingent", "TEXT"),
                             ("schluessel_lauf", "sonde", "TEXT"),
                             ("schluessel_lauf", "rest_kontingent", "TEXT")):
        vorhanden = {r[1] for r in c.execute(f"PRAGMA table_info({tab})")}
        if spalte not in vorhanden:
            c.execute(f"ALTER TABLE {tab} ADD COLUMN {spalte} {typ}")
    c.commit()


# ── Schutz: kein Schluessel darf je in Text landen ─────────────────────

def _ohne_schluessel(text: str, werte) -> str:
    """Letzter Riegel vor dem Speichern. Manche Anbieter spiegeln den
    gesendeten Schluessel in der Fehlermeldung zurueck (DeepSeek zeigt
    'your api key: ****0000', OpenRouter das Etikett). Ausserdem steht bei
    OpenAlex der Schluessel in der URL, die in Ausnahmetexten auftauchen kann.
    """
    t = text or ""
    for w in werte:
        if w and len(w) >= 8 and w in t:
            t = t.replace(w, "<SCHLUESSEL>")
    t = re.sub(r"\b(sk-[A-Za-z0-9_\-]{12,}|gsk_[A-Za-z0-9]{12,}|"
               r"hf_[A-Za-z0-9]{12,}|nvapi-[A-Za-z0-9_\-]{12,}|"
               r"tvly-[A-Za-z0-9_\-]{12,}|e2b_[A-Za-z0-9]{12,}|"
               r"cfat[A-Za-z0-9_\-]{12,}|AIza[A-Za-z0-9_\-]{20,})\b",
               "<SCHLUESSEL>", t)
    return t


def _fingerabdruck(wert: str) -> str:
    return f"{len(wert)} Z., {wert[:4]!r}"


# ═══════════════════════════════════════════════════════════════════════
#  1. PRUEFEN
# ═══════════════════════════════════════════════════════════════════════

REST_KOPFZEILEN = ("ratelimit", "x-rate", "remaining", "retry-after", "quota")


def _rest_aus_kopf(kopf: dict) -> dict:
    return {k: v for k, v in kopf.items()
            if any(m in k.lower() for m in REST_KOPFZEILEN)}


def _rest_aus_koerper(sonde: str, leib: str) -> dict:
    """Nur fuer die zwei Anbieter, die den Stand in den Koerper legen —
    beide Pfade an der echten Antwort abgelesen, nicht geraten."""
    try:
        d = json.loads(leib)
    except Exception:
        return {}
    if sonde == "openrouter/key":
        k = d.get("data") or {}
        return {"verbrauch_usd": k.get("usage"), "limit": k.get("limit"),
                "limit_rest": k.get("limit_remaining"),
                "verbrauch_tag": k.get("usage_daily")}
    if sonde == "tavily/usage":
        konto = d.get("account") or {}
        rest = None
        if konto.get("plan_limit") is not None and konto.get("plan_usage") is not None:
            rest = konto["plan_limit"] - konto["plan_usage"]
        return {"plan": konto.get("current_plan"), "verbraucht": konto.get("plan_usage"),
                "limit": konto.get("plan_limit"), "rest": rest}
    return {}


def anklopfen(sonde_name: str, schluessel: str) -> dict:
    """Ein Aufruf auf der Sonde des Anbieters. Wo es geht: eine Liste oder
    eine Konto-Auskunft, die keinen Token kostet. Wo der Anbieter anders
    nicht ehrlich antwortet (NVIDIA): ein Chat mit max_tokens=1."""
    s = SONDEN[sonde_name]
    url = s["url"].replace(PLATZ, schluessel)
    kopf = {"User-Agent": ABSENDER, "Accept": "application/json"}
    for k, v in s["kopf"].items():
        kopf[k] = v.replace(PLATZ, schluessel)
    daten = json.dumps(s["koerper"]).encode() if s.get("koerper") else None
    req = urllib.request.Request(url, data=daten, headers=kopf,
                                 method=s["methode"])
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=ZEITLIMIT_S) as r:
            leib = r.read(6000).decode("utf-8", "replace")
            return {"http": r.status, "ms": (time.perf_counter() - t0) * 1000,
                    "leib": leib, "fehler": "", "kopf": dict(r.headers)}
    except urllib.error.HTTPError as e:
        try:
            leib = e.read(4000).decode("utf-8", "replace")
        except Exception:
            leib = ""
        return {"http": e.code, "ms": (time.perf_counter() - t0) * 1000,
                "leib": leib, "fehler": leib[:300], "kopf": dict(e.headers or {})}
    except Exception as e:
        return {"http": 0, "ms": (time.perf_counter() - t0) * 1000,
                "leib": "", "fehler": f"{type(e).__name__}: {e}"[:300], "kopf": {}}


def rest_per_chat(sonde_name: str, schluessel: str) -> dict:
    """1-Token-Chat NUR dort, wo der Anbieter den Restzaehler ausschliesslich
    am Chat-Endpunkt sendet (Groq, Mistral — beides gemessen). Bei NVIDIA
    unterbleibt das: der sendet nirgends einen Zaehler, ein Extra-Aufruf
    brachte also nichts ausser Kosten."""
    w = REST_CHAT[sonde_name]
    daten = json.dumps({"model": w["modell"],
                        "messages": [{"role": "user", "content": "hi"}],
                        "max_tokens": 1}).encode()
    req = urllib.request.Request(w["url"], data=daten, headers={
        "Authorization": f"Bearer {schluessel}", "Content-Type": "application/json",
        "User-Agent": ABSENDER}, method="POST")
    # Rueckgabe traegt seit 2026-08-20 zusaetzlich den Status unter dem
    # Sonderschluessel "_chat_http" (und den Fehlertext unter "_chat_text").
    # Vorher wurde beides verschluckt -- ein Schluessel mit totem Abo sah an
    # /models gruen aus und wurde taeglich als GESUND gemeldet, waehrend jeder
    # Produktionsaufruf an /chat/completions 402 bekam. Der Sonderschluessel
    # beginnt mit "_", damit ihn die Rest-Anzeige (_kurz_rest) nicht als
    # Kontingentwert missversteht.
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            d = _rest_aus_kopf(dict(r.headers))
            d["_chat_http"] = int(r.status)
            return d
    except urllib.error.HTTPError as e:
        d = _rest_aus_kopf(dict(e.headers or {}))
        d["_chat_http"] = int(e.code)
        try:
            d["_chat_text"] = e.read(2000).decode("utf-8", "replace")
        except Exception:
            d["_chat_text"] = ""
        return d
    except Exception as e:
        return {"_chat_http": 0, "_chat_text": f"{type(e).__name__}: {e}"[:300]}


# ═══════════════════════════════════════════════════════════════════════
#  2. EINORDNEN — mechanisch, dann Sondenwache
# ═══════════════════════════════════════════════════════════════════════

AUTH_WOERTER = (
    "invalid api key", "invalid_api_key", "invalid api token", "invalid token",
    "invalid authentication", "incorrect api key", "unauthorized",
    "authentication", "authorization", "api key", "api token", "expired",
    "revoked", "disabled", "credential", "not authorized",
    "username or password", "user not found", "api key not valid",
)
ABO_WOERTER = ("upgrade to", "upgrade your", "does not have access",
               "not subscribed", "pro plan", "requires a paid",
               "subscribe to", "plan to get access",
               # 2026-08-20 gemessen: Mistral antwortet auf einen lebenden
               # Schluessel ohne aktives Abo mit 402 und GENAU diesem Satz --
               # "check your subscription". Ohne das Wort landete der Fall in
               # UNKLAR und kostete taeglich einen Modellaufruf, um dann doch
               # "Abonnement nicht aktiv" zu sagen. Mechanisch statt geraten.
               "check your subscription", "your subscription")
KONTINGENT_WOERTER = ("rate limit", "rate_limit", "quota", "too many requests",
                      "resource_exhausted", "over capacity", "exceeded")
MODELL_WOERTER = ("model", "modell", "unavailable for", "no endpoints",
                  "does not exist")


def einordnen(http: int, text: str) -> tuple[str, str]:
    """MECHANISCH, in dieser Reihenfolge. Gibt (Klasse, Regel) zurueck.

    Die Reihenfolge ist das Ergebnis der Gegenproben, nicht Geschmack:
      - 1010/Cloudflare VOR Auth: beide sind 403. Erst pruefen, ob WIR das
        Problem sind, bevor ein fremder Schluessel beschuldigt wird.
      - ABO VOR Auth: Exa antwortet auf einen LEBENDEN Schluessel mit 401
        'Upgrade to a Pro plan'. Ohne diese Vorfahrt waere ein gesunder
        Schluessel taeglich als tot gemeldet worden.
      - 400 GEHOERT in die Auth-Regel: Gemini antwortet auf einen toten
        Schluessel mit 400 'API key not valid' (gemessen), nicht mit 401.
        Ohne 400 waere ein toter Gemini-Schluessel nie aufgefallen.
      - 429 frueh: ein leerer Topf ist kein Fehler, er heilt von selbst.
    """
    t = (text or "").lower()

    if http == 0:
        if "timed out" in t or "timeout" in t:
            return NETZ, "kein HTTP-Code, Zeitlimit"
        if "name or service not known" in t or "nodename" in t or "dns" in t:
            return NETZ, "kein HTTP-Code, DNS"
        return NETZ, "kein HTTP-Code (Verbindung)"

    if 200 <= http < 300:
        return GESUND, f"HTTP {http}"

    if http == 429:
        return KONTINGENT_LEER, "HTTP 429"

    if http == 403 and ("1010" in t or "cloudflare" in t or "just a moment" in t
                        or "attention required" in t):
        return ABSENDER_GEBLOCKT, "403 + Cloudflare/1010 — unser Absender, nicht der Schluessel"

    if http in (401, 402, 403) and any(w in t for w in ABO_WOERTER):
        return ABO_FEHLT, f"HTTP {http} + Tarif-/Abo-Wort (Schluessel lebt)"

    if http in (400, 401, 403) and any(w in t for w in AUTH_WOERTER):
        return SCHLUESSEL_TOT, f"HTTP {http} + Auth-Wort"

    if http == 404 and any(w in t for w in MODELL_WOERTER):
        return MODELL_WEG, "404 + Modellname/Modellwort"

    if 500 <= http < 600:
        return ANBIETER_KAPUTT, f"HTTP {http}"

    if http in (401, 403) and not t.strip():
        return UNKLAR, f"HTTP {http}, aber leerer Fehlertext"
    if any(w in t for w in KONTINGENT_WOERTER):
        return KONTINGENT_LEER, f"HTTP {http} + Kontingent-Wort"
    return UNKLAR, f"HTTP {http}, keine Regel trifft"


def sonde_je_bestaetigt(c, sonde_name: str) -> tuple[bool, str]:
    """Zwei unabhaengige Wege, eine Sonde zu bestaetigen:
      (a) im Code: sie wurde beim Bau gegen einen bekannt GUTEN und einen
          bekannt TOTEN Schluessel gemessen (Feld 'bestaetigt');
      (b) in der Historie: sie hat schon einmal fuer irgendeinen Schluessel
          einen Zustand geliefert, der LEBEN beweist.
    (b) allein genuegt nicht fuer ein Todesurteil, denn eine Sonde kann
    gruen antworten und trotzdem blind fuer Tod sein — genau das war der
    NVIDIA-Fall. Deshalb ist (a) die harte Bedingung und (b) nur Zusatz.
    """
    s = SONDEN[sonde_name]
    if s.get("bestaetigt"):
        return True, s["bestaetigt"]
    row = c.execute(
        "SELECT count(*) FROM schluessel_lauf WHERE sonde=? AND einordnung IN "
        "(?,?,?)", (sonde_name, *LEBT)).fetchone()
    if row and row[0]:
        return False, (f"nur Erfahrungswert: {row[0]} lebende Antworten in der "
                       f"Historie, aber nie gegen einen bekannt TOTEN "
                       f"Schluessel gegengeprueft")
    return False, "nie gegen bekannt gute/tote Schluessel geprueft"


def sondenwache(c, klasse: str, sonde_name: str) -> tuple[str, str]:
    """Das Gesetz aus dem Kopf dieser Datei, in Code gegossen.

    Ein Todesurteil darf nur fallen, wenn die Sonde nachweislich zwischen
    lebendem und totem Schluessel unterscheiden kann. Sonst geht der Fall an
    einen Menschen — nicht in die Statistik, nicht an ein Modell.
    """
    s = SONDEN[sonde_name]
    if klasse != SCHLUESSEL_TOT and not (klasse == ABO_FEHLT and not s["tot_erkennbar"]):
        return klasse, ""
    if not s["tot_erkennbar"]:
        return SONDE_UNBESTAETIGT, (
            f"Sonde {sonde_name} kann Tod nicht von fehlendem Abo trennen "
            f"(beides dieselbe Antwort) — Urteil ausgesetzt, Mensch noetig")
    ok, warum = sonde_je_bestaetigt(c, sonde_name)
    if not ok:
        return SONDE_UNBESTAETIGT, (
            f"Sonde {sonde_name} haette SCHLUESSEL_TOT gesagt, ist aber "
            f"unbestaetigt ({warum}) — Urteil ausgesetzt, Mensch noetig")
    return klasse, ""


# ═══════════════════════════════════════════════════════════════════════
#  3. AUSWERTEN (nur der Rest, festes Kontingent)
# ═══════════════════════════════════════════════════════════════════════

def darf(zugang: str, menge: int) -> tuple[float, str]:
    try:
        r = subprocess.run(
            ["python3", KONTINGENT, "darf", "--konto", KONTO,
             "--zugang", zugang, "--menge", str(menge), "--json"],
            capture_output=True, text=True, timeout=60)
        d = json.loads(r.stdout)
        return float(d.get("erlaubt", 0)), str(d.get("grund", "?"))
    except Exception as e:
        return 0.0, f"Kontingentbuch nicht erreichbar: {e}"


def buchen(zugang: str, menge: float, zweck: str) -> None:
    if not zugang:
        return
    try:
        # --quelle laesst kontingent.py nur als 'buchen'/'synthetic' zu;
        # die Herkunft steht deshalb in --schluessel-hinweis (freies Feld).
        subprocess.run(["python3", KONTINGENT, "buchen", "--konto", KONTO,
                        "--zugang", zugang, "--menge", str(menge),
                        "--zweck", zweck,
                        "--schluessel-hinweis", "schluesselwacht"],
                       capture_output=True, text=True, timeout=60)
    except Exception as e:
        print(f"  Buchung fehlgeschlagen: {e}", file=sys.stderr)


def modell_aufrufe_heute(c) -> int:
    row = c.execute(
        "SELECT count(*) FROM schluessel_lauf "
        "WHERE schluessel LIKE ? AND substr(zeit,1,10)=?",
        (MODELL_MARKER + "%", heute())).fetchone()
    return int(row[0] if row else 0)


def _lebender_schluessel(c, u: dict, envs: list) -> tuple:
    """Nimmt fuer den Auswerter den ersten Schluessel, den die Wacht selbst
    zuletzt als lebend gemessen hat. Die Wacht fuettert sich hier aus dem
    eigenen Messergebnis, statt blind den ersten zu nehmen."""
    for env_name in envs:
        eintrag = next((e for e in SCHLUESSEL if e[1] == env_name), None)
        if not eintrag or not u.get(env_name):
            continue
        row = c.execute("SELECT einordnung FROM schluessel_lage WHERE schluessel=?",
                        (eintrag[0],)).fetchone()
        if row is None or row[0] in LEBT:
            return u[env_name], eintrag[0]
    return None, None


def modell_rufen(w: dict, schluessel: str, system: str, frage: str) -> dict:
    daten = json.dumps({
        "model": w["modell"],
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": frage}],
        "max_tokens": MODELL_MAX_TOKEN, "temperature": 0,
    }).encode()
    req = urllib.request.Request(
        w["url"], data=daten,
        headers={"Authorization": f"Bearer {schluessel}",
                 "Content-Type": "application/json", "User-Agent": ABSENDER})
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            roh = json.loads(r.read().decode())
            return {"ok": True, "http": r.status,
                    "ms": (time.perf_counter() - t0) * 1000,
                    "text": (roh["choices"][0]["message"]["content"] or "").strip()}
    except urllib.error.HTTPError as e:
        return {"ok": False, "http": e.code, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": e.read()[:300].decode("utf-8", "replace")}
    except Exception as e:
        return {"ok": False, "http": 0, "ms": (time.perf_counter() - t0) * 1000,
                "text": "", "fehler": str(e)[:300]}


def auswerten(c, u: dict, rest: list, zusammenfassung: str) -> None:
    """Der Rest geht an ein Modell — festes Kontingent, volle Buchung.

    Was zurueckkommt, ist ein VORSCHLAG (model_output_is_not_authority) und
    landet in modell_meinung. 'einordnung' fasst diese Funktion NICHT an.

    NICHT hier: SONDE_UNBESTAETIGT-Faelle. Ein Modell kann eine Sonde nicht
    bestaetigen — es wuerde nur den Anschein von Klaerung erzeugen. Diese
    Faelle gehoeren an einen Menschen.
    """
    if not rest:
        print("Rest: 0 — kein Modell-Aufruf noetig (Normalfall).")
        return
    schon = modell_aufrufe_heute(c)
    frei = MODELL_AUFRUFE_PRO_TAG - schon
    if frei <= 0:
        print(f"Tageskontingent aufgebraucht ({schon}/{MODELL_AUFRUFE_PRO_TAG}) "
              f"— kein Aufruf. Der Rest bleibt UNKLAR und wartet auf morgen.")
        return

    system = ("you look at api key errors. answer GERMAN, short. "
              "for each key one line: KEY = one sentence what likely wrong and "
              "what human must do. no praise, no filler. "
              "if you not sure, say 'unklar'. never invent error codes.")
    frage = zusammenfassung + "\n\nUNKLARE FAELLE:\n" + "\n".join(rest)

    for w in AUSWERTER:
        if frei <= 0:
            break
        k, welcher = _lebender_schluessel(c, u, w["envs"])
        if not k:
            print(f"  {w['name']}: kein lebender Schluessel — uebersprungen")
            continue
        erlaubt, grund = darf(w["zugang"], 1)
        print(f"  Kontingentbuch {w['zugang']}: {erlaubt:g} von 1 — {grund}")
        if erlaubt < 1:
            continue
        res = modell_rufen(w, k, system, frage)
        buchen(w["zugang"], 1, "schluesselwacht-auswertung")
        _retry(c.execute,
               "INSERT INTO schluessel_lauf (zeit, schluessel, http, ms, "
               "einordnung, fehlertext, sonde) VALUES (?,?,?,?,?,?,?)",
               (jetzt(), f"{MODELL_MARKER}:{w['name']}", res["http"],
                round(res["ms"], 1), "MODELL",
                _ohne_schluessel(res.get("fehler", "") or res["text"][:300],
                                 u.values()), welcher))
        c.commit()
        frei -= 1
        if not res["ok"]:
            print(f"  {w['name']}: FEHLER {res['http']} "
                  f"{res.get('fehler','')[:80]} — naechster Auswerter")
            continue
        meinung = _ohne_schluessel(res["text"], u.values())
        print(f"  {w['name']} ({w['modell']}, Schluessel {welcher}) "
              f"in {res['ms']:.0f} ms:")
        for zeile in meinung.splitlines():
            print(f"    | {zeile}")
        for name in [r.split(" ", 1)[0] for r in rest]:
            treffer = [z for z in meinung.splitlines() if name in z]
            if treffer:
                _retry(c.execute,
                       "UPDATE schluessel_lage SET modell_meinung=? WHERE schluessel=?",
                       (f"[{w['name']}/{w['modell']} {jetzt()[:19]}] "
                        + " ".join(treffer)[:500], name))
        c.commit()
        return


# ── Schreiben ──────────────────────────────────────────────────────────

def lage_schreiben(c, name, sonde, http, ms, klasse, fehlertext, rest) -> str:
    """'seit' bleibt stehen, solange die Klasse gleich bleibt.

    ⚠️ Ausgeschriebene Spaltenliste, ON CONFLICT DO UPDATE SET mit benannten
    Spalten. Kein INSERT OR REPLACE: das hat hier dreimal nicht genannte
    Spalten auf NULL gesetzt. modell_meinung steht absichtlich NICHT im
    UPDATE-Teil und ueberlebt damit jede Messung.
    """
    alt = c.execute("SELECT einordnung, seit FROM schluessel_lage WHERE schluessel=?",
                    (name,)).fetchone()
    seit = alt[1] if (alt and alt[0] == klasse and alt[1]) else jetzt()
    rest_j = json.dumps(rest, ensure_ascii=False) if rest else None
    _retry(c.execute, """
        INSERT INTO schluessel_lage
            (schluessel, zuletzt_geprueft, http, ms, einordnung, seit,
             fehlertext, modell_meinung, geprueft_gesamt, gesund_gesamt,
             sonde, rest_kontingent)
        VALUES (?,?,?,?,?,?,?,NULL,1,?,?,?)
        ON CONFLICT(schluessel) DO UPDATE SET
            zuletzt_geprueft = excluded.zuletzt_geprueft,
            http             = excluded.http,
            ms               = excluded.ms,
            einordnung       = excluded.einordnung,
            seit             = excluded.seit,
            fehlertext       = excluded.fehlertext,
            sonde            = excluded.sonde,
            rest_kontingent  = excluded.rest_kontingent,
            geprueft_gesamt  = schluessel_lage.geprueft_gesamt + 1,
            gesund_gesamt    = schluessel_lage.gesund_gesamt
                               + CASE WHEN excluded.einordnung=? THEN 1 ELSE 0 END
    """, (name, jetzt(), http, round(ms, 1), klasse, seit, fehlertext or None,
          1 if klasse == GESUND else 0, sonde, rest_j, GESUND))
    _retry(c.execute,
           "INSERT INTO schluessel_lauf (zeit, schluessel, http, ms, einordnung, "
           "fehlertext, sonde, rest_kontingent) VALUES (?,?,?,?,?,?,?,?)",
           (jetzt(), name, http, round(ms, 1), klasse, fehlertext or None,
            sonde, rest_j))
    c.commit()
    return seit


# ── Unterbefehle ───────────────────────────────────────────────────────

ZEICHEN = {GESUND: "✓", KONTINGENT_LEER: "·", ABSENDER_GEBLOCKT: "⚠",
           ANBIETER_KAPUTT: "⚠", MODELL_WEG: "⚠", NETZ: "⚠", ABO_FEHLT: "○",
           SCHLUESSEL_TOT: "✘", SONDE_UNBESTAETIGT: "?", UNKLAR: "?"}


def _dauer(seit: str) -> str:
    try:
        d = (datetime.now(timezone.utc) - datetime.fromisoformat(seit)).total_seconds()
    except Exception:
        return "?"
    if d < 3600:
        return f"{d/60:.0f} min"
    if d < 86400:
        return f"{d/3600:.1f} h"
    return f"{d/86400:.1f} d"


def _kurz_rest(rest: dict) -> str:
    if not rest:
        return ""
    teile = []
    for k, v in rest.items():
        if v is None:
            continue
        kk = (k.replace("x-ratelimit-", "").replace("remaining-", "rest-")
              .replace("-minute", "/min"))
        teile.append(f"{kk}={v}")
    return " ".join(teile[:4])


def cmd_pruefen(a) -> None:
    c = _db()
    tabellen(c)
    u = umgebung()
    print(f"schluesselwacht pruefen — {jetzt()}   ({len(SCHLUESSEL)} Schluessel, "
          f"{len(SONDEN)} Sonden)\n")
    rest_unklar, zeilen, menschen = [], [], []
    zaehler = {}
    for name, env_name, sonde, zugang in SCHLUESSEL:
        k = u.get(env_name)
        rest = {}
        if not k:
            klasse, regel, fehler, http, ms = (
                UNKLAR, "kein Schluessel in der Zugangsdatei",
                "Schluessel fehlt", 0, 0.0)
        else:
            r = anklopfen(sonde, k)
            http, ms = r["http"], r["ms"]
            # Bei 2xx wird der Koerper NICHT eingeordnet: dort stehen
            # Modellnamen und Beschreibungen, in denen Worte wie 'not found'
            # vorkommen und sonst eine Regel ausloesen wuerden.
            klasse, regel = einordnen(
                http, r["fehler"] if (http >= 400 or http == 0) else "")
            klasse, hinweis = sondenwache(c, klasse, sonde)
            if hinweis:
                regel = hinweis
            fehler = _ohne_schluessel(r["fehler"], u.values())[:300]
            rest = _rest_aus_kopf(r["kopf"])
            if SONDEN[sonde].get("rest") == "koerper":
                rest.update({x: y for x, y in
                             _rest_aus_koerper(sonde, r["leib"]).items() if y is not None})
            if (a.rest and SONDEN[sonde].get("rest") == "chat"
                    and klasse in LEBT and sonde in REST_CHAT):
                _chat = rest_per_chat(sonde, k)
                buchen(REST_CHAT[sonde]["zugang"], 1, "schluesselwacht-restzaehler")
                # ── Der Chat-Endpunkt entscheidet, wenn er widerspricht ──
                # Nur bei PRO-SCHLUESSEL-Lagen (401/402/403): das sind die
                # Faelle, in denen DIESER Schluessel im Betrieb nicht traegt,
                # obwohl /models ihn kennt. 429/5xx bleiben aussen vor -- ein
                # voller Topf oder eine Anbieterstoerung sagt nichts ueber den
                # Schluessel und wuerde ihn nur zu Unrecht anschwaerzen.
                _chttp = int(_chat.pop("_chat_http", 0) or 0)
                _ctext = _chat.pop("_chat_text", "")
                rest.update(_chat)
                if _chttp in (401, 402, 403):
                    klasse, regel = einordnen(_chttp, _ctext)
                    regel = (f"Chat-Endpunkt HTTP {_chttp} trotz gruener "
                             f"/models-Sonde — {regel}")
                    fehler = _ohne_schluessel(_ctext, u.values())[:300]
            kosten = SONDEN[sonde].get("kostet")
            if kosten and klasse in LEBT:
                buchen(kosten[0], kosten[1], "schluesselwacht-sonde")
        seit = lage_schreiben(c, name, sonde, http, ms, klasse, fehler, rest)
        zaehler[klasse] = zaehler.get(klasse, 0) + 1
        pfx = _fingerabdruck(k) if k else "fehlt"
        print(f"  {ZEICHEN.get(klasse,'?')} {name:12} {klasse:19} {http:<4}"
              f"{ms:6.0f} ms  seit {_dauer(seit):>7}  [{pfx:14}] {sonde}")
        if rest:
            print(f"      Rest: {_kurz_rest(rest)}")
        if klasse != GESUND:
            print(f"      Regel: {regel}")
            if fehler:
                print(f"      Antwort: {fehler[:140]}")
        zeilen.append(f"{name}: HTTP {http}, {klasse}")
        if klasse == UNKLAR:
            rest_unklar.append(f"{name} sonde={sonde} http={http} text={fehler[:200]}")
        if klasse in FUER_MENSCHEN:
            menschen.append((name, klasse, regel, fehler))

    print("\n  " + " · ".join(f"{k}={v}" for k, v in sorted(zaehler.items())))

    if menschen:
        print("\n" + "=" * 70)
        print("  FUER EINEN MENSCHEN — geht bewusst NICHT an ein Modell:")
        for name, klasse, regel, fehler in menschen:
            print(f"    {name}: {klasse}")
            print(f"       {regel}")
            if fehler:
                print(f"       Antwort: {fehler[:130]}")
        print("=" * 70)

    if a.modell:
        print("\nAuswertung des Rests:")
        auswerten(c, u, rest_unklar, "LAGE:\n" + "\n".join(zeilen))
    elif rest_unklar:
        print(f"\nRest: {len(rest_unklar)} unklar — 'pruefen --modell' wertet ihn aus.")
    c.close()


def cmd_taeglich(a) -> None:
    a.modell = True
    a.rest = True
    cmd_pruefen(a)


def cmd_stand(a) -> None:
    c = _db()
    tabellen(c)
    rows = c.execute(
        "SELECT schluessel, zuletzt_geprueft, http, ms, einordnung, seit, "
        "fehlertext, modell_meinung, geprueft_gesamt, gesund_gesamt, sonde, "
        "rest_kontingent FROM schluessel_lage ORDER BY "
        "CASE einordnung WHEN ? THEN 0 WHEN ? THEN 1 WHEN ? THEN 2 ELSE 3 END, "
        "schluessel", (SCHLUESSEL_TOT, SONDE_UNBESTAETIGT, UNKLAR)).fetchall()
    if not rows:
        print("Noch keine Pruefung gelaufen. 'schluesselwacht.py pruefen' zuerst.")
        return
    print(f"{'SCHLUESSEL':13}{'ZUSTAND':20}{'HTTP':>4}{'ms':>7}{'SEIT':>9}"
          f"{'GESUND':>8}  SONDE")
    print("-" * 92)
    for (s, zg, http, ms, kl, seit, ft, mm, ges, gd, sonde, rj) in rows:
        quote = f"{100*gd/ges:.0f}%" if ges else "-"
        print(f"{ZEICHEN.get(kl,'?')} {s:11}{kl:20}{http if http is not None else '-':>4}"
              f"{ms or 0:7.0f}{_dauer(seit):>9}{quote:>8}  {sonde or '-'}")
        if rj:
            try:
                kurz = _kurz_rest(json.loads(rj))
                if kurz:
                    print(f"    Rest: {kurz}")
            except Exception:
                pass
        if kl not in LEBT and ft:
            print(f"    Antwort: {ft[:120]}")
        if mm:
            print(f"    Modell-MEINUNG (kein Befund): {mm[:150]}")
    lebend = sum(1 for r in rows if r[4] in LEBT)
    print(f"\n{lebend} von {len(rows)} Schluesseln nachweislich lebend  ·  "
          f"letzte Pruefung {rows[0][1]}  ·  Modell-Aufrufe heute "
          f"{modell_aufrufe_heute(c)}/{MODELL_AUFRUFE_PRO_TAG}")
    offen = [r for r in rows if r[4] in FUER_MENSCHEN]
    if offen:
        print(f"⚠ {len(offen)} Fall/Faelle warten auf einen Menschen: "
              + ", ".join(f"{r[0]} ({r[4]})" for r in offen))
    c.close()


def cmd_sonden(a) -> None:
    """Zeigt, welche Sonde ueberhaupt urteilen darf. Wer das nicht sehen
    kann, glaubt jeder Anzeige — und genau das war der Fehler."""
    c = _db()
    tabellen(c)
    print("SONDE                 TOT ERKENNBAR   BESTAETIGT")
    print("-" * 92)
    for name in sorted(SONDEN):
        s = SONDEN[name]
        ok, warum = sonde_je_bestaetigt(c, name)
        n = sum(1 for e in SCHLUESSEL if e[2] == name)
        print(f"{name:22}{'ja' if s['tot_erkennbar'] else 'NEIN':16}"
              f"{'ja' if ok else 'NEIN':4} ({n} Schluessel)")
        print(f"    {warum}")
        if s.get("rest"):
            print(f"    Restzaehler: {s['rest']}")
    c.close()


def cmd_verlauf(a) -> None:
    c = _db()
    tabellen(c)
    print(f"Zustandswechsel der letzten {a.tage} Tage (aus schluessel_lauf):")
    rows = c.execute(
        "SELECT zeit, schluessel, http, einordnung, fehlertext FROM schluessel_lauf "
        "WHERE zeit >= datetime('now', ?) AND schluessel NOT LIKE ? ORDER BY id",
        (f"-{a.tage} days", MODELL_MARKER + "%")).fetchall()
    vorher = {}
    n = 0
    for zeit, s, http, kl, ft in rows:
        if vorher.get(s) != kl:
            if vorher.get(s) is not None:
                print(f"  {zeit[:19]}  {s:12} {vorher[s]} -> {kl}  (HTTP {http})"
                      + (f"  {str(ft)[:60]}" if ft else ""))
                n += 1
            vorher[s] = kl
    print(f"  {n} Wechsel · {len(rows)} Messpunkte")
    c.close()


def cmd_toepfe(a) -> None:
    """Teilen sich zwei Schluessel desselben Anbieters einen Zaehler?

    Wird NICHT geraten, sondern aus den gespeicherten Restzaehlern gelesen:
    sinkt der Wert von Schluessel B, nachdem NUR A benutzt wurde, ist es ein
    Topf. Bleibt er stehen, sind es zwei. Dafuer braucht es mehrere Tage
    Historie — der Befehl zeigt, was bisher da ist, und behauptet nichts.
    """
    c = _db()
    tabellen(c)
    print("Restzaehler je Schluessel (aus der Historie, neueste zuerst):\n")
    for sonde in sorted({e[2] for e in SCHLUESSEL}):
        namen = [e[0] for e in SCHLUESSEL if e[2] == sonde]
        if len(namen) < 2:
            continue
        print(f"  {sonde}  ({len(namen)} Schluessel)")
        hat_daten = False
        for n in namen:
            rows = c.execute(
                "SELECT zeit, rest_kontingent FROM schluessel_lauf WHERE schluessel=? "
                "AND rest_kontingent IS NOT NULL ORDER BY id DESC LIMIT ?",
                (n, a.punkte)).fetchall()
            if not rows:
                print(f"    {n:12} keine Restzaehler gespeichert")
                continue
            hat_daten = True
            for zeit, rj in rows:
                try:
                    print(f"    {n:12} {zeit[:19]}  {_kurz_rest(json.loads(rj))}")
                except Exception:
                    pass
        if not hat_daten:
            print("    -> dieser Anbieter sendet keine Restzaehler (gemessen). "
                  "Die Frage 'ein Topf oder zwei' ist hier so NICHT beantwortbar.")
        print()
    c.close()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    s = p.add_subparsers(dest="b", required=True)
    q = s.add_parser("pruefen", help="alle Schluessel anklopfen und einordnen")
    q.add_argument("--modell", action="store_true",
                   help="den unklaren Rest zusaetzlich vom Modell beurteilen lassen")
    q.add_argument("--rest", action="store_true",
                   help="Restzaehler auch dort holen, wo dafuer ein "
                        "1-Token-Chat noetig ist (Groq, Mistral)")
    s.add_parser("taeglich", help="was der Timer ruft: pruefen + Restzaehler + Auswertung")
    s.add_parser("stand", help="eine Tabelle: alle Schluessel, Zustand, seit wann")
    s.add_parser("sonden", help="welche Sonde darf urteilen — und warum nicht")
    t = s.add_parser("toepfe", help="teilen sich Zweitschluessel einen Zaehler?")
    t.add_argument("--punkte", type=int, default=3)
    v = s.add_parser("verlauf", help="Zustandswechsel aus der Historie")
    v.add_argument("--tage", type=int, default=14)
    a = p.parse_args()
    for feld in ("modell", "rest"):
        if not hasattr(a, feld):
            setattr(a, feld, False)
    {"pruefen": cmd_pruefen, "taeglich": cmd_taeglich, "stand": cmd_stand,
     "sonden": cmd_sonden, "toepfe": cmd_toepfe, "verlauf": cmd_verlauf}[a.b](a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
