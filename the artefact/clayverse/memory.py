from __future__ import annotations
import re
from .store import UnifiedDB
EXPLICIT=re.compile(r"(?im)^\s*(FACT|DECISION|TASK|COMMITMENT|PREFERENCE)\s*:\s*(.+?)\s*$")
class MemoryManager:
    """Newest 20 remain full; unknown meaning fails closed during compression."""
    LEVELS=("full","detailed_summary","semantic_summary","fact_decision_trace","key_phrase","minimum_trace")
    def __init__(self,db:UnifiedDB,full_window=20): self.db=db; self.full_window=full_window
    def extract_explicit(self,turn_id,user_id,content):
        return [self.db.add_memory(k.lower(),user_id,v.strip(),turn_id,user_id,{"extractor":"explicit-v1","lossless":True}) for k,v in EXPLICIT.findall(content)]
    @staticmethod
    def _compress(text,level):
        words=text.split()
        if level<=1: return " ".join(words[:80])
        if level==2: return " ".join(words[:40])
        if level==3:
            typed=EXPLICIT.findall(text)
            return " | ".join(f"{k}:{v.strip()}" for k,v in typed) if typed else " ".join(words[:20])
        if level==4: return " ".join(words[:8])
        return " ".join(words[:2]) if words else ""
    def compact(self,session_id):
        rows=self.db.all_turns(session_id); n=len(rows); changed=0
        for i,row in enumerate(rows):
            age=n-i
            if age<=self.full_window: continue
            level=min(5,1+(age-self.full_window-1)//20)
            if row['compression_generation']>=level: continue
            self.db.db.execute("UPDATE turns SET content=?, fidelity=?, compression_generation=? WHERE turn_id=?",(self._compress(row['content'],level),self.LEVELS[level],level,row['turn_id'])); changed+=1
        return changed
