-- UnifiedDB: vollstaendiges Schema, KEINE Daten.
-- Erzeugt 2026-08-19T09:11:09Z aus /var/lib/clay/wiki.db.
-- Wer diese Datei hat, kann EntityOS neu aufbauen, ohne einen einzigen
-- Datensatz zu besitzen. Die echte Datenbank ist 3,8 GB und gehoert
-- nicht in ein Repo -- ihre Struktur schon.

PRAGMA foreign_keys=OFF;
BEGIN;
CREATE TABLE active_turns(session_id TEXT PRIMARY KEY REFERENCES sessions(session_id),user_id TEXT NOT NULL REFERENCES users(user_id),turn_id TEXT NOT NULL UNIQUE REFERENCES turns(turn_id),episode_id TEXT NOT NULL UNIQUE REFERENCES workspace_episodes(episode_id),causal_id TEXT NOT NULL UNIQUE,generation INTEGER NOT NULL,resource_refs TEXT NOT NULL DEFAULT '[]',effect_id TEXT REFERENCES effects(effect_id),outcome TEXT,workspace_selected INTEGER NOT NULL DEFAULT 0,started_at REAL NOT NULL);
CREATE TABLE anreicherung (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            artikel_id   TEXT NOT NULL,
            quelle_url   TEXT,
            art          TEXT,
            auszug       TEXT,
            geholt_am    TEXT,
            hash         TEXT
        );
CREATE TABLE artikel (
            id TEXT PRIMARY KEY,
            art TEXT NOT NULL,
            titel TEXT,
            quelle TEXT,
            quell_hash TEXT,
            datum TEXT,
            metadaten TEXT,       -- JSON, verbatim source metadata
            offene_fragen TEXT,   -- JSON array
            belegt INTEGER,
            erzeugt_am TEXT
        , duenn INTEGER DEFAULT 0, zuletzt_bearbeitet TEXT, zeitquelle TEXT, wirt TEXT, zuletzt_von TEXT, von_quelle TEXT, logical_id TEXT, id_quelle TEXT, epistemic_class TEXT, status TEXT, scope TEXT, tags TEXT, konfidenz REAL, projekt TEXT, projekt_art TEXT, sphaere TEXT, herkunft TEXT DEFAULT 'gemessen' CHECK (herkunft IN ('gemessen','nutzer')), verfallen INTEGER DEFAULT 0, protected INTEGER DEFAULT 0);
CREATE TABLE artikel_sphaere (
            artikel_id TEXT NOT NULL,
            sphaere TEXT NOT NULL,
            beleg TEXT,
            PRIMARY KEY (artikel_id, sphaere)
        );
CREATE TABLE artikel_suchtext (
                id INTEGER PRIMARY KEY,
                artikel_id TEXT NOT NULL UNIQUE,
                titel TEXT,
                text TEXT,
                blase TEXT,
                indiziert TEXT NOT NULL
            );
CREATE TABLE bahn_lage (
        schluessel TEXT PRIMARY KEY, wert TEXT NOT NULL, zeit TEXT NOT NULL);
CREATE TABLE bahn_lauf (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit TEXT NOT NULL, art TEXT NOT NULL, bahn TEXT, modell TEXT,
        ziel_id TEXT, dauer_ms REAL, http INTEGER,
        token_ein INTEGER, token_aus INTEGER,
        ergebnis TEXT NOT NULL,        -- angenommen | verworfen | fehler
        pruefung TEXT,                 -- warum verworfen
        antwort TEXT
    );
CREATE TABLE bahn_livestreak(
  bahn TEXT PRIMARY KEY,
  serie INTEGER NOT NULL DEFAULT 0,
  zuletzt_fehler REAL,
  zuletzt_ergebnis TEXT
);
CREATE TABLE bahn_nutzung(
  bahn TEXT NOT NULL,
  prozess TEXT NOT NULL,
  tag TEXT NOT NULL,
  anfragen INTEGER NOT NULL DEFAULT 0,
  token INTEGER NOT NULL DEFAULT 0,
  fehler INTEGER NOT NULL DEFAULT 0,
  zuletzt REAL NOT NULL,
  PRIMARY KEY(bahn, prozess, tag)
);
CREATE TABLE bearbeitung (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artikel_id TEXT NOT NULL,
        feld TEXT NOT NULL,
        alt_wert TEXT,
        neu_wert TEXT,
        autor TEXT,
        zeit TEXT NOT NULL,
        herkunft TEXT NOT NULL DEFAULT 'nutzer' CHECK (herkunft = 'nutzer')
    );
CREATE TABLE causal_episodes(causal_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),effect_id TEXT REFERENCES effects(effect_id),observation_turn_id TEXT REFERENCES turns(turn_id),outcome_hash TEXT,credit REAL NOT NULL DEFAULT 0,reentered INTEGER NOT NULL DEFAULT 0,ts REAL NOT NULL);
CREATE TABLE checkpoints(checkpoint_id TEXT PRIMARY KEY,ts REAL NOT NULL,state_hash TEXT NOT NULL,note TEXT NOT NULL);
CREATE TABLE datei (
                id INTEGER PRIMARY KEY,
                pruefsumme TEXT NOT NULL UNIQUE,
                titel TEXT,                 -- Dateiname des ERSTEN gesehenen Fundorts (nur Anzeige)
                art TEXT NOT NULL,          -- 'text' | 'binaer'
                volltext_indiziert INTEGER NOT NULL DEFAULT 0,
                groesse INTEGER,
                text TEXT,                  -- Volltext, EINMAL gespeichert
                indiziert TEXT NOT NULL
            );
