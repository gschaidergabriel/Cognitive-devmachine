"""Bahnrouter: Zero fragt nach einer FAEHIGKEIT, nie nach einem Anbieter.

Der Clay-Unterbau haelt eine durchdachte Verdrahtung -- 22 Zugaenge, 11 kognitive
Prozesse, je mit Erst-, Zweit- und Drittbahn und einem Anteilsdeckel. Sie war aber
Dokumentation: nichts erzwang die Deckel, und Zeros Container erreichte keine
einzige Bahn.

Drei Regeln, die diesen Router von einer Anbieterliste unterscheiden:

  1. DAS MODELL WAEHLT NICHT. Aufgerufen wird eine Faehigkeit ("kondensieren",
     "zweitmeinung"). Welche Bahn das bedient, entscheidet Code. Sonst waehlt auf
     Dauer die Formulierung des Prompts den Anbieter, und niemand kann sagen, warum
     eine Rechnung gestiegen ist.

  2. DECKEL WERDEN ERZWUNGEN, NICHT ERKLAERT. Jeder Prozess darf hoechstens seinen
     Anteil am Tageskontingent einer Bahn verbrauchen. Ein Deckel, den niemand
     zaehlt, ist ein Vorsatz.

  3. ERSCHOEPFT HEISST ABLEHNUNG, NICHT ABSTIEG. Sind alle verdrahteten Bahnen
     eines Prozesses erschoepft, wird abgelehnt -- nicht heimlich auf etwas
     Schlechteres ausgewichen. Ein stiller Abstieg liefert weiter Antworten, nur
     schlechtere, und das faellt erst auf, wenn niemand mehr weiss warum.

⚠️ NVIDIA gehoert der Kognition. Steht so im Unterbau und wird hier nicht umgangen.
"""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

BAHNEN_JSON = Path(__file__).with_name("bahnen.json")
ZUGAENGE_ENV = Path("/etc/clayverse/freie-zugaenge.env")

# OpenAI-kompatible Endpunkte -- Groq, Mistral, NVIDIA, OpenRouter und DeepSeek
# sprechen dasselbe Protokoll. Ein Aufrufer statt fuenf.
ENDPUNKTE = {
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "GROQ_API_KEY"),
    "mistral": ("https://api.mistral.ai/v1/chat/completions", "MISTRAL_API_KEY"),
    "nvidia": ("https://integrate.api.nvidia.com/v1/chat/completions", "NVIDIA_NIM_API_KEY"),
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", "OPENROUTER_API_KEY"),
    "deepseek": ("https://api.deepseek.com/v1/chat/completions", "DEEPSEEK_API_KEY"),
}

SCHEMA = """
CREATE TABLE IF NOT EXISTS bahn_nutzung(
  bahn TEXT NOT NULL,
  prozess TEXT NOT NULL,
  tag TEXT NOT NULL,
  anfragen INTEGER NOT NULL DEFAULT 0,
  token INTEGER NOT NULL DEFAULT 0,
  fehler INTEGER NOT NULL DEFAULT 0,
  zuletzt REAL NOT NULL,
  PRIMARY KEY(bahn, prozess, tag)
);
CREATE TABLE IF NOT EXISTS bahn_livestreak(
  bahn TEXT PRIMARY KEY,
  serie INTEGER NOT NULL DEFAULT 0,
  zuletzt_fehler REAL,
  zuletzt_ergebnis TEXT
);
"""

# Eine Kalibrierung ("zustand": "nutzbar" in bahnen.json) ist eine Momentaufnahme
# von einem bestimmten Tag -- kein Betriebszustand. Provider schalten Modelle ab,
# ohne die Datei zu aktualisieren (siehe bahnen.json-Hinweis: Groq hat zwischen
# dem 15. und 18.08. Modelle abgeschaltet, die dort als "nutzbar" standen). Live-
# Fehlschlaege muessen das stechen koennen. LEBEND_SCHWELLE ist bewusst klein --
# ein einzelner Ausrutscher soll keine Bahn sperren, eine kleine Serie schon.
LEBEND_SCHWELLE = 3
# Nach der Abkuehlung darf die Bahn wieder ran (halb offen: ein Versuch zeigt,
# ob sie sich erholt hat). Sonst wird aus einer voruebergehenden Stoerung eine
# Dauersperre -- das ist selbst ein Bug.
LEBEND_ABKUEHLUNG_SEK = 300


