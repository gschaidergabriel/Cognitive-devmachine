#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <json-c/json.h>
#include <curl/curl.h>
#include <sqlite3.h>
#include <stdint.h>
#include <stdarg.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

#define MINI_VERSION "mini-entity/0.7.0-dev1"
#define MAX_TEXT (8u * 1024u * 1024u)
#define MAX_EVENTS 512
#define MAX_ARGV 128

typedef struct { char *p; size_t n, cap; } buf_t;
typedef struct { char *id; char *kind; char *payload; } event_t;
typedef struct { event_t *v; size_t n; int sensor_ok; } packet_t;

static void die(const char *m){ fprintf(stderr,"ERROR:%s\n",m); exit(2); }
static void die_sql(sqlite3 *db,const char *m){ fprintf(stderr,"ERROR:%s:%s\n",m,db?sqlite3_errmsg(db):"sqlite"); exit(2); }
static char *xstrdup(const char *s){ if(!s) return NULL; char *p=strdup(s); if(!p) die("OOM"); return p; }
static void *xmalloc(size_t n){ void *p=malloc(n?n:1); if(!p) die("OOM"); return p; }
static void buf_init(buf_t *b){ memset(b,0,sizeof *b); }
static void buf_reserve(buf_t *b,size_t add){ size_t need=b->n+add+1; if(need<=b->cap)return; size_t c=b->cap?b->cap:1024; while(c<need)c*=2; b->p=realloc(b->p,c); if(!b->p)die("OOM"); b->cap=c; }
static void buf_addn(buf_t*b,const char*s,size_t n){ buf_reserve(b,n); memcpy(b->p+b->n,s,n); b->n+=n; b->p[b->n]=0; }
static void buf_add(buf_t*b,const char*s){ buf_addn(b,s,strlen(s)); }
static void buf_printf(buf_t*b,const char*fmt,...){ va_list ap; va_start(ap,fmt); va_list cp; va_copy(cp,ap); int n=vsnprintf(NULL,0,fmt,cp); va_end(cp); if(n<0)die("FORMAT"); buf_reserve(b,(size_t)n); vsnprintf(b->p+b->n,b->cap-b->n,fmt,ap); va_end(ap); b->n+=(size_t)n; }
static char *buf_take(buf_t*b){ if(!b->p) return xstrdup(""); char *p=b->p; memset(b,0,sizeof *b); return p; }
static void buf_free(buf_t*b){ free(b->p); memset(b,0,sizeof *b); }

/* compact SHA-256 */
typedef struct { uint32_t h[8]; uint64_t bits; unsigned char b[64]; size_t used; } sha_ctx;
static uint32_t rr(uint32_t x,int n){return (x>>n)|(x<<(32-n));}
static const uint32_t K256[64]={
0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2};
static void sha_block(sha_ctx*c,const unsigned char*p){ uint32_t w[64]; for(int i=0;i<16;i++)w[i]=((uint32_t)p[4*i]<<24)|((uint32_t)p[4*i+1]<<16)|((uint32_t)p[4*i+2]<<8)|p[4*i+3]; for(int i=16;i<64;i++){uint32_t a=w[i-15],b=w[i-2];w[i]=(rr(b,17)^rr(b,19)^(b>>10))+w[i-7]+(rr(a,7)^rr(a,18)^(a>>3))+w[i-16];} uint32_t a=c->h[0],b=c->h[1],cc=c->h[2],d=c->h[3],e=c->h[4],f=c->h[5],g=c->h[6],h=c->h[7]; for(int i=0;i<64;i++){uint32_t t1=h+(rr(e,6)^rr(e,11)^rr(e,25))+((e&f)^((~e)&g))+K256[i]+w[i],t2=(rr(a,2)^rr(a,13)^rr(a,22))+((a&b)^(a&cc)^(b&cc));h=g;g=f;f=e;e=d+t1;d=cc;cc=b;b=a;a=t1+t2;} c->h[0]+=a;c->h[1]+=b;c->h[2]+=cc;c->h[3]+=d;c->h[4]+=e;c->h[5]+=f;c->h[6]+=g;c->h[7]+=h; }
static void sha_init(sha_ctx*c){ static const uint32_t iv[8]={0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19}; memset(c,0,sizeof *c); memcpy(c->h,iv,sizeof iv); }
static void sha_up(sha_ctx*c,const void*p0,size_t n){ const unsigned char*p=p0; c->bits+=(uint64_t)n*8; while(n){size_t t=64-c->used;if(t>n)t=n;memcpy(c->b+c->used,p,t);c->used+=t;p+=t;n-=t;if(c->used==64){sha_block(c,c->b);c->used=0;}}}
static void sha_fin(sha_ctx*c,unsigned char out[32]){uint64_t bits=c->bits;c->b[c->used++]=0x80;if(c->used>56){while(c->used<64)c->b[c->used++]=0;sha_block(c,c->b);c->used=0;}while(c->used<56)c->b[c->used++]=0;for(int i=7;i>=0;i--)c->b[c->used++]=(unsigned char)(bits>>(i*8));sha_block(c,c->b);for(int i=0;i<8;i++){out[4*i]=c->h[i]>>24;out[4*i+1]=c->h[i]>>16;out[4*i+2]=c->h[i]>>8;out[4*i+3]=c->h[i];}}
static void sha_hex(const void*p,size_t n,char out[65]){ unsigned char h[32]; sha_ctx c; sha_init(&c); sha_up(&c,p,n); sha_fin(&c,h); static const char*x="0123456789abcdef"; for(int i=0;i<32;i++){out[2*i]=x[h[i]>>4];out[2*i+1]=x[h[i]&15];}out[64]=0; }

