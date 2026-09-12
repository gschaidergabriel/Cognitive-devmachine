#!/usr/bin/env python3
"""Root-cause-fixed runner for body_webgl_gate.py.

The v1 gate used JS constants SW/SH from inside GLSL.  GLSL has a separate
namespace, so Chrome correctly rejected the vertex shader.  This runner reuses
v1 verbatim except for injecting explicit GLSL source dimensions before shader
compilation.  It is scratch-only and never mutates the live avatar.
"""
from __future__ import annotations
import argparse, html as htmlmod, importlib.util, json, pathlib, re, subprocess, tempfile


def load_base(path: pathlib.Path):
    spec = importlib.util.spec_from_file_location("body_webgl_gate_base", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-script", required=True)
    ap.add_argument("--visual-root", default=".")
    ap.add_argument("--chrome", default="/usr/bin/google-chrome")
    ap.add_argument("--scale", type=float, default=0.4036458333333333)
    args = ap.parse_args()

    base = load_base(pathlib.Path(args.base_script))
    root = pathlib.Path(args.visual_root).resolve()
    page = base.html(root, args.scale)
    old = "precision highp float;\nattribute vec2 a_src;"
    new = "precision highp float;\nconst float SW=1536.0; const float SH=1024.0;\nattribute vec2 a_src;"
    if old not in page:
        raise RuntimeError("expected vertex-shader header not found")
    page = page.replace(old, new, 1)

    with tempfile.TemporaryDirectory(prefix="body-webgl-v2-") as td:
        p = pathlib.Path(td) / "gate.html"
        p.write_text(page)
        r = subprocess.run(
            [args.chrome, "--headless=new", "--no-sandbox", "--allow-file-access-from-files",
             "--use-gl=angle", "--virtual-time-budget=120000", "--dump-dom", p.as_uri()],
            capture_output=True, text=True, timeout=190,
        )
        m = re.search(r"RESULT_JSON (\{.*?\})</body>", r.stdout, re.S)
        if not m:
            print(json.dumps({"status":"ERROR","chrome_rc":r.returncode,
                              "stdout_tail":r.stdout[-2500:],"stderr_tail":r.stderr[-2500:]}, sort_keys=True))
            return 2
        d = json.loads(htmlmod.unescape(m.group(1)))
        d["schema"] = "BODY_WEBGL_GATE/v2"
        d["root_cause_fix"] = "declare_SW_SH_inside_GLSL"
        d["live_mutation"] = False
        print(json.dumps(d, sort_keys=True))
        print("CHROME_RC", r.returncode)
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
