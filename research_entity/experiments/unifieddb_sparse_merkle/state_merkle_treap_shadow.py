from __future__ import annotations

"""Deterministic compressed authenticated-map shadow for UnifiedDB.

Research-only: canonical StateLedger SHA-256 remains authority. This Merkle treap tests an
O(log N) incremental commitment using O(N) nodes. Priority derives from key hash, so tree
shape is deterministic and insertion-order independent.
"""
import hashlib
from dataclasses import dataclass
from typing import Iterable

def H(data:bytes)->bytes:return hashlib.sha256(data).digest()
EMPTY=H(b'CLAY_MERKLE_TREAP_EMPTY_V1')
def key_digest(domain:str,key:str)->bytes:return H(domain.encode()+b'\0'+key.encode())
def priority_of(key_hash:bytes)->tuple[bytes,bytes]:return H(b'CLAY_MERKLE_TREAP_PRIORITY_V1\0'+key_hash),key_hash
def node_digest(key_hash:bytes,row_hash:bytes,left:bytes,right:bytes)->bytes:return H(b'\x02'+key_hash+row_hash+left+right)

@dataclass
class Node:
    key_hash:bytes; row_hash:bytes; priority:tuple[bytes,bytes]
    left:'Node|None'=None; right:'Node|None'=None; digest:bytes=EMPTY; size:int=1

@dataclass(frozen=True)
class ProofStep:
    parent_key_hash_hex:str; parent_row_hash_hex:str; sibling_hash_hex:str; child_side:str

@dataclass(frozen=True)
class TreapProof:
    key_hash_hex:str; row_hash_hex:str
    target_left_hash_hex:str; target_right_hash_hex:str
    steps:tuple[ProofStep,...]; root_hash_hex:str

class MerkleTreapStateShadow:
    def __init__(self):self.root:Node|None=None
    @staticmethod
    def _d(n):return EMPTY if n is None else n.digest
    @staticmethod
    def _s(n):return 0 if n is None else n.size
    def _fix(self,n):
        n.size=1+self._s(n.left)+self._s(n.right); n.digest=node_digest(n.key_hash,n.row_hash,self._d(n.left),self._d(n.right)); return n
    def _split(self,n,key):
        if n is None:return None,None
        if key<n.key_hash:
            a,b=self._split(n.left,key); n.left=b; return a,self._fix(n)
        a,b=self._split(n.right,key); n.right=a; return self._fix(n),b
    def _merge(self,a,b):
        if a is None:return b
        if b is None:return a
        if a.priority<b.priority:a.right=self._merge(a.right,b); return self._fix(a)
        b.left=self._merge(a,b.left); return self._fix(b)
    def _upsert(self,n,key,row_hash):
        if n is None:return self._fix(Node(key,row_hash,priority_of(key)))
        if key==n.key_hash:n.row_hash=row_hash; return self._fix(n)
        p=priority_of(key)
        if p<n.priority:
            left,right=self._split(n,key); return self._fix(Node(key,row_hash,p,left,right))
        if key<n.key_hash:n.left=self._upsert(n.left,key,row_hash)
        else:n.right=self._upsert(n.right,key,row_hash)
        return self._fix(n)
    def _remove(self,n,key):
        if n is None:return None
        if key==n.key_hash:return self._merge(n.left,n.right)
        if key<n.key_hash:n.left=self._remove(n.left,key)
        else:n.right=self._remove(n.right,key)
        return self._fix(n)
    def update_hash(self,*,domain:str,key:str,row_hash_hex:str)->None:self.root=self._upsert(self.root,key_digest(domain,key),bytes.fromhex(row_hash_hex))
    def remove(self,*,domain:str,key:str)->None:self.root=self._remove(self.root,key_digest(domain,key))
    def map_root(self)->bytes:return self._d(self.root)
    def node_count(self)->int:return self._s(self.root)
    def rebuild(self,rows:Iterable[tuple[str,str,str]])->bytes:
        """Deterministic O(N log N) sort + O(N) Cartesian-tree rebuild/recovery path."""
        entries=[]
        for d,k,r in rows:
            kh=key_digest(d,k); entries.append((kh,bytes.fromhex(r),priority_of(kh)))
        entries.sort(key=lambda x:x[0])
        stack=[]
        for kh,row_hash,priority in entries:
            n=Node(kh,row_hash,priority); last=None
            while stack and priority<stack[-1].priority:last=stack.pop()
            n.left=last
            if stack:stack[-1].right=n
            stack.append(n)
        self.root=stack[0] if stack else None
        if self.root is not None:
            todo=[(self.root,False)]
            while todo:
                n,visited=todo.pop()
                if visited:self._fix(n)
                else:
                    todo.append((n,True))
                    if n.right is not None:todo.append((n.right,False))
                    if n.left is not None:todo.append((n.left,False))
        return self.map_root()
    def committed_root(self,*,global_epoch:int,domain_epochs_hash_hex:str,semantic_chain_hash_hex:str)->bytes:
        meta=H(b'CLAY_MERKLE_TREAP_META_V1\0'+int(global_epoch).to_bytes(8,'big')+bytes.fromhex(domain_epochs_hash_hex)+bytes.fromhex(semantic_chain_hash_hex))
        return H(b'CLAY_MERKLE_TREAP_STATE_V1\0'+meta+self.map_root())
    def proof(self,*,domain:str,key:str)->TreapProof:
        kh=key_digest(domain,key); n=self.root; path=[]
        while n is not None and n.key_hash!=kh:
            if kh<n.key_hash:path.append((n,'LEFT',self._d(n.right))); n=n.left
            else:path.append((n,'RIGHT',self._d(n.left))); n=n.right
        if n is None:raise KeyError((domain,key))
        steps=[ProofStep(p.key_hash.hex(),p.row_hash.hex(),sib.hex(),side) for p,side,sib in reversed(path)]
        return TreapProof(kh.hex(),n.row_hash.hex(),self._d(n.left).hex(),self._d(n.right).hex(),tuple(steps),self.map_root().hex())
    @staticmethod
    def verify(proof:TreapProof)->bool:
        cur=node_digest(bytes.fromhex(proof.key_hash_hex),bytes.fromhex(proof.row_hash_hex),bytes.fromhex(proof.target_left_hash_hex),bytes.fromhex(proof.target_right_hash_hex))
        for s in proof.steps:
            pk=bytes.fromhex(s.parent_key_hash_hex); pr=bytes.fromhex(s.parent_row_hash_hex); sib=bytes.fromhex(s.sibling_hash_hex)
            cur=node_digest(pk,pr,cur,sib) if s.child_side=='LEFT' else node_digest(pk,pr,sib,cur)
        return cur.hex()==proof.root_hash_hex
