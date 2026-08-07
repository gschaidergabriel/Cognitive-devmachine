# KMP-G7 — Hierarchical Causal Governor

- **packet_id:** KMP-G7-HIERARCHICAL-GOVERNOR
- **status:** OPEN / synthetic-supported
- **domains:** synthetic-clay, frank-runtime, control, android-edge
- **claim:** G6's causal budget vector should be organized hierarchically: slow semantic utility/resource allocation plus fast safety loops for thermal, freshness, authority, cascade risk and deadlines. Dimensions remain coupled through constraints/shadow prices.
- **evidence:** EXP-G7-HIERARCHICAL-GOV-002: mean loss scalar `.45988`, flat vector `.29379`, hierarchical `.25716`; hierarchy improved 12.47% vs flat and removed constructed thermal violations.
- **negative shadow:** hierarchy switched `.3324` dimensions/step vs `.0672` flat, so hysteresis/rate limits/switching cost are mandatory shadows.
- **boundary:** constructed nonstationary six-resource controller; not a universal control proof.
- **next falsifier:** replay real FRANK traces with scalar/flat/hierarchical controllers including controller overhead, switching and recovery debt.
- **origin:** chatgpt-secondary / OpenAI / GPT-5.6 Sol / clay-20260808T0542p0700-chatgpt-secondary
