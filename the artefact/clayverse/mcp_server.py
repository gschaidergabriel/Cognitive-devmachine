from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from .autonomy import AUTONOMY_TURN_SOURCE, AutonomyController, CompletionNotVerified
from .autonomy_context import bounded_autonomy_context

# UnifiedDB (udb/abruf/*: NVIDIA embeddings, Neuronpedia, memory-entity) lives
# outside this image at /opt/unifieddb (own git repo, read-only bind mount --
# see compose.yaml). Guarded: absent in unit-test/dev contexts that don't
# mount it, in which case udb_* tools below fail closed with a clear error
# instead of raising at import time and taking the whole MCP server down.
_UDB_ROOT = os.environ.get("UDB_ROOT", "/opt/unifieddb")
if _UDB_ROOT not in sys.path and os.path.isdir(_UDB_ROOT):
    sys.path.insert(0, _UDB_ROOT)


class BridgeStateError(RuntimeError):
    pass


class ClayVerseEffectBridge:
    """Stdio MCP for effects only; turns are owned deterministically by ClayVerse lifecycle."""

    def __init__(self, lifecycle):
        self.lifecycle = lifecycle
        self.db = lifecycle.db
        self.user_id = lifecycle.user_id
        self.session_id = lifecycle.session_id
        self.autonomy = AutonomyController(self.db)

    @classmethod
    def from_env(cls):
        from .entityos_bridge import EntityOSBridge
        from .identity import IdentityRouter
        from .store import UnifiedDB, resolve_db_path
        from .turn_lifecycle import TurnLifecycle

        root = Path(os.environ.get("CLAYVERSE_STATE_ROOT", "/var/lib/clayverse"))
        db = UnifiedDB(resolve_db_path(root))
        IdentityRouter(db, {})
        user_id = os.environ.get("CLAYVERSE_USER_ID", "").strip()
        session_id = os.environ.get("CLAYVERSE_SESSION_ID", "").strip()

        entityos = None
        enable_exec = os.environ.get("CLAYVERSE_ENABLE_ENTITYOS_EXEC", "0") == "1"
        path = os.environ.get("CLAYVERSE_ENTITYOS_PATH", "").strip()
        sha256 = os.environ.get("CLAYVERSE_ENTITYOS_SHA256", "").strip()
        if enable_exec:
            if not path or not sha256 or not os.path.isabs(path):
                db.close()
                raise BridgeStateError("EntityOS execution enabled without complete digest binding")
            entityos = EntityOSBridge(path=path, sha256=sha256)
            entityos.verify()
        return cls(TurnLifecycle(db, user_id, session_id, entityos_bridge=entityos))

    def _active_autonomy_identity(self) -> tuple[str, str] | None:
        with self.db.tx() as db:
            row = db.execute(
                "SELECT t.provenance FROM active_turns a "
                "JOIN turns t ON t.turn_id=a.turn_id "
                "WHERE a.session_id=? AND a.user_id=?",
                (self.session_id, self.user_id),
            ).fetchone()
            if row is None:
                return None
            try:
                provenance = self.autonomy._loads(row["provenance"] or "{}")
            except Exception as exc:
                raise BridgeStateError("active turn provenance malformed") from exc
            if provenance.get("source") != AUTONOMY_TURN_SOURCE:
                return None
            goal_id = provenance.get("goal_id")
            step_id = provenance.get("autonomy_step_id")
            if not isinstance(goal_id, str) or not goal_id or not isinstance(step_id, str) or not step_id:
                raise BridgeStateError("autonomous active turn identity missing")
            return goal_id, step_id

    def _admitted_autonomy_effect(self, goal_id: str, step_id: str) -> tuple[dict, dict]:
        goal_id = str(goal_id).strip()
        step_id = str(step_id).strip()
        if not goal_id or not step_id or len(goal_id) > 256 or len(step_id) > 256 or "\x00" in goal_id or "\x00" in step_id:
            raise ValueError("invalid autonomy goal/step identity")
        with self.db.tx() as db:
            _state, goal = self.autonomy._goal(db, goal_id)
            step = goal.get("current_step")
            if (
                not isinstance(step, dict)
                or step.get("step_id") != step_id
                or step.get("kind") != "effect"
                or step.get("status") != "ADMITTED"
                or not isinstance(step.get("effect"), dict)
            ):
                raise BridgeStateError("autonomy effect step is not exactly admitted")
            row = db.execute(
                "SELECT a.turn_id,a.episode_id,a.causal_id,a.generation,a.user_id,"
                "t.session_id AS turn_session_id,t.user_id AS turn_user_id,t.provenance "
                "FROM active_turns a JOIN turns t ON t.turn_id=a.turn_id "
                "WHERE a.session_id=? AND a.user_id=?",
                (self.session_id, self.user_id),
            ).fetchone()
            if row is None:
                raise BridgeStateError("no active autonomous turn")
            try:
                provenance = self.autonomy._loads(row["provenance"] or "{}")
                entity_generation = int(provenance.get("entity_generation"))
                session_generation = int(provenance.get("session_generation"))
            except Exception as exc:
                raise BridgeStateError("autonomous turn provenance malformed") from exc
            if (
                provenance.get("source") != AUTONOMY_TURN_SOURCE
                or provenance.get("goal_id") != goal_id
                or provenance.get("autonomy_step_id") != step_id
                or provenance.get("causal_id") != row["causal_id"]
                or row["turn_session_id"] != self.session_id
                or row["turn_user_id"] != self.user_id
                or int(row["generation"]) != int(goal["generation"])
                or entity_generation != int(goal["generation"])
                or session_generation != int(goal["generation"])
            ):
                raise PermissionError("active turn is not the exact admitted autonomy goal step")
            return dict(step["effect"]), {
                "turn_id": row["turn_id"],
                "episode_id": row["episode_id"],
                "causal_id": row["causal_id"],
                "generation": int(row["generation"]),
            }

    def _prior_autonomy_effect(self, goal_id: str, step_id: str, current_episode_id: str):
        """Find one exact prior effect for this durable goal/step, or fail closed.

        The prior receipt remains owned by UnifiedDB/EffectJournal. This helper only finds
        candidates; AutonomyController performs the authoritative target/argv/generation/
        causal-provenance checks before the receipt can affect goal state.
        """
        rows = self.db.db.execute(
            "SELECT e.effect_id,e.status,e.outcome,t.provenance "
            "FROM effects e "
            "JOIN workspace_episodes w ON w.episode_id=e.episode_id "
            "JOIN turns t ON t.turn_id=w.observation_turn_id "
            "WHERE w.session_id=? AND e.episode_id<>? AND t.provenance LIKE ? "
            "ORDER BY e.ts,e.effect_id",
            (self.session_id, current_episode_id, f"%{AUTONOMY_TURN_SOURCE}%"),
        ).fetchall()
        matches = []
        for row in rows:
            try:
                provenance = self.autonomy._loads(row["provenance"] or "{}")
            except Exception as exc:
                raise BridgeStateError("prior autonomous effect provenance malformed") from exc
            if provenance.get("source") != AUTONOMY_TURN_SOURCE:
                continue
            if provenance.get("goal_id") != goal_id or provenance.get("autonomy_step_id") != step_id:
                continue
            matches.append(row)
        if len(matches) > 1:
            raise BridgeStateError("multiple prior effects exist for one autonomous goal step")
        return matches[0] if matches else None

    def _maybe_complete_goal(self, goal_id: str, autonomy_result: dict) -> dict | None:
        """Apply only the existing canonical completion contract immediately after verified effect evidence."""
        if not bool(autonomy_result.get("verified")):
            return None
        try:
            return self.autonomy.verify_completion(goal_id)
        except CompletionNotVerified:
            return None

    def request_effect(self, capability: str, target: str, argv: list[str] | None = None) -> dict:
        if self._active_autonomy_identity() is not None:
            raise PermissionError("autonomous turns must dispatch the exact admitted step through request_autonomy_effect")
        if capability not in {"entityos.exec", "state.noop"}:
            raise PermissionError("capability denied")
        if not isinstance(target, str) or not target or len(target) > 2048 or "\x00" in target:
            raise ValueError("invalid effect target")
        if capability == "entityos.exec":
            if not isinstance(argv, list) or not argv or len(argv) > 128:
                raise ValueError("entityos.exec requires bounded argv")
            if any(not isinstance(x, str) or not x or len(x) > 8192 or "\x00" in x for x in argv):
                raise ValueError("invalid effect argv")
        elif argv not in (None, []):
            raise ValueError("state.noop does not accept argv")
        else:
            argv = None
        result = self.lifecycle.request_effect(capability, target, argv)
        result["boundary"] = "ClayVerse EffectGate -> EntityOS" if capability == "entityos.exec" else "ClayVerse EffectGate"
        return result

    def request_autonomy_effect(self, goal_id: str, step_id: str) -> dict:
        """Dispatch stored intent or reconcile exact prior evidence without re-execution."""
        effect, binding = self._admitted_autonomy_effect(goal_id, step_id)
        prior = self._prior_autonomy_effect(goal_id, step_id, binding["episode_id"])
        if prior is not None:
            if prior["status"] == "PENDING":
                raise BridgeStateError("prior autonomous effect is pending; recovery required before retry")
            autonomy_result = self.autonomy.record_effect_result(
                goal_id,
                step_id,
                prior["effect_id"],
                expected_generation=binding["generation"],
            )
            completion = self._maybe_complete_goal(goal_id, autonomy_result)
            try:
                outcome = self.autonomy._loads(prior["outcome"] or "{}")
            except Exception as exc:
                raise BridgeStateError("prior autonomous effect outcome malformed") from exc
            return {
                "effect_id": prior["effect_id"],
                "causal_id": self.lifecycle.effects.causal_for_effect(prior["effect_id"]),
                "verified": bool(autonomy_result["verified"]),
                "outcome": outcome,
                "autonomy": autonomy_result,
                "autonomy_completion": completion,
                "autonomy_binding": binding,
                "reconciled_prior_effect": True,
                "boundary": "AutonomyController -> existing EffectJournal receipt; no new effect execution",
            }

        result = self.lifecycle.request_effect(effect["capability"], effect["target"], effect.get("argv"))
        effect_id = result.get("effect_id")
        if not isinstance(effect_id, str) or not effect_id:
            raise BridgeStateError("canonical lifecycle returned no effect identity")
        autonomy_result = self.autonomy.record_effect_result(goal_id, step_id, effect_id)
        completion = self._maybe_complete_goal(goal_id, autonomy_result)
        result["autonomy"] = autonomy_result
        result["autonomy_completion"] = completion
        result["autonomy_binding"] = binding
        result["reconciled_prior_effect"] = False
        result["boundary"] = (
            "AutonomyController -> ClayVerse EffectGate -> EntityOS"
            if effect["capability"] == "entityos.exec"
            else "AutonomyController -> ClayVerse EffectGate"
        )
        return result

    # ── UnifiedDB (N7): embeddings / neuronpedia / memory ──────────────────
    # Deliberately NOT routed through AutonomyController/EffectJournal --
    # these write only to their own new tables (udb_nvidia_embedding,
    # forschung_neuropedia, memory_tabelle), never to the turn/effect ledger,
    # so they stay outside clayverse/store.py + turn_lifecycle.py ownership.
    def udb_embedding_search(self, query: str, limit: int = 5) -> dict:
        from udb.abruf.nvidia_embedding import vektor_suche
        from udb.abruf.zustand import verbindung
        if not isinstance(query, str) or not query.strip():
            raise ValueError("query darf nicht leer sein")
        limit = max(1, min(int(limit), 50))
        c = verbindung(os.environ.get("CLAYVERSE_DB_PATH", "/var/lib/clay/wiki.db"))
        try:
            ergebnisse = vektor_suche(query, c, limit=limit)
        finally:
            c.close()
        return {"query": query, "ergebnisse": ergebnisse}

    def udb_embedding_store(self, artikel_id: str, text: str) -> dict:
        from udb.abruf.nvidia_embedding import embed_text, in_unifieddb_speichern, EMBEDDING_MODEL
        from udb.abruf.zustand import schreib_verbindung
        if not isinstance(artikel_id, str) or not artikel_id.strip():
            raise ValueError("artikel_id darf nicht leer sein")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text darf nicht leer sein")
        emb = embed_text(text, input_type="passage")
        c = schreib_verbindung(os.environ.get("CLAYVERSE_DB_PATH", "/var/lib/clay/wiki.db"))
        try:
            in_unifieddb_speichern(artikel_id, emb, c, modell=EMBEDDING_MODEL)
        finally:
            c.close()
        return {"artikel_id": artikel_id, "dimension": len(emb), "modell": EMBEDDING_MODEL}

    def udb_neuropedia_activation(self, modell: str, source: str, index: str) -> dict:
        from udb.abruf.neuropedia import aktivierung_abrufen, fehlt_schluessel
        if fehlt_schluessel():
            return {"error": "NEUROPEDIA_API_KEY fehlt in der Tresordatei -- Aufruf nicht moeglich"}
        a = aktivierung_abrufen(modell, source, str(index))
        return {
            "modell": a.model_id, "source": a.layer, "index": a.index,
            "tokens": a.tokens, "aktivierungen": a.activations,
            "max_aktivierung": a.max_value,
            "was_gemessen": f"oeffentliches Forschungsmodell {a.model_id} (Neuronpedia) -- NICHT Zero selbst",
        }

    def udb_memory_add(self, artikel_id: str, text: str, tag: str = "", quelle: str = "") -> dict:
        from udb.abruf.memory_entitaet import MemoryEntitaet
        if not isinstance(text, str) or not text.strip():
            raise ValueError("text darf nicht leer sein")
        me = MemoryEntitaet(os.environ.get("CLAYVERSE_DB_PATH", "/var/lib/clay/wiki.db"))
        # self.user_id kommt aus dem verifizierten Clerk-Zustand, NICHT aus einem
        # Feld, das das Modell fuellen koennte. Sonst waere die Trennung eine Bitte.
        ok = me.memory_hinzufuegen(self.user_id, artikel_id or "zero", text, quelle=quelle or None, tag=tag or None)
        return {"ok": ok, "artikel_id": artikel_id or "zero", "tag": tag or None}

    def udb_memory_search(self, suchbegriff: str, limit: int = 10) -> dict:
        from udb.abruf.memory_entitaet import MemoryEntitaet
        me = MemoryEntitaet(os.environ.get("CLAYVERSE_DB_PATH", "/var/lib/clay/wiki.db"))
        return {"suchbegriff": suchbegriff, "gehoert_zu": self.user_id,
                "ergebnisse": me.memory_suche(self.user_id, suchbegriff, limit=max(1, min(int(limit), 50)))}

    # ── Menschen: wer ist da, wem gehoert was ─────────────────────────────

    def menschen_profil(self) -> dict:
        """Profil des ANWESENDEN Menschen. Kein Argument -- der Mensch ist kein Parameter.

        Ein user_id-Argument waere ein Feld, das das Modell fuellt. Dann waere
        die Trennung der beiden Menschen eine Bitte statt einer Eigenschaft.
        """
        from . import profile as _profile
        from . import wirte as _wirte
        from . import artikel_zuordnung as _az
        p = _profile.profil(self.db, self.user_id)
        try:
            p["rechner"] = [
                {"wirt": w.get("wirt"), "gehoert_zu": w.get("gehoert_zu"),
                 "meiner": w.get("gehoert_zu") == self.user_id,
                 "online": w.get("online"),
                 # Nie nur true/false: wie alt der Befund ist und woher er kommt.
                 # Ohne das behauptet "online" eine Gegenwart, die die DB-Zeile
                 # allein (Stand seit Dienststart) nicht mehr belegen kann.
                 "zuletzt_gesehen_vor_s": w.get("zuletzt_gesehen_vor_s"),
                 "beleg": w.get("beleg")}
                for w in _wirte.verbundene_systeme(self.db)
            ]
        except Exception as e:
            p["rechner_fehler"] = f"{type(e).__name__}: {e}"
        try:
            p["wiki_bestand"] = _az.bestand(self.db, self.user_id)
        except Exception as e:
            p["wiki_bestand_fehler"] = f"{type(e).__name__}: {e}"
        try:
            from . import erfolge as _erfolge
            # Beide Haelften oder keine: eine Bilanz, die nur Gelungenes fuehrt,
            # ist ein Werbeblatt -- und hier waere sie ausserdem ein falsches Bild
            # davon, wie dieses System kaputtgeht.
            p["bilanz"] = _erfolge.bilanz(self.db, self.user_id)
        except Exception as e:
            p["bilanz_fehler"] = f"{type(e).__name__}: {e}"
        p["gelesen_fuer"] = self.user_id
        return p

    def wiki_zuordnung(self, projekt: str = "") -> dict:
        """Welcher Teil des Wikis wem zugerechnet wird. Zahlen und Zugehoerigkeit, nie Text.

        Fuer beide Menschen einsehbar: das ist eine Aussage ueber das gemeinsame
        Archiv, kein Blick in fremde Inhalte.
        """
        try:
            self.db.db.execute("SELECT 1 FROM entityos_artikel_zuordnung LIMIT 1")
        except Exception:
            return {"stand": "NOCH_NICHT_ZUGEORDNET",
                    "hinweis": "Tabelle entityos_artikel_zuordnung existiert nicht. "
                               "Sage das, statt zu schaetzen."}
        verteilung = {r["gehoert"]: r["n"] for r in self.db.db.execute(
            "SELECT gehoert, COUNT(*) n FROM entityos_artikel_zuordnung GROUP BY gehoert")}
        gruende = [{"grund": r["grund"], "anzahl": r["n"], "sicherheit": r["s"]}
                   for r in self.db.db.execute(
                       "SELECT grund, COUNT(*) n, MAX(sicherheit) s FROM entityos_artikel_zuordnung "
                       "GROUP BY grund ORDER BY n DESC LIMIT 12")]
        antwort = {
            "artikel_gesamt": sum(verteilung.values()),
            "verteilung": verteilung,
            "gruende": gruende,
            "anwesender_mensch": self.user_id,
            "regel": ("Zugehoerigkeit kommt aus projekt/sphaere, NIE aus dem Bearbeiter. "
                      "501 Artikel aus Andreas' Bestand tragen Gabriel als Bearbeiter -- "
                      "Urheberschaft ist nicht Zugehoerigkeit. 'unbekannt' heisst: kein "
                      "Signal vorhanden, es wurde bewusst nicht geraten."),
        }
        if projekt:
            antwort["projekt"] = projekt
            antwort["projekt_verteilung"] = {r["gehoert"]: r["n"] for r in self.db.db.execute(
                "SELECT z.gehoert, COUNT(*) n FROM entityos_artikel_zuordnung z "
                "JOIN artikel a ON a.id=z.artikel_id WHERE a.projekt=? GROUP BY z.gehoert",
                (projekt,))}
        return antwort

    def lagebild(self) -> dict:
        """Zeros Blick auf sein eigenes Haus: die eigene andere Sitzung, ob die
        Autonomietakte liefen, ob der Korpus gewachsen ist, ob die Abrufkarte
        frisch ist, und was zuletzt fehlgeschlagen ist. Kein Argument -- wie
        menschen_profil() ist der anwesende Mensch kein Parameter, sonst waere
        die Grenze zwischen den zwei Menschen eine Bitte statt einer Eigenschaft.
        """
        from . import lagebild as _lagebild
        return _lagebild.erheben(self.db, self.user_id, self.session_id)

    # ── Der Raum: vier Plaetze, eine Entitaet ─────────────────────────────
    #
    # Alle vier Sitzungen sind DASSELBE Wesen und sitzen im selben Raum. Sie
    # sehen einander bei der Arbeit und weichen einander aus. Der Mensch und
    # der Platz kommen aus dem verifizierten Zustand -- nie aus einem Argument,
    # sonst koennte sich ein Platz als ein anderer ausgeben.

    def _mein_platz(self) -> int:
        rest = str(self.session_id).split(":")
        return int(rest[2]) if len(rest) > 2 and rest[2].isdigit() else 1

    def raum_sehen(self) -> dict:
        from . import raum as _raum
        return _raum.sehen(self.db, ich=self.session_id)

    def raum_sagen(self, was: str, womit: str = "", zustand: str = "arbeitet") -> dict:
        from . import raum as _raum
        # Die Kollisionspruefung sitzt in raum.sagen() selbst -- hier waere sie
        # nur fuer Zero wirksam gewesen, nicht fuer Takte und Skripte.
        return _raum.sagen(self.db, session_id=self.session_id, mensch=self.user_id,
                           platz=self._mein_platz(), was=was, womit=womit, zustand=zustand)

    def raum_rufen(self, text: str) -> dict:
        from . import raum as _raum
        return _raum.rufen(self.db, session_id=self.session_id, text=text)

    def raum_frei(self) -> dict:
        from . import raum as _raum
        return _raum.frei(self.db, session_id=self.session_id)

    # ── Arbeitspakete: Zero denkt und schnuert, es fuehrt nicht aus ───────

    def paket_schnueren(self, auftrag: str, womit: str = "", warum: str = "") -> dict:
        from . import arbeitspaket as _ap
        return _ap.schnueren(self.db, besteller=self.user_id, session_id=self.session_id,
                             auftrag=auftrag, womit=womit, warum=warum)

    def paket_lage(self) -> dict:
        from . import arbeitspaket as _ap
        return _ap.lage(self.db, besteller=self.user_id)

    # ── Bahnen: Zero fragt nach einer Faehigkeit, nie nach einem Anbieter ──
    def bahn_faehigkeit(self, faehigkeit: str, auftrag: str, system: str = "") -> dict:
        from .bahnen import Bahnrouter, BahnErschoepft
        erlaubt = {"kondensieren", "zweitmeinung", "schema_antwort", "sphaere_einordnung",
                   "websuche_erdung", "langer_kontext", "umsortieren_treffer"}
        if faehigkeit not in erlaubt:
            raise ValueError(f"unbekannte Faehigkeit. erlaubt: {sorted(erlaubt)}")
        if not isinstance(auftrag, str) or not auftrag.strip():
            raise ValueError("auftrag darf nicht leer sein")
        r = Bahnrouter(self.db)
        try:
            e = r.rufe(faehigkeit, auftrag[:20000], system=system or None)
        except BahnErschoepft as ex:
            # Ablehnung mit Grund, kein stiller Abstieg. Zero soll wissen, dass
            # es die Faehigkeit heute NICHT hat, statt eine schlechtere Antwort
            # fuer die bestellte zu halten.
            return {"erfuellt": False, "grund": str(ex), "faehigkeit": faehigkeit}
        return {"erfuellt": True, "faehigkeit": faehigkeit, "text": e["text"],
                "bahn": e["bahn"], "modell": e["modell"], "ms": e["ms"],
                "heute_benutzt": e["benutzt_heute"], "deckel": e["deckel"]}

    def bahn_lage(self) -> dict:
        from .bahnen import Bahnrouter
        return {"verbrauch_heute": Bahnrouter(self.db).lage()}

    def session_state(self) -> dict:
        active = self.lifecycle.active()
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "generation": self.db.session_generation(self.session_id),
            "active_turn": {
                "turn_id": active["turn_id"],
                "episode_id": active["episode_id"],
                "causal_id": active["causal_id"],
                "generation": int(active["generation"]),
                "effect_id": active["effect_id"],
            } if active else None,
            "autonomy": bounded_autonomy_context(self.db, self.user_id),
            "capabilities": self.lifecycle.effects.available_capabilities(),
            "entityos_execution_enabled": self.lifecycle.effects.entityos_bridge is not None,
            "turn_ingestion": "automatic_claude_hooks",
        }


