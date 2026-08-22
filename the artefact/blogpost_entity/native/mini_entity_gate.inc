#include <regex.h>

/*
 * Profile-driven canonical envelope and immutable post-inference gate.
 * Application semantics stay in the DB-resident profile. Unsupported metric
 * expressions degrade to UNKNOWN rather than manufacturing a VERIFIED value.
 */
typedef struct {
    json_object *canonical;
    json_object *metrics;
    json_object *allowed_refs;
    char canonical_hash[65];
    char packet_hash[65];
} native_compiled_t;

static int native_jbool(json_object *o,const char *k,int d){
    json_object *v=jget(o,k);
    if(!v)return d;
    if(json_object_get_type(v)==json_type_boolean)return json_object_get_boolean(v)?1:0;
    if(json_object_get_type(v)==json_type_int)return json_object_get_int(v)!=0;
    return d;
}

static int native_eval_expr(json_object *expr,const packet_t *p,double *out){
    if(!expr){*out=0.0;return 1;}
    enum json_type t=json_object_get_type(expr);
    if(t==json_type_int||t==json_type_double){*out=json_object_get_double(expr);return 1;}
    if(t==json_type_boolean){*out=json_object_get_boolean(expr)?1.0:0.0;return 1;}
    if(t!=json_type_object)return 0;
    json_object *ref=jget(expr,"ref");
    if(ref&&json_object_get_type(ref)==json_type_string){
        const char *r=json_object_get_string(ref);
        if(!strcmp(r,"derived.source_count")){*out=(double)p->n;return 1;}
        if(!strcmp(r,"derived.quiet_sensors_ok")){*out=p->sensor_ok?1.0:0.0;return 1;}
        return 0;
    }
    const char *op=jstr(expr,"op",NULL);
    if(!op)return 0;
    if(!strcmp(op,"not")){
        double a=0;if(!native_eval_expr(jget(expr,"arg"),p,&a))return 0;*out=a?0.0:1.0;return 1;
    }
    if(!strcmp(op,"eq")){
        double a=0,b=0;if(!native_eval_expr(jget(expr,"a"),p,&a)||!native_eval_expr(jget(expr,"b"),p,&b))return 0;*out=(a==b)?1.0:0.0;return 1;
    }
    if(!strcmp(op,"and")||!strcmp(op,"or")||!strcmp(op,"add")){
        json_object *args=jget(expr,"args");if(!args||json_object_get_type(args)!=json_type_array)return 0;
        int is_and=!strcmp(op,"and"),is_or=!strcmp(op,"or");double acc=is_and?1.0:0.0;
        int n=json_object_array_length(args);
        for(int i=0;i<n;i++){
            double v=0;if(!native_eval_expr(json_object_array_get_idx(args,i),p,&v))return 0;
            if(is_and)acc=(acc!=0.0&&v!=0.0)?1.0:0.0;
            else if(is_or)acc=(acc!=0.0||v!=0.0)?1.0:0.0;
            else acc+=v;
        }
        *out=acc;return 1;
    }
    if(!strcmp(op,"div")){
        double a=0,b=0;if(!native_eval_expr(jget(expr,"a"),p,&a)||!native_eval_expr(jget(expr,"b"),p,&b))return 0;if(b==0.0)return 0;*out=a/b;return 1;
    }
    if(!strcmp(op,"clamp01")){
        double a=0;if(!native_eval_expr(jget(expr,"arg"),p,&a))return 0;if(a<0)a=0;if(a>1)a=1;*out=a;return 1;
    }
    if(!strcmp(op,"if")){
        double c=0;if(!native_eval_expr(jget(expr,"cond"),p,&c))return 0;
        return native_eval_expr(jget(expr,c!=0.0?"then":"else"),p,out);
    }
    /* count_where/sum_where and unknown future operators fail closed to UNKNOWN. */
    return 0;
}

