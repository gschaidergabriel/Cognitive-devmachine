#!/usr/bin/env python3
import base64
import hashlib
import json
import os
import pathlib
import re
import shutil
import statistics
import struct
import subprocess
import sys
import threading
import time
import urllib.request
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
EXP = ROOT / "research_entity/experiments/qwen35_abliteration_vps"
CASES_PATH = EXP / "BENCHMARK_CASES_V1.json"
CACHE = pathlib.Path.home() / ".cache/clay-qwen35-challenger"
CACHE.mkdir(parents=True, exist_ok=True)
EXP.mkdir(parents=True, exist_ok=True)

BASELINE_URL = "https://huggingface.co/mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF/resolve/main/Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf"
CHALLENGER_URL = "https://huggingface.co/kaineone/Qwen3.5-4B-abliterated-GGUF/resolve/main/KAINE-Qwen3.5-4B-abliterated.Q4_K_M.gguf"
MMPROJ_URL = "https://huggingface.co/mradermacher/Huihui-Qwen3.5-4B-abliterated-GGUF/resolve/main/Huihui-Qwen3.5-4B-abliterated.mmproj-Q8_0.gguf"


def sh(cmd, timeout=None, check=True, cwd=None):
    p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, cwd=cwd)
    if check and p.returncode != 0:
        raise RuntimeError(f"command failed {cmd}: {p.stderr[-4000:]}")
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8 * 1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def free_bytes(path):
    return shutil.disk_usage(path).free


def download(url, dest):
    dest = pathlib.Path(dest)
    if dest.exists() and dest.stat().st_size > 1_000_000_000:
        return dest
    if free_bytes(CACHE) < 7_000_000_000:
        raise RuntimeError("insufficient free disk for matched model downloads")
    tmp = dest.with_suffix(dest.suffix + ".part")
    cmd = ["curl", "-L", "--fail", "--retry", "4", "--retry-delay", "2", "--continue-at", "-", "-o", str(tmp), url]
    sh(cmd, timeout=3600)
    tmp.rename(dest)
    return dest


def find_local_baseline():
    roots = [pathlib.Path.home(), pathlib.Path("/opt"), pathlib.Path("/srv"), pathlib.Path("/mnt"), pathlib.Path("/var/lib")]
    patterns = [
        re.compile(r"v26\.1.*q4_k_m.*\.gguf$", re.I),
        re.compile(r"frank.*q4_k_m.*\.gguf$", re.I),
        re.compile(r"huihui-qwen3\.5-4b-abliterated.*q4_k_m.*\.gguf$", re.I),
    ]
    candidates = []
    for root in roots:
        if not root.exists():
            continue
        try:
            p = sh(["find", str(root), "-maxdepth", "6", "-type", "f", "-name", "*.gguf", "-print"], timeout=50, check=False)
        except Exception:
            continue
        for line in p.stdout.splitlines():
            low = line.lower()
            if "mmproj" in low or "kaine-qwen" in low:
                continue
            path = pathlib.Path(line)
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size < 1_500_000_000:
                continue
            for rank, pat in enumerate(patterns):
                if pat.search(path.name):
                    candidates.append((rank, -path.stat().st_mtime, path))
                    break
    if candidates:
        candidates.sort(key=lambda x: (x[0], x[1], str(x[2])))
        return candidates[0][2]
    return None


def find_bin(name):
    p = shutil.which(name)
    if p:
        return pathlib.Path(p)
    guesses = [
        pathlib.Path.home()/"llama.cpp/build/bin"/name,
        pathlib.Path.home()/"llama.cpp/build/bin/Release"/name,
        pathlib.Path("/opt/llama.cpp/build/bin")/name,
        pathlib.Path("/usr/local/bin")/name,
    ]
    for g in guesses:
        if g.exists() and os.access(g, os.X_OK):
            return g
    return None


def ensure_llama_server():
    server = find_bin("llama-server")
    if server:
        return server, "preinstalled", sh([str(server), "--version"], check=False).stdout.strip()
    src = CACHE / "llama.cpp"
    if not src.exists():
        sh(["git", "clone", "--depth", "1", "https://github.com/ggml-org/llama.cpp.git", str(src)], timeout=300)
    else:
        sh(["git", "fetch", "--depth", "1", "origin", "master"], timeout=120, check=False, cwd=src)
        sh(["git", "reset", "--hard", "origin/master"], timeout=60, check=False, cwd=src)
    sh(["cmake", "-B", "build", "-DCMAKE_BUILD_TYPE=Release", "-DGGML_NATIVE=ON"], timeout=300, cwd=src)
    jobs = str(max(1, min(os.cpu_count() or 2, 8)))
    sh(["cmake", "--build", "build", "--config", "Release", "-j", jobs, "--target", "llama-server"], timeout=900, cwd=src)
    server = src / "build/bin/llama-server"
    if not server.exists():
        server = src / "build/bin/Release/llama-server"
    commit = sh(["git", "rev-parse", "HEAD"], cwd=src).stdout.strip()
    version = sh([str(server), "--version"], check=False).stdout.strip()
    return server, commit, version


