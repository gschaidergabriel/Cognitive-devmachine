# `/api/history` — dauerhafter Chatverlauf, fertig und geprueft

Fuer die Instanz, die die Oberflaeche neu einkleidet: **der Verlauf ist da, er
muss nur aufgerufen werden.** Das Frontend, das ihn geladen hat, wurde am
18.08. um 10:07 beim Neueinkleiden von `web/chat/index.html` ueberschrieben --
das Backend hat ueberlebt und ist unveraendert nutzbar.

## Warum es das gibt

Gabriel hat neu geladen und sein ganzer Chat war weg. Die Daten waren NIE
verloren: `turns` hielt 56 Zeilen, korrekt nach Sitzung getrennt. Es gab nur
keinen Weg zurueck ins Fenster. Ein Speicher, den niemand liest.

## Aufruf

    GET /api/history?session=<session_id>&limit=50[&before=<ordinal>]

    session   Pflicht. `session:<mensch>` oder `session:<mensch>:2`.
    limit     Vorgabe 50, Hoechstwert 200.
    before    Blaettert aelter: der `ordinal` der aeltesten schon geladenen Zeile.

Antwort: Zuege aeltestes-zuerst, plus `has_more`. Bei Assistenten-Zuegen wird
ueber `mv_translation_log` die deutsche Uebersetzung mitgeliefert -- dieselbe,
die auch live im Chat steht. Fehlt eine (Terminal-Zuege, abgebrochene Zuege),
kommt der Rohtext.

## ⚠️ Was beim Einbau nicht verlorengehen darf

1. **Nach dem `ready` des Gateways laden, nicht beim DOM-Start.** `ready` feuert
   beim Verbinden UND beim Sitzungswechsel -- damit laedt jede Sitzung ihren
   eigenen Verlauf, ohne zweiten Auslöser.

2. **Leer ist ein Zustand, keine leere Seite.** Eine Sitzung ohne Zuege muss
   "Noch keine Nachrichten in dieser Sitzung" zeigen. Sonst sieht sie exakt so
   aus wie ein fehlgeschlagener Ladevorgang -- genau die Zweideutigkeit, wegen
   der dieser Endpunkt gebaut wurde.

3. **Eine sichtbare Trennlinie** zwischen geladenem Verlauf und dem, was in
   dieser Sitzung neu dazukommt. Ohne sie kann niemand unterscheiden, was Zero
   gerade gesagt hat und was von gestern stammt.

4. **Ladefehler anzeigen, nicht verschlucken.** Ein stiller Fehlschlag sieht
   wieder aus wie eine leere Sitzung.

## Berechtigung — nicht anfassen

Die Sitzungs-ID aus der Adresszeile wird NIE geglaubt. Geprueft wird ueber
`identity.ist_kanonische_sitzung(session_id, user_id)`, wobei `user_id`
ausschliesslich aus dem verifizierten Clerk-Token stammt.

Nachgewiesen mit echten Tokens gegen den laufenden Container:

    kein/falsches Token        -> 401
    gabriel -> session:gabriel   -> 200
    gabriel -> session:gabriel:2 -> 200
    gabriel -> session:andreas   -> 403
    gabriel -> session:andreas:2 -> 403
    gabriel -> session:andreas:99-> 403   (faellt auch bei Unsinn geschlossen)
    andreas -> session:andreas:2 -> 200
    andreas -> session:gabriel:2 -> 403

Am 18.08. hat dieses System schon einmal einem Menschen die privaten Eintraege
des anderen gezeigt, weil einer Tabelle die Nutzerspalte fehlte. Diese Tuer
bleibt zu.

## Nebenbefund, ungeprueft weitergegeben

`/etc/clayverse/entityos-clerk.env` enthaelt eine VERALTETE Clerk-Kennung fuer
Andreas, die nicht zu `CLAYVERSE_CLERK_MAP_JSON` im laufenden Container passt
(die steht in `/etc/clayverse/entityos-deploy.env`). Wer gegen die alte Datei
testet, bekommt "unmapped Clerk subject". Ob die Datei noch irgendwo gelesen
wird, wurde NICHT geprueft.
