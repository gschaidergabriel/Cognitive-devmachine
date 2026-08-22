static void cmd_preset(const char*dbpath,const char*file){char*text=read_file(file,MAX_TEXT);if(!text)die("PRESET_READ");json_object*j=parse_json(text);if(!j)die("PRESET_JSON");const char*pid0=jstr(j,"profile_id",NULL);if(!pid0||!*pid0)die("PRESET_PROFILE_ID");char*pid=xstrdup(pid0);char hash[65];sha_hex(text,strlen(text),hash);sqlite3*db=open_db(dbpath);init_entity(db);char now[32];utc_now(now);sqlite3_stmt*s=NULL;sqlite3_prepare_v2(db,"BEGIN IMMEDIATE",-1,&s,NULL);sqlite3_step(s);sqlite3_finalize(s);sqlite3_prepare_v2(db,"INSERT INTO profiles(profile_id,profile_json,profile_sha256,updated_at) VALUES(?,?,?,?) ON CONFLICT(profile_id) DO UPDATE SET profile_json=excluded.profile_json,profile_sha256=excluded.profile_sha256,updated_at=excluded.updated_at",-1,&s,NULL);sqlite3_bind_text(s,1,pid,-1,SQLITE_TRANSIENT);sqlite3_bind_text(s,2,text,-1,SQLITE_TRANSIENT);sqlite3_bind_text(s,3,hash,-1,SQLITE_TRANSIENT);sqlite3_bind_text(s,4,now,-1,SQLITE_TRANSIENT);if(sqlite3_step(s)!=SQLITE_DONE)die_sql(db,"PRESET_INSERT");sqlite3_finalize(s);sqlite3_prepare_v2(db,"UPDATE entity_state SET active_profile=?,updated_at=? WHERE id=1",-1,&s,NULL);sqlite3_bind_text(s,1,pid,-1,SQLITE_TRANSIENT);sqlite3_bind_text(s,2,now,-1,SQLITE_TRANSIENT);sqlite3_step(s);sqlite3_finalize(s);sql_exec(db,"COMMIT");sqlite3_close(db);json_object_put(j);free(text);printf("{\"ok\":true,\"profile_id\":\"%s\",\"profile_sha256\":\"%s\"}\n",pid,hash);free(pid);}
static void cmd_state_box(const char*dbpath,const char*file){char*text=read_file(file,MAX_TEXT);if(!text)die("STATE_BOX_READ");json_object*sj=parse_json(text);if(!sj){free(text);die("STATE_BOX_JSON");}json_object_put(sj);sqlite3*db=open_db(dbpath);init_entity(db);set_config(db,"state_box_json",text);sqlite3_close(db);free(text);printf("{\"ok\":true}\n");}
static void cmd_set_local_model(const char*dbpath,const char*path){if(access(path,R_OK))die("MODEL_NOT_READABLE");sqlite3*db=open_db(dbpath);init_entity(db);set_config(db,"local_model_path",path);sqlite3_close(db);printf("{\"ok\":true}\n");}
static void cmd_set_runner(const char*dbpath,const char*json){json_object*a=parse_json(json);if(!a||json_object_get_type(a)!=json_type_array)die("RUNNER_JSON");json_object_put(a);sqlite3*db=open_db(dbpath);init_entity(db);set_config(db,"local_argv_json",json);sqlite3_close(db);printf("{\"ok\":true}\n");}
static void cmd_status(const char*dbpath){sqlite3*db=open_db(dbpath);init_entity(db);long long g=get_generation(db);char*pid=NULL,*profile=active_profile_json(db,&pid);char*lm=get_config(db,"local_model_path");printf("{\"ok\":true,\"version\":\"%s\",\"generation\":%lld,\"active_profile\":%s,\"local_model_configured\":%s,\"profile_present\":%s}\n",MINI_VERSION,g,pid?"\"configured\"":"null",lm?"true":"false",profile?"true":"false");free(pid);free(profile);free(lm);sqlite3_close(db);}
static int contains_secret(const char*out,const char*secret){return secret&&*secret&&out&&strstr(out,secret)!=NULL;}

