from __future__ import annotations

import hashlib
import json
import math
import re
import time
import uuid
from dataclasses import dataclass
from typing import Any

from .store import StaleGeneration, UnifiedDB

_TOKEN = re.compile(r"[\w.-]{2,}", re.UNICODE)


@dataclass(frozen=True)
class RetrievalCandidate:
    memory_id: str
    kind: str
    subject: str
    value: str
    ts: float
    provenance: dict[str, Any]
    baseline_score: float
    adaptive_score: float
    entry_keys: tuple[str, ...]

    def public(self) -> dict[str, Any]:
        return {
            "memory_id": self.memory_id,
            "kind": self.kind,
            "subject": self.subject,
            "value": self.value,
            "ts": self.ts,
            "provenance": self.provenance,
            "retrieval_score": self.baseline_score,
        }


class MicroClayRetrieval:
    """Persistent bounded online-adaptive retrieval organ.

    MicroClay changes accessibility, entry-point priors and context packing only.
    It cannot alter semantic truth, durable memory contents, provenance, user rights,
    effect authority or EntityOS capabilities.

    The adaptive policy starts in SHADOW. Classical retrieval remains the serving
    path until an explicit externally validated promotion changes the mode.
    """

    POLICY_VERSION = 1
    DEFAULT_MODE = "SHADOW"
    MAX_SOURCE_ROWS = 5000
    MAX_QUERY_TOKENS = 64
    MAX_ENTRY_KEYS = 24
    CAPITAL_MIN = -2.0
    CAPITAL_MAX = 4.0
    LEARNING_RATE = 0.20
    REWARD_EMA_ALPHA = 0.10
    ACCESS_RENT = 0.005

    def __init__(self, db: UnifiedDB):
        self.db = db

    @staticmethod
    def _tokens(text: str) -> set[str]:
        return {x.lower() for x in _TOKEN.findall(text or "")[:256]}

    @staticmethod
    def _token_key(token: str) -> str:
        return "cue:" + hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]

    @staticmethod
    def _safe_provenance(raw: str) -> dict[str, Any]:
        try:
            value = json.loads(raw)
            return value if isinstance(value, dict) else {"raw_type": type(value).__name__}
        except Exception:
            return {"parse_error": True}

    def mode(self) -> str:
        row = self.db.db.execute(
            "SELECT mode FROM retrieval_policy_state WHERE singleton=1"
        ).fetchone()
        return row["mode"] if row else self.DEFAULT_MODE

    def _policy_capitals(self) -> dict[str, float]:
        return {
            str(row["entry_key"]): float(row["capital"])
            for row in self.db.db.execute(
                "SELECT entry_key,capital FROM retrieval_entrypoint_policy"
            ).fetchall()
        }

    def _entry_keys(
        self,
        kind: str,
        subject: str,
        query_tokens: set[str],
        value_tokens: set[str],
    ) -> tuple[str, ...]:
        keys = [f"kind:{kind}", f"subject:{subject}"]
        for token in sorted(query_tokens.intersection(value_tokens))[: self.MAX_ENTRY_KEYS - 2]:
            keys.append(self._token_key(token))
        return tuple(keys)

    def _score_candidate(
        self,
        row,
        query_tokens: set[str],
        now: float,
        capitals: dict[str, float],
    ) -> RetrievalCandidate:
        value = str(row["value"])
        subject = str(row["subject"])
        kind = str(row["kind"])
        value_tokens = self._tokens(value + " " + subject + " " + kind)
        if query_tokens:
            overlap = len(query_tokens.intersection(value_tokens))
            coverage = overlap / max(1, len(query_tokens))
            precision = overlap / max(1, len(value_tokens))
            lexical = min(1.0, 0.75 * coverage + 0.25 * precision)
        else:
            lexical = 0.0

        age_days = max(0.0, (now - float(row["ts"])) / 86400.0)
        recency = math.exp(-age_days / 30.0)
        structured = 1.0 if kind in {
            "fact", "decision", "task", "commitment", "preference", "open", "open_question"
        } else 0.4
        # No cue match means UNKNOWN, not "probably relevant because recent". The
        # recent 20-turn working window handles conversational continuity separately.
        baseline = (
            (0.82 * lexical) + (0.12 * recency) + (0.06 * structured)
            if lexical > 0.0 else 0.0
        )

        keys = self._entry_keys(kind, subject, query_tokens, value_tokens)
        learned = sum(
            max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, capitals.get(k, 0.0)))
            for k in keys
        )
        learned /= max(1, len(keys))
        adaptive = baseline + 0.08 * learned

        return RetrievalCandidate(
            memory_id=str(row["memory_id"]),
            kind=kind,
            subject=subject,
            value=value,
            ts=float(row["ts"]),
            provenance=self._safe_provenance(row["provenance"]),
            baseline_score=baseline,
            adaptive_score=adaptive,
            entry_keys=keys,
        )

    def learn_from_verified_outcomes(self, *, session_id: str, generation: int) -> dict[str, int]:
        """Consume new effect-outcome receipts from earlier retrieval episodes.

        Learning is delayed until a causally re-entered external outcome exists. Pure
        conversational completion is not treated as reward, avoiding self-reinforcing
        "the retriever liked its own result" feedback. Automatic effect-derived learning
        accepts only verified outcomes with non-zero canonical credit; uncertain/stale,
        denied/failed, and verified zero-credit outcomes remain evidence-neutral here.
        Explicit correction/miss feedback may still use ``credit()`` directly.

        ⭐ KEIN Generationszaun auf den Episoden. Eine Belohnung entsteht bei der
        Wirkung, gebucht wird sie erst beim naechsten Abruf. Zaehlte die Generation
        dazwischen hoch -- und sie zaehlt bei jedem Neustart hoch --, fiel die
        Belohnung durch den Rost und war fuer immer weg: gemessen Generation 101
        gegen juengste Episode 98, also alles. Gegen doppeltes Lernen schuetzt die
        Quittung in ``retrieval_feedback`` (NOT EXISTS oben), nicht die Generation.
        """
        self.db.assert_live_generation(session_id, generation)
        rows = self.db.db.execute(
            "SELECT r.*,c.credit AS outcome_credit,e.status AS effect_status "
            "FROM retrieval_episodes r "
            "JOIN causal_episodes c ON c.causal_id=r.causal_id "
            "JOIN effects e ON e.effect_id=c.effect_id "
            "WHERE r.session_id=? AND c.reentered=1 "
            "AND e.status='VERIFIED' AND c.credit != 0.0 "
            "AND NOT EXISTS(SELECT 1 FROM retrieval_feedback f "
            "WHERE f.retrieval_id=r.retrieval_id AND f.signal_class LIKE 'effect_outcome:%') "
            "ORDER BY r.ts LIMIT 100",
            (session_id,),
        ).fetchall()
        applied = 0
        for row in rows:
            result = self._apply_credit(
                row,
                credit=float(row["outcome_credit"]),
                signal_class=f"effect_outcome:{row['effect_status']}",
            )
            applied += int(bool(result.get("applied")))
        return {"eligible": len(rows), "applied": applied}

    # ── Die Tuer fuer das Urteil eines Menschen ───────────────────────────
    #
    # ⭐ Der automatische Weg oben lernt NUR aus einer verifizierten aeusseren
    # Wirkung. Ein Mensch, der sagt "das war falsch", erzeugt keine Wirkung --
    # ohne diese Tuer erreicht sein Urteil das Lernen nie, egal wie deutlich er
    # es sagt. Genau das war der Befund: credit() existierte, aber kein einziger
    # Aufrufer fuehrte von einem Menschen dorthin.

    GEWICHTE = {"geholfen": 1.0, "daneben": -1.0}
    MAX_RUECKMELDUNG_ZUEGE = 10

    def menschliche_rueckmeldung(
        self,
        *,
        session_id: str,
        user_id: str,
        bewertung: str,
        zuege: int = 1,
    ) -> dict[str, Any]:
        """Ausdrueckliche Rueckmeldung eines Menschen auf die letzten Abrufe buchen.

        ``user_id`` grenzt die Episoden mit ein: niemand bewertet fremde Abrufe.
        Die Kennung ist die geprueften Anmeldung des Aufrufers, nie ein Argument.

        Aendert nur Wegpunkt-Prioren -- kein Gedaechtnisinhalt, keine Wahrheit,
        keine Befugnis. Zweimal dieselbe Rueckmeldung bucht genau einmal, weil
        die Quittungskennung aus Episode, Generation, Klasse und Wert entsteht.
        """
        if bewertung not in self.GEWICHTE:
            raise ValueError(
                f"unbekannte bewertung. erlaubt: {sorted(self.GEWICHTE)}"
            )
        anzahl = max(1, min(int(zuege), self.MAX_RUECKMELDUNG_ZUEGE))
        rows = self.db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE session_id=? AND user_id=? "
            "ORDER BY ts DESC LIMIT ?",
            (session_id, user_id, anzahl),
        ).fetchall()

        wegpunkte_vorher = int(
            self.db.db.execute(
                "SELECT COUNT(*) FROM retrieval_entrypoint_policy"
            ).fetchone()[0]
        )
        gewicht = self.GEWICHTE[bewertung]
        signal_class = f"mensch:{bewertung}"
        gebucht, schon_bekannt = [], []
        for row in rows:
            ergebnis = self._apply_credit(
                row, credit=gewicht, signal_class=signal_class
            )
            eintrag = {
                "abruf_id": str(row["retrieval_id"]),
                "causal_id": str(row["causal_id"]),
                "generation": int(row["generation"]),
                "wegpunkte": len(json.loads(row["entry_keys"])),
            }
            if ergebnis.get("applied"):
                eintrag["quittung"] = ergebnis["receipt_id"]
                gebucht.append(eintrag)
            else:
                eintrag["grund"] = ergebnis.get("reason", "unbekannt")
                schon_bekannt.append(eintrag)
        wegpunkte_nachher = int(
            self.db.db.execute(
                "SELECT COUNT(*) FROM retrieval_entrypoint_policy"
            ).fetchone()[0]
        )
        return {
            "bewertung": bewertung,
            "gewicht": gewicht,
            "gefundene_abrufe": len(rows),
            "gebucht": gebucht,
            "folgenlos": schon_bekannt,
            "angewandt": len(gebucht),
            "wegpunkte_vorher": wegpunkte_vorher,
            "wegpunkte_nachher": wegpunkte_nachher,
            # Ohne diesen Satz liest ein Modell "angewandt: 0" als Fehler. Es ist
            # keiner -- es heisst, die Rueckmeldung lag schon vor.
            "hinweis": (
                "keine Abrufe in dieser Sitzung -- nichts zu bewerten"
                if not rows
                else "angewandt=0 heisst: dieselbe Rueckmeldung lag bereits vor"
            ),
        }

    # ── Befoerderung: SHADOW -> ACTIVE ─────────────────────────────────────
    #
    # ⭐ Bis hierher schrieb NICHTS ausser der Tabellenerzeugung selbst in
    # ``retrieval_policy_state`` -- der Modus blieb fuer immer SHADOW, egal wie
    # viel geprueftes Lernsignal in ``retrieval_entrypoint_policy`` ankam. Die
    # Klassendoku sagt "bis eine explizit extern validierte Befoerderung den
    # Modus aendert" -- diese Befoerderung existierte nirgends im Code. Reine
    # Beobachtung ohne einen Uebergang ist keine SHADOW-Politik, sondern eine
    # Sackgasse, die wie eine Politik aussieht.
    #
    # "Extern validiert" wird hier NICHT selbst behauptet, sondern an zwei
    # mechanische, im Store bereits vorhandene Tatsachen gebunden:
    #   (a) mindestens MIN_SCHLUESSEL gelernte Eintrittspunkte mit >=1 Pull --
    #       roher Beweis, dass ueberhaupt etwas gelernt wurde, kein leerer Start.
    #   (b) mindestens MIN_QUITTUNGEN VERSCHIEDENE Rueckmeldungs-Quittungen in
    #       ``retrieval_feedback`` -- nicht dieselbe Buchung, die zufaellig
    #       mehrere Eintrittspunkte trifft. Eine Quittung ist entweder ein
    #       verifizierter aeusserer Wirkungsnachweis (``effect_outcome:*``) oder
    #       ein ausdrueckliches menschliches Urteil (``mensch:*``) -- niemals
    #       die eigene Ausgabe des Retrievers selbst (kein Echo-Kreislauf).
    #
    # Nur EIN Weg, absichtlich: SHADOW->ACTIVE. Ein automatischer Rueckfall
    # ACTIVE->SHADOW waere eine Notbremse und gehoert dort hin, nicht hierher
    # als Nebenwirkung einer Zaehlfunktion.

    MIN_SCHLUESSEL_FUER_AKTIV = 3
    MIN_QUITTUNGEN_FUER_AKTIV = 2

    def befoerderung_pruefen(self) -> dict[str, Any]:
        """Prueft das validierte Lernsignal und hebt SHADOW auf ACTIVE, wenn genug da ist.

        Rein mechanisch, kein Modellaufruf, keine Behauptung ohne Beleg -- die
        Rueckgabe traegt immer die Rohzahlen, gegen die geprueft wurde.
        """
        vorher = self.mode()
        schluessel = int(
            self.db.db.execute(
                "SELECT COUNT(*) FROM retrieval_entrypoint_policy WHERE pulls>=1"
            ).fetchone()[0]
        )
        quittungen = int(
            self.db.db.execute(
                "SELECT COUNT(DISTINCT receipt_id) FROM retrieval_feedback"
            ).fetchone()[0]
        )
        ergebnis: dict[str, Any] = {
            "modus_vorher": vorher,
            "gelernte_schluessel": schluessel,
            "schwelle_schluessel": self.MIN_SCHLUESSEL_FUER_AKTIV,
            "quittungen": quittungen,
            "schwelle_quittungen": self.MIN_QUITTUNGEN_FUER_AKTIV,
        }
        if vorher == "ACTIVE":
            ergebnis["befoerdert"] = False
            ergebnis["modus_nachher"] = "ACTIVE"
            ergebnis["grund"] = "bereits ACTIVE"
            return ergebnis
        if schluessel < self.MIN_SCHLUESSEL_FUER_AKTIV or quittungen < self.MIN_QUITTUNGEN_FUER_AKTIV:
            ergebnis["befoerdert"] = False
            ergebnis["modus_nachher"] = "SHADOW"
            ergebnis["grund"] = "noch nicht genug validiertes Lernsignal"
            return ergebnis
        now = time.time()
        self.db.db.execute(
            "UPDATE retrieval_policy_state SET mode='ACTIVE', "
            "policy_version=policy_version+1, updated_at=? WHERE singleton=1",
            (now,),
        )
        ergebnis["befoerdert"] = True
        ergebnis["modus_nachher"] = "ACTIVE"
        ergebnis["grund"] = "Schwellen erreicht: gelernte Eintrittspunkte + unabhaengige Quittungen"
        return ergebnis

    def retrieve(
        self,
        *,
        query: str,
        user_id: str,
        session_id: str,
        turn_id: str,
        episode_id: str,
        causal_id: str,
        generation: int,
        limit: int = 24,
        budget_chars: int = 12_000,
    ) -> dict[str, Any]:
        if not isinstance(query, str) or not query.strip():
            raise ValueError("MicroClay retrieval requires a non-empty query")
        if limit < 1 or limit > 100:
            raise ValueError("invalid retrieval limit")
        if budget_chars < 256 or budget_chars > 200_000:
            raise ValueError("invalid retrieval budget")
        self.db.assert_live_generation(session_id, generation)
        learned_outcomes = self.learn_from_verified_outcomes(
            session_id=session_id,
            generation=generation,
        )

        query_hash = hashlib.sha256(query.encode("utf-8")).hexdigest()
        existing = self.db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=?",
            (causal_id,),
        ).fetchone()
        if existing:
            if (
                existing["session_id"] != session_id
                or int(existing["generation"]) != int(generation)
                or existing["query_hash"] != query_hash
            ):
                raise StaleGeneration("retrieval_identity")
            ids = json.loads(existing["selected_memory_ids"])
            by_id = {
                str(row["memory_id"]): row
                for row in self.db.db.execute(
                    "SELECT * FROM durable_memory WHERE memory_id IN (%s)"
                    % ",".join("?" for _ in ids),
                    tuple(ids),
                ).fetchall()
            } if ids else {}
            items = []
            for memory_id in ids:
                row = by_id.get(memory_id)
                if row is not None:
                    items.append({
                        "memory_id": memory_id,
                        "kind": row["kind"],
                        "subject": row["subject"],
                        "value": row["value"],
                        "ts": float(row["ts"]),
                        "provenance": self._safe_provenance(row["provenance"]),
                        "retrieval_score": None,
                    })
            return {
                "items": items,
                "receipt": {
                    "retrieval_id": existing["retrieval_id"],
                    "policy_version": int(existing["policy_version"]),
                    "mode": existing["mode"],
                    "query_sha256": existing["query_hash"],
                    "candidate_count": None,
                    "selected_count": len(items),
                    "chars_selected": int(existing["chars_selected"]),
                    "status": existing["status"],
                    "shadow_differs": json.loads(existing["selected_memory_ids"]) != json.loads(existing["shadow_memory_ids"]),
                    "truth_authority": False,
                    "effect_authority": False,
                    "outcome_learning_applied": learned_outcomes["applied"],
                    "replayed": True,
                },
            }

        query_tokens = set(sorted(self._tokens(query))[: self.MAX_QUERY_TOKENS])
        rows = self.db.db.execute(
            "SELECT * FROM durable_memory "
            "WHERE kind NOT IN ('source_archive','compression_receipt','compression_clearance') "
            "AND (user_id IS NULL OR user_id=?) "
            "AND (source_turn_id IS NULL OR source_turn_id<>?) "
            "ORDER BY ts DESC LIMIT ?",
            (user_id, turn_id, self.MAX_SOURCE_ROWS),
        ).fetchall()
        now = time.time()
        capitals = self._policy_capitals()
        candidates = [self._score_candidate(row, query_tokens, now, capitals) for row in rows]
        baseline = sorted(
            candidates,
            key=lambda x: (x.baseline_score, x.ts, x.memory_id),
            reverse=True,
        )
        adaptive = sorted(
            candidates,
            key=lambda x: (x.adaptive_score, x.ts, x.memory_id),
            reverse=True,
        )

        mode = self.mode()
        serving = adaptive if mode == "ACTIVE" else baseline
        selected: list[RetrievalCandidate] = []
        chars = 0
        for item in serving:
            if item.baseline_score <= 0.0:
                continue
            item_chars = len(item.value)
            if selected and chars + item_chars > budget_chars:
                continue
            selected.append(item)
            chars += item_chars
            if len(selected) >= limit:
                break

        retrieval_id = str(uuid.uuid4())
        token_hashes = [self._token_key(x)[4:] for x in sorted(query_tokens)]
        selected_ids = [x.memory_id for x in selected]
        shadow_ids = [x.memory_id for x in adaptive if x.baseline_score > 0.0][:limit]
        entry_keys = sorted({k for item in selected for k in item.entry_keys})[:256]

        self.db.db.execute(
            "INSERT INTO retrieval_episodes("
            "retrieval_id,turn_id,episode_id,causal_id,session_id,user_id,generation,"
            "policy_version,mode,query_hash,query_token_hashes,selected_memory_ids,"
            "shadow_memory_ids,entry_keys,budget_chars,chars_selected,status,ts"
            ") VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                retrieval_id, turn_id, episode_id, causal_id, session_id, user_id, int(generation),
                self.POLICY_VERSION, mode, query_hash, json.dumps(token_hashes),
                json.dumps(selected_ids), json.dumps(shadow_ids), json.dumps(entry_keys),
                int(budget_chars), int(chars),
                "PRESENT" if selected else "UNKNOWN", now,
            ),
        )

        return {
            "items": [x.public() for x in selected],
            "receipt": {
                "retrieval_id": retrieval_id,
                "policy_version": self.POLICY_VERSION,
                "mode": mode,
                "query_sha256": query_hash,
                "candidate_count": len(candidates),
                "selected_count": len(selected),
                "chars_selected": chars,
                "status": "PRESENT" if selected else "UNKNOWN",
                "shadow_differs": selected_ids != shadow_ids,
                "truth_authority": False,
                "effect_authority": False,
                "outcome_learning_applied": learned_outcomes["applied"],
            },
        }

    def credit(
        self,
        *,
        causal_id: str,
        generation: int,
        credit: float,
        signal_class: str,
        receipt_id: str | None = None,
    ) -> dict[str, Any]:
        """Apply provenance-bound outcome credit to retrieval policy only.

        Replaying the same receipt is idempotent; stale generations are rejected.
        No durable-memory row is changed.
        """
        row = self.db.db.execute(
            "SELECT * FROM retrieval_episodes WHERE causal_id=? ORDER BY ts DESC LIMIT 1",
            (causal_id,),
        ).fetchone()
        if not row:
            return {"applied": False, "reason": "no_retrieval_episode"}
        if int(row["generation"]) != int(generation):
            raise StaleGeneration("retrieval_generation")
        self.db.assert_live_generation(row["session_id"], generation)
        return self._apply_credit(
            row, credit=credit, signal_class=signal_class, receipt_id=receipt_id
        )

    def _apply_credit(
        self,
        row: Any,
        *,
        credit: float,
        signal_class: str,
        receipt_id: str | None = None,
    ) -> dict[str, Any]:
        """Die Buchung selbst, ohne Generationszaun. Nur fuer Aufrufer im Haus.

        WARUM ohne Zaun: gebucht werden ausschliesslich
        ``retrieval_entrypoint_policy`` und ``retrieval_feedback``. Beide sind
        generationsfrei -- es gibt hier keinen Weltzustand, in den eine veraltete
        Annahme hineinschreiben koennte. Der Zaun in ``credit()`` schuetzt einen
        AUFRUFER davor, mit einer ueberholten Generationsannahme zu buchen. Wer die
        Generation direkt aus der Episodenzeile nimmt, kann sich darin gar nicht
        irren -- fuer den ist der Zaun kein Schutz, sondern ein Vernichter: jede
        Belohnung, deren Generation zwischen Wirkung und Buchung hochzaehlt, waere
        endgueltig verloren.

        Die Generation der Episode wandert unveraendert in die Quittungskennung,
        damit dieselbe Rueckmeldung dieselbe Kennung ergibt und ein zweites Mal
        folgenlos bleibt.
        """
        value = max(-1.0, min(1.0, float(credit)))
        # Beides aus der Episodenzeile, nicht aus Argumenten: so kann die
        # Quittungskennung gar nicht von der Wirklichkeit abweichen.
        generation = int(row["generation"])
        causal_id = str(row["causal_id"])

        rid = receipt_id or hashlib.sha256(
            f"{row['retrieval_id']}\x1f{causal_id}\x1f{generation}\x1f{signal_class}\x1f{value:.9f}".encode()
        ).hexdigest()
        exists = self.db.db.execute(
            "SELECT 1 FROM retrieval_feedback WHERE receipt_id=?", (rid,)
        ).fetchone()
        if exists:
            return {"applied": False, "reason": "duplicate_receipt", "receipt_id": rid}

        keys = json.loads(row["entry_keys"])
        now = time.time()
        for key in keys:
            current = self.db.db.execute(
                "SELECT capital,reward_ema,pulls FROM retrieval_entrypoint_policy WHERE entry_key=?",
                (key,),
            ).fetchone()
            if current:
                old_capital = float(current["capital"])
                old_ema = float(current["reward_ema"])
                pulls = int(current["pulls"])
            else:
                old_capital, old_ema, pulls = 0.0, 0.0, 0
            new_ema = (1.0 - self.REWARD_EMA_ALPHA) * old_ema + self.REWARD_EMA_ALPHA * value
            delta = self.LEARNING_RATE * (value - old_ema) - self.ACCESS_RENT
            new_capital = max(self.CAPITAL_MIN, min(self.CAPITAL_MAX, old_capital + delta))
            self.db.db.execute(
                "INSERT INTO retrieval_entrypoint_policy(entry_key,capital,reward_ema,pulls,updated_at) "
                "VALUES(?,?,?,?,?) ON CONFLICT(entry_key) DO UPDATE SET "
                "capital=excluded.capital,reward_ema=excluded.reward_ema,"
                "pulls=excluded.pulls,updated_at=excluded.updated_at",
                (key, new_capital, new_ema, pulls + 1, now),
            )

        self.db.db.execute(
            "INSERT INTO retrieval_feedback(receipt_id,retrieval_id,causal_id,generation,"
            "credit,signal_class,ts) VALUES(?,?,?,?,?,?,?)",
            (rid, row["retrieval_id"], causal_id, int(generation), value, str(signal_class)[:80], now),
        )
        return {
            "applied": True,
            "receipt_id": rid,
            "policy_version": self.POLICY_VERSION,
            "mode": row["mode"],
            "updated_entrypoints": len(keys),
            "truth_authority": False,
            "effect_authority": False,
        }
