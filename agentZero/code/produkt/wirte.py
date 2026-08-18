"""Verbundene Rechner (Wirte) und ihre Zugehoerigkeit -- fuer Zero sichtbar."""
from __future__ import annotations

import json
import time
from pathlib import Path

from .store import UnifiedDB

# Wo der Clay-Unterbau die Herzschlaege der Zwillinge ablegt. Read-only fuer uns:
# geschrieben wird das von quorum.py auf der Clay-Seite.
ZWILLING_DIR = Path("/var/lib/clay/zwilling")

# ── Zugehoerigkeit: DEKLARIERT, nicht geraten ──────────────────────────────
# Ein Wirt, der hier nicht steht, bekommt gehoert_zu = None. Sichtbar unbekannt
# ist besser als per Namensaehnlichkeit falsch zugeordnet -- der Name eines
# Rechners ist kein Eigentumsnachweis.
WIRT_GEHOERT = {
    "ai-core-node-projekt-frankenstein": "gabriel",
    "ai-core-node": "gabriel",
    "andreas-MACO": "andreas",
    "andreas-maco": "andreas",
    "clayverse": None,   # der VPS selbst gehoert keinem der beiden Menschen
}

# Ab wann gilt ein Wirt als offline. Der Herzschlag kommt alle ~16 s; drei
# ausgefallene Takte plus Luft. Zu knapp und jeder Netzhaenger meldet einen
# Ausfall, zu weit und ein toter Rechner gilt minutenlang als da.
OFFLINE_NACH_SEKUNDEN = 90

SCHEMA = """
CREATE TABLE IF NOT EXISTS entityos_wirte(
  wirt TEXT PRIMARY KEY,
  gehoert_zu TEXT,
  erste_sichtung REAL NOT NULL,
  zuletzt_gesehen REAL NOT NULL,
  generation INTEGER,
  gesund INTEGER NOT NULL DEFAULT 0,
  boot_id TEXT,
  module TEXT NOT NULL DEFAULT '{}',
  quelle TEXT NOT NULL DEFAULT 'herzschlag'
);
"""


def _sicherstellen(db: UnifiedDB) -> None:
    db.db.executescript(SCHEMA)


def aufnehmen(db: UnifiedDB) -> dict:
    """Herzschlagdateien einlesen und in die UnifiedDB heben.

    Ueberschreibt je Wirt eine Zeile -- die Historie steckt bewusst NICHT hier,
    sondern in den Kartenaufnahmen des Exports. Diese Tabelle beantwortet eine
    Gegenwartsfrage: wer ist gerade da.
    """
    _sicherstellen(db)
    jetzt = time.time()
    gesehen = 0
    if ZWILLING_DIR.is_dir():
        for datei in sorted(ZWILLING_DIR.glob("*.json")):
            try:
                d = json.loads(datei.read_text(encoding="utf-8"))
            except Exception:
                continue
            wirt = str(d.get("zwilling") or datei.stem)
            with db.tx() as sql:
                sql.execute(
                    "INSERT INTO entityos_wirte(wirt,gehoert_zu,erste_sichtung,zuletzt_gesehen,"
                    "generation,gesund,boot_id,module) VALUES(?,?,?,?,?,?,?,?) "
                    "ON CONFLICT(wirt) DO UPDATE SET zuletzt_gesehen=excluded.zuletzt_gesehen,"
                    "generation=excluded.generation,gesund=excluded.gesund,"
                    "boot_id=excluded.boot_id,module=excluded.module,gehoert_zu=excluded.gehoert_zu",
                    (wirt, WIRT_GEHOERT.get(wirt), jetzt, datei.stat().st_mtime,
                     int(d.get("generation") or 0), 1 if d.get("gesund") else 0,
                     str(d.get("boot_id") or ""), json.dumps(d.get("module") or {}, sort_keys=True)),
                )
            gesehen += 1
    return {"eingelesen": gesehen, "verzeichnis": str(ZWILLING_DIR)}


def verbundene_systeme(db: UnifiedDB) -> list[dict]:
    """Was die Mistral-Vorstufe braucht: wer ist verbunden, wem gehoert er, ist er online.

    `kognitive_module` wird bewusst mitgeliefert: der Herzschlag meldet heute
    eine LEERE Liste. Ein Wirt kann also online und gesund sein und trotzdem
    nichts koennen -- das ist ein Unterschied, den die Vorstufe sehen muss,
    sonst plant sie Arbeit auf einem Rechner, der nur winkt.
    """
    _sicherstellen(db)
    jetzt = time.time()
    aus = []
    for r in db.db.execute(
        "SELECT wirt,gehoert_zu,zuletzt_gesehen,generation,gesund,module "
        "FROM entityos_wirte ORDER BY wirt"
    ):
        alter = jetzt - float(r["zuletzt_gesehen"])
        module = {}
        try:
            module = json.loads(r["module"] or "{}")
        except Exception:
            pass
        aus.append({
            "wirt": r["wirt"],
            "gehoert_zu": r["gehoert_zu"],          # None = bewusst nicht zugeordnet
            "online": alter <= OFFLINE_NACH_SEKUNDEN,
            "zuletzt_gesehen_vor_s": round(alter, 1),
            "generation": r["generation"],
            "gesund": bool(r["gesund"]),
            "kognitive_module": module.get("kognitive_module_gebaut", []),
            "hinweis": ("Zugehoerigkeit sagt, WEM der Rechner gehoert -- nicht, wo gearbeitet "
                        "werden darf."),
        })
    return aus
