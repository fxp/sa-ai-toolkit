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
        # Frontend reads pkg.snapshot/profile/scoring/schedule/opening_remarks/
        # selected at root, so return the package directly (don't wrap).
        company = body.get("company") or "Acme Inc"
        info = search_company(company)
        pkg = generate_package(info) if generate_package else {"profile": info}
        if isinstance(pkg, dict):
            pkg.setdefault("company_info", info)
        return pkg
    if action == "customize":
        # Frontend posts {package, action, params} where action ∈
        # {"replace","deepen","audience"}. Server originally only read
        # body.sub_action with long names — accept both, and wrap the
        # response as {package: ...} per the frontend's `out.package`.
        pkg = body.get("package") or {}
        act = body.get("action") or body.get("sub_action") or body.get("act") or "replace"
        params = body.get("params") or {}
        ALIASES = {"replace": "replace_terms", "deepen": "deepen_demo",
                   "audience": "switch_audience"}
        act = ALIASES.get(act, act)
        if act == "replace_terms":
            updated = replace_terms(pkg, params.get("mapping") or {})
        elif act == "deepen_demo":
            updated = deepen_demo(pkg, params.get("demo_id", ""))
        elif act == "switch_audience":
            updated = switch_audience(pkg, params.get("audience", "executives"))
        else:
            raise HTTPException(400, f"unknown customize action {act}")
        return {"package": updated, "action": act}
    if action == "present":
        # Frontend reads `out.plays` (rehearse) and `out.email`.
        pkg = body.get("package") or {}
        mode = body.get("mode") or "rehearse"
        if mode == "rehearse":
            return {"plays": rehearse(pkg)}
        if mode == "email":
            return {"email": export_email(pkg)}
        raise HTTPException(400, f"unknown mode {mode}")
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
