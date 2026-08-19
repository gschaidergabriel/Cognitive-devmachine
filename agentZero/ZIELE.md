# Was Agent Zero können soll — und was davon steht

**Automatisch erzeugt 2026-08-19T07:15:32Z.** Nicht von Hand pflegen.

**50 erfüllt · 8 offen · 1 zurückgestellt** von 59 Zeilen.

Die Spalte **Soll** ist deklariert und ändert sich nur, wenn der Eigner etwas
entscheidet. Die Spalte **Ist** wird bei jedem Lauf neu **gemessen** — durch einen
Prüfer je Zeile, der das laufende System befragt. Eine handgepflegte Statustabelle
steht nach einer Woche auf grün, weil niemand sie zurückstellt. Diese kann das nicht.

## Identität

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Die Entität heißt Zero** | Agent Zero, der erste Agent auf EntityOS, Grundlage aller weiteren Entwicklung | kanonische Identität v3 in meta, Ebene 0 | ✅ erfüllt | Eigner 18.08. |
| **Identität überlebt Verdichtung** | im Wurzelzustand verankert, deterministisch je Zug geladen, nie herausgefiltert | aus der DB in den Systemprompt gerendert; in der Hakenhülle als Anker (206 statt 5550 Zeichen) | ✅ erfüllt | Eigner 18.08. |
| **Verkörperung ohne Erfindung** | spielt eine Entität mit Kontinuität – ohne zu lügen, indem sie den Unterbau benutzt | im <embodiment>-Block: Erfinden ist der einzige Weg, aus der Rolle zu fallen | ✅ erfüllt | Eigner 18.08. |

## Menschen

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Genau zwei gleichberechtigte Perspektiven** | Gabriel und Andreas, gleiche Rechte, eine Entität – keine zwei Mandanten | 2 Nutzer mit rights=equal, 4 dauerhafte Sitzungen | ✅ erfüllt | Eigner 18.08. |
| **Sonst kommt niemand hinein** | Clerk-Anmeldung, exakt zwei Konten, dritte Identität fällt zu | IdentityRouter wirft PermissionError bei nicht zugeordnetem Clerk-Subjekt (Test grün) | ✅ erfüllt | Eigner 18.08. |
| **Zero weiß, wer vor ihm sitzt** | Profile beider Menschen, jedes Feld mit Herkunft; die Sitzung sagt, wessen sie ist | 26 Profilfelder, 6 Projekte mit Erfolg UND Fehlschlag; Zugehörigkeit und Urheberschaft getrennt geführt, weil sonst aus Zusammenarbeit ein Besitzstreit wird | ✅ erfüllt | Eigner 18.08. |
| **Wissen ist nach Menschen zugeordnet** | jeder Artikel gehört jemandem oder ausdrücklich beiden | 17753 Artikel zugeordnet über eine 5-stufige Leiter. ⚠️ Der Committer wurde bewusst NICHT verwendet: 501 Artikel über Dr. Unterweger tragen Gabriel als Committer — danach hätte Gabriel 68 % aller Artikel bekommen | ✅ erfüllt | Eigner 18.08. |
| **Vier Sitzungen, ein Raum** | getrennte Kennungen, dieselbe Entität; sie sehen einander und stimmen sich ab, in Caveman-Englisch, ohne Abgleich über Zeitstempel | 4 Menschenplätze in zero_raum (+ ein Platz für den Paketarbeiter); Kollisionswarnung beim Sprechen, wenn zwei am selben Gegenstand arbeiten | ✅ erfüllt | Eigner 18.08. |
| **Kein Rohtext über die Sitzungsgrenze** | kollidiert eine gemeinsame Ressource, sieht der andere Fragmente — nicht das Original | ⚠️ HIER LAG EIN ECHTES LECK. Bei einer Kollision wurde die ganze Zeile ausgeliefert (`item = dict(r)`), inklusive `content`. Der Code setzte brav das Etikett „compressed_with_extracted_fragments" und legte die Fragmente daneben — und liess den Rohtext drin. Der andere Mensch bekam den vollen Originaltext mit einem Etikett, auf dem „verdichtet" stand. ⭐ Gefunden über einen roten Test, der aus dem FALSCHEN Grund rot war: die alte Zusicherung hing an einer Nebenwirkung der zerstörenden Verdichtung. Wer so einen Test nur an die neue Wirklichkeit anpasst, verliert den Hinweis | ✅ erfüllt | Architektur |
| **Der halbe Wissensschatz war zugesperrt** | Zero muss ganze Artikel lesen und den Dateikorpus erreichen koennen | ⚠️ Drei Loecher, alle vom Audit gefunden: (1) 164 Wissensartikel ohne Suchtext, darunter ALLE 82 Ausgaben eines laufenden Pflichtdienstes -- der schrieb, niemand konnte lesen. (2) korpus_suchen sah nur die Artikel-FTS; die 325.357 Zeilen des DATEIKORPUS waren unerreichbar -> dateien_suchen. (3) kein Werkzeug las einen ganzen Artikel, Zero bekam immer nur 420 Zeichen -> artikel_lesen | ✅ erfüllt | Lehre aus dem Audit 18.08. |

