# -*- coding: utf-8 -*-
"""Gezielt: gibt es IRGENDWO ein 'X darf ueber Y entscheiden'?"""
import sqlite3
c=sqlite3.connect('file:/var/lib/clay/wiki.db?mode=ro',uri=True); c.execute('PRAGMA busy_timeout=30000')
MUSTER=['%author%','%berecht%','%permit%','%capab%','%faehig%','%owner%','%eigent%',
        '%entscheid%','%decide%','%approve%','%freigab%','%grant%','%recht%','%darf%',
        '%zustaend%','%verantwort%','%massgeb%','%autorit%','%govern%','%policy%','%mandat%']
print("=== 1. kante.art ===")
arten=[r[0] for r in c.execute("select distinct art from kante")]
tr=[a for a in arten for m in MUSTER if m.strip('%') in a.lower()]
print("   Arten gesamt:",len(arten)," | mit Autoritaets-Wortstamm:",sorted(set(tr)) or "KEINE")
print("=== 2. Spaltennamen aller Tabellen ===")
found=[]
for (t,) in c.execute("select name from sqlite_master where type='table'"):
    try: cols=[r[1] for r in c.execute("PRAGMA table_info(%s)"%t)]
    except Exception: continue
    for col in cols:
        for m in MUSTER:
            if m.strip('%') in col.lower(): found.append((t,col))
print("   ", sorted(set(found)) or "KEINE Spalte mit Autoritaets-Wortstamm")
print("=== 3. artikel.art (Knotenklassen) ===")
kl=[r[0] for r in c.execute("select distinct art from artikel")]
print("   Klassen gesamt:",len(kl))
print("   mit Wortstamm:",sorted({k for k in kl for m in MUSTER if m.strip('%') in (k or '').lower()}) or "KEINE")
print("=== 4. artikel.scope / tags / projekt_art als Autoritaetstraeger? ===")
for sp in ['scope','tags','projekt_art','herkunft']:
    n=c.execute("select count(*) from artikel where %s is not null"%sp).fetchone()[0]
    bsp=[r[0] for r in c.execute("select distinct %s from artikel where %s is not null limit 5"%(sp,sp))]
    print("   %-12s belegt=%-6d Beispiele=%s"%(sp,n,bsp))
print("=== 5. herkunft: gemessen vs nutzer (einzige Autoritaetsunterscheidung?) ===")
for r in c.execute("select herkunft,count(*) from artikel group by 1"): print("   ",r)
print("=== 6. bearbeitung-Tabelle (massgebliche Handbearbeitung laut README) ===")
try:
    print("   Spalten:",[r[1] for r in c.execute("PRAGMA table_info(bearbeitung)")])
    print("   Zeilen :",c.execute("select count(*) from bearbeitung").fetchone()[0])
except Exception as e: print("   ",e)
