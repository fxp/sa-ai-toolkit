"""
Standalone FastAPI server for SA Toolkit demo.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import (
    search_company,
    generate_package,
    replace_terms,
    deepen_demo,
    switch_audience,
    rehearse,
    export_email,
)

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="SA Toolkit", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "sa-toolkit"}


@app.post("/api/sa_toolkit")
async def sa_toolkit(action: str = "gen", body: dict = Body(default={})):
    if action == "gen":
        company = body.get("company") or "Acme Inc"
        info = search_company(company)
        pkg = generate_package(info) if generate_package else {"profile": info}
        return {"company_info": info, "package": pkg}
    if action == "customize":
        pkg = body.get("package") or {}
        act = body.get("sub_action") or body.get("act") or "replace_terms"
        params = body.get("params") or {}
        if act == "replace_terms":
            return replace_terms(pkg, params.get("mapping") or {})
        if act == "deepen_demo":
            return deepen_demo(pkg, params.get("demo_id", ""))
        if act == "switch_audience":
            return switch_audience(pkg, params.get("audience", "executives"))
        raise HTTPException(400, f"unknown sub_action {act}")
    if action == "present":
        pkg = body.get("package") or {}
        mode = body.get("mode") or "rehearse"
        if mode == "rehearse":
            return {"plan": rehearse(pkg)}
        if mode == "email":
            return {"email": export_email(pkg)}
        raise HTTPException(400, f"unknown mode {mode}")
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
