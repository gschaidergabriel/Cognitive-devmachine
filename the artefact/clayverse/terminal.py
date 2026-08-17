from __future__ import annotations
import os,pty,shlex,signal
from dataclasses import dataclass
@dataclass
class PermanentTerminal:
    user_id:str; argv:list[str]; pid:int|None=None; master_fd:int|None=None
    def start(self):
        if self.pid: return
        pid,fd=pty.fork()
        if pid==0: os.execvp(self.argv[0],self.argv)
        self.pid=pid; self.master_fd=fd
    def stop(self):
        if self.pid:
            try: os.kill(self.pid,signal.SIGTERM)
            except ProcessLookupError: pass
            self.pid=None
class TerminalSupervisor:
    """Two user perspectives; not two ClayVerse entities."""
    def __init__(self,command='claude'):
        argv=shlex.split(command); self.terminals={u:PermanentTerminal(u,argv) for u in ('gabriel','andreas')}
    def start_all(self):
        for t in self.terminals.values(): t.start()
    def stop_all(self):
        for t in self.terminals.values(): t.stop()