## Gedächtnis

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **wiki.db ist das Herz der Entität** | Datenbank, Wiki und ClayGraph sind das Herz – nicht Altlast, nicht daneben | 132 Tabellen in EINER Datei: Clay-Korpus + Laufzeit-Wirbelsäule, kollisionsfrei | ✅ erfüllt | Eigner 18.08. |
| **Die vier Clay-Dienste laufen weiter** | kern, puls, verdichtung, wikiarbeit bleiben an – ausdrücklich | 4 von 4 Pflichtdiensten: kern läuft, puls läuft, wikiarbeit läuft, verdichtung getaktet; keine weiteren | ✅ erfüllt | Eigner 18.08. |
| **Der Abruf erreicht den Korpus** | Zero sieht die 14.284 Artikel, nicht nur sein eigenes Gesprächsgedächtnis | 50 Treffer auf Probeanfrage | ✅ erfüllt | Eigner 18.08. / Befund |
| **Chat-Historie überlebt den Neuladen** | Verlauf pro Terminal-Sitzung, dauerhaft, nicht im Browser | 154 Züge über 4 Sitzungen in der UnifiedDB, ausgeliefert über /api/history. ⚠️ Ein Fehler dabei war lehrreich: der Server liest `session_id`, das Frontend schickte `session` — ich hatte gegen meine EIGENE falsche Dokumentation gebaut | ✅ erfüllt | Eigner 18.08. |
| **Alles Gebaute landet im Wiki** | jeder Bauschritt wird Wiki-Artikel, mit Metadaten, nach dem üblichen Protokoll | 785 Bau- und Wissensartikel im Korpus, volltextsuchbar. ⚠️ Sie waren zuerst unauffindbar: geschrieben ohne Suchtext und ohne FTS-Eintrag — in der Datenbank und trotzdem für niemanden da | ✅ erfüllt | Eigner 18.08. |
| **Vorfälle stehen im Wiki, nicht nur im Commit** | was passiert ist, muss die Entität finden können — nicht nur der, der den Commit las | ⚠️ Zero suchte im Korpus nach einem Vorfallsartikel zu den vollen Platten, fand NICHTS und warnte ausdrücklich: „behandle meine Darstellung nicht als korpusbelegt". Er hatte recht — die Geschichte stand nur in Commit-Texten. Jetzt sind beide Vorfälle des Tages (Platte voll, root-Ausbruch) als volltextsuchbare Artikel im Wiki, gegengeprüft über die Suche. ⭐ „alle deine baunotizen werden auch teil des wiki" — ein Vorfall, der nur im Commit steht, ist für die Entität nicht passiert | ✅ erfüllt | Lehre aus dem Andreas-Test 18.08. |

