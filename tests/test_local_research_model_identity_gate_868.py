from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import signal
import socket
import subprocess
import tempfile
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/local_research_model_server.sh"

FAKE_C = r'''
#include <arpa/inet.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
static volatile sig_atomic_t running = 1;
static int server_fd = -1;
static void stop(int sig){ (void)sig; running=0; if(server_fd>=0) close(server_fd); }
int main(int argc, char **argv){
  const char *model=""; int port=0;
  for(int i=1;i<argc;i++){
    if(strcmp(argv[i],"-m")==0 && i+1<argc) model=argv[++i];
    else if(strcmp(argv[i],"--port")==0 && i+1<argc) port=atoi(argv[++i]);
  }
  const char *override=getenv("FAKE_REPORT_MODEL_PATH");
  const char *reported=(override && *override)?override:model;
  if(!*model || port<=0) return 3;
  signal(SIGTERM,stop); signal(SIGINT,stop);
  int fd=socket(AF_INET,SOCK_STREAM,0); if(fd<0) return 4; server_fd=fd;
  int one=1; setsockopt(fd,SOL_SOCKET,SO_REUSEADDR,&one,sizeof(one));
  struct sockaddr_in a; memset(&a,0,sizeof(a)); a.sin_family=AF_INET; a.sin_addr.s_addr=htonl(INADDR_LOOPBACK); a.sin_port=htons((unsigned short)port);
  if(bind(fd,(struct sockaddr*)&a,sizeof(a))<0) return 5;
  if(listen(fd,8)<0) return 6;
  while(running){
    int c=accept(fd,NULL,NULL); if(c<0){ if(!running) break; continue; }
    char req[2048]={0}; ssize_t n=read(c,req,sizeof(req)-1); (void)n;
    const char *health=strstr(req,"GET /health ");
    const char *props=strstr(req,"GET /props ");
    char body[4096];
    if(health) snprintf(body,sizeof(body),"{\"status\":\"ok\"}");
    else if(props) snprintf(body,sizeof(body),"{\"model_path\":\"%s\",\"build_info\":\"fake-exact-runtime\"}",reported);
    else snprintf(body,sizeof(body),"{\"error\":\"not_found\"}");
    char out[8192]; int len=snprintf(out,sizeof(out),"HTTP/1.1 %s\r\nContent-Type: application/json\r\nContent-Length: %zu\r\nConnection: close\r\n\r\n%s",(health||props)?"200 OK":"404 Not Found",strlen(body),body);
    write(c,out,(size_t)len); close(c);
  }
  if(fd>=0) close(fd); return 0;
}
'''


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


