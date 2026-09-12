#!/usr/bin/env python3
"""grid_packet_bridge.py -- verbindet GRID (grid_autonomie.py) mit dem
Claude-Code-Terminal-Koordinator ueber das BEREITS EXISTIERENDE, getestete
Architect-Worker-Coordination-Protokoll aus ~/frankenstein-2.0
(workpackages/ARCHITECT_WORKER_COORDINATION_PROTOCOL.md +
tools/coordination/architect_packet.py), NICHT ueber einen neu erfundenen
Mechanismus.

Warum ueber dieses Protokoll und nicht direkt: die Autoritaets-Invariante
ist im Schema selbst erzwungen (validate_packet() wirft PacketError, wenn
mutation_authority/runtime_dispatch_authority/effect_authority/
credit_authority nicht exakt False sind -- das ist keine Konvention,
sondern eine harte Feldpruefung). Ein Paket kann Aufmerksamkeit/Prioritaet/
Stop-Defer-Hinweise setzen, es kann NIE selbst eine Werkzeugausfuehrung
auslösen. "ACK" heisst hier "Paket beobachtet und klassifiziert", nicht
"Anweisung befolgt" (Protokoll Abschnitt 8).

Zwei Funktionen fuer die zwei Seiten:
  - grid_schreibe_paket(...)  -- GRID (aus grid_autonomie.py) legt ein
    Steuerungspaket fuer den Terminal-Koordinator an.
  - pruefe_pakete(...)        -- der Koordinator (stern.py's Injektions-
    pfad, _f2wp1207_grid_rueckweg) liest offene, passende Pakete, schreibt
    ihre ACKs, und liefert den Text, der als additionalContext angehaengt
    wird. Bereits klassifizierte Nonces werden nicht erneut injiziert
    (ACK_ONLY_DUPLICATE).

Fail-silent wie der Rest von stern.py (§1.9.4): jeder Fehler hier lässt die
Injektion einfach leer, nie eine Ausnahme nach aussen.
"""
from __future__ import annotations

import importlib.util as _ilu
import json
import pathlib
import sqlite3
import sys
from typing import Any, Optional

F2_ROOT = pathlib.Path("/home/ai-core-node/frankenstein-2.0")
_AP_PATH = F2_ROOT / "tools" / "coordination" / "architect_packet.py"
PENDING_DIR = F2_ROOT / "coordination" / "architect_packets" / "pending"
ACKS_DIR = F2_ROOT / "coordination" / "architect_packets" / "acks"

# Fester Ziel-Selektor fuer "der Claude-Code-Terminal-Koordinator, egal
# welche Sitzung" -- Gabriel will eine generelle Kopplung, nicht eine
# einzelne Session-ID. Wer eine spezifische Sitzung ansprechen will, kann
# zusaetzlich runtime_subject_id im target setzen (Protokoll Abschnitt 7).
COORDINATOR_WORKER_ID = "claude-code-coordinator-terminal"

# Eigene, kleine Zustandsdatei fuer bereits gesehene Nonces -- die vom
# Protokoll selbst verlangte Idempotenz (Abschnitt 8, Punkt 5) braucht
# irgendeine Persistenz auf Empfaengerseite; das Protokoll schreibt nicht
# vor, WIE. sqlite passt zum Rest von stern.py.
_SEEN_DB = pathlib.Path.home() / ".claude" / "star" / "grid_packet_seen.db"


def _ap_module():
    if not _AP_PATH.is_file():
        return None
    spec = _ilu.spec_from_file_location("_architect_packet_bridge", _AP_PATH)
    mod = _ilu.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _seen_conn() -> sqlite3.Connection:
    _SEEN_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(_SEEN_DB))
    conn.execute(
        "CREATE TABLE IF NOT EXISTS seen_nonces ("
        " nonce TEXT PRIMARY KEY, packet_id TEXT, seen_at TEXT)"
    )
    return conn


def _seen_nonces() -> set[str]:
    try:
        with _seen_conn() as c:
            return {r[0] for r in c.execute("SELECT nonce FROM seen_nonces")}
    except Exception:
        return set()


def _mark_seen(nonce: str, packet_id: str) -> None:
    try:
        with _seen_conn() as c:
            c.execute(
                "INSERT OR IGNORE INTO seen_nonces (nonce, packet_id, seen_at) "
                "VALUES (?, ?, datetime('now'))", (nonce, packet_id))
    except Exception:
        pass


