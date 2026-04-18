"""
Standalone FastAPI server for Enterprise Gen demo.
Mounts docs/enterprise-gen/ as static site + /api/enterprise endpoints.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import core as _core
from core import score_demos

try:
    from core import generate_package  # type: ignore
except ImportError:  # pragma: no cover
    generate_package = None  # type: ignore

try:
    from core import build_profile_markdown  # type: ignore
except ImportError:  # pragma: no cover
    build_profile_markdown = None  # type: ignore

try:
    from core import build_matrix_markdown  # type: ignore
except ImportError:  # pragma: no cover
    build_matrix_markdown = None  # type: ignore

try:
    from core import build_schedule_markdown  # type: ignore
except ImportError:  # pragma: no cover
    build_schedule_markdown = None  # type: ignore

try:
    from core import build_runbook_markdown  # type: ignore
except ImportError:  # pragma: no cover
    build_runbook_markdown = None  # type: ignore

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Enterprise Gen", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "enterprise-gen"}


@app.post("/api/enterprise")
async def enterprise(action: str = "score", body: dict = Body(default={})):
    profile = body.get("profile") or body
    if action == "score":
        return {"scored": score_demos(profile)}
    if action == "generate":
        if hasattr(_core, "generate_package"):
            return _core.generate_package(profile)
        return {
            "profile_md": build_profile_markdown(profile) if build_profile_markdown else "",
            "scored": score_demos(profile),
            "matrix_md": build_matrix_markdown(profile) if build_matrix_markdown else "",
            "schedule_md": build_schedule_markdown(profile) if build_schedule_markdown else "",
            "runbook_md": build_runbook_markdown(profile) if build_runbook_markdown else "",
        }
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
