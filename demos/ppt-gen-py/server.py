"""
Standalone FastAPI server for PPT-Gen demo.
"""
from __future__ import annotations
import base64
import pathlib
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import generate_pptx

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="PPT-Gen", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "ppt-gen"}


@app.post("/api/ppt")
async def ppt(body: dict = Body(default={})):
    pptx_bytes = generate_pptx(
        title=body.get("title", "Untitled"),
        subtitle=body.get("subtitle", ""),
        slides=body.get("slides") or [],
        theme=body.get("theme", "blue-orange"),
    )
    return {
        "filename": body.get("filename") or "deck.pptx",
        "pptx_base64": base64.b64encode(pptx_bytes).decode("ascii"),
        "size": len(pptx_bytes),
    }


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
