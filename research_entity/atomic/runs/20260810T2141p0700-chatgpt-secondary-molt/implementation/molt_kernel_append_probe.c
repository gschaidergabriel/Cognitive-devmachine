#define _GNU_SOURCE
#include <errno.h>
#include <fcntl.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/types.h>
#include <sys/uio.h>
#include <unistd.h>
#ifndef RWF_NOAPPEND
#define RWF_NOAPPEND 0x00000020
#endif

static long fsize(const char *p) { struct stat st; if (stat(p,&st)) return -1; return (long)st.st_size; }
static void emit_errno(const char *name,int rc,int e){ printf("\"%s\":{\"rc\":%d,\"errno\":%d,\"error\":\"%s\"}",name,rc,e,strerror(e)); }

int main(int argc,char **argv){
  if(argc!=2){fprintf(stderr,"usage: %s file\n",argv[0]);return 2;}
  const char *p=argv[1]; long before=fsize(p); unsigned char prefix_before[16],prefix_after[16];
  int rfd=open(p,O_RDONLY); if(rfd<0)return 3; if(read(rfd,prefix_before,sizeof(prefix_before))!=(ssize_t)sizeof(prefix_before))return 4; close(rfd);

  errno=0; int noappend=open(p,O_WRONLY); int noappend_e=errno; if(noappend>=0) close(noappend);
  errno=0; int fd=open(p,O_WRONLY|O_APPEND); int append_open_e=errno;
  if(fd<0){ printf("{\"status\":\"APPEND_OPEN_FAILED\",\"errno\":%d}\n",append_open_e); return 5; }

  errno=0; ssize_t pw=pwrite(fd,"P",1,0); int pw_e=errno;
  struct iovec iov={.iov_base=(void*)"V",.iov_len=1}; errno=0; ssize_t pv=pwritev2(fd,&iov,1,0,RWF_NOAPPEND); int pv_e=errno;
  errno=0; int tr=ftruncate(fd,1); int tr_e=errno;
  errno=0; int fa=posix_fallocate(fd,0,1); int fa_e=(fa==0?0:fa);
  fsync(fd); close(fd);

  long after=fsize(p); rfd=open(p,O_RDONLY); if(rfd<0)return 6; if(read(rfd,prefix_after,sizeof(prefix_after))!=(ssize_t)sizeof(prefix_after))return 7; close(rfd);
  int prefix_changed=memcmp(prefix_before,prefix_after,sizeof(prefix_before))!=0;

  printf("{\"status\":\"COMPLETE\",\"file_size_before\":%ld,\"file_size_after\":%ld,\"prefix_changed\":%s,",before,after,prefix_changed?"true":"false");
  emit_errno("open_without_append",noappend,noappend_e); printf(",");
  emit_errno("pwrite_offset0",(int)pw,pw_e); printf(",");
  emit_errno("pwritev2_noappend_offset0",(int)pv,pv_e); printf(",");
  emit_errno("ftruncate_to_1",tr,tr_e); printf(",");
  emit_errno("posix_fallocate",fa,fa_e); printf("}\n");
  return prefix_changed?10:0;
}
