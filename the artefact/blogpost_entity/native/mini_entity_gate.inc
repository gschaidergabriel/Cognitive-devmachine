#include <regex.h>

/*
 * Immutable generic semantic gate for the native Mini Entity path.
 *
 * The gate is intentionally application-neutral: field names, leak patterns,
 * evidence prefixes and state-claim policy come from the active DB profile.
 * The binary owns only the invariant that unbound/missing/unknown claims are
 * rejected before any output/event/generation commit.
 *
 * Current native compilation is conservative for state metrics: only metrics
 * explicitly supplied by profile data with status=VERIFIED and a numeric value
 * are claimable here. Expression-derived metrics remain UNKNOWN until the full
 * profile expression/compiler surface is ported. This fails closed rather than
 * manufacturing state from unsupported native semantics.
 */

typedef struct {
    char canonical_state_hash[65];
    char packet_hash[65];
    char *canonical_json;
    char *allowed_refs_json;
} gate_context_t;

static int json_truth(json_object *v,int d){
    if(!v)return d;
    if(json_object_get_type(v)==json_type_boolean)return json_object_get_boolean(v);
    if(json_object_get_type(v)==json_type_int)return json_object_get_int(v)!=0;
    return d;
}

static int json_number(json_object *v,double *out){
    if(!v)return 0;
    enum json_type t=json_object_get_type(v);
    if(t!=json_type_int&&t!=json_type_double)return 0;
    *out=json_object_get_double(v);
    return 1;
}

static const char *profile_evidence_prefix(json_object *profile,const char *kind){
    json_object *sources=jget(profile,"sources");
    if(!sources||json_object_get_type(sources)!=json_type_array)return NULL;
    int n=json_object_array_length(sources);
    for(int i=0;i<n;i++){
        json_object *spec=json_object_array_get_idx(sources,i);
        if(!spec||json_object_get_type(spec)!=json_type_object)continue;
        const char *k=jstr(spec,"kind",NULL);
        if(k&&!strcmp(k,kind))return jstr(spec,"evidence_prefix",NULL);
    }
    return NULL;
}

static int json_array_has_string(json_object *a,const char *s){
    if(!a||json_object_get_type(a)!=json_type_array||!s)return 0;
    int n=json_object_array_length(a);
    for(int i=0;i<n;i++){
        json_object *v=json_object_array_get_idx(a,i);
        if(v&&json_object_get_type(v)==json_type_string&&!strcmp(json_object_get_string(v),s))return 1;
    }
    return 0;
}

static void json_array_add_unique_string(json_object *a,const char *s){
    if(s&&*s&&!json_array_has_string(a,s))json_object_array_add(a,json_object_new_string(s));
}

static json_object *gate_allowed_refs(json_object *profile,const packet_t *packet){
    json_object *a=json_object_new_array();
    for(size_t i=0;i<packet->n;i++){
        const char *prefix=profile_evidence_prefix(profile,packet->v[i].kind);
        buf_t b;buf_init(&b);
        if(prefix&&*prefix)buf_add(&b,prefix);else buf_printf(&b,"%s:",packet->v[i].kind);
        buf_add(&b,packet->v[i].id);
        char *ref=buf_take(&b);
        json_array_add_unique_string(a,ref);
        free(ref);
    }
    json_object *metrics=jget(profile,"state_metrics");
    if(metrics&&json_object_get_type(metrics)==json_type_array){
        int n=json_object_array_length(metrics);
        for(int i=0;i<n;i++){
            json_object *m=json_object_array_get_idx(metrics,i);
            if(!m||json_object_get_type(m)!=json_type_object)continue;
            const char *status=jstr(m,"status",NULL),*ref=jstr(m,"evidence_ref",NULL);
            double value=0.0;
            if(status&&!strcmp(status,"VERIFIED")&&json_number(jget(m,"value"),&value))json_array_add_unique_string(a,ref);
        }
    }
    return a;
}

static int gate_context_build(json_object *profile,const packet_t *packet,long long observed,const char *profile_id,gate_context_t *ctx){
    memset(ctx,0,sizeof *ctx);
    packet_hash(packet,ctx->packet_hash);
    json_object *allowed=gate_allowed_refs(profile,packet);
    json_object *canonical=json_object_new_object();
    json_object_object_add(canonical,"generation",json_object_new_int64(observed+1));
    json_object_object_add(canonical,"profile_id",json_object_new_string(profile_id?profile_id:""));
    json_object_object_add(canonical,"source_count",json_object_new_int64((int64_t)packet->n));
    json_object_object_add(canonical,"sensor_health",json_object_new_string(packet->sensor_ok?"VERIFIED":"UNKNOWN"));
    json_object_object_add(canonical,"packet_hash",json_object_new_string(ctx->packet_hash));
    const char *raw=json_object_to_json_string_ext(canonical,JSON_C_TO_STRING_PLAIN);
    sha_hex(raw,strlen(raw),ctx->canonical_state_hash);
    ctx->canonical_json=xstrdup(raw);
    ctx->allowed_refs_json=xstrdup(json_object_to_json_string_ext(allowed,JSON_C_TO_STRING_PLAIN));
    json_object_put(canonical);
    json_object_put(allowed);
    return 1;
}

