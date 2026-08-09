from pathlib import Path

_here = Path(__file__).resolve().parent
_parts = sorted((_here / "parts").glob("claycode_base.part*"))
if not _parts:
    raise RuntimeError("ClayCode BASE source parts missing")
_source = "".join(p.read_text() for p in _parts)
exec(compile(_source, str(_here / "claycode_base.concatenated.py"), "exec"), globals(), globals())
