"""udb._quelle — die eine Quelle je Modul.

Der Befund, der dieses Modul noetig macht: /opt/unifieddb/udb/ war ein KLON
von /opt/clayverse/werkzeug/. 9 Module byte-identisch, 4 binnen eines Tages
auseinandergelaufen. Ein Klon, der driftet, ist in einem Monat ein zweites
System -- und dann ist "ClayVerse ist nur ein Modul" kein Aufraeumen mehr,
sondern ein Umbau.

Also: kein udb-Modul ist noch eine KOPIE. Es ist ein VERWEIS.

Richtung der Wahrheit, begruendet (nicht nach Datum):
  Quelle = /opt/clayverse/werkzeug/. Dort laufen die Dienste (systemd-Units),
  dort landeten die Verbesserungen dieses Tages, und dort zeigt jeder
  Aufrufer hin. udb hatte zum Zeitpunkt der Messung NULL Importeure -- eine
  Seite ohne Leser kann nicht die Quelle sein.
  ⚠️ Das ist die Richtung fuer HEUTE, nicht fuer immer. Sobald die
  abgedrifteten Module abgeglichen sind, gehoert die Bibliothek nach udb und
  werkzeug/ wird die duenne Kommandozeile darueber -- das ist die Richtung,
  die der Eigner vorgegeben hat. Sie jetzt zu erzwingen hiesse, laufenden
  Diensten einen neuen Ladeweg unterzuschieben. Erst abgleichen, dann drehen.
"""
from __future__ import annotations

import importlib.util
import os
import sys

WERKZEUG = os.environ.get("CLAYVERSE_WERKZEUG", "/opt/clayverse/werkzeug")


def lade(name: str):
    """Laedt werkzeug/<name>.py als Modul 'udb._wz.<name>'.

    Bewusst NICHT als oberste Ebene: 'index', 'graph' oder 'karte' wuerden
    dort mit fremden Paketen kollidieren. Der eigene Namensraum verhindert
    das. __name__ ist dabei nie '__main__', die main()-Blöcke laufen also
    nicht mit.
    """
    voll = "udb._wz." + name
    da = sys.modules.get(voll)
    if da is not None:
        return da
    pfad = os.path.join(WERKZEUG, name + ".py")
    if not os.path.isfile(pfad):
        raise ImportError(
            "Quelle fehlt: %s (erwartet fuer udb._wz.%s)" % (pfad, name))
    spec = importlib.util.spec_from_file_location(voll, pfad)
    if spec is None or spec.loader is None:            # pragma: no cover
        raise ImportError("nicht ladbar: %s" % pfad)
    m = importlib.util.module_from_spec(spec)
    # Vor exec_module eintragen, damit Selbstbezuege nicht endlos laufen.
    sys.modules[voll] = m
    try:
        spec.loader.exec_module(m)
    except BaseException:
        sys.modules.pop(voll, None)
        raise
    return m


def uebernehmen(zielname: str, quellname: str):
    """Haengt alle oeffentlichen Namen der Quelle an das aufrufende Modul.

    Auch die mit einem fuehrenden Unterstrich werden uebernommen -- die
    Werkzeuge dieses Hauses nutzen _hilfsnamen quer, und ein Verweis, der
    weniger kann als die Kopie, ist ein Rueckschritt. Nur die Dunder
    bleiben beim Ziel.
    """
    m = lade(quellname)
    ziel = sys.modules[zielname]
    uebernommen = []
    for k, v in vars(m).items():
        if k.startswith("__") and k.endswith("__"):
            continue
        setattr(ziel, k, v)
        uebernommen.append(k)
    ziel.__quelle__ = m.__file__
    ziel.__all__ = sorted(k for k in uebernommen if not k.startswith("_"))
    return m
