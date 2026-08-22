#include <regex.h>

/*
 * Native 0.7 immutable compile/gate layer.
 *
 * Application names and semantics remain profile data. The native executable only owns
 * invariants: profile integrity, explicit UNKNOWN handling, bounded compiled evidence,
 * hash binding, output-contract validation, claim/evidence checks and leak rejection.
 *
 * The native event source does not pretend to have source-specific sensor/probe health
 * which it has not measured. Missing context therefore resolves conservatively and can
 * make a configured metric UNKNOWN; it never manufactures VERIFIED state.
 */

static int key_eq_ci(const char *a,const char *b){
    if(!a||!b)return 0;
    while(*a&&*b){char x=*a++,y=*b++;if(x>='A'&&x<='Z')x=(char)(x-'A'+'a');if(y>='A'&&y<='Z')y=(char)(y-'A'+'a');if(x!=y)return 0;}
    return *a==0&&*b==0;
}

static int json_contains_forbidden_secret_value(json_object *v){
    if(!v)return 0;
    if(json_object_get_type(v)==json_type_object){
        json_object_object_foreach(v,k,child){
            if((key_eq_ci(k,"api_token")||key_eq_ci(k,"token_value")||key_eq_ci(k,"secret_value")||key_eq_ci(k,"password")) &&
               child && json_object_get_type(child)!=json_type_null){
                if(json_object_get_type(child)!=json_type_string || *json_object_get_string(child))return 1;
            }
            if(json_contains_forbidden_secret_value(child))return 1;
        }
    }else if(json_object_get_type(v)==json_type_array){
        for(size_t i=0;i<json_object_array_length(v);i++)if(json_contains_forbidden_secret_value(json_object_array_get_idx(v,(int)i)))return 1;
    }
    return 0;
}

static int profile_contract_valid(json_object *p){
    if(!p||json_object_get_type(p)!=json_type_object)return 0;
    if(strcmp(jstr(p,"schema",""),"clay-pipeline-profile/v2"))return 0;
    if(!*jstr(p,"profile_id",""))return 0;
    json_object *inf=jget(p,"inference"),*personality=jget(p,"personality");
    if(!inf||json_object_get_type(inf)!=json_type_object)return 0;
    if(!personality||json_object_get_type(personality)!=json_type_object)return 0;
    json_object *oc=jget(personality,"output_contract");
    if(!oc||json_object_get_type(oc)!=json_type_object)return 0;
    if(json_contains_forbidden_secret_value(p))return 0;
    return 1;
}

static json_object *parse_json_profile_guarded(const char *s){
    json_object *o=parse_json(s);
    if(o&&!profile_contract_valid(o)){json_object_put(o);return NULL;}
    return o;
}

static char *active_profile_json_checked(sqlite3 *db,char **profile_id_out){
    char *pid=NULL,*raw=active_profile_json(db,&pid);
    if(!raw){if(profile_id_out)*profile_id_out=pid;else free(pid);return NULL;}
    sqlite3_stmt *s=NULL;
    if(sqlite3_prepare_v2(db,"SELECT profile_sha256 FROM profiles WHERE profile_id=?",-1,&s,NULL)!=SQLITE_OK){free(raw);free(pid);die_sql(db,"PROFILE_HASH_PREP");}
    sqlite3_bind_text(s,1,pid,-1,SQLITE_TRANSIENT);
    const char *stored=NULL;char *copy=NULL;
    if(sqlite3_step(s)==SQLITE_ROW){stored=(const char*)sqlite3_column_text(s,0);if(stored)copy=xstrdup(stored);}
    sqlite3_finalize(s);
    char actual[65];sha_hex(raw,strlen(raw),actual);
    if(!copy||strcmp(copy,actual)){free(copy);free(raw);free(pid);die("PROFILE_HASH_MISMATCH");}
    free(copy);
    json_object *checked=parse_json_profile_guarded(raw);
    if(!checked){free(raw);free(pid);die("PROFILE_CONTRACT_REJECTED");}
    json_object_put(checked);
    if(profile_id_out)*profile_id_out=pid;else free(pid);
    return raw;
}

