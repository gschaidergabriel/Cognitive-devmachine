"""Profile autonom verdichten -- aus gemessenen Datenpunkten, nie aus Vermutung.

Eignerauftrag: "diese profile ueber die beiden muessen autonom weiter verdichtet
und angereichert werden aus allen moeglichen datenpunkten aber sinvoll".

⭐ DIE EINE REGEL, DIE DIESES MODUL TRAEGT

    ERKLAERTES WIRD NIE UEBERSCHRIEBEN.

Ein Mensch, der etwas ueber sich sagt, hat immer recht gegenueber einer
Maschine, die es aus Daten erschliesst. Felder mit herkunft `eigner` oder
`iar.frank.ink` sind fuer dieses Modul UNANTASTBAR -- es schreibt ausschliesslich
in den eigenen Namensraum `gemessen_*`. Damit kann eine Verdichtung ein Profil
anreichern, aber niemals verfaelschen, und ein Fehler hier bleibt ein Fehler in
einer Zusatzspalte statt in der Identitaet eines Menschen.

Die zweite Regel: JEDER WERT TRAEGT SEINEN BELEG -- die Abfrage oder Quelle, aus
der er stammt, in Textform. Ein Profilfeld ohne Beleg ist eine Behauptung ueber
einen Menschen. Wer sie spaeter pruefen will, muss sie nachrechnen koennen,
ohne dieses Modul zu lesen.

Die dritte Regel: WAS SICH NICHT MESSEN LAESST, WIRD NICHT GESCHRIEBEN. Kein
Feld bekommt einen Platzhalter, keine Zahl wird geschaetzt. Ein fehlendes Feld
ist ein ehrlicher Zustand; ein geschaetztes sieht aus wie ein gemessenes.
"""
from __future__ import annotations

import time

# Was dieses Modul anfassen darf. Alles andere gehoert dem Menschen.
EIGENER_NAMENSRAUM = "gemessen_"
UNANTASTBAR = {"eigner", "iar.frank.ink"}


def _schreibe(db, user_id: str, feld: str, wert: str, beleg: str) -> bool:
    """Nur in den eigenen Namensraum, nur wenn nichts Erklaertes im Weg steht."""
    if not feld.startswith(EIGENER_NAMENSRAUM):
        raise ValueError(f"Verdichtung darf nur {EIGENER_NAMENSRAUM}* schreiben, nicht {feld}")
    vorhanden = db.db.execute(
        "SELECT herkunft FROM entityos_profil WHERE user_id=? AND feld=?", (user_id, feld)
    ).fetchone()
    if vorhanden and vorhanden["herkunft"] in UNANTASTBAR:
        # Kann bei korrektem Namensraum nicht passieren -- aber wenn doch, ist
        # Schweigen richtig. Ein Mensch hat gegenueber einer Messung recht.
        return False
    with db.tx() as sql:
        sql.execute(
            "INSERT INTO entityos_profil(user_id,feld,wert,herkunft,beleg,erfasst) "
            "VALUES(?,?,?,'gemessen',?,?) ON CONFLICT(user_id,feld) DO UPDATE SET "
            "wert=excluded.wert, herkunft='gemessen', beleg=excluded.beleg, "
            "erfasst=excluded.erfasst",
            (user_id, feld, wert, beleg, time.time()))
    return True


# ── Die Messsonden. Jede gibt (feld, wert, beleg) oder nichts zurueck. ──────

def _wiki_bestand(db, user_id):
    r = db.db.execute(
        "SELECT gehoert, COUNT(*) n FROM entityos_artikel_zuordnung "
        "WHERE gehoert IN (?, 'gemeinsam') GROUP BY gehoert", (user_id,)).fetchall()
    if not r:
        return None
    d = {x["gehoert"]: x["n"] for x in r}
    eigen, geteilt = d.get(user_id, 0), d.get("gemeinsam", 0)
    return (f"{EIGENER_NAMENSRAUM}wiki_bestand",
            f"{eigen} eigene Artikel, {geteilt} gemeinsame",
            "SELECT COUNT(*) FROM entityos_artikel_zuordnung GROUP BY gehoert")


