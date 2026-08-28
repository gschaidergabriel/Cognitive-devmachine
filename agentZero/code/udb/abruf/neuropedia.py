#!/usr/bin/env python3
"""udb/abruf/neuropedia.py — Neuronpedia API-Client fuer UnifiedDB.

⚠️ WAS HIER GEMESSEN WIRD (das muss klar sein, sonst liest der Eigner es als
Zeros eigene Neuronen): Neuronpedia liefert Aktivierungswerte OFFENER
FORSCHUNGSMODELLE (Standard: gpt2-small, ein 2019er GPT-2 mit 12 Layern),
gemessen auf deren internen Feature-/Neuron-Dimensionen (Sparse Autoencoder
bzw. rohe Residual-Stream-Neuronen, je nach 'source'). Das ist NICHT Zero,
NICHT das Modell hinter dieser Session, und NICHT ClayVerse. Es ist eine
externe, oeffentliche Forschungsdatenbank ueber ANDERE, kleine Modelle.
Der Nutzen fuer ClayVerse ist Forschungsvergleich (z.B. "wie aktivieren
bestimmte Token-Muster ein bekanntes Modell"), keine Introspektion von Zero
selbst -- dafuer gibt es hier keinen Messweg.

Schluessel-Konvention wie nvidia_embedding.py: frisch aus der Tresordatei,
nie geloggt. NEUROPEDIA_API_KEY steht Stand 2026-08-18 NICHT in
/etc/clayverse/freie-zugaenge.env -- ohne ihn liefert dieses Modul einen
klaren Fehler statt eines stillen Fehlschlags (siehe fehlt_schluessel()).
"""
from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from typing import Literal

try:
    import httpx2 as _http
except ImportError:  # pragma: no cover
    import httpx as _http  # type: ignore[no-redef]

from udb.abruf.zustand import verbindung, schreib_verbindung

ZUGAENGE_PFAD = os.environ.get("CLAYVERSE_ZUGAENGE_PFAD", "/etc/clayverse/freie-zugaenge.env")
NEUROPEDIA_BASE_URL = os.environ.get("NEUROPEDIA_BASE_URL", "https://www.neuronpedia.org/api")


def _schluessel_optional(name: str) -> str | None:
    """Wie nvidia_embedding._schluessel(), aber gibt None statt zu werfen --
    Neuronpedia ist (noch) kein Pflichtzugang im Haus."""
    if not os.path.exists(ZUGAENGE_PFAD):
        return None
    for zeile in open(ZUGAENGE_PFAD, encoding="utf-8"):
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        k, v = zeile.split("=", 1)
        if k.strip() == name:
            v = v.strip().strip('"').strip("'")
            return v or None
    return None


def fehlt_schluessel() -> bool:
    """True, wenn NEUROPEDIA_API_KEY (noch) nicht in der Tresordatei steht."""
    return _schluessel_optional("NEUROPEDIA_API_KEY") is None


@dataclass
class ActivationData:
    tokens: list[str]
    activations: list[float]
    max_value: float
    max_value_token_index: int
    layer: str
    model_id: str
    index: str
    # Ohne diese vier ist ein Merkmal nur eine Zahlenreihe.
    deutung: str = ""
    max_act_approx: float = 0.0
    frac_nonzero: float = 0.0
    top_token: tuple = ()
    beispiele: int = 0
    gemessen_an: str = "oeffentliches Forschungsmodell auf Neuronpedia-SAE, nicht Zero"