CREATE TABLE durable_memory(memory_id TEXT PRIMARY KEY,kind TEXT NOT NULL,subject TEXT NOT NULL,value TEXT NOT NULL,source_turn_id TEXT REFERENCES turns(turn_id),user_id TEXT,ts REAL NOT NULL,provenance TEXT NOT NULL);
CREATE TABLE effects(effect_id TEXT PRIMARY KEY,episode_id TEXT REFERENCES workspace_episodes(episode_id),user_id TEXT NOT NULL,capability TEXT NOT NULL,target TEXT NOT NULL,argv TEXT,requested_generation INTEGER NOT NULL,status TEXT NOT NULL,outcome TEXT,ts REAL NOT NULL,verified_at REAL);
CREATE TABLE entityos_arbeitspaket (
  paket_id   TEXT PRIMARY KEY,
  besteller  TEXT NOT NULL,          -- gabriel | andreas, aus dem gepruefsten Zustand
  session_id TEXT NOT NULL,
  auftrag    TEXT NOT NULL,          -- Caveman: was zu tun ist
  womit      TEXT,                   -- die Sache: Datei, Dienst, Tabelle
  warum      TEXT,                   -- die Begruendung, damit ein Mensch pruefen kann
  stand      TEXT NOT NULL,          -- offen | laeuft | fertig | gescheitert | abgelehnt
  ergebnis   TEXT,
  beleg      TEXT,                   -- WOMIT belegt der Ausfuehrer, dass es getan ist
  erstellt   REAL NOT NULL,
  geaendert  REAL NOT NULL
);
CREATE TABLE entityos_artikel_zuordnung(
  artikel_id TEXT PRIMARY KEY,
  gehoert TEXT NOT NULL,           -- gabriel | andreas | gemeinsam | unbekannt
  grund TEXT NOT NULL,
  sicherheit REAL NOT NULL,        -- 0..1
  erfasst REAL NOT NULL
);
CREATE TABLE entityos_erfolge(
  id TEXT PRIMARY KEY,
  art TEXT NOT NULL,               -- erfolg | fehlschlag
  titel TEXT NOT NULL,
  wirkung TEXT,                    -- was es konkret geaendert hat
  beleg TEXT NOT NULL,             -- Messung/Beobachtung. Ohne Beleg kein Eintrag.
  gehoert TEXT,                    -- gabriel | andreas | gemeinsam
  seit_zero INTEGER NOT NULL DEFAULT 0,
  datum TEXT NOT NULL,
  erfasst REAL NOT NULL
);
CREATE TABLE entityos_profil(
  user_id TEXT NOT NULL,
  feld TEXT NOT NULL,
  wert TEXT NOT NULL,
  herkunft TEXT NOT NULL,          -- eigner | iar.frank.ink | abgeleitet | gemessen
  beleg TEXT,
  erfasst REAL NOT NULL,
  PRIMARY KEY(user_id, feld)
);
CREATE TABLE entityos_projekte(
  projekt TEXT PRIMARY KEY,
  gehoert TEXT,                    -- gabriel | andreas | gemeinsam
  gebaut_von TEXT,                 -- kann abweichen: Besitz ist nicht Urheberschaft
  stand TEXT NOT NULL,             -- laufend | abgeschlossen | gescheitert | ruht
  erfolg TEXT,                     -- erfolgreich | nicht_erfolgreich | offen
  seit_zero INTEGER NOT NULL DEFAULT 0,
  beschreibung TEXT,
  beleg TEXT,
  herkunft TEXT NOT NULL,
  erfasst REAL NOT NULL
);
CREATE TABLE entityos_wirte(
  wirt TEXT PRIMARY KEY,
  gehoert_zu TEXT,
  erste_sichtung REAL NOT NULL,
  zuletzt_gesehen REAL NOT NULL,
  generation INTEGER,
  gesund INTEGER NOT NULL DEFAULT 0,
  boot_id TEXT,
  module TEXT NOT NULL DEFAULT '{}',
  quelle TEXT NOT NULL DEFAULT 'herzschlag'
);
CREATE TABLE fehler (
            id TEXT PRIMARY KEY,
            art TEXT NOT NULL CHECK (art IN ('sql', 'shell', 'python', 'daten', 'provenienz', 'methode')),
            ausloeser_muster TEXT NOT NULL,
            was_passiert TEXT NOT NULL,
            wie_erkannt TEXT NOT NULL,
            wie_vermieden TEXT NOT NULL,
            schwere TEXT NOT NULL CHECK (schwere IN ('hoch', 'mittel', 'niedrig')),
            beleg TEXT NOT NULL,
            quelle TEXT NOT NULL,
            erkannt_am TEXT,
            bestaetigt_durch TEXT
        );
CREATE TABLE folgerung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            art TEXT NOT NULL CHECK (art IN ('hypothese','implikation','lehre')),
            aussage TEXT NOT NULL,
            begruendung TEXT,
            gilt_fuer TEXT NOT NULL,
            autor TEXT,
            zeit TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','gestuetzt','widerlegt','abgeloest')),
            widerlegt_durch INTEGER REFERENCES folgerung(id)
        , konfidenz REAL);
CREATE TABLE folgerung_beleg (
            folgerung_id INTEGER NOT NULL REFERENCES folgerung(id),
            beleg_art TEXT NOT NULL CHECK (beleg_art IN
                ('protokoll','artikel','messung','problem','kante','datei')),
            beleg_id TEXT NOT NULL,
            PRIMARY KEY (folgerung_id, beleg_art, beleg_id)
        );
CREATE VIRTUAL TABLE fts_index_artikel USING fts5(titel, text, content='artikel_suchtext', content_rowid='id');
CREATE VIRTUAL TABLE fts_index_datei USING fts5(titel, text, content='datei', content_rowid='id');
CREATE TABLE fundort (
                datei_id INTEGER NOT NULL,  -- FK auf datei.id (robuster Join)
                pruefsumme TEXT NOT NULL,   -- wie vom Eigentuemer verlangt, zur Anzeige/Direktabfrage
                wirt TEXT NOT NULL,
                pfad TEXT NOT NULL,
                blase TEXT,                 -- NULL = Kern/unbeschraenkt
                geaendert TEXT,
                PRIMARY KEY (wirt, pfad)
            );
CREATE TABLE gedaechtnis_ausbeute(  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,  turn_id TEXT, rolle TEXT, bahn TEXT, modell TEXT,  genommen INTEGER NOT NULL, verworfen INTEGER NOT NULL, gruende TEXT);
CREATE TABLE grabstein (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        was TEXT NOT NULL,
        ziel_id TEXT NOT NULL,
        autor TEXT,
        zeit TEXT NOT NULL,
        grund TEXT,
        inhalt_hash TEXT NOT NULL
    );
