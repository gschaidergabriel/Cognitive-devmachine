#!/usr/bin/env python3
"""Verfall der Wegehierarchie -- als eigenes Skript, nicht als Einzeiler.

Der erste Versuch stand als python -c direkt in der systemd-Unit und scheiterte
an verschachtelten Anfuehrungszeichen ("Unbalanced quoting, ignoring"). Die
Unit war damit KOMPLETT ungueltig -- also waere auch der Schnappschuss davor
nicht mehr gelaufen. Ein zu cleverer Einzeiler kann einen funktionierenden Takt
mitreissen.
"""
import sys, json, contextlib
sys.path.insert(0, "/opt/unifieddb")
from udb.abruf import paket as P
from udb.abruf import wegehierarchie as W


class Gefaess:
    """Duenne Huelle: wegehierarchie erwartet db.tx()/db.db wie der Store."""
    def __init__(self, conn):
        self.db = conn

    def tx(self):
        @contextlib.contextmanager
        def t():
            yield self.db
        return t()


if __name__ == "__main__":
    c = P._connect()
    h = Gefaess(c)
    W.sicherstellen(h)
    print(json.dumps({**W.verfallen(h), "pruefung": W.pruefung(h)}, ensure_ascii=False))
    c.close()