static int gate_bool(json_object *gate,const char *name,int def){
    json_object *v=gate?jget(gate,name):NULL;
    if(!v)return def;
    if(json_object_get_type(v)!=json_type_boolean)return def;
    return json_object_get_boolean(v);
}

static json_object *context_ref(json_object *root,const char *path){
    if(!root||!path||!*path)return NULL;
    char *tmp=xstrdup(path),*save=NULL,*tok=strtok_r(tmp,".",&save);json_object *cur=root;
    while(tok&&cur){cur=jget(cur,tok);tok=strtok_r(NULL,".",&save);}
    free(tmp);return cur;
}

static double expr_num(json_object *expr,json_object *ctx,int *known);
static int expr_bool(json_object *expr,json_object *ctx,int *known);

static double expr_num(json_object *expr,json_object *ctx,int *known){
    if(!expr){*known=1;return 0.0;}
    enum json_type t=json_object_get_type(expr);
    if(t==json_type_int||t==json_type_double){*known=1;return json_object_get_double(expr);}
    if(t==json_type_boolean){*known=1;return json_object_get_boolean(expr)?1.0:0.0;}
    if(t!=json_type_object){*known=0;return 0.0;}
    json_object *ref=jget(expr,"ref");
    if(ref&&json_object_get_type(ref)==json_type_string){
        json_object *v=context_ref(ctx,json_object_get_string(ref));
        if(!v){*known=0;return 0.0;}
        enum json_type vt=json_object_get_type(v);
        if(vt==json_type_int||vt==json_type_double){*known=1;return json_object_get_double(v);}
        if(vt==json_type_boolean){*known=1;return json_object_get_boolean(v)?1.0:0.0;}
        *known=0;return 0.0;
    }
    json_object *cw=jget(expr,"count_where");
    if(cw&&json_object_get_type(cw)==json_type_object){
        const char *rp=jstr(cw,"ref",NULL),*field=jstr(cw,"field",NULL);json_object *rows=rp?context_ref(ctx,rp):NULL;
        if(!rows||json_object_get_type(rows)!=json_type_array||!field){*known=0;return 0.0;}
        json_object *in=jget(cw,"in"),*notin=jget(cw,"not_in");double n=0;
        for(size_t i=0;i<json_object_array_length(rows);i++){
            json_object *row=json_object_array_get_idx(rows,(int)i),*rv=row?jget(row,field):NULL;int match=1;
            if(in&&json_object_get_type(in)==json_type_array){match=0;for(size_t q=0;q<json_object_array_length(in);q++)if(json_object_equal(rv,json_object_array_get_idx(in,(int)q))){match=1;break;}}
            if(notin&&json_object_get_type(notin)==json_type_array){match=1;for(size_t q=0;q<json_object_array_length(notin);q++)if(json_object_equal(rv,json_object_array_get_idx(notin,(int)q))){match=0;break;}}
            if(match)n+=1.0;
        }
        *known=1;return n;
    }
    json_object *sw=jget(expr,"sum_where");
    if(sw&&json_object_get_type(sw)==json_type_object){
        const char *rp=jstr(sw,"ref",NULL),*vf=jstr(sw,"value_field",NULL);json_object *rows=rp?context_ref(ctx,rp):NULL,*where=jget(sw,"where");
        if(!rows||json_object_get_type(rows)!=json_type_array||!vf||!where||json_object_get_type(where)!=json_type_object){*known=0;return 0.0;}
        const char *wf=jstr(where,"field",NULL);json_object *want=jget(where,"eq");if(!wf){*known=0;return 0.0;}double sum=0;
        for(size_t i=0;i<json_object_array_length(rows);i++){json_object *row=json_object_array_get_idx(rows,(int)i),*got=row?jget(row,wf):NULL,*vv=row?jget(row,vf):NULL;if(json_object_equal(got,want)&&vv&&(json_object_get_type(vv)==json_type_int||json_object_get_type(vv)==json_type_double))sum+=json_object_get_double(vv);}
        *known=1;return sum;
    }
    const char *op=jstr(expr,"op",NULL);if(!op){*known=0;return 0.0;}
    if(!strcmp(op,"add")){json_object *a=jget(expr,"args");if(!a||json_object_get_type(a)!=json_type_array){*known=0;return 0.0;}double sum=0;for(size_t i=0;i<json_object_array_length(a);i++){int k=0;double v=expr_num(json_object_array_get_idx(a,(int)i),ctx,&k);if(!k){*known=0;return 0.0;}sum+=v;}*known=1;return sum;}
    if(!strcmp(op,"div")){int ka=0,kb=0;double a=expr_num(jget(expr,"a"),ctx,&ka),b=expr_num(jget(expr,"b"),ctx,&kb);if(!ka||!kb){*known=0;return 0.0;}*known=1;return b==0.0?0.0:a/b;}
    if(!strcmp(op,"clamp01")){int k=0;double v=expr_num(jget(expr,"arg"),ctx,&k);if(!k){*known=0;return 0.0;}if(v<0)v=0;if(v>1)v=1;*known=1;return v;}
    if(!strcmp(op,"if")){int kc=0,c=expr_bool(jget(expr,"cond"),ctx,&kc);if(!kc){*known=0;return 0.0;}return expr_num(jget(expr,c?"then":"else"),ctx,known);}
    if(!strcmp(op,"eq")||!strcmp(op,"not")||!strcmp(op,"and")||!strcmp(op,"or")){int k=0,v=expr_bool(expr,ctx,&k);*known=k;return v?1.0:0.0;}
    *known=0;return 0.0;
}