static void cmd_run(const char*dbpath,const char*source_path,const char*secret_file){
    sqlite3*db=open_db(dbpath);init_entity(db);
    long long observed=get_generation(db);
    char*pid=NULL,*profile_text=active_profile_json(db,&pid);
    if(!profile_text){sqlite3_close(db);die("NO_ACTIVE_PROFILE");}
    json_object*profile=parse_json(profile_text);
    if(!profile){free(profile_text);free(pid);sqlite3_close(db);die("PROFILE_JSON_INVALID");}

    packet_t packet=collect_packet(source_path);
    if(!packet.sensor_ok){json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);packet_free(&packet);die("SOURCE_SENSOR_UNKNOWN");}
    if(packet.n==0){
        json_object*r=json_object_new_object();
        json_object_object_add(r,"ok",json_object_new_boolean(1));
        json_object_object_add(r,"quiet",json_object_new_boolean(1));
        json_object_object_add(r,"generation",json_object_new_int64(observed));
        json_object_object_add(r,"source_count",json_object_new_int64(0));
        json_object_object_add(r,"sensor_health",json_object_new_string("VERIFIED"));
        json_object_object_add(r,"profile_id",json_object_new_string(pid?pid:""));
        puts(json_object_to_json_string_ext(r,JSON_C_TO_STRING_PLAIN));
        json_object_put(r);packet_free(&packet);json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);return;
    }

    char*pjson=packet_json(&packet);
    gate_context_t gctx;
    if(!gate_context_build(profile,&packet,observed,pid,&gctx)){free(pjson);packet_free(&packet);json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);die("CANONICAL_COMPILE_FAILED_NO_COMMIT");}
    char*sys=system_prompt(profile),*user=build_guarded_user_prompt(profile,observed,&packet,pjson,&gctx);
    char*backend=NULL,*model=NULL,*secret=NULL;
    char*out=model_output(profile,db,sys,user,secret_file,&backend,&model,&secret);
    if(!out){free(sys);free(user);free(pjson);gate_context_free(&gctx);packet_free(&packet);json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);free(backend);free(model);free(secret);die("INFERENCE_FAILED_NO_COMMIT");}
    if(contains_secret(out,secret)){free(out);free(sys);free(user);free(pjson);gate_context_free(&gctx);packet_free(&packet);json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);free(backend);free(model);free(secret);die("SECRET_LEAK_REJECTED_NO_COMMIT");}

    char gate_err[160]={0};
    if(!gate_output(profile,&gctx,out,secret,gate_err,sizeof gate_err)){
        free(out);free(sys);free(user);free(pjson);gate_context_free(&gctx);packet_free(&packet);json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);free(backend);free(model);free(secret);
        fprintf(stderr,"ERROR:GATE_REJECTED_NO_COMMIT:%s\n",gate_err[0]?gate_err:"UNKNOWN_GATE_FAILURE");
        exit(2);
    }

    char*box=NULL,study_hash[65];
    char*study=build_study(db,profile,pid,backend,model,observed+1,packet.n,1,out,&box,study_hash);
    long long ng=0,oid=0;
    int committed=commit_run(db,source_path,&packet,observed,pid,gctx.packet_hash,gctx.canonical_state_hash,out,study,study_hash,box,&ng,&oid);
    if(!committed){free(out);free(sys);free(user);free(pjson);gate_context_free(&gctx);packet_free(&packet);json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);free(backend);free(model);free(secret);free(box);free(study);die("STALE_GENERATION_OR_EVENT_CAS_NO_COMMIT");}

    json_object*r=json_object_new_object();
    json_object_object_add(r,"ok",json_object_new_boolean(1));
    json_object_object_add(r,"quiet",json_object_new_boolean(0));
    json_object_object_add(r,"output_id",json_object_new_int64(oid));
    json_object_object_add(r,"generation",json_object_new_int64(ng));
    json_object_object_add(r,"source_count",json_object_new_int64((int64_t)packet.n));
    json_object_object_add(r,"sensor_health",json_object_new_string("VERIFIED"));
    json_object_object_add(r,"profile_id",json_object_new_string(pid?pid:""));
    json_object_object_add(r,"inference_kind",json_object_new_string(backend?backend:""));
    json_object_object_add(r,"model_label",json_object_new_string(model?model:""));
    json_object_object_add(r,"canonical_state_hash",json_object_new_string(gctx.canonical_state_hash));
    json_object_object_add(r,"packet_hash",json_object_new_string(gctx.packet_hash));
    json_object_object_add(r,"study_payload_hash",json_object_new_string(study_hash));
    json_object_object_add(r,"state_box",json_object_new_string(box?box:""));
    puts(json_object_to_json_string_ext(r,JSON_C_TO_STRING_PLAIN));
    json_object_put(r);
    free(out);free(sys);free(user);free(pjson);gate_context_free(&gctx);packet_free(&packet);json_object_put(profile);free(profile_text);free(pid);sqlite3_close(db);free(backend);free(model);free(secret);free(box);free(study);
}

static void usage(void){fprintf(stderr,"usage: mini_entity.clay --version | init DB | source-init DB | source-add DB KIND SOURCE_ID PAYLOAD_JSON | preset-apply DB PRESET.json | state-box-apply DB CONFIG.json | set-local-model DB FILE | set-local-runner-json DB JSON_ARRAY | status DB | run ENTITY_DB SOURCE_DB [SECRET_FILE]\n");exit(2);} 
int main(int argc,char**argv){if(argc==2&&!strcmp(argv[1],"--version")){puts(MINI_VERSION);return 0;}if(argc<3)usage();curl_global_init(CURL_GLOBAL_DEFAULT);if(!strcmp(argv[1],"init")&&argc==3)cmd_init(argv[2]);else if(!strcmp(argv[1],"source-init")&&argc==3)cmd_source_init(argv[2]);else if(!strcmp(argv[1],"source-add")&&argc==6)cmd_source_add(argv[2],argv[3],argv[4],argv[5]);else if(!strcmp(argv[1],"preset-apply")&&argc==4)cmd_preset(argv[2],argv[3]);else if(!strcmp(argv[1],"state-box-apply")&&argc==4)cmd_state_box(argv[2],argv[3]);else if(!strcmp(argv[1],"set-local-model")&&argc==4)cmd_set_local_model(argv[2],argv[3]);else if(!strcmp(argv[1],"set-local-runner-json")&&argc==4)cmd_set_runner(argv[2],argv[3]);else if(!strcmp(argv[1],"status")&&argc==3)cmd_status(argv[2]);else if(!strcmp(argv[1],"run")&&(argc==4||argc==5))cmd_run(argv[2],argv[3],argc==5?argv[4]:"");else usage();curl_global_cleanup();return 0;}