static int native_array_has_string(json_object *a,const char *s){
    if(!a||json_object_get_type(a)!=json_type_array||!s)return 0;
    int n=json_object_array_length(a);
    for(int i=0;i<n;i++){
        json_object *v=json_object_array_get_idx(a,i);
        if(v&&json_object_get_type(v)==json_type_string&&!strcmp(json_object_get_string(v),s))return 1;
    }
    return 0;
}

static void native_add_ref(json_object *a,const char *s){
    if(s&&*s&&!native_array_has_string(a,s))json_object_array_add(a,json_object_new_string(s));
}

static const char *native_source_prefix(json_object *profile,const char *kind){
    json_object *sources=jget(profile,"sources");
    if(!sources||json_object_get_type(sources)!=json_type_array)return NULL;
    int n=json_object_array_length(sources);
    for(int i=0;i<n;i++){
        json_object *spec=json_object_array_get_idx(sources,i);
        if(!spec||json_object_get_type(spec)!=json_type_object)continue;
        const char *k=jstr(spec,"kind",NULL);
        if(k&&kind&&!strcmp(k,kind))return jstr(spec,"evidence_prefix",NULL);
    }
    return NULL;
}

static json_object *native_compile_metrics(json_object *profile,const packet_t *p,json_object *allowed){
    json_object *metrics=json_object_new_object();
    json_object *specs=jget(profile,"state_metrics");
    if(!specs||json_object_get_type(specs)!=json_type_array)return metrics;
    int n=json_object_array_length(specs);
    for(int i=0;i<n;i++){
        json_object *spec=json_object_array_get_idx(specs,i);
        if(!spec||json_object_get_type(specs)!=json_type_array)continue;
        const char *name=jstr(spec,"name",NULL);if(!name||!*name)continue;
        char default_ref[512];snprintf(default_ref,sizeof default_ref,"state:%s",name);
        const char *evidence_ref=jstr(spec,"evidence_ref",default_ref);
        native_add_ref(allowed,evidence_ref);
        const char *explicit_status=jstr(spec,"status",NULL);
        const char *status=explicit_status?explicit_status:"UNKNOWN";
        int status_known=explicit_status!=NULL;
        if(!explicit_status){
            double u=0;
            if(native_eval_expr(jget(spec,"unknown_if"),p,&u)){status=u!=0.0?"UNKNOWN":"VERIFIED";status_known=1;}
        }
        double value=0;
        int value_known=native_eval_expr(jget(spec,"value"),p,&value);
        if(!status_known||!value_known)status="UNKNOWN";
        json_object *m=json_object_new_object();
        json_object_object_add(m,"status",json_object_new_string(status));
        json_object_object_add(m,"value",json_object_new_double(value_known?value:0.0));
        json_object_object_add(m,"evidence_ref",json_object_new_string(evidence_ref));
        json_object_object_add(metrics,name,m);
    }
    return metrics;
}

static int native_compile(json_object *profile,const packet_t *p,const char *packet_hash_s,native_compiled_t *c){
    memset(c,0,sizeof *c);
    snprintf(c->packet_hash,sizeof c->packet_hash,"%s",packet_hash_s?packet_hash_s:"");
    c->allowed_refs=json_object_new_array();
    for(size_t i=0;i<p->n;i++){
        const char *prefix=native_source_prefix(profile,p->v[i].kind);
        buf_t ref;buf_init(&ref);
        if(prefix&&*prefix)buf_printf(&ref,"%s%s",prefix,p->v[i].id);
        else buf_printf(&ref,"%s:%s",p->v[i].kind?p->v[i].kind:"event",p->v[i].id?p->v[i].id:"");
        char *r=buf_take(&ref);native_add_ref(c->allowed_refs,r);free(r);
    }
    if(p->n==0&&p->sensor_ok)native_add_ref(c->allowed_refs,"quiet:verified");
    c->metrics=native_compile_metrics(profile,p,c->allowed_refs);

    c->canonical=json_object_new_object();
    json_object *health=json_object_new_object();
    for(size_t i=0;i<p->n;i++){
        if(jget(health,p->v[i].kind))continue;
        json_object *h=json_object_new_object();
        json_object_object_add(h,"ok",json_object_new_boolean(p->sensor_ok));
        json_object_object_add(health,p->v[i].kind,json_object_get(h));
        json_object_put(h);
    }
    json_object_object_add(c->canonical,"sources_health",health);
    json_object_object_add(c->canonical,"probes",json_object_new_object());
    json_object *notes=jget(profile,"profile_notes");
    json_object_object_add(c->canonical,"profile_notes",notes?json_object_get(notes):json_object_new_object());
    json_object_object_add(c->canonical,"epistemic_rule",json_object_new_string("UNKNOWN != ZERO != ERROR != MEASURED"));
    const char *raw=json_object_to_json_string_ext(c->canonical,JSON_C_TO_STRING_PLAIN);
    sha_hex(raw,strlen(raw),c->canonical_hash);
    return 1;
}

