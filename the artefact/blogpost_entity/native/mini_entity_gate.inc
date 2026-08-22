#include <regex.h>

/*
 * Fail-closed native semantic gate.
 *
 * This closes the post-inference/pre-commit invariant boundary for the generic event
 * pipeline without pretending the native 0.7 source already implements the richer
 * reference-runtime state-metric compiler. Profiles that opt into `gate` must echo the
 * exact native canonical/packet hashes, satisfy their configured output-field contract,
 * cite only offered evidence, and pass leak checks. State claims remain fail-closed until
 * a native VERIFIED metric compiler exists.
 */

static int gate_bool(json_object *o,const char *k,int d){
    json_object *v=jget(o,k);
    if(!v)return d;
    if(json_object_get_type(v)==json_type_boolean)return json_object_get_boolean(v);
    return d;
}

static int gate_ref_allowed(const packet_t *p,const char *ref){
    if(!ref)return 0;
    if(p->n==0&&!strcmp(ref,"quiet:verified"))return 1;
    for(size_t i=0;i<p->n;i++)if(!strcmp(ref,p->v[i].id))return 1;
    return 0;
}

static int gate_regex_matches(const char *pattern,const char *text){
    regex_t rx;
    if(regcomp(&rx,pattern,REG_EXTENDED|REG_ICASE|REG_NOSUB)!=0)return -1;
    int rc=regexec(&rx,text?text:"",0,NULL,0);
    regfree(&rx);
    return rc==0?1:0;
}

static const char *gate_scan_text(json_object *gate,const char *text){
    json_object *patterns=jget(gate,"leak_patterns");
    if(!patterns)return NULL;
    if(json_object_get_type(patterns)!=json_type_array)return "GATE_LEAK_PATTERNS_NOT_ARRAY_NO_COMMIT";
    for(size_t i=0;i<json_object_array_length(patterns);i++){
        json_object *v=json_object_array_get_idx(patterns,(int)i);
        if(!v||json_object_get_type(v)!=json_type_string)return "GATE_LEAK_PATTERN_NOT_STRING_NO_COMMIT";
        int m=gate_regex_matches(json_object_get_string(v),text);
        if(m<0)return "GATE_LEAK_PATTERN_INVALID_NO_COMMIT";
        if(m>0)return "GATE_LEAK_PATTERN_NO_COMMIT";
    }
    return NULL;
}

static char *mini_entity_gated_build_user_prompt(json_object *profile,long long generation,const packet_t *p,const char *packet_json_text){
    char *base=build_user_prompt(profile,generation,p,packet_json_text);
    json_object *gate=jget(profile,"gate");
    if(!gate||json_object_get_type(gate)!=json_type_object)return base;

    char phash[65];
    packet_hash(p,phash);
    const char *pid=jstr(profile,"profile_id","");
    char state_src[512],state_hash[65];
    snprintf(state_src,sizeof state_src,"generation=%lld;profile=%s;packet=%s;sensor=VERIFIED",generation+1,pid,phash);
    sha_hex(state_src,strlen(state_src),state_hash);

    json_object *ctx=json_object_new_object();
    json_object_object_add(ctx,"canonical_state_hash",json_object_new_string(state_hash));
    json_object_object_add(ctx,"packet_hash",json_object_new_string(phash));
    json_object *refs=json_object_new_array();
    if(p->n==0)json_object_array_add(refs,json_object_new_string("quiet:verified"));
    for(size_t i=0;i<p->n;i++)json_object_array_add(refs,json_object_new_string(p->v[i].id));
    json_object_object_add(ctx,"allowed_evidence_refs",refs);
    json_object_object_add(ctx,"state_claim_policy",json_object_new_string("NO_NATIVE_VERIFIED_METRICS_YET: state_claims MUST be empty"));
    const char *plain=json_object_to_json_string_ext(ctx,JSON_C_TO_STRING_PLAIN);

    buf_t b;buf_init(&b);
    buf_add(&b,base);
    buf_add(&b,"\nIMMUTABLE_NATIVE_GATE: Echo canonical_state_hash_seen and packet_hash_seen exactly. Every section must obey configured evidence rules. Never cite evidence outside allowed_evidence_refs. State claims are forbidden until native VERIFIED metrics exist.\nNATIVE_GATE_CONTEXT_JSON=");
    buf_add(&b,plain);
    buf_add(&b,"\n");
    free(base);
    json_object_put(ctx);
    return buf_take(&b);
}

