"""Shared OpenSCAD CLI helpers for this repo."""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCAD = ROOT / "leg-drawers.scad"
VARIANTS = ROOT / "variants.json"
OPENSCAD = Path(r"C:\Program Files\OpenSCAD\openscad.exe")


def load_variants() -> dict:
    return json.loads(VARIANTS.read_text(encoding="utf-8"))


def dash_d(params: dict, extra: dict | None = None) -> list[str]:
    merged = dict(params)
    if extra:
        merged.update(extra)
    args: list[str] = []
    for key, val in merged.items():
        if isinstance(val, bool):
            args += ["-D", f"{key}={'true' if val else 'false'}"]
        elif isinstance(val, str):
            args += ["-D", f'{key}="{val}"']
        else:
            args += ["-D", f"{key}={val}"]
    return args


def run_openscad(
    out: Path,
    params: dict,
    extra: dict | None = None,
    *,
    camera: str | None = None,
    imgsize: str = "1400,1050",
    projection: str | None = None,
    colorscheme: str = "Tomorrow Night",
    timeout: int = 180,
) -> subprocess.CompletedProcess:
    out.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(OPENSCAD), "-o", str(out), "--hardwarnings"]
    if out.suffix.lower() in {".png", ".gif"}:
        cmd += ["--imgsize", imgsize, "--autocenter", "--viewall"]
        if camera:
            cmd += ["--camera", camera]
        if projection:
            cmd += ["--projection", projection]
        cmd += ["--colorscheme", colorscheme]
    cmd += dash_d(params, extra)
    cmd.append(str(SCAD))
    env = {**os.environ, "OPENSCADPATH": str(ROOT)}
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
        env=env,
        cwd=str(ROOT),
    )
    return result


def parse_dims(stderr: str) -> dict:
    match = re.search(r'ECHO: "JSON:(\{.*\})"', stderr)
    if not match:
        raise ValueError(f"no DIMS JSON in OpenSCAD output:\n{stderr[-2000:]}")
    return json.loads(match.group(1))


def dims_for(params: dict) -> tuple[dict, str]:
    result = run_openscad(
        ROOT / "renders" / "_dims.stl",
        params,
        {"part": "dims"},
        timeout=60,
    )
    # dims part writes no geometry; OpenSCAD may still exit 0 with ECHO on stderr
    combined = (result.stdout or "") + "\n" + (result.stderr or "")
    if result.returncode != 0 and "JSON:" not in combined:
        raise RuntimeError(
            f"openscad dims failed ({result.returncode}):\n{combined[-3000:]}"
        )
    return parse_dims(combined), combined


if __name__ == "__main__":
    data = load_variants()
    vid = sys.argv[1] if len(sys.argv) > 1 else data["variants"][0]["id"]
    variant = next(v for v in data["variants"] if v["id"] == vid)
    dims, raw = dims_for(variant["params"])
    print(json.dumps({"id": vid, "dims": dims}, indent=2))
