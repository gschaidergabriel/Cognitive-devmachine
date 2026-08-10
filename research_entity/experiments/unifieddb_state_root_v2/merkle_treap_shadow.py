from __future__ import annotations

"""Deterministic authenticated state-root shadow for UnifiedDB research.

This module is deliberately NOT the canonical StateLedger semantic_state_hash.
It is a rebuildable candidate commitment over the same semantic row content, intended
for measuring whether an O(log N) authenticated update path can eventually replace or
complement the current O(N) byte-exact SHA-256 state scan under an explicit versioned
migration contract.

Authority law:
- canonical StateLedger state + current semantic_state_hash remain authoritative;
- this shadow may detect drift and provide a candidate/proof root only;
- mismatch fails closed for any future promotion experiment;
- no caller may reinterpret a matching shadow root as truth/effect authority.
"""

from dataclasses import dataclass
import hashlib
import json
from typing import Any, Iterable, Mapping


EMPTY_HASH = hashlib.sha256(b"clay.udb.merkle-treap.empty.v1").digest()
ROOT_VERSION = "CLAY_UDB_MERKLE_TREAP_SHADOW_V1"


def _canon(value: Any) -> Any:
    if isinstance(value, dict):
        kind = value.get("$kind")
        if kind in ("set", "ordered"):
            items = value.get("items", [])
            if not isinstance(items, list):
                raise TypeError("typed collection items must be list")
            xs = [_canon(x) for x in items]
            if kind == "set":
                dedup = {
                    json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":")): x
                    for x in xs
                }
                xs = [dedup[k] for k in sorted(dedup)]
            return {"$kind": kind, "items": xs}
        return {str(k): _canon(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (list, tuple)):
        return [_canon(x) for x in value]
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, float):
        if value != value or value in (float("inf"), float("-inf")):
            raise ValueError("non-finite float")
        return value
    raise TypeError(type(value).__name__)