static char *read_file(const char *path,size_t limit){ int fd=open(path,O_RDONLY|O_CLOEXEC|O_NOFOLLOW); if(fd<0)return NULL; struct stat st;if(fstat(fd,&st)||!S_ISREG(st.st_mode)||st.st_size<0||(size_t)st.st_size>limit){close(fd);return NULL;} size_t n=(size_t)st.st_size; char*p=xmalloc(n+1); size_t off=0; while(off<n){ssize_t r=read(fd,p+off,n-off);if(r<=0){free(p);close(fd);return NULL;}off+=(size_t)r;}p[n]=0;close(fd);return p; }
static int write_all(int fd,const char*p,size_t n){ while(n){ssize_t w=write(fd,p,n);if(w<0){if(errno==EINTR)continue;return -1;}p+=w;n-=(size_t)w;}return 0; }
static void utc_now(char out[32]){ time_t t=time(NULL); struct tm tm; gmtime_r(&t,&tm); strftime(out,32,"%Y-%m-%dT%H:%M:%SZ",&tm); }

static void sql_exec(sqlite3*db,const char*sql){ char*e=NULL; if(sqlite3_exec(db,sql,NULL,NULL,&e)!=SQLITE_OK){fprintf(stderr,"SQL:%s\n",e?e:"");sqlite3_free(e);die_sql(db,"SQL_EXEC");} }
static sqlite3 *open_db(const char*path){ sqlite3*db=NULL; if(sqlite3_open_v2(path,&db,SQLITE_OPEN_READWRITE|SQLITE_OPEN_CREATE|SQLITE_OPEN_FULLMUTEX,NULL)!=SQLITE_OK)die_sql(db,"OPEN_DB"); sqlite3_busy_timeout(db,5000); sql_exec(db,"PRAGMA foreign_keys=ON; PRAGMA journal_mode=DELETE; PRAGMA synchronous=FULL;"); return db; }
static void init_entity(sqlite3*db){ sql_exec(db,
"CREATE TABLE IF NOT EXISTS entity_state(id INTEGER PRIMARY KEY CHECK(id=1),generation INTEGER NOT NULL,active_profile TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);"
"CREATE TABLE IF NOT EXISTS profiles(profile_id TEXT PRIMARY KEY,profile_json TEXT NOT NULL,profile_sha256 TEXT NOT NULL,updated_at TEXT NOT NULL);"
"CREATE TABLE IF NOT EXISTS config(key TEXT PRIMARY KEY,value TEXT NOT NULL,updated_at TEXT NOT NULL);"
"CREATE TABLE IF NOT EXISTS outputs(output_id INTEGER PRIMARY KEY AUTOINCREMENT,generation INTEGER NOT NULL UNIQUE,profile_id TEXT,packet_hash TEXT NOT NULL,canonical_state_hash TEXT NOT NULL,model_output TEXT NOT NULL,created_at TEXT NOT NULL);"
"CREATE TABLE IF NOT EXISTS study_rows(output_id INTEGER PRIMARY KEY,generation INTEGER NOT NULL UNIQUE,payload_json TEXT NOT NULL,payload_hash TEXT NOT NULL,box_text TEXT NOT NULL,FOREIGN KEY(output_id) REFERENCES outputs(output_id) ON DELETE CASCADE);"
"CREATE TABLE IF NOT EXISTS run_receipts(run_id INTEGER PRIMARY KEY AUTOINCREMENT,generation_before INTEGER NOT NULL,generation_after INTEGER,status TEXT NOT NULL,packet_hash TEXT,detail TEXT,created_at TEXT NOT NULL);"
); char now[32];utc_now(now);sqlite3_stmt*s=NULL;sqlite3_prepare_v2(db,"INSERT OR IGNORE INTO entity_state(id,generation,active_profile,created_at,updated_at) VALUES(1,0,NULL,?,?)",-1,&s,NULL);sqlite3_bind_text(s,1,now,-1,SQLITE_TRANSIENT);sqlite3_bind_text(s,2,now,-1,SQLITE_TRANSIENT);sqlite3_step(s);sqlite3_finalize(s); }
