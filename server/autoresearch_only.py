"""Minimal autoresearch-only FastAPI shim for local smoke testing.
Mounts /api/research and serves docs/ as static."""
from __future__ import annotations
import sys, pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

ROOT = pathlib.Path(__file__).resolve().parent.parent

# Load both autoresearch cores with distinct module names to avoid import collision.
import importlib.util
def _load(slug: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(slug, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[slug] = mod  # Python 3.14 dataclass needs this
    spec.loader.exec_module(mod)
    return mod

core = _load("autoresearch_sched", ROOT / "demos" / "autoresearch-py" / "core.py")
vrp_core = _load("autoresearch_vrp", ROOT / "demos" / "autoresearch-vrp-py" / "core.py")

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.post("/api/research")
async def research_post(action: str = "iterate", body: dict = Body(default={})):
    lang = body.get("lang", "en")
    if action == "iterate":
        iter_idx = int(body.get("iter_idx", 0))
        return core.run_iteration(iter_idx, lang=lang)
    if action == "full":
        return core.run_full(lang=lang)
    raise HTTPException(400, f"unknown action {action}")


@app.get("/api/research")
async def research_get(action: str = "instance", lang: str = "en"):
    if action == "instance":
        return {
            "instance": core.get_instance_payload(),
            "program_md": core.get_program_md(lang=lang),
            "num_iterations": core.NUM_ITERATIONS,
        }
    if action == "meta":
        return {
            "num_iterations": core.NUM_ITERATIONS,
            "variants": [
                {"idx": v["idx"], "name": v["name"], "name_zh": v["name_zh"],
                 "hypothesis": v["hypothesis"], "hypothesis_zh": v["hypothesis_zh"]}
                for v in core.VARIANTS
            ],
        }
    raise HTTPException(400, f"unknown action {action}")


# ---- VRP (demo B) ----
@app.post("/api/vrp")
async def vrp_post(action: str = "iterate", body: dict = Body(default={})):
    lang = body.get("lang", "en")
    if action == "iterate":
        return vrp_core.run_iteration(int(body.get("iter_idx", 0)), lang=lang)
    if action == "full":
        return vrp_core.run_full(lang=lang)
    raise HTTPException(400, f"unknown action {action}")


@app.get("/api/vrp")
async def vrp_get(action: str = "instance", lang: str = "en"):
    if action == "instance":
        return {
            "instance": vrp_core.get_instance_payload(),
            "program_md": vrp_core.get_program_md(lang=lang),
            "num_iterations": vrp_core.NUM_ITERATIONS,
        }
    if action == "meta":
        return {
            "num_iterations": vrp_core.NUM_ITERATIONS,
            "variants": [
                {"idx": v["idx"], "name": v["name"], "name_zh": v["name_zh"],
                 "hypothesis": v["hypothesis"], "hypothesis_zh": v["hypothesis_zh"]}
                for v in vrp_core.VARIANTS
            ],
        }
    raise HTTPException(400, f"unknown action {action}")


@app.get("/")
async def root():
    return RedirectResponse(url="/autoresearch/")


app.mount("/", StaticFiles(directory=str(ROOT / "docs"), html=True), name="docs")
