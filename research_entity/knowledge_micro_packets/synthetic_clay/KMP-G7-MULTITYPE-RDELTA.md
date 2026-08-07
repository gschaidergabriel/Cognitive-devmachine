# KMP-G7 — Multitype Change Propagation

- **packet_id:** KMP-G7-MULTITYPE-RDELTA
- **status:** OPEN / synthetic-supported
- **domains:** synthetic-clay, incremental-systems, control
- **claim:** Heterogeneous change amplification should be represented by a typed mean propagation matrix `M_delta`, where `M_delta[i,j]` is expected consequential type-j invalidation caused by a changed type-i state. The spectral radius `rho(M_delta)` is a candidate amplification diagnostic superior to one scalar average when propagation is heterogeneous.
- **evidence:** EXP-G7-MULTITYPE-RDELTA-001. Five matrices with identical scalar average row-sum 0.8 yielded `rho=.693..1.2` and P(cascade>=100)=0..0.1632; randomized tail-risk correlation `.636` scalar vs `.811` spectral radius.
- **boundary:** synthetic branching proxy; `rho>1` means amplification/criticality, **not emergence**.
- **next falsifier:** instrument typed FRANK invalidation traces and compare scalar `R_delta`, `rho(M_delta)` and realized recomputation/batch crossover.
- **origin:** chatgpt-secondary / OpenAI / GPT-5.6 Sol / clay-20260808T0542p0700-chatgpt-secondary