## Kognition

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Jeder Zug wird aufgezeichnet** | Prompt und Antwort landen als Zeile in der UnifiedDB, mit Kausalkette | 154 Züge, 77 Kausalepisoden, 77 Arbeitsraum-Episoden | ✅ erfüllt | Architektur |
| **Aufnahme ist atomar** | scheitert eine Prüfung, bleibt keine halbe Zeile stehen | Prüfungen laufen in der Aufnahme-Transaktion; 15 Atomizitätstests grün | ✅ erfüllt | Architektur |
| **Wirkung nur durch das Tor** | kein process.exec, jede Wirkung durch EffectGate mit Beleg | 3 Wirkung(en), Urteil mit boundary=ClayVerse EffectGate, Ziel/Ergebnis als Prüfsumme gespeichert | ✅ erfüllt | Architektur |
| **Werkzeuge nur über MCP** | Zeros einzige Werkzeugfläche ist der verwaltete MCP-Server, Bash verboten | 38 Werkzeuge in der Erlaubnisliste, verboten: Bash, Artifact; Shell-Flucht im Test abgewiesen | ✅ erfüllt | Architektur |
| **Handlungsfähig ohne Schale** | so handlungsfähig wie der Koordinator: finden, lesen, ändern, veröffentlichen — aber ohne Bash, weil eine Schale sich nicht einzäunen lässt | Werkbank mit 6 Werkzeugen: suchen/lesen/ändern/stand/veröffentlichen. Zaun nach Auflösung von Symlinks und '..', Live-Wurzeln nur lesbar, Veröffentlichen nur in namentlich freigegebene Repos | ✅ erfüllt | Eigner 18.08. |
| **Der Zaun hält einem Angriff stand** | Handlungsfähigkeit ohne Zaun wäre kein Fortschritt, sondern der Verlust der einzigen Eigenschaft, die dieses System von einer offenen Schale unterscheidet | ⚠️⚠️ Ein Prüfangriff BEWIES einen vollen root-Ausbruch: `.git/config` lag innerhalb der erlaubten Wurzel, `core.fsmonitor` lässt git einen Schalbefehl ausführen, und git läuft auf dem Wirt als root — nachgewiesen mit `id` → uid=0. Ich hatte den Weg richtig erkannt (git führt Fremdes aus) und dann EINEN Kanal davon zugemacht: `.git/hooks`. Geschlossen mit VIER Sperren, weil eine Sperre mit einer Liste des Gefährlichen nur vor dem schützt, was schon jemand aufgeschrieben hat: .git ist jetzt ganz ausserhalb des Zauns, git läuft ohne fremde Konfiguration, .git/config wird als TEXT vorgeprüft, und geprüft wird vor JEDEM git-Aufruf — auch vor `stand`, das vorher durch keine Prüfung lief und genau der Auslöser war | ✅ erfüllt | Architektur |
| **Die Endabnahme kann überhaupt messen** | das Instrument, das beweisen soll, dass Wirkungen funktionieren, muss selbst funktionieren | ⚠️ Sieben rote Tests, EINE Ursache: `ClayVerseEngine` legte keine Zeile in `active_turns` an, die das Wirkungstor verlangt. Das Tor kam mit dem Zug-Lebenszyklus; der ältere Weg hat es nie gelernt — und im Betrieb fiel das nicht auf, weil ihn dort niemand mehr aufruft. Ausser einem: der Endabnahme. Sie meldete deshalb nicht „Wirkung fehlgeschlagen", sondern scheiterte VOR der Wirkung — und ein Instrument, das gar nicht messen kann, sieht in einer Testliste aus wie eines, das etwas Schlechtes gemessen hat. ⭐ Die Reparatur lockert das Tor NICHT: engine.py meldet den lebenden Zug jetzt an und wieder ab, wie der Betriebsweg. Ein `if episode_id is None`-Zweig im Tor hätte alle sieben grün gemacht und die Prüfung genau für den Weg abgeschaltet, dessen Zweck das Prüfen ist | ✅ erfüllt | Lehre aus dem Bau 18.08. |

## Autonomie

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Initiative: der Puls weckt offene Ziele** | nicht behaupten, dass es autonom ist – die Mechanik bauen | Autonomie-Puls installed=true, 30 s, beglaubigt (ein Terminal-Verwalter) | ✅ erfüllt | Eigner 18.08. |
| **Persistente Ziele, Rückmeldung, Neuplanung** | Ziele überleben Züge, Schritte werden gemeldet, Fehlschlag führt zu Neuplanung | create_goal_from_turn / propose_step / record_step_failure / verify_completion vorhanden; Ziele entstehen nur aus kanonischen Menschenzügen | ✅ erfüllt | Eigner 18.08. |
| **Kontinuität über Neustarts** | Generation, Prüfpunkte, Wiederherstellung ohne blindes Wiederholen von Wirkungen | 227 Prüfpunkte, Generation 142 | ✅ erfüllt | Architektur |