CREATE TABLE graph_edges(edge_id TEXT PRIMARY KEY,src TEXT NOT NULL,dst TEXT NOT NULL,kind TEXT NOT NULL,provenance TEXT NOT NULL);
CREATE TABLE graph_kante(
            source_node_id TEXT NOT NULL,
            target_node_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL NOT NULL DEFAULT 1.0,
            confidence REAL,
            graph_epoch INTEGER NOT NULL,
            source_kante_art TEXT NOT NULL,
            beleg TEXT,
            built_at TEXT NOT NULL, verfallen INTEGER, protected INTEGER,
            PRIMARY KEY(source_node_id, target_node_id, edge_type)
        ) WITHOUT ROWID;
CREATE TABLE graph_knoten(
            node_id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            external_id TEXT NOT NULL,
            titel TEXT,
            quelle TEXT,
            source_content_hash TEXT,
            datum TEXT,
            metadaten TEXT,
            graph_epoch INTEGER NOT NULL,
            built_at TEXT NOT NULL
        , status TEXT, verfallen INTEGER, protected INTEGER);
CREATE TABLE graph_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
CREATE TABLE graph_nodes(node_id TEXT PRIMARY KEY,kind TEXT NOT NULL,label TEXT NOT NULL,source_table TEXT NOT NULL,source_id TEXT NOT NULL);
CREATE TABLE kante (
            von TEXT NOT NULL,
            nach TEXT NOT NULL,
            art TEXT NOT NULL,    -- which source field produced this edge
            beleg TEXT, konfidenz REAL, erzeugt_am TEXT, zeitquelle TEXT, verfallen INTEGER DEFAULT 0, protected INTEGER DEFAULT 0,           -- provenance: quelle path of the asserting article
            PRIMARY KEY (von, nach, art)
        );
CREATE TABLE kb_auftrag (
            id               INTEGER PRIMARY KEY AUTOINCREMENT,
            prozess           TEXT NOT NULL,
            nutzlast          TEXT NOT NULL,
            zustand           TEXT NOT NULL DEFAULT 'offen'
                              CHECK (zustand IN ('offen','laeuft','fertig','unbedienbar')),
            versuche          INTEGER NOT NULL DEFAULT 0,
            letzter_grund     TEXT,
            gesperrte_bahnen  TEXT,
            angelegt          TEXT NOT NULL,
            geaendert         TEXT NOT NULL,
            -- unbedienbar OHNE Grund ist verboten: sonst weiss niemand mehr,
            -- warum etwas liegen blieb, und der Auftrag ist faktisch verloren.
            CHECK (zustand <> 'unbedienbar'
                   OR (letzter_grund IS NOT NULL AND TRIM(letzter_grund) <> ''))
        );
CREATE TABLE kb_buchung (
            id                    INTEGER PRIMARY KEY AUTOINCREMENT,
            zeit                   TEXT NOT NULL,
            konto                   TEXT NOT NULL REFERENCES kb_konto(konto),
            zugang                   TEXT NOT NULL REFERENCES kb_zugang(zugang),
            menge                    REAL NOT NULL CHECK (menge >= 0),
            einheit                  TEXT,
            zweck                    TEXT,
            batch_id                 TEXT,
            taetigkeit_id             INTEGER,
            schluessel_hinweis        TEXT,
            quelle                   TEXT NOT NULL DEFAULT 'buchen'
                                     CHECK (quelle IN ('buchen','synthetic')),
            roh_hash                 TEXT UNIQUE
        );
CREATE TABLE kb_konto (
            konto                 TEXT PRIMARY KEY,
            anzeige                TEXT NOT NULL,
            vorrang                 INTEGER NOT NULL,
            hat_eigenes_limit        INTEGER NOT NULL DEFAULT 0
                                     CHECK (hat_eigenes_limit IN (0,1)),
            eigenes_limit_wert       REAL,
            eigenes_limit_einheit    TEXT,
            eigenes_limit_fenster    TEXT,
            warnung_an              TEXT NOT NULL,
            wirt                    TEXT,
            angelegt                TEXT NOT NULL
        );
CREATE TABLE kb_verdrahtung (
            prozess         TEXT PRIMARY KEY,
            bahn_erst       TEXT,
            bahn_zweit      TEXT,
            bahn_dritt      TEXT,
            hoechstanteil   REAL NOT NULL
                            CHECK (hoechstanteil > 0.0 AND hoechstanteil <= 1.0),
            begruendung     TEXT NOT NULL CHECK (LENGTH(TRIM(begruendung)) > 0),
            max_je_lauf     INTEGER,
            schema_pflicht  INTEGER,
            angelegt        TEXT NOT NULL
        );
CREATE TABLE kb_warnung (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            zeit                TEXT NOT NULL,
            konto                TEXT,
            zugang                TEXT,
            art                  TEXT NOT NULL CHECK (art IN (
                                 'ueber_norm', 'reset_naehert_sich',
                                 'verbrauch_ohne_fortschritt',
                                 'mehrdeutiger_schluessel',
                                 'kein_limit_kein_muster')),
            text                 TEXT NOT NULL,
            kennzahlen_json       TEXT
        );
CREATE TABLE kb_zugang (
            zugang                    TEXT PRIMARY KEY,
            anzeige                    TEXT NOT NULL,
            einheit                    TEXT,
            fenster_dauer_sekunden      INTEGER,
            fenster_limit                REAL,
            woche_limit                  REAL,
            tag_limit                    REAL,
            minute_limit                 REAL,
            tageswechsel_stunde          INTEGER,
            spitzenzeit_json             TEXT,
            geteilt_mit                  TEXT,
            besonderheit                TEXT NOT NULL,
            mehrdeutiger_schluessel      INTEGER NOT NULL DEFAULT 0
                                         CHECK (mehrdeutiger_schluessel IN (0,1)),
            angelegt                    TEXT NOT NULL
        , modell TEXT, token_minute_limit REAL, token_tag_limit REAL, zustand TEXT NOT NULL DEFAULT 'ungeprueft', zustand_grund TEXT, zustand_gemessen TEXT, grenzen_quelle TEXT, unbekannt_felder TEXT, unbekannt_grund TEXT, kann_embedding INTEGER, kann_schema INTEGER, kann_batch INTEGER, ausgereizt INTEGER NOT NULL DEFAULT 0, konten_anzahl INTEGER, konten_getrennt INTEGER, schluessel_namen TEXT);