static void gate_context_free(gate_context_t *ctx){
    free(ctx->canonical_json);free(ctx->allowed_refs_json);memset(ctx,0,sizeof *ctx);
}

static char *build_guarded_user_prompt(json_object *profile,long long generation,const packet_t *packet,const char *packet_json_text,const gate_context_t *ctx){
    char *base=build_user_prompt(profile,generation,packet,packet_json_text);
    buf_t b;buf_init(&b);
    buf_add(&b,"IMMUTABLE_PIPELINE_GUARD=UNKNOWN!=ZERO!=ERROR!=MEASURED; output cannot mint canonical evidence.\n");
    buf_printf(&b,"CANONICAL_STATE_HASH=%s\n",ctx->canonical_state_hash);
    buf_printf(&b,"PACKET_HASH=%s\n",ctx->packet_hash);
    buf_add(&b,"CANONICAL_STATE=");buf_add(&b,ctx->canonical_json?ctx->canonical_json:"{}");buf_add(&b,"\n");
    buf_add(&b,"ALLOWED_EVIDENCE_REFS=");buf_add(&b,ctx->allowed_refs_json?ctx->allowed_refs_json:"[]");buf_add(&b,"\n");
    buf_add(&b,"If the active output contract requires hash echo, return canonical_state_hash_seen and packet_hash_seen exactly.\n");
    buf_add(&b,base?base:"");
    free(base);
    return buf_take(&b);
}

static int regex_matches(const char *pattern,const char *text){
    if(!pattern||!*pattern||!text)return 0;
    regex_t rx;
    if(regcomp(&rx,pattern,REG_EXTENDED|REG_ICASE|REG_NOSUB)!=0)return 1; /* invalid configured pattern fails closed */
    int match=regexec(&rx,text,0,NULL,0)==0;
    regfree(&rx);
    return match;
}

static int gate_scan_value(json_object *v,json_object *patterns,const char *secret,char *err,size_t errn){
    if(!v)return 1;
    enum json_type t=json_object_get_type(v);
    if(t==json_type_string){
        const char *s=json_object_get_string(v);
        if(secret&&*secret&&strstr(s,secret)){snprintf(err,errn,"SECRET_LEAK");return 0;}
        if(patterns&&json_object_get_type(patterns)==json_type_array){
            int n=json_object_array_length(patterns);
            for(int i=0;i<n;i++){
                json_object *p=json_object_array_get_idx(patterns,i);
                if(!p||json_object_get_type(p)!=json_type_string){snprintf(err,errn,"BAD_LEAK_PATTERN");return 0;}
                if(regex_matches(json_object_get_string(p),s)){snprintf(err,errn,"LEAK_PATTERN");return 0;}
            }
        }
        return 1;
    }
    if(t==json_type_array){
        int n=json_object_array_length(v);
        for(int i=0;i<n;i++)if(!gate_scan_value(json_object_array_get_idx(v,i),patterns,secret,err,errn))return 0;
        return 1;
    }
    if(t==json_type_object){
        json_object_object_foreach(v,key,val){(void)key;if(!gate_scan_value(val,patterns,secret,err,errn))return 0;}
    }
    return 1;
}

static json_object *profile_metric(json_object *profile,const char *name){
    json_object *metrics=jget(profile,"state_metrics");
    if(!metrics||json_object_get_type(metrics)!=json_type_array)return NULL;
    int n=json_object_array_length(metrics);
    for(int i=0;i<n;i++){
        json_object *m=json_object_array_get_idx(metrics,i);
        if(m&&json_object_get_type(m)==json_type_object){const char *mn=jstr(m,"name",NULL);if(mn&&!strcmp(mn,name))return m;}
    }
    return NULL;
}

static int gate_required_field(json_object *payload,json_object *contract,const char *contract_key,char *err,size_t errn){
    const char *field=jstr(contract,contract_key,NULL);
    if(!field||!*field){snprintf(err,errn,"OUTPUT_CONTRACT_MISSING_%s",contract_key);return 0;}
    if(!jget(payload,field)){snprintf(err,errn,"MISSING_OUTPUT_FIELD:%s",field);return 0;}
    return 1;
}