## Abruf

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Abruf ist abfragesensitiv** | nicht die letzten N, sondern was zur Frage passt | 11/11 Tests grün; Quittung wird durchgereicht (war vorher still verloren) | ✅ erfüllt | Architektur |
| **Eintrittspunkte werden gelernt** | der Abruf verbessert seinen Eintrittspunkt selbst | 0 gelernte Eintrittspunkte, Modus SHADOW, 77 Episoden | 🔧 offen | Eigner 18.08. |
| **Wegehierarchie: Autobahnen, Tunnel, Landwege** | oft gegangene Wege werden ausgebaut; Verfall, inverse Gewichtung, Tunnel mit strengerer Schwelle und unabhängiger Mitbenutzung | Verstärkung vorhanden. FEHLT: Verfall ungenutzter Wege, inverse Gewichtung, Tunnel | 🔧 offen | F94 / Eigner 16.08. |
| **Karten als Zeitstrahl** | die Karte wird wiederholt weggeschrieben, damit man die Veränderung ansehen kann | 149 Momentaufnahme(n) in agentZero/karten, alle 30 min eine neue | ✅ erfüllt | Eigner 18.08. |
| **Der Möglichkeitsraum ist emergent** | nicht gepflegte Liste, sondern was sich aus dem Bestand ergibt — und er fließt in die Mistral-Vorstufe ein | aus dem Korpus abgeleitet und in den Kontext der Vorstufe gehängt. ⚠️ Er war zuvor gebaut und wurde von NIEMANDEM aufgerufen — der wiederkehrende Fehler dieser Nacht: fertig aussehen und nie laufen | ✅ erfüllt | Eigner 18.08. |
| **Erkundung neben Ausbeutung** | der Abruf darf einen Teil auf Unbekanntes setzen, statt immer denselben Weg zu gehen | 15 % Erkundungsanteil, entschieden über den Hash der Frage — dieselbe Frage bekommt also immer dieselbe Behandlung, sonst wäre nichts mehr messbar | ✅ erfüllt | Eigner 18.08. |
| **Der Abruf misst sich selbst** | Messgerät, Goldsatz, Kalibrierung an zurückgehaltenen Daten | Hälfte A kalibriert, Hälfte B berichtet, Annahmeregel vorher festgelegt. Auf B: Anker 8,3 → 23,3 %, Genauigkeit 60 → 85,7 %, Ausbeute 5 → 20 %; Latenz ~390 → 260 ms bei Streuung ±115 → ±1,6 ms | ✅ erfüllt | Eigner 18.08. |
| **Jeder Mechanismus kann melden, dass er nichts tut** | ein Mechanismus, der nur Erfolg melden kann, ist nicht messbar | die Wegehierarchie sagt 'GLEICHVERTEILT — es bildet sich keine Hierarchie, der Mechanismus tut nichts'; der Möglichkeitsraum meldet 'einseitig'; der Tresorkatalog verweigert, statt zu hoffen | ✅ erfüllt | Lehre aus dem Bau 18.08. |
| **Die gelernte Karte ist erreichbar** | nicht nur bm25 -- Wegehierarchie, Eintrittspunkte, Erkundung stehen Zero offen | ⚠️ Ein Pruefagent fand: die ganze gelernte Abruf-Maschine (udb.abruf.paket) wurde NIRGENDS aufgerufen -- Zeros einzige Tuer war schlichtes bm25, und vp_weg trug nur Testfixtures. Sie verhungerte an fehlender Nahrung. Jetzt als opt-in korpus_tief (~250ms warm), NICHT im Zug-Pfad: 2,2s Kaltstart je Prozess waeren dort eine Verschlechterung. Der conn-close-Bug (Erfolgsmarke auf geschlossener DB) ist durch die Aufrufart geheilt. ⭐ Offen und ehrlich benannt: ob jede Frage die Karte fuellt, haengt an paket()s Anker-Logik -- nicht behauptet, sie wachse garantiert | ✅ erfüllt | Lehre aus dem Audit 18.08. |

