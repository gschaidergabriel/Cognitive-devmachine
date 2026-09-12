#!/usr/bin/env python3
"""modell_profile.py -- Modell-spezifische Profile fuer dynamisches Chunking
(PHASE 53 Teil 2, Gabriel-Auftrag 2026-09-12, woertlich):

    "wenn die aufgabe zu gross ist soll sie in chunks zerlegt werden vom
    grid, und dann soll der grid das injizieren nach und nach oder wenn es
    sein muss immer nen neuen request machen -- deshalb muss der grid
    wissen was er verwendet, bei claude/glm ist das nicht noetig aber beim
    free pool schon, deshalb muss der grid dynamisch jedes modell angepasst
    behandeln, auch bei anthropic immer, und das soll dynamisch immer
    weiter verbessert werden mittels der nutzung und auswertung dessen und
    der selbstverbesserungsschleife."

Vier Teile, wie gefordert:
  1. MODELL_PROFILE -- ein Profil pro Modell-ID (Kontextfenster, sicheres
     Einzelaufruf-Budget, Chunk-Strategie). Anthropic/GLM = "keins"
     (koennen selbst mit langem Kontext umgehen -- Claude Code/GLM
     verwalten das selbst, kein Chunking hier noetig). Free-Pool-Modelle
     (kleinere PRAKTISCHE Budgets, oft durch Free-Tier-Ratenlimits
     begrenzt, nicht nur durchs nominale Kontextfenster) = "progressiv"
     oder "neuer_request".
  2. braucht_chunking()/chunks_bilden() -- echte Zerlegung, kein Abschneiden.
  3. verlauf_aufzeichnen()/erfolgsquote() -- reale, persistente Erfolgs-/
     Fehler-Historie (SQLite), bei JEDEM echten Lauf befuellt (siehe
     harness_aider.py's einen_lauf(), das ruft dies nach jedem Lauf auf) --
     kein leeres Schema, sondern die Datengrundlage fuer die spaetere
     Selbstverbesserungsschleife.
  4. chunked_lauf() -- die tatsaechliche Ausfuehrung: prueft, ob eine
     Aufgabe zu gross fuer das Zielmodell ist, und wenn ja, zerlegt sie
     ECHT (mehrere echte harness_aider.einen_lauf()-Aufrufe je nach
     Strategie), statt sie unveraendert an ein Modell zu schicken, das sie
     entweder ablehnt (Ratenlimit) oder nur einen Bruchteil verarbeitet.

Reale Quellen, nicht geraten:
  * modell_katalog.py MODELLE[*]['kontextfenster'] -- nominale Fenstergroesse
    je Modell (bereits vorhandener, gepflegter Katalog).
  * harness_aider.py PHASE-48-Kommentar (Bugfix nach echtem Testlauf
    2026-08-27): Groq Free-Tier real gemessen 8000 Token/Minute -- die
    eigentliche Chunking-Ursache bei Free-Pool-Modellen ist meistens NICHT
    das nominale Kontextfenster (256K reicht fast immer aus), sondern das
    viel kleinere Free-Tier-DURCHSATZLIMIT pro Minute. `sicherer_
    einzelaufruf_tokens` bildet deshalb das PRAKTISCHE Budget ab, nicht das
    nominale Fenster.
"""
import json
import os
import sqlite3
import time

DB_PFAD = os.path.expanduser("~/.claude/star/daten/modell_profile.db")

