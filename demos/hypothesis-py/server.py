"""
Standalone FastAPI server for Hypothesis demo.
Mounts docs/hypothesis/ as static site + /api/hypothesis endpoint.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import classify_sentences

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Hypothesis", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "hypothesis"}


@app.post("/api/hypothesis")
async def hypothesis(body: dict = Body(default={})):
    text = body.get("text") or ""
    return {"annotations": classify_sentences(text)}


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