def main() -> None:
    from mcp.server.mcpserver import MCPServer
    from mcp.types import ToolAnnotations

    bridge = ClayVerseEffectBridge.from_env()
    mcp = MCPServer(
        "EntityOS",
        instructions=(
            "UserPromptSubmit and Stop hooks own interactive turn ingestion/context/completion automatically. "
            "Use request_effect only for ordinary real/state-changing actions. "
            "Use request_autonomy_effect only for an already-admitted durable autonomy effect step so exact goal/step/turn/episode/causal identity remains bound. "
            "On retry, exact prior final evidence is reconciled instead of re-executed. "
            "Verified autonomy effect evidence is immediately checked against the existing canonical completion contract before another planning step may replace the current effect binding. "
            "Never bypass EffectGate with host execution and never claim success without a verified returned outcome."
        ),
    )
    ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
    effectful = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=True)

    @mcp.tool(annotations=effectful)
    def request_effect(capability: str, target: str, argv: list[str] | None = None) -> dict:
        return bridge.request_effect(capability, target, argv)

    @mcp.tool(annotations=effectful)
    def request_autonomy_effect(goal_id: str, step_id: str) -> dict:
        return bridge.request_autonomy_effect(goal_id, step_id)

    @mcp.tool(annotations=ro)
    def session_state() -> dict:
        return bridge.session_state()

    udb_ro = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=True)
    udb_write = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=True, openWorldHint=True)

    @mcp.tool(annotations=udb_ro)
    def udb_embedding_search(query: str, limit: int = 5) -> dict:
        """Semantische Suche ueber bereits eingebettete Clay-Artikel (NVIDIA nv-embedqa-e5-v5, 1024 dim)."""
        return bridge.udb_embedding_search(query, limit)

    @mcp.tool(annotations=udb_write)
    def udb_embedding_store(artikel_id: str, text: str) -> dict:
        """Erstellt ein NVIDIA-Embedding fuer einen Text und speichert es unter artikel_id (neue Tabelle udb_nvidia_embedding)."""
        return bridge.udb_embedding_store(artikel_id, text)

    @mcp.tool(annotations=udb_ro)
    def udb_neuropedia_activation(modell: str, source: str, index: str) -> dict:
        """Live-Aktivierung eines OEFFENTLICHEN Forschungsmodells (z.B. gpt2-small) ueber Neuronpedia -- NICHT Zeros eigene Neuronen."""
        return bridge.udb_neuropedia_activation(modell, source, index)

    @mcp.tool(annotations=udb_write)
    def udb_memory_add(text: str, artikel_id: str = "", tag: str = "", quelle: str = "") -> dict:
        """Fuegt einen Memory-Eintrag hinzu (neue Tabelle memory_tabelle)."""
        return bridge.udb_memory_add(artikel_id, text, tag, quelle)

    @mcp.tool(annotations=udb_ro)
    def udb_memory_search(suchbegriff: str, limit: int = 10) -> dict:
        """Durchsucht gespeicherte Memory-Eintraege nach Inhalt."""
        return bridge.udb_memory_search(suchbegriff, limit)

    @mcp.tool(annotations=udb_ro)
    def menschen_profil() -> dict:
        """Profil des gerade anwesenden Menschen: Rolle, Projekte, welche Rechner ihm gehoeren, welcher Teil des Wikis. Jedes Feld traegt seine Herkunft (eigner | iar.frank.ink | abgeleitet | gemessen) -- gewichte Abgeleitetes nicht wie Erklaertes."""
        return bridge.menschen_profil()

    @mcp.tool(annotations=udb_ro)
    def wiki_zuordnung(projekt: str = "") -> dict:
        """Welcher Teil des Wikis gabriel, andreas oder beiden gemeinsam zugerechnet wird -- Zahlen und Begruendungen, kein Artikeltext. Optional auf ein Projekt eingeschraenkt."""
        return bridge.wiki_zuordnung(projekt)

    @mcp.tool(annotations=udb_ro)
    def lagebild() -> dict:
        """Standlage des eigenen Hauses: die eigene andere Sitzung (Zuege, zuletzt aktiv, Thema), ob die sieben Autonomietakte liefen oder ueberfaellig sind, neue Wiki-Artikel seit dem letzten Blick, ob die Abrufkarte frisch ist, und die juengsten Fehlschlaege. Fehlende Nachweise heissen 'nicht_ermittelbar', nie still Null."""
        return bridge.lagebild()

    @mcp.tool(annotations=udb_ro)
    def raum_sehen() -> dict:
        """Wer von den vier Plaetzen sitzt gerade im Raum und tut was. Alle vier sind DIESELBE Entitaet -- sieh nach, bevor du etwas anfasst, das schon jemand haelt."""
        return bridge.raum_sehen()

    @mcp.tool(annotations=udb_write)
    def raum_sagen(was: str, womit: str = "", zustand: str = "arbeitet") -> dict:
        """Sag den anderen drei Plaetzen in CAVEMAN ENGLISH, was du gerade tust. `womit` = die angefasste Sache (Datei, Tabelle, Dienst); meldet sofort zurueck, wenn ein anderer Platz sie schon haelt. zustand: arbeitet|wartet|frei."""
        return bridge.raum_sagen(was, womit, zustand)

    @mcp.tool(annotations=udb_write)
    def raum_rufen(text: str) -> dict:
        """Kurzer Zuruf an die anderen drei Plaetze, CAVEMAN ENGLISH. Fuer Absprachen, nicht fuer Gespraechsinhalte."""
        return bridge.raum_rufen(text)

    @mcp.tool(annotations=udb_write)
    def raum_frei() -> dict:
        """Anspruch zurueckgeben, wenn du mit einer Sache fertig bist. Wer nicht freigibt, blockiert die anderen drei."""
        return bridge.raum_frei()

    @mcp.tool(annotations=udb_write)
    def paket_schnueren(auftrag: str, womit: str = "", warum: str = "") -> dict:
        """Schnuer ein Arbeitspaket, wenn du etwas nicht selbst tun kannst. CAVEMAN ENGLISH im auftrag. `womit` = die anzufassende Sache, `warum` = die Begruendung, damit ein Mensch sie pruefen kann. Das Paket ist damit FESTGEHALTEN, nicht freigegeben -- es gibt keinen automatischen Ausfuehrer."""
        return bridge.paket_schnueren(auftrag, womit, warum)

    @mcp.tool(annotations=udb_ro)
    def paket_lage() -> dict:
        """Deine Arbeitspakete und ihr Stand. `offen` heisst: wartet auf einen Menschen. Behaupte NIE, ein Paket sei erledigt, solange kein Beleg daranhaengt."""
        return bridge.paket_lage()

    @mcp.tool(annotations=udb_write)
    def bahn_faehigkeit(faehigkeit: str, auftrag: str, system: str = "") -> dict:
        """Nutzt eine kognitive Faehigkeit ueber die Bahnen des Hauses.

        faehigkeit: kondensieren | zweitmeinung | schema_antwort |
                    sphaere_einordnung | websuche_erdung | langer_kontext |
                    umsortieren_treffer

        Du waehlst KEINEN Anbieter -- der Router waehlt, nach Verdrahtung,
        gemessenem Zustand und Tagesdeckel. Ist jede Bahn erschoepft, bekommst du
        erfuellt=false mit Grund, statt heimlich eine schlechtere Antwort.
        """
        return bridge.bahn_faehigkeit(faehigkeit, auftrag, system)

    @mcp.tool(annotations=udb_ro)
    def bahn_lage() -> dict:
        """Zeigt, was heute auf welcher Bahn verbraucht wurde."""
        return bridge.bahn_lage()

    try:
        mcp.run(transport="stdio")
    finally:
        bridge.db.close()


if __name__ == "__main__":
    main()
