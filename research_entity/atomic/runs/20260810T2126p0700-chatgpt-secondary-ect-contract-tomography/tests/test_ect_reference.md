# Reference discriminator tests

Executed in the local synthetic reference harness:

1. exact finite-domain recovery with FIELD_VALUE_WITNESS;
2. field-only witness recovery;
3. stale epoch rejects;
4. `Frank.id` / non-`self.root` identity rejects;
5. non-sandbox effect probe degrades to UNKNOWN;
6. BOOL_ONLY mismatch cannot be promoted to an exact contract;
7. no path mints effect authority.

The executable assertions live in `implementation/ect_reference.py`. This is not target-VPS or real Frank acceptance evidence.