CREATE TABLE kommentar (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artikel_id TEXT NOT NULL,
        text TEXT NOT NULL,
        autor TEXT,
        zeit TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'offen'
            CHECK (status IN ('offen','beantwortet','gestuetzt','widerlegt','unentscheidbar')),
        antwort_folgerung_id INTEGER REFERENCES folgerung(id)
    );
CREATE TABLE kuration (
            artikel_id           TEXT PRIMARY KEY,
            quelle                TEXT,
            ereignis              TEXT,
            klasse                TEXT NOT NULL,
            alt_hash              TEXT,
            neu_hash              TEXT,
            alt_groesse           INTEGER,
            alt_zeilen            INTEGER,
            neu_groesse           INTEGER,
            neu_zeilen            INTEGER,
            erkannt_am            TEXT NOT NULL,
            zuletzt_geprueft_am   TEXT NOT NULL,
            noetig                TEXT NOT NULL,
            status                TEXT NOT NULL DEFAULT 'offen'
        );
CREATE TABLE leases(resource TEXT PRIMARY KEY,holder TEXT NOT NULL,generation INTEGER NOT NULL,expires_at REAL NOT NULL,nonce TEXT NOT NULL);
CREATE TABLE memory_tabelle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    artikel_id TEXT NOT NULL,
                    memory_text TEXT NOT NULL,
                    quelle TEXT,
                    erstellt_am TEXT NOT NULL DEFAULT (datetime('now')),
                    priority REAL DEFAULT 1.0,
                    tag TEXT
                , user_id TEXT);
CREATE TABLE messung(
            id TEXT PRIMARY KEY,
            bauteil TEXT NOT NULL,
            quelle TEXT NOT NULL,
            zeile_hash TEXT NOT NULL,
            was TEXT NOT NULL,
            wert REAL NOT NULL,
            einheit TEXT NOT NULL,
            zeit TEXT NOT NULL,
            wirt TEXT,
            instanz TEXT,
            roh TEXT NOT NULL
        );
