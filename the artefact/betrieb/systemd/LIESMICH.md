# Autonome Takte

Diese Units laufen auf dem Wirt (nicht im Container) als Benutzer `clay` und
halten die Daten in Bewegung, aus denen Zero seine Antworten zieht.

| Takt | Alle | Was er tut |
|---|---|---|
| `entityos-baunotizen` | 15 min | Nimmt Baunotizen auf (protokoll.jsonl, bauverlauf.jsonl, Git-Commits) **und ordnet danach alle Artikel zu** |
| `entityos-profile` | 30 min | Verdichtet die Menschenprofile aus 5 Sonden, jede mit Beleg |

## Warum das Zuordnen am Aufnehmen haengt

Gemessen: 16.558 Artikel, aber nur 16.551 in der Zuordnungstabelle. Sieben neue
Baunotizen waren aufgenommen, aber niemand hatte sie zugeordnet -- und die
Luecke waechst mit jedem Takt still weiter. Zwei getrennte Zeitplaene fuer zwei
Schritte derselben Kette laufen unweigerlich auseinander. Deshalb `ExecStartPost`
statt eines zweiten Timers.

## Warum sie hier im Repo liegen

Sie sind ausfuehrbarer Teil von EntityOS. Lagen sie nur unter
`/etc/systemd/system/`, waeren sie beim naechsten Wiederaufbau verschwunden --
und niemand haette gemerkt, dass die Daten aufhoeren, sich zu erneuern. Ein
stehender Takt sieht von aussen aus wie ein ruhiger.

⚠️ Die Kopien hier sind die Wahrheit; nach dem Aendern zurueck nach
`/etc/systemd/system/` und `systemctl daemon-reload`.
