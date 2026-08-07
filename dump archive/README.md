# DUMP ARCHIVE

Completed dump batches are moved here only after the RAE Dump Protocol has finished and verified the original hashes.

Layout:

`dump archive/<batch_id>/original/`

Each completed batch must also contain `MANIFEST.json`, `DUMP_RESULT.json` and `RESEARCH_DELTA.md`.

The archive is immutable research intake history. Re-analysis creates new derived packets/events; it does not rewrite old batch bytes.