CREATE TABLE messung_meta(
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE mv_eval_runs (
    run_id TEXT PRIMARY KEY,
    iteration INTEGER NOT NULL,
    prompt_version TEXT NOT NULL,
    eval_set_size INTEGER NOT NULL,
    pass_rate REAL NOT NULL,
    avg_faithfulness REAL NOT NULL,
    avg_readability REAL NOT NULL,
    fabrication_count INTEGER NOT NULL,
    notes TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE mv_prestage_state (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL UNIQUE,
    value_json TEXT NOT NULL,
    updated_at REAL NOT NULL
);
CREATE TABLE mv_prestage_turns (
    prestage_id TEXT PRIMARY KEY,
    turn_id TEXT,
    session_id TEXT,
    user_id TEXT,
    raw_prompt TEXT NOT NULL,
    world_digest TEXT,
    connected_systems_json TEXT,
    caveman_prompt TEXT NOT NULL,
    tool_selection_json TEXT,
    memory_artefacts_json TEXT,
    outsourced_json TEXT,
    user_intent TEXT,
    watch_out TEXT,
    hypotheses_json TEXT,
    counter_hypotheses_json TEXT,
    prestage_model TEXT,
    prestage_receipt_json TEXT,
    created_at REAL NOT NULL
);
CREATE TABLE mv_translation_log (
    translation_id TEXT PRIMARY KEY,
    turn_id TEXT,
    prestage_id TEXT,
    caveman_original TEXT NOT NULL,
    german_translation TEXT NOT NULL,
    translator_model TEXT,
    translator_receipt_json TEXT,
    faithfulness_score REAL,
    readability_score REAL,
    judge_model TEXT,
    judge_verdict_json TEXT,
    fabrication_flag INTEGER NOT NULL DEFAULT 0,
    created_at REAL NOT NULL
);
CREATE TABLE mv_uebersetzung_ausfall(  id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL,  turn_id TEXT, session_id TEXT, fehler TEXT);
CREATE TABLE problem (
            id TEXT PRIMARY KEY,
            bauteil TEXT,
            quelle TEXT NOT NULL,
            zeile_hash TEXT NOT NULL,
            text TEXT NOT NULL,
            art TEXT NOT NULL CHECK (art IN ('problem','huerde','risiko','offene_frage')),
            erkannt_am TEXT,
            status TEXT NOT NULL DEFAULT 'offen' CHECK (status IN ('offen','geloest')),
            geloest_am TEXT,
            geloest_durch TEXT
        );
CREATE TABLE pu_lage (
        schluessel TEXT PRIMARY KEY, wert TEXT NOT NULL, zeit TEXT NOT NULL
    );
CREATE TABLE pu_takt (
        folge INTEGER PRIMARY KEY,
        clay_id TEXT NOT NULL,
        zeit TEXT NOT NULL,
        monoton REAL NOT NULL,
        boot_id TEXT NOT NULL,
        art TEXT NOT NULL,
        delta INTEGER NOT NULL DEFAULT 0,
        kosten_us REAL,
        modellaufrufe INTEGER NOT NULL DEFAULT 0,
        werkzeugaufrufe INTEGER NOT NULL DEFAULT 0,
        detail TEXT
    );
CREATE TABLE retrieval_entrypoint_policy(entry_key TEXT PRIMARY KEY,capital REAL NOT NULL DEFAULT 0.0,reward_ema REAL NOT NULL DEFAULT 0.0,pulls INTEGER NOT NULL DEFAULT 0,updated_at REAL NOT NULL);
CREATE TABLE retrieval_episodes(retrieval_id TEXT PRIMARY KEY,turn_id TEXT NOT NULL UNIQUE REFERENCES turns(turn_id),episode_id TEXT NOT NULL UNIQUE REFERENCES workspace_episodes(episode_id),causal_id TEXT NOT NULL UNIQUE,session_id TEXT NOT NULL REFERENCES sessions(session_id),user_id TEXT NOT NULL REFERENCES users(user_id),generation INTEGER NOT NULL,policy_version INTEGER NOT NULL,mode TEXT NOT NULL CHECK(mode IN ('SHADOW','ACTIVE')),query_hash TEXT NOT NULL,query_token_hashes TEXT NOT NULL,selected_memory_ids TEXT NOT NULL,shadow_memory_ids TEXT NOT NULL,entry_keys TEXT NOT NULL,budget_chars INTEGER NOT NULL,chars_selected INTEGER NOT NULL,status TEXT NOT NULL CHECK(status IN ('PRESENT','UNKNOWN')),ts REAL NOT NULL);
CREATE TABLE retrieval_feedback(receipt_id TEXT PRIMARY KEY,retrieval_id TEXT NOT NULL REFERENCES retrieval_episodes(retrieval_id) ON DELETE CASCADE,causal_id TEXT NOT NULL,generation INTEGER NOT NULL,credit REAL NOT NULL,signal_class TEXT NOT NULL,ts REAL NOT NULL);
CREATE TABLE retrieval_policy_state(singleton INTEGER PRIMARY KEY CHECK(singleton=1),mode TEXT NOT NULL CHECK(mode IN ('SHADOW','ACTIVE')),policy_version INTEGER NOT NULL,updated_at REAL NOT NULL);
CREATE TABLE schluessel_lage (
        schluessel      TEXT PRIMARY KEY,
        zuletzt_geprueft TEXT,
        http            INTEGER,
        ms              REAL,
        einordnung      TEXT,      -- MECHANISCH, nur hier steht die Wahrheit
        seit            TEXT,      -- wann dieser Zustand begann
        fehlertext      TEXT,
        modell_meinung  TEXT,      -- VORSCHLAG eines Modells, keine Tatsache
        geprueft_gesamt INTEGER DEFAULT 0,
        gesund_gesamt   INTEGER DEFAULT 0
    , sonde TEXT, rest_kontingent TEXT);
CREATE TABLE schluessel_lauf (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit TEXT NOT NULL, schluessel TEXT NOT NULL,
        http INTEGER, ms REAL, einordnung TEXT, fehlertext TEXT
    , sonde TEXT, rest_kontingent TEXT);
CREATE TABLE sessions(session_id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(user_id),created_at REAL NOT NULL,updated_at REAL NOT NULL,generation INTEGER NOT NULL DEFAULT 1,terminal_name TEXT NOT NULL UNIQUE);
CREATE TABLE speicher_rueckweg(pfad TEXT PRIMARY KEY, erfasst REAL NOT NULL, warum TEXT, modelle INTEGER, verzeichnis TEXT NOT NULL);
CREATE TABLE speicherwacht_log(id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, belegt_prozent REAL, frei_gb REAL, stufe TEXT, gehandelt INTEGER NOT NULL, befreit_gb REAL, bericht TEXT, df_gb REAL, gezaehlt_gb REAL, luecke_gb REAL, nicht_zaehlbar TEXT, bilanz_urteil TEXT);
CREATE TABLE taetigkeit (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    wirt TEXT,
    instanz TEXT,
    sitzung TEXT,
    zeit TEXT,
    werkzeug TEXT,
    ziel_pfad TEXT,
    aktion TEXT,
    ergebnis TEXT,
    quelle TEXT,
    zeile_nr INTEGER,
    roh_hash TEXT UNIQUE
);
CREATE TABLE taetigkeit_kante (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    taetigkeit_id INTEGER NOT NULL,
    artikel_id TEXT NOT NULL,
    art TEXT NOT NULL,
    beleg TEXT,
    UNIQUE(taetigkeit_id, artikel_id, art)
);
CREATE TABLE turn_compressions(
    compression_id TEXT PRIMARY KEY,
    turn_id TEXT NOT NULL REFERENCES turns(turn_id),
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    level INTEGER NOT NULL,
    level_name TEXT NOT NULL,
    content TEXT NOT NULL,
    source_sha256 TEXT NOT NULL,
    derived_from_turn_ids TEXT NOT NULL,
    extractor TEXT NOT NULL,
    prompt_version TEXT,
    created_at REAL NOT NULL,
    UNIQUE(turn_id, level)
);
CREATE TABLE turns(turn_id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(session_id),user_id TEXT NOT NULL REFERENCES users(user_id),ordinal INTEGER NOT NULL,ts REAL NOT NULL,role TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),content TEXT NOT NULL,fidelity TEXT NOT NULL DEFAULT 'full',compression_generation INTEGER NOT NULL DEFAULT 0,resource_refs TEXT NOT NULL DEFAULT '[]',causal_refs TEXT NOT NULL DEFAULT '[]',provenance TEXT NOT NULL DEFAULT '{}',UNIQUE(session_id, ordinal));
CREATE TABLE udb_nvidia_embedding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            artikel_id TEXT NOT NULL UNIQUE,
            modell TEXT NOT NULL,
            dim INTEGER NOT NULL,
            embedding_json TEXT NOT NULL,
            erstellt_am TEXT NOT NULL DEFAULT (datetime('now'))
        );
CREATE TABLE users(user_id TEXT PRIMARY KEY,display_name TEXT NOT NULL,rights TEXT NOT NULL DEFAULT 'equal',clerk_subject TEXT UNIQUE);
CREATE TABLE vd_aufnahme (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit          TEXT NOT NULL,
        strom         TEXT NOT NULL,
        neu           INTEGER NOT NULL,
        geaendert     INTEGER NOT NULL,
        offen_gesamt  INTEGER NOT NULL,
        schwelle      INTEGER NOT NULL,
        ausgeloest    INTEGER NOT NULL
    );
CREATE TABLE vd_gesehen (
        strom            TEXT NOT NULL,
        quell_id         TEXT NOT NULL,
        zeit             TEXT NOT NULL,
        anreicherung_id  INTEGER,
        PRIMARY KEY (strom, quell_id)
    );
CREATE TABLE vd_grenze (
        zugang            TEXT PRIMARY KEY,
        anzahl_429        INTEGER NOT NULL DEFAULT 0,
        erste_429         TEXT,
        letzte_429        TEXT,
        letzte_wartezeit  REAL,
        rufe_ohne_429     INTEGER NOT NULL DEFAULT 0,
        bemerkung         TEXT
    );
CREATE TABLE vd_lauf (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit             TEXT NOT NULL,
        strom            TEXT NOT NULL,
        quellen          INTEGER NOT NULL,
        bahn             TEXT,
        modell           TEXT,
        http             INTEGER,
        dauer_ms         REAL,
        token_ein        INTEGER,
        token_aus        INTEGER,
        ergebnis         TEXT NOT NULL,
        grund            TEXT,
        detail           TEXT,
        anreicherung_id  INTEGER,
        verdichtung_id   TEXT
    );
