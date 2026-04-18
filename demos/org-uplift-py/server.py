"""
Standalone FastAPI server for Org-Uplift demo.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import execute_task, compute_stats

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Org-Uplift", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "org-uplift"}


@app.post("/api/org_uplift")
async def org_uplift(action: str = "execute", body: dict = Body(default={})):
    if action == "execute":
        return execute_task(
            task_description=body.get("task", ""),
            context=body.get("context", ""),
            player=body.get("player", ""),
            scenario=body.get("scenario", "startup"),
        )
    if action == "stats":
        return compute_stats(body.get("tasks") or [])
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
