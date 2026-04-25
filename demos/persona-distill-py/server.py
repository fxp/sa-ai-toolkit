"""Standalone FastAPI for Persona Distill demo."""
from __future__ import annotations
import base64
import pathlib
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from core import (
    search_persona, extract_patterns, distill_skill, package_zip,
    parse_skill, generate_with_skill, run_full,
)

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Persona Distill", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "persona-distill"}


# ── Distill flow ──────────────────────────────────────────────────

@app.post("/api/persona")
async def persona_post(action: str = Query("distill"), body: dict = Body(default={})):
    company = (body.get("company") or "").strip()
    person = (body.get("person") or "").strip() or None

    if action == "search":
        if not company and not person:
            raise HTTPException(400, "company or person required")
        return search_persona(company or person, person if company else None)

    if action == "distill":
        if not company and not person:
            raise HTTPException(400, "company or person required")
        sr = body.get("search_results") or search_persona(company or person, person if company else None)
        pat = extract_patterns(sr)
        out = distill_skill(company or person, person, pat, search_results=sr)
        return {
            "search": sr,
            "patterns": {k: v for k, v in pat.items() if k != "sources"},
            "n_sources": pat.get("n_sources", 0),
            "skill": {
                "slug": out["slug"],
                "persona_label": out["persona_label"],
                "skill_md": out["skill_md"],
                "references_md": out["references_md"],
                "meta": out["meta"],
            },
        }

    if action == "full":
        if not company and not person:
            raise HTTPException(400, "company or person required")
        return run_full(company or person, person if company else None)

    if action == "use":
        skill_md = (body.get("skill_md") or "").strip()
        user_input = (body.get("input") or "").strip()
        mode = body.get("mode", "advise")
        if not skill_md or not user_input:
            raise HTTPException(400, "skill_md and input required")
        return generate_with_skill(skill_md, user_input, mode=mode)

    if action == "parse":
        skill_md = (body.get("skill_md") or "").strip()
        if not skill_md:
            raise HTTPException(400, "skill_md required")
        return parse_skill(skill_md)

    raise HTTPException(400, f"unknown action: {action}")


@app.post("/api/persona/zip")
async def persona_zip(body: dict = Body(default={})):
    """Build distilled bundle and stream as application/zip."""
    company = (body.get("company") or "").strip()
    person = (body.get("person") or "").strip() or None
    if not company and not person:
        raise HTTPException(400, "company or person required")
    sr = body.get("search_results") or search_persona(company or person, person if company else None)
    pat = extract_patterns(sr)
    out = distill_skill(company or person, person, pat, search_results=sr)
    zbytes = package_zip(out)
    headers = {
        "Content-Disposition": f'attachment; filename="{out["slug"]}.skill.zip"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }
    return Response(content=zbytes, media_type="application/zip", headers=headers)


# Static frontend
if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