static int expr_bool(json_object *expr,json_object *ctx,int *known){
    if(!expr){*known=1;return 0;}
    enum json_type t=json_object_get_type(expr);
    if(t==json_type_boolean){*known=1;return json_object_get_boolean(expr);}
    if(t==json_type_int||t==json_type_double){*known=1;return json_object_get_double(expr)!=0.0;}
    if(t!=json_type_object){*known=0;return 0;}
    json_object *ref=jget(expr,"ref");
    if(ref&&json_object_get_type(ref)==json_type_string){json_object *v=context_ref(ctx,json_object_get_string(ref));if(!v){*known=1;return 0;}enum json_type vt=json_object_get_type(v);if(vt==json_type_boolean){*known=1;return json_object_get_boolean(v);}if(vt==json_type_int||vt==json_type_double){*known=1;return json_object_get_double(v)!=0.0;}if(vt==json_type_null){*known=1;return 0;}*known=1;return 1;}
    const char *op=jstr(expr,"op",NULL);if(!op){int k=0;double v=expr_num(expr,ctx,&k);*known=k;return v!=0.0;}
    if(!strcmp(op,"not")){int k=0,v=expr_bool(jget(expr,"arg"),ctx,&k);*known=k;return k?!v:0;}
    if(!strcmp(op,"and")||!strcmp(op,"or")){json_object *a=jget(expr,"args");if(!a||json_object_get_type(a)!=json_type_array){*known=0;return 0;}int is_and=!strcmp(op,"and");for(size_t i=0;i<json_object_array_length(a);i++){int k=0,v=expr_bool(json_object_array_get_idx(a,(int)i),ctx,&k);if(!k){*known=0;return 0;}if(is_and&&!v){*known=1;return 0;}if(!is_and&&v){*known=1;return 1;}}*known=1;return is_and?1:0;}
    if(!strcmp(op,"eq")){json_object *a=jget(expr,"a"),*b=jget(expr,"b");if(!a||!b){*known=0;return 0;}json_object *ra=a,*rb=b;json_object *ar=jget(a,"ref"),*br=jget(b,"ref");if(ar&&json_object_get_type(ar)==json_type_string)ra=context_ref(ctx,json_object_get_string(ar));if(br&&json_object_get_type(br)==json_type_string)rb=context_ref(ctx,json_object_get_string(br));if(!ra||!rb){*known=1;return ra==rb;}if((json_object_get_type(ra)==json_type_int||json_object_get_type(ra)==json_type_double||json_object_get_type(ra)==json_type_boolean)&&(json_object_get_type(rb)==json_type_int||json_object_get_type(rb)==json_type_double||json_object_get_type(rb)==json_type_boolean)){*known=1;return json_object_get_double(ra)==json_object_get_double(rb);}*known=1;return json_object_equal(ra,rb);}
    int k=0;double v=expr_num(expr,ctx,&k);*known=k;return v!=0.0;
}