CREATE TABLE vd_strom (
        strom            TEXT PRIMARY KEY,
        schwelle         INTEGER NOT NULL,
        rate_je_stunde   REAL,
        rate_beleg       TEXT,
        aktiv            INTEGER NOT NULL DEFAULT 1,
        angelegt         TEXT NOT NULL,
        letzte_pruefung  TEXT,
        letzter_lauf     TEXT
    , portion INTEGER);
CREATE TABLE vp_alias (
      alias_id INTEGER PRIMARY KEY AUTOINCREMENT,
      target_kind TEXT, target_id TEXT, alias_norm TEXT,
      alias_class TEXT, confidence REAL, source_epoch INTEGER
    );
CREATE TABLE vp_alias_df (
  wort TEXT PRIMARY KEY,
  df INTEGER NOT NULL,          -- in wie vielen Aliassen kommt das Wort vor
  gebaut_am TEXT
);
CREATE VIRTUAL TABLE vp_alias_fts USING fts5(alias_norm, content='vp_alias', content_rowid='alias_id');
CREATE TABLE vp_alias_meta (key TEXT PRIMARY KEY, value TEXT);
CREATE VIRTUAL TABLE vp_datei_fts USING fts5(titel, datei_id UNINDEXED);
CREATE VIRTUAL TABLE vp_dir_fts USING fts5(verzeichnisname, datei_id UNINDEXED);
CREATE TABLE vp_edge_lern (
      query_class TEXT, edge_art TEXT,
      gewicht REAL DEFAULT 0, beobachtungen INTEGER DEFAULT 0,
      zuletzt_gelernt TEXT, gesehen INTEGER DEFAULT 0, genutzt INTEGER DEFAULT 0,
      PRIMARY KEY(query_class, edge_art)
    );
CREATE TABLE vp_edge_lern_backup_preflift(
  query_class TEXT,
  edge_art TEXT,
  gewicht REAL,
  beobachtungen INT,
  zuletzt_gelernt TEXT
);
CREATE TABLE vp_ereignis (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      zeit TEXT, art TEXT, detail TEXT
    );
CREATE TABLE vp_erfolgsmarke (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL, frage TEXT, region TEXT, anker TEXT,
  getragen INTEGER,              -- 1 = der Eintritt hat zur Antwort gefuehrt
  quelle TEXT                    -- wer die Marke gesetzt hat
);
CREATE TABLE vp_gesehen (
      lauf TEXT, record_id TEXT, zeit TEXT
    );
CREATE TABLE vp_karte_region (
  version INTEGER NOT NULL, region TEXT NOT NULL,
  projekt TEXT, art TEXT, artikel_n INTEGER,
  landmarken TEXT,               -- JSON: die am staerksten vernetzten Artikel
  PRIMARY KEY(version, region)
);
CREATE TABLE vp_karte_version (
  version INTEGER PRIMARY KEY AUTOINCREMENT,
  gebaut_am TEXT NOT NULL,
  anlass TEXT,
  regionen INTEGER, landmarken INTEGER, wegweiser INTEGER,
  korpus_artikel INTEGER, korpus_kanten INTEGER,
  verhaeltnis REAL,              -- Kartenzeilen / Korpuszeilen. Muss klein bleiben.
  erkundungsanteil REAL DEFAULT 0.0,   -- 0.0 = Gegenmittel gegen das Echo NICHT aktiv
  dauer_s REAL
);
CREATE TABLE vp_karte_wegweiser (
  version INTEGER NOT NULL, wort TEXT NOT NULL, region TEXT NOT NULL,
  staerke REAL NOT NULL,         -- Lift: wie stark zeigt dieses Wort auf die Region
  PRIMARY KEY(version, wort, region)
);
CREATE TABLE vp_lese_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      zeit TEXT, ort_id TEXT, paket_id TEXT, bytes INTEGER, erlaubt INTEGER, grund TEXT
    );
CREATE TABLE vp_paket_log (
      paket_id TEXT PRIMARY KEY, zeit TEXT, epoch_sekunden INTEGER,
      frage TEXT, orte_json TEXT
    );
CREATE TABLE vp_plan_cache (
      sig_hash TEXT PRIMARY KEY,
      source_epoch INTEGER, graph_epoch INTEGER,
      anchor_ids TEXT, gap_terms TEXT,
      plan_json TEXT,
      erzeugt_am TEXT, treffer_anzahl INTEGER DEFAULT 0, zuletzt_getroffen TEXT
    );
CREATE TABLE vp_sitzung (
      id TEXT PRIMARY KEY,
      rechner TEXT NOT NULL,
      rolle TEXT NOT NULL,           -- z.B. 'clayverse' / 'gabriel' / 'andreas'
      gestartet REAL NOT NULL,
      lebenszeichen REAL NOT NULL
    );
CREATE TABLE vp_snapshot (
      snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
      erzeugt_am TEXT, state_hash TEXT,
      normals_score TEXT, normals_bestanden INTEGER,
      beobachtungen_gesamt INTEGER, edge_lern_snapshot TEXT
    , source_epoch INTEGER, graph_epoch INTEGER);
CREATE TABLE vp_weg (
  von TEXT NOT NULL,
  nach TEXT NOT NULL,
  art TEXT,                          -- Kantenart, aus der der Weg entstand
  nutzung INTEGER NOT NULL DEFAULT 0,
  getragen INTEGER NOT NULL DEFAULT 0,
  guete REAL NOT NULL DEFAULT 0.0,   -- 0 = langsame Strasse, 1 = Autobahn
  sitzungen TEXT,                    -- verschiedene Sitzungen, die ihn trugen (JSON-Liste)
  tunnel INTEGER NOT NULL DEFAULT 0,
  erste_nutzung REAL NOT NULL,
  letzte_nutzung REAL NOT NULL,
  PRIMARY KEY(von, nach)
);
CREATE TABLE wa_ereignis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit TEXT, art TEXT, ziel TEXT, detail TEXT, quelle TEXT
    );
CREATE TABLE wa_grenze (
        id INTEGER PRIMARY KEY AUTOINCREMENT, zeit TEXT, detail TEXT
    );
CREATE TABLE wa_snapshot (
        ziel TEXT PRIMARY KEY,
        zeit TEXT, rchar INTEGER, wchar INTEGER, cpu_ticks INTEGER,
        active_enter TEXT, active_state TEXT
    );
