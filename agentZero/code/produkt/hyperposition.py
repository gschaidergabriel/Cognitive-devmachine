from __future__ import annotations

import hashlib
import re
import json
from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class Facet:
    value: str
    source_turn_id: str | None
    user_id: str | None
    ts: float | None
    provenance: Any


@dataclass(frozen=True)
class HyperpositionReadout:
    relation_id: str
    relation_key: str
    subject: str
    kind: str
    facets: tuple[Facet, ...]
    semantic_hash: str
    alternative_count: int
    uncertainty: float

    def as_dict(self) -> dict:
        data = asdict(self)
        data["facets"] = [asdict(x) for x in self.facets]
        data["truth_promoted"] = False
        data["effect_authority"] = False
        data["backend"] = "set-valued-faceted-runtime-v2"
        return data


class HyperpositionProjector:
    """Conservative set-valued projection over explicitly related evidence.

    A user, memory kind, or broad subject is not a semantic relation. Facets therefore
    coexist only when provenance supplies an explicit ``relation_key`` (preferred) or a
    predicate that can be combined with the subject. This prevents unrelated facts from
    being misclassified as competing alternatives. The projection never chooses truth
    and never grants effect authority.
    """

    @staticmethod
    def _stable_json(value: Any) -> str:
        try:
            return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        except TypeError:
            return json.dumps(str(value), ensure_ascii=False)

    @staticmethod
    def _provenance(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value
        if isinstance(value, str):
            try:
                decoded = json.loads(value)
            except json.JSONDecodeError:
                return {}
            return decoded if isinstance(decoded, dict) else {}
        return {}

    # ⭐⭐ WARUM ES HIER EINEN RUECKFALL BRAUCHT.
    # Gemessen 2026-08-21: dieser Projektor lieferte an fuenf von fuenf echten
    # Fragen **eine leere Liste** -- seit dem Bau. Der Grund steht direkt
    # darunter: er verlangt einen `relation_key` oder ein `predicate` aus der
    # Provenienz, und die Gedaechtnis-Extraktion schreibt beides **nie**. Ein
    # Bauteil, dessen Vorbedingung niemand erfuellt, ist kein Bauteil.
    #
    # ⚠️ DER NAHELIEGENDE RUECKFALL WAERE FALSCH. `subject::kind` als Schluessel
    # zu nehmen sieht bequem aus und ist Unsinn: dann gehoerten ALLE `fact`-
    # Eintraege ueber Gabriel in eine Gruppe, und je zwei verschiedene Tatsachen
    # ueber ihn -- der Pfad der Arbeitskopie und der Name seines Rechners --
    # erschienen als "gleichzeitig gueltige Lesarten" desselben Sachverhalts.
    # Das ist keine Mehrdeutigkeit, das ist ein Kategorienfehler, und er wuerde
    # den Kontext mit erfundenen Widerspruechen fluten.
    #
    # Der Rueckfall haengt deshalb am GEGENSTAND: zwei Eintraege gehoeren
    # zusammen, wenn sie von derselben Sache handeln. Als Naeherung dafuer die
    # zwei laengsten Inhaltswoerter des Werts -- lange Woerter sind im Deutschen
    # die spezifischen ("Pruefrechner", "Arbeitskopie"), kurze die allgemeinen.
    # Umlautfrei verglichen, weil derselbe Gegenstand mal so und mal so
    # geschrieben wird (gemessen: "Prüfrechner" gegen "Pruefrechner").
    _UMLAUT = ((chr(228), "ae"), (chr(246), "oe"), (chr(252), "ue"), (chr(223), "ss"))
    _ALLERWELT = frozenset((
        "dass", "diese", "dieser", "dieses", "einem", "einen", "einer", "eines",
        "haben", "heisst", "immer", "nicht", "oder", "seine", "sich", "sind",
        "ueber", "unter", "wenn", "werden", "wird", "wurde", "seinem", "ihrem",
    ))

    # Ab dieser Laenge gilt ein Wort als spezifisch genug, um zwei Aussagen
    # ueberhaupt auf denselben Gegenstand zu beziehen.
    _GEGENSTAND_MIN = 8
    # Ein Wort, das in zu vielen Eintraegen vorkommt, ist ein THEMA, kein
    # Gegenstand ("seimensch" steht in dreissig Notizen). Solche Woerter
    # gruppieren nichts, sie fluten nur.
    _GEGENSTAND_MAX_EINTRAEGE = 3

    @classmethod
    def _worte(cls, wert: str) -> set:
        """Spezifische Inhaltswoerter eines Werts, umlautfrei."""
        t = str(wert or "").lower()
        for zeichen, ersatz in cls._UMLAUT:
            t = t.replace(zeichen, ersatz)
        return {w for w in re.findall(r"[a-z0-9_-]{%d,}" % cls._GEGENSTAND_MIN, t)
                if w not in cls._ALLERWELT}

    @classmethod
    def _relation_key(cls, memory: dict[str, Any]) -> str | None:
        provenance = cls._provenance(memory.get("provenance"))
        explicit = provenance.get("relation_key")
        if isinstance(explicit, str) and explicit.strip():
            return explicit.strip()
        predicate = provenance.get("predicate")
        subject = memory.get("subject")
        if isinstance(predicate, str) and predicate.strip() and isinstance(subject, str) and subject.strip():
            return f"{subject.strip()}::{predicate.strip()}"
        return None

    @classmethod
    def _gegenstands_gruppen(cls, memories: list) -> dict:
        """Ohne ausdrueckliche Provenienz: gruppiere ueber GETEILTE Woerter.

        ⚠️ Zweiter Anlauf. Der erste bildete einen Schluessel aus den laengsten
        Woertern JEDES Eintrags -- und nahm damit ausgerechnet das
        unterscheidende Wort mit auf ("pruefrechner+quirlbaum-8" gegen
        "faltbogen-3+pruefrechner"). Jeder Wert bekam seine eigene Gruppe, und
        gruppiert wurde nie. Ein Schluessel, der den Unterschied enthaelt, kann
        nichts zusammenfuehren.

        Richtig ist die andere Richtung: nicht je Eintrag einen Schluessel
        rechnen, sondern die Eintraege ueber das vergleichen, was sie TEILEN.
        Zwei Aussagen gehoeren zusammen, wenn sie ein spezifisches Wort
        gemeinsam haben -- und sie sind erst dann mehrdeutig, wenn ihre Werte
        sich unterscheiden.

        Zwei Sperren gegen Flutung: das Wort muss lang genug sein
        (`_GEGENSTAND_MIN`), und es darf nicht in zu vielen Eintraegen stehen
        (`_GEGENSTAND_MAX_EINTRAEGE`) -- sonst ist es ein Thema und kein
        Gegenstand.
        """
        vorkommen: dict[str, list] = {}
        for m in memories:
            for w in cls._worte(m.get("value")):
                vorkommen.setdefault(w, []).append(m)
        raus: dict[str, list] = {}
        for wort, eintraege in vorkommen.items():
            if not (2 <= len(eintraege) <= cls._GEGENSTAND_MAX_EINTRAEGE):
                continue
            if len({str(m.get("value")) for m in eintraege}) < 2:
                continue
            raus[wort] = eintraege
        return raus

    @classmethod
    def from_world(cls, world: dict, *, max_relations: int = 32, max_facets: int = 8) -> list[dict]:
        groups: dict[tuple[str, str, str], list[Facet]] = {}
        # Eintraege ohne ausdrueckliche Provenienz bekommen ihren Schluessel aus
        # dem, was sie mit anderen TEILEN (siehe _gegenstands_gruppen). Ohne
        # diesen Rueckfall lieferte der Projektor seit dem Bau immer [] -- die
        # Extraktion schreibt naemlich nie einen `relation_key`.
        brauchbar = [m for m in world.get("durable_memory", [])
                     if isinstance(m, dict) and str(m.get("value", ""))
                     and str(m.get("kind", "memory")) not in {"compression_receipt",
                                                              "source_archive"}]
        geteilt = {}
        for wort, eintraege in cls._gegenstands_gruppen(
                [m for m in brauchbar if cls._relation_key(m) is None]).items():
            for m in eintraege:
                geteilt.setdefault(id(m), f"gegenstand::{wort}")
        for memory in brauchbar:
            kind = str(memory.get("kind", "memory"))
            subject = str(memory.get("subject", "shared"))
            value = str(memory.get("value", ""))
            relation_key = cls._relation_key(memory) or geteilt.get(id(memory))
            if relation_key is None:
                continue
            facet = Facet(
                value=value,
                source_turn_id=memory.get("source_turn_id"),
                user_id=memory.get("user_id"),
                ts=float(memory["ts"]) if isinstance(memory.get("ts"), (int, float)) else None,
                provenance=memory.get("provenance"),
            )
            groups.setdefault((kind, subject, relation_key), []).append(facet)

        readouts: list[dict] = []
        for (kind, subject, relation_key), facets in sorted(groups.items()):
            unique: dict[str, Facet] = {}
            for facet in sorted(facets, key=lambda x: (x.ts or 0.0, x.value), reverse=True):
                unique.setdefault(facet.value, facet)
            if len(unique) < 2:
                continue
            bounded = tuple(list(unique.values())[:max_facets])
            semantic_payload = {
                "kind": kind,
                "relation_key": relation_key,
                "members": sorted(x.value for x in bounded),
            }
            semantic_hash = hashlib.sha256(cls._stable_json(semantic_payload).encode()).hexdigest()
            relation_id = "hyper:" + semantic_hash[:24]
            readout = HyperpositionReadout(
                relation_id=relation_id,
                relation_key=relation_key,
                subject=subject,
                kind=kind,
                facets=bounded,
                semantic_hash=semantic_hash,
                alternative_count=len(bounded),
                uncertainty=min(1.0, (len(bounded) - 1) / max(1, len(bounded))),
            )
            readouts.append(readout.as_dict())
            if len(readouts) >= max_relations:
                break
        return readouts