def png_solid(rgb, w=224, h=224):
    raw = b"".join(b"\x00" + bytes(rgb) * w for _ in range(h))
    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    return b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b"")


def http_json(url, payload=None, timeout=180):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def wait_health(port, proc, timeout=180):
    end = time.time() + timeout
    last = None
    while time.time() < end:
        if proc.poll() is not None:
            raise RuntimeError(f"llama-server exited early rc={proc.returncode}")
        try:
            last = http_json(f"http://127.0.0.1:{port}/health", timeout=3)
            if last.get("status") in ("ok", "no slot available"):
                return last
        except Exception:
            pass
        time.sleep(1)
    raise RuntimeError(f"llama-server health timeout; last={last}")


def normalize(s):
    return s.strip().replace("\r\n", "\n")


def score_case(case, text):
    text = normalize(text)
    if "expect_exact" in case:
        return text == case["expect_exact"]
    if "expect_regex" in case:
        return re.fullmatch(case["expect_regex"], text) is not None
    if "expect_json" in case:
        try:
            return json.loads(text) == case["expect_json"]
        except Exception:
            return False
    return False


def rss_kib(pid):
    try:
        with open(f"/proc/{pid}/status") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    return int(line.split()[1])
    except Exception:
        return None


def run_model(label, model_path, mmproj_path, cases, port, server, threads):
    log_path = EXP / f"server_{label}.log"
    log = open(log_path, "w", encoding="utf-8")
    cmd = [str(server), "-m", str(model_path), "--mmproj", str(mmproj_path), "--host", "127.0.0.1", "--port", str(port), "-c", "4096", "-t", str(threads), "--jinja"]
    start = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, text=True)
    peak = 0
    stop_mon = False
    def monitor():
        nonlocal peak
        while not stop_mon and proc.poll() is None:
            r = rss_kib(proc.pid)
            if r is not None:
                peak = max(peak, r)
            time.sleep(0.1)
    mt = threading.Thread(target=monitor, daemon=True); mt.start()
    rows = []
    try:
        wait_health(port, proc)
        startup_s = time.perf_counter() - start
        colors = {
            "generated:red": png_solid((255,0,0)),
            "generated:green": png_solid((0,255,0)),
            "generated:blue": png_solid((0,0,255)),
        }
        all_cases = [(c, False) for c in cases["cases"]] + [(c, True) for c in cases.get("vision_cases", [])]
        for case, is_vision in all_cases:
            if is_vision:
                b64 = base64.b64encode(colors[case["image"]]).decode("ascii")
                content = [
                    {"type":"text", "text":case["prompt"]},
                    {"type":"image_url", "image_url":{"url":"data:image/png;base64,"+b64}},
                ]
            else:
                content = case["prompt"]
            payload = {
                "model":"local",
                "messages":[{"role":"user","content":content}],
                "temperature":cases["generation"]["temperature"],
                "seed":cases["generation"]["seed"],
                "max_tokens":cases["generation"]["max_tokens"],
                "chat_template_kwargs":{"enable_thinking":False},
            }
            t0 = time.perf_counter()
            err = None; resp = None; out = ""
            try:
                resp = http_json(f"http://127.0.0.1:{port}/v1/chat/completions", payload, timeout=240)
                out = resp["choices"][0]["message"].get("content") or ""
            except Exception as e:
                err = f"{type(e).__name__}:{e}"
            wall = time.perf_counter() - t0
            ok = False if err else score_case(case, out)
            rows.append({
                "case_id":case["id"], "vision":is_vision, "passed":ok,
                "wall_s":wall, "output":out, "error":err,
                "usage": None if resp is None else resp.get("usage"),
                "timings": None if resp is None else resp.get("timings"),
            })
        return {"label":label, "startup_s":startup_s, "peak_rss_kib":peak, "rows":rows}
    finally:
        stop_mon = True
        try:
            proc.terminate(); proc.wait(timeout=20)
        except Exception:
            try: proc.kill()
            except Exception: pass
        mt.join(timeout=2)
        log.close()


def p95(vals):
    if not vals: return None
    vals=sorted(vals)
    return vals[max(0, min(len(vals)-1, int(round(0.95*(len(vals)-1)))))]


def summarize(r):
    rows=r["rows"]
    text=[x for x in rows if not x["vision"]]
    vision=[x for x in rows if x["vision"]]
    good=[x for x in rows if x["error"] is None]
    walls=[x["wall_s"] for x in good]
    def frac(xs): return None if not xs else sum(bool(x["passed"]) for x in xs)/len(xs)
    return {
        "total":len(rows), "passed":sum(bool(x["passed"]) for x in rows), "accuracy":frac(rows),
        "text_accuracy":frac(text), "vision_accuracy":frac(vision),
        "errors":sum(x["error"] is not None for x in rows),
        "median_wall_s":statistics.median(walls) if walls else None,
        "p95_wall_s":p95(walls), "startup_s":r["startup_s"], "peak_rss_kib":r["peak_rss_kib"]
    }


