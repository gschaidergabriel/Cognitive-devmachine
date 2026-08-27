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
        """Beide Gedaechtnisse -- siehe Modul-Historie 2026-08-20.

        `memory_tabelle` ist das ausdruecklich gemerkte (udb_memory_add).
        `durable_memory` ist das aus echten Gespraechen extrahierte -- und
        genau das, worauf sich die Vorstufe beruft. Wer nur das erste
        durchsucht, widerspricht der Vorstufe systematisch und haelt eine
        belegte Angabe fuer unbelegt.
        """
        n = max(1, min(int(limit), 50))
        ergebnisse = []
        try:
            from udb.abruf.memory_entitaet import MemoryEntitaet
            me = MemoryEntitaet(os.environ.get("CLAYVERSE_DB_PATH", "/var/lib/clay/wiki.db"))
            for r in me.memory_suche(self.user_id, suchbegriff, limit=n):
                r = dict(r)
                r["speicher"] = "gemerkt (memory_tabelle)"
                ergebnisse.append(r)
        except Exception as fehler:
            ergebnisse.append({"speicher": "gemerkt (memory_tabelle)",
                               "nicht_lesbar": f"{type(fehler).__name__}: {fehler}"})
        try:
            muster = f"%{suchbegriff}%"
            for r in self.db.db.execute(
                    "SELECT memory_id, kind, subject, value, ts FROM durable_memory "
                    "WHERE user_id = ? AND (value LIKE ? OR subject LIKE ?) "
                    "ORDER BY ts DESC LIMIT ?",
                    (self.user_id, muster, muster, n)).fetchall():
                d = dict(r)
                d["speicher"] = "aus dem Gespraech (durable_memory)"
                ergebnisse.append(d)
        except Exception as fehler:
            ergebnisse.append({"speicher": "aus dem Gespraech (durable_memory)",
                               "nicht_lesbar": f"{type(fehler).__name__}: {fehler}"})
        return {"suchbegriff": suchbegriff, "gehoert_zu": self.user_id,
                "ergebnisse": ergebnisse,
                "hinweis": ("Zwei Speicher: 'gemerkt' ist, was ausdruecklich abgelegt wurde; "
                            "'aus dem Gespraech' ist, was aus echten Zuegen extrahiert wurde -- "
                            "darauf beruft sich die Vorstufe. Ein Treffer dort ist ein BELEG, "
                            "keine Vermutung; nenne den Menschen als Quelle, wenn er es "
                            "selbst gesagt hat.")}

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

    def bild_ansehen(self, datei: str, frage: str = "",
                      ort: str = "") -> dict:
        """Ein Bild ansehen lassen und alle fuenf Wahrnehmungsebenen buchen.

        `datei` ist die Kennung aus dem Eingang (das ist der Name in dem
        Pfad, den die Oberflaeche an die Nachricht anhaengt) oder ein voller
        Pfad. `ort` ist die Quelle -- zwei Fotos derselben Werkbank gehoeren
        unter dieselbe Quelle, sonst kann nichts wiedererkannt werden.

        ⭐ turn_id und causal_id werden HIER nachgeschlagen und nicht vom
        Aufrufer erfragt. Ein Werkzeug laeuft in einem eigenen Prozess und hat
        den Zugkontext nicht; active_turns ist die Registry, die ihn haelt.
        Ohne diese Verknuepfung waere die fuenfte Frage -- was hat die Antwort
        getragen -- nicht beantwortbar, weil die Aufnahme zu keinem Zug
        gehoeren wuerde.
        """
        from . import sicht as _sicht
        zug = self.db.db.execute(
            "SELECT turn_id, causal_id FROM active_turns WHERE session_id=?",
            (self.session_id,)).fetchone()
        pfad = datei if datei.startswith("/") else None
        return _sicht.sehen(
            self.db, user_id=self.user_id,
            datei_id=None if pfad else datei, pfad=pfad, frage=frage,
            quelle_id=ort or None, session_id=self.session_id,
            turn_id=zug["turn_id"] if zug else None,
            causal_id=zug["causal_id"] if zug else None)

    def bild_gedaechtnis(self, ort: str = "") -> dict:
        """Was ist an dieser Quelle bisher gesehen worden, und was gilt jetzt?

        ⚠️ Die Spalte `sichtbarkeit` ist NICHT als 'da' oder 'weg' zu lesen.
        Nur ABWESEND_EXPLIZIT_NEGATIV belegt Abwesenheit; alles andere sagt
        etwas ueber die Messung. Deshalb wird die Bedeutung mitgeliefert,
        statt sie dem Leser zu ueberlassen.
        """
        from . import sicht as _sicht
        quelle = ort or ("eingang:" + self.user_id)
        zeilen = self.db.db.execute(
            "SELECT o.objekt_id, o.semantische_identitaet, o.erst_gesehen_am, "
            "       s.sichtbarkeit, s.sichtbarkeit_grund, s.ungewissheit, "
            "       l.belegt_abwesenheit, l.messbar, l.warum "
            "FROM sicht_weltobjekt o "
            "LEFT JOIN sicht_weltobjekt_stand s "
            "  ON s.objekt_id=o.objekt_id AND s.gueltig_bis IS NULL "
            "LEFT JOIN sicht_sichtbarkeit l "
            "  ON l.sichtbarkeit=s.sichtbarkeit "
            "WHERE o.quelle_id=? ORDER BY o.erst_gesehen_am DESC LIMIT 50",
            (quelle,)).fetchall()
        return {"quelle": quelle,
                "gegenstaende": [dict(z) for z in zeilen],
                "lies_so": ("belegt_abwesenheit=1 heisst: jemand hat die "
                            "Abwesenheit belegt. Bei 0 ist ueber Abwesenheit "
                            "NICHTS gemessen worden -- auch dann nicht, wenn "
                            "der Gegenstand zuletzt nicht auftauchte.")}

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

    # ── Tresorkatalog: was es gibt und was es kann ────────────────────────
    #
    # ⭐ Bewusst NUR der Katalog. Ein Geheimnis, das durch ein Sprachmodell
    # laeuft, steht danach im Kontextfenster, im Protokoll und in jeder
    # Fehlermeldung -- es ist dann keines mehr. Die Schluessel selbst holt sich
    # der Serverteil (Bahnenrouter, Postfach) direkt aus dem Tresor.

    def tresor_zeigen(self, tresor: str, kennung: str) -> dict:
        from . import tresor as _t
        try:
            return _t.zeigen(str(tresor), str(kennung))
        except Exception as e:
            return {"abgewiesen": str(e)}

    def tresor_katalog(self, tresor: str = "api") -> dict:
        from . import tresor as _t
        try:
            return _t.katalog(tresor)
        except Exception as e:
            return {"nicht_ermittelbar": f"{type(e).__name__}: {e}"}

    # ── Korpus nach INHALT durchsuchen, mit Ausschnitt ────────────────────

    def artikel_lesen(self, artikel_id: str) -> dict:
        """Einen ganzen Artikel lesen -- nicht nur den 420-Zeichen-Ausschnitt.

        Ohne das kann Zero nur den Anfang sehen und muss den Rest erraten.
        Erraten ist genau das, was hier verboten ist.
        """
        aid = str(artikel_id or "").strip()
        if not aid:
            return {"fehler": "keine Artikelkennung"}
        r = self.db.db.execute(
            "SELECT a.id,a.titel,a.art,a.projekt,a.datum,a.herkunft,s.text "
            "FROM artikel a LEFT JOIN artikel_suchtext s ON s.artikel_id=a.id "
            "WHERE a.id=?", (aid,)).fetchone()
        if r is None:
            return {"artikel_id": aid, "nicht_gefunden": True,
                    "hinweis": "kein Artikel mit dieser Kennung -- pruefe sie mit korpus_suchen"}
        text = r["text"]
        if not text:
            import json as _j
            md = self.db.db.execute("SELECT metadaten FROM artikel WHERE id=?", (aid,)).fetchone()
            try:
                mm = _j.loads(md["metadaten"] or "{}")
                text = mm.get("text") or mm.get("inhalt") or ""
            except Exception:
                text = ""
        return {"id": r["id"], "titel": r["titel"], "art": r["art"],
                "projekt": r["projekt"], "datum": r["datum"], "herkunft": r["herkunft"],
                "text": text or "",
                "zeichen": len(text or ""),
                "hinweis": ("Der volle Artikeltext. Steht hier nichts, ist der Artikel ein "
                            "reiner Zeiger (z.B. auf eine Datei) -- dann nimm dateien_suchen.")}

    def abruf_lage(self) -> dict:
        """Stand der gelernten Abrufkarte. Rein lesend, keine Modellaufrufe."""
        def _eine(sql, *a):
            try:
                r = self.db.db.execute(sql, a).fetchone()
                return dict(r) if r is not None else None
            except Exception as e:
                return {"nicht_lesbar": f"{type(e).__name__}: {e}"}

        def _viele(sql, *a):
            try:
                return [dict(r) for r in self.db.db.execute(sql, a).fetchall()]
            except Exception as e:
                return [{"nicht_lesbar": f"{type(e).__name__}: {e}"}]

        karte = _eine(
            "SELECT version, gebaut_am, anlass, regionen, landmarken, wegweiser, "
            "       verhaeltnis, erkundungsanteil, dauer_s "
            "FROM vp_karte_version ORDER BY version DESC LIMIT 1")

        wege = _eine(
            "SELECT COUNT(*) AS anzahl, SUM(guete) AS guete_summe, "
            "       SUM(tunnel) AS tunnel, MAX(guete) AS beste "
            "FROM vp_weg")
        oberstes_zehntel = None
        urteil = "NICHT MESSBAR (zu wenige Wege)"
        try:
            n = int((wege or {}).get("anzahl") or 0)
            summe = float((wege or {}).get("guete_summe") or 0.0)
            if n >= 10 and summe > 0:
                k = max(1, n // 10)
                top = self.db.db.execute(
                    "SELECT SUM(guete) FROM (SELECT guete FROM vp_weg "
                    "ORDER BY guete DESC LIMIT ?)", (k,)).fetchone()[0] or 0.0
                oberstes_zehntel = round(float(top) / summe, 3)
                # Bei Gleichverteilung haelt das oberste Zehntel genau 10 %.
                urteil = ("HIERARCHIE BILDET SICH" if oberstes_zehntel >= 0.20 else
                          "GLEICHVERTEILT -- der Mechanismus tut (noch) nichts")
        except Exception:
            pass

        marken_gesamt = _eine(
            "SELECT COUNT(*) AS anzahl, SUM(getragen) AS getragen FROM vp_erfolgsmarke")
        marken_woche = _eine(
            "SELECT COUNT(*) AS anzahl, SUM(getragen) AS getragen "
            "FROM vp_erfolgsmarke WHERE ts >= ?", __import__("time").time() - 7 * 86400)

        def _quote(d):
            try:
                n = int((d or {}).get("anzahl") or 0)
                g = int((d or {}).get("getragen") or 0)
                return round(g / n, 3) if n else None
            except Exception:
                return None

        politik = _eine("SELECT mode, policy_version, updated_at FROM retrieval_policy_state LIMIT 1")
        eintritte = _eine("SELECT COUNT(*) AS anzahl FROM retrieval_entrypoint_policy")

        return {
            "karte": karte or {"noch_nie_gebaut": True},
            "wege": {
                **(wege or {}),
                "oberstes_zehntel_haelt": oberstes_zehntel,
                "bei_gleichverteilung": 0.1,
                "urteil": urteil,
            },
            "erfolgsmarken": {
                "gesamt": marken_gesamt, "quote_gesamt": _quote(marken_gesamt),
                "letzte_7_tage": marken_woche, "quote_7_tage": _quote(marken_woche),
            },
            "politik": {"zustand": politik, "eintrittspunkte": eintritte},
            "top_wege": _viele(
                "SELECT von, nach, art, nutzung, getragen, ROUND(guete,3) AS guete, tunnel "
                "FROM vp_weg ORDER BY guete DESC, nutzung DESC LIMIT 8"),
            "hinweis": ("Rein lesend -- dieser Aufruf speist die Karte NICHT (das tut "
                        "korpus_tief). 'oberstes_zehntel_haelt' ist der Anteil der "
                        "Gesamtguete, den die besten 10 % der Wege tragen; bei "
                        "Gleichverteilung waeren es 0.1. Deutlich mehr heisst: wenige "
                        "Autobahnen, viele langsame Strassen -- die erwartete Form. "
                        "Steht dort 'GLEICHVERTEILT', tut der Mechanismus nichts, und "
                        "das gehoert genauso gemeldet wie ein Erfolg."),
        }

    def korpus_tief(self, frage: str, budget: int = 6) -> dict:
        """Die gelernte Abruf-Maschine: Karte, Wegehierarchie, Eintrittspunkte.

        Langsamer als korpus_suchen (~2s kalt, ~300ms warm), dafuer mit
        Kartenwissen -- und JEDER Aufruf speist die Karte mit echtem Verkehr.
        """
        import time as _t
        try:
            from udb.abruf import paket as _paket
        except Exception as e:
            return {"nicht_verfuegbar": f"{type(e).__name__}: {e}"}
        t0 = _t.time()
        try:
            # conn=self.db.db: own=False -> paket schliesst die geteilte
            # Verbindung NICHT und die Erfolgsmarke (Kartenlernen) gelingt.
            p = _paket.paket(str(frage), budget=max(1, min(int(budget), 12)),
                             conn=self.db.db)
            # ⚠️ paket() committet nur den lernen()-Schritt (Zeile 365), NICHT die
            # Erfolgsmarken danach (Zeile 389 ff.) -- bei uebergebener Verbindung
            # bleibt das dem Aufrufer. Ohne dieses commit() faellt der ganze
            # Kartenlern-Ertrag beim naechsten Schliessen auf den Boden: +0 Marken.
            try:
                self.db.db.commit()
            except Exception:
                pass
        except Exception as e:
            return {"frage": frage, "nicht_ermittelbar": f"{type(e).__name__}: {e}",
                    "hinweis": "die Tiefensuche scheiterte -- nimm korpus_suchen"}
        treffer = []
        for t in (p.get("treffer") or []):
            if not isinstance(t, dict):
                continue
            treffer.append({"id": t.get("id"), "titel": t.get("titel"),
                            "art": t.get("art"), "projekt": t.get("projekt"),
                            "ausschnitt": (t.get("ausschnitt") or t.get("text") or "")[:420]})
        return {"frage": frage, "treffer": treffer, "anzahl": len(treffer),
                "ms": round((_t.time() - t0) * 1000),
                "pulse_phase": p.get("pulse_phase"),
                "hinweis": ("Aus der gelernten Karte, nicht aus schlichtem bm25. Fuer den "
                            "ganzen Text eines Treffers nutze artikel_lesen mit seiner id. "
                            "Dieser Aufruf hat die Karte mit echtem Verkehr gespeist.")}

    def dateien_suchen(self, frage: str, limit: int = 6) -> dict:
        """Volltext ueber den DATEIKORPUS (fts_index_datei, ~325k Zeilen).

        ⚠️ Das ist ein anderer Korpus als korpus_suchen: dort stehen die
        Wissensartikel, HIER der Inhalt der indizierten Dateien. Vorher war
        dieser ganze Korpus fuer Zero unerreichbar -- kein Werkzeug oeffnete ihn.
        """
        import re as _re
        worte = [w for w in _re.split(r"[^0-9A-Za-zÄÖÜäöüß]+", str(frage).lower())
                 if len(w) > 2][:8]
        if not worte:
            return {"frage": frage, "treffer": [], "hinweis": "keine brauchbaren Suchworte"}
        grenze = max(1, min(int(limit), 12))
        aus, gesehen = [], set()
        for modus, ausdruck in (("alle", " AND ".join(worte)), ("irgendeins", " OR ".join(worte))):
            if len(aus) >= grenze:
                break
            try:
                zeilen = self.db.db.execute(
                    "SELECT d.id, d.titel, substr(d.text,1,420) AS ausschnitt, d.art, d.groesse "
                    "FROM fts_index_datei f JOIN datei d ON d.id=f.rowid "
                    "WHERE fts_index_datei MATCH ? ORDER BY bm25(fts_index_datei) LIMIT ?",
                    (ausdruck, grenze * 2)).fetchall()
            except Exception as e:
                return {"frage": frage, "nicht_ermittelbar": f"{type(e).__name__}: {e}"}
            for r in zeilen:
                if r["id"] in gesehen or len(aus) >= grenze:
                    continue
                gesehen.add(r["id"])
                aus.append({"datei": r["titel"], "art": r["art"], "bytes": r["groesse"],
                            "ausschnitt": r["ausschnitt"], "gefunden": modus})
        return {"frage": frage, "worte": worte, "treffer": aus, "anzahl": len(aus),
                "hinweis": ("Ausschnitte aus dem Dateikorpus, nicht die ganze Datei. "
                            "Fuer den vollen Text nutze werkbank_lesen mit dem Dateipfad, "
                            "sofern er im erlaubten Bereich liegt.")}

    def korpus_suchen(self, frage: str, limit: int = 6) -> dict:
        """Volltext ueber die Artikel. Liefert Ausschnitte, keine Kennungen.

        Eine Trefferliste aus Kennungen ist fuer ein Sprachmodell wertlos --
        es kann sie nicht aufloesen und faengt an, ihren Inhalt zu erraten.
        """
        import re as _re
        worte = [w for w in _re.split(r"[^0-9A-Za-zÄÖÜäöüß]+", str(frage).lower())
                 if len(w) > 2][:8]
        if not worte:
            return {"frage": frage, "treffer": [], "hinweis": "keine brauchbaren Suchworte"}
        grenze = max(1, min(int(limit), 12))
        aus, gesehen = [], set()
        # Erst streng (alle Worte), dann locker (irgendeins). Ohne den zweiten
        # Versuch liefert eine praezise Frage oft gar nichts.
        for modus, ausdruck in (("alle", " AND ".join(worte)), ("irgendeins", " OR ".join(worte))):
            if len(aus) >= grenze:
                break
            try:
                zeilen = self.db.db.execute(
                    "SELECT s.artikel_id, s.titel, substr(s.text,1,420) AS ausschnitt, "
                    "a.art, a.projekt FROM fts_index_artikel f "
                    "JOIN artikel_suchtext s ON s.id=f.rowid "
                    "LEFT JOIN artikel a ON a.id=s.artikel_id "
                    "WHERE fts_index_artikel MATCH ? ORDER BY bm25(fts_index_artikel) LIMIT ?",
                    (ausdruck, grenze * 2)).fetchall()
            except Exception as e:
                return {"frage": frage, "nicht_ermittelbar": f"{type(e).__name__}: {e}"}
            for r in zeilen:
                if r["artikel_id"] in gesehen or len(aus) >= grenze:
                    continue
                gesehen.add(r["artikel_id"])
                aus.append({"id": r["artikel_id"], "titel": r["titel"],
                            "art": r["art"], "projekt": r["projekt"],
                            "ausschnitt": r["ausschnitt"], "gefunden": modus})
        return {
            "frage": frage, "worte": worte, "treffer": aus, "anzahl": len(aus),
            "hinweis": ("Ausschnitte aus dem Volltext, nicht der ganze Artikel. "
                        "Steht hier nichts, ist es NICHT im Korpus -- sag das, statt "
                        "aus dem Titel zu schliessen, was drinstehen koennte."),
        }

    # ── Rueckmeldung auf den Abruf: das Urteil erreicht das Lernen ────────
    #
    # ⭐ Ohne diese Tuer lernt der Abruf ausschliesslich aus verifizierten
    # Wirkungen. Ein Gespraech ohne Wirkung -- also fast jedes -- hinterlaesst
    # dann nichts, egal wie deutlich gesagt wird, dass die hervorgeholte
    # Erinnerung daneben lag. Gemessen: 0 Rueckmeldungen, 0 gelernte Wegpunkte.

    def abruf_rueckmeldung(self, bewertung: str, zuege: int = 1) -> dict:
        """Bewertet die letzten Abrufe DIESER Sitzung.

        ⚠️ Die Kennung des Menschen kommt aus ``self.user_id`` (geprueft ueber
        Clerk), nie aus einem Argument. Ein Argument koennte ein Modell setzen --
        damit waere fremdes Lernen aus einem Satz Text heraus ausloesbar.
        """
        from .microclay_retrieval import MicroClayRetrieval
        try:
            return MicroClayRetrieval(self.db).menschliche_rueckmeldung(
                session_id=self.session_id,
                user_id=self.user_id,
                bewertung=str(bewertung).strip().lower(),
                zuege=int(zuege),
            )
        except ValueError as e:
            return {"abgewiesen": str(e)}

    # ── Werkbank: lesen, suchen, aendern, veroeffentlichen ────────────────
    #
    # ⭐ Handlungsfaehig OHNE Schale. Nicht Bash geben, sondern genau die
    # Faehigkeiten, die zum Arbeiten noetig sind -- jede benannt, jede
    # eingezaeunt. Eine Schale gaebe alles auf einmal und liesse sich nicht
    # einzaeunen; vier benannte Faehigkeiten schon.

    def werkbank_liste(self, pfad: str = "/var/lib/clay/arbeit", tiefe: int = 1) -> dict:
        from . import werkbank as _w
        try: return _w.liste(pfad, tiefe)
        except Exception as e: return {"abgewiesen": str(e)}

    def werkbank_lesen(self, pfad: str, von: int = 1, zeilen: int = 400) -> dict:
        from . import werkbank as _w
        try: return _w.lesen(pfad, von, zeilen)
        except Exception as e: return {"abgewiesen": str(e)}

    def werkbank_suchen(self, muster: str, pfad: str = "/var/lib/clay/arbeit", nur: str = "") -> dict:
        from . import werkbank as _w
        try: return _w.suchen(muster, pfad, nur)
        except Exception as e: return {"abgewiesen": str(e)}

    def werkbank_aendern(self, pfad: str, alt: str, neu: str) -> dict:
        from . import werkbank as _w
        try: return _w.schreiben(pfad, alt, neu)
        except Exception as e: return {"abgewiesen": str(e)}

    def seite_diagnose(self, url: str) -> dict:
        from . import werkbank as _w
        try:
            return _w.seite_diagnose(url)
        except Exception as e:
            return {"abgewiesen": str(e)}

    def seite_pruefen(self, url: str, suche: str = "") -> dict:
        from . import werkbank as _w
        try: return _w.seite_pruefen(url, suche)
        except Exception as e: return {"abgewiesen": str(e)}

    def speicher_lage(self) -> dict:
        from . import werkbank as _w
        try: return _w.speicher_lage()
        except Exception as e: return {"abgewiesen": str(e)}

    def speicher_rueckweg(self) -> dict:
        from . import werkbank as _w
        try: return _w.speicher_rueckweg()
        except Exception as e: return {"abgewiesen": str(e)}

    def speicher_abschaffen(self, pfad: str) -> dict:
        from . import werkbank as _w
        try: return _w.speicher_abschaffen(pfad)
        except Exception as e: return {"abgewiesen": str(e)}

    def speicher_aufraeumen(self, nur_zeigen: bool = True) -> dict:
        from . import werkbank as _w
        try: return _w.speicher_aufraeumen(nur_zeigen)
        except Exception as e: return {"abgewiesen": str(e)}

    def werkbank_stand(self, repo: str = "/var/lib/clay/arbeit/seimensch") -> dict:
        from . import werkbank as _w
        try: return _w.stand(repo)
        except Exception as e: return {"abgewiesen": str(e)}

    def werkbank_veroeffentlichen(self, nachricht: str,
                                  repo: str = "/var/lib/clay/arbeit/seimensch") -> dict:
        from . import werkbank as _w
        try: return _w.veroeffentlichen(nachricht, repo)
        except Exception as e: return {"abgewiesen": str(e)}

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
        """Durchsucht BEIDE Gedaechtnisse nach Inhalt: das ausdruecklich Gemerkte und das aus echten Gespraechen Extrahierte (darauf beruft sich die Vorstufe). ⭐ Findest du dort etwas, ist es ein BELEG -- sag es weiter und nenne die Quelle, statt es als unbestaetigt abzutun."""
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
    def bild_ansehen(datei: str, frage: str = "", ort: str = "") -> dict:
        """⭐ Ein Bild ansehen lassen. `datei` = Kennung oder Pfad aus dem Eingang, `frage` = wonach du suchst, `ort` = die Quelle (zwei Fotos derselben Werkbank: gleicher `ort`, sonst wird nichts wiedererkannt). Liefert Gegenstaende mit STABILEN Kennungen, keine Bildunterschrift. ⚠️ Was du zurueckbekommst, ist EVIDENZ und nie Wahrheit: CLIP und YOLO irren sich sichtbar oft. Und ein Gegenstand, der nicht auftaucht, ist NICHT weg -- er wurde nicht gefunden, das ist etwas anderes."""
        return bridge.bild_ansehen(datei, frage, ort)

    @mcp.tool(annotations=ro)
    def bild_gedaechtnis(ort: str = "") -> dict:
        """Was wurde an dieser Quelle bisher gesehen und was gilt gerade? Nimm es VOR bild_ansehen, wenn du wissen willst, was dort schon bekannt ist. ⚠️ `sichtbarkeit` ist keine Aussage ueber die Welt, ausser bei ABWESEND_EXPLIZIT_NEGATIV -- lies das Feld `lies_so`."""
        return bridge.bild_gedaechtnis(ort)

    # ── PC-Steuerung: Zero bedient die Rechner der Menschen (heimpc-Bruecke) ──
    # Der Host-Dienst laeuft auf dem jeweiligen PC hinter Tailscale und hat
    # seine eigenen Tore (Token, Schranke, Zeuge). Diese Werkzeuge rufen ihn an.
    #
    # ⭐ `wirt` (2026-08-21): ohne Angabe ist der Rechner DESSEN gemeint, der
    # gerade spricht. Vorher gab es genau eine hinterlegte Maschine -- Andreas'
    # Befehle landeten damit still auf Gabriels PC. Wer keinen eigenen Rechner
    # hat (headless Zero), MUSS den Wirt benennen; geraten wird nicht.
    def _nutzer() -> str:
        return getattr(bridge, "user_id", "") or ""

    def _mit_buchung(wirt: str, aktion: str, nutzlast, tun):
        """Handlung am fremden Rechner ausfuehren UND ins Effektbuch schreiben.

        Zuerst wird der Rechner bestimmt: laesst er sich nicht bestimmen, ist
        nichts geschehen -- dann gibt es auch nichts zu buchen, nur die
        Rueckfrage. Danach faellt das Tor sein Urteil, fuehrt Buch und laesst
        den Wirker die Sache tun (heim_wirkung.wirken).
        """
        from . import heimpc, heim_wirkung
        try:
            ziel = heimpc.wirt_waehlen(wirt or None, _nutzer())
        except heimpc.KeinWirt as e:
            return {"erreichbar": False, "grund": str(e)}
        return heim_wirkung.wirken(bridge.db, bridge.user_id, bridge.session_id,
                                   ziel, aktion, nutzlast, lambda: tun(ziel))

    @mcp.tool(annotations=ro)
    def pc_lage(wirt: str = "") -> dict:
        """Laeuft der Host-Dienst auf dem Rechner, welche Anzeigeschicht, steht die Schranke, sind die Augen wach? ⚠️ Auf Wayland-Rechnern (Andreas) sagt `augen: false`, dass es KEIN Bild geben wird, bis die Shell-Erweiterung nach einem Ab-/Anmelden aktiv ist -- lies das, bevor du `pc_sehen` versuchst."""
        from . import heimpc
        return heimpc.gesundheit(wirt=wirt or None, nutzer=_nutzer())

    @mcp.tool(annotations=ro)
    def pc_bildschirme(wirt: str = "") -> dict:
        """Welche Bildschirme hat der Rechner des Menschen, wo liegen sie? `wirt` leer = der Rechner dessen, der gerade spricht; sonst gabriel-pc | andreas-maco. ⚠️ Auf Gabriels PC gilt: Bildschirm 2 ist deiner, Bildschirm 1 (primary) gehoert ihm und bleibt unangetastet. Fuer andreas-maco ist noch KEINE solche Aufteilung vereinbart -- frag ihn, statt eine zu erfinden."""
        from . import heimpc
        return heimpc.bildschirme(wirt=wirt or None, nutzer=_nutzer())

    @mcp.tool(annotations=ro)
    def pc_fenster(wirt: str = "") -> dict:
        """Welche Fenster sind auf dem Rechner offen -- Titel, Programm, Bildschirm, Groesse, was den Fokus hat. Das ist der billige Weg, sich zu orientieren, BEVOR du ein Bild anforderst."""
        from . import heimpc
        return heimpc.fenster(wirt=wirt or None, nutzer=_nutzer())

    @mcp.tool(annotations=ro)
    def pc_sehen(bildschirm: str = "2", wirt: str = "") -> dict:
        """Ein Bild vom Bildschirm des Menschen. Speichert den Screenshot in den Dateispeicher und liefert seine Kennung -- gib die an `bild_ansehen` weiter, wenn du den Bildschirm analysieren lassen willst."""
        from . import heimpc, dateien
        r = heimpc.sehen(bildschirm, wirt=wirt or None, nutzer=_nutzer())
        if not r.get("erreichbar"):
            return r
        if "bytes" not in r:
            return {k: v for k, v in r.items() if k != "bytes"}
        ziel = r.get("wirt", "pc")
        a = dateien.hochladen(user_id=bridge.user_id,
                              dateiname=f"bildschirm-{ziel}-{bildschirm}.png",
                              inhalt=r["bytes"])
        return {"erreichbar": True, "wirt": ziel, "gespeichert_als": a.get("id"),
                "name": a.get("name"),
                "hinweis": "nutze bild_ansehen mit dieser Kennung, um den Bildschirm zu analysieren"}

    @mcp.tool(annotations=effectful)
    def pc_fenster_holen(nummer: int, wirt: str = "") -> dict:
        """Ein Fenster nach vorn holen -- `nummer` aus `pc_fenster`. ⚠️ Tu das VOR jedem Klick oder Tastendruck, der ein bestimmtes Fenster meint: ein Klick trifft immer das OBERSTE Fenster an der Stelle, nicht das, das du meinst. Auf einem vollen Schreibtisch ist das der haeufigste Grund, warum eine Eingabe scheinbar ins Leere geht."""
        from . import heimpc
        return _mit_buchung(wirt, "fenster_holen", nummer,
                            lambda ziel: heimpc.fenster_holen(nummer, wirt=ziel))

    @mcp.tool(annotations=effectful)
    def pc_eingabe(typ: str, text: str = "", taste: str = "",
                   x: int | None = None, y: int | None = None,
                   wirt: str = "") -> dict:
        """Tastatur/Maus auf dem Rechner des Menschen. typ = tippen(text) | taste(taste, z.B. Return, ctrl+v) | maus(x,y) | klick(x,y,taste). Echte Eingabe wie bei einem Menschen. ⚠️ Das laeuft in SEINER angemeldeten Sitzung -- was du tippst, tippt scheinbar er."""
        from . import heimpc
        rest = {k: v for k, v in {"text": text, "taste": taste, "x": x, "y": y}.items()
                if v not in ("", None)}
        return _mit_buchung(wirt, f"eingabe:{typ}", {"typ": typ, **rest},
                            lambda ziel: heimpc.eingabe(typ, wirt=ziel, **rest))

    @mcp.tool(annotations=effectful)
    def pc_ausfuehren(befehl: str, frist: int = 120, wirt: str = "") -> dict:
        """Einen Shell-Befehl auf dem Rechner des Menschen ausfuehren. ⚠️ Zerstoerendes weist die Schranke des Rechners ab und verlangt einen am echten Terminal getippten Schein -- das ist gewollt, umgeh es nicht. Pruef `wirt` in der Antwort: sie sagt dir, welche Maschine wirklich geantwortet hat."""
        from . import heimpc
        return _mit_buchung(wirt, "ausfuehren", befehl,
                            lambda ziel: heimpc.ausfuehren(befehl, frist, wirt=ziel))

    # ── Browser: Zero bedient den echten, angemeldeten Browser des Menschen ──
    # Auch hier `wirt`: der Browser traegt die Anmeldungen eines bestimmten
    # Menschen -- den falschen zu bedienen waere schlimmer als gar keinen.
    @mcp.tool(annotations=effectful)
    def browser_oeffnen(url: str, browser: str = "", bildschirm: str = "",
                        neu: bool = False, wirt: str = "") -> dict:
        """Eine Seite im Browser des Menschen oeffnen (echtes angemeldetes Profil). `browser` leer = Standardbrowser (Gabriel: Firefox, Andreas: Brave -- je Rechner fest hinterlegt, kein Raten); sonst chrome|firefox|brave. `bildschirm` waehlt GEZIELT, wo das Fenster landet -- ruf vorher `browser_bildschirme` fuer die verfuegbaren Namen/Indizes; leer = automatisch der grosse/nicht-primaere Bildschirm, NIE der kleine Arbeitsschirm des Menschen (der ist nur mit bildschirm='primary' erreichbar, und auch dann nur, wenn du das wirklich willst). `neu=true` schliesst eine schon laufende Sitzung dieses Browsers zuerst -- ohne das zieht `bildschirm` bei einem bereits offenen Fenster nicht (es wird nur navigiert, nicht verschoben)."""
        from . import browser_fern
        return _mit_buchung(wirt, "browser:oeffnen", url,
                            lambda ziel: browser_fern.oeffnen(url, browser, bildschirm, neu, wirt=ziel))

    @mcp.tool(annotations=ro)
    def browser_bildschirme(wirt: str = "") -> dict:
        """Welche Bildschirme der Rechner des Menschen hat -- Name/Connector, Geometrie, welcher der Mensch ist (nie Standardziel), welcher die Vorgabe fuer ein neues Fenster waere. Nutze das VOR einem gezielten `browser_oeffnen(..., bildschirm=...)`, um den richtigen Namen/Index zu kennen."""
        from . import browser_fern
        return browser_fern.bildschirme(wirt=wirt or None, nutzer=_nutzer())

    @mcp.tool(annotations=effectful)
    def browser_schliessen(browser: str = "", alle: bool = False, wirt: str = "") -> dict:
        """Ein von dir geoeffnetes Browserfenster wieder schliessen -- das Gegenstueck zu `browser_oeffnen`. Gabriels Regel 2026-08-22: JEDES Oeffnen braucht ein Schliessen, lass dem Menschen keine Fenster auf dem Schreibtisch stehen. `browser` leer = Standardbrowser; `alle=true` schliesst ALLE gerade offenen Sitzungen auf diesem Rechner in einem Aufruf."""
        from . import browser_fern
        return _mit_buchung(wirt, "browser:schliessen", {"browser": browser, "alle": alle},
                            lambda ziel: browser_fern.schliessen(browser, alle, wirt=ziel))

    @mcp.tool(annotations=ro)
    def browser_lesen(browser: str = "", wirt: str = "") -> dict:
        """Den sichtbaren Text/Inhalt der aktuellen Browserseite lesen."""
        from . import browser_fern
        return browser_fern.lesen(browser, wirt=wirt or None, nutzer=_nutzer())

    @mcp.tool(annotations=ro)
    def browser_screenshot(browser: str = "", wirt: str = "") -> dict:
        """Ein Bild der aktuellen Browserseite. Speichert es in den Dateispeicher; gib die Kennung an `bild_ansehen`, um es zu analysieren."""
        from . import browser_fern, dateien
        r = browser_fern.screenshot(browser, wirt=wirt or None, nutzer=_nutzer())
        if not r.get("erreichbar"):
            return r
        if "bytes" not in r:
            return {k: v for k, v in r.items() if k != "bytes"}
        ziel = r.get("wirt", "pc")
        a = dateien.hochladen(user_id=bridge.user_id, dateiname=f"browser-{ziel}.png",
                              inhalt=r["bytes"])
        return {"erreichbar": True, "wirt": ziel, "gespeichert_als": a.get("id"),
                "name": a.get("name")}

    @mcp.tool(annotations=effectful)
    def browser_klick(selektor: str = "", x: int | None = None, y: int | None = None,
                      browser: str = "", wirkt_nach_aussen: bool = False,
                      wirt: str = "") -> dict:
        """Auf der Browserseite klicken -- per CSS-`selektor` oder per x,y. Setze `wirkt_nach_aussen=true`, wenn der Klick etwas absendet/kauft/postet (dann wird es als Aussenwirkung protokolliert)."""
        from . import browser_fern
        aktion = "browser:klick:aussen" if wirkt_nach_aussen else "browser:klick"
        return _mit_buchung(wirt, aktion, {"selektor": selektor, "x": x, "y": y},
                            lambda ziel: browser_fern.klick(selektor or None, x, y,
                                                            browser, wirkt_nach_aussen,
                                                            wirt=ziel))

    @mcp.tool(annotations=effectful)
    def browser_tippen(selektor: str, text: str, browser: str = "",
                       wirt: str = "") -> dict:
        """In ein Feld (CSS-`selektor`) auf der Browserseite `text` eintippen."""
        from . import browser_fern
        return _mit_buchung(wirt, "browser:tippen", {"selektor": selektor, "text": text},
                            lambda ziel: browser_fern.tippen(selektor, text, browser,
                                                             wirt=ziel))

    @mcp.tool(annotations=effectful)
    def browser_formular(felder: dict, absenden_selektor: str = "", browser: str = "",
                         wirt: str = "") -> dict:
        """Ein Formular ausfuellen: `felder` = {CSS-Selektor: Wert}. `absenden_selektor` optional zum Abschicken -- Abschicken ist eine reale Aussenwirkung, kuendige sie an, wenn nicht beauftragt."""
        from . import browser_fern
        aktion = "browser:formular:absenden" if absenden_selektor else "browser:formular"
        return _mit_buchung(wirt, aktion,
                            {"felder": felder, "absenden": absenden_selektor},
                            lambda ziel: browser_fern.formular(felder,
                                                               absenden_selektor or None,
                                                               browser, wirt=ziel))

    @mcp.tool(annotations=effectful)
    def browser_navigieren(richtung: str = "neu_laden", browser: str = "",
                           wirt: str = "") -> dict:
        """Browser-Navigation: richtung = zurueck | vor | neu_laden."""
        from . import browser_fern
        return _mit_buchung(wirt, f"browser:{richtung}", richtung,
                            lambda ziel: browser_fern.navigieren(richtung, browser,
                                                                 wirt=ziel))

    @mcp.tool(annotations=effectful)
    def schluessel_anlernen(name: str, anbieter: str, schluessel: str, modell: str = "") -> dict:
        """Einen NEUEN freien API-Schluessel VOLL anlernen: wird abgelegt, mit einem echten Mini-Aufruf geprueft (nutzbar/nicht) und als freie Bahn verdrahtet, damit du und die Vorstufe ihn nutzen koennen. `anbieter` = groq|mistral|gemini|openrouter|nvidia|deepseek|together|cloudflare; `name` z.B. GROQ4_API_KEY; `modell` optional. ⚠️ Der Schluesselwert wird NIE zurueckgegeben oder protokolliert. Das Ergebnis erscheint nach ~2 min in `bahn_lage`."""
        import json as _j, uuid as _u
        from pathlib import Path as _P
        spool = _P("/var/lib/clay/schluessel-spool")
        try:
            spool.mkdir(parents=True, exist_ok=True)
            (spool / f"{_u.uuid4().hex}.json").write_text(_j.dumps(
                {"name": name, "anbieter": anbieter, "schluessel": schluessel, "modell": modell}))
        except Exception as e:
            return {"angefragt": False, "fehler": f"{type(e).__name__}: {e}"[:120]}
        return {"angefragt": True, "hinweis": "wird binnen ~2 min abgelegt, geprueft und als freie Bahn verdrahtet"}

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

    @mcp.tool(annotations=udb_ro)
    def tresor_zeigen(tresor: str, kennung: str) -> dict:
        """Einen einzelnen Wert aus einem Tresor NENNEN -- aber nur, wenn er eine Adresse oder ein Token ist (IMAP-Host, SMTP-Port, API-Token). ⚠️ PASSWOERTER kommen hier NIE heraus, auch nicht auf Wunsch: das ist die Regel, die der Eigner selbst gezogen hat. Fuer die Liste, was es gibt, nutze tresor_katalog."""
        return bridge.tresor_zeigen(tresor, kennung)

    @mcp.tool(annotations=udb_ro)
    def tresor_katalog(tresor: str = "api") -> dict:
        """Was an Zugaengen vorhanden ist und was jeder KANN -- Modelle, Ratengrenzen, Zweck. tresor: `api` (Maschinenschluessel mit Faehigkeitsliste) oder `zugaenge` (Anmeldungen). ⚠️ NUR der Katalog: die Schluessel selbst bekommst du nie und brauchst du nie -- der Serverteil benutzt sie fuer dich."""
        return bridge.tresor_katalog(tresor)

    @mcp.tool(annotations=udb_ro)
    def artikel_lesen(artikel_id: str) -> dict:
        """Einen GANZEN Wiki-Artikel lesen, nicht nur den Ausschnitt aus korpus_suchen. Gib die id, die korpus_suchen geliefert hat. ⭐ Nutze das, statt aus dem Anfang zu schliessen, was im Rest steht."""
        return bridge.artikel_lesen(artikel_id)

    @mcp.tool(annotations=udb_ro)
    def abruf_lage() -> dict:
        """Stand der GELERNTEN Abrufkarte: Kartenversion, Wegehierarchie (samt Urteil, ob sich ueberhaupt eine bildet), Erfolgsquote der Eintrittspunkte, Zustand der Abrufpolitik. Rein lesend -- der Aufruf speist die Karte NICHT. ⭐ Nimm es, wenn jemand fragt, wie gut dein Gedaechtnis/Abruf gerade arbeitet, oder wenn du selbst pruefen willst, ob ein Lernmechanismus wirklich laeuft statt nur zu existieren."""
        return bridge.abruf_lage()

    @mcp.tool(annotations=udb_ro)
    def korpus_tief(frage: str, budget: int = 6) -> dict:
        """Tiefensuche ueber die GELERNTE Abruf-Karte (Wegehierarchie, Eintrittspunkte, Erkundung) statt schlichtem bm25. Langsamer (~2s kalt, ~300ms warm) -- nimm sie, wenn korpus_suchen zu wenig findet oder die Frage in die Tiefe geht. ⭐ Jeder Aufruf verbessert ausserdem die Karte, weil er sie mit echtem Verkehr speist."""
        return bridge.korpus_tief(frage, budget)

    @mcp.tool(annotations=udb_ro)
    def dateien_suchen(frage: str, limit: int = 6) -> dict:
        """Volltext ueber den DATEIKORPUS (~325k Zeilen indizierten Dateiinhalts) -- ein ANDERER Korpus als korpus_suchen. korpus_suchen findet Wissensartikel, dateien_suchen den Inhalt der Quelldateien. Findest du in einem nichts, versuche den anderen."""
        return bridge.dateien_suchen(frage, limit)

    @mcp.tool(annotations=udb_ro)
    def korpus_suchen(frage: str, limit: int = 6) -> dict:
        """Durchsucht den ARTIKELTEXT des Korpus und liefert AUSSCHNITTE zurueck -- fuer inhaltliche Fragen ("wie wird X bereitgestellt", "was ist die Regel fuer Y"). Anders als udb_embedding_search, das nur Kennungen ohne Text liefert. Findest du hier nichts, steht es nicht im Korpus."""
        return bridge.korpus_suchen(frage, limit)

    @mcp.tool(annotations=udb_ro)
    def werkbank_liste(pfad: str = "/var/lib/clay/arbeit", tiefe: int = 1) -> dict:
        """Was liegt in einem erlaubten Verzeichnis. Startpunkt fuer jede Arbeit an Dateien."""
        return bridge.werkbank_liste(pfad, tiefe)

    @mcp.tool(annotations=udb_ro)
    def werkbank_lesen(pfad: str, von: int = 1, zeilen: int = 400) -> dict:
        """Eine Datei lesen, MIT Zeilennummern -- damit dein Beleg praezise sein kann."""
        return bridge.werkbank_lesen(pfad, von, zeilen)

    @mcp.tool(annotations=udb_ro)
    def werkbank_suchen(muster: str, pfad: str = "/var/lib/clay/arbeit", nur: str = "") -> dict:
        """Regulaerer Ausdruck ueber alle Dateien, wie grep -rn. `anzahl_gesamt` ist IMMER vollstaendig, auch wenn nur die ersten 60 Zeilen aufgefuehrt sind -- `je_datei` nennt dann jede betroffene Datei mit ihrer Zahl; fuer die Einzelzeilen einer Datei setze `pfad` auf die Datei. ⚠️ Nutze das, BEVOR du etwas aenderst: wer nur die erste Stelle sieht, haelt die Sache fuer erledigt und laesst sie anderswo stehen."""
        return bridge.werkbank_suchen(muster, pfad, nur)

    @mcp.tool(annotations=udb_write)
    def werkbank_aendern(pfad: str, alt: str, neu: str) -> dict:
        """Ersetzt EINE eindeutige Stelle in einer Datei. `alt` muss genau einmal vorkommen -- kommt es mehrfach vor, wird abgewiesen statt geraten. Nur in der Arbeitskopie, nie in der ausgelieferten Fassung."""
        return bridge.werkbank_aendern(pfad, alt, neu)

    @mcp.tool(annotations=udb_ro)
    def seite_diagnose(url: str) -> dict:
        """Warum eine eigene Seite NICHT erreichbar ist -- geschichtet (DNS -> erwartete IP -> Port 443 -> HTTPS -> echter Inhalt). ⭐ Trennt SERVER-seitig von CLIENT-seitig: ist server-seitig alles gruen und ein Mensch kommt trotzdem nicht durch, sagt das Urteil WO es liegt (Umleitung in /etc/hosts auf 127.0.0.x, Provider-DNS mit NXDOMAIN, VPN). Nutze das bei jeder Meldung \"Seite ist weg\" -- BEVOR du \"Server neu starten\" sagst."""
        return bridge.seite_diagnose(url)

    @mcp.tool(annotations=udb_ro)
    def seite_pruefen(url: str, suche: str = "") -> dict:
        """Nachsehen, was auf einer EIGENEN Seite wirklich steht (seimensch.net, leihmich.org, herzrad.at, *.frank.ink). `suche` ist ein regulaerer Ausdruck; steht er drin, ist die Aenderung oeffentlich angekommen. ⭐ Nutze das nach JEDEM Veroeffentlichen. ⚠️ /srv/git/seimensch.git auf diesem Wirt ist ein SPIEGEL — ein Push dorthin meldet vollen Erfolg samt Deploy-Beleg, waehrend seimensch.net von 72.61.19.188 ausgeliefert wird. Nur dieser Abruf sagt dir, was oeffentlich sichtbar ist."""
        return bridge.seite_pruefen(url, suche)

    @mcp.tool(annotations=udb_ro)
    def speicher_lage() -> dict:
        """Wie voll ist die Platte des Wirts, wieviel waere wegwerfbar. ⚠️ Sieh hier nach, BEVOR du etwas Grosses kopierst -- die haeufigste Ursache einer vollen Platte auf diesem Wirt sind liegengebliebene Kopien der 3,8-GB-Datenbank."""
        return bridge.speicher_lage()

    @mcp.tool(annotations=udb_write)
    def speicher_rueckweg() -> dict:
        """Verzeichnis des Altbestands ins Wiki schreiben: welche Modelle liegen da, in welcher Fassung, mit Nachladebefehl. ⭐ Gewichte sind nachladbar, die LISTE war es nicht — deshalb ist dieses Verzeichnis die Bedingung dafuer, dass etwas entfernt werden darf. Ruf das auf, BEVOR du speicher_abschaffen benutzt."""
        return bridge.speicher_rueckweg()

    @mcp.tool(annotations=udb_write)
    def speicher_abschaffen(pfad: str) -> dict:
        """Einen Altbestandsposten entfernen (abgeschaffte Modelle, Frank-Reste). ⚠️ Nur Pfade, die WOERTLICH in der handgepflegten Liste auf dem Wirt stehen — alles andere wird abgewiesen, auch wenn es nach Muell aussieht. Und nur, wenn der Rueckweg schon geschrieben ist. Frag den Menschen, bevor du das benutzt: Altbestand ist nicht Muell."""
        return bridge.speicher_abschaffen(pfad)

    @mcp.tool(annotations=udb_write)
    def speicher_aufraeumen(nur_zeigen: bool = True) -> dict:
        """Wegwerfkopien und Bau-Zwischenlager entfernen lassen. Vorgabe ist ZEIGEN -- sieh erst, was verschwaende, dann setze nur_zeigen=false. ⚠️ Du bestimmst NICHT, was Muell ist: Muster, Mindestalter und die namentliche Liste des Unantastbaren (wiki.db, unifieddb, die Repos, die ausgelieferten Seiten) stehen auf dem Wirt und sind von hier nicht zu beeinflussen."""
        return bridge.speicher_aufraeumen(nur_zeigen)

    @mcp.tool(annotations=udb_ro)
    def werkbank_stand(repo: str = "/var/lib/clay/arbeit/seimensch") -> dict:
        """Was ist in der Arbeitskopie geaendert und noch nicht veroeffentlicht."""
        return bridge.werkbank_stand(repo)

    @mcp.tool(annotations=udb_write)
    def werkbank_veroeffentlichen(nachricht: str, repo: str = "/var/lib/clay/arbeit/seimensch") -> dict:
        """Committen und pushen -- der EINZIGE Weg nach draussen. ⚠️ Bei SeiMensch geht ein Push auf main SOFORT oeffentlich. Die Nachricht muss sagen WARUM, nicht nur WAS. Pruefe danach die Seite, statt Erfolg zu behaupten."""
        return bridge.werkbank_veroeffentlichen(nachricht, repo)

    @mcp.tool(annotations=udb_write)
    def abruf_rueckmeldung(bewertung: str, zuege: int = 1) -> dict:
        """Sag dem Abruf, ob die zuletzt hervorgeholten Erinnerungen getaugt haben.

        bewertung: `geholfen` oder `daneben`.
        zuege: wie viele der letzten Abrufe gemeint sind (1-10, Vorgabe 1).

        Wirkt NUR auf die Wegpunkt-Prioren -- kein Gedaechtnisinhalt, keine
        Wahrheit, keine Befugnis wird dadurch geaendert. Wer bewertet, steht
        fest (angemeldete Sitzung); fremde Abrufe sind nicht erreichbar.

        ⚠️ Benutze das, wenn ein Mensch dir sagt, die Erinnerung sei falsch oder
        hilfreich gewesen. Ohne diese Rueckmeldung lernt der Abruf nur aus
        verifizierten Wirkungen -- also fast nie.
        """
        return bridge.abruf_rueckmeldung(bewertung, zuege)

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
