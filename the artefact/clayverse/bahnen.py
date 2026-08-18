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
"""


class BahnErschoepft(RuntimeError):
    """Alle verdrahteten Bahnen eines Prozesses sind aufgebraucht."""


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
        with self.db.tx() as sql:
            sql.execute(
                "INSERT INTO bahn_nutzung(bahn,prozess,tag,anfragen,token,fehler,zuletzt) "
                "VALUES(?,?,?,1,?,?,?) ON CONFLICT(bahn,prozess,tag) DO UPDATE SET "
                "anfragen=anfragen+1, token=token+excluded.token, "
                "fehler=fehler+excluded.fehler, zuletzt=excluded.zuletzt",
                (bahn, prozess, _heute(), token, 1 if fehler else 0, time.time()),
            )

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
    def waehle(self, prozess: str) -> dict:
        """Erste brauchbare Bahn samt Begruendung -- oder Ablehnung."""
        p = self.prozesse.get(prozess)
        if not p:
            raise KeyError(f"unbekannter Prozess: {prozess}")
        abgelehnt = []
        for bahn in p["bahnen"]:
            z = self.zugaenge.get(bahn)
            if not z:
                abgelehnt.append((bahn, "nicht in der Verdrahtung"))
                continue
            if z.get("zustand") not in (None, "nutzbar"):
                abgelehnt.append((bahn, f"Zustand {z.get('zustand')}"))
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
        wahl = self.waehle(prozess)
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
            # Fehler wird gebucht und weitergereicht. KEIN stiller Abstieg auf die
            # naechste Bahn: ein Ausweichen, das niemand sieht, verwandelt einen
            # Ausfall in eine schleichende Verschlechterung.
            raise RuntimeError(f"Bahn {bahn} antwortete {e.code}: {e.read().decode()[:200]}") from None
        ms = (time.time() - t) * 1000
        token = int((d.get("usage") or {}).get("total_tokens") or 0)
        self._buchen(bahn, prozess, token=token)
        return {
            "prozess": prozess, "bahn": bahn, "modell": wahl["modell"],
            "text": (d.get("choices") or [{}])[0].get("message", {}).get("content", ""),
            "ms": round(ms, 1), "token": token,
            "benutzt_heute": wahl["benutzt_heute"] + 1, "deckel": wahl["deckel"],
            "verworfene_bahnen": wahl["verworfen"],
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