def grid_schreibe_paket(
    objective: str,
    *,
    action_class: str = "COORDINATION_ONLY",
    ttl_minutes: int = 30,
    priority: int = 50,
    constraints: Optional[list[str]] = None,
    evidence_refs: Optional[list[str]] = None,
    target: Optional[dict[str, Any]] = None,
    architect_id: str = "grid-autonomie",
) -> Optional[str]:
    """GRID legt ein Steuerungspaket fuer den Terminal-Koordinator an.
    Liefert den packet_id-String oder None bei Fehler. Schreibt NIE eine
    mutation/runtime/effect/credit-Autoritaet -- new_packet() im Protokoll-
    Helfer setzt diese Felder hart auf False, validate_packet() erzwingt
    das mechanisch."""
    ap = _ap_module()
    if ap is None:
        return None
    try:
        packet = ap.new_packet(
            target=target or {"worker_id": COORDINATOR_WORKER_ID},
            objective=objective,
            action_class=action_class,
            ttl_minutes=ttl_minutes,
            priority=priority,
            architect_id=architect_id,
            project="frankenstein-terminal-coordinator",
            constraints=constraints or [],
            evidence_refs=evidence_refs or [],
        )
        PENDING_DIR.mkdir(parents=True, exist_ok=True)
        out = PENDING_DIR / f"{packet['packet_id']}.json"
        out.write_text(json.dumps(packet, indent=2, sort_keys=True,
                                   ensure_ascii=False) + "\n", encoding="utf-8")
        return packet["packet_id"]
    except Exception:
        return None


def pruefe_pakete(worker_context: Optional[dict[str, Any]] = None) -> str:
    """Liest offene, passende, nicht-abgelaufene Pakete, schreibt ihre ACKs,
    liefert Injektionstext fuer additionalContext. Leerer String, wenn
    nichts Neues anliegt oder irgendetwas fehlschlaegt (fail-silent)."""
    ap = _ap_module()
    if ap is None or not PENDING_DIR.is_dir():
        return ""
    ctx = dict(worker_context or {})
    ctx.setdefault("worker_id", COORDINATOR_WORKER_ID)
    seen = _seen_nonces()
    zeilen: list[str] = []
    try:
        for pfad in sorted(PENDING_DIR.glob("*.json")):
            try:
                packet = json.loads(pfad.read_text(encoding="utf-8"))
            except Exception:
                continue
            disposition = ap.packet_disposition(packet, ctx, seen_nonces=seen)
            if disposition == "REJECT_SCHEMA_INVALID":
                continue
            if disposition in ("ACK_ONLY_DUPLICATE",):
                continue
            # ACK immer schreiben (auch bei REJECT_*), das Protokoll
            # verlangt vollstaendige ACK-Abdeckung (Abschnitt 17, Punkt 10).
            try:
                ack = ap.make_ack(
                    packet, ctx, reason=f"terminal-coordinator:{disposition}",
                    authority_head="claude-code-coordinator",
                )
                ack_dir = ACKS_DIR / packet["packet_id"]
                ack_dir.mkdir(parents=True, exist_ok=True)
                (ack_dir / f"{ctx['worker_id']}.{ack['ack_id']}.json").write_text(
                    json.dumps(ack, indent=2, sort_keys=True,
                               ensure_ascii=False) + "\n", encoding="utf-8")
            except Exception:
                pass
            _mark_seen(packet.get("nonce", ""), packet.get("packet_id", ""))
            if disposition != "APPLIED":
                continue
            obj = str(packet.get("objective") or "").strip()
            if not obj:
                continue
            cons = packet.get("constraints") or []
            cons_txt = ("; " + "; ".join(str(c) for c in cons[:12])) if cons else ""
            zeilen.append(
                f"GRID-Hinweis (Paket {packet['packet_id']}, "
                f"{packet.get('action_class')}, nur Empfehlung, keine "
                f"Ausfuehrungsautoritaet): {obj}{cons_txt}")
    except Exception:
        return ""
    if not zeilen:
        return ""
    return "\n".join(zeilen)


if __name__ == "__main__":
    # Smoke-Test: Paket anlegen, sofort einlesen, zweites Mal duplikatfrei.
    pid = grid_schreibe_paket(
        "Selbsttest grid_packet_bridge", action_class="STATUS",
        ttl_minutes=5, constraints=["nur Test, keine echte Anweisung"])
    print("angelegt:", pid)
    print("erster Abruf:", repr(pruefe_pakete()))
    print("zweiter Abruf (sollte leer sein, Duplikat):", repr(pruefe_pakete()))
