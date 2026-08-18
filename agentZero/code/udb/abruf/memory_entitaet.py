#!/usr/bin/env python3
"""udb/abruf/memory_entitaet.py — Mini-Entitaet fuer Memory-Ausgabe.

Verwaltet memory_tabelle (neue Tabelle, kollidiert mit keiner der
bestehenden 104 in wiki.db, geprueft 2026-08-18). Nutzt die schreibende/
lesende Standardverbindung des Hauses (udb.abruf.zustand) statt eigener
sqlite3.connect()-Aufrufe -- damit teilt sich diese Klasse busy_timeout und
Wiederholung mit den vier Dauerlaeufern, die dieselbe 3,5-GB-WAL-Datei
gleichzeitig beschreiben, statt sofort auf 'database is locked' zu laufen.
"""
from __future__ import annotations

from typing import List, Dict

from udb.abruf.zustand import verbindung, schreib_verbindung


class MemoryEntitaet:
    """Mini-Entitaet die Memory-Eintraege verwaltet und ausgibt."""

    def __init__(self, db_pfad: str):
        self.db_pfad = db_pfad
        self._ensure_memory_tabelle()

    def _ensure_memory_tabelle(self):
        c = schreib_verbindung(self.db_pfad)
        try:
            c.execute("""
                CREATE TABLE IF NOT EXISTS memory_tabelle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artikel_id TEXT NOT NULL,
                    memory_text TEXT NOT NULL,
                    quelle TEXT,
                    erstellt_am TEXT NOT NULL DEFAULT (datetime('now')),
                    priority REAL DEFAULT 1.0,
                    tag TEXT
                )
            """)
            c.execute("CREATE INDEX IF NOT EXISTS idx_memory_artikel ON memory_tabelle(artikel_id)")
            c.execute("CREATE INDEX IF NOT EXISTS idx_memory_tag ON memory_tabelle(tag)")
            c.commit()
        finally:
            c.close()

    def memory_hinzufuegen(self, user_id, artikel_id: str, memory_text: str,
                            quelle: str = None, priority: float = 1.0,
                            tag: str = None) -> bool:
        try:
            c = schreib_verbindung(self.db_pfad)
            try:
                c.execute("""
                    INSERT INTO memory_tabelle (artikel_id, memory_text, quelle, priority, tag, user_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (artikel_id, memory_text, quelle, priority, tag, user_id))
                c.commit()
            finally:
                c.close()
            return True
        except Exception as e:
            print(f"FEHLER Memory hinzufuegen: {e}")
            return False

    @staticmethod
    def _zeilen_zu_dicts(rows) -> List[Dict]:
        return [
            {"id": r[0], "artikel_id": r[1], "memory_text": r[2], "quelle": r[3],
             "erstellt_am": r[4], "priority": r[5], "tag": r[6]}
            for r in rows
        ]

    def memory_abrufen(self, artikel_id: str = None, tag: str = None, limit: int = 10) -> List[Dict]:
        try:
            c = verbindung(self.db_pfad)
            try:
                if artikel_id and tag:
                    rows = c.execute(
                        "SELECT * FROM memory_tabelle WHERE user_id = ? AND artikel_id = ? AND tag = ? "
                        "ORDER BY priority DESC, erstellt_am DESC LIMIT ?",
                        (artikel_id, tag, limit)).fetchall()
                elif artikel_id:
                    rows = c.execute(
                        "SELECT * FROM memory_tabelle WHERE artikel_id = ? "
                        "ORDER BY priority DESC, erstellt_am DESC LIMIT ?",
                        (artikel_id, limit)).fetchall()
                elif tag:
                    rows = c.execute(
                        "SELECT * FROM memory_tabelle WHERE tag = ? "
                        "ORDER BY priority DESC, erstellt_am DESC LIMIT ?",
                        (tag, limit)).fetchall()
                else:
                    rows = c.execute(
                        "SELECT * FROM memory_tabelle ORDER BY priority DESC, erstellt_am DESC LIMIT ?",
                        (limit,)).fetchall()
            finally:
                c.close()
            return self._zeilen_zu_dicts(rows)
        except Exception as e:
            print(f"FEHLER Memory abrufen: {e}")
            return []

    def memory_suche(self, user_id, suchbegriff: str, limit: int = 10) -> List[Dict]:
        try:
            c = verbindung(self.db_pfad)
            try:
                # user_id ZUERST in der Bedingung. Ohne sie sah jede Suche
                # alles -- gemessen: Andreas bekam Gabriels private Eintraege
                # woertlich zurueck. Die Tabelle konnte strukturell nicht
                # trennen, weil ihr die Spalte fehlte.
                rows = c.execute(
                    "SELECT * FROM memory_tabelle WHERE user_id = ? AND memory_text LIKE ? "
                    "ORDER BY priority DESC, erstellt_am DESC LIMIT ?",
                    (user_id, f"%{suchbegriff}%", limit)).fetchall()
            finally:
                c.close()
            return self._zeilen_zu_dicts(rows)
        except Exception as e:
            print(f"FEHLER Memory suche: {e}")
            return []

    def memory_loeschen(self, user_id, memory_id: int) -> bool:
        try:
            c = schreib_verbindung(self.db_pfad)
            try:
                # Auch hier user_id: eine blosse Nummer waere sonst ein
                # Loeschrecht auf fremde Erinnerungen, wenn man sie erraet.
                c.execute("DELETE FROM memory_tabelle WHERE id = ? AND user_id = ?",
                          (memory_id, user_id))
                c.commit()
            finally:
                c.close()
            return True
        except Exception as e:
            print(f"FEHLER Memory loeschen: {e}")
            return False

    def alle_memory_abrufen(self, limit: int = 50) -> List[Dict]:
        try:
            c = verbindung(self.db_pfad)
            try:
                rows = c.execute(
                    "SELECT * FROM memory_tabelle ORDER BY erstellt_am DESC LIMIT ?",
                    (limit,)).fetchall()
            finally:
                c.close()
            return self._zeilen_zu_dicts(rows)
        except Exception as e:
            print(f"FEHLER alle Memory abrufen: {e}")
            return []

    def memory_statistik(self) -> Dict:
        try:
            c = verbindung(self.db_pfad)
            try:
                total = c.execute("SELECT COUNT(*) FROM memory_tabelle").fetchone()[0]
                by_tag = c.execute(
                    "SELECT tag, COUNT(*) FROM memory_tabelle GROUP BY tag ORDER BY 2 DESC").fetchall()
                by_artikel = c.execute(
                    "SELECT artikel_id, COUNT(*) FROM memory_tabelle GROUP BY artikel_id "
                    "ORDER BY 2 DESC LIMIT 5").fetchall()
            finally:
                c.close()
            return {
                "total_memory": total,
                "by_tag": [{"tag": t, "anzahl": a} for t, a in by_tag],
                "top_artikel": [{"artikel_id": aid, "anzahl": a} for aid, a in by_artikel],
            }
        except Exception as e:
            print(f"FEHLER Memory statistik: {e}")
            return {"total_memory": 0, "by_tag": [], "top_artikel": []}

    def memory_priorisiere_neu(self, artikel_id: str, min_priority: float = 1.5) -> int:
        try:
            c = schreib_verbindung(self.db_pfad)
            try:
                cur = c.execute(
                    "UPDATE memory_tabelle SET priority = priority * 1.5 "
                    "WHERE artikel_id = ? AND priority < ?", (artikel_id, min_priority))
                updated = cur.rowcount
                c.commit()
            finally:
                c.close()
            return updated
        except Exception as e:
            print(f"FEHLER Memory priorisiere neu: {e}")
            return 0