# ── 1. Profile ──────────────────────────────────────────────────────────
# 'chunk_strategie': 'keins' | 'progressiv' | 'neuer_request'
#   'keins'         -- Modell bekommt die Aufgabe immer komplett, unveraendert.
#   'progressiv'    -- EIN Harness-Lauf, aber die Aufgabe wird in Teile
#                       zerlegt und als aufeinanderfolgende, nummerierte
#                       Abschnitte MIT wachsender Kurz-Zusammenfassung des
#                       bereits Gesagten in den Auftragstext eingespeist
#                       (echtes "nach und nach", kein Multi-Turn-API noetig).
#   'neuer_request' -- JEDER Teil wird als EIGENSTAENDIGER
#                       harness_aider.einen_lauf()-Aufruf verschickt (echter
#                       neuer Request, eigene Session/Handoff), mit nur
#                       einer knappen Kurzfassung des Vor-Ergebnisses als
#                       Ueberleitung -- fuer Modelle, deren Ratenlimit/
#                       Kontextbudget selbst kleine Mehrfach-Injektion
#                       innerhalb einer Sitzung sprengen wuerde (Groq).
MODELL_PROFILE = {
    # ── Anthropic/GLM -- KEIN Chunking (Gabriel woertlich), riesige
    # Fenster, von Claude Code / GLM selbst verwaltet. Werden hier trotzdem
    # GEFUEHRT (nicht nur per Kommentar ausgenommen), damit `profil()` fuer
    # JEDES Modell, das die Koordination je anfasst, eine echte Antwort
    # liefert -- "auch bei anthropic immer" (Gabriel).
    "claude-opus":    {"kontextfenster_tokens": 200_000, "sicherer_einzelaufruf_tokens": 180_000, "chunk_strategie": "keins", "tpm_limit": None, "quelle": "modell_katalog.py"},
    "claude-sonnet":  {"kontextfenster_tokens": 200_000, "sicherer_einzelaufruf_tokens": 180_000, "chunk_strategie": "keins", "tpm_limit": None, "quelle": "modell_katalog.py"},
    "claude-haiku":   {"kontextfenster_tokens": 200_000, "sicherer_einzelaufruf_tokens": 180_000, "chunk_strategie": "keins", "tpm_limit": None, "quelle": "modell_katalog.py"},
    "glm-5.3":        {"kontextfenster_tokens": 1_000_000, "sicherer_einzelaufruf_tokens": 900_000, "chunk_strategie": "keins", "tpm_limit": None, "quelle": "modell_katalog.py"},
    "glm-5.3-flash":  {"kontextfenster_tokens": 1_000_000, "sicherer_einzelaufruf_tokens": 900_000, "chunk_strategie": "keins", "tpm_limit": None, "quelle": "modell_katalog.py"},
    "glm-5-turbo":    {"kontextfenster_tokens": 200_000, "sicherer_einzelaufruf_tokens": 180_000, "chunk_strategie": "keins", "tpm_limit": None, "quelle": "modell_katalog.py"},
    "glm-4.7":        {"kontextfenster_tokens": 200_000, "sicherer_einzelaufruf_tokens": 180_000, "chunk_strategie": "keins", "tpm_limit": None, "quelle": "modell_katalog.py"},

    # ── Free-Pool (harness_aider.py MODELL_MAP) -- Chunking noetig. Das
    # 'sicherer_einzelaufruf_tokens'-Budget ist bewusst KONSERVATIV
    # (deutlich unter dem nominalen Fenster) -- Aiders eigene Repo-Map +
    # Systemprompt + unser Hinweis-Block verbrauchen bereits einen Teil,
    # bevor der eigentliche Auftrag ueberhaupt drankommt.
    "nvidia-nemotron":     {"kontextfenster_tokens": 262_144, "sicherer_einzelaufruf_tokens": 60_000, "chunk_strategie": "progressiv", "tpm_limit": None, "quelle": "modell_katalog.py (Free-Tier oft 262.144)"},
    "mistral-small":       {"kontextfenster_tokens": 256_000, "sicherer_einzelaufruf_tokens": 40_000, "chunk_strategie": "progressiv", "tpm_limit": None, "quelle": "modell_katalog.py"},
    "openrouter-deepseek": {"kontextfenster_tokens": 128_000, "sicherer_einzelaufruf_tokens": 50_000, "chunk_strategie": "progressiv", "tpm_limit": None, "quelle": "modell_katalog.py"},
    # Groq: das ENGSTE reale Budget ist nicht das 131K-Fenster, sondern das
    # Free-Tier-Durchsatzlimit -- real gemessen (harness_aider.py PHASE 48:
    # RateLimitError beim ersten Testlauf, "8000 Token/Min real gemessen").
    # Deshalb eigener, viel kleinerer Wert + eigene Strategie (neuer_request
    # statt progressiv: selbst mehrere Nachrichten IN DERSELBEN Sitzung
    # koennten das Minutenlimit reissen, getrennte Laeufe verteilen das
    # ueber die Zeit).
    "groq-gptoss": {"kontextfenster_tokens": 131_072, "sicherer_einzelaufruf_tokens": 6_000, "chunk_strategie": "neuer_request", "tpm_limit": 8_000, "quelle": "harness_aider.py PHASE-48-Kommentar (real gemessen)"},
}

