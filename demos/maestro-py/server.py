"""
Standalone FastAPI server for Maestro demo.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import parse_yaml, simulate_execution

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Maestro", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "maestro"}


@app.post("/api/maestro")
async def maestro(action: str = "parse", body: dict = Body(default={})):
    yaml_text = body.get("yaml") or ""
    parsed = parse_yaml(yaml_text)
    if action == "parse":
        return parsed
    if action == "simulate":
        return {"parsed": parsed, "trace": simulate_execution(parsed)}
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