static json_object *native_compile_context(const packet_t *p){
    json_object *ctx=json_object_new_object(),*derived=json_object_new_object(),*sources=json_object_new_object(),*sensors=json_object_new_object(),*probes=json_object_new_object();
    json_object_object_add(derived,"source_count",json_object_new_int64((int64_t)p->n));
    json_object_object_add(derived,"quiet_sensors_ok",json_object_new_boolean(p->sensor_ok));
    for(size_t i=0;i<p->n;i++){
        json_object *bucket=jget(sources,p->v[i].kind),*rows=NULL;
        if(!bucket){bucket=json_object_new_object();rows=json_object_new_array();json_object_object_add(bucket,"rows",rows);json_object_object_add(sources,p->v[i].kind,bucket);}else rows=jget(bucket,"rows");
        json_object *row=parse_json(p->v[i].payload);if(!row||json_object_get_type(row)!=json_type_object){if(row)json_object_put(row);row=json_object_new_object();json_object_object_add(row,"value",json_object_new_string(p->v[i].payload));}
        if(!jget(row,"source_id"))json_object_object_add(row,"source_id",json_object_new_string(p->v[i].id));
        json_object_array_add(rows,row);
    }
    /* No source-specific sensor/probe health is invented by the generic event adapter. */
    json_object_object_add(ctx,"derived",derived);json_object_object_add(ctx,"sources",sources);json_object_object_add(ctx,"sensors",sensors);json_object_object_add(ctx,"probes",probes);return ctx;
}

static json_object *native_personality_state(json_object *profile,const packet_t *p){
    json_object *out=json_object_new_object(),*specs=jget(profile,"state_metrics"),*ctx=native_compile_context(p);
    if(specs&&json_object_get_type(specs)==json_type_array)for(size_t i=0;i<json_object_array_length(specs);i++){
        json_object *spec=json_object_array_get_idx(specs,(int)i);if(!spec||json_object_get_type(spec)!=json_type_object)continue;const char *name=jstr(spec,"name",NULL);if(!name||!*name)continue;
        const char *explicit_status=jstr(spec,"status",NULL),*status="UNKNOWN";int value_known=0;double value=expr_num(jget(spec,"value"),ctx,&value_known);
        if(explicit_status){if(!strcmp(explicit_status,"VERIFIED")&&value_known)status="VERIFIED";else status=explicit_status;}
        else{int uk=0;int unknown=expr_bool(jget(spec,"unknown_if"),ctx,&uk);if(uk&&!unknown&&value_known)status="VERIFIED";}
        json_object *m=json_object_new_object();json_object_object_add(m,"status",json_object_new_string(status));json_object_object_add(m,"value",json_object_new_double(value_known?value:0.0));
        const char *eref=jstr(spec,"evidence_ref",NULL);char generated[512];if(!eref){snprintf(generated,sizeof generated,"state:%s",name);eref=generated;}json_object_object_add(m,"evidence_ref",json_object_new_string(eref));json_object_object_add(out,name,m);
    }
    json_object_put(ctx);return out;
}

static json_object *native_allowed_evidence(json_object *profile,const packet_t *p,json_object *metrics){
    (void)profile;json_object *a=json_object_new_array();
    for(size_t i=0;i<p->n;i++)json_object_array_add(a,json_object_new_string(p->v[i].id));
    if(metrics&&json_object_get_type(metrics)==json_type_object){json_object_object_foreach(metrics,mname,m){(void)mname;const char *r=jstr(m,"evidence_ref",NULL);if(r)json_object_array_add(a,json_object_new_string(r));}}
    if(p->n==0&&p->sensor_ok)json_object_array_add(a,json_object_new_string("quiet:verified"));
    return a;
}