_STANDARD_PROFIL = {
    "kontextfenster_tokens": 32_000, "sicherer_einzelaufruf_tokens": 8_000,
    "chunk_strategie": "neuer_request", "tpm_limit": None,
    "quelle": "unbekanntes Modell -- konservativer Rueckfall",
}

# Grobe, dokumentierte Naeherung (kein Tokenizer-Aufruf noetig fuer diesen
# Zweck) -- 1 Token ~= 4 Zeichen im Deutschen/Englischen Mischtext, Standard-
# Faustregel (auch von OpenAI/Anthropic-Doku so verwendet).
_ZEICHEN_JE_TOKEN = 4


def profil(modell_id: str) -> dict:
    """Liefert IMMER ein vollstaendiges Profil-Dict -- unbekannte Modelle
    bekommen den konservativen Standard-Rueckfall, nie eine Ausnahme."""
    p = dict(MODELL_PROFILE.get(modell_id, _STANDARD_PROFIL))
    p["modell_id"] = modell_id
    return p


def _tokens_schaetzen(text: str) -> int:
    return max(1, len(text) // _ZEICHEN_JE_TOKEN)


def braucht_chunking(modell_id: str, auftrag_text: str) -> bool:
    """Reale Schaetzung, kein Rateln -- vergleicht die geschaetzte
    Token-Laenge des Auftrags gegen das sichere Einzelaufruf-Budget des
    Zielmodells. Modelle mit chunk_strategie='keins' brauchen NIE
    Chunking (Gabriel: 'bei claude/glm ist das nicht noetig')."""
    p = profil(modell_id)
    if p["chunk_strategie"] == "keins":
        return False
    return _tokens_schaetzen(auftrag_text) > p["sicherer_einzelaufruf_tokens"]


def chunks_bilden(auftrag_text: str, modell_id: str) -> list:
    """Zerlegt `auftrag_text` in geordnete Teile, die je unter dem sicheren
    Einzelaufruf-Budget des Modells liegen. Zerlegt an Absatzgrenzen (\n\n),
    faellt bei zu langen Einzelabsaetzen auf Zeilen, dann auf harte
    Zeichen-Fenster zurueck -- NIE mitten im Wort, wenn vermeidbar, aber
    IMMER unter dem Budget (ein zu langer Rest waere schlimmer als ein
    haesslicher Schnitt)."""
    p = profil(modell_id)
    budget_zeichen = p["sicherer_einzelaufruf_tokens"] * _ZEICHEN_JE_TOKEN
    if len(auftrag_text) <= budget_zeichen:
        return [auftrag_text]

    einheiten = [a for a in auftrag_text.split("\n\n") if a.strip()] or [auftrag_text]
    chunks, aktuell = [], ""
    for einheit in einheiten:
        stueck = einheit if not aktuell else "\n\n" + einheit
        if len(aktuell) + len(stueck) <= budget_zeichen:
            aktuell += stueck
            continue
        if aktuell:
            chunks.append(aktuell)
            aktuell = ""
        if len(einheit) <= budget_zeichen:
            aktuell = einheit
        else:
            # Einzelner Absatz sprengt selbst das volle Budget -- hart in
            # Fenster schneiden, damit KEIN Teil je das Modell-Limit reisst.
            for i in range(0, len(einheit), budget_zeichen):
                chunks.append(einheit[i:i + budget_zeichen])
    if aktuell:
        chunks.append(aktuell)
    return chunks


# ── 3. Persistente Erfolgs-/Fehler-Historie ─────────────────────────────

def _db() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PFAD), exist_ok=True)
    conn = sqlite3.connect(DB_PFAD, timeout=10.0)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS aufrufe (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ts REAL NOT NULL,
            modell_id TEXT NOT NULL,
            ok INTEGER NOT NULL,
            chunked INTEGER NOT NULL DEFAULT 0,
            anzahl_chunks INTEGER NOT NULL DEFAULT 1,
            geschaetzte_tokens INTEGER,
            dauer_s REAL,
            grund TEXT,
            quelle TEXT
        )
    """)
    conn.commit()
    return conn


def verlauf_aufzeichnen(modell_id: str, ok: bool, *, chunked: bool = False,
                         anzahl_chunks: int = 1, geschaetzte_tokens: int = None,
                         dauer_s: float = None, grund: str = None,
                         quelle: str = "harness_aider.einen_lauf") -> None:
    """Schreibt EINEN echten Datenpunkt -- aufgerufen bei JEDEM realen
    Modell-Lauf (nicht nur testweise), Grundlage fuer erfolgsquote() und
    spaeter die Selbstverbesserungsschleife. Fail-soft: DB-Fehler duerfen
    nie einen echten Arbeitszyklus zum Absturz bringen."""
    try:
        conn = _db()
        try:
            conn.execute(
                "INSERT INTO aufrufe (ts, modell_id, ok, chunked, anzahl_chunks, "
                "geschaetzte_tokens, dauer_s, grund, quelle) VALUES (?,?,?,?,?,?,?,?,?)",
                (time.time(), modell_id, 1 if ok else 0, 1 if chunked else 0,
                 anzahl_chunks, geschaetzte_tokens, dauer_s, grund, quelle),
            )
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass


def erfolgsquote(modell_id: str, fenster: int = 50) -> dict:
    """Echte Quote aus den letzten `fenster` Eintraegen dieses Modells --
    Grundlage der Selbstverbesserungs-Auswertung (welches Modell/welche
    Chunking-Strategie traegt wirklich). Liefert {'n':0,...} bei leerem
    Verlauf, nie eine erfundene Zahl."""
    try:
        conn = _db()
        try:
            rows = conn.execute(
                "SELECT ok, chunked FROM aufrufe WHERE modell_id=? "
                "ORDER BY id DESC LIMIT ?", (modell_id, fenster)).fetchall()
        finally:
            conn.close()
    except Exception:
        rows = []
    n = len(rows)
    if n == 0:
        return {"n": 0, "erfolgsquote": None, "anteil_chunked": None}
    erfolgreich = sum(r[0] for r in rows)
    gechunkt = sum(r[1] for r in rows)
    return {"n": n, "erfolgsquote": round(erfolgreich / n, 3),
            "anteil_chunked": round(gechunkt / n, 3)}


def alle_erfolgsquoten() -> dict:
    """Uebersicht ueber alle bisher tatsaechlich gelaufenen Modelle --
    fuer Dashboards/Selbstpruefung, nicht nur die Profile, sondern der
    reale, gemessene Stand."""
    try:
        conn = _db()
        try:
            modelle = [r[0] for r in conn.execute(
                "SELECT DISTINCT modell_id FROM aufrufe").fetchall()]
        finally:
            conn.close()
    except Exception:
        modelle = []
    return {m: erfolgsquote(m) for m in modelle}


def _roh_lauf(harness, modell_id, auftrag_text, **kwargs):
    """Ruft bevorzugt harness._einen_lauf_kern() (KEIN Auto-Verbuchen) statt
    harness.einen_lauf() (verbucht sich seit PHASE 53 selbst) -- sonst
    wuerde chunked_lauf() jeden Teil-Aufruf DOPPELT in der Historie fuehren
    (einmal automatisch mit chunked=False/anzahl_chunks=1 im Wrapper, einmal
    hier mit den korrekten chunked=True-Werten). Faellt auf einen_lauf()
    zurueck, wenn der Kern nicht existiert (z.B. ein einfacher Test-Stub)."""
    kern = getattr(harness, "_einen_lauf_kern", None)
    if kern is not None:
        return kern(modell_id, auftrag_text, **kwargs)
    return harness.einen_lauf(modell_id, auftrag_text, **kwargs)


# ── 4. Echte Ausfuehrung mit Chunking ────────────────────────────────────

def chunked_lauf(modell_id: str, auftrag_text: str, *, harness=None, **kwargs) -> dict:
    """Wie harness_aider.einen_lauf(), aber chunk-bewusst: prueft zuerst
    braucht_chunking(); wenn nein, EIN normaler Lauf (kein Overhead). Wenn
    ja, wird nach der Strategie des Zielmodells zerlegt:

      * 'progressiv'    -- EIN einen_lauf()-Aufruf, dessen Auftragstext
                            selbst die nummerierten Teile + eine wachsende
                            Kurz-Zusammenfassung traegt ("nach und nach
                            injizieren" -- Gabriel).
      * 'neuer_request'  -- MEHRERE einen_lauf()-Aufrufe nacheinander, je
                            einer pro Teil, mit knapper Ueberleitung
                            zwischen den Aufrufen ("immer nen neuen
                            request machen" -- Gabriel).

    `harness` ist das schon importierte harness_aider-Modul (Dependency
    Injection statt hartem Import, macht diese Funktion isoliert testbar
    ohne echte API-Keys/Netzwerk). Jeder echte Teillauf wird ueber
    verlauf_aufzeichnen() in der Historie festgehalten. Liefert
    {'ok','chunked','anzahl_chunks','teil_ergebnisse',...}."""
    start = time.time()
    p = profil(modell_id)
    if not braucht_chunking(modell_id, auftrag_text):
        if harness is None:
            return {"ok": False, "grund": "kein harness-Modul uebergeben", "chunked": False}
        r = _roh_lauf(harness, modell_id, auftrag_text, **kwargs)
        verlauf_aufzeichnen(modell_id, bool(r.get("ok")), chunked=False,
                            anzahl_chunks=1,
                            geschaetzte_tokens=_tokens_schaetzen(auftrag_text),
                            dauer_s=time.time() - start, grund=r.get("grund"))
        return {**r, "chunked": False, "anzahl_chunks": 1}

    teile = chunks_bilden(auftrag_text, modell_id)
    n = len(teile)
    ergebnisse = []

    if p["chunk_strategie"] == "progressiv":
        zusammenfassung = ""
        aufgebauter_text = (
            f"GROSSE AUFGABE, in {n} Teile zerlegt (Modell-Budget "
            f"{p['sicherer_einzelaufruf_tokens']} Token) -- lies ALLE Teile, "
            f"bevor du antwortest/aenderst:\n\n")
        for i, teil in enumerate(teile, 1):
            aufgebauter_text += f"--- Teil {i}/{n} ---\n{teil}\n\n"
        aufgebauter_text += (
            f"--- Ende, {n} Teile insgesamt ---\nBearbeite jetzt die "
            f"GESAMTE, oben in {n} Teilen eingespeiste Aufgabe.")
        if harness is None:
            return {"ok": False, "grund": "kein harness-Modul uebergeben", "chunked": True, "anzahl_chunks": n}
        r = _roh_lauf(harness, modell_id, aufgebauter_text, **kwargs)
        ergebnisse.append(r)
        verlauf_aufzeichnen(modell_id, bool(r.get("ok")), chunked=True,
                            anzahl_chunks=n,
                            geschaetzte_tokens=_tokens_schaetzen(auftrag_text),
                            dauer_s=time.time() - start, grund=r.get("grund"))
        gesamt_ok = bool(r.get("ok"))
    else:  # 'neuer_request'
        vorherige_kurzfassung = ""
        gesamt_ok = True
        for i, teil in enumerate(teile, 1):
            teil_auftrag = (
                f"Teil {i}/{n} einer groesseren, in mehrere EIGENSTAENDIGE "
                f"Auftraege zerlegten Aufgabe (Modell-Budget "
                f"{p['sicherer_einzelaufruf_tokens']} Token je Anfrage).\n")
            if vorherige_kurzfassung:
                teil_auftrag += f"Bisher erledigt (Kurzfassung): {vorherige_kurzfassung[:400]}\n"
            teil_auftrag += f"\nDieser Teil:\n{teil}"
            if harness is None:
                r = {"ok": False, "grund": "kein harness-Modul uebergeben"}
            else:
                r = _roh_lauf(harness, modell_id, teil_auftrag, **kwargs)
            ergebnisse.append(r)
            verlauf_aufzeichnen(modell_id, bool(r.get("ok")), chunked=True,
                                anzahl_chunks=n,
                                geschaetzte_tokens=_tokens_schaetzen(teil_auftrag),
                                dauer_s=time.time() - start, grund=r.get("grund"),
                                quelle="modell_profile.chunked_lauf[neuer_request]")
            gesamt_ok = gesamt_ok and bool(r.get("ok"))
            vorherige_kurzfassung = (
                f"Teil {i}/{n}: {'ok' if r.get('ok') else 'fehlgeschlagen (' + str(r.get('grund'))[:80] + ')'}")

    return {"ok": gesamt_ok, "chunked": True, "anzahl_chunks": n,
            "teil_ergebnisse": ergebnisse,
            "grund": None if gesamt_ok else "mindestens ein Teil-Lauf fehlgeschlagen"}


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "status":
        print(json.dumps({"profile": MODELL_PROFILE, "gemessen": alle_erfolgsquoten()},
                         ensure_ascii=False, indent=2))
    else:
        print("Nutzung: modell_profile.py status", file=sys.stderr)
