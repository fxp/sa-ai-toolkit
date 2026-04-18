"""
Standalone FastAPI server for AutoResearch demo.
Mounts docs/autoresearch/ as static site + /api/research endpoints.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import (
    run_iteration,
    run_full,
    get_instance_payload,
    get_program_md,
    NUM_ITERATIONS,
    VARIANTS,
)

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="AutoResearch", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "autoresearch"}


@app.post("/api/research")
async def research_post(action: str = "iterate", body: dict = Body(default={})):
    lang = body.get("lang", "en")
    if action == "iterate":
        iter_idx = int(body.get("iter_idx", 0))
        return run_iteration(iter_idx, lang=lang)
    if action == "full":
        return run_full(lang=lang)
    raise HTTPException(400, f"unknown action {action}")


@app.get("/api/research")
async def research_get(action: str = "instance", lang: str = "en"):
    if action == "instance":
        return {
            "instance": get_instance_payload(),
            "program_md": get_program_md(lang=lang),
            "num_iterations": NUM_ITERATIONS,
        }
    if action == "meta":
        return {
            "num_iterations": NUM_ITERATIONS,
            "variants": [
                {"idx": v["idx"], "name": v["name"], "name_zh": v["name_zh"],
                 "hypothesis": v["hypothesis"], "hypothesis_zh": v["hypothesis_zh"]}
                for v in VARIANTS
            ],
        }
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