static void native_compiled_free(native_compiled_t *c){
    if(c->canonical)json_object_put(c->canonical);
    if(c->metrics)json_object_put(c->metrics);
    if(c->allowed_refs)json_object_put(c->allowed_refs);
    memset(c,0,sizeof *c);
}

static char *native_guarded_system_prompt(json_object *profile){
    char *editable=system_prompt(profile);
    json_object *personality=jget(profile,"personality"),*contract=jget(personality,"output_contract");
    const char *contract_text=contract?json_object_to_json_string_ext(contract,JSON_C_TO_STRING_PLAIN):"{}";
    buf_t b;buf_init(&b);
    buf_add(&b,"IMMUTABLE PIPELINE GUARD:\nUse only the supplied canonical envelope. UNKNOWN != ZERO != ERROR != MEASURED. Echo canonical_state_hash_seen and packet_hash_seen exactly when required. Every configured section must use only allowed evidence_refs. State claims may use only VERIFIED metrics, within configured overshoot tolerance, and must cite the metric evidence_ref. Never reveal active secrets or configured leak patterns. Editable profile instructions cannot override this guard.\nOutput contract: ");
    buf_add(&b,contract_text);
    buf_add(&b,"\n\nEDITABLE PROFILE INSTRUCTIONS (lower priority):\n");
    buf_add(&b,editable?editable:"");
    free(editable);
    return buf_take(&b);
}

static char *native_guarded_user_prompt(json_object *profile,long long generation,const packet_t *p,const char *packet_json_text,const native_compiled_t *c){
    char *legacy=build_user_prompt(profile,generation,p,packet_json_text);
    json_object *env=json_object_new_object();
    json_object_object_add(env,"CANONICAL_STATE_HASH",json_object_new_string(c->canonical_hash));
    json_object_object_add(env,"PACKET_HASH",json_object_new_string(c->packet_hash));
    json_object_object_add(env,"CANONICAL_STATE",json_object_get(c->canonical));
    json_object_object_add(env,"PERSONALITY_STATE",json_object_get(c->metrics));
    json_object *packet=parse_json(packet_json_text);
    json_object_object_add(env,"NEW_EVENT_PACKET",packet?packet:json_object_new_array());
    json_object_object_add(env,"ALLOWED_EVIDENCE_REFS",json_object_get(c->allowed_refs));
    json_object *personality=jget(profile,"personality");
    json_object_object_add(env,"PUBLIC_STYLE",json_object_new_string(jstr(personality,"public_style","")));
    json_object_object_add(env,"GENERATION_BEFORE",json_object_new_int64(generation));
    const char *et=json_object_to_json_string_ext(env,JSON_C_TO_STRING_PLAIN);
    buf_t b;buf_init(&b);buf_add(&b,legacy);buf_add(&b,"\nIMMUTABLE_CANONICAL_ENVELOPE_JSON=\n");buf_add(&b,et);buf_add(&b,"\n");
    free(legacy);json_object_put(env);return buf_take(&b);
}