CREATE TABLE weg(
            id TEXT PRIMARY KEY,
            ursprung TEXT NOT NULL,
            ziel_wirt TEXT NOT NULL,
            ziel_dienst TEXT,
            ziel_pfad TEXT,
            transport TEXT NOT NULL,
            proxyjump_via TEXT,
            konto TEXT,
            befehl TEXT NOT NULL,
            tor TEXT NOT NULL,
            darf TEXT NOT NULL,
            schritte TEXT,
            erreichbar INTEGER NOT NULL,
            fehler TEXT,
            zuletzt_bewiesen TEXT NOT NULL,
            beleg TEXT NOT NULL
        );
CREATE TABLE wk_aufgabe (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        art           TEXT NOT NULL,
        artikel_id    TEXT NOT NULL,
        wert          REAL NOT NULL DEFAULT 0,
        zustand       TEXT NOT NULL DEFAULT 'offen'
                      CHECK (zustand IN ('offen','laeuft','fertig','verworfen','unbedienbar')),
        versuche      INTEGER NOT NULL DEFAULT 0,
        letzter_grund TEXT,
        angelegt      TEXT NOT NULL,
        geaendert     TEXT NOT NULL,
        UNIQUE (art, artikel_id)
    );
CREATE TABLE wm_cast_regel (
        von_domaene  TEXT NOT NULL,
        nach_domaene TEXT NOT NULL,
        erlaubt      INTEGER NOT NULL,
        bedingung    TEXT,
        beleg        TEXT NOT NULL,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1,
        erzeugt_am   TEXT NOT NULL,
        PRIMARY KEY (von_domaene, nach_domaene)
    );
CREATE TABLE wm_guss_log (
        id           INTEGER PRIMARY KEY AUTOINCREMENT,
        zeit         TEXT NOT NULL,
        von_domaene  TEXT NOT NULL,
        nach_domaene TEXT NOT NULL,
        ergebnis     TEXT NOT NULL,
        grund        TEXT NOT NULL,
        bedingung    TEXT,
        beleg        TEXT,
        gegenstand   TEXT,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1
    );
CREATE TABLE wm_lesart (
        lesart_id    TEXT PRIMARY KEY,
        artikel_id   TEXT NOT NULL,
        achse        TEXT NOT NULL,
        wert         TEXT,
        kontext_json TEXT NOT NULL DEFAULT '{}',
        domaene      TEXT NOT NULL DEFAULT 'FACT_EXACT',
        basis_json   TEXT NOT NULL,
        quelle       TEXT NOT NULL,
        konfidenz    REAL,
        erzeugt_am   TEXT NOT NULL,
        gueltig_von  TEXT NOT NULL,
        gueltig_bis  TEXT,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1,
        offen_grund  TEXT
    );
CREATE TABLE wm_topologie (
        von          TEXT NOT NULL,
        nach         TEXT NOT NULL,
        topologie    TEXT NOT NULL,
        herkunft_art TEXT NOT NULL DEFAULT '',
        gewicht      REAL NOT NULL DEFAULT 1.0,
        basis_json   TEXT NOT NULL,
        quelle       TEXT,
        erzeugt_am   TEXT NOT NULL,
        gueltig_von  TEXT NOT NULL,
        gueltig_bis  TEXT,
        kandidat     TEXT NOT NULL,
        offen        INTEGER NOT NULL DEFAULT 1,
        offen_grund  TEXT,
        PRIMARY KEY (von, nach, topologie, herkunft_art)
    );
CREATE TABLE wm_topologie_name (
        topologie  TEXT PRIMARY KEY,
        h_nummer   TEXT NOT NULL,
        bedeutung  TEXT NOT NULL,
        kandidat   TEXT NOT NULL,
        offen      INTEGER NOT NULL DEFAULT 1
    );
CREATE TABLE workspace_episodes(episode_id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES sessions(session_id),ts REAL NOT NULL,observation_turn_id TEXT REFERENCES turns(turn_id),salience REAL NOT NULL,alternatives TEXT NOT NULL,selected TEXT,state TEXT NOT NULL);
CREATE TABLE zero_raum (
  session_id TEXT PRIMARY KEY,          -- eine Zeile je Sitzung, wird ueberschrieben
  mensch     TEXT NOT NULL,             -- gabriel | andreas
  platz      INTEGER NOT NULL,
  was        TEXT NOT NULL,             -- Caveman: was ich gerade tue
  womit      TEXT,                      -- die angefasste Sache: Datei, Tabelle, Dienst
  zustand    TEXT NOT NULL,             -- arbeitet | wartet | frei
  seit       REAL NOT NULL
);
CREATE TABLE zero_raum_ruf (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts REAL NOT NULL,
  von TEXT NOT NULL,
  text TEXT NOT NULL
);
CREATE INDEX idx_arbeitspaket_stand ON entityos_arbeitspaket(stand, erstellt);
CREATE INDEX idx_artikel_art ON artikel(art);
CREATE INDEX idx_artikel_baunotiz_lookup ON artikel(art, von_quelle, datum);
CREATE INDEX idx_artikel_epistemic_class ON artikel(epistemic_class);
CREATE INDEX idx_artikel_logical_id ON artikel(logical_id);
CREATE INDEX idx_artikel_projekt ON artikel(projekt);
CREATE INDEX idx_artikel_quelle ON artikel(quelle);
CREATE INDEX idx_artikel_sphaere ON artikel(sphaere);
CREATE INDEX idx_artikel_status ON artikel(status);
CREATE INDEX idx_artikel_verdichtung_lookup ON artikel(art, von_quelle, datum);
CREATE INDEX idx_asuchtext_blase ON artikel_suchtext(blase);
CREATE INDEX idx_bahn_lauf_art_zeit ON bahn_lauf(art, zeit);
CREATE INDEX idx_bearbeitung_artikel ON bearbeitung(artikel_id);
CREATE INDEX idx_erfolgsmarke_region ON vp_erfolgsmarke(region, ts);
CREATE INDEX idx_fehler_art ON fehler(art);
CREATE INDEX idx_fehler_schwere ON fehler(schwere);
CREATE INDEX idx_folgerung_beleg_fid ON folgerung_beleg(folgerung_id);
CREATE INDEX idx_folgerung_gilt_fuer ON folgerung(gilt_fuer);
CREATE INDEX idx_fundort_blase ON fundort(blase);
CREATE INDEX idx_fundort_datei ON fundort(datei_id);
CREATE INDEX idx_fundort_pruefsumme ON fundort(pruefsumme);
CREATE INDEX idx_grabstein_ziel ON grabstein(was, ziel_id);
CREATE INDEX idx_graph_kante_source_epoch
            ON graph_kante(source_node_id, graph_epoch DESC, weight DESC);
