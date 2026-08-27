# GRID10 RAM‑Effizienz‑Konzept – Antwort

**(a) Plausibilität & Mechanismus**  
Die beobachteten ~379 MB `Private_Dirty` pro Kind‑Prozess stammen fast ausschließlich von PyTorchs CPU‑Allocator (ein Wrapper um `malloc`/`free`), der freigegebene Tensor‑Speicher (Aktivierungen, KV‑Cache) nicht an das OS zurückgibt, sondern intern für spätere Allokationen behält. Dies ist genau das Verhalten von PyTorchs *caching allocator* (auch bei CPU‑Tensoren verwendet).  

Geeigneter Rückgabemechanismus im Idle‑Zustand (nach `generate()`):  