static const char *mini_entity_gate_validate(json_object *profile,const packet_t *p,const char *packet_hash_s,const char *state_hash,const char *output){
    json_object *gate=jget(profile,"gate");
    if(!gate)return NULL;
    if(json_object_get_type(gate)!=json_type_object)return "GATE_CONFIG_NOT_OBJECT_NO_COMMIT";
    json_object *personality=jget(profile,"personality"),*contract=jget(personality,"output_contract");
    if(!contract||json_object_get_type(contract)!=json_type_object)return "GATE_OUTPUT_CONTRACT_MISSING_NO_COMMIT";
    json_object *root=parse_json(output);
    if(!root||json_object_get_type(root)!=json_type_object){if(root)json_object_put(root);return "GATE_OUTPUT_NOT_JSON_OBJECT_NO_COMMIT";}
    const char *error=NULL;

    if(gate_bool(gate,"require_hash_echo",1)){
        const char *seen_state=jstr(root,"canonical_state_hash_seen",NULL);
        const char *seen_packet=jstr(root,"packet_hash_seen",NULL);
        if(!seen_state||strcmp(seen_state,state_hash)){error="GATE_CANONICAL_HASH_MISMATCH_NO_COMMIT";goto done;}
        if(!seen_packet||strcmp(seen_packet,packet_hash_s)){error="GATE_PACKET_HASH_MISMATCH_NO_COMMIT";goto done;}
    }

    const char *title_field=jstr(contract,"title_field",NULL),*intro_field=jstr(contract,"intro_field",NULL),*sections_field=jstr(contract,"sections_field",NULL),*continuity_field=jstr(contract,"continuity_field",NULL),*hyp_field=jstr(contract,"autobiographical_hypotheses_field",NULL);
    const char *section_text_field=jstr(contract,"section_text_field",NULL),*section_evidence_field=jstr(contract,"section_evidence_field",NULL),*section_claims_field=jstr(contract,"section_claims_field",NULL);
    if(!title_field||!intro_field||!sections_field||!continuity_field||!hyp_field||!section_text_field||!section_evidence_field||!section_claims_field){error="GATE_CONTRACT_FIELDS_MISSING_NO_COMMIT";goto done;}
    const char *required_fields[]={title_field,intro_field,sections_field,continuity_field,hyp_field};
    for(size_t i=0;i<sizeof(required_fields)/sizeof(required_fields[0]);i++)if(!jget(root,required_fields[i])){error="GATE_REQUIRED_OUTPUT_FIELD_MISSING_NO_COMMIT";goto done;}

    json_object *title=jget(root,title_field),*intro=jget(root,intro_field),*sections=jget(root,sections_field);
    if(!title||json_object_get_type(title)!=json_type_string||!intro||json_object_get_type(intro)!=json_type_string||!sections||json_object_get_type(sections)!=json_type_array){error="GATE_OUTPUT_FIELD_TYPE_NO_COMMIT";goto done;}
    error=gate_scan_text(gate,json_object_get_string(title));if(error)goto done;
    error=gate_scan_text(gate,json_object_get_string(intro));if(error)goto done;

    for(size_t i=0;i<json_object_array_length(sections);i++){
        json_object *section=json_object_array_get_idx(sections,(int)i);
        if(!section||json_object_get_type(section)!=json_type_object){error="GATE_SECTION_NOT_OBJECT_NO_COMMIT";goto done;}
        json_object *text=jget(section,section_text_field),*refs=jget(section,section_evidence_field),*claims=jget(section,section_claims_field);
        if(!text||json_object_get_type(text)!=json_type_string){error="GATE_SECTION_TEXT_MISSING_NO_COMMIT";goto done;}
        error=gate_scan_text(gate,json_object_get_string(text));if(error)goto done;
        if(!refs){if(gate_bool(gate,"require_evidence_per_section",1)){error="GATE_SECTION_WITHOUT_EVIDENCE_NO_COMMIT";goto done;}}
        else {
            if(json_object_get_type(refs)!=json_type_array){error="GATE_SECTION_EVIDENCE_NOT_ARRAY_NO_COMMIT";goto done;}
            if(gate_bool(gate,"require_evidence_per_section",1)&&json_object_array_length(refs)==0){error="GATE_SECTION_WITHOUT_EVIDENCE_NO_COMMIT";goto done;}
            for(size_t r=0;r<json_object_array_length(refs);r++){
                json_object *rv=json_object_array_get_idx(refs,(int)r);
                if(!rv||json_object_get_type(rv)!=json_type_string||!gate_ref_allowed(p,json_object_get_string(rv))){error="GATE_UNKNOWN_EVIDENCE_REF_NO_COMMIT";goto done;}
            }
        }
        if(claims){
            if(json_object_get_type(claims)!=json_type_object){error="GATE_STATE_CLAIMS_NOT_OBJECT_NO_COMMIT";goto done;}
            if(json_object_object_length(claims)>0){error="GATE_UNVERIFIED_STATE_CLAIM_NO_COMMIT";goto done;}
        }
    }

done:
    json_object_put(root);
    return error;
}

static int mini_entity_gated_commit_run(sqlite3 *db,const char *source_path,const packet_t *p,long long observed_gen,const char *profile_id,const char *packet_hash_s,const char *state_hash,const char *output,const char *study,const char *study_hash,const char *box,long long *new_gen,long long *out_id){
    char *pid=NULL,*profile_text=active_profile_json(db,&pid);
    json_object *profile=profile_text?parse_json(profile_text):NULL;
    const char *error=profile?mini_entity_gate_validate(profile,p,packet_hash_s,state_hash,output):"GATE_PROFILE_RELOAD_FAILED_NO_COMMIT";
    if(profile)json_object_put(profile);
    free(profile_text);free(pid);
    if(error)die(error);
    return commit_run(db,source_path,p,observed_gen,profile_id,packet_hash_s,state_hash,output,study,study_hash,box,new_gen,out_id);
}