def _cjson(value: Any) -> str:
    return json.dumps(_canon(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _enc(text: str) -> bytes:
    raw = text.encode("utf-8")
    return len(raw).to_bytes(4, "big") + raw


def _key(row: Mapping[str, Any]) -> str:
    return f"{row['domain']}\x00{row['key']}"


def _priority(key: str) -> bytes:
    return hashlib.sha256(b"clay.udb.merkle-treap.priority.v1\x00" + key.encode("utf-8")).digest()


def _row_digest(row: Mapping[str, Any]) -> bytes:
    """Bind all semantic row fields represented by StateLedger.materialized()."""
    payload = {
        "domain": str(row["domain"]),
        "domain_epoch": int(row["domain_epoch"]),
        "epistemic": str(row["epistemic"]),
        "key": str(row["key"]),
        "semantic_hash": str(row["semantic_hash"]),
        "status": str(row["status"]),
        "value": row.get("value"),
    }
    return hashlib.sha256(b"clay.udb.semantic-row.v1\x00" + _cjson(payload).encode("utf-8")).digest()


@dataclass
class _Node:
    key: str
    priority: bytes
    value_digest: bytes
    left: "_Node | None" = None
    right: "_Node | None" = None
    node_hash: bytes = b""


def _node_hash(node: _Node | None) -> bytes:
    if node is None:
        return EMPTY_HASH
    digest = hashlib.sha256()
    digest.update(b"clay.udb.merkle-treap.node.v1\x00")
    digest.update(_enc(node.key))
    digest.update(node.value_digest)
    digest.update(node.left.node_hash if node.left else EMPTY_HASH)
    digest.update(node.right.node_hash if node.right else EMPTY_HASH)
    return digest.digest()


def _rank(node: _Node) -> tuple[bytes, str]:
    return node.priority, node.key


def _rotate_right(root: _Node) -> _Node:
    pivot = root.left
    if pivot is None:
        return root
    root.left = pivot.right
    root.node_hash = _node_hash(root)
    pivot.right = root
    pivot.node_hash = _node_hash(pivot)
    return pivot


def _rotate_left(root: _Node) -> _Node:
    pivot = root.right
    if pivot is None:
        return root
    root.right = pivot.left
    root.node_hash = _node_hash(root)
    pivot.left = root
    pivot.node_hash = _node_hash(pivot)
    return pivot


def _upsert(root: _Node | None, key: str, value_digest: bytes) -> tuple[_Node, bool, int]:
    if root is None:
        node = _Node(key=key, priority=_priority(key), value_digest=value_digest)
        node.node_hash = _node_hash(node)
        return node, True, 1
    if key == root.key:
        root.value_digest = value_digest
        root.node_hash = _node_hash(root)
        return root, False, 1
    inserted = False
    depth = 1
    if key < root.key:
        root.left, inserted, child_depth = _upsert(root.left, key, value_digest)
        depth += child_depth
        if _rank(root.left) < _rank(root):
            root = _rotate_right(root)
    else:
        root.right, inserted, child_depth = _upsert(root.right, key, value_digest)
        depth += child_depth
        if _rank(root.right) < _rank(root):
            root = _rotate_left(root)
    root.node_hash = _node_hash(root)
    return root, inserted, depth


def _build_sorted(items: list[tuple[str, bytes]]) -> _Node | None:
    """O(N) Cartesian-tree build for deterministic rebuild from sorted state keys."""
    stack: list[_Node] = []
    for key, value_digest in items:
        node = _Node(key=key, priority=_priority(key), value_digest=value_digest)
        last: _Node | None = None
        while stack and _rank(stack[-1]) > _rank(node):
            last = stack.pop()
        node.left = last
        if stack:
            stack[-1].right = node
        stack.append(node)
    root = stack[0] if stack else None
    if root is None:
        return None
    work: list[tuple[_Node, bool]] = [(root, False)]
    while work:
        node, visited = work.pop()
        if visited:
            node.node_hash = _node_hash(node)
            continue
        work.append((node, True))
        if node.right:
            work.append((node.right, False))
        if node.left:
            work.append((node.left, False))
    return root


class MerkleTreapShadow:
    def __init__(self) -> None:
        self.root: _Node | None = None
        self.node_count = 0

    @classmethod
    def rebuild(cls, rows: Iterable[Mapping[str, Any]]) -> "MerkleTreapShadow":
        by_key: dict[str, bytes] = {}
        for row in rows:
            key = _key(row)
            if key in by_key:
                raise ValueError(f"duplicate semantic state key: {key!r}")
            by_key[key] = _row_digest(row)
        shadow = cls()
        items = sorted(by_key.items())
        shadow.root = _build_sorted(items)
        shadow.node_count = len(items)
        return shadow

    @property
    def state_merkle_root(self) -> str:
        return (self.root.node_hash if self.root else EMPTY_HASH).hex()

    def upsert(self, row: Mapping[str, Any]) -> dict[str, Any]:
        key = _key(row)
        before = self.node_count
        self.root, inserted, depth = _upsert(self.root, key, _row_digest(row))
        if inserted:
            self.node_count += 1
        return {
            "inserted": inserted,
            "path_depth": depth,
            "node_count_before": before,
            "node_count_after": self.node_count,
            "state_merkle_root": self.state_merkle_root,
        }

    def wrapper_root(
        self,
        *,
        global_epoch: int,
        domain_epochs: Mapping[str, int],
        semantic_chain_hash: str,
    ) -> str:
        payload = {
            "version": ROOT_VERSION,
            "global_epoch": int(global_epoch),
            "domain_epochs": {str(k): int(domain_epochs[k]) for k in sorted(domain_epochs)},
            "semantic_chain_hash": str(semantic_chain_hash),
            "state_merkle_root": self.state_merkle_root,
        }
        return hashlib.sha256(_cjson(payload).encode("utf-8")).hexdigest()

    def verify_rebuild(self, rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
        rebuilt = MerkleTreapShadow.rebuild(rows)
        return {
            "verified": rebuilt.state_merkle_root == self.state_merkle_root,
            "expected": rebuilt.state_merkle_root,
            "actual": self.state_merkle_root,
            "node_count_expected": rebuilt.node_count,
            "node_count_actual": self.node_count,
        }
