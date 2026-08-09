from pathlib import Path

_here = Path(__file__).resolve().parent
_parts = sorted((_here / "parts").glob("run_proof_suite.part*"))
if not _parts:
    raise RuntimeError("ClayCode BASE proof parts missing")
_source = "".join(p.read_text() for p in _parts)
exec(compile(_source, str(_here / "run_proof_suite.concatenated.py"), "exec"), globals(), globals())
