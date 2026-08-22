#include "mini_entity_part00.inc"
#include "mini_entity_part01.inc"
#include "mini_entity_part02.inc"
#include "mini_entity_part03.inc"
#include <regex.h>

/* Native 0.7 invariant gate. Application field names remain profile data. */
static int key_eq_ci(const char *a,const char *b){
    if(!a||!b)return 0;
    while(*a&&*b){char x=*a++,y=*b++;if(x>='A'&&x<='Z')x=(char)(x-'A'+'a');if(y>='A'&&y<='Z')y=(char)(y-'A'+'a');if(x!=y)return 0;}
    return *a==0&&*b==0;
}
static int json_contains_forbidden_secret_value(json_object *v){
    if(!v)return 0;
    if(json_object_get_type(v)==json_type_object){
        json_object_object_foreach(v,k,child){
            if((key_eq_ci(k,"api_token")||key_eq_ci(k,"token_value")||key_eq_ci(k,"secret_value")||key_eq_ci(k,"password"))&&child&&json_object_get_type(child)!=json_type_null){
                if(json_object_get_type(child)!=json_type_string||*json_object_get_string(child))return 1;
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
    if(profile_id_out)*profile_id_out=pid;else free(pid);return raw;
}
static int mapped_field_present(json_object *root,json_object *oc,const char *mapping_key){
    json_object *m=jget(oc,mapping_key);if(!m)return 1;
    if(json_object_get_type(m)!=json_type_string||!*json_object_get_string(m))return 0;
    return jget(root,json_object_get_string(m))!=NULL;
}
static int regex_matches_anywhere(json_object *v,regex_t *rx,size_t nrx){
    if(!v)return 0;
    if(json_object_get_type(v)==json_type_object){json_object_object_foreach(v,k,child){(void)k;if(regex_matches_anywhere(child,rx,nrx))return 1;}}
    else if(json_object_get_type(v)==json_type_array){for(size_t i=0;i<json_object_array_length(v);i++)if(regex_matches_anywhere(json_object_array_get_idx(v,(int)i),rx,nrx))return 1;}
    else if(json_object_get_type(v)==json_type_string){const char *s=json_object_get_string(v);for(size_t i=0;i<nrx;i++)if(regexec(&rx[i],s,0,NULL,0)==0)return 1;}
    return 0;
}
static int output_contract_valid(json_object *profile,const char *raw,const char *expected_packet_hash,const char *expected_state_hash){
    json_object *root=parse_json(raw);if(!root||json_object_get_type(root)!=json_type_object){if(root)json_object_put(root);return 0;}
    json_object *personality=jget(profile,"personality"),*oc=personality?jget(personality,"output_contract"):NULL;
    if(!oc||json_object_get_type(oc)!=json_type_object){json_object_put(root);return 0;}
    const char *core[]={"title_field","intro_field","sections_field","continuity_field","autobiographical_hypotheses_field"};
    for(size_t i=0;i<sizeof(core)/sizeof(core[0]);i++)if(!mapped_field_present(root,oc,core[i])){json_object_put(root);return 0;}
    json_object *sf=jget(oc,"sections_field");
    if(sf&&json_object_get_type(sf)==json_type_string){
        json_object *sections=jget(root,json_object_get_string(sf));if(!sections||json_object_get_type(sections)!=json_type_array){json_object_put(root);return 0;}
        const char *text_name=jstr(oc,"section_text_field",NULL),*evidence_name=jstr(oc,"section_evidence_field",NULL);
        json_object *gate=jget(profile,"gate");int require_evidence=gate&&jget(gate,"require_evidence_per_section")?json_object_get_boolean(jget(gate,"require_evidence_per_section")):0;
        for(size_t i=0;i<json_object_array_length(sections);i++){
            json_object *sec=json_object_array_get_idx(sections,(int)i);if(!sec||json_object_get_type(sec)!=json_type_object){json_object_put(root);return 0;}
            if(text_name&&!jget(sec,text_name)){json_object_put(root);return 0;}
            if(require_evidence&&evidence_name){json_object *refs=jget(sec,evidence_name);if(!refs||json_object_get_type(refs)!=json_type_array||json_object_array_length(refs)==0){json_object_put(root);return 0;}}
        }
    }
    json_object *gate=jget(profile,"gate");
    if(gate&&jget(gate,"require_hash_echo")&&json_object_get_boolean(jget(gate,"require_hash_echo"))){
        json_object *ph=jget(root,"packet_hash_seen"),*sh=jget(root,"canonical_state_hash_seen");
        if(!ph||!sh||json_object_get_type(ph)!=json_type_string||json_object_get_type(sh)!=json_type_string||strcmp(json_object_get_string(ph),expected_packet_hash)||strcmp(json_object_get_string(sh),expected_state_hash)){json_object_put(root);return 0;}
    }
    json_object *patterns=gate?jget(gate,"leak_patterns"):NULL;
    if(patterns&&json_object_get_type(patterns)==json_type_array){
        size_t cap=json_object_array_length(patterns),n=0;regex_t *rx=cap?xmalloc(sizeof(regex_t)*cap):NULL;
        for(size_t i=0;i<cap;i++){json_object *p=json_object_array_get_idx(patterns,(int)i);if(p&&json_object_get_type(p)==json_type_string&&regcomp(&rx[n],json_object_get_string(p),REG_EXTENDED|REG_ICASE|REG_NOSUB)==0)n++;}
        int leak=regex_matches_anywhere(root,rx,n);for(size_t i=0;i<n;i++)regfree(&rx[i]);free(rx);if(leak){json_object_put(root);return 0;}
    }
    json_object_put(root);return 1;
}
static char *build_user_prompt_checked(json_object *profile,long long generation,const packet_t *p,const char *packet_json_text){
    char *base=build_user_prompt(profile,generation,p,packet_json_text),ph[65],state_hash[65];packet_hash(p,ph);
    const char *pid=jstr(profile,"profile_id","");char state_src[512];snprintf(state_src,sizeof state_src,"generation=%lld;profile=%s;packet=%s;sensor=VERIFIED",generation+1,pid,ph);sha_hex(state_src,strlen(state_src),state_hash);
    json_object *personality=jget(profile,"personality"),*oc=personality?jget(personality,"output_contract"):NULL,*gate=jget(profile,"gate");
    buf_t b;buf_init(&b);buf_add(&b,base);free(base);
    buf_printf(&b,"packet_hash_expected=%s\ncanonical_state_hash_expected=%s\n",ph,state_hash);
    if(oc)buf_printf(&b,"output_contract_json=%s\n",json_object_to_json_string_ext(oc,JSON_C_TO_STRING_PLAIN));
    if(gate)buf_printf(&b,"output_gate_json=%s\n",json_object_to_json_string_ext(gate,JSON_C_TO_STRING_PLAIN));
    if(gate&&jget(gate,"require_hash_echo")&&json_object_get_boolean(jget(gate,"require_hash_echo")))buf_add(&b,"Include exact top-level packet_hash_seen and canonical_state_hash_seen fields matching the expected hashes.\n");
    return buf_take(&b);
}
static int extract_line_value(const char *text,const char *prefix,char out[65]){
    const char *p=strstr(text,prefix);if(!p)return 0;p+=strlen(prefix);size_t n=0;while(p[n]&&p[n]!='\n'&&n<64)n++;if(n!=64)return 0;memcpy(out,p,64);out[64]=0;return 1;
}
static char *model_output_gated(json_object *profile,sqlite3 *edb,const char *system,const char *user,const char *secret_file,char **backend_out,char **model_out,char **secret_out){
    char *out=model_output(profile,edb,system,user,secret_file,backend_out,model_out,secret_out);if(!out)return NULL;
    char ph[65],sh[65];if(!extract_line_value(user,"packet_hash_expected=",ph)||!extract_line_value(user,"canonical_state_hash_expected=",sh)){free(out);die("OUTPUT_GATE_CONTEXT_MISSING_NO_COMMIT");}
    if(!output_contract_valid(profile,out,ph,sh)){free(out);die("OUTPUT_CONTRACT_GATE_REJECTED_NO_COMMIT");}
    return out;
}
#define active_profile_json active_profile_json_checked
#define build_user_prompt build_user_prompt_checked
#define model_output model_output_gated
#include "mini_entity_part04.inc"
