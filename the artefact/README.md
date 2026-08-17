# ClayVerse artefact — integrated core candidate

This directory is the canonical implementation home for the single ClayVerse OCI/Docker image.

Current candidate scope is deliberately narrow and executable:

- one durable ClayVerse identity shared by sessions;
- UnifiedDB-style SQLite/WAL authority with a hash-chained event stream;
- ClayGraph as a rebuildable projection of authoritative `LINK` events;
- causal process-effect path: request -> outcome -> verification -> causal re-entry -> credit update;
- explicit argv process execution with `shell=False`;
- fail-closed event tamper detection and effect-id collision handling;
- restart continuity and first-two-session proof.

It does **not** claim whole ClayVerse acceptance. Clerk, Hyperposition/GWT, full ClayCode/EntityOS integration, network/audio/visual surfaces, inference-engine integration, container build portability, and final VPS deployment remain open.

## Local isolated verification

```sh
python3 -m unittest discover -s tests -v
python3 clayverse.py --selftest --state /tmp/clayverse-selftest
```

## Container candidate

```sh
docker build -t clayverse:dev .
docker run --rm -v clayverse-state:/var/lib/clayverse clayverse:dev --selftest --state /var/lib/clayverse
```