def main():
    observed_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cases = json.loads(CASES_PATH.read_text())
    server, llama_source, llama_version = ensure_llama_server()
    baseline_local = find_local_baseline()
    if baseline_local:
        baseline = baseline_local
        baseline_source = "LOCAL_CURRENT_CANDIDATE"
    else:
        baseline = download(BASELINE_URL, CACHE/"Huihui-Qwen3.5-4B-abliterated.Q4_K_M.gguf")
        baseline_source = "PUBLIC_HUIHUI_FALLBACK"
    challenger = download(CHALLENGER_URL, CACHE/"KAINE-Qwen3.5-4B-abliterated.Q4_K_M.gguf")
    mmproj = download(MMPROJ_URL, CACHE/"Huihui-Qwen3.5-4B-abliterated.mmproj-Q8_0.gguf")
    threads = max(1, min(os.cpu_count() or 2, 16))
    meta = {
        "schema_version":"1.0", "kind":"QWEN35_ABLITERATION_MATCHED_VPS_BENCHMARK",
        "observed_at":observed_at, "github_run_id":os.environ.get("GITHUB_RUN_ID"), "github_sha":os.environ.get("GITHUB_SHA"),
        "runner_name":os.environ.get("RUNNER_NAME"), "runner_os":os.environ.get("RUNNER_OS"),
        "llama_server":str(server), "llama_source":llama_source, "llama_version":llama_version,
        "threads":threads, "baseline_source":baseline_source,
        "baseline":{"path":str(baseline),"size_bytes":baseline.stat().st_size,"sha256":sha256(baseline)},
        "challenger":{"path":str(challenger),"size_bytes":challenger.stat().st_size,"sha256":sha256(challenger)},
        "mmproj":{"path":str(mmproj),"size_bytes":mmproj.stat().st_size,"sha256":sha256(mmproj)},
        "cases_sha256":sha256(CASES_PATH),
    }
    results=[]
    results.append(run_model("baseline", baseline, mmproj, cases, 18101, server, threads))
    results.append(run_model("challenger", challenger, mmproj, cases, 18102, server, threads))
    sums={r["label"]:summarize(r) for r in results}
    b=sums["baseline"]; c=sums["challenger"]
    comparable_baseline = baseline_source == "LOCAL_CURRENT_CANDIDATE"
    no_quality_regression = (c["accuracy"] is not None and b["accuracy"] is not None and c["accuracy"] >= b["accuracy"] and (c["vision_accuracy"] or 0) >= (b["vision_accuracy"] or 0))
    resource_ok = (c["peak_rss_kib"] <= max(1,b["peak_rss_kib"])*1.10 and c["median_wall_s"] <= max(0.001,b["median_wall_s"])*1.15)
    better = no_quality_regression and resource_ok and (c["accuracy"] > b["accuracy"] or c["median_wall_s"] < b["median_wall_s"]*0.95)
    if comparable_baseline and better:
        verdict="CHALLENGER_SUPPORTED_FOR_DEEPER_FRANK_EVAL_NOT_PROMOTED"
    elif not comparable_baseline and better:
        verdict="CHALLENGER_SUPPORTED_VS_PUBLIC_HUIHUI_ONLY_CURRENT_FRANK_BASELINE_MISSING"
    elif no_quality_regression and resource_ok:
        verdict="NO_CLEAR_WIN_DEEPER_EVAL_OPTIONAL"
    else:
        verdict="CHALLENGER_NOT_SUPPORTED_BY_THIS_SCREEN"
    receipt={"meta":meta,"summary":sums,"verdict":verdict,"promotion":False,"results":results}
    (EXP/"VPS_BENCHMARK_RECEIPT_CURRENT.json").write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n")
    md=["# Qwen3.5 4B Abliteration VPS Challenger — matched screen", "", f"Observed: {observed_at}", f"Baseline source: **{baseline_source}**", f"Verdict: **{verdict}**", "", "| model | total | passed | accuracy | text | vision | median s | p95 s | peak RSS KiB |", "|---|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for key in ["baseline","challenger"]:
        s=sums[key]
        md.append(f"| {key} | {s['total']} | {s['passed']} | {s['accuracy']:.3f} | {s['text_accuracy']:.3f} | {s['vision_accuracy']:.3f} | {s['median_wall_s']:.3f} | {s['p95_wall_s']:.3f} | {s['peak_rss_kib']} |")
    md += ["", "This is a promotion **screen**, not final model promotion evidence. A public Huihui fallback is explicitly weaker evidence than the exact current Frank v26.1/local GGUF.", "", "Exact hashes and per-case rows are in `VPS_BENCHMARK_RECEIPT_CURRENT.json`."]
    (EXP/"VPS_BENCHMARK_REPORT_CURRENT.md").write_text("\n".join(md)+"\n")
    print(json.dumps({"summary":sums,"verdict":verdict},indent=2))

if __name__ == "__main__":
    main()