def _schwerpunkte(db, user_id):
    """Woran dieser Mensch tatsaechlich arbeitet -- aus den eigenen Artikeln."""
    r = db.db.execute(
        "SELECT a.projekt, COUNT(*) n FROM entityos_artikel_zuordnung z "
        "JOIN artikel a ON a.id = z.artikel_id WHERE z.gehoert=? AND a.projekt IS NOT NULL "
        "GROUP BY a.projekt ORDER BY n DESC LIMIT 5", (user_id,)).fetchall()
    if not r:
        return None
    return (f"{EIGENER_NAMENSRAUM}schwerpunkte",
            ", ".join(f"{x['projekt']} ({x['n']})" for x in r),
            "Projekte der ihm zugeordneten Wiki-Artikel, absteigend")


def _rechner(db, user_id):
    # Die Spalte heisst gehoert_zu. Sie hier `gehoert` zu nennen kostete einen
    # ganzen Messdurchgang: die Abfrage warf, das except schluckte, der Bericht
    # meldete "nichts gemessen" -- bei voller Tabelle mit korrekter Zuordnung.
    try:
        r = db.db.execute(
            "SELECT wirt, gehoert_zu FROM entityos_wirte ORDER BY wirt").fetchall()
    except Exception as e:
        # Eine fehlende Tabelle ist ein zulaessiger Zustand. Eine kaputte
        # Abfrage ist ein Fehler und muss als solcher hochkommen -- sonst sieht
        # ein Tippfehler wieder aus wie ein leeres Messergebnis.
        if "no such table" in str(e):
            return None
        raise
    if not r:
        return None
    eigen = [x["wirt"] for x in r if x["gehoert_zu"] == user_id]
    if not eigen:
        return None
    return (f"{EIGENER_NAMENSRAUM}rechner",
            ", ".join(eigen),
            "entityos_wirte, Spalte gehoert_zu -- erklaerte Zuordnung, nicht geraten")


def _gespraechsaktivitaet(db, user_id):
    for tab, sp in (("turns", "user_id"), ("mv_prestage_turns", "user_id")):
        try:
            r = db.db.execute(
                f"SELECT COUNT(*) n, MIN(created_at) a, MAX(created_at) b FROM {tab} WHERE {sp}=?",
                (user_id,)).fetchone()
        except Exception:
            continue
        if r and r["n"]:
            return (f"{EIGENER_NAMENSRAUM}gespraeche",
                    f"{r['n']} Zuege in {tab}",
                    f"SELECT COUNT(*) FROM {tab} WHERE {sp}='{user_id}'")
    return None


def _gedaechtnis(db, user_id):
    try:
        r = db.db.execute(
            "SELECT COUNT(*) n FROM memory_tabelle WHERE user_id=?", (user_id,)).fetchone()
    except Exception:
        return None
    if not r or not r["n"]:
        return None
    return (f"{EIGENER_NAMENSRAUM}gedaechtniseintraege", str(r["n"]),
            "memory_tabelle, nach user_id getrennt (Spalte am 18.08. ergaenzt)")


SONDEN = (_wiki_bestand, _schwerpunkte, _rechner, _gespraechsaktivitaet, _gedaechtnis)


def verdichten(db, user_ids=("gabriel", "andreas")) -> dict:
    """Alle Sonden fuer alle Menschen. Ausfallsicher je Sonde."""
    bericht = {}
    for uid in user_ids:
        geschrieben, still, fehler = [], [], []
        for sonde in SONDEN:
            name = sonde.__name__.lstrip("_")
            try:
                treffer = sonde(db, uid)
            except Exception as e:
                # Eine kaputte Sonde darf die anderen nicht mitnehmen -- aber sie
                # wird GENANNT. Stilles Ueberspringen liesse eine tote Sonde wie
                # eine ergebnislose aussehen.
                fehler.append(f"{name}: {type(e).__name__}: {e}")
                continue
            if treffer is None:
                still.append(name)          # nichts gemessen ist ein Ergebnis
                continue
            feld, wert, beleg = treffer
            if _schreibe(db, uid, feld, wert, beleg):
                geschrieben.append(feld)
        bericht[uid] = {"geschrieben": geschrieben, "nichts_gemessen": still, "fehler": fehler}
    return bericht
