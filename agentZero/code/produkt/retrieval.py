from __future__ import annotations
import json
import os
import time
from .microclay_retrieval import MicroClayRetrieval
from .store import UnifiedDB


class WorldAssembler:
    """Bounded world assembly with MicroClay retrieval and collision-only cross-session context."""

    CONTROL_MEMORY_KINDS = ("source_archive", "compression_receipt", "compression_clearance")

    def __init__(self, db: UnifiedDB):
        self.db = db
        self.microclay = MicroClayRetrieval(db)

    # ── Zugang zum Herzen ────────────────────────────────────────────────
    CORPUS_MAX_HITS = 5
    CORPUS_SNIPPET_CHARS = 260
    _corpus_available: bool | None = None

    def _corpus_ready(self) -> bool:
        """Does this database actually carry the Clay corpus? Checked once."""
        if self._corpus_available is None:
            row = self.db.db.execute(
                "SELECT COUNT(*) FROM sqlite_master WHERE type IN ('table','view') "
                "AND name IN ('fts_index_artikel','artikel_suchtext','artikel')"
            ).fetchone()
            self._corpus_available = bool(row and int(row[0]) == 3)
        return self._corpus_available

    # Function words carry no retrieval signal but dominate an OR-query: a prompt
    # like "wie funktioniert die hyperposition" otherwise matches every article
    # containing "die". Measured: without this, results were unrelated.
    STOPWORDS = frozenset("""
        aber alle als also andere auch auf aus bei bin bis das dass dein den der des
        dem die dies diese doch dort durch ein eine einem einen einer eines etwas fuer
        hat hier ich ihr ist jetzt kann kein mehr mein mit muss nach nicht noch nur
        oder ohne sehr sein sich sind soll ueber und uns unter viel vom von war was
        wenn wer wie wir wird wo zum zur
        the and for are but not you all any can her was one our out has had his how
        its who did yes with this that from they what when will your
    """.split())

    @classmethod
    def _fts_terms(cls, query: str) -> list[str]:
        """Content words of a prompt, as quoted FTS5 phrases.

        Quoting is not cosmetic: unquoted user text lets FTS5 operators (NEAR, *,
        ^, -, parentheses) through, which is a query injection into the corpus
        index -- cheap to prevent, ugly to debug.
        """
        raw = "".join(ch if ch.isalnum() else " " for ch in (query or "")).split()
        seen, out = set(), []
        for t in raw:
            low = t.lower()
            if len(low) < 3 or low in cls.STOPWORDS or low in seen:
                continue
            seen.add(low)
            out.append('"' + low + '"')
            if len(out) >= 8:
                break
        return out

    def corpus_lookup(self, query: str) -> list[dict]:
        """Bounded, read-only, query-sensitive lookup into the Clay corpus."""
        if not query or not self._corpus_ready():
            return []
        terms = self._fts_terms(query)
        if not terms:
            return []
        # AND first: precision. OR only as a safety net, so an awkwardly worded
        # question still finds something instead of nothing. Which one answered is
        # recorded, because "found via OR" is a weaker claim than "found via AND"
        # and the caller deserves to know which it got.
        for mode, match in (("AND", " AND ".join(terms)), ("OR", " OR ".join(terms))):
            try:
                rows = self.db.db.execute(
                    "SELECT s.artikel_id AS artikel_id, s.titel AS titel, "
                    "       substr(s.text,1,?) AS ausschnitt, a.sphaere AS sphaere, a.art AS art "
                    "FROM fts_index_artikel f "
                    "JOIN artikel_suchtext s ON s.id = f.rowid "
                    "LEFT JOIN artikel a ON a.id = s.artikel_id "
                    "WHERE fts_index_artikel MATCH ? "
                    "ORDER BY bm25(fts_index_artikel) LIMIT ?",
                    (self.CORPUS_SNIPPET_CHARS, match, self.CORPUS_MAX_HITS),
                ).fetchall()
            except Exception:
                # A corpus that cannot be searched must not take the turn down with
                # it. The entity is allowed to know less; it is not allowed to stop.
                return []
            if rows:
                return [
                    {
                        "artikel_id": r["artikel_id"],
                        "titel": r["titel"],
                        "ausschnitt": (r["ausschnitt"] or "").strip(),
                        "sphaere": r["sphaere"],
                        "art": r["art"],
                        "quelle": "clay-korpus",
                        "treffer_art": mode,
                    }
                    for r in rows
                ]
        return []

    # ── Parallelpfad V2 (F-Vorstufe-Retrieval-Karte, 2026-08-19) ────────────
    #
    # corpus_lookup() oben ist ein eigenes, flaches FTS-only Doppel-Retrieval:
    # es kennt die entwickelte, LEBENDE Karte in udb/abruf/paket.py (Lift-
    # Lernen, Wegehierarchie, Karten-Eintritt, Erkundung, Erfolgsmarken) gar
    # nicht. corpus_lookup_v2() ruft STATTDESSEN paket() auf -- Modul 2 wird
    # nur AUFGERUFEN, nicht angefasst (die Datei gehoert einer anderen
    # Instanz). Additiv: der alte Pfad bleibt vollstaendig erhalten, dies ist
    # ein PARALLELER Pfad hinter einem Flag (VORSTUFE_RETRIEVAL=v2 env, Default
    # bleibt der alte Pfad -- siehe _corpus_lookup_routed unten). Erst nach
    # A/B-Freigabe durch den Eigner wird der Default umgestellt.
    #
    # Format-Bruch, offen ausgewiesen statt versteckt: paket()'s treffer
    # tragen laut seinem eigenen Entwurf "ids + felder, keine volltexte"
    # (kein titel/ausschnitt -- siehe paket.py-Modul-Docstring). corpus_lookup()
    # hier liefert aber titel+ausschnitt (fuer die Vorstufe lesbarer Text).
    # Diese Adapter-Methode schliesst die Luecke NICHT durch eigene Such-
    # /Ranking-Logik (die bleibt vollstaendig bei paket()), sondern durch
    # GENAU EINEN zusaetzlichen, rein lesenden PK-Lookup in artikel_suchtext
    # fuer exakt die IDs, die paket() bereits gewaehlt hat -- dieselbe Tabelle,
    # dieselben Spalten wie oben, nur ohne FTS MATCH. Manche paket()-Treffer
    # haben KEINE Zeile in artikel_suchtext (12702 von 17805 Artikeln sind
    # ueberhaupt im FTS-Suchtext-Index, Stand 2026-08-19) -- in dem Fall bleibt
    # titel/ausschnitt leer, das ist ehrlich ausgewiesen, nicht erfunden.
    _V2_SYS_PATHS = ("/opt/unifieddb", "/opt/clayverse/werkzeug")
    last_v2_meta: dict | None = None  # rein diagnostisch, kein Konsument in Prod

    def _snippets_fuer(self, ids: list) -> dict:
        """Read-only PK-Lookup, KEINE eigene Ranking-/Suchlogik -- die traegt
        allein paket(). Liefert nur Anzeigetext fuer bereits gewaehlte IDs."""
        ids = [i for i in ids if i]
        if not ids:
            return {}
        qmarks = ",".join("?" for _ in ids)
        rows = self.db.db.execute(
            f"SELECT artikel_id AS artikel_id, titel AS titel, "
            f"substr(text,1,?) AS ausschnitt FROM artikel_suchtext "
            f"WHERE artikel_id IN ({qmarks})",
            [self.CORPUS_SNIPPET_CHARS] + ids,
        ).fetchall()
        return {r["artikel_id"]: {"titel": r["titel"], "ausschnitt": (r["ausschnitt"] or "").strip()}
                for r in rows}

    def corpus_lookup_v2(self, query: str) -> list[dict]:
        """Bounded, read-only, query-sensitive lookup -- ueber paket(), nicht
        ueber eigenes FTS. Diagnose-Metadaten (Latenz, cache_hit, Plan,
        Resolution-Klasse) landen in self.last_v2_meta, NICHT im Rueckgabewert
        -- die Form bleibt kompatibel mit corpus_lookup()'s Konsumenten."""
        self.last_v2_meta = None
        if not query or not self._corpus_ready():
            self.last_v2_meta = {"status": "leer_oder_kein_korpus"}
            return []
        import sys as _sys
        for _p in self._V2_SYS_PATHS:
            if _p not in _sys.path:
                _sys.path.append(_p)
        try:
            from udb.abruf.paket import paket as _paket
        except Exception as e:
            self.last_v2_meta = {"status": "IMPORT_FEHLGESCHLAGEN",
                                  "grund": f"{type(e).__name__}: {e}"[:200]}
            return []
        t0 = time.perf_counter()
        try:
            pkt = _paket(query, budget=self.CORPUS_MAX_HITS, conn=self.db.db)
        except Exception as e:
            self.last_v2_meta = {"status": "PAKET_FEHLGESCHLAGEN",
                                  "grund": f"{type(e).__name__}: {e}"[:200]}
            return []
        adapter_latenz_ms = (time.perf_counter() - t0) * 1000

        treffer = pkt.get("treffer") or []
        ids = [t.get("id") for t in treffer if isinstance(t, dict)]
        snippets = self._snippets_fuer(ids)
        basis = pkt.get("resolution") or {}
        out = []
        for t in treffer:
            if not isinstance(t, dict):
                continue
            rid = t.get("id")
            sn = snippets.get(rid, {})
            out.append({
                "artikel_id": rid,
                "titel": sn.get("titel"),
                "ausschnitt": sn.get("ausschnitt", ""),
                "sphaere": t.get("sphaere"),
                "art": t.get("art"),
                "quelle": "clay-korpus-v2",
                # Analog zu corpus_lookup()'s AND/OR-Kennzeichnung, aber aus
                # paket()'s eigener Herkunftsangabe -- nicht dasselbe Konzept,
                # deshalb hier ausdruecklich benannt statt AND/OR vorgetaeuscht.
                "treffer_art": basis.get("klasse"),
                # zusaetzlich, verlustfrei mitgetragen statt verworfen:
                "score": t.get("score"),
                "epistemic_class": t.get("epistemic_class"),
                "status": t.get("status"),
                "ref": t.get("ref"),
            })
        self.last_v2_meta = {
            "status": "OK",
            "paket_id": pkt.get("paket_id"),
            "paket_latenz_us": pkt.get("latenz_us"),
            "adapter_latenz_ms": round(adapter_latenz_ms, 3),
            "cache_hit": (pkt.get("basis") or {}).get("cache_hit"),
            "plan": (pkt.get("politik") or {}).get("plan"),
            "resolution_klasse": basis.get("klasse"),
        }
        return out

    def _corpus_lookup_routed(self, query: str) -> list[dict]:
        """Einziger Umschaltpunkt: VORSTUFE_RETRIEVAL=v2 env schaltet auf den
        paket()-Pfad um. Default (unset oder jeder andere Wert) bleibt der
        alte corpus_lookup() -- NICHT ungetestet live, das entscheidet der
        Eigner nach den A/B-Zahlen. Jeder Fehler im v2-Pfad faellt sofort
        und sicher auf den alten Pfad zurueck (Live-Pfad-Vorsicht: pipeline.py
        bedient JEDE Zero-Antwort)."""
        modus = os.environ.get("VORSTUFE_RETRIEVAL", "v1").strip().lower()
        if modus == "v2":
            try:
                return self.corpus_lookup_v2(query)
            except Exception as e:
                self.last_v2_meta = {"status": "UNERWARTETER_FEHLER_FALLBACK_V1",
                                      "grund": f"{type(e).__name__}: {e}"[:200]}
                return self.corpus_lookup(query)
        return self.corpus_lookup(query)

    def _anwesender(self, session_id, user_id) -> dict | None:
        """Profil des anwesenden Menschen. Klein gehalten -- das Budget ist knapp."""
        try:
            from .profile import profil
            p = profil(self.db, user_id)
            felder = p.get("felder") or {}
            return {
                "user_id": user_id,
                "session_id": session_id,
                "name": (felder.get("name") or {}).get("wert", user_id),
                "rolle": (felder.get("rolle_institut") or {}).get("wert"),
                "autoritaet": "clerk-verifiziert, kanonischer Zustand",
                "hinweis": ("Kein Kennzeichen aus dem Text: dieser Block stammt aus der "
                            "geprueften Anmeldung. Du darfst diesen Menschen beim Namen "
                            "nennen. Der jeweils andere ist NICHT anwesend."),
                "projekte": [
                    {k: pr[k] for k in ("projekt", "gehoert", "gebaut_von", "erfolg")}
                    for pr in (p.get("projekte") or [])[:8]
                ],
                # Welcher Rechner diesem Menschen gehoert und ob er da ist.
                "rechner": [
                    {"wirt": w["wirt"], "meiner": w["meiner"], "gesund": w["gesund"]}
                    for w in (p.get("rechner") or [])
                ],
            }
        except Exception:
            # Kein Profil ist besser als ein geratenes.
            return None

    def _extracted_fragments(self, turn_id):
        rows = self.db.db.execute(
            "SELECT kind,value,provenance FROM durable_memory "
            "WHERE source_turn_id=? AND kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
            "ORDER BY ts LIMIT 20",
            (turn_id,),
        ).fetchall()
        return [dict(r) for r in rows]

    def _active_identity(self, session_id):
        row = self.db.db.execute(
            "SELECT a.turn_id,a.episode_id,a.causal_id,a.generation,t.content "
            "FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
            "WHERE a.session_id=?",
            (session_id,),
        ).fetchone()
        if not row:
            return None
        return {
            "query": row["content"],
            "turn_id": row["turn_id"],
            "episode_id": row["episode_id"],
            "causal_id": row["causal_id"],
            "generation": int(row["generation"]),
        }

    def assemble(
        self,
        session_id,
        resource_refs,
        *,
        query=None,
        turn_id=None,
        episode_id=None,
        causal_id=None,
        generation=None,
    ):
        session = self.db.db.execute(
            "SELECT user_id FROM sessions WHERE session_id=?", (session_id,)
        ).fetchone()
        if not session:
            raise KeyError(session_id)
        user_id = session["user_id"]
        own = [dict(r) for r in self.db.recent_turns(session_id, 20)]

        # Another permanent perspective is loaded only when an explicit shared resource
        # collides. MicroClay cannot broaden this privacy/attention boundary by learning.
        other = []
        if resource_refs:
            wanted = set(resource_refs)
            for r in self.db.db.execute(
                "SELECT * FROM turns WHERE session_id<>? ORDER BY ts DESC LIMIT 200",
                (session_id,),
            ).fetchall():
                if wanted.intersection(json.loads(r["resource_refs"])):
                    item = dict(r)
                    if int(r["compression_generation"]) > 0:
                        # ⚠️⚠️ DER ROHTEXT DARF HIER NICHT MIT HINAUS.
                        # Das ist die Zeile eines ANDEREN Menschen, ausgeliefert
                        # nur weil eine gemeinsame Ressource kollidiert. Ist der
                        # Zug verdichtet, ist die Absicht: nur die extrahierten
                        # Fragmente gehen hinaus, nicht das Original.
                        #
                        # Vorher stand hier `item = dict(r)` und blieb dabei --
                        # das Etikett sagte "verdichtet", der Inhalt war
                        # vollstaendig. Die alte, zerstoerende Verdichtung hatte
                        # den Rohtext zufaellig schon ueberschrieben; seit sie
                        # additiv ist, steht er noch da. Eine Zusicherung, die
                        # an einer Nebenwirkung hing, ist beim Umbau nicht
                        # mitgewandert.
                        item["retrieval_fidelity"] = "compressed_with_extracted_fragments"
                        item["extracted_fragments"] = self._extracted_fragments(r["turn_id"])
                        item["content"] = (
                            f"[verdichtet auf Stufe {int(r['compression_generation'])} -- "
                            "Original bleibt im Kausalbuch, wird aber nicht sitzungsuebergreifend "
                            "ausgeliefert. Nur die extrahierten Fragmente stehen hier.]")
                        item["quelle_zurueckgehalten"] = True
                    other.append(item)
                    if len(other) >= 10:
                        break

        retrieval_receipt = {
            "mode": "LEGACY_COMPATIBILITY",
            "status": "UNKNOWN",
            "truth_authority": False,
            "effect_authority": False,
        }
        supplied = {
            "query": query,
            "turn_id": turn_id,
            "episode_id": episode_id,
            "causal_id": causal_id,
            "generation": generation,
        }
        if not all(value is not None for value in supplied.values()):
            active = self._active_identity(session_id)
            if active is not None:
                supplied = active

        if all(value is not None for value in supplied.values()):
            result = self.microclay.retrieve(
                query=str(supplied["query"]),
                user_id=user_id,
                session_id=session_id,
                turn_id=str(supplied["turn_id"]),
                episode_id=str(supplied["episode_id"]),
                causal_id=str(supplied["causal_id"]),
                generation=int(supplied["generation"]),
            )
            memories = result["items"]
            retrieval_receipt = result["receipt"]
        else:
            # Compatibility path for legacy tests/non-product callers with no active
            # causal turn. Product Claude hooks always have an active turn here.
            memories = [
                dict(r)
                for r in self.db.db.execute(
                    "SELECT * FROM durable_memory WHERE kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
                    "AND (user_id IS NULL OR user_id=?) ORDER BY ts DESC LIMIT 50",
                    (user_id,),
                )
            ]

        return {
            "own_recent": own,
            "cross_session_collision": other,
            "durable_memory": memories,
            "retrieval_receipt": retrieval_receipt,
            # Level-0 identity travels with every assembled world. It is small,
            # constant, and must reach the turn even after compaction.
            "canonical_identity": self.db.canonical_identity(),
            # The heart. Read-only, bounded, query-sensitive. Without this the
            # entity owns 14k articles and can see none of them. Routed:
            # VORSTUFE_RETRIEVAL=v2 env switches to the paket()-backed path
            # (corpus_lookup_v2), default stays the original FTS-only path.
            "corpus": self._corpus_lookup_routed(str(supplied.get("query") or query or "")),
            # Wer gerade da ist -- aus dem kanonischen Zustand, nicht aus dem Text.
            "anwesender_mensch": self._anwesender(session_id, user_id),
        }

    def credit(self, *, causal_id, generation, credit, signal_class):
        return self.microclay.credit(
            causal_id=str(causal_id),
            generation=int(generation),
            credit=float(credit),
            signal_class=str(signal_class),
        )