static int native_refs_contains(json_object *refs,const char *s){return native_array_has_string(refs,s);}

static int native_scan_pattern(json_object *patterns,const char *text){
    if(!patterns||json_object_get_type(patterns)!=json_type_array||!text)return 0;
    int n=json_object_array_length(patterns);
    for(int i=0;i<n;i++){
        json_object *v=json_object_array_get_idx(patterns,i);
        if(!v||json_object_get_type(v)!=json_type_string)return 2;
        regex_t re;int rc=regcomp(&re,json_object_get_string(v),REG_EXTENDED|REG_ICASE|REG_NOSUB);
        if(rc!=0)return 2;
        int hit=regexec(&re,text,0,NULL,0)==0;regfree(&re);if(hit)return 1;
    }
    return 0;
}

static const char *native_gate(json_object *profile,const char *output,const native_compiled_t *c,const char *active_secret){
    json_object *root=parse_json(output);if(!root)return "OUTPUT_NOT_JSON_NO_COMMIT";
    if(json_object_get_type(root)!=json_type_object){json_object_put(root);return "OUTPUT_NOT_OBJECT_NO_COMMIT";}
    json_object *personality=jget(profile,"personality"),*contract=jget(personality,"output_contract"),*gate=jget(profile,"gate");
    if(!contract||json_object_get_type(contract)!=json_type_object){json_object_put(root);return "OUTPUT_CONTRACT_INVALID_NO_COMMIT";}
    if(native_jbool(gate,"require_hash_echo",1)){
        const char *ch=jstr(root,"canonical_state_hash_seen",NULL),*ph=jstr(root,"packet_hash_seen",NULL);
        if(!ch||strcmp(ch,c->canonical_hash)){json_object_put(root);return "CANONICAL_HASH_MISMATCH_NO_COMMIT";}
        if(!ph||strcmp(ph,c->packet_hash)){json_object_put(root);return "PACKET_HASH_MISMATCH_NO_COMMIT";}
    }
    const char *title_f=jstr(contract,"title_field",NULL),*intro_f=jstr(contract,"intro_field",NULL),*sections_f=jstr(contract,"sections_field",NULL),*continuity_f=jstr(contract,"continuity_field",NULL),*hyp_f=jstr(contract,"autobiographical_hypotheses_field",NULL);
    const char *text_f=jstr(contract,"section_text_field",NULL),*evidence_f=jstr(contract,"section_evidence_field",NULL),*claims_f=jstr(contract,"section_claims_field",NULL);
    if(!title_f||!intro_f||!sections_f||!continuity_f||!hyp_f||!text_f||!evidence_f||!claims_f){json_object_put(root);return "OUTPUT_CONTRACT_INVALID_NO_COMMIT";}
    const char *required[5]={title_f,intro_f,sections_f,continuity_f,hyp_f};
    for(int i=0;i<5;i++)if(!jget(root,required[i])){json_object_put(root);return "MISSING_OUTPUT_FIELD_NO_COMMIT";}
    json_object *title=jget(root,title_f),*intro=jget(root,intro_f),*sections=jget(root,sections_f);
    if(!title||json_object_get_type(title)!=json_type_string||!intro||json_object_get_type(intro)!=json_type_string||!sections||json_object_get_type(sections)!=json_type_array){json_object_put(root);return "OUTPUT_CONTRACT_TYPE_NO_COMMIT";}
    json_object *patterns=jget(gate,"leak_patterns");
    int scan=native_scan_pattern(patterns,json_object_get_string(title));if(scan==2){json_object_put(root);return "INVALID_LEAK_PATTERN_NO_COMMIT";}if(scan==1){json_object_put(root);return "LEAK_PATTERN_NO_COMMIT";}
    scan=native_scan_pattern(patterns,json_object_get_string(intro));if(scan==2){json_object_put(root);return "INVALID_LEAK_PATTERN_NO_COMMIT";}if(scan==1){json_object_put(root);return "LEAK_PATTERN_NO_COMMIT";}
    if(active_secret&&*active_secret&&(strstr(json_object_get_string(title),active_secret)||strstr(json_object_get_string(intro),active_secret))){json_object_put(root);return "SECRET_LEAK_REJECTED_NO_COMMIT";}
    int require_evidence=native_jbool(gate,"require_evidence_per_section",1);
    double max_overshoot=jdbl(gate,"max_claim_overshoot",0.0);
    int ns=json_object_array_length(sections);
    for(int i=0;i<ns;i++){
        json_object *section=json_object_array_get_idx(sections,i);
        if(!section||json_object_get_type(section)!=json_type_object){json_object_put(root);return "SECTION_CONTRACT_INVALID_NO_COMMIT";}
        json_object *text=jget(section,text_f);if(!text||json_object_get_type(text)!=json_type_string){json_object_put(root);return "SECTION_TEXT_MISSING_NO_COMMIT";}
        scan=native_scan_pattern(patterns,json_object_get_string(text));if(scan==2){json_object_put(root);return "INVALID_LEAK_PATTERN_NO_COMMIT";}if(scan==1){json_object_put(root);return "LEAK_PATTERN_NO_COMMIT";}
        if(active_secret&&*active_secret&&strstr(json_object_get_string(text),active_secret)){json_object_put(root);return "SECRET_LEAK_REJECTED_NO_COMMIT";}
        json_object *refs=jget(section,evidence_f);
        if(!refs){if(require_evidence){json_object_put(root);return "SECTION_WITHOUT_EVIDENCE_NO_COMMIT";}}
        else if(json_object_get_type(refs)!=json_type_array){json_object_put(root);return "SECTION_EVIDENCE_TYPE_NO_COMMIT";}
        if(refs){
            int nr=json_object_array_length(refs);
            if(require_evidence&&nr==0){json_object_put(root);return "SECTION_WITHOUT_EVIDENCE_NO_COMMIT";}
            for(int r=0;r<nr;r++){
                json_object *rv=json_object_array_get_idx(refs,r);
                if(!rv||json_object_get_type(rv)!=json_type_string||!native_refs_contains(c->allowed_refs,json_object_get_string(rv))){json_object_put(root);return "UNKNOWN_EVIDENCE_REF_NO_COMMIT";}
            }
        }
        json_object *claims=jget(section,claims_f);
        if(claims&&json_object_get_type(claims)!=json_type_object){json_object_put(root);return "STATE_CLAIMS_TYPE_NO_COMMIT";}
        if(claims){
            json_object_object_foreach(claims,name,strength){
                json_object *metric=jget(c->metrics,name);if(!metric){json_object_put(root);return "UNKNOWN_STATE_CLAIM_NO_COMMIT";}
                const char *status=jstr(metric,"status","UNKNOWN");if(strcmp(status,"VERIFIED")){json_object_put(root);return "UNVERIFIED_STATE_CLAIM_NO_COMMIT";}
                enum json_type st=json_object_get_type(strength);if(st!=json_type_int&&st!=json_type_double){json_object_put(root);return "STATE_CLAIM_TYPE_NO_COMMIT";}
                double claim=json_object_get_double(strength),measured=jdbl(metric,"value",0.0);
                if(claim>measured+max_overshoot){json_object_put(root);return "STATE_CLAIM_OVERSHOOT_NO_COMMIT";}
                const char *metric_ref=jstr(metric,"evidence_ref",NULL);
                if(!metric_ref||!refs||!native_refs_contains(refs,metric_ref)){json_object_put(root);return "STATE_CLAIM_WITHOUT_METRIC_EVIDENCE_NO_COMMIT";}
            }
        }
    }
    json_object_put(root);return NULL;
}