CREATE INDEX idx_graph_kante_target_epoch
            ON graph_kante(target_node_id, graph_epoch DESC, weight DESC);
CREATE INDEX idx_graph_knoten_external
            ON graph_knoten(external_id);
CREATE INDEX idx_graph_knoten_type
            ON graph_knoten(node_type);
CREATE INDEX idx_kante_nach ON kante(nach);
CREATE INDEX idx_kante_von ON kante(von);
CREATE INDEX idx_karte_wegweiser_wort ON vp_karte_wegweiser(wort);
CREATE INDEX idx_kommentar_artikel ON kommentar(artikel_id);
CREATE INDEX idx_kommentar_status ON kommentar(status);
CREATE INDEX idx_memory_artikel ON memory_tabelle(artikel_id);
CREATE INDEX idx_memory_tag ON memory_tabelle(tag);
CREATE INDEX idx_memory_user ON memory_tabelle(user_id);
CREATE INDEX idx_messung_bauteil ON messung(bauteil);
CREATE INDEX idx_messung_einheit ON messung(einheit);
CREATE INDEX idx_messung_zeile ON messung(zeile_hash);
CREATE INDEX idx_problem_bauteil ON problem(bauteil);
CREATE INDEX idx_problem_status ON problem(status);
CREATE INDEX idx_problem_zeile_hash ON problem(zeile_hash);
CREATE INDEX idx_retrieval_session_ts ON retrieval_episodes(session_id,ts DESC);
CREATE INDEX idx_taetigkeit_sitzung ON taetigkeit(sitzung);
CREATE INDEX idx_taetigkeit_ziel_pfad ON taetigkeit(ziel_pfad);
CREATE INDEX idx_turn_compressions_turn ON turn_compressions(turn_id, level);
CREATE INDEX idx_turns_session_ord ON turns(session_id, ordinal DESC);
CREATE INDEX idx_vd_aufnahme_strom ON vd_aufnahme(strom, zeit);
CREATE INDEX idx_vd_lauf_strom ON vd_lauf(strom, zeit);
CREATE INDEX idx_vp_alias_df_df ON vp_alias_df(df);
CREATE INDEX idx_vp_weg_guete ON vp_weg(guete DESC);
CREATE INDEX idx_weg_ursprung_ziel ON weg(ursprung, ziel_wirt);
CREATE INDEX idx_weg_ziel ON weg(ziel_wirt);
CREATE INDEX idx_wk_aufgabe_art ON wk_aufgabe(art, zustand);
CREATE INDEX idx_wk_aufgabe_wahl ON wk_aufgabe(zustand, wert DESC);
CREATE INDEX ix_kuration_status_noetig ON kuration(status, noetig);
CREATE INDEX ix_schluessel_lauf_zeit ON schluessel_lauf(zeit);
CREATE INDEX ix_taetigkeit_zeit ON taetigkeit(zeit);
CREATE INDEX kb_auftrag_zustand
            ON kb_auftrag(zustand, prozess);
CREATE INDEX kb_buchung_batch
            ON kb_buchung(batch_id);
CREATE INDEX kb_buchung_kz_zeit
            ON kb_buchung(konto, zugang, zeit);
CREATE INDEX kb_warnung_zeit ON kb_warnung(zeit);
CREATE INDEX mv_prestage_turns_session_idx
    ON mv_prestage_turns(session_id, created_at);
CREATE INDEX wm_guss_log_ix1 ON wm_guss_log(ergebnis, zeit);
CREATE INDEX wm_lesart_ix1 ON wm_lesart(artikel_id, gueltig_bis);
CREATE INDEX wm_lesart_ix2 ON wm_lesart(artikel_id, achse, gueltig_bis);
CREATE INDEX wm_lesart_ix3 ON wm_lesart(achse, gueltig_bis);
CREATE INDEX wm_topologie_ix1 ON wm_topologie(von, topologie, gueltig_bis);
CREATE INDEX wm_topologie_ix2 ON wm_topologie(topologie);
CREATE INDEX wm_topologie_ix3 ON wm_topologie(nach, topologie, gueltig_bis);
CREATE VIEW kondensat AS
SELECT
    'messung'        AS kind,
    json_extract(metadaten, '$.bauteil') AS bauteil,
    NULL             AS gilt_fuer,
    NULL             AS folgerung_id,
    id               AS ref_id,
    titel            AS label,
    datum            AS zeit
FROM artikel
WHERE art = 'vorfall'

UNION ALL

SELECT
    'problem_offen'  AS kind,
    bauteil          AS bauteil,
    NULL             AS gilt_fuer,
    NULL             AS folgerung_id,
    id               AS ref_id,
    substr(text, 1, 120) AS label,
    erkannt_am       AS zeit
FROM problem
WHERE status = 'offen'

UNION ALL

SELECT
    'folgerung'      AS kind,
    NULL             AS bauteil,
    gilt_fuer        AS gilt_fuer,
    id               AS folgerung_id,
    CAST(id AS TEXT) AS ref_id,
    substr(aussage, 1, 120) || ' [' || status || ']' AS label,
    zeit             AS zeit
FROM folgerung

UNION ALL

SELECT
    'beleg'          AS kind,
    NULL             AS bauteil,
    f.gilt_fuer      AS gilt_fuer,
    fb.folgerung_id  AS folgerung_id,
    fb.beleg_art || ':' || fb.beleg_id AS ref_id,
    fb.beleg_art     AS label,
    NULL             AS zeit
FROM folgerung_beleg fb
JOIN folgerung f ON f.id = fb.folgerung_id;
CREATE VIEW messung_kompakt AS
        SELECT
            bauteil AS bauteil,
            was     AS was,
            wert    AS wert,
            einheit AS einheit,
            zeit    AS zeit,
            quelle  AS quelle
        FROM messung
        ORDER BY zeit DESC, bauteil;
COMMIT;