static json_object *native_canonical_state(json_object *profile,const packet_t *p){
    json_object *root=json_object_new_object(),*health=json_object_new_object(),*event_sensor=json_object_new_object(),*probes=json_object_new_object();
    json_object_object_add(event_sensor,"ok",json_object_new_boolean(p->sensor_ok));json_object_object_add(health,"mini_entity_events",event_sensor);
    json_object_object_add(root,"sources_health",health);json_object_object_add(root,"probes",probes);
    json_object *notes=jget(profile,"profile_notes");if(notes)json_object_object_add(root,"profile_notes",json_object_get(notes));else json_object_object_add(root,"profile_notes",json_object_new_object());
    json_object_object_add(root,"epistemic_rule",json_object_new_string("UNKNOWN != ZERO != ERROR != MEASURED"));return root;
}

static char *packet_json_canonical(const packet_t *p){
    json_object *root=json_object_new_object(),*sources=json_object_new_object(),*events=json_object_new_object(),*rows=json_object_new_array();
    for(size_t i=0;i<p->n;i++){json_object *e=json_object_new_object();json_object_object_add(e,"source_id",json_object_new_string(p->v[i].id));json_object_object_add(e,"kind",json_object_new_string(p->v[i].kind));json_object *payload=parse_json(p->v[i].payload);if(payload)json_object_object_add(e,"payload",payload);else json_object_object_add(e,"payload",json_object_new_string(p->v[i].payload));json_object_array_add(rows,e);}
    json_object_object_add(events,"ok",json_object_new_boolean(p->sensor_ok));json_object_object_add(events,"rows",rows);json_object_object_add(events,"evidence_prefix",json_object_new_string(""));json_object_object_add(sources,"events",events);
    json_object_object_add(root,"sources",sources);json_object_object_add(root,"source_count",json_object_new_int64((int64_t)p->n));json_object_object_add(root,"quiet_sensors_ok",json_object_new_boolean(p->sensor_ok));
    char *out=xstrdup(json_object_to_json_string_ext(root,JSON_C_TO_STRING_PLAIN));json_object_put(root);return out;
}

static void packet_hash_canonical(const packet_t *p,char out[65]){char *raw=packet_json_canonical(p);sha_hex(raw,strlen(raw),out);free(raw);}

static int json_array_has_string(json_object *a,const char *s){if(!a||json_object_get_type(a)!=json_type_array||!s)return 0;for(size_t i=0;i<json_object_array_length(a);i++){json_object *v=json_object_array_get_idx(a,(int)i);if(v&&json_object_get_type(v)==json_type_string&&!strcmp(json_object_get_string(v),s))return 1;}return 0;}

static int mapped_field_present(json_object *root,json_object *oc,const char *mapping_key){json_object *m=jget(oc,mapping_key);if(!m)return 1;if(json_object_get_type(m)!=json_type_string||!*json_object_get_string(m))return 0;return jget(root,json_object_get_string(m))!=NULL;}

static int regex_matches_anywhere(json_object *v,regex_t *rx,size_t nrx){
    if(!v)return 0;
    if(json_object_get_type(v)==json_type_object){json_object_object_foreach(v,k,child){(void)k;if(regex_matches_anywhere(child,rx,nrx))return 1;}}
    else if(json_object_get_type(v)==json_type_array){for(size_t i=0;i<json_object_array_length(v);i++)if(regex_matches_anywhere(json_object_array_get_idx(v,(int)i),rx,nrx))return 1;}
    else if(json_object_get_type(v)==json_type_string){const char *s=json_object_get_string(v);for(size_t i=0;i<nrx;i++)if(regexec(&rx[i],s,0,NULL,0)==0)return 1;}
    return 0;
}

