"""
Standalone FastAPI server for GStack demo.
Mounts docs/gstack/ as static site + /api/gstack endpoint.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import run_command, run_turn

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="GStack", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "gstack"}


@app.get("/api/gstack")
async def gstack(command: str = Query(...), input: str | None = None):
    """Legacy one-shot endpoint — returns the entire scripted flow."""
    return {"command": command, "script": run_command(command, user_input=input)}


@app.post("/api/gstack")
async def gstack_turn(body: dict = Body(default={})):
    """Multi-turn endpoint.

    body = {command: str, turn: int, input: str|null, history: [{role, text}, ...]}
    Returns: {script, prompt, done, turn, total_turns}
    """
    command = body.get("command") or ""
    turn = int(body.get("turn") or 0)
    user_input = body.get("input")
    history = body.get("history") or []
    return run_turn(command=command, turn=turn, user_input=user_input, history=history)


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
