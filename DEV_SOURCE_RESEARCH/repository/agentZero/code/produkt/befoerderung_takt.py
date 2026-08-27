#!/usr/bin/env python3
"""EntityOS -- periodischer Check: reicht das validierte Lernsignal fuer SHADOW->ACTIVE?

Eigenes Skript, nicht ``python -c``: dieselbe Lehre wie in udb/abruf/wegverfall.py --
ein Einzeiler mit verschachtelten Anfuehrungszeichen kann eine ganze systemd-Unit
ungueltig machen, und damit auch jeden anderen Schritt derselben Unit mitreissen.

Ruft NUR ``MicroClayRetrieval.befoerderung_pruefen()`` auf -- die eigentliche
Pruefung (Schwellen, Beleg, Reversibilitaet) steht dort, nicht hier. Dieses
Skript ist bewusst duenn: ein Takt, kein zweiter Ort mit eigener Meinung ueber
die Schwellen.
"""
import json
import sys

sys.path.insert(0, "/opt/entityos/the artefact")

from clayverse.microclay_retrieval import MicroClayRetrieval
from clayverse.store import UnifiedDB

DB_PATH = "/var/lib/clay/wiki.db"


def main() -> None:
    db = UnifiedDB(DB_PATH)
    try:
        ergebnis = MicroClayRetrieval(db).befoerderung_pruefen()
    finally:
        db.close()
    print(json.dumps(ergebnis, ensure_ascii=False))


if __name__ == "__main__":
    main()
