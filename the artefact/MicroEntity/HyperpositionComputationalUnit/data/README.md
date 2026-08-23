# HCU data root

All datasets, generated teacher packets, calibration tables, benchmark outputs and durable
HCU research data belong under this directory or a typed subdirectory beneath it.

Rules:

- every data shard carries provenance and schema/version metadata;
- free-LLM/provider output is candidate data until separately admitted;
- secrets, API keys, cookies and auth headers are forbidden;
- raw sensitive user data must not be copied here merely to improve training;
- large generated artifacts should be chunked deterministically with a manifest and hashes;
- the MicroEntity snapshot builder recursively includes this subtree.