class BahnErschoepft(RuntimeError):
    """Alle verdrahteten Bahnen eines Prozesses sind aufgebraucht."""


class _BahnLieferteNichts(RuntimeError):
    """Diese eine Bahn hat nichts geliefert -- die naechste ist dran."""
    def __init__(self, bahn: str, grund: str):
        super().__init__(f"{bahn}: {grund}")
        self.bahn, self.grund = bahn, grund


class KeinZugang(RuntimeError):
    """Fuer diese Bahn liegt kein Schluessel vor."""


def _heute() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _schluessel(name: str) -> str | None:
    """Zugangsdaten frisch je Aufruf lesen. Nie zwischenspeichern, nie ausgeben."""
    if name in os.environ:
        return os.environ[name] or None
    if not ZUGAENGE_ENV.exists():
        return None
    for zeile in ZUGAENGE_ENV.read_text(encoding="utf-8").splitlines():
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        k, v = zeile.split("=", 1)
        if k.strip() == name:
            return v.strip() or None
    return None


class Bahnrouter:
    def __init__(self, db):
        self.db = db
        self.db.db.executescript(SCHEMA)
        d = json.loads(BAHNEN_JSON.read_text(encoding="utf-8"))
        self.zugaenge = {z["zugang"]: z for z in d["zugaenge"]}
        self.prozesse = {p["prozess"]: p for p in d["prozesse"]}

    # ── Buchfuehrung ──────────────────────────────────────────────────────
    def _verbrauch(self, bahn: str, prozess: str) -> int:
        r = self.db.db.execute(
            "SELECT anfragen FROM bahn_nutzung WHERE bahn=? AND prozess=? AND tag=?",
            (bahn, prozess, _heute()),
        ).fetchone()
        return int(r[0]) if r else 0

    def _buchen(self, bahn: str, prozess: str, *, token: int = 0, fehler: bool = False) -> None:
        jetzt = time.time()
        with self.db.tx() as sql:
            sql.execute(
                "INSERT INTO bahn_nutzung(bahn,prozess,tag,anfragen,token,fehler,zuletzt) "
                "VALUES(?,?,?,1,?,?,?) ON CONFLICT(bahn,prozess,tag) DO UPDATE SET "
                "anfragen=anfragen+1, token=token+excluded.token, "
                "fehler=fehler+excluded.fehler, zuletzt=excluded.zuletzt",
                (bahn, prozess, _heute(), token, 1 if fehler else 0, jetzt),
            )
            # Livestreak ist je Bahn (nicht je Prozess) gefuehrt: die Bahn selbst
            # ist tot oder nicht, unabhaengig davon, welcher Prozess gerade fragt.
            if fehler:
                sql.execute(
                    "INSERT INTO bahn_livestreak(bahn,serie,zuletzt_fehler,zuletzt_ergebnis) "
                    "VALUES(?,1,?,'fehler') ON CONFLICT(bahn) DO UPDATE SET "
                    "serie=serie+1, zuletzt_fehler=excluded.zuletzt_fehler, zuletzt_ergebnis='fehler'",
                    (bahn, jetzt),
                )
            else:
                sql.execute(
                    "INSERT INTO bahn_livestreak(bahn,serie,zuletzt_fehler,zuletzt_ergebnis) "
                    "VALUES(?,0,NULL,'erfolg') ON CONFLICT(bahn) DO UPDATE SET "
                    "serie=0, zuletzt_ergebnis='erfolg'",
                    (bahn,),
                )

    def _lebend_gesperrt(self, bahn: str) -> tuple[bool, str | None]:
        """Ist diese Bahn wegen einer LIVE-Fehlschlagserie gerade gesperrt?

        Sticht eine stehende 'nutzbar'-Kalibrierung -- die kann Tage alt sein.
        Erholt sich die Bahn (Erfolg -> serie=0 in _buchen, oder Abkuehlung
        verstrichen -> ein Versuch darf's zeigen), ist sie sofort wieder dran.
        """
        r = self.db.db.execute(
            "SELECT serie, zuletzt_fehler FROM bahn_livestreak WHERE bahn=?", (bahn,),
        ).fetchone()
        if not r or r[0] < LEBEND_SCHWELLE:
            return False, None
        serie, zuletzt_fehler = r[0], r[1] or 0.0
        seit = time.time() - zuletzt_fehler
        if seit >= LEBEND_ABKUEHLUNG_SEK:
            return False, None  # Abkuehlung um -- naechster Versuch darf Erholung zeigen
        return True, (f"{serie} Fehlschlaege in Folge (live), Kalibrierung ignoriert; "
                      f"naechster Versuch in {int(LEBEND_ABKUEHLUNG_SEK - seit)}s")

    def _deckel(self, bahn: str, prozess: str) -> int | None:
        """Wie viele Anfragen dieser Prozess heute auf dieser Bahn noch darf."""
        z, p = self.zugaenge.get(bahn), self.prozesse.get(prozess)
        if not z or not p:
            return 0
        tag = z.get("tag_limit")
        if not tag:
            return None  # kein bekanntes Tageslimit -> nicht deckelbar, siehe unten
        return int(tag * float(p.get("hoechstanteil") or 1.0))

    # ── Auswahl ───────────────────────────────────────────────────────────
    def waehle(self, prozess: str, *, ueberspringen: set | None = None) -> dict:
        """Erste brauchbare Bahn samt Begruendung -- oder Ablehnung."""
        p = self.prozesse.get(prozess)
        if not p:
            raise KeyError(f"unbekannter Prozess: {prozess}")
        ueberspringen = ueberspringen or set()
        abgelehnt = []
        for bahn in p["bahnen"]:
            if bahn in ueberspringen:
                abgelehnt.append((bahn, "in diesem Aufruf bereits ohne Ergebnis"))
                continue
            z = self.zugaenge.get(bahn)
            if not z:
                abgelehnt.append((bahn, "nicht in der Verdrahtung"))
                continue
            if z.get("zustand") not in (None, "nutzbar"):
                abgelehnt.append((bahn, f"Zustand {z.get('zustand')}"))
                continue
            gesperrt, grund = self._lebend_gesperrt(bahn)
            if gesperrt:
                abgelehnt.append((bahn, grund))
                continue
            familie = self._familie(bahn)
            if familie is None:
                abgelehnt.append((bahn, "kein Aufrufer fuer diese Bahn gebaut"))
                continue
            if not _schluessel(ENDPUNKTE[familie][1]):
                abgelehnt.append((bahn, "kein Schluessel hinterlegt"))
                continue
            deckel = self._deckel(bahn, prozess)
            benutzt = self._verbrauch(bahn, prozess)
            if deckel is not None and benutzt >= deckel:
                abgelehnt.append((bahn, f"Deckel erreicht: {benutzt}/{deckel} heute"))
                continue
            return {"bahn": bahn, "familie": familie, "modell": z.get("modell"),
                    "benutzt_heute": benutzt, "deckel": deckel, "verworfen": abgelehnt}
        raise BahnErschoepft(
            f"Prozess '{prozess}': keine Bahn verfuegbar. " +
            "; ".join(f"{b}: {g}" for b, g in abgelehnt))

    @staticmethod
    def _familie(bahn: str) -> str | None:
        for f in ENDPUNKTE:
            if bahn.startswith(f):
                return f
        return None

    # ── Aufruf ────────────────────────────────────────────────────────────
    def rufe(self, prozess: str, auftrag: str, *, system: str | None = None,
             max_token: int = 800, timeout: int = 60) -> dict:
        """Ruft die erste brauchbare Bahn. Liefert eine Bahn nichts, kommt die naechste."""
        ausgefallen: list[tuple[str, str]] = []
        letzter = None
        for _ in range(4):  # hoechstens so viele Bahnen wie ein Prozess hat
            try:
                return self._ein_versuch(prozess, auftrag, system=system, max_token=max_token,
                                         timeout=timeout, ueberspringen=set(b for b, _ in ausgefallen),
                                         bisher=ausgefallen)
            except _BahnLieferteNichts as e:
                ausgefallen.append((e.bahn, e.grund))
                letzter = e
                continue
        raise BahnErschoepft(
            f"Prozess '{prozess}': alle Bahnen ohne Ergebnis. " +
            "; ".join(f"{b}: {g}" for b, g in ausgefallen))

    def _ein_versuch(self, prozess: str, auftrag: str, *, system, max_token, timeout,
                     ueberspringen: set, bisher: list) -> dict:
        wahl = self.waehle(prozess, ueberspringen=ueberspringen)
        familie, bahn = wahl["familie"], wahl["bahn"]
        url, keyname = ENDPUNKTE[familie]
        schluessel = _schluessel(keyname)
        if not schluessel:
            raise KeinZugang(f"{keyname} fehlt")

        nachrichten = ([{"role": "system", "content": system}] if system else []) + \
                      [{"role": "user", "content": auftrag}]
        koerper = json.dumps({"model": wahl["modell"], "messages": nachrichten,
                              "max_tokens": max_token}).encode()
        # Ohne eigenen User-Agent weist Cloudflare mit "error code: 1010" ab --
        # das sieht wie ein ungueltiger Schluessel aus und ist keiner. Hat mich
        # heute einmal zu der falschen Aussage verleitet, ein Schluessel sei tot.
        req = urllib.request.Request(url, data=koerper, headers={
            "Authorization": f"Bearer {schluessel}", "Content-Type": "application/json",
            "User-Agent": "EntityOS/1.0 (+https://entityos.frank.ink)"})
        t = time.time()
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            self._buchen(bahn, prozess, fehler=True)
            raise _BahnLieferteNichts(bahn, f"HTTP {e.code}: {e.read().decode()[:120]}") from None
        except Exception as e:
            self._buchen(bahn, prozess, fehler=True)
            raise _BahnLieferteNichts(bahn, f"{type(e).__name__}") from None
        ms = (time.time() - t) * 1000
        token = int((d.get("usage") or {}).get("total_tokens") or 0)
        inhalt = (d.get("choices") or [{}])[0].get("message", {}).get("content", "") or ""
        if not inhalt.strip():
            # 200, Token verbraucht, nichts gesagt. Reasoning-Modelle tun das,
            # wenn das Budget im Denkkanal aufgeht. Als Ausfall behandeln --
            # sonst gibt der Router eine leere Antwort als Ergebnis aus.
            self._buchen(bahn, prozess, token=token, fehler=True)
            raise _BahnLieferteNichts(
                bahn, f"HTTP 200 aber leerer Inhalt bei {token} Token "
                      "(Reasoning-Modell? max_token zu klein?)")
        self._buchen(bahn, prozess, token=token)
        return {
            "prozess": prozess, "bahn": bahn, "modell": wahl["modell"],
            "text": inhalt,
            "ms": round(ms, 1), "token": token,
            "benutzt_heute": wahl["benutzt_heute"] + 1, "deckel": wahl["deckel"],
            "verworfene_bahnen": wahl["verworfen"] + list(bisher),
        }

    def lage(self) -> list[dict]:
        """Was heute auf welcher Bahn verbraucht wurde -- fuer die Vorstufe und den Export."""
        aus = []
        for prozess, p in self.prozesse.items():
            for bahn in p["bahnen"]:
                benutzt = self._verbrauch(bahn, prozess)
                if benutzt:
                    aus.append({"prozess": prozess, "bahn": bahn, "benutzt_heute": benutzt,
                                "deckel": self._deckel(bahn, prozess)})
        return aus
