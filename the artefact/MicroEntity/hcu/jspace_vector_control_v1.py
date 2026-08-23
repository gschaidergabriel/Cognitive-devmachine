from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation, ROUND_HALF_EVEN, localcontext
from typing import Iterable, Mapping, Sequence

SCHEMA_VERSION = "JSPACE_VECTOR_CONTROL_ABI/v1"
_TOKEN_RE = re.compile(r"^[A-Za-z0-9._:-]{1,96}$")
_MAX_DIMS = 4096
_MAX_WORKSPACE_HANDLES = 64
_MAX_GATES = 64


class JSpaceControlError(ValueError):
    pass


def _canonical_json(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _token(name: str, value: str) -> str:
    if not isinstance(value, str) or not _TOKEN_RE.fullmatch(value):
        raise JSpaceControlError(f"invalid {name}")
    return value


def _decimal(value: object) -> Decimal:
    if isinstance(value, bool):
        raise JSpaceControlError("boolean is not a vector coordinate")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise JSpaceControlError("invalid vector coordinate") from exc
    if not d.is_finite():
        raise JSpaceControlError("non-finite vector coordinate")
    return d


def _decimal_text(d: Decimal) -> str:
    if d == 0:
        return "0"
    # Canonical non-exponent decimal string; deterministic across Python float formatting paths.
    s = format(d.normalize(), "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return "0" if s in {"-0", ""} else s


def _quantize_q8(values: Sequence[object]) -> tuple[str, list[int]]:
    if not values or len(values) > _MAX_DIMS:
        raise JSpaceControlError("vector dimension out of bounds")
    ds = [_decimal(v) for v in values]
    max_abs = max(abs(v) for v in ds)
    if max_abs == 0:
        return "0", [0] * len(ds)
    with localcontext() as ctx:
        ctx.prec = 50
        scale = max_abs / Decimal(127)
        q: list[int] = []
        for value in ds:
            raw = (value / scale).to_integral_value(rounding=ROUND_HALF_EVEN)
            qi = max(-127, min(127, int(raw)))
            q.append(qi)
    return _decimal_text(scale), q


def _q8_hex(q: Iterable[int]) -> str:
    out = bytearray()
    for value in q:
        if value < -127 or value > 127:
            raise JSpaceControlError("q8 coordinate out of range")
        out.append(value & 0xFF)
    return out.hex()


def _q8_from_hex(text: str, dims: int) -> list[int]:
    if not isinstance(text, str) or len(text) != dims * 2:
        raise JSpaceControlError("q8 payload length mismatch")
    try:
        data = bytes.fromhex(text)
    except ValueError as exc:
        raise JSpaceControlError("invalid q8 payload") from exc
    q = [b - 256 if b >= 128 else b for b in data]
    if any(v == -128 for v in q):
        raise JSpaceControlError("-128 is outside ABI q8 range")
    return q


def _canonical_gates(gates: Mapping[str, object] | None) -> dict[str, int]:
    if gates is None:
        return {}
    if len(gates) > _MAX_GATES:
        raise JSpaceControlError("too many gates")
    out: dict[str, int] = {}
    for key, value in gates.items():
        k = _token("gate key", key)
        if isinstance(value, bool):
            iv = int(value)
        elif isinstance(value, int) and value in (0, 1):
            iv = value
        else:
            raise JSpaceControlError("gate values must be boolean/0/1")
        out[k] = iv
    return dict(sorted(out.items()))


def _canonical_workspace(handles: Sequence[str] | None) -> list[str]:
    if handles is None:
        return []
    if len(handles) > _MAX_WORKSPACE_HANDLES:
        raise JSpaceControlError("too many workspace handles")
    out = [_token("workspace handle", h) for h in handles]
    if len(set(out)) != len(out):
        raise JSpaceControlError("duplicate workspace handle")
    return out


@dataclass(frozen=True)
class DecodedControl:
    schema_version: str
    basis_id: str
    role: str
    generation: int
    vector: tuple[Decimal, ...]
    gates: Mapping[str, int]
    workspace: tuple[str, ...]
    payload_sha256: str
    packet_sha256: str


def encode_control(
    vector: Sequence[object],
    *,
    basis_id: str,
    role: str,
    generation: int,
    gates: Mapping[str, object] | None = None,
    workspace: Sequence[str] | None = None,
) -> str:
    basis_id = _token("basis_id", basis_id)
    role = _token("role", role)
    if not isinstance(generation, int) or isinstance(generation, bool) or generation < 0:
        raise JSpaceControlError("generation must be a non-negative integer")
    scale, q = _quantize_q8(vector)
    qhex = _q8_hex(q)
    gate_obj = _canonical_gates(gates)
    workspace_obj = _canonical_workspace(workspace)
    payload = {"dims": len(q), "scale": scale, "q8": qhex}
    payload_sha256 = _sha256_text(_canonical_json(payload))
    core = {
        "schema_version": SCHEMA_VERSION,
        "basis_id": basis_id,
        "role": role,
        "generation": generation,
        "payload_sha256": payload_sha256,
        "gates": gate_obj,
        "workspace": workspace_obj,
    }
    packet_sha256 = _sha256_text(_canonical_json(core))
    return "\n".join(
        [
            f"<jctl:v1 basis={basis_id} role={role} gen={generation} dims={len(q)} scale={scale} payload_sha256={payload_sha256} packet_sha256={packet_sha256}>",
            f"q8:{qhex}",
            f"gate:{_canonical_json(gate_obj)}",
            f"workspace:{_canonical_json(workspace_obj)}",
            "</jctl>",
        ]
    )


def decode_control(
    packet: str,
    *,
    expected_basis_id: str,
    expected_role: str,
    expected_generation: int,
) -> DecodedControl:
    expected_basis_id = _token("expected_basis_id", expected_basis_id)
    expected_role = _token("expected_role", expected_role)
    if not isinstance(expected_generation, int) or isinstance(expected_generation, bool) or expected_generation < 0:
        raise JSpaceControlError("expected_generation must be a non-negative integer")
    if not isinstance(packet, str) or len(packet) > 1_000_000:
        raise JSpaceControlError("invalid packet")
    lines = packet.splitlines()
    if len(lines) != 5 or lines[-1] != "</jctl>":
        raise JSpaceControlError("malformed packet framing")
    header = lines[0]
    m = re.fullmatch(
        r"<jctl:v1 basis=([A-Za-z0-9._:-]{1,96}) role=([A-Za-z0-9._:-]{1,96}) gen=([0-9]+) dims=([0-9]+) scale=([^ ]+) payload_sha256=([0-9a-f]{64}) packet_sha256=([0-9a-f]{64})>",
        header,
    )
    if not m:
        raise JSpaceControlError("malformed packet header")
    basis_id, role, gen_s, dims_s, scale_s, payload_sha256, packet_sha256 = m.groups()
    generation = int(gen_s)
    dims = int(dims_s)
    if dims <= 0 or dims > _MAX_DIMS:
        raise JSpaceControlError("vector dimension out of bounds")
    if basis_id != expected_basis_id:
        raise JSpaceControlError("wrong J-Space basis")
    if role != expected_role:
        raise JSpaceControlError("wrong cell role")
    if generation != expected_generation:
        raise JSpaceControlError("stale or unexpected generation")
    scale = _decimal(scale_s)
    if scale < 0:
        raise JSpaceControlError("negative scale")
    if not lines[1].startswith("q8:") or not lines[2].startswith("gate:") or not lines[3].startswith("workspace:"):
        raise JSpaceControlError("malformed packet sections")
    q = _q8_from_hex(lines[1][3:], dims)
    try:
        gates = json.loads(lines[2][5:])
        workspace = json.loads(lines[3][10:])
    except json.JSONDecodeError as exc:
        raise JSpaceControlError("invalid packet json") from exc
    gates = _canonical_gates(gates if isinstance(gates, dict) else None)
    if not isinstance(workspace, list) or not all(isinstance(x, str) for x in workspace):
        raise JSpaceControlError("invalid workspace section")
    workspace = _canonical_workspace(workspace)
    payload = {"dims": dims, "scale": _decimal_text(scale), "q8": lines[1][3:]}
    observed_payload_sha256 = _sha256_text(_canonical_json(payload))
    if observed_payload_sha256 != payload_sha256:
        raise JSpaceControlError("payload digest mismatch")
    core = {
        "schema_version": SCHEMA_VERSION,
        "basis_id": basis_id,
        "role": role,
        "generation": generation,
        "payload_sha256": payload_sha256,
        "gates": gates,
        "workspace": workspace,
    }
    observed_packet_sha256 = _sha256_text(_canonical_json(core))
    if observed_packet_sha256 != packet_sha256:
        raise JSpaceControlError("packet digest mismatch")
    if scale == 0 and any(q):
        raise JSpaceControlError("zero-scale packet contains non-zero q8")
    with localcontext() as ctx:
        ctx.prec = 80
        vector = tuple(scale * Decimal(v) for v in q)
    return DecodedControl(
        schema_version=SCHEMA_VERSION,
        basis_id=basis_id,
        role=role,
        generation=generation,
        vector=vector,
        gates=gates,
        workspace=tuple(workspace),
        payload_sha256=payload_sha256,
        packet_sha256=packet_sha256,
    )


def max_abs_reconstruction_error(original: Sequence[object], decoded: Sequence[Decimal]) -> Decimal:
    if len(original) != len(decoded):
        raise JSpaceControlError("dimension mismatch")
    with localcontext() as ctx:
        ctx.prec = 80
        return max((abs(_decimal(a) - b) for a, b in zip(original, decoded)), default=Decimal(0))