class LocalResearchModelIdentityGate868(unittest.TestCase):
    def compile_runtime(self, td: Path) -> Path:
        src = td / "fake_server.c"
        src.write_text(FAKE_C, encoding="utf-8")
        binary = td / "llama-server"
        subprocess.run(["gcc", "-O2", str(src), "-o", str(binary)], check=True, capture_output=True, text=True)
        return binary

    def fixture(self, td: Path):
        runtime = self.compile_runtime(td)
        model = td / "model.gguf"
        model.write_bytes(b"GGUF-exact-test-bytes-v2")
        artifacts = td / "artifacts"
        env = os.environ.copy()
        env.update({
            "CLAY_LLAMA_SERVER_BIN": str(runtime),
            "CLAY_LLAMA_SERVER_SHA256": digest(runtime),
            "CLAY_LOCAL_MODEL_FILE": str(model),
            "CLAY_LOCAL_MODEL_SHA256": digest(model),
            "CLAY_LOCAL_RESEARCH_STATE_DIR": str(artifacts),
            "CLAY_LOCAL_RESEARCH_PORT": str(free_port()),
            "CLAY_LOCAL_RESEARCH_READY_TIMEOUT": "10",
        })
        return runtime, model, artifacts, env

    def test_source_has_no_remote_materialization_or_selector_execution(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for forbidden in ("git clone", " -hf ", "huggingface", "Qwen/Qwen", "integrate.api", "openrouter.ai"):
            self.assertNotIn(forbidden, text)
        for required in ("CLAY_LLAMA_SERVER_SHA256", "CLAY_LOCAL_MODEL_SHA256", '"$RUNTIME_BIN" \\\n  -m "$MODEL_FILE"', "loader_consumption_attestation"):
            self.assertIn(required, text)

    def test_exact_bytes_crosscheck_reaches_ready_without_minting_loader_credit(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            runtime, model, artifacts, env = self.fixture(td)
            proc = subprocess.Popen(["bash", str(SCRIPT)], cwd=ROOT, env=env, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            state_path = artifacts / "local-model.json"
            state = None
            deadline = time.time() + 8
            try:
                while time.time() < deadline:
                    if state_path.exists():
                        try:
                            state = json.loads(state_path.read_text(encoding="utf-8"))
                        except json.JSONDecodeError:
                            state = None
                        if state and state.get("state") in {"READY_IDENTITY_OBSERVED", "READY_IDENTITY_REJECTED"}:
                            break
                    if proc.poll() is not None:
                        break
                    time.sleep(0.1)
                self.assertIsNotNone(state)
                self.assertEqual(state["state"], "READY_IDENTITY_OBSERVED")
                self.assertTrue(state["identity_admitted_prerequisite"])
                self.assertEqual(state["expected_runtime_sha256"], digest(runtime))
                self.assertEqual(state["server_exe_sha256"], digest(runtime))
                self.assertEqual(state["expected_model_sha256"], digest(model))
                self.assertEqual(state["model_sha256_post_load_path"], digest(model))
                self.assertTrue(state["runtime_process_bound_to_expected_path"])
                self.assertTrue(state["model_path_matches_expected"])
                self.assertFalse(state["loader_consumption_attestation"])
                self.assertEqual(state["jspace_model_runtime_credit"], 0)
            finally:
                if proc.poll() is None:
                    proc.send_signal(signal.SIGTERM)
                    try:
                        proc.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        proc.kill()
                        proc.wait()
                if proc.stdout:
                    proc.stdout.close()
                if proc.stderr:
                    proc.stderr.close()

    def test_wrong_preload_model_hash_rejects_before_runtime(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            _, _, artifacts, env = self.fixture(td)
            env["CLAY_LOCAL_MODEL_SHA256"] = "0" * 64
            proc = subprocess.run(["bash", str(SCRIPT)], cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 64)
            self.assertIn("MODEL_SHA256_MISMATCH", proc.stderr)
            self.assertFalse((artifacts / "local-model.json").exists())

    def test_wrong_preload_runtime_hash_rejects_before_runtime(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            _, _, artifacts, env = self.fixture(td)
            env["CLAY_LLAMA_SERVER_SHA256"] = "f" * 64
            proc = subprocess.run(["bash", str(SCRIPT)], cwd=ROOT, env=env, text=True, capture_output=True)
            self.assertEqual(proc.returncode, 64)
            self.assertIn("RUNTIME_SHA256_MISMATCH", proc.stderr)
            self.assertFalse((artifacts / "local-model.json").exists())

    def test_postload_reported_model_mismatch_is_rejected_and_server_stopped(self):
        with tempfile.TemporaryDirectory() as raw:
            td = Path(raw)
            _, model, artifacts, env = self.fixture(td)
            wrong = td / "other.gguf"
            wrong.write_bytes(model.read_bytes())
            env["FAKE_REPORT_MODEL_PATH"] = str(wrong)
            proc = subprocess.run(["bash", str(SCRIPT)], cwd=ROOT, env=env, text=True, capture_output=True, timeout=10)
            self.assertEqual(proc.returncode, 65, proc.stderr)
            state = json.loads((artifacts / "local-model.json").read_text(encoding="utf-8"))
            self.assertEqual(state["state"], "READY_IDENTITY_REJECTED")
            self.assertFalse(state["identity_admitted_prerequisite"])
            self.assertFalse(state["model_path_matches_expected"])
            self.assertFalse(state["loader_consumption_attestation"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
