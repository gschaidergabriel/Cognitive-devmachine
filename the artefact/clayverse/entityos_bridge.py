from __future__ import annotations
import hashlib, os, stat, subprocess
from dataclasses import dataclass

class EntityOSIntegrityError(PermissionError): pass

@dataclass(frozen=True)
class EntityOSBridge:
    """Linux open-object execution bridge for an exact SHA-256 pinned EntityOS artifact."""
    path: str
    sha256: str
    timeout: float = 10.0

    def _open_verified(self):
        if len(self.sha256) != 64 or any(c not in '0123456789abcdefABCDEF' for c in self.sha256):
            raise EntityOSIntegrityError('invalid EntityOS sha256 pin')
        flags=os.O_RDONLY|getattr(os,'O_NOFOLLOW',0)
        try: fd=os.open(self.path,flags)
        except OSError as exc: raise EntityOSIntegrityError(f'EntityOS open failed: {exc}') from exc
        try:
            st=os.fstat(fd)
            if not stat.S_ISREG(st.st_mode) or not (st.st_mode & (stat.S_IXUSR|stat.S_IXGRP|stat.S_IXOTH)):
                raise EntityOSIntegrityError('EntityOS must be an executable regular file')
            h=hashlib.sha256()
            while True:
                chunk=os.read(fd,1024*1024)
                if not chunk: break
                h.update(chunk)
            if h.hexdigest().lower()!=self.sha256.lower(): raise EntityOSIntegrityError('EntityOS digest mismatch')
            os.lseek(fd,0,os.SEEK_SET); return fd
        except Exception:
            os.close(fd); raise

    def verify(self):
        """Fail-closed readiness probe for the exact pinned executable object."""
        fd=self._open_verified()
        try:
            st=os.fstat(fd)
            return {
                'path': self.path,
                'sha256': self.sha256.lower(),
                'size': int(st.st_size),
                'mode': stat.S_IMODE(st.st_mode),
            }
        finally:
            os.close(fd)

    def run(self, argv):
        if not isinstance(argv,list) or not argv or any(not isinstance(x,str) or '\x00' in x for x in argv):
            raise ValueError('explicit non-empty string argv required')
        fd=self._open_verified()
        try:
            executable=f'/proc/self/fd/{fd}'
            cp=subprocess.run([executable,*argv],executable=executable,pass_fds=(fd,),shell=False,capture_output=True,text=False,timeout=self.timeout,env={'PATH':os.environ.get('PATH','/usr/bin:/bin')})
        finally: os.close(fd)
        return {'ok':cp.returncode==0,'exit':cp.returncode,'stdout_sha256':hashlib.sha256(cp.stdout).hexdigest(),'stderr_sha256':hashlib.sha256(cp.stderr).hexdigest(),'stdout':cp.stdout[:4096].decode(errors='replace'),'stderr':cp.stderr[:4096].decode(errors='replace')}
