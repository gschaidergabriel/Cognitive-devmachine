from __future__ import annotations

"""Sparse authenticated state-map shadow for UnifiedDB research.

This module is deliberately NON-CANONICAL. StateLedger.semantic_state_hash remains the
current authority. The shadow explores whether O(log keyspace) update commitments and
inclusion proofs can remove the remaining O(N) flat-root scaling cost without changing
current replay/authority semantics prematurely.
"""

import hashlib
from dataclasses import dataclass
from typing import Iterable


def H(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def key_digest(domain: str, key: str) -> bytes:
    return H(domain.encode('utf-8') + b'\x00' + key.encode('utf-8'))


def leaf_digest(key_hash: bytes, row_hash_hex: str) -> bytes:
    return H(b'\x00' + key_hash + bytes.fromhex(row_hash_hex))


def node_digest(left: bytes, right: bytes) -> bytes:
    return H(b'\x01' + left + right)


def metadata_digest(*, global_epoch: int, domain_epochs_hash_hex: str,
                    semantic_chain_hash_hex: str) -> bytes:
    return H(
        b'CLAY_SPARSE_MERKLE_META_V1\x00'
        + int(global_epoch).to_bytes(8, 'big', signed=False)
        + bytes.fromhex(domain_epochs_hash_hex)
        + bytes.fromhex(semantic_chain_hash_hex)
    )


@dataclass(frozen=True)
class SparseMerkleProof:
    key_hash_hex: str
    row_hash_hex: str
    siblings_hex: tuple[str, ...]
    map_root_hex: str


class SparseMerkleStateShadow:
    """256-bit sparse Merkle map keyed by SHA-256(domain || NUL || key).

    Only non-empty nodes are stored. One logical row update touches at most 257 node
    positions regardless of total state cardinality. Full rebuild remains available as a
    differential/recovery oracle.
    """

    DEPTH=256

    def __init__(self):
        empty=[b'']*(self.DEPTH+1)
        empty[self.DEPTH]=H(b'\x00EMPTY')
        for depth in range(self.DEPTH-1,-1,-1):
            empty[depth]=node_digest(empty[depth+1],empty[depth+1])
        self.empty=tuple(empty)
        self.nodes: dict[tuple[int,int],bytes]={}
        self.row_hashes: dict[int,str]={}

    @staticmethod
    def _path_int(key_hash: bytes) -> int:
        return int.from_bytes(key_hash,'big')

    def map_root(self) -> bytes:
        return self.nodes.get((0,0),self.empty[0])

    def committed_root(self, *, global_epoch: int, domain_epochs_hash_hex: str,
                       semantic_chain_hash_hex: str) -> bytes:
        meta=metadata_digest(
            global_epoch=global_epoch,
            domain_epochs_hash_hex=domain_epochs_hash_hex,
            semantic_chain_hash_hex=semantic_chain_hash_hex,
        )
        return H(b'CLAY_SPARSE_MERKLE_STATE_V1\x00'+meta+self.map_root())

    def update_hash(self, *, domain: str, key: str, row_hash_hex: str) -> None:
        kh=key_digest(domain,key); path=self._path_int(kh)
        self.row_hashes[path]=row_hash_hex
        self.nodes[(self.DEPTH,path)]=leaf_digest(kh,row_hash_hex)
        for depth in range(self.DEPTH-1,-1,-1):
            prefix=path >> (self.DEPTH-depth)
            left_prefix=prefix << 1; right_prefix=left_prefix | 1
            left=self.nodes.get((depth+1,left_prefix),self.empty[depth+1])
            right=self.nodes.get((depth+1,right_prefix),self.empty[depth+1])
            digest=node_digest(left,right)
            pos=(depth,prefix)
            if digest==self.empty[depth]:
                self.nodes.pop(pos,None)
            else:
                self.nodes[pos]=digest

    def remove(self, *, domain: str, key: str) -> None:
        kh=key_digest(domain,key); path=self._path_int(kh)
        self.row_hashes.pop(path,None); self.nodes.pop((self.DEPTH,path),None)
        for depth in range(self.DEPTH-1,-1,-1):
            prefix=path >> (self.DEPTH-depth)
            left_prefix=prefix << 1; right_prefix=left_prefix | 1
            left=self.nodes.get((depth+1,left_prefix),self.empty[depth+1])
            right=self.nodes.get((depth+1,right_prefix),self.empty[depth+1])
            digest=node_digest(left,right); pos=(depth,prefix)
            if digest==self.empty[depth]: self.nodes.pop(pos,None)
            else: self.nodes[pos]=digest

    def rebuild(self, rows: Iterable[tuple[str,str,str]]) -> bytes:
        self.nodes.clear(); self.row_hashes.clear()
        for domain,key,row_hash_hex in rows:
            self.update_hash(domain=domain,key=key,row_hash_hex=row_hash_hex)
        return self.map_root()

    def proof(self, *, domain: str, key: str) -> SparseMerkleProof:
        kh=key_digest(domain,key); path=self._path_int(kh)
        row_hash=self.row_hashes.get(path)
        if row_hash is None: raise KeyError((domain,key))
        siblings=[]
        for depth in range(self.DEPTH-1,-1,-1):
            prefix=path >> (self.DEPTH-depth)
            bit=(path >> (self.DEPTH-1-depth)) & 1
            sibling_prefix=(prefix << 1) | (0 if bit else 1)
            siblings.append(self.nodes.get((depth+1,sibling_prefix),self.empty[depth+1]).hex())
        return SparseMerkleProof(kh.hex(),row_hash,tuple(siblings),self.map_root().hex())

    @classmethod
    def verify(cls, proof: SparseMerkleProof) -> bool:
        kh=bytes.fromhex(proof.key_hash_hex); path=int.from_bytes(kh,'big')
        cur=leaf_digest(kh,proof.row_hash_hex)
        if len(proof.siblings_hex)!=cls.DEPTH: return False
        for i,shex in enumerate(proof.siblings_hex):
            depth=cls.DEPTH-1-i
            bit=(path >> (cls.DEPTH-1-depth)) & 1
            sibling=bytes.fromhex(shex)
            cur=node_digest(sibling,cur) if bit else node_digest(cur,sibling)
        return cur.hex()==proof.map_root_hex
