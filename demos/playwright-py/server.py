"""
Standalone FastAPI server for Playwright demo.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import simulate_run, SCENARIOS

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Playwright", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "playwright"}


@app.get("/api/playwright")
async def playwright(scenario: str = "bing"):
    trace = simulate_run(scenario)
    meta = SCENARIOS.get(scenario, {}) if isinstance(SCENARIOS, dict) else {}
    return {
        "scenario": scenario,
        "title": meta.get("title", scenario),
        "script": meta.get("script", []),
        "trace": trace,
    }


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