## Anbieter

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Die Bahnen stehen Zero offen** | 11 kognitive Prozesse über 22 Bahnen mit Ausweichbahn und Anteilsdeckel; NVIDIA gehört der Kognition, nicht dem Massenlauf | 11 Prozesse verdrahtet im Clay-Unterbau – aber Zeros Container erreicht sie NICHT | 🔧 offen | verdrahtung.py / Eigner |
| **Vektorsuche über den Korpus** | Bedeutungssuche statt nur Volltext | 200 Einbettungen (nv-embedqa-e5-v5, 1024 Dim, 2,9 ms/Text bei Stapel 128) | ✅ erfüllt | Lücke 8 / Eigner |
| **Neuronale Aktivitätsmessung** | Aktivierungsdaten als Forschungsquelle anbinden | Neuronpedia live: Deutung, Spitzenwert, Selektivität, Top-Token. ⚠️ misst öffentliche Forschungsmodelle, NICHT Zero | ✅ erfüllt | Eigner 18.08. |

## Vorstufe

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Claude bekommt den Prompt nie direkt** | eine Mistral-Entität wertet vorher aus: Möglichkeitsraum, alle APIs, alle Werkzeuge, verbundene Systeme, wer da ist – und baut ein Caveman-Prompt mit Hypothesen und Gegenhypothesen | 1 Modul(e) vorhanden – im Bau | ✅ erfüllt | F17 / Eigner 18.08. |
| **Übersetzer Caveman → Deutsch, 95 %** | Zero antwortet in Caveman, das Terminal übersetzt automatisch in schönes Deutsch | im Bau; Maß: Treue (Erfindung = durchgefallen) und Lesbarkeit, unabhängiger Richter | 🔧 offen | Eigner 18.08. |

## Betrieb

