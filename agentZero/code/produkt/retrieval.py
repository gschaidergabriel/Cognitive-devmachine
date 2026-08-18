from __future__ import annotations
import json
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
            # entity owns 14k articles and can see none of them.
            "corpus": self.corpus_lookup(str(supplied.get("query") or query or "")),
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
