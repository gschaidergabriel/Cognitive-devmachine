"""udb — die vereinigte Datenbank als Modul.

Die Umkehrung, die hier gilt: die Datenbank IST das System. ClayVerse ist ein
Modul darauf, nicht umgekehrt. Deshalb ist dies die einzige Vordertuer:

    import udb
    udb.zustand()        # was tut das System GERADE -- ein Aufruf, kein Modell
    udb.verbindung()     # die nur-lesende Standardverbindung des Hauses

Die Namen werden ERST BEIM ZUGRIFF geladen (PEP 562). Ein `import udb`
kostet damit nichts und zieht keine Nebenwirkung nach sich -- wichtig, weil
mehrere Dauerlaeufer gegen dieselbe Datei arbeiten.
"""

__all__ = ["zustand", "zustand_json", "zustand_text", "verbindung", "DB_PATH"]


def __getattr__(name):
    if name in __all__:
        from .abruf import zustand as _z
        return getattr(_z, name)
    raise AttributeError("Modul 'udb' hat kein Attribut %r" % name)


def __dir__():
    return sorted(__all__)
