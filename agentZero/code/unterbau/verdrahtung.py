#!/usr/bin/env python3
"""
verdrahtung.py — welcher Prozess auf welcher Bahn faehrt, und was uebrig bleibt.

Drei Dinge, mehr nicht:

  1. kb_zugang bekommt die WIRKLICHEN Grenzen der freien Anbieter -- je Modell
     dort, wo die Grenzen je Modell verschieden sind (Groq). Getrennt gefuehrt
     wird dabei:
         NULL + Feld steht in unbekannt_felder  -> UNBEKANNT (Anbieter schweigt)
         NULL + Feld steht NICHT drin           -> nicht zutreffend
         0                                      -> VERBOTEN (Grenze ist null)
     Diese drei duerfen nie gleich aussehen.

  2. kb_verdrahtung: Prozess -> erste/zweite/dritte Bahn, mit Begruendung und
     mit hoechstanteil -- dem Anteil des TAGESKONTINGENTS der ersten Bahn, den
     dieser Prozess verbrauchen darf. Die Summe je Bahn muss UNTER 1.0 bleiben,
     damit ein freier Rest fuer Unvorhergesehenes bleibt. Wird sie erreicht,
     verweigert dieses Werkzeug das Schreiben. Es normiert NICHT still.
     Ausnahme: Bahnen mit ausgereizt=1 duerfen bis 1.0 verplant werden.

  3. kb_auftrag: was keine Bahn tragen konnte, ist nicht verloren, sondern
     unbedient -- mit Grund, und mit der Liste der Bahnen, die abgewiesen
     haben. Wird eine Bahn wieder gesund, kann sie den Auftrag holen.

Mechanisch. Kein Modellaufruf. Schreibt nur kb_*-Tabellen in wiki.db.

⚠️ LEHRE, DIE FAST DIE GANZE EINBETTUNGSBAHN GEKOSTET HAETTE (2026-08-15):
    Ein 401 vom FALSCHEN Endpunkt sieht aus wie ein toter Schluessel.
    GET /client/v4/user/tokens/verify gab 401 "Invalid API Token" -- daraus
    wurde geschlossen, der Cloudflare-Schluessel sei tot. Mit demselben
    Schluessel gab GET /client/v4/accounts HTTP 200 und ai/run lieferte
    Vektoren. Ein toter Schluessel und eine falsche Sonde sind von aussen
    nicht unterscheidbar. Eine Sonde muss an einem BEKANNT GUTEN Schluessel
    geprueft werden, BEVOR man ihrem Urteil glaubt.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys

# Modulgrenze: der LESE-Zweig oeffnet die Datenbank nicht mehr selbst.
# udb ist die Vordertuer fuer den nur-lesenden Fall; der Schreib-Zweig
# bleibt lokal, weil udb.verbindung() strukturell nur liest.
sys.path.insert(0, "/opt/unifieddb")
import udb
from datetime import datetime, timezone

DB_PATH = "/var/lib/clay/wiki.db"

# ── ZUSTAND EINER BAHN ──────────────────────────────────────────────────
# nutzbar        heute gemessen erreichbar
# schluessel_tot Schluessel wird abgewiesen -- SCHLUESSELPROBLEM, kein
#                Faehigkeitsproblem. Die Grenzen bleiben trotzdem eingetragen,
#                damit sichtbar ist, was ein reparierter Schluessel freikauft.
# konto_leer     Schluessel gilt, Guthaben reicht nicht. Etwas anderes.
# unbrauchbar    technisch erreichbar, aber zu klein/zu teuer, um Bahn zu sein
# ungeprueft     nie gemessen
# sammelzeile    alte Sammelzeile, durch konkrete Zeilen abgeloest
ZUSTAENDE = ("nutzbar", "schluessel_tot", "konto_leer", "unbrauchbar",
             "ungeprueft", "sammelzeile")

# ── VORRANG-RESERVE vs HOECHSTANTEIL — zwei Bremsen, zwei Achsen ────────
# kontingent.py::RESERVE_JE_VORRANG bremst auf der KONTO-Achse: ein Konto mit
# vorrang 2 sieht nur 60 % des Topfes, gemessen am GESAMTverbrauch des Topfes.
# hoechstanteil hier bremst auf der PROZESS-Achse: gemessen am Verbrauch, den
# genau dieser Prozess auf dieser Bahn gebucht hat.
# Sie leiten sich NICHT auseinander ab und heben einander nicht auf. Es gilt
# beides; es bindet die kleinere der beiden Restmengen:
#     erlaubt = min( vorrang_rest(konto, topf), prozess_rest(prozess, topf) )
# GEMESSEN 2026-08-15 mit `verdrahtung.py probe sphaere_einordnung`, Bahn
# groq_llama31_8b (tag_limit 28800, minute_limit 60), Buchungen leer:
#   Konto clayverse (vorrang 2): Prozess-Rest 11.520 | Vorrang-Rest  36
#   Konto master_clay (vorrang 0): Prozess-Rest 11.520 | Vorrang-Rest 60
#   kontingent.py meldet beide Male "gebunden durch: (vorrang-reserve-)minute"
# Ergebnis, das die Vermutung widerlegt: fuer einen EINZELNEN Aufruf bindet
# WEDER der hoechstanteil NOCH die Tagesreserve, sondern das MINUTENLIMIT.
# Auf Tagesebene verglichen (die einzige Ebene, auf der hoechstanteil und
# Vorrang-Reserve ueberhaupt dieselbe Einheit haben):
#   hoechstanteil 0,40 -> 11.520 ; Vorrang-Reserve 0,40 -> 17.280
#   -> es bindet der hoechstanteil, solange der Topf sonst leer ist.
# Erst wenn ANDERE Konten den Topf ueber 17.280 gefuellt haben, uebernimmt
# der Vorrang. Beide Bremsen sind also real, sie liegen nur meist nicht
# gleichauf -- und die dritte Bremse (Minute) liegt vor beiden.
# Zweite Folge: laufen alle verdrahteten Prozesse unter dem Konto 'clayverse'
# (vorrang 2, Reserve 0,40), dann ist ihre gemeinsame Obergrenze ohnehin 0,60
# des Topfes -- eine Anteilssumme ueber 0,60 waere fuer dieses Konto gar nicht
# erreichbar. Das ist kein Fehler, sondern eine zweite, hoehere Sicherung.
#
# ── FREIER REST ────────────────────────────────────────────────────────
# Der nicht verdrahtete Anteil gehoert dem Konto 'clayverse_frei'. Er ist
# absichtlich ein eigenes Konto und keine blosse Rechenluecke: eine Reserve,
# die niemand sehen kann, wird gegessen.
#
# ── FALLBACK-VERKEHR ───────────────────────────────────────────────────
# hoechstanteil gilt fuer die ERSTE Bahn eines Prozesses. Verkehr, der auf die
# zweite oder dritte Bahn ausweicht, ist per Definition Ausnahmeverkehr und
# zieht dort aus dem FREIEN REST. Sonst muesste jeder Anteil dreifach gebucht
# werden und der freie Rest waere nur noch rechnerisch vorhanden.
KONTO_FREI = "clayverse_frei"
MIN_FREIER_REST = 0.25          # Warnschwelle, nicht Verbot


def jetzt() -> str:
    return datetime.now(timezone.utc).isoformat()


def verbinden(readonly: bool = False) -> sqlite3.Connection:
    if readonly:
        con = udb.verbindung()
    else:
        con = sqlite3.connect(DB_PATH, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    con.row_factory = sqlite3.Row
    return con


# ── SCHEMA-ERWEITERUNG ─────────────────────────────────────────────────
# ALTER TABLE ADD COLUMN kann in SQLite kein CHECK nachtragen. Die erlaubten
# Werte von `zustand` prueft deshalb dieser Code (pruefe_katalog), nicht die DB.
NEUE_SPALTEN = [
    ("modell", "TEXT"),                  # konkretes Modell, falls je Modell verschieden
    ("token_minute_limit", "REAL"),      # TPM
    ("token_tag_limit", "REAL"),         # TPD
    ("zustand", "TEXT NOT NULL DEFAULT 'ungeprueft'"),
    ("zustand_grund", "TEXT"),
    ("zustand_gemessen", "TEXT"),
    ("grenzen_quelle", "TEXT"),          # woher die Zahlen stammen
    ("unbekannt_felder", "TEXT"),        # JSON-Liste: welches NULL heisst UNBEKANNT
    ("unbekannt_grund", "TEXT"),
    ("kann_embedding", "INTEGER"),       # NULL=unbekannt, 0=nein, 1=ja
    ("kann_schema", "INTEGER"),
    ("kann_batch", "INTEGER"),
    ("ausgereizt", "INTEGER NOT NULL DEFAULT 0"),
    ("konten_anzahl", "INTEGER"),        # wie viele Schluessel wir haben
    ("konten_getrennt", "INTEGER"),      # 1=getrennte Toepfe GEMESSEN,
                                         # 0=ein Topf GEMESSEN, NULL=unbekannt
    ("schluessel_namen", "TEXT"),        # NUR die Namen aus der env-Datei,
                                         # niemals ein Wert
]


def schema(con: sqlite3.Connection) -> None:
    vorhanden = {r["name"] for r in con.execute("PRAGMA table_info(kb_zugang)")}
    for name, typ in NEUE_SPALTEN:
        if name not in vorhanden:
            con.execute(f"ALTER TABLE kb_zugang ADD COLUMN {name} {typ}")
    con.executescript("""
        CREATE TABLE IF NOT EXISTS kb_verdrahtung (
            prozess         TEXT PRIMARY KEY,
            bahn_erst       TEXT,
            bahn_zweit      TEXT,
            bahn_dritt      TEXT,
            hoechstanteil   REAL NOT NULL
                            CHECK (hoechstanteil > 0.0 AND hoechstanteil <= 1.0),
            begruendung     TEXT NOT NULL CHECK (LENGTH(TRIM(begruendung)) > 0),
            max_je_lauf     INTEGER,
            schema_pflicht  INTEGER,
            angelegt        TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS kb_auftrag (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            prozess           TEXT NOT NULL,
            nutzlast          TEXT NOT NULL,
            zustand           TEXT NOT NULL DEFAULT 'offen'
                              CHECK (zustand IN ('offen','laeuft','fertig','unbedienbar')),
            versuche          INTEGER NOT NULL DEFAULT 0,
            letzter_grund     TEXT,
            gesperrte_bahnen  TEXT,
            angelegt          TEXT NOT NULL,
            geaendert         TEXT NOT NULL,
            -- unbedienbar OHNE Grund ist verboten: sonst weiss niemand mehr,
            -- warum etwas liegen blieb, und der Auftrag ist faktisch verloren.
            CHECK (zustand <> 'unbedienbar'
                   OR (letzter_grund IS NOT NULL AND TRIM(letzter_grund) <> ''))
        );
        CREATE INDEX IF NOT EXISTS kb_auftrag_zustand
            ON kb_auftrag(zustand, prozess);
    """)
    con.commit()


# ── DER KATALOG: konkrete Bahnen mit gemessenen Grenzen ─────────────────
# Reihenfolge der Felder ist bewusst ein dict, kein Tupel: bei 20 Spalten ist
# ein verrutschtes Tupel die wahrscheinlichste Fehlerquelle.
#
# minute_limit = Anfragen je Minute (RPM), tag_limit = Anfragen je Tag (RPD)
# -- so, weil kontingent.py::_fensteranfang genau diese beiden Spalten liest.
# token_minute_limit = TPM, token_tag_limit = TPD.
#
# tageswechsel_stunde ist in Europe/Vienna (so rechnet kontingent.py).
# Sommerzeit: 00:00 UTC = 02:00 Wien, 00:00 Pacific = 09:00 Wien.
# ⚠️ Im Winter verschiebt sich beides um eine Stunde. Bekannte Ungenauigkeit.

GEM_GROQ = ("Groq-Doku console.groq.com/docs/rate-limits + LIVE gemessen "
            "2026-08-15 aus x-ratelimit-Kopfzeilen")
GROQ_FENSTER = ("Ruecksetzfenster UNBEKANNT: Groq nennt in x-ratelimit-reset "
                "nur eine Restdauer (gemessen 6s bzw. 37m26s) -- ob rollend "
                "oder feste Uhr ist daraus nicht unterscheidbar.")
GROQ_ORG = ("Grenzen gelten je Organisation, nicht je Schluessel.")

# ⚠️ GEMESSEN 2026-08-15, gegen die Annahme: wir haben DREI Groq-Schluessel,
# aber nur ZWEI Toepfe. Versuch: erst 5 Zusatzaufrufe nur auf GROQ, dann 5 nur
# auf GROQ2, dazwischen und danach x-ratelimit-remaining-requests aller drei
# gelesen.
#   Lauf 1 (Last auf GROQ):  GROQ -7, GROQ3 -7, GROQ2 -1
#   Lauf 2 (Last auf GROQ2): GROQ -2, GROQ3 -2, GROQ2 -6
# GROQ und GROQ3 bewegen sich immer gemeinsam und stehen dauerhaft genau
# eine Anfrage auseinander -> derselbe Topf. GROQ2 bewegt sich unabhaengig
# -> eigener Topf.
# Folge: nicht 3 x 14.400 = 43.200, sondern 2 x 14.400 = 28.800 Anfragen/Tag.
GROQ_KONTEN = ("Drei Schluessel (GROQ, GROQ2, GROQ3), aber nur ZWEI Toepfe: "
               "GROQ und GROQ3 teilen sich einen (gemessen), GROQ2 hat einen "
               "eigenen. Die Zahlen in dieser Zeile sind die SUMME beider "
               "Toepfe. Je Topf gilt die Haelfte. Ein dritter Topf existiert "
               "NICHT -- die Annahme 3 x 14.400 war falsch.")

ZUGAENGE_NEU = [
    # ── GROQ, je Modell eine Zeile: die Grenzen sind je Modell verschieden ──
    dict(zugang="groq_llama31_8b", anzeige="Groq llama-3.1-8b-instant",
         modell="llama-3.1-8b-instant", einheit="anfragen",
         minute_limit=60, tag_limit=28800,
         token_minute_limit=12000, token_tag_limit=1000000,
         tageswechsel_stunde=None, geteilt_mit="groq-organisation",
         zustand="nutzbar", zustand_grund="HTTP 200 gemessen 2026-08-15",
         grenzen_quelle=GEM_GROQ,
         unbekannt_felder=["tageswechsel_stunde"],
         unbekannt_grund=GROQ_FENSTER,
         kann_embedding=0, kann_schema=1, kann_batch=None,
         konten_anzahl=3, konten_getrennt=1,
         schluessel_namen="GROQ_API_KEY,GROQ2_API_KEY,GROQ3_API_KEY",
         besonderheit=("GEMESSEN live je Topf: x-ratelimit-limit-requests "
                       "14400, x-ratelimit-limit-tokens 6000, also 30 RPM. "
                       + GROQ_KONTEN + " TPD 500.000 je Topf steht NUR in der "
                       "Doku und taucht in KEINER Kopfzeile auf -- die hier "
                       "eingetragene 1.000.000 ist die Verdopplung eines "
                       "UNGEPRUEFTEN Doku-Werts, nicht einer Messung. "
                       + GROQ_ORG + " Groesstes freies Tageskontingent, das "
                       "wir haben. Kontext 131.072. "
                       "kann_batch: Batch-API im Freitier UNGEPRUEFT.")),
    dict(zugang="groq_gptoss_20b", anzeige="Groq openai/gpt-oss-20b",
         modell="openai/gpt-oss-20b", einheit="anfragen",
         minute_limit=60, tag_limit=2000,
         token_minute_limit=16000, token_tag_limit=400000,
         tageswechsel_stunde=None, geteilt_mit="groq-organisation",
         zustand="nutzbar", zustand_grund="HTTP 200 gemessen 2026-08-15",
         grenzen_quelle=GEM_GROQ,
         unbekannt_felder=["tageswechsel_stunde"], unbekannt_grund=GROQ_FENSTER,
         kann_embedding=0, kann_schema=1, kann_batch=None,
         konten_anzahl=3, konten_getrennt=1,
         schluessel_namen="GROQ_API_KEY,GROQ2_API_KEY,GROQ3_API_KEY",
         besonderheit=("GEMESSEN live je Topf: 1000 Anfragen/Tag, TPM 8000. "
                       + GROQ_KONTEN + " json_schema mit strict=true, Groq "
                       "sagt 100 % Schematreue zu -- deshalb die Schema-Bahn. "
                       "TPD 200.000 je Topf nur Doku.")),
    dict(zugang="groq_gptoss_120b", anzeige="Groq openai/gpt-oss-120b",
         modell="openai/gpt-oss-120b", einheit="anfragen",
         minute_limit=60, tag_limit=2000,
         token_minute_limit=16000, token_tag_limit=400000,
         tageswechsel_stunde=None, geteilt_mit="groq-organisation",
         zustand="ungeprueft",
         zustand_grund="nicht selbst aufgerufen, nur aus der Doku uebernommen",
         grenzen_quelle="Groq-Doku, NICHT live nachgemessen",
         unbekannt_felder=["tageswechsel_stunde"], unbekannt_grund=GROQ_FENSTER,
         kann_embedding=0, kann_schema=1, kann_batch=None,
         konten_anzahl=3, konten_getrennt=1,
         schluessel_namen="GROQ_API_KEY,GROQ2_API_KEY,GROQ3_API_KEY",
         besonderheit=("Groesstes Groq-Modell mit Schemamodus. Zahlen aus der "
                       "Doku, verdoppelt. " + GROQ_KONTEN)),
    dict(zugang="groq_llama33_70b", anzeige="Groq llama-3.3-70b-versatile",
         modell="llama-3.3-70b-versatile", einheit="anfragen",
         minute_limit=60, tag_limit=2000,
         token_minute_limit=24000, token_tag_limit=200000,
         tageswechsel_stunde=None, geteilt_mit="groq-organisation",
         zustand="nutzbar", zustand_grund="HTTP 200 gemessen 2026-08-15",
         grenzen_quelle=GEM_GROQ,
         unbekannt_felder=["tageswechsel_stunde"], unbekannt_grund=GROQ_FENSTER,
         kann_embedding=0, kann_schema=1, kann_batch=None,
         konten_anzahl=3, konten_getrennt=1,
         schluessel_namen="GROQ_API_KEY,GROQ2_API_KEY,GROQ3_API_KEY",
         besonderheit=("GEMESSEN live je Topf: 1000/Tag, TPM 12000. Beim "
                       "Messen waren bereits 26 der 1000 Anfragen verbraucht "
                       "-- Beleg dafuer, dass der Topf organisationsweit "
                       "geteilt ist. " + GROQ_KONTEN + " Das ist die Bahn, die "
                       "bahn.py heute zuerst ruft -- nur 1000/Tag je Topf, "
                       "deshalb ist sie fuer Massenarbeit die falsche Wahl.")),
    dict(zugang="groq_qwen3_6_27b", anzeige="Groq qwen/qwen3.6-27b",
         modell="qwen/qwen3.6-27b", einheit="anfragen",
         minute_limit=60, tag_limit=2000,
         token_minute_limit=16000, token_tag_limit=400000,
         tageswechsel_stunde=None, geteilt_mit="groq-organisation",
         zustand="ungeprueft", zustand_grund="nicht aufgerufen",
         grenzen_quelle="Groq-Doku, NICHT live nachgemessen",
         unbekannt_felder=["tageswechsel_stunde"], unbekannt_grund=GROQ_FENSTER,
         kann_embedding=0, kann_schema=1, kann_batch=None,
         konten_anzahl=3, konten_getrennt=1,
         schluessel_namen="GROQ_API_KEY,GROQ2_API_KEY,GROQ3_API_KEY",
         besonderheit=("Reserve. Andere Modellfamilie als llama/gpt-oss. "
                       + GROQ_KONTEN)),
    dict(zugang="groq_compound", anzeige="Groq compound (mit Websuche)",
         modell="groq/compound", einheit="anfragen",
         minute_limit=60, tag_limit=500,
         token_minute_limit=140000, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit="groq-organisation",
         zustand="ungeprueft", zustand_grund="nicht aufgerufen",
         grenzen_quelle="Groq-Doku",
         unbekannt_felder=["token_tag_limit", "tageswechsel_stunde"],
         unbekannt_grund=("Groq veroeffentlicht fuer compound kein TPD. "
                          + GROQ_FENSTER),
         kann_embedding=0, kann_schema=None, kann_batch=None,
         konten_anzahl=3, konten_getrennt=1,
         schluessel_namen="GROQ_API_KEY,GROQ2_API_KEY,GROQ3_API_KEY",
         besonderheit=("Freier Weg zu geerdeter Websuche innerhalb eines "
                       "Modellaufrufs. Gemini kann Erdung auch, verlangt "
                       "dafuer aber Geld je Suchanfrage. 250/Tag je Topf, "
                       + GROQ_KONTEN + " Bleibt knapp -- sparsam verdrahten. "
                       "TAVILY und EXA liegen als eigene Suchbahnen im "
                       "Schluesselvorrat, sind aber UNGEPRUEFT.")),
    dict(zugang="groq_whisper_v3", anzeige="Groq whisper-large-v3",
         modell="whisper-large-v3", einheit="anfragen",
         minute_limit=40, tag_limit=4000,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit="groq-organisation",
         zustand="ungeprueft", zustand_grund="nicht aufgerufen",
         grenzen_quelle="Groq-Doku",
         unbekannt_felder=["tageswechsel_stunde"],
         unbekannt_grund=GROQ_FENSTER,
         kann_embedding=0, kann_schema=0, kann_batch=None,
         konten_anzahl=3, konten_getrennt=1,
         schluessel_namen="GROQ_API_KEY,GROQ2_API_KEY,GROQ3_API_KEY",
         besonderheit=("Audio. 2000/Tag und 20 RPM je Topf, hier verdoppelt. "
                       + GROQ_KONTEN + " "
                       "token_minute_limit/token_tag_limit sind NULL, "
                       "weil Token bei Audio nicht die Einheit sind -- das "
                       "ist NICHT unbekannt, sondern nicht zutreffend, "
                       "deshalb stehen sie auch nicht in unbekannt_felder.")),

    # ── CLOUDFLARE: EIN Neuronentopf ueber alle Modelle ─────────────────
    dict(zugang="cloudflare_workers_ai", anzeige="Cloudflare Workers AI",
         modell=None, einheit="neuronen",
         minute_limit=3000, tag_limit=10000,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=2, geteilt_mit="ein-topf-alle-modelle",
         zustand="nutzbar",
         zustand_grund=("GEMESSEN 2026-08-15: bge-m3, bge-small-en-v1.5 und "
                        "bge-reranker-base liefern alle HTTP 200. Die "
                        "Konto-Kennung war ableitbar (siehe besonderheit)."),
         grenzen_quelle=("Cloudflare-Doku fuer den Neuronentopf; Neuronenkosten "
                         "LIVE gemessen aus meta.neurons der Antwort"),
         unbekannt_felder=["token_minute_limit", "token_tag_limit"],
         unbekannt_grund=("Cloudflare rechnet in Neuronen, nicht in Token. Ein "
                          "Token-Limit gibt es nicht -- die Token-Grenze ergibt "
                          "sich aus dem Neuronentopf und ist modellabhaengig."),
         kann_embedding=1, kann_schema=None, kann_batch=None,
         konten_anzahl=1, konten_getrennt=None,
         schluessel_namen="CLOUDFLARE_API_KEY",
         besonderheit=("Konto-Kennung 7837b9c786eead1feb3eb9e758303cf0 -- "
                       "GELESEN aus der Antwort von GET /client/v4/accounts "
                       "(HTTP 200), nicht eingetippt. Wer sie spaeter fest "
                       "eintippt, merkt einen Kontowechsel nicht mehr: dann "
                       "faellt der Aufruf still auf 403, statt dass die "
                       "Abfrage die neue Kennung liefert. "
                       "⚠️ GET /client/v4/user/tokens/verify gibt 401 "
                       "'Invalid API Token' -- das ist KEIN toter Schluessel, "
                       "sondern der falsche Pruefendpunkt fuer diese Art "
                       "Zugangsdaten; /client/v4/user gibt 403 (9109). Der "
                       "Arbeitsendpunkt ai/run funktioniert. "
                       "Neuronenkosten GEMESSEN an echtem Bestandstext: "
                       "bge-m3 = 1074,59 Neuronen je 1 Mio Token, 1024 Dim, "
                       "mehrsprachig, 8192 Token Eingabe -> 9,31 Mio Token "
                       "Einbettung je Tag. bge-small (384 Dim) laut Doku 1841 "
                       "N/1M -> 5,43 Mio/Tag und liefert kein meta zurueck, "
                       "also nicht nachmessbar. bge-reranker-base gemessen ok. "
                       "Groesster freier Einbettungstopf, den wir haben. "
                       "Ratengrenze Einbettungen 3000/min, Texterzeugung "
                       "300/min -- hier steht die Einbettungsgrenze. "
                       "Ruecksetzung 00:00 UTC = 02:00 Wien (Sommerzeit).")),

    # ── GEMINI: Grenzen nicht mehr veroeffentlicht ──────────────────────
    dict(zugang="gemini_flash_lite_latest", anzeige="Gemini Flash Lite (Alias)",
         modell="gemini-flash-lite-latest", einheit="anfragen",
         minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=9, geteilt_mit="gemini-projekt",
         zustand="nutzbar", zustand_grund="HTTP 200 gemessen 2026-08-15",
         grenzen_quelle=("keine -- Google hat die statische Freitier-Tabelle "
                         "entfernt, Grenzen nur im eingeloggten AI-Studio je "
                         "Projekt sichtbar"),
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund=("Google veroeffentlicht die Freitier-Grenzen nicht "
                          "mehr. Alle kursierenden Zahlen stammen von Dritten. "
                          "Richtige Behandlung: 429 abfangen, zuruecknehmen, "
                          "die echte Decke aus den Abweisungen lernen."),
         kann_embedding=0, kann_schema=1, kann_batch=1,
         konten_anzahl=2, konten_getrennt=None,
         schluessel_namen="GEMINI_API_KEY,GEMINI2_API_KEY",
         besonderheit=("⚠️ NUR den -latest-Alias verdrahten. Feste Modell-IDs "
                       "werden ohne Vorwarnung abgeschaltet: gemini-2.0-flash-"
                       "lite und gemini-2.5-flash-lite gaben am 2026-08-15 "
                       "beide 404 'no longer available'. Derselbe Fehler hat "
                       "am selben Tag schon die OpenRouter-Bahn gekostet. "
                       "GEMESSEN: 494 ms. RPD-Ruecksetzung Mitternacht Pacific "
                       "= 09:00 Wien. Grenzen gelten je PROJEKT, nicht je "
                       "Schluessel -- unsere zwei Schluessel GEMINI und "
                       "GEMINI2 helfen nur, wenn sie in verschiedenen "
                       "Projekten haengen; UNGEPRUEFT.")),
    dict(zugang="gemini_flash_latest", anzeige="Gemini Flash (Alias, 1M Kontext)",
         modell="gemini-flash-latest", einheit="anfragen",
         minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=9, geteilt_mit="gemini-projekt",
         zustand="ungeprueft",
         zustand_grund="nicht aufgerufen; der Lite-Alias derselben Familie geht",
         grenzen_quelle="keine -- siehe gemini_flash_lite_latest",
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund="Google veroeffentlicht die Freitier-Grenzen nicht mehr.",
         kann_embedding=0, kann_schema=1, kann_batch=1,
         konten_anzahl=2, konten_getrennt=None,
         schluessel_namen="GEMINI_API_KEY,GEMINI2_API_KEY",
         besonderheit=("Einziges freies Millionenfenster: Kontext 1.048.576, "
                       "Ausgabe 65.536. Dafuer und nur dafuer verdrahtet. "
                       "Auch hier: nur der -latest-Alias.")),
    dict(zugang="gemini_embedding_001", anzeige="Gemini gemini-embedding-001",
         modell="gemini-embedding-001", einheit="anfragen",
         minute_limit=None, tag_limit=1500,
         token_minute_limit=10000000, token_tag_limit=None,
         tageswechsel_stunde=9, geteilt_mit="gemini-projekt",
         zustand="nutzbar", zustand_grund="HTTP 200 gemessen 2026-08-15",
         grenzen_quelle=("Recherche 2026-08-15 (1500 Anfragen/Tag, 10 Mio "
                         "Token/min) -- NICHT aus Kopfzeilen bestaetigt, "
                         "nur die Erreichbarkeit ist gemessen"),
         unbekannt_felder=["minute_limit", "token_tag_limit"],
         unbekannt_grund=("Fuer RPM und TPD gibt es keine veroeffentlichte "
                          "Zahl."),
         kann_embedding=1, kann_schema=0, kann_batch=1,
         konten_anzahl=2, konten_getrennt=None,
         schluessel_namen="GEMINI_API_KEY,GEMINI2_API_KEY",
         besonderheit=("Die 1500/Tag gelten je PROJEKT. Ob GEMINI und GEMINI2 "
                       "in verschiedenen Projekten haengen, ist UNGEPRUEFT -- "
                       "deshalb steht hier 1500 und nicht 3000. "
                       "3072 Dimensionen, per Matryoshka frei kuerzbar auf "
                       "128-3072; mit 768 gemessen. 8192 Token Eingabe. "
                       "Zweite Einbettungsbahn hinter Cloudflare.")),

    # ── NVIDIA: der Kognitionsbahn ─────────────────────────────────────
    dict(zugang="nvidia_nim", anzeige="NVIDIA NIM", modell=None,
         einheit="anfragen",
         minute_limit=40, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="nutzbar",
         zustand_grund=("GEMESSEN 2026-08-15: nvidia/nv-embedqa-e5-v5 liefert "
                        "HTTP 200"),
         grenzen_quelle=("⚠️ 40 RPM stammen aus dem NVIDIA-Entwicklerforum und "
                         "von Dritten, NICHT von einer offiziellen Seite. Als "
                         "WEICHE UNTERGRENZE gefuehrt: wir bremsen darauf, "
                         "korrigieren aber nach oben/unten, sobald echte 429 "
                         "das wahre Dach zeigen."),
         unbekannt_felder=["tag_limit", "token_minute_limit", "token_tag_limit",
                           "tageswechsel_stunde"],
         unbekannt_grund=("NVIDIA veroeffentlicht weder Tagesgrenze noch "
                          "Tokengrenzen noch das Ruecksetzfenster. Auch ob das "
                          "Startguthaben (~1000) monatlich zurueckläuft, ist "
                          "UNBEKANNT -- das ist die groesste offene Frage an "
                          "dieser Bahn."),
         kann_embedding=1, kann_schema=1, kann_batch=0,
         ausgereizt=1,
         konten_anzahl=3, konten_getrennt=None,
         schluessel_namen="NVIDIA_NIM_API_KEY,NVIDIA2_API_KEY,NVIDIA3_API_KEY",
         besonderheit=("⚠️ Wir haben DREI NVIDIA-Schluessel. Ob sie getrennte "
                       "Toepfe haben, ist UNBEKANNT: NVIDIA sendet keine "
                       "remaining-Kopfzeilen, mit denen man das messen "
                       "koennte -- wie bei Groq. Deshalb steht hier 40 RPM "
                       "und NICHT 120. Wer 120 einsetzt, raet. "
                       "⭐ EIGNER-ENTSCHEIDUNG: diese Bahn ist ausschliesslich "
                       "fuer die KOGNITION von ClayVerse reserviert "
                       "(Anfrage-Einbettung, Umsortierung, Zustandsuebergaenge, "
                       "Retrieval) und darf dafuer VOLL ausgereizt werden -- "
                       "kein freier Rest. Kein Massenprozess auf diese Bahn. "
                       "ausgereizt=1. "
                       "nv-embedqa-e5-v5: 1024 Dim, Eingabe nur 512 Token, "
                       "braucht input_type query|passage. Gefuehrte Dekodierung "
                       "(xgrammar/outlines/guided_*) ist staerker als reines "
                       "json_schema. Kein Batch, keine Websuche.")),

    # ── MISTRAL: laeuft, Zahlen unveroeffentlicht ───────────────────────
    dict(zugang="mistral_small", anzeige="Mistral small (frei)",
         modell="mistral-small-latest", einheit="anfragen",
         minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="ungeprueft",
         zustand_grund=("bahn.py nutzt die Bahn produktiv, aber in dieser "
                        "Sitzung nicht nachgemessen"),
         grenzen_quelle=("keine -- Mistral zeigt RPS/TPM/Token-je-Monat nur im "
                         "eingeloggten Admin"),
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund=("Mistral veroeffentlicht die Freimodus-Grenzen nicht. "
                          "Grenzarten sind bekannt (Anfragen je SEKUNDE, Token "
                          "je Minute, Token je Monat), die Zahlen nicht."),
         kann_embedding=0, kann_schema=1, kann_batch=1,
         konten_anzahl=3, konten_getrennt=None,
         schluessel_namen="MISTRAL_API_KEY,MISTRAL2_API_KEY,MISTRAL3_API_KEY",
         besonderheit=("⚠️ Drei Schluessel, aber ob sie getrennte Toepfe haben, "
                       "ist UNBEKANNT -- Mistral sendet keine remaining-"
                       "Kopfzeilen. Nicht mit 3 multiplizieren. "
                       "Andere Modellfamilie als Groq/Gemini -- deshalb die "
                       "Zweitmeinungsbahn: eine Gegenpruefung im selben Haus "
                       "ist keine. Stufen steigen ueber tatsaechlich "
                       "abgerechnete Ausgaben, nicht ueber Guthaben; wir "
                       "bleiben also dauerhaft im Freimodus. mistral-embed ist "
                       "kostenpflichtig -- nicht als Einbettungsbahn nutzen.")),

    # ── OPENROUTER ─────────────────────────────────────────────────────
    dict(zugang="openrouter_frei", anzeige="OpenRouter :free-Modelle",
         modell=None, einheit="anfragen",
         minute_limit=40, tag_limit=100,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=2, geteilt_mit="openrouter-konto",
         zustand="ungeprueft",
         zustand_grund=("heute 429 gesehen (50/Tag aufgebraucht) und 404 auf "
                        "ein zurueckgezogenes :free-Modell; nicht neu gemessen"),
         grenzen_quelle="OpenRouter-Doku, klare Zahlen",
         unbekannt_felder=[],
         unbekannt_grund=None,
         kann_embedding=1, kann_schema=None, kann_batch=1,
         konten_anzahl=2, konten_getrennt=1,
         schluessel_namen="OPENROUTER_API_KEY,OPENROUTER2_API_KEY",
         besonderheit=("50 Anfragen/Tag und 20/min JE KONTO unter 10 $ "
                       "Lebensguthaben, 1000/Tag ab 10 $ gekauft. Wir haben "
                       "ZWEI getrennte Konten -- GEMESSEN dadurch, dass "
                       "Schluessel 1 im selben Moment 429 gab, waehrend "
                       "Schluessel 2 mit 200 antwortete. Deshalb hier 100/Tag "
                       "und 40/min. Innerhalb EINES Kontos helfen mehrere "
                       "Schluessel nicht, die Grenze ist kontoweit. "
                       "Ruecksetzung Mitternacht UTC = 02:00 Wien. "
                       "⚠️ Die :free-Liste rotiert monatlich -- Modellnamen "
                       "NIE fest verdrahten; genau daran ist der Aufruf am "
                       "2026-08-15 mit 404 gescheitert. 100/Tag bleibt zu "
                       "klein fuer eine feste Verdrahtung; die Bahn ist "
                       "Reserve fuer den freien Rest.")),

    # ── TOTE / UNBRAUCHBARE BAHNEN: eingetragen, damit sie niemand neu ──
    #    ausprobiert, und damit sichtbar ist, was ihre Reparatur wert waere.
    dict(zugang="deepseek_chat", anzeige="DeepSeek (Guthaben)",
         modell="deepseek-chat", einheit="euro",
         minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="konto_leer",
         zustand_grund=("GEMESSEN 2026-08-15: Schluessel gilt, Guthaben -0,01, "
                        "is_available false, Aufruf gibt 402 Insufficient "
                        "Balance. KONTO_LEER, nicht schluessel_tot -- das ist "
                        "ein anderes Problem mit einer anderen Loesung."),
         grenzen_quelle="kein Freitier, Vorkasse",
         unbekannt_felder=[],
         unbekannt_grund=None,
         kann_embedding=0, kann_schema=0, kann_batch=None,
         besonderheit=("Kontext 1M, Ausgabe 384K, nur json_object statt echtem "
                       "Schema. ⚠️ Ab 2026-08-16 16:00 UTC gelten neue Haupt-/"
                       "Nebenzeitpreise: das ist eine PREISERHOEHUNG. Die "
                       "Nebenzeit ist die Haelfte des NEUEN hoeheren Grundpreises "
                       "und liegt damit immer noch ueber dem heutigen Preis -- "
                       "NICHT als Ersparnis verbuchen. Hauptzeit 01:00-04:00 "
                       "und 06:00-10:00 UTC.")),
    dict(zugang="hf_inference", anzeige="Hugging Face Inference",
         modell=None, einheit="euro",
         minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="unbrauchbar",
         zustand_grund=("0,10 $ Guthaben je MONAT fuer Freinutzer. Das ist "
                        "keine Bahn, das ist eine Probe."),
         grenzen_quelle="HF-Doku",
         unbekannt_felder=[],
         unbekannt_grund=None,
         kann_embedding=1, kann_schema=None, kann_batch=0,
         besonderheit=("Als Bezugsquelle fuer Modelle und Daten weiter "
                       "wertvoll, als Rechenbahn nicht. Nicht verdrahten.")),
    dict(zugang="together_ai", anzeige="Together AI",
         modell=None, einheit="anfragen",
         minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="schluessel_tot",
         zustand_grund=("GEMESSEN 2026-08-15 (Parallelmessung): HTTP 401 "
                        "Unauthorized. Die freien Guthaben wurden eingestellt."),
         grenzen_quelle="keine",
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund="Bahn nicht erreichbar, also nichts messbar.",
         kann_embedding=None, kann_schema=None, kann_batch=None,
         konten_anzahl=0, konten_getrennt=None, schluessel_namen=None,
         besonderheit=("Steht hier, damit niemand die Bahn ein zweites Mal "
                       "ausprobiert. Kein Schluessel in freie-zugaenge.env.")),

    # ── DIENSTE, DIE KEINE RECHENBAHN SIND ─────────────────────────────
    # Seit 2026-08-15 liegen 21 Zugaenge in freie-zugaenge.env. Diese fuenf
    # sind keine Modellbahnen, koennen aber Prozesse tragen (Websuche,
    # Literatur, Sandkasten). Sie stehen hier NUR mit dem, was gemessen ist:
    # dass ein Schluessel existiert. Alles andere ist UNBEKANNT.
    dict(zugang="tavily", anzeige="Tavily (Websuche)", modell=None,
         einheit="anfragen", minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="ungeprueft", zustand_grund="Schluessel vorhanden, nie aufgerufen",
         grenzen_quelle="keine -- nicht recherchiert, nicht gemessen",
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund="Zugang wurde noch nie benutzt, es gibt nichts zu messen.",
         kann_embedding=0, kann_schema=0, kann_batch=None,
         konten_anzahl=1, konten_getrennt=None, schluessel_namen="TAVILY_API_KEY",
         besonderheit=("Kandidat fuer websuche_erdung, wenn groq_compound mit "
                       "500/Tag zu eng wird. Erst messen, dann verdrahten.")),
    dict(zugang="exa", anzeige="Exa (Websuche)", modell=None,
         einheit="anfragen", minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="ungeprueft", zustand_grund="Schluessel vorhanden, nie aufgerufen",
         grenzen_quelle="keine -- nicht recherchiert, nicht gemessen",
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund="Zugang wurde noch nie benutzt.",
         kann_embedding=0, kann_schema=0, kann_batch=None,
         konten_anzahl=1, konten_getrennt=None, schluessel_namen="EXA_API_KEY",
         besonderheit="Zweiter Kandidat fuer websuche_erdung."),
    dict(zugang="openalex", anzeige="OpenAlex (Literatur)", modell=None,
         einheit="anfragen", minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="ungeprueft", zustand_grund="Schluessel vorhanden, nie aufgerufen",
         grenzen_quelle="keine -- nicht recherchiert, nicht gemessen",
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund="Zugang wurde noch nie benutzt.",
         kann_embedding=0, kann_schema=0, kann_batch=None,
         konten_anzahl=1, konten_getrennt=None, schluessel_namen="OPENALEX_API_KEY",
         besonderheit="Datenquelle, keine Rechenbahn. Nicht verdrahtet."),
    dict(zugang="e2b", anzeige="E2B (Sandkasten)", modell=None,
         einheit="anfragen", minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="ungeprueft", zustand_grund="Schluessel vorhanden, nie aufgerufen",
         grenzen_quelle="keine -- nicht recherchiert, nicht gemessen",
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund="Zugang wurde noch nie benutzt.",
         kann_embedding=0, kann_schema=0, kann_batch=None,
         konten_anzahl=1, konten_getrennt=None, schluessel_namen="E2B_API_KEY",
         besonderheit="Codeausfuehrung, keine Modellbahn. Nicht verdrahtet."),
    dict(zugang="rapidapi", anzeige="RapidAPI (Sammelzugang)", modell=None,
         einheit="anfragen", minute_limit=None, tag_limit=None,
         token_minute_limit=None, token_tag_limit=None,
         tageswechsel_stunde=None, geteilt_mit=None,
         zustand="ungeprueft", zustand_grund="Schluessel vorhanden, nie aufgerufen",
         grenzen_quelle="keine -- Grenzen haengen am einzelnen Dienst dahinter",
         unbekannt_felder=["minute_limit", "tag_limit", "token_minute_limit",
                           "token_tag_limit"],
         unbekannt_grund=("RapidAPI ist ein Marktplatz: die Grenze gehoert "
                          "jeweils dem dahinterliegenden Dienst, nicht "
                          "RapidAPI. Eine Zahl fuer 'RapidAPI' gibt es nicht."),
         kann_embedding=None, kann_schema=None, kann_batch=None,
         konten_anzahl=1, konten_getrennt=None, schluessel_namen="RAPIDAPI_KEY",
         besonderheit="Nicht verdrahtet."),
]

# ── VERMERKE AUF DEN ALTEN SAMMELZEILEN ────────────────────────────────
# ⚠️ Hier werden AUSSCHLIESSLICH die neuen Spalten geschrieben. Die alten
# Spalten dieser elf Zeilen gehoeren kontingent.py::cmd_init -- wer sie hier
# ueberschreibt, verliert sie beim naechsten `kontingent.py init`. Genau so
# gehen Daten in diesem Haus verloren.
ALT_VERMERK = [
    ("groq", "sammelzeile",
     "abgeloest durch groq_llama31_8b / _gptoss_20b / _gptoss_120b / "
     "_llama33_70b / _qwen3_6_27b / _compound / _whisper_v3 -- Groq hat je "
     "Modell verschiedene Grenzen, eine Sammelzeile kann sie nicht fuehren."),
    ("cloudflare", "sammelzeile", "abgeloest durch cloudflare_workers_ai."),
    ("nvidia", "sammelzeile", "abgeloest durch nvidia_nim."),
    ("mistral", "sammelzeile", "abgeloest durch mistral_small."),
    ("openrouter", "sammelzeile", "abgeloest durch openrouter_frei."),
    ("deepseek", "sammelzeile", "abgeloest durch deepseek_chat (konto_leer)."),
    ("hf", "sammelzeile", "abgeloest durch hf_inference (unbrauchbar)."),
    ("gemini_frei", "sammelzeile",
     "abgeloest durch gemini_flash_lite_latest / gemini_flash_latest / "
     "gemini_embedding_001. ⚠️ Die 1500/Tag und 15/min in dieser Zeile "
     "stammen aus dem B17-Plan; Google veroeffentlicht keine Freitier-Tabelle "
     "mehr, die Zahlen sind UNBELEGT."),
    ("claude_pro", "nutzbar",
     "letzte Bahn. Kostet Gabriels Kontingent, deshalb immer zuletzt und nie "
     "zuerst. Kann weder Vektoren noch Audio -- fuer Einbettung und "
     "Transkription ist sie KEIN Rueckfall."),
    ("zai_glm_lite", "ungeprueft", "in dieser Sitzung nicht gemessen."),
    ("ocrspace", "ungeprueft", "in dieser Sitzung nicht gemessen."),
]


# ── DIE VERDRAHTUNG ────────────────────────────────────────────────────
# Geprueft, nicht abgeschrieben. Wo der Vorschlag aus ZUGAENGE-GEMESSEN.md
# nicht traegt, steht der Grund in begruendung.
VERDRAHTUNG = [
    dict(prozess="einbettung_bestand",
         bahn_erst="cloudflare_workers_ai",
         bahn_zweit="gemini_embedding_001",
         bahn_dritt=None,
         hoechstanteil=0.45, max_je_lauf=200, schema_pflicht=0,
         begruendung=(
             "Vorschlag bestaetigt: der Cloudflare-Schluessel gilt. GEMESSEN "
             "2026-08-15: bge-m3 HTTP 200, Konto-Kennung per GET /accounts "
             "GELESEN (nicht eingetippt). Kosten gemessen an echtem "
             "Bestandstext: 1074,59 Neuronen je 1 Mio Token -> 9,31 Mio Token "
             "Einbettung je Tag im vollen Topf, mit diesem Anteil 4,19 Mio je "
             "Tag. bge-m3 ist mehrsprachig (unser Bestand ist deutsch), 1024 "
             "Dim, 8192 Token Eingabe -- kein Zerhacken noetig. "
             "⚠️ ARITHMETIK: artikel_suchtext hat 9.251 Texte mit 20.756.728 "
             "Zeichen (gemessen). Bei gemessenen 1,787 Zeichen je Token sind "
             "das 11,61 Mio Token -> 2,8 Tage unter diesem Anteil, 1,25 Tage "
             "im vollen Topf. Machbar. "
             "⚠️ NICHT machbar ist der Dateibestand: 179.536 Dateien mit "
             "2.308.304.639 Zeichen = 1,29 Mrd Token -> 139 Tage selbst im "
             "vollen Topf. Ein Vollindex ueber alle Dateien ist mit freien "
             "Kontingenten kein Projekt, sondern ein Quartal. Dafuer braucht "
             "es eine Auswahl, keine groessere Bahn. "
             "⚠️ DRITTE BAHN IST BEWUSST LEER: claude_pro kann keine Vektoren "
             "liefern. Eine Einbettung auf claude_pro zurueckfallen zu lassen "
             "waere eine Kette, die nur so tut als halte sie. Was hier "
             "durchfaellt, geht als kb_auftrag ins Unbediente und wartet auf "
             "eine gesunde Einbettungsbahn. "
             "NVIDIA ist hier bewusst NICHT verdrahtet: Eigner-Entscheidung, "
             "die NVIDIA-Bahn gehoert der Kognition, nicht dem Massenlauf.")),

    dict(prozess="einbettung_anfrage",
         bahn_erst="nvidia_nim",
         bahn_zweit="cloudflare_workers_ai",
         bahn_dritt=None,
         hoechstanteil=1.0, max_je_lauf=40, schema_pflicht=0,
         begruendung=(
             "⭐ EIGNER: 'nvidia wird nur noch fuer die kognition von clayverse "
             "verwendet und voll ausgereizt'. Anfrage-Einbettung IST Kognition: "
             "sie steht im Retrieval-Pfad, nicht im Massenlauf. Deshalb "
             "hoechstanteil 1.0 -- die einzige erlaubte Ausnahme von der "
             "Regel 'Summe je Bahn unter 1.0', getragen von ausgereizt=1 auf "
             "der Bahn, nicht vom Namen 'nvidia'. "
             "512 Token Eingabegrenze ist fuer eine Suchanfrage reichlich; "
             "sie waere nur beim Massenlauf ein Problem -- und genau dort "
             "ist die Bahn auch nicht verdrahtet. "
             "⚠️ ARITHMETIK ZUM 'VOLL AUSREIZEN', damit die Erwartung stimmt: "
             "wollte man den Artikelbestand ueber NVIDIA einbetten, waeren es "
             "11,61 Mio Token / 512 = 22.680 Stuecke; bei 40 Anfragen/min sind "
             "das 9,5 Stunden -- an einem Tag machbar. Der DATEIbestand waere "
             "1,29 Mrd Token / 512 = 2,52 Mio Stuecke = 43,8 Tage bei 40 RPM. "
             "Das Zerhacken auf 512 Token vervielfacht die Anfragen; die "
             "Anfragengrenze, nicht die Tokengrenze, ist hier die Bremse. "
             "Ob die drei NVIDIA-Schluessel getrennte Toepfe haben (dann 120 "
             "RPM), ist UNBEKANNT -- gerechnet wird mit 40. "
             "Folge, die sichtbar bleiben muss: diese Bahn traegt NICHTS mehr "
             "zum freien Rest bei. Der dynamische Vorrat wird dadurch kleiner. "
             "Zweite Bahn Cloudflare, damit das Retrieval nicht steht, wenn "
             "NVIDIA 429 gibt. claude_pro entfaellt: keine Vektoren.")),

    dict(prozess="umsortieren_treffer",
         bahn_erst="cloudflare_workers_ai",
         bahn_zweit="nvidia_nim",
         bahn_dritt="claude_pro",
         hoechstanteil=0.20, max_je_lauf=50, schema_pflicht=0,
         begruendung=(
             "Vorschlag bestaetigt: bge-reranker-base ist der einzige freie "
             "Umsortierer, den wir haben, GEMESSEN 2026-08-15 HTTP 200 mit "
             "brauchbaren Rangwerten. Zweite Bahn NVIDIA, weil Umsortierung "
             "ausdruecklich Kognition ist -- ob NIM einen Umsortierer im "
             "Freitier fuehrt, ist UNGEPRUEFT. Dritte Bahn claude_pro: eine "
             "Trefferliste kann ein Sprachmodell notfalls selbst ordnen, das "
             "ist teuer, aber es geht -- anders als bei der Einbettung.")),

    dict(prozess="sphaere_einordnung",
         bahn_erst="groq_llama31_8b",
         bahn_zweit="gemini_flash_lite_latest",
         bahn_dritt="claude_pro",
         hoechstanteil=0.40, max_je_lauf=200, schema_pflicht=1,
         begruendung=(
             "Vorschlag bestaetigt. GEMESSEN live: 14.400 Anfragen/Tag je "
             "Topf, zwei Toepfe = 28.800/Tag. Das groesste freie "
             "Tageskontingent im Haus. Anteil 0,40 = 11.520 Anfragen/Tag. "
             "⚠️ ARITHMETIK, DIE DER EIGNER SEHEN MUSS: 11.859 Artikel ohne "
             "Sphaere (gemessen: SELECT count(*) FROM artikel ohne Eintrag in "
             "artikel_sphaere). 11.859 / 11.520 = 1,03 -- es passt knapp NICHT "
             "in einen Tag, es braucht zwei Kalendertage. Mehr Anteil bekommt "
             "der Prozess dafuer nicht. "
             "⚠️ Zweite, haertere Grenze: das dokumentierte TPD von 500.000 je "
             "Topf (= 1.000.000) taucht in KEINER Kopfzeile auf, ist also "
             "ungeprueft. Waere es echt, waeren bei Anteil 0,40 nur 400.000 "
             "Token/Tag verfuegbar; bei rund 290 Token je Einordnung (Titel + "
             "300 Zeichen Ausschnitt, gerechnet mit gemessenen 1,787 Zeichen "
             "je Token auf unserem Bestand) sind das 1.379 Artikel/Tag = 8,6 "
             "Tage. Dann bindet das TPD, nicht das RPD. Deshalb: Ausschnitt "
             "kurz halten und beim Lauf beobachten, ob nach etwa 500.000 "
             "Token je Topf ein 429 kommt. Die Zahl lernen, nicht raten. "
             "⚠️ Dritte Grenze, die frueher bindet als beide: TPM 6.000 je "
             "Topf. Bei 290 Token je Anfrage sind das 20 Anfragen/min je Topf "
             "= 40/min = 57.600/Tag -- reicht, aber bei laengeren Ausschnitten "
             "(1.500 Zeichen = 840 Token) nur noch 7 Anfragen/min je Topf. "
             "Zweite Bahn Gemini NUR ueber den -latest-Alias: feste Gemini-IDs "
             "wurden am 2026-08-15 ohne Vorwarnung mit 404 abgeschaltet, "
             "derselbe Fehler hat am selben Tag die OpenRouter-Bahn gekostet. "
             "schema_pflicht=1: die Antwort muss genau EIN Sphaerenwort sein, "
             "bahn.py::pruefe_sphaere verwirft alles andere.")),

    dict(prozess="schema_antwort",
         bahn_erst="groq_gptoss_20b",
         bahn_zweit="mistral_small",
         bahn_dritt="claude_pro",
         hoechstanteil=0.50, max_je_lauf=50, schema_pflicht=1,
         begruendung=(
             "Vorschlag bestaetigt. gpt-oss-20b mit json_schema und strict=true, "
             "Groq sichert 100 % Schematreue zu. GEMESSEN live: 1.000 "
             "Anfragen/Tag, TPM 8.000 -- viel kleiner als die 8b-Bahn, deshalb "
             "sparsam einsetzen: Anteil 0,50 = 500 Anfragen/Tag. "
             "Zweite Bahn Mistral, weil es dort echtes json_schema gibt und "
             "eine ANDERE Modellfamilie ist. Dritte Bahn claude_pro.")),

    dict(prozess="kondensieren",
         bahn_erst="groq_llama31_8b",
         bahn_zweit="mistral_small",
         bahn_dritt="claude_pro",
         hoechstanteil=0.20, max_je_lauf=100, schema_pflicht=0,
         begruendung=(
             "Zusammenfassen ist Massenarbeit und gehoert damit ausdruecklich "
             "NICHT auf die NVIDIA-Bahn (Eigner-Entscheidung). Anteil 0,20 = "
             "5.760 Anfragen/Tag auf der 8b-Bahn. "
             "Zusammen mit sphaere_einordnung (0,40) sind auf dieser Bahn 0,60 "
             "verplant -- 0,40 = 11.520 Anfragen/Tag bleiben freier Rest, "
             "deutlich ueber den geforderten 25 %.")),

    dict(prozess="langer_kontext",
         bahn_erst="gemini_flash_latest",
         bahn_zweit="claude_pro",
         bahn_dritt=None,
         hoechstanteil=0.40, max_je_lauf=5, schema_pflicht=0,
         begruendung=(
             "Vorschlag bestaetigt: 1.048.576 Token Kontext ist das einzige "
             "freie Millionenfenster. DeepSeek haette auch 1M, ist aber "
             "konto_leer (402, Guthaben -0,01). "
             "⚠️ Der hoechstanteil von 0,40 ist heute wirkungslos, weil Google "
             "die Freitier-Grenzen nicht mehr veroeffentlicht -- es gibt keine "
             "Zahl, von der 40 % genommen werden koennten. Er steht trotzdem "
             "drin, damit er greift, sobald die Bahn ihre echte Decke aus "
             "beobachteten 429 gelernt hat. "
             "Nur der -latest-Alias. Zweite und letzte Bahn ist claude_pro.")),

    dict(prozess="zweitmeinung",
         bahn_erst="mistral_small",
         bahn_zweit="groq_gptoss_120b",
         bahn_dritt="claude_pro",
         hoechstanteil=0.30, max_je_lauf=20, schema_pflicht=0,
         begruendung=(
             "Vorschlag bestaetigt. Der Sinn einer Gegenpruefung ist die andere "
             "Modellfamilie -- Groq gegen Groq ist keine Zweitmeinung. Deshalb "
             "Mistral zuerst, gpt-oss als zweite Familie, claude_pro als "
             "dritte. Anteil 0,30 ist heute rechnerisch wirkungslos: Mistral "
             "veroeffentlicht seine Freimodus-Grenzen nicht.")),

    dict(prozess="websuche_erdung",
         bahn_erst="groq_compound",
         bahn_zweit="claude_pro",
         bahn_dritt=None,
         hoechstanteil=0.60, max_je_lauf=10, schema_pflicht=0,
         begruendung=(
             "Einziger freier Weg zu geerdeter Websuche: Gemini kann Erdung "
             "auch, verlangt aber Geld je Suchanfrage, und Mistrals Websuche "
             "kostet 30 $ je 1000 Aufrufe. Nur 250 Anfragen/Tag, Anteil 0,60 = "
             "150/Tag, 100/Tag bleiben freier Rest. Ob claude_pro als zweite "
             "Bahn wirklich im Netz suchen kann, ist in dieser Verdrahtung "
             "UNGEPRUEFT.")),

    dict(prozess="transkription",
         bahn_erst="groq_whisper_v3",
         bahn_zweit=None,
         bahn_dritt=None,
         hoechstanteil=0.70, max_je_lauf=20, schema_pflicht=0,
         begruendung=(
             "Einzige freie Audiobahn: 2.000 Anfragen/Tag, 20/min. "
             "⚠️ ES GIBT KEINEN RUECKFALL. claude_pro nimmt kein Audio "
             "entgegen -- die Regel 'letzte Bahn ist immer claude_pro' gilt "
             "hier nicht, und so zu tun als gaelte sie waere die gefaehrlichere "
             "Antwort. Was hier durchfaellt, wird kb_auftrag mit Zustand "
             "unbedienbar und wartet, bis whisper wieder traegt.")),

    dict(prozess="rueckfall_allgemein",
         bahn_erst="claude_pro",
         bahn_zweit=None,
         bahn_dritt=None,
         hoechstanteil=0.99, max_je_lauf=10, schema_pflicht=0,
         begruendung=(
             "Alles, was durch jede freie Bahn faellt und Text ist. Dies ist "
             "der einzige Prozess, dessen ERSTE Bahn claude_pro sein darf -- "
             "er IST der Rueckfall. Kostet Gabriels Kontingent, deshalb "
             "max_je_lauf klein. hoechstanteil 0,99, weil claude_pro kein "
             "gefuehrtes Tageslimit hat: es gibt nichts zu teilen, aber ein "
             "Prozent bleibt formal offen, damit die Regel 'nie 100 %' auch "
             "hier sichtbar ist.")),
]


# ── SCHREIBEN ──────────────────────────────────────────────────────────

ZUGANG_SPALTEN = [
    "zugang", "anzeige", "einheit", "minute_limit", "tag_limit",
    "tageswechsel_stunde", "geteilt_mit", "besonderheit", "modell",
    "token_minute_limit", "token_tag_limit", "zustand", "zustand_grund",
    "zustand_gemessen", "grenzen_quelle", "unbekannt_felder",
    "unbekannt_grund", "kann_embedding", "kann_schema", "kann_batch",
    "ausgereizt", "konten_anzahl", "konten_getrennt", "schluessel_namen",
    "angelegt",
]


def pruefe_katalog() -> list[str]:
    """Vor dem ersten Schreibzugriff. Findet Tippfehler, keine Meinungen."""
    fehler = []
    bekannt = {z["zugang"] for z in ZUGAENGE_NEU} | {a[0] for a in ALT_VERMERK}
    for z in ZUGAENGE_NEU:
        if z["zustand"] not in ZUSTAENDE:
            fehler.append(f"{z['zugang']}: zustand {z['zustand']!r} unbekannt")
        # Ein Feld darf nur dann als unbekannt gelten, wenn es auch NULL ist.
        for f in z.get("unbekannt_felder") or []:
            if z.get(f) is not None:
                fehler.append(f"{z['zugang']}: {f} steht in unbekannt_felder, "
                              f"hat aber den Wert {z.get(f)!r}")
        if (z.get("unbekannt_felder") or []) and not z.get("unbekannt_grund"):
            fehler.append(f"{z['zugang']}: unbekannt_felder ohne unbekannt_grund")
    # ⚠️ Die letzte Bahn heisst hier claude_pro, nicht "claude_code".
    # bahn.py fuehrt eine Bahn NAMENS claude_code, die auf den ZUGANG
    # claude_pro bucht. kb_verdrahtung zeigt auf den ZUGANG -- sonst findet
    # die Buchung ihre Zeile in kb_zugang nicht.
    for v in VERDRAHTUNG:
        for feld in ("bahn_erst", "bahn_zweit", "bahn_dritt"):
            b = v.get(feld)
            if b and b not in bekannt:
                fehler.append(f"{v['prozess']}: {feld}={b!r} ist keine bekannte Bahn")
        if not v["begruendung"].strip():
            fehler.append(f"{v['prozess']}: begruendung leer")
        if v["prozess"] != "rueckfall_allgemein" and v["bahn_erst"] == "claude_pro":
            fehler.append(f"{v['prozess']}: claude_pro ist Rueckfall, nie erste Bahn")
    return fehler


def pruefe_anteile(con) -> tuple[list[str], dict]:
    """Summe der hoechstanteil je ERSTER Bahn. Muss unter 1.0 bleiben --
    ausser die Bahn ist als ausgereizt markiert (Eigner-Ausnahme, per Flag,
    NICHT per Name, damit die Regel lesbar bleibt)."""
    summe: dict[str, float] = {}
    for v in VERDRAHTUNG:
        b = v["bahn_erst"]
        summe[b] = round(summe.get(b, 0.0) + float(v["hoechstanteil"]), 6)
    ausgereizt = {r["zugang"] for r in
                  con.execute("SELECT zugang FROM kb_zugang WHERE ausgereizt=1")}
    ausgereizt |= {z["zugang"] for z in ZUGAENGE_NEU if z.get("ausgereizt")}
    fehler = []
    for b, s in sorted(summe.items()):
        if b in ausgereizt:
            if s > 1.0:
                fehler.append(f"Bahn {b}: Summe {s} ueber 1.0 -- auch eine "
                              f"ausgereizte Bahn hat nur einen Topf")
            continue
        if s >= 1.0:
            fehler.append(f"Bahn {b}: Summe der hoechstanteil = {s} >= 1.0. "
                          f"Kein freier Rest. Schreiben verweigert -- es wird "
                          f"NICHT still normiert.")
    return fehler, summe


def cmd_init(a) -> None:
    con = verbinden()
    schema(con)
    fehler = pruefe_katalog()
    if fehler:
        for f in fehler:
            print("KATALOGFEHLER:", f)
        sys.exit(1)
    anteil_fehler, summe = pruefe_anteile(con)
    if anteil_fehler:
        for f in anteil_fehler:
            print("ANTEILSFEHLER:", f)
        sys.exit(1)

    t = jetzt()
    setz = ", ".join(f"{s}=excluded.{s}" for s in ZUGANG_SPALTEN
                     if s not in ("zugang", "angelegt"))
    sql = (f"INSERT INTO kb_zugang ({', '.join(ZUGANG_SPALTEN)}) "
           f"VALUES ({', '.join('?' * len(ZUGANG_SPALTEN))}) "
           f"ON CONFLICT(zugang) DO UPDATE SET {setz}")
    for z in ZUGAENGE_NEU:
        werte = []
        for s in ZUGANG_SPALTEN:
            if s == "angelegt":
                werte.append(t)
            elif s == "zustand_gemessen":
                werte.append(t)
            elif s == "unbekannt_felder":
                werte.append(json.dumps(z.get("unbekannt_felder") or []))
            elif s == "ausgereizt":
                werte.append(int(z.get("ausgereizt") or 0))
            else:
                werte.append(z.get(s))
        con.execute(sql, werte)

    # Alte Sammelzeilen: NUR die neuen Spalten. Siehe Warnung bei ALT_VERMERK.
    for zugang, zustand, grund in ALT_VERMERK:
        if zustand not in ZUSTAENDE:
            sys.exit(f"ALT_VERMERK {zugang}: zustand {zustand!r} unbekannt")
        r = con.execute("UPDATE kb_zugang SET zustand=?, zustand_grund=?, "
                        "zustand_gemessen=? WHERE zugang=?",
                        (zustand, grund, t, zugang))
        if r.rowcount == 0:
            print(f"HINWEIS: Sammelzeile {zugang} gibt es nicht (mehr).")

    # Konto fuer den freien Rest. vorrang 1: es darf nicht alles nehmen, aber
    # es ist sichtbar und messbar. Eine Reserve, die niemand sehen kann, wird
    # gegessen.
    con.execute("""
        INSERT INTO kb_konto (konto, anzeige, vorrang, hat_eigenes_limit,
            eigenes_limit_wert, eigenes_limit_einheit, eigenes_limit_fenster,
            warnung_an, wirt, angelegt)
        VALUES (?,?,?,?,?,?,?,?,?,?)
        ON CONFLICT(konto) DO UPDATE SET
            anzeige=excluded.anzeige, vorrang=excluded.vorrang,
            hat_eigenes_limit=excluded.hat_eigenes_limit,
            warnung_an=excluded.warnung_an
    """, (KONTO_FREI, "freier Rest (alles Unverdrahtete)", 1, 1, None, None,
          "tag", "gabriel", "clayverse", t))

    vspalten = ["prozess", "bahn_erst", "bahn_zweit", "bahn_dritt",
                "hoechstanteil", "begruendung", "max_je_lauf",
                "schema_pflicht", "angelegt"]
    vsetz = ", ".join(f"{s}=excluded.{s}" for s in vspalten
                      if s not in ("prozess", "angelegt"))
    vsql = (f"INSERT INTO kb_verdrahtung ({', '.join(vspalten)}) "
            f"VALUES ({', '.join('?' * len(vspalten))}) "
            f"ON CONFLICT(prozess) DO UPDATE SET {vsetz}")
    for v in VERDRAHTUNG:
        con.execute(vsql, (v["prozess"], v.get("bahn_erst"), v.get("bahn_zweit"),
                           v.get("bahn_dritt"), float(v["hoechstanteil"]),
                           v["begruendung"], v.get("max_je_lauf"),
                           v.get("schema_pflicht"), t))
    con.commit()
    print(f"kb_zugang: {len(ZUGAENGE_NEU)} konkrete Bahnen, "
          f"{len(ALT_VERMERK)} Sammelzeilen vermerkt")
    print(f"kb_verdrahtung: {len(VERDRAHTUNG)} Prozesse")
    print("Anteile je erster Bahn (freier Rest in Klammern):")
    aus = {z["zugang"] for z in ZUGAENGE_NEU if z.get("ausgereizt")}
    for b, s in sorted(summe.items()):
        marke = "  AUSGEREIZT (Eigner)" if b in aus else ""
        print(f"  {b:26s} verplant {s:.2f}  (frei {1.0 - s:.2f}){marke}")


# ── BAHNENWAHL: keine Kette, sondern was gerade traegt ──────────────────

def cmd_bahnen(a) -> None:
    con = verbinden(readonly=True)
    v = con.execute("SELECT * FROM kb_verdrahtung WHERE prozess=?",
                    (a.prozess,)).fetchone()
    if not v:
        sys.exit(f"Unbekannter Prozess: {a.prozess!r}")
    print(f"{a.prozess}  (hoechstanteil {v['hoechstanteil']}, "
          f"max_je_lauf {v['max_je_lauf']}, schema_pflicht {v['schema_pflicht']})")
    for feld in ("bahn_erst", "bahn_zweit", "bahn_dritt"):
        b = v[feld]
        if not b:
            print(f"  {feld:11s} -")
            continue
        z = con.execute("SELECT zustand, zustand_grund FROM kb_zugang "
                        "WHERE zugang=?", (b,)).fetchone()
        zu = z["zustand"] if z else "FEHLT"
        marke = "TRAEGT" if zu == "nutzbar" else f"uebergangen ({zu})"
        print(f"  {feld:11s} {b:26s} {marke}")
    print("Begruendung:", v["begruendung"])


# ── AUFTRAEGE: nie verloren, hoechstens unbedient ───────────────────────

def cmd_auftrag_neu(a) -> None:
    con = verbinden()
    schema(con)
    if not con.execute("SELECT 1 FROM kb_verdrahtung WHERE prozess=?",
                       (a.prozess,)).fetchone():
        sys.exit(f"Unbekannter Prozess: {a.prozess!r}")
    t = jetzt()
    cur = con.execute("INSERT INTO kb_auftrag (prozess, nutzlast, zustand, "
                      "versuche, letzter_grund, gesperrte_bahnen, angelegt, "
                      "geaendert) VALUES (?,?,?,?,?,?,?,?)",
                      (a.prozess, a.nutzlast, "offen", 0, None,
                       json.dumps([]), t, t))
    con.commit()
    print(f"auftrag {cur.lastrowid} angelegt ({a.prozess})")


def cmd_auftrag_nehmen(a) -> None:
    """Nimmt einen offenen Auftrag. Wer eine Bahn nennt, bekommt nur, was
    diese Bahn nicht schon abgewiesen hat -- so kann jede gesunde Bahn
    liegengebliebene Arbeit aufnehmen, statt dass eine feste Kette blockiert."""
    con = verbinden()
    schema(con)
    bed = "zustand='offen'"
    par: list = []
    if a.prozess:
        bed += " AND prozess=?"
        par.append(a.prozess)
    zeilen = con.execute(f"SELECT * FROM kb_auftrag WHERE {bed} "
                         f"ORDER BY versuche, id LIMIT 50", par).fetchall()
    for r in zeilen:
        gesperrt = json.loads(r["gesperrte_bahnen"] or "[]")
        if a.bahn and a.bahn in gesperrt:
            continue
        t = jetzt()
        con.execute("UPDATE kb_auftrag SET zustand='laeuft', versuche=versuche+1, "
                    "geaendert=? WHERE id=? AND zustand='offen'", (t, r["id"]))
        con.commit()
        print(json.dumps({"id": r["id"], "prozess": r["prozess"],
                          "nutzlast": r["nutzlast"],
                          "versuche": r["versuche"] + 1}, ensure_ascii=False))
        return
    print("nichts offen")


def cmd_auftrag_fertig(a) -> None:
    con = verbinden()
    schema(con)
    con.execute("UPDATE kb_auftrag SET zustand='fertig', letzter_grund=?, "
                "geaendert=? WHERE id=?", (a.grund, jetzt(), a.id))
    con.commit()
    print(f"auftrag {a.id} fertig")


def cmd_auftrag_unbedienbar(a) -> None:
    """Ein Auftrag ist nie verloren. 'unbedienbar' heisst: heute traegt ihn
    keine Bahn -- mit Grund, und mit der Bahn, die abgewiesen hat."""
    con = verbinden()
    schema(con)
    if not (a.grund or "").strip():
        sys.exit("unbedienbar ohne Grund ist verboten.")
    r = con.execute("SELECT gesperrte_bahnen FROM kb_auftrag WHERE id=?",
                    (a.id,)).fetchone()
    if not r:
        sys.exit(f"kein auftrag {a.id}")
    g = json.loads(r["gesperrte_bahnen"] or "[]")
    if a.bahn and a.bahn not in g:
        g.append(a.bahn)
    con.execute("UPDATE kb_auftrag SET zustand='unbedienbar', letzter_grund=?, "
                "gesperrte_bahnen=?, geaendert=? WHERE id=?",
                (a.grund.strip(), json.dumps(g), jetzt(), a.id))
    con.commit()
    print(f"auftrag {a.id} unbedienbar: {a.grund.strip()}")


def cmd_wiederbeleben(a) -> None:
    """Eine Bahn ist wieder gesund -> alles Unbediente, das NICHT genau an
    dieser Bahn gescheitert ist, darf es wieder versuchen. Damit ist die
    Verdrahtung keine Kette: ein Auftrag haengt an keiner bestimmten Bahn."""
    con = verbinden()
    schema(con)
    zeilen = con.execute("SELECT id, gesperrte_bahnen FROM kb_auftrag "
                         "WHERE zustand='unbedienbar'").fetchall()
    t = jetzt()
    n = 0
    for r in zeilen:
        g = json.loads(r["gesperrte_bahnen"] or "[]")
        if a.bahn and a.bahn in g:
            continue
        con.execute("UPDATE kb_auftrag SET zustand='offen', letzter_grund=?, "
                    "geaendert=? WHERE id=?",
                    (f"wiederbelebt: {a.grund}", t, r["id"]))
        n += 1
    con.commit()
    print(f"{n} Auftraege wieder offen (Bahn {a.bahn or 'beliebig'}): {a.grund}")


# ── ANZEIGEN ───────────────────────────────────────────────────────────

def cmd_zeigen(a) -> None:
    con = verbinden(readonly=True)
    if a.was in ("zugang", "alles"):
        print("== kb_zugang ==========================================")
        print(f"{'zugang':26s} {'zust':14s} {'RPM':>7s} {'RPD':>8s} "
              f"{'TPM':>9s} {'TPD':>9s}  unbekannt")
        for r in con.execute("SELECT * FROM kb_zugang ORDER BY zustand, zugang"):
            def f(v):
                return "-" if v is None else (f"{v:.0f}" if v == int(v) else str(v))
            unb = json.loads(r["unbekannt_felder"] or "[]") if "unbekannt_felder" \
                in r.keys() else []
            kurz = {"minute_limit": "RPM", "tag_limit": "RPD",
                    "token_minute_limit": "TPM", "token_tag_limit": "TPD"}
            u = ",".join(kurz.get(x, x) for x in unb) or "-"
            print(f"{r['zugang']:26s} {str(r['zustand'])[:14]:14s} "
                  f"{f(r['minute_limit']):>7s} {f(r['tag_limit']):>8s} "
                  f"{f(r['token_minute_limit']):>9s} "
                  f"{f(r['token_tag_limit']):>9s}  {u}")
    if a.was in ("verdrahtung", "alles"):
        print("\n== kb_verdrahtung =====================================")
        for r in con.execute("SELECT * FROM kb_verdrahtung ORDER BY prozess"):
            print(f"{r['prozess']:22s} {str(r['bahn_erst']):26s} -> "
                  f"{str(r['bahn_zweit'] or '-'):26s} -> "
                  f"{str(r['bahn_dritt'] or '-'):14s} "
                  f"anteil {r['hoechstanteil']:.2f} "
                  f"max {r['max_je_lauf']} schema {r['schema_pflicht']}")
    if a.was in ("auftrag", "alles"):
        print("\n== kb_auftrag =========================================")
        for r in con.execute("SELECT zustand, count(*) n FROM kb_auftrag "
                             "GROUP BY zustand"):
            print(f"  {r['zustand']:14s} {r['n']}")


def cmd_probe(a) -> None:
    """MESSUNG statt Behauptung: welche der beiden Bremsen bindet wirklich?

    Fragt fuer denselben Prozess und dieselbe Bahn einmal das Kontingentbuch
    (Vorrang-Achse) und rechnet einmal den hoechstanteil (Prozess-Achse) aus.
    Beides wird angezeigt, und die kleinere Zahl ist die, die gilt.
    """
    import subprocess
    con = verbinden(readonly=True)
    v = con.execute("SELECT * FROM kb_verdrahtung WHERE prozess=?",
                    (a.prozess,)).fetchone()
    if not v:
        sys.exit(f"Unbekannter Prozess: {a.prozess!r}")
    bahn = v["bahn_erst"]
    z = con.execute("SELECT tag_limit, ausgereizt FROM kb_zugang WHERE zugang=?",
                    (bahn,)).fetchone()
    if not z or z["tag_limit"] is None:
        print(f"{a.prozess}: Bahn {bahn} fuehrt kein tag_limit -- der "
              f"hoechstanteil {v['hoechstanteil']} hat heute nichts, wovon er "
              f"einen Anteil nehmen koennte. UNBEKANNT, nicht null.")
        return
    tag = float(z["tag_limit"])
    prozess_decke = tag * float(v["hoechstanteil"])
    verbraucht = con.execute(
        "SELECT COALESCE(SUM(menge),0) s FROM kb_buchung "
        "WHERE zugang=? AND zweck=?", (bahn, a.prozess)).fetchone()["s"]
    prozess_rest = max(0.0, prozess_decke - verbraucht)

    r = subprocess.run(["python3", "/opt/clayverse/werkzeug/kontingent.py",
                        "darf", "--konto", a.konto, "--zugang", bahn,
                        "--menge", str(int(tag))],
                       capture_output=True, text=True, timeout=60)
    buch = (r.stdout or r.stderr).strip().splitlines()
    vorrang_rest = None
    binder = "?"
    tag_decke = None
    for zeile in buch:
        teile = zeile.split()
        if teile and teile[0].replace(".", "", 1).isdigit() and "erlaubt" in zeile:
            vorrang_rest = float(teile[0])
        if zeile.startswith("gebunden durch:"):
            binder = zeile.split(":", 1)[1].strip()
        if "zugang.tag.reserviert" in zeile:
            try:
                tag_decke = float(zeile.split("'rest_unter_decke':")[1]
                                  .split("}")[0].strip())
            except Exception:
                pass
    print(f"Prozess     {a.prozess}")
    print(f"Bahn        {bahn}  tag_limit {tag:.0f}"
          f"{'  AUSGEREIZT' if z['ausgereizt'] else ''}")
    print(f"Konto       {a.konto}")
    print(f"  Prozess-Achse (hoechstanteil {v['hoechstanteil']:.2f}): "
          f"Decke {prozess_decke:.0f}, verbraucht {verbraucht:.0f}, "
          f"Rest {prozess_rest:.0f}")
    if vorrang_rest is None:
        print("  Vorrang-Achse : Kontingentbuch gab keine Zahl zurueck:")
        for zeile in buch[:6]:
            print("     ", zeile)
        return
    print(f"  Vorrang-Achse (kontingent.py darf): Rest {vorrang_rest:.0f}, "
          f"gebunden durch {binder}")
    if tag_decke is not None:
        print(f"  ... davon auf TAGES-Ebene (vergleichbar zum hoechstanteil): "
              f"Rest {tag_decke:.0f}")
        bindet = "Prozess-Achse (hoechstanteil)" if prozess_rest <= tag_decke \
            else "Vorrang-Achse (RESERVE_JE_VORRANG)"
        print(f"  TAGESVERGLEICH: min = {min(prozess_rest, tag_decke):.0f} "
              f"-- es bindet die {bindet}")
    print(f"  ES GILT FUER DIESEN AUFRUF: {min(prozess_rest, vorrang_rest):.0f} "
          f"-- kleinste aller Bremsen")


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    s = p.add_subparsers(dest="cmd", required=True)

    s.add_parser("init").set_defaults(fn=cmd_init)

    z = s.add_parser("zeigen")
    z.add_argument("was", nargs="?", default="alles",
                   choices=["zugang", "verdrahtung", "auftrag", "alles"])
    z.set_defaults(fn=cmd_zeigen)

    b = s.add_parser("bahnen")
    b.add_argument("prozess")
    b.set_defaults(fn=cmd_bahnen)

    an = s.add_parser("auftrag-neu")
    an.add_argument("--prozess", required=True)
    an.add_argument("--nutzlast", required=True)
    an.set_defaults(fn=cmd_auftrag_neu)

    ah = s.add_parser("auftrag-nehmen")
    ah.add_argument("--prozess")
    ah.add_argument("--bahn")
    ah.set_defaults(fn=cmd_auftrag_nehmen)

    af = s.add_parser("auftrag-fertig")
    af.add_argument("--id", type=int, required=True)
    af.add_argument("--grund", default="ok")
    af.set_defaults(fn=cmd_auftrag_fertig)

    au = s.add_parser("auftrag-unbedienbar")
    au.add_argument("--id", type=int, required=True)
    au.add_argument("--grund", required=True)
    au.add_argument("--bahn")
    au.set_defaults(fn=cmd_auftrag_unbedienbar)

    pr = s.add_parser("probe")
    pr.add_argument("prozess")
    pr.add_argument("--konto", default="clayverse")
    pr.set_defaults(fn=cmd_probe)

    aw = s.add_parser("wiederbeleben")
    aw.add_argument("--bahn")
    aw.add_argument("--grund", required=True)
    aw.set_defaults(fn=cmd_wiederbeleben)

    a = p.parse_args()
    a.fn(a)
    return 0


if __name__ == "__main__":
    sys.exit(main())
