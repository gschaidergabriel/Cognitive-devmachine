# Fusion 2 — after external collision search

External research destroys two easy versions of the idea. First, O_APPEND alone is not a durable security primitive: modern Linux exposes RWF_NOAPPEND for pwritev2. Second, append-only cryptographic databases and Merkle transparency logs are established mechanisms, so neither append-only state nor hash chaining is novel.

The surviving candidate is narrower and more testable. MOLT requires *kernel inode append-only state* (FS_APPEND_FL or an experimentally stronger equivalent), verified absence of CAP_LINUX_IMMUTABLE in the broker, and complete removal of writable self-image descriptors from the cognitive runtime. The broker accepts only typed StateDeltaEnvelope messages; compaction/root replacement is outside target self-authority and constructs a new candidate image.

Landlock can be defense in depth but is not the primary subregion mechanism. fs-verity is a strong whole-file immutable control, not a mixed immutable-prefix/mutable-tail solution. A loop-device offset/sizelimit projection becomes the strongest conventional one-inode range alternative and must be included in the target-VPS comparison.

The key scientific/engineering discriminator is therefore not append-only history. It is whether **monotonic physical write direction plus capability separation** can recover the least-privilege property lost by naive one-inode EUDI while preserving one authoritative image and acceptable recovery/resource economics.