static int output_contract_valid(json_object *profile,const char *raw,const char *expected_packet_hash,const char *expected_state_hash,const char *allowed_json,const char *metrics_json){
    json_object *root=parse_json(raw),*allowed=parse_json(allowed_json),*metrics=parse_json(metrics_json);if(!root||json_object_get_type(root)!=json_type_object||!allowed||json_object_get_type(allowed)!=json_type_array||!metrics||json_object_get_type(metrics)!=json_type_object){if(root)json_object_put(root);if(allowed)json_object_put(allowed);if(metrics)json_object_put(metrics);return 0;}
    json_object *personality=jget(profile,"personality"),*oc=personality?jget(personality,"output_contract"):NULL,*gate=jget(profile,"gate");
    if(!oc||json_object_get_type(oc)!=json_type_object){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
    const char *core[]={"title_field","intro_field","sections_field","continuity_field","autobiographical_hypotheses_field"};for(size_t i=0;i<sizeof(core)/sizeof(core[0]);i++)if(!mapped_field_present(root,oc,core[i])){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
    if(gate_bool(gate,"require_hash_echo",1)){
        json_object *ph=jget(root,"packet_hash_seen"),*sh=jget(root,"canonical_state_hash_seen");if(!ph||!sh||json_object_get_type(ph)!=json_type_string||json_object_get_type(sh)!=json_type_string||strcmp(json_object_get_string(ph),expected_packet_hash)||strcmp(json_object_get_string(sh),expected_state_hash)){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
    }
    json_object *sf=jget(oc,"sections_field");
    if(sf&&json_object_get_type(sf)==json_type_string){
        json_object *sections=jget(root,json_object_get_string(sf));if(!sections||json_object_get_type(sections)!=json_type_array){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
        const char *text_name=jstr(oc,"section_text_field",NULL),*evidence_name=jstr(oc,"section_evidence_field",NULL),*claims_name=jstr(oc,"section_claims_field",NULL);double overshoot=gate?jdbl(gate,"max_claim_overshoot",0.0):0.0;
        for(size_t i=0;i<json_object_array_length(sections);i++){
            json_object *sec=json_object_array_get_idx(sections,(int)i);if(!sec||json_object_get_type(sec)!=json_type_object){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
            if(text_name&&!jget(sec,text_name)){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
            json_object *refs=evidence_name?jget(sec,evidence_name):NULL;if(gate_bool(gate,"require_evidence_per_section",1)&&(!refs||json_object_get_type(refs)!=json_type_array||json_object_array_length(refs)==0)){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
            if(refs){if(json_object_get_type(refs)!=json_type_array){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}for(size_t r=0;r<json_object_array_length(refs);r++){json_object *rv=json_object_array_get_idx(refs,(int)r);if(!rv||json_object_get_type(rv)!=json_type_string||!json_array_has_string(allowed,json_object_get_string(rv))){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}}}
            json_object *claims=claims_name?jget(sec,claims_name):NULL;if(claims){if(json_object_get_type(claims)!=json_type_object){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}json_object_object_foreach(claims,cname,strength){json_object *metric=jget(metrics,cname);if(!metric||strcmp(jstr(metric,"status","UNKNOWN"),"VERIFIED")||!strength||(json_object_get_type(strength)!=json_type_int&&json_object_get_type(strength)!=json_type_double)){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}double claimed=json_object_get_double(strength),measured=jdbl(metric,"value",0.0);if(claimed>measured+overshoot){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}const char *metric_ref=jstr(metric,"evidence_ref",NULL);if(metric_ref&&!json_array_has_string(refs,metric_ref)){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}}}
        }
    }
    json_object *patterns=gate?jget(gate,"leak_patterns"):NULL;
    if(patterns&&json_object_get_type(patterns)==json_type_array){
        size_t cap=json_object_array_length(patterns),n=0;regex_t *rx=cap?xmalloc(sizeof(regex_t)*cap):NULL;int bad_rx=0;
        for(size_t i=0;i<cap;i++){json_object *pat=json_object_array_get_idx(patterns,(int)i);if(!pat||json_object_get_type(pat)!=json_type_string||regcomp(&rx[n],json_object_get_string(pat),REG_EXTENDED|REG_ICASE|REG_NOSUB)!=0){bad_rx=1;break;}n++;}
        int leak=!bad_rx&&regex_matches_anywhere(root,rx,n);for(size_t i=0;i<n;i++)regfree(&rx[i]);free(rx);if(bad_rx||leak){json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 0;}
    }
    json_object_put(root);json_object_put(allowed);json_object_put(metrics);return 1;
}

static char *build_user_prompt_checked(json_object *profile,long long generation,const packet_t *p,const char *packet_json_text){
    char *base=build_user_prompt(profile,generation,p,packet_json_text),ph[65],state_hash[65];packet_hash_canonical(p,ph);
    json_object *canonical=native_canonical_state(profile,p),*metrics=native_personality_state(profile,p),*allowed=native_allowed_evidence(profile,p,metrics);const char *canonical_raw=json_object_to_json_string_ext(canonical,JSON_C_TO_STRING_PLAIN);sha_hex(canonical_raw,strlen(canonical_raw),state_hash);
    json_object *personality=jget(profile,"personality"),*oc=personality?jget(personality,"output_contract"):NULL,*gate=jget(profile,"gate");buf_t b;buf_init(&b);buf_add(&b,base);free(base);
    buf_printf(&b,"packet_hash_expected=%s\ncanonical_state_hash_expected=%s\n",ph,state_hash);buf_printf(&b,"canonical_state_json=%s\n",canonical_raw);buf_printf(&b,"personality_state_json=%s\n",json_object_to_json_string_ext(metrics,JSON_C_TO_STRING_PLAIN));buf_printf(&b,"allowed_evidence_refs_json=%s\n",json_object_to_json_string_ext(allowed,JSON_C_TO_STRING_PLAIN));
    if(oc)buf_printf(&b,"output_contract_json=%s\n",json_object_to_json_string_ext(oc,JSON_C_TO_STRING_PLAIN));if(gate)buf_printf(&b,"output_gate_json=%s\n",json_object_to_json_string_ext(gate,JSON_C_TO_STRING_PLAIN));if(gate_bool(gate,"require_hash_echo",1))buf_add(&b,"Include exact top-level packet_hash_seen and canonical_state_hash_seen fields matching the expected hashes.\n");
    json_object_put(canonical);json_object_put(metrics);json_object_put(allowed);return buf_take(&b);
}

static int extract_hash_line(const char *text,const char *prefix,char out[65]){const char *p=strstr(text,prefix);if(!p)return 0;p+=strlen(prefix);size_t n=0;while(p[n]&&p[n]!='\n'&&n<64)n++;if(n!=64)return 0;memcpy(out,p,64);out[64]=0;return 1;}
static char *extract_text_line(const char *text,const char *prefix){const char *p=strstr(text,prefix);if(!p)return NULL;p+=strlen(prefix);const char *e=strchr(p,'\n');size_t n=e?(size_t)(e-p):strlen(p);char *out=xmalloc(n+1);memcpy(out,p,n);out[n]=0;return out;}

static char *model_output_gated(json_object *profile,sqlite3 *edb,const char *system,const char *user,const char *secret_file,char **backend_out,char **model_out,char **secret_out){
    char *out=model_output(profile,edb,system,user,secret_file,backend_out,model_out,secret_out);if(!out)return NULL;char ph[65],sh[65];char *allowed=extract_text_line(user,"allowed_evidence_refs_json="),*metrics=extract_text_line(user,"personality_state_json=");
    if(!extract_hash_line(user,"packet_hash_expected=",ph)||!extract_hash_line(user,"canonical_state_hash_expected=",sh)||!allowed||!metrics){free(out);free(allowed);free(metrics);die("OUTPUT_GATE_CONTEXT_MISSING_NO_COMMIT");}
    if(secret_out&&*secret_out&&**secret_out&&strstr(out,*secret_out)){free(out);free(allowed);free(metrics);die("OUTPUT_SECRET_LEAK_NO_COMMIT");}
    if(!output_contract_valid(profile,out,ph,sh,allowed,metrics)){free(out);free(allowed);free(metrics);die("OUTPUT_CONTRACT_GATE_REJECTED_NO_COMMIT");}free(allowed);free(metrics);return out;
}

/* Redirect only later native call sites (part04) through the canonicalized compile/gate wrappers. */
#define active_profile_json active_profile_json_checked
#define packet_json packet_json_canonical
#define packet_hash packet_hash_canonical
#define build_user_prompt build_user_prompt_checked
#define model_output model_output_gated