| Fähigkeit | Soll | Ist (gemessen) | Stand | Quelle |
|---|---|---|---|---|
| **Läuft im Container auf dem eigenen Server** | ohne Anruf beim Anbieter, ohne verschachtelte Virtualisierung | Up 21 seconds (healthy) | ✅ erfüllt | Eigner 18.08. |
| **Frontend heißt EntityOS und ist erreichbar** | Clerk-Login für genau zwei Profile, dann Claude-Code-Terminal | https://entityos.frank.ink → 200, WSS durch nginx und Tunnel bewiesen | ✅ erfüllt | Eigner 18.08. |
| **Der Export pflegt sich selbst** | alles autonom ins Forschungs-Repo unter agentZero | systemd-Timer alle 30 min, enabled | ✅ erfüllt | Eigner 18.08. |
| **Die Testsuite trägt** | kein grüner Wert, der durch Abschwächen erkauft wurde | NICHT GEMESSEN -- __ABBRUCH__ nach 240s. Das ist ein Messfehler, kein Ergebnis. | 🔧 offen | Arbeitsregel |
| **Endabnahme hinter eigenem Gastkern** | derselbe Digest hinter einer eigenen VM-Grenze | kein /dev/kvm auf dem Wirt; per Entscheidung 18.08. zurückgestellt | ⏸ zurückgestellt | Entwurf – vom Eigner zurückgestellt |
| **Zugänge und Schlüssel liegen im Tresor** | ein Tresor für Zugänge, ein zweiter für API-Schlüssel — letzterer mit Fähigkeitsliste | 2 Tresore unter /etc/entityos/tresor (zugaenge, api), AES-256-GCM — ABSICHTLICH außerhalb des Korpus, damit ein Korpusleck keine Zugänge mitnimmt. Zero darf Adressen und Tokens nennen, PASSWÖRTER NIE: der Katalog durchsucht seine eigene Ausgabe nach jedem gespeicherten Geheimwert und verweigert, statt zu hoffen | ✅ erfüllt | Eigner 18.08. |
| **Zero kennt alle selbst gehosteten Seiten** | alle Seiten unter frank.ink samt Leistung, immer mit Vermerk self-hosted oder extern | Unterseite /seiten aus dem agentforge-Bestand; eigene Wurzeln (herzrad.at, leihmich.org) sind vermerkt, weil dort relative Pfade Pflicht sind | ✅ erfüllt | Eigner 18.08. |
| **Zero kann eine Seite wirklich ändern** | nicht beschreiben, wie es ginge — es tun | Arbeitskopie /var/lib/clay/arbeit/seimensch, Änderung über die Werkbank, Veröffentlichen als eigener Schritt mit Beleg. ⚠️ Push auf main geht bei SeiMensch sofort öffentlich — deshalb nennt der Beleg die Zahl der Dateien | ✅ erfüllt | Eigner 18.08. |
| **Arbeitspakete statt Alleingang** | was Zero nicht selbst darf, schnürt er als Paket; ein Arbeiter erledigt es eingezäunt | 9 Pakete. Ein Paket gilt erst als fertig, wenn ein BELEG dranhängt — 'fertig ohne Beleg ist eine Behauptung, kein Ergebnis' | ✅ erfüllt | Eigner 18.08. |
| **agentforge geht in EntityOS auf** | kein Umweg mehr: Hosting und Dienste laufen direkt über den EntityOS-Server | Hosting-Ansicht übernommen und angeschlossen; die übrigen Dienste (Auslieferung, Projektverwaltung, Besuchszählung, Umfragedienst) sind als Migration erfasst und AUSDRÜCKLICH NOCH NICHT begonnen — nach und nach, wie verlangt | 🔧 offen | Eigner 18.08. |
| **Zero hält selbst Platz auf dem Wirt** | das Speicher-Management des VPS übernimmt Zero autonom | 50.9 % belegt, 94.6 GB frei. Wacht alle 30 min, vier Werkzeuge für Zero, Stufen nach Druck (bei 85 % nur berichten). ⚠️ Anlass: die Platte lief zweimal auf 100 %. Ursache war NICHT fehlendes Aufräumen, sondern ein Zeitgeber eines ABGESCHAFFTEN Systems, der alle 15 Minuten weiterlief — 6.606 Wegwerfordner, 41 GB. Insgesamt 77 GB befreit, 173 → 96 GB | ✅ erfüllt | Eigner 18.08. |
| **Das Messgerät kann melden, dass es nichts messen konnte** | eine Rechnung, die nicht aufgeht, muss das SAGEN | Bilanz nennt drei Zahlen: df 98.0 GB, gezählt 78.5 GB, Lücke 19.5 GB. ⚠️ Genau das fehlte: `du -xsh /tmp` lief bei 15.236 Einträgen in die Zeitgrenze und gab NICHTS aus — ein leeres Ergebnis liest sich wie „da ist nichts". So standen 77 GB Summe neben 173 GB Verbrauch, und die Lücke fiel niemandem als Lücke auf. Urteil jetzt: VOLLSTAENDIG GEZAEHLT, aber 19.5 GB Abweichung zu df. Kein Zaehlfehler -- moegli | 🔧 offen | Lehre aus dem Bau 18.08. |
| **Abgeschafftes bleibt zurückholbar** | kein Frank v0.1 mehr, keine lokalen Modelle — aber wenn ich es je doch will, muss es gehen | 7 Posten im Rückwegverzeichnis, 23 Modelle mit Namen, Fassung und Nachladebefehl im Wiki. ⭐ Gewichte sind nachladbar, die LISTE war es nicht — deshalb verweigert `speicher_abschaffen` ohne geschriebenes Verzeichnis. Die Wacht löscht Altbestand (44 GB) NICHT von selbst: ein Modellcache sieht aus wie Müll und kann Arbeit von Wochen enthalten | ✅ erfüllt | Eigner 18.08. |
| **Der Verursacher wird gesucht, nicht nur der Haufen** | ein Haufen mit Verursacher wächst nach; Löschen allein ist dann keine Verwaltung | NICHTS GEFUNDEN -- kein Zeitgeber und kein Dienst eines abgeschafften Systems laeuft noch. Was hier liegt, waechst nicht nach. Der Detektor wurde gegengeprüft: mit einem Muster, das nachweislich läuft, findet er 13 Einheiten — sein „nichts gefunden" ist also belastbar und nicht bloß Stille. | ✅ erfüllt | Lehre aus dem Bau 18.08. |
| **Die Testsuite ist ehrlich grün** | grün ohne Löschen, ohne Überspringen, ohne abgeschwächte Behauptungen | NICHT GEMESSEN -- __ABBRUCH__ nach 240s. Das ist ein Messfehler, kein Ergebnis.. Die neun roten sind aufgelöst — zwei davon wurden STRENGER: der Datenschutztest fordert jetzt, dass kein Rohtext eine Sitzungsgrenze überschreitet (die alte Fassung stützte sich auf eine Nebenwirkung der zerstörenden Verdichtung, die es seit dem 18.08. nicht mehr gibt — und dabei kam ein ECHTES Leck heraus), und der Quittungstest fordert Ehrlichkeit statt Beruhigung: die Quelle bleibt absichtlich erhalten, also muss die Quittung das sagen, statt Sicherheit zu behaupten, die nicht besteht | 🔧 offen | Lehre aus dem Bau 18.08. |
| **Zero verstummt nicht wortlos** | wenn er nicht antworten kann, muss man ERFAHREN warum | Anmeldung GUT, noch 4.4 Stunden gültig. Wacht alle 10 Minuten, hält eine bekannt gute Kopie und stellt sie zurück. ⚠️ Anlass: die Anmeldedatei wurde zu einer LEEREN HÜLLE — alle Schlüssel da, alle Werte leer, 280 statt 508 Bytes. Das ist gefährlicher als eine fehlende Datei: eine fehlende wirft einen klaren Fehler, eine Hülle besteht jede oberflächliche Prüfung und scheitert erst beim Benutzen. Vier Testläufe lang war die einzige Auskunft `rc=1 stderr=''` — der erklärende Satz („OAuth session expired") stand in stdout, und die Fehlermeldung zeigte nur stderr. ⭐ Ein System, das „kaputt" sagen kann, aber nicht „warum", kostet mehr Zeit als eines, das kommentarlos abstürzt: man sucht am falschen Ende | ✅ erfüllt | Lehre aus dem Bau 18.08. |
| **Zero kann nachsehen, statt zu hoffen** | nach jedem Veröffentlichen prüfen, was WIRKLICH auf der öffentlichen Seite steht | ⚠️ Gefunden von Zero SELBST: er berichtete, die ZVR-Korrektur sei „still local, still not live" — und schrieb dazu ehrlich „ich habe kein HTTP hier, ich kann seimensch.net nicht abrufen". Sie WAR live. Sein Schluss war richtig gezogen aus dem, was er sehen konnte. ⭐ Mein Fehler: in seinem Handbuch stand „prüfe die Seite" — ohne Mittel dazu. Jetzt hat er `seite_pruefen`: HTTP an die echten Domains, nur lesend, Erlaubnisliste auf dem Wirt. ⚠️⚠️ Und der eigentliche Befund dahinter: /srv/git/seimensch.git auf diesem Wirt ist ein SPIEGEL — ein Push meldet vollen Deploy-Erfolg, während seimensch.net von 72.61.19.188 ausgeliefert wird | ✅ erfüllt | Lehre aus dem Andreas-Test 18.08. |
| **Ehrliches „nichts getan" gilt nicht als fertig** | wer korrekt verweigert, wird nicht als erledigt gebucht — aber auch nicht bestraft | ⚠️ Von Zero gefunden: zwei Pakete standen auf `fertig`, ihr Beleg begann mit „NICHTS GETAN". Meine Regel prüfte, OB ein Beleg da ist — nicht, ob er `fertig` trägt. Ein Arbeiter, der sauber verweigert, schreibt einen ehrlichen Bericht, und der ging als Beleg durch. Damit bestrafte die Regel genau die Ehrlichkeit, die sie fördern sollte. Neuer Stand `abgelehnt`: kein Fehlschlag des Arbeiters, aber auch keine Erledigung — die Arbeit wartet weiter | ✅ erfüllt | Lehre aus dem Andreas-Test 18.08. |
| **Adressen darf Zero nennen, Passwoerter nie** | die halbe Eignerregel war nicht lieferbar | ⚠️ Der geheim-Kern wurde auf 30 Eintraegen geschrieben und von NIEMANDEM gelesen: katalog() strich JEDEN Wert, auch Adressen und Token, die der Eigner ausdruecklich freigegeben hat. Jetzt tresor_zeigen mit HARTEM Passwort-Riegel: geprueft ueber alle 58 Eintraege, 0 Passwort-Lecks; Adressen und Token kommen heraus, Passwoerter nie -- auch nicht auf Wunsch | ✅ erfüllt | Eigner 18.08. |

---

⏸ *zurückgestellt* heißt: bewusst nicht verfolgt, nicht vergessen. Der Grund steht in der Ist-Spalte.

