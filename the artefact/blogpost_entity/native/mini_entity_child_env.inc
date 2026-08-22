/*
 * Immutable local-exec child environment boundary.
 *
 * A configured local model runner is inference only. It must not inherit ambient
 * API/cloud credentials merely because it is executed by the Mini Entity process.
 * Preserve only the command-search path plus deterministic locale/time settings.
 */
static int mini_entity_execvp_isolated(const char *file, char *const argv[]){
    const char *parent_path=getenv("PATH");
    char *safe_path=strdup((parent_path&&*parent_path)?parent_path:"/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin");
    if(!safe_path){errno=ENOMEM;return -1;}
    if(clearenv()!=0){int e=errno;free(safe_path);errno=e;return -1;}
    if(setenv("PATH",safe_path,1)!=0||setenv("LANG","C",1)!=0||setenv("LC_ALL","C",1)!=0||setenv("TZ","UTC",1)!=0){
        int e=errno;free(safe_path);errno=e;return -1;
    }
    free(safe_path);
    return execvp(file,argv);
}
