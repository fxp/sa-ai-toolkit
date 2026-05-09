"""
Standalone FastAPI server for Karpathy KB demo.
Mounts docs/karpathy-kb/ as static site + /api/karpathy endpoints.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import extract_concepts, lint_kb, build_graph, compare_concepts, compile_brief

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Karpathy KB", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "karpathy-kb"}


@app.post("/api/karpathy")
async def karpathy(action: str = "extract", body: dict = Body(default={})):
    if action == "extract":
        text = body.get("text") or ""
        n = int(body.get("n", 5))
        return {"concepts": extract_concepts(text, n=n)}
    if action == "lint":
        concepts = body.get("concepts") or []
        return lint_kb(concepts)
    if action == "graph":
        # Frontend reads data.nodes / data.edges / data.type_counts /
        # data.num_contradictions for the cytoscape view.
        concepts = body.get("concepts") or []
        return build_graph(concepts)
    if action == "compare":
        # Frontend reads data.selected / data.metrics / data.rowcount
        concepts = body.get("concepts") or []
        names = body.get("names") or []
        return compare_concepts(concepts, names)
    if action == "brief":
        concepts = body.get("concepts") or []
        name = body.get("name") or ""
        lang = body.get("lang") or "en"
        return {"brief_md": compile_brief(concepts, name, lang=lang),
                "name": name, "lang": lang}
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
