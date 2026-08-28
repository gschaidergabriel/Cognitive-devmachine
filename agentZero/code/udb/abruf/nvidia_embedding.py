#!/usr/bin/env python3
"""udb/abruf/nvidia_embedding.py — NVIDIA NIM Embedding-Client fuer UnifiedDB.

Modell nvidia/nv-embedqa-e5-v5, 1024 Dimensionen. GEMESSEN (2026-08-18, VPS
frank-api, echter API-Aufruf gegen integrate.api.nvidia.com):
    Einzelaufruf (1 Text):     ~199 ms
    Batch  8 Texte in 1 Call:  ~27.8 ms/Text  (222.7 ms gesamt)
    Batch 128 Texte in 1 Call:  ~2.9 ms/Text  (367.1 ms gesamt)
    -> 128er-Batch ist der Suesspunkt: 9.7x weniger Zeit je Text als bei 8.
IMMER BATCHEN. embed_batch() schickt bis zu BATCH_SIZE Texte in EINEM
HTTP-Aufruf -- das ist der Unterschied zur ersten Fassung dieses Moduls,
die pro Text einen eigenen Request machte (Lueckenfassung 2026-08-16, nie
gegen die echte API gemessen).

Schluessel kommen NIE aus einer committeten .env-Datei, sondern werden bei
jedem Aufruf frisch aus der Tresordatei gelesen (Hauskonvention, siehe
/opt/clayverse/werkzeug/werkzeuge.py:schluessel()). Werte werden nie
geloggt, nie in Rueckgaben eingebettet, nie in die DB geschrieben.
"""
from __future__ import annotations

import json
import os
import time
from typing import List

try:
    import httpx2 as _http  # im EntityOS-Image installiert (mcp-Abhaengigkeit)
except ImportError:  # pragma: no cover -- Host-Betrieb/Tests ausserhalb des Images
    import httpx as _http  # type: ignore[no-redef]

from udb.abruf.zustand import verbindung, schreib_verbindung

# ── Zugaenge ─────────────────────────────────────────────────────────────
ZUGAENGE_PFAD = os.environ.get("CLAYVERSE_ZUGAENGE_PFAD", "/etc/clayverse/freie-zugaenge.env")


def _schluessel(name: str) -> str:
    """Liest EINEN Wert aus der Tresordatei. Gibt ihn zurueck, gibt ihn nie
    aus. Fehlt er, ist das ein klarer Fehler statt eines stillen 401.
    (Hauskonvention aus werkzeuge.py:schluessel(), hier dupliziert statt
    importiert -- werkzeuge.py liegt ausserhalb des UnifiedDB-Pakets und
    ausserhalb des EntityOS-Images.)
    """
    if not os.path.exists(ZUGAENGE_PFAD):
        raise RuntimeError(f"Tresordatei fehlt: {ZUGAENGE_PFAD}")
    for zeile in open(ZUGAENGE_PFAD, encoding="utf-8"):
        zeile = zeile.strip()
        if not zeile or zeile.startswith("#") or "=" not in zeile:
            continue
        k, v = zeile.split("=", 1)
        if k.strip() == name:
            v = v.strip().strip('"').strip("'")
            if not v:
                raise RuntimeError(f"{name} steht in {ZUGAENGE_PFAD}, ist aber leer.")
            return v
    raise RuntimeError(f"{name} steht nicht in {ZUGAENGE_PFAD}.")


NVIDIA_NIM_BASE_URL = os.environ.get("NVIDIA_NIM_BASE_URL", "https://integrate.api.nvidia.com/v1")
EMBEDDING_MODEL = "nvidia/nv-embedqa-e5-v5"
EMBEDDING_DIM = 1024

# GEMESSEN: 128 ist der Suesspunkt (siehe Kopf). NIM nimmt bis zu 259 Texte
# je Aufruf an, aber ungemessen jenseits von 128 -- hier bewusst am
# gemessenen Wert gedeckelt statt am theoretischen Maximum.
BATCH_SIZE = 128
MAX_RETRIES = 3
RETRY_BACKOFF_S = 1.5


def _client() -> "_http.Client":
    return _http.Client(timeout=60.0)


def _post_embeddings(inputs: List[str], input_type: str, model: str, api_key: str) -> dict:
    letzter = None
    for versuch in range(MAX_RETRIES):
        try:
            with _client() as c:
                r = c.post(
                    f"{NVIDIA_NIM_BASE_URL}/embeddings",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "input": inputs,
                        "input_type": input_type,
                        "encoding_format": "float",
                        "truncate": "END",
                    },
                )
            if r.status_code == 429:
                letzter = ConnectionError(f"NVIDIA NIM 429 (Kontingent): {r.text[:300]}")
                time.sleep(RETRY_BACKOFF_S * (2 ** versuch))
                continue
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001 -- Netzfehler jeder Art, gleich behandelt
            letzter = e
            time.sleep(RETRY_BACKOFF_S * (2 ** versuch))
    raise ConnectionError(f"NVIDIA NIM API Fehler nach {MAX_RETRIES} Versuchen: {letzter}")


