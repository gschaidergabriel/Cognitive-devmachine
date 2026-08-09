from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import json
import re
from typing import Any, Mapping

SCHEMA_VERSION = "h1-needle-boundary-0.1"
AUTHORITY_NONE = "NONE"
SEMANTIC_LANGUAGE_CLAY = "CLAY"
_ALLOWED_PROPOSAL_CLASSES = {"OBSERVATION", "ROUTE_PROPOSAL", "OBSERVATION_OR_ROUTE_PROPOSAL"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


class NeedleBoundaryError(ValueError):
    pass


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _require_nonempty(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise NeedleBoundaryError(f"{name} must be non-empty")


def _require_sha256(name: str, value: str) -> None:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise NeedleBoundaryError(f"{name} must be a lowercase sha256 hex digest")


@dataclass(frozen=True)
class TranslatorReceipt:
    translator_id: str
    translator_version: str
    source_language: str
    source_text_sha256: str
    normalized_text_sha256: str

    def validate(self) -> None:
        for name in ("translator_id", "translator_version", "source_language"):
            _require_nonempty(name, getattr(self, name))
        _require_sha256("source_text_sha256", self.source_text_sha256)
        _require_sha256("normalized_text_sha256", self.normalized_text_sha256)


@dataclass(frozen=True)
class NeedleReceipt:
    needle_id: str
    needle_version: str
    input_sha256: str
    route: str
    certificate_id: str
    certificate_sha256: str
    semantic_language: str
    proposal_class: str
    payload_clay: str
    authority_claim: str = AUTHORITY_NONE

    def validate(self) -> None:
        for name in ("needle_id", "needle_version", "route", "certificate_id", "payload_clay"):
            _require_nonempty(name, getattr(self, name))
        _require_sha256("input_sha256", self.input_sha256)
        _require_sha256("certificate_sha256", self.certificate_sha256)
        if self.semantic_language != SEMANTIC_LANGUAGE_CLAY:
            raise NeedleBoundaryError("Needle bridge output must enter the cognitive boundary as CLAY")
        if self.proposal_class not in _ALLOWED_PROPOSAL_CLASSES:
            raise NeedleBoundaryError("unsupported Needle proposal_class")
        if self.authority_claim != AUTHORITY_NONE:
            raise NeedleBoundaryError("Needle may not mint execution authority")
        if self.route.upper() in {"BYPASS_NEEDLE", "SKIP_NEEDLE", "NO_NEEDLE"}:
            raise NeedleBoundaryError("Needle bypass is forbidden for normal ingress")


@dataclass(frozen=True)
class ClayIngressEnvelope:
    schema_version: str
    semantic_language: str
    semantic_role: str
    payload_clay: str
    translator: Mapping[str, str]
    needle: Mapping[str, str]
    authority: str
    effect_eligible: bool
    effect_gate_required: bool
    bridge_hash: str

    def canonical_body(self) -> dict[str, Any]:
        body = asdict(self)
        body.pop("bridge_hash", None)
        return body


def bridge_to_clay(translator: TranslatorReceipt, needle: NeedleReceipt) -> ClayIngressEnvelope:
    """Validate the outer translator->Needle chain and produce a typed Clay ingress envelope.

    This adapter does not implement or redesign Needle. It consumes an already-produced
    Needle receipt, binds it to the translator receipt, strips any authority claim, and
    emits a deterministic provenance-bound Clay ingress object for the H1 reference harness.
    """
    translator.validate()
    needle.validate()
    if needle.input_sha256 != translator.normalized_text_sha256:
        raise NeedleBoundaryError("Needle input hash does not match translator normalized output")

    body: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "semantic_language": SEMANTIC_LANGUAGE_CLAY,
        "semantic_role": needle.proposal_class,
        "payload_clay": needle.payload_clay,
        "translator": {
            "translator_id": translator.translator_id,
            "translator_version": translator.translator_version,
            "source_language": translator.source_language,
            "source_text_sha256": translator.source_text_sha256,
            "normalized_text_sha256": translator.normalized_text_sha256,
        },
        "needle": {
            "needle_id": needle.needle_id,
            "needle_version": needle.needle_version,
            "input_sha256": needle.input_sha256,
            "route": needle.route,
            "certificate_id": needle.certificate_id,
            "certificate_sha256": needle.certificate_sha256,
            "proposal_class": needle.proposal_class,
        },
        "authority": AUTHORITY_NONE,
        "effect_eligible": False,
        "effect_gate_required": True,
    }
    bridge_hash = sha256_text(_canonical_json(body))
    return ClayIngressEnvelope(**body, bridge_hash=bridge_hash)


def verify_envelope(envelope: ClayIngressEnvelope) -> bool:
    if envelope.schema_version != SCHEMA_VERSION:
        return False
    if envelope.semantic_language != SEMANTIC_LANGUAGE_CLAY:
        return False
    if envelope.semantic_role not in _ALLOWED_PROPOSAL_CLASSES:
        return False
    if envelope.authority != AUTHORITY_NONE or envelope.effect_eligible or not envelope.effect_gate_required:
        return False
    required_translator = {
        "translator_id", "translator_version", "source_language",
        "source_text_sha256", "normalized_text_sha256",
    }
    required_needle = {
        "needle_id", "needle_version", "input_sha256", "route",
        "certificate_id", "certificate_sha256", "proposal_class",
    }
    if set(envelope.translator) != required_translator or set(envelope.needle) != required_needle:
        return False
    try:
        _require_sha256("source_text_sha256", envelope.translator["source_text_sha256"])
        _require_sha256("normalized_text_sha256", envelope.translator["normalized_text_sha256"])
        _require_sha256("input_sha256", envelope.needle["input_sha256"])
        _require_sha256("certificate_sha256", envelope.needle["certificate_sha256"])
    except NeedleBoundaryError:
        return False
    if envelope.needle["input_sha256"] != envelope.translator["normalized_text_sha256"]:
        return False
    expected = sha256_text(_canonical_json(envelope.canonical_body()))
    return expected == envelope.bridge_hash
