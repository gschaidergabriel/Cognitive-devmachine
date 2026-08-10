from __future__ import annotations

"""Deterministic compressed authenticated-map shadow for UnifiedDB.

Research-only: the canonical StateLedger SHA-256 root is unchanged. This Merkle treap is a
candidate O(log N) incremental commitment with O(N) nodes. Tree priority is derived from the
key hash, making the shape deterministic and insertion-order independent without storing a
256-level sparse path per row.
"""

import hashlib
from dataclasses import dataclass
from typing import Iterable


def H(data: bytes) -> bytes: return hashlib.sha256(data).digest()
EMPTY=H(b'CLAY_MERKLE_TREAP_EMPTY_V1')

def key_digest(domain:str,key:str)->bytes:
    return H(domain.encode('utf-8')+b'\x00'+key.encode('utf-8'))

def priority_of(key_hash:bytes)->tuple[bytes,bytes]:
    return H(b'CLAY_MERKLE_TREAP_PRIORITY_V1\x00'+key_hash),key_hash

def node_digest(key_hash:bytes,row_hash:bytes,left:bytes,right:bytes)->bytes:
    return H(b'\x02'+key_hash+row_hash+left+right)

@dataclass
class Node:
    key_hash:bytes
    row_hash:bytes
    priority:tuple[bytes,bytes]
    left:'Node|None'=None
    right:'Node|None'=None
    digest:bytes=EMPTY
    size:int=1

@dataclass(frozen=True)
class ProofStep:
    parent_key_hash_hex:str
    parent_row_hash_hex:str
    sibling_hash_hex:str
    child_side:str  # LEFT means reconstructed child belongs left of parent.

@dataclass(frozen=True)
class TreapProof:
    key_hash_hex:str
    row_hash_hex:str
    steps:tuple[ProofStep,...]
    root_hash_hex:str

class MerkleTreapStateShadow:
    def __init__(self): self.root:Node|None=None
    @staticmethod
    def _d(n:Node|None)->bytes: return EMPTY if n is None else n.digest
    @staticmethod
    def _s(n:Node|None)->int: return 0 if n is None else n.size
    def _fix(self,n:Node)->Node:
        n.size=1+self._s(n.left)+self._s(n.right)
        n.digest=node_digest(n.key_hash,n.row_hash,self._d(n.left),self._d(n.right)); return n
    def _split(self,n:Node|None,key:bytes)->tuple[Node|None,Node|None]:
        if n is None:return None,None
        if key<n.key_hash:
            a,b=self._split(n.left,key); n.left=b; return a,self._fix(n)
        a,b=self._split(n.right,key); n.right=a; return self._fix(n),b
    def _merge(self,a:Node|None,b:Node|None)->Node|None:
        if a is None:return b
        if b is None:return a
        if a.priority<b.priority:
            a.right=self._merge(a.right,b); return self._fix(a)
        b.left=self._merge(a,b.left); return self._fix(b)
    def _upsert(self,n:Node|None,key:bytes,row_hash:bytes)->Node:
        if n is None:return self._fix(Node(key,row_hash,priority_of(key)))
        if key==n.key_hash:
            n.row_hash=row_hash; return self._fix(n)
        p=priority_of(key)
        if p<n.priority:
            left,right=self._split(n,key); return self._fix(Node(key,row_hash,p,left,right))
        if key<n.key_hash:n.left=self._upsert(n.left,key,row_hash)
        else:n.right=self._upsert(n.right,key,row_hash)
        return self._fix(n)
    def _remove(self,n:Node|None,key:bytes)->Node|None:
        if n is None:return None
        if key==n.key_hash:return self._merge(n.left,n.right)
        if key<n.key_hash:n.left=self._remove(n.left,key)
        else:n.right=self._remove(n.right,key)
        return self._fix(n)
    def update_hash(self,*,domain:str,key:str,row_hash_hex:str)->None:
        self.root=self._upsert(self.root,key_digest(domain,key),bytes.fromhex(row_hash_hex))
    def remove(self,*,domain:str,key:str)->None:
        self.root=self._remove(self.root,key_digest(domain,key))
    def map_root(self)->bytes:return self._d(self.root)
    def node_count(self)->int:return self._s(self.root)
    def rebuild(self,rows:Iterable[tuple[str,str,str]])->bytes:
        self.root=None
        for d,k,r in rows:self.update_hash(domain=d,key=k,row_hash_hex=r)
        return self.map_root()
    def committed_root(self,*,global_epoch:int,domain_epochs_hash_hex:str,semantic_chain_hash_hex:str)->bytes:
        meta=H(b'CLAY_MERKLE_TREAP_META_V1\x00'+int(global_epoch).to_bytes(8,'big')+bytes.fromhex(domain_epochs_hash_hex)+bytes.fromhex(semantic_chain_hash_hex))
        return H(b'CLAY_MERKLE_TREAP_STATE_V1\x00'+meta+self.map_root())
    def proof(self,*,domain:str,key:str)->TreapProof:
        kh=key_digest(domain,key); n=self.root; path=[]
        while n is not None and n.key_hash!=kh:
            if kh<n.key_hash:
                path.append((n,'LEFT',self._d(n.right))); n=n.left
            else:
                path.append((n,'RIGHT',self._d(n.left))); n=n.right
        if n is None:raise KeyError((domain,key))
        steps=[]
        for parent,side,sibling in reversed(path):
            steps.append(ProofStep(parent.key_hash.hex(),parent.row_hash.hex(),sibling.hex(),side))
        return TreapProof(kh.hex(),n.row_hash.hex(),tuple(steps),self.map_root().hex())
    @staticmethod
    def verify(proof:TreapProof)->bool:
        cur=node_digest(bytes.fromhex(proof.key_hash_hex),bytes.fromhex(proof.row_hash_hex),EMPTY,EMPTY)
        # Inclusion proof is only valid when the target node itself has no hidden children.
        # General subtree proofs require target left/right hashes; encode them via first step
        # is not sufficient. Therefore this method intentionally supports leaf proofs only.
        for step in proof.steps:
            pk=bytes.fromhex(step.parent_key_hash_hex); pr=bytes.fromhex(step.parent_row_hash_hex); sib=bytes.fromhex(step.sibling_hash_hex)
            cur=node_digest(pk,pr,cur,sib) if step.child_side=='LEFT' else node_digest(pk,pr,sib,cur)
        return cur.hex()==proof.root_hash_hex