class NeuronpediaAPI:
    """Client fuer die oeffentliche Neuronpedia-API -- Aktivierungen ANDERER,
    offener Forschungsmodelle (siehe Modul-Docstring)."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        self.api_key = api_key if api_key is not None else _schluessel_optional("NEUROPEDIA_API_KEY")
        self.base_url = base_url or NEUROPEDIA_BASE_URL
        if not self.api_key:
            raise RuntimeError(
                f"NEUROPEDIA_API_KEY fehlt in {ZUGAENGE_PFAD}. Neuronpedia-Aufrufe sind "
                "damit nicht moeglich -- kein stiller Fehlschlag, klarer Abbruch."
            )
        self.headers = {"X-Api-Key": self.api_key, "Content-Type": "application/json"}

    # Was hier gemessen wird: Merkmale oeffentlicher Forschungsmodelle auf
    # Neuronpedias gehosteten SAEs. NICHT Zero, nicht das Modell dieser Sitzung.
    GEMESSEN_AN = "oeffentliches Forschungsmodell auf Neuronpedia-SAE, nicht Zero"

    def get_activation(self, model_id: str, source: str, index: str) -> ActivationData:
        """Merkmal samt Deutung und Aktivierungsstatistik lesen.

        GET /feature/... statt POST /activation/new: gemessen 18.08. antwortet
        der POST-Weg mit 500, auch mit echtem Text -- serverseitig, nicht bei
        uns. Der GET-Weg liefert 200 mit explanations, maxActApprox,
        frac_nonzero und den staerkst aktivierenden Token.
        """
        url = f"{self.base_url}/feature/{model_id}/{source}/{index}"
        with _http.Client(timeout=30.0) as c:
            r = c.get(url, headers=self.headers)
        if r.status_code >= 400:
            raise ConnectionError(f"Neuronpedia API Fehler {r.status_code}: {r.text[:300]}")
        data = r.json()
        if isinstance(data, list):
            if not data:
                raise ValueError("Keine Aktivierungsdaten zurueckgegeben")
            data = data[0]
        if not isinstance(data, dict):
            raise ValueError(f"Unerwartete Antwortform: {type(data)}")

        # Die Aktivierungsbeispiele liegen EINE EBENE TIEFER. Die oberste Ebene
        # traegt die Merkmalsbeschreibung, data["activations"] die Belege dazu.
        beispiele = data.get("activations") or []
        first = beispiele[0] if beispiele else {}
        deutungen = data.get("explanations") or []
        deutung = ""
        if deutungen and isinstance(deutungen[0], dict):
            deutung = str(deutungen[0].get("description") or "")

        return ActivationData(
            tokens=first.get("tokens", []),
            activations=first.get("values", []),
            max_value=first.get("maxValue", 0),
            max_value_token_index=first.get("maxValueTokenIndex", 0),
            layer=first.get("layer", source) or source,
            model_id=first.get("modelId", model_id) or model_id,
            index=str(first.get("index", index)),
            deutung=deutung,
            max_act_approx=float(data.get("maxActApprox") or 0.0),
            frac_nonzero=float(data.get("frac_nonzero") or 0.0),
            top_token=tuple((data.get("pos_str") or [])[:10]),
            beispiele=len(beispiele),
        )


def aktivierung_abrufen(model_id: str, source: str, index: str) -> ActivationData:
    """Convenience-Funktion: EINE Live-Neuronpedia-Aktivierung abrufen."""
    return NeuronpediaAPI().get_activation(model_id, source, index)


def clayverse_forschung_analyse(modell: str, source: str, indices: list[str]) -> dict:
    """Forschungsanalyse ueber eine Handvoll konkreter Indizes (kein
    ungebremstes 'alle Aktivierungen', das gab es in der Lueckenfassung als
    unbegrenzten Endpunkt, der so bei Neuronpedia nicht existiert)."""
    api = NeuronpediaAPI()
    aktivierungen = []
    fehler = []
    for idx in indices:
        try:
            aktivierungen.append(api.get_activation(modell, source, idx))
        except Exception as e:  # noqa: BLE001
            fehler.append(str(e))
    if not aktivierungen:
        return {"error": "Keine Aktivierungen gefunden", "fehler": fehler,
                "was_gemessen": "gpt2-small u.ae. -- NICHT Zero selbst"}

    alle_aktivierungen = [v for a in aktivierungen for v in a.activations]
    alle_tokens = [t for a in aktivierungen for t in a.tokens]
    return {
        "modell": modell,
        "source": source,
        "was_gemessen": f"oeffentliches Forschungsmodell {modell}, nicht Zero",
        "anzahl_aktivierungen": len(aktivierungen),
        "tokens_total": len(alle_tokens),
        "einzigartige_tokens": len(set(alle_tokens)),
        "durchschnittliche_aktivierung": sum(alle_aktivierungen) / len(alle_aktivierungen) if alle_aktivierungen else 0,
        "max_aktivierung": max(alle_aktivierungen) if alle_aktivierungen else 0,
        "min_aktivierung": min(alle_aktivierungen) if alle_aktivierungen else 0,
        "fehler": fehler,
    }


TABELLE = "forschung_neuropedia"


def _ensure_tabelle(c) -> None:
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABELLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            projekt TEXT NOT NULL,
            modell TEXT NOT NULL,
            source TEXT NOT NULL,
            aktiv_index TEXT NOT NULL,
            tokens_json TEXT NOT NULL,
            aktivierungen_json TEXT NOT NULL,
            max_aktivierung REAL NOT NULL,
            erstellt_am TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    c.commit()


def in_unifieddb_speichern(aktivierung: ActivationData, c, projekt: str) -> None:
    _ensure_tabelle(c)
    c.execute(f"""
        INSERT INTO {TABELLE}
        (projekt, modell, source, aktiv_index, tokens_json, aktivierungen_json, max_aktivierung, erstellt_am)
        VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, (
        projekt, aktivierung.model_id, aktivierung.layer, aktivierung.index,
        json.dumps(aktivierung.tokens), json.dumps(aktivierung.activations), aktivierung.max_value,
    ))
    c.commit()


def forschung_neuropedia_anzeigen(c, limit: int = 10) -> list[dict]:
    rows = c.execute(f"""
        SELECT projekt, modell, source, aktiv_index, max_aktivierung, erstellt_am
        FROM {TABELLE} ORDER BY erstellt_am DESC LIMIT ?
    """, (limit,)).fetchall()
    return [
        {"projekt": r[0], "modell": r[1], "source": r[2], "index": r[3],
         "max_aktivierung": r[4], "erstellt_am": r[5]}
        for r in rows
    ]


def aktivierung_fuer_text(model_id: str, source: str, index: str, text: str) -> dict:
    """Eigenen Text durch den SAE schicken.

    ⚠️ GEMESSEN 2026-08-18: Neuronpedia antwortet auf diesem Endpunkt mit
    HTTP 500, auch bei gueltigem Schluessel und echtem Text. Der Fehler liegt
    beim Anbieter. Die Funktion bleibt bestehen, damit der Weg vorhanden ist,
    sobald er dort wieder geht -- sie meldet den Zustand aber klar, statt ihn
    als unseren Fehler erscheinen zu lassen.
    """
    api = NeuronpediaAPI()
    with _http.Client(timeout=40.0) as c:
        r = c.post(
            f"{api.base_url}/activation/new",
            headers=api.headers,
            json={"modelId": model_id, "source": source, "index": index, "customText": text},
        )
    if r.status_code >= 400:
        return {
            "status": "ANBIETER_FEHLER",
            "http": r.status_code,
            "hinweis": "POST /activation/new ist bei Neuronpedia serverseitig gestoert (gemessen 2026-08-18). "
                       "Der Merkmalsabruf ueber get_activation() funktioniert.",
            "gemessen_an": NeuronpediaAPI.GEMESSEN_AN,
        }
    return {"status": "OK", "daten": r.json(), "gemessen_an": NeuronpediaAPI.GEMESSEN_AN}