static int gate_output(json_object *profile,const gate_context_t *ctx,const char *output,const char *active_secret,char *err,size_t errn){
    json_object *payload=parse_json(output);
    if(!payload||json_object_get_type(payload)!=json_type_object){if(payload)json_object_put(payload);snprintf(err,errn,"OUTPUT_NOT_JSON_OBJECT");return 0;}
    json_object *personality=jget(profile,"personality"),*contract=jget(personality,"output_contract"),*gate=jget(profile,"gate");
    if(!contract||json_object_get_type(contract)!=json_type_object){json_object_put(payload);snprintf(err,errn,"OUTPUT_CONTRACT_MISSING");return 0;}

    int require_hash=1;
    if(gate&&jget(gate,"require_hash_echo"))require_hash=json_truth(jget(gate,"require_hash_echo"),1);
    if(require_hash){
        const char *seen=jstr(payload,"canonical_state_hash_seen",NULL),*pseen=jstr(payload,"packet_hash_seen",NULL);
        if(!seen||strcmp(seen,ctx->canonical_state_hash)){json_object_put(payload);snprintf(err,errn,"CANONICAL_HASH_MISMATCH");return 0;}
        if(!pseen||strcmp(pseen,ctx->packet_hash)){json_object_put(payload);snprintf(err,errn,"PACKET_HASH_MISMATCH");return 0;}
    }

    const char *required_keys[]={"title_field","intro_field","sections_field","continuity_field","autobiographical_hypotheses_field"};
    for(size_t i=0;i<sizeof required_keys/sizeof required_keys[0];i++)if(!gate_required_field(payload,contract,required_keys[i],err,errn)){json_object_put(payload);return 0;}

    json_object *patterns=gate?jget(gate,"leak_patterns"):NULL;
    if(!gate_scan_value(payload,patterns,active_secret,err,errn)){json_object_put(payload);return 0;}

    const char *sections_field=jstr(contract,"sections_field",NULL),*text_field=jstr(contract,"section_text_field",NULL),*refs_field=jstr(contract,"section_evidence_field",NULL),*claims_field=jstr(contract,"section_claims_field",NULL);
    json_object *sections=jget(payload,sections_field);
    if(!sections||json_object_get_type(sections)!=json_type_array){json_object_put(payload);snprintf(err,errn,"SECTIONS_NOT_ARRAY");return 0;}
    if(!text_field||!refs_field||!claims_field){json_object_put(payload);snprintf(err,errn,"SECTION_CONTRACT_INCOMPLETE");return 0;}
    json_object *allowed=parse_json(ctx->allowed_refs_json?ctx->allowed_refs_json:"[]");
    int require_evidence=1;
    if(gate&&jget(gate,"require_evidence_per_section"))require_evidence=json_truth(jget(gate,"require_evidence_per_section"),1);
    double overshoot=gate?jdbl(gate,"max_claim_overshoot",0.0):0.0;

    int sn=json_object_array_length(sections);
    for(int i=0;i<sn;i++){
        json_object *section=json_object_array_get_idx(sections,i);
        if(!section||json_object_get_type(section)!=json_type_object){snprintf(err,errn,"SECTION_NOT_OBJECT");goto reject;}
        json_object *text=jget(section,text_field),*refs=jget(section,refs_field),*claims=jget(section,claims_field);
        if(!text||json_object_get_type(text)!=json_type_string){snprintf(err,errn,"SECTION_TEXT_MISSING");goto reject;}
        if(!refs||json_object_get_type(refs)!=json_type_array){snprintf(err,errn,"SECTION_EVIDENCE_NOT_ARRAY");goto reject;}
        if(require_evidence&&json_object_array_length(refs)==0){snprintf(err,errn,"SECTION_WITHOUT_EVIDENCE");goto reject;}
        int rn=json_object_array_length(refs);
        for(int r=0;r<rn;r++){
            json_object *rv=json_object_array_get_idx(refs,r);
            if(!rv||json_object_get_type(rv)!=json_type_string||!json_array_has_string(allowed,json_object_get_string(rv))){snprintf(err,errn,"UNKNOWN_EVIDENCE_REF");goto reject;}
        }
        if(claims){
            if(json_object_get_type(claims)!=json_type_object){snprintf(err,errn,"STATE_CLAIMS_NOT_OBJECT");goto reject;}
            json_object_object_foreach(claims,name,strength){
                json_object *metric=profile_metric(profile,name);double claim=0.0,value=0.0;
                if(!metric){snprintf(err,errn,"UNKNOWN_STATE_CLAIM");goto reject;}
                const char *status=jstr(metric,"status",NULL),*mref=jstr(metric,"evidence_ref",NULL);
                if(!status||strcmp(status,"VERIFIED")){snprintf(err,errn,"UNVERIFIED_STATE_CLAIM");goto reject;}
                if(!json_number(jget(metric,"value"),&value)||!json_number(strength,&claim)){snprintf(err,errn,"STATE_CLAIM_NOT_NUMERIC");goto reject;}
                if(claim>value+overshoot){snprintf(err,errn,"STATE_CLAIM_OVERSHOOT");goto reject;}
                if(!mref||!json_array_has_string(refs,mref)){snprintf(err,errn,"STATE_CLAIM_WITHOUT_METRIC_EVIDENCE");goto reject;}
            }
        }
    }
    json_object_put(allowed);json_object_put(payload);return 1;
reject:
    json_object_put(allowed);json_object_put(payload);return 0;
}