def embed_batch(texts: List[str], input_type: str = "passage", model: str = None) -> List[List[float]]:
    """Embed mehrere Texte, IMMER in Haeppchen von BATCH_SIZE als EIN
    HTTP-Aufruf je Haeppchen -- das ist die gemessene Effizienzgrenze
    (siehe Modulkopf). Reihenfolge der Rueckgabe == Reihenfolge der Eingabe.

    input_type: 'passage' fuer zu indizierenden Text (Artikel), 'query' fuer
    Suchanfragen -- nv-embedqa-e5-v5 ist ein asymmetrisches Modell, NIM
    verlangt das Feld.
    """
    model = model or EMBEDDING_MODEL
    api_key = _schluessel("NVIDIA_NIM_API_KEY")
    ergebnis: List[List[float]] = [None] * len(texts)  # type: ignore[list-item]
    for start in range(0, len(texts), BATCH_SIZE):
        stueck = texts[start:start + BATCH_SIZE]
        stueck = [t[:8192] for t in stueck]
        data = _post_embeddings(stueck, input_type, model, api_key)
        if "data" not in data or len(data["data"]) != len(stueck):
            raise ValueError(f"NVIDIA NIM: erwartet {len(stueck)} Embeddings, bekam {len(data.get('data', []))}")
        # NIM gibt 'index' je Eintrag zurueck -- daran einsortieren statt
        # Reihenfolge zu unterstellen.
        for eintrag in data["data"]:
            ergebnis[start + eintrag["index"]] = eintrag["embedding"]
    return ergebnis


def embed_text(text: str, model: str = None, input_type: str = "query") -> List[float]:
    """Embed EINEN Text. Fuer viele Texte immer embed_batch() nutzen --
    ein Einzelaufruf je Text ist bei 9251 Artikeln 128x so teuer wie noetig."""
    return embed_batch([text], input_type=input_type, model=model)[0]


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = sum(a * a for a in vec1) ** 0.5
    norm2 = sum(b * b for b in vec2) ** 0.5
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


# ── Speicher: eigene Tabelle, kollidiert mit keiner der bestehenden 104 ──
# (geprueft 2026-08-18 gegen sqlite_master von /var/lib/clay/wiki.db).
TABELLE = "udb_nvidia_embedding"


def _ensure_tabelle(c) -> None:
    c.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABELLE} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artikel_id TEXT NOT NULL UNIQUE,
            modell TEXT NOT NULL,
            dim INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            erstellt_am TEXT NOT NULL DEFAULT (datetime('now'))
        )
    """)
    c.commit()


def in_unifieddb_speichern(artikel_id: str, embedding: List[float], c, modell: str = EMBEDDING_MODEL) -> None:
    """Embedding in UnifiedDB speichern (neue Tabelle, siehe TABELLE)."""
    _ensure_tabelle(c)
    c.execute(f"""
        INSERT INTO {TABELLE} (artikel_id, modell, dim, embedding_json, erstellt_am)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(artikel_id) DO UPDATE SET
            modell=excluded.modell, dim=excluded.dim,
            embedding_json=excluded.embedding_json, erstellt_am=excluded.erstellt_am
    """, (artikel_id, modell, len(embedding), json.dumps(embedding)))
    c.commit()


def batch_in_unifieddb_speichern(paare: List[tuple], c, modell: str = EMBEDDING_MODEL) -> int:
    """paare: Liste von (artikel_id, embedding). Eine Transaktion fuer alle."""
    _ensure_tabelle(c)
    c.executemany(f"""
        INSERT INTO {TABELLE} (artikel_id, modell, dim, embedding_json, erstellt_am)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(artikel_id) DO UPDATE SET
            modell=excluded.modell, dim=excluded.dim,
            embedding_json=excluded.embedding_json, erstellt_am=excluded.erstellt_am
    """, [(aid, modell, len(emb), json.dumps(emb)) for aid, emb in paare])
    c.commit()
    return len(paare)


def embedding_abrufen(artikel_id: str, c) -> List[float]:
    row = c.execute(
        f"SELECT embedding_json FROM {TABELLE} WHERE artikel_id = ?", (artikel_id,)
    ).fetchone()
    return json.loads(row[0]) if row else []


def alle_embeddings_abrufen(c) -> List[tuple]:
    rows = c.execute(f"SELECT artikel_id, embedding_json FROM {TABELLE}").fetchall()
    return [(row[0], json.loads(row[1])) for row in rows]


def vektor_suche(query: str, c, limit: int = 5) -> List[dict]:
    """Vektor-Similarity-Search mit NVIDIA-Embeddings gegen bereits
    gespeicherte Artikel-Embeddings (siehe embed_batch fuer den Aufbau)."""
    query_emb = embed_text(query, input_type="query")
    alle = alle_embeddings_abrufen(c)
    ergebnisse = []
    for artikel_id, emb in alle:
        if emb:
            sim = cosine_similarity(query_emb, emb)
            ergebnisse.append({"artikel_id": artikel_id, "similarity": sim})
    ergebnisse.sort(key=lambda x: x["similarity"], reverse=True)
    return ergebnisse[:limit]
