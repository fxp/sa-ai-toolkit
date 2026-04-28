"""Standalone FastAPI for Persona Distill demo."""
from __future__ import annotations
import base64
import os
import pathlib
from fastapi import FastAPI, HTTPException, Body, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from core import (
    search_persona, extract_patterns, distill_skill, package_zip,
    parse_skill, generate_with_skill, run_full,
    format_for_repo, quality_check, submit_to_repo,
)

REPO_TARGET = os.environ.get("PERSONA_REPO", "fxp/persona-distill-skills")
REPO_BASE_BRANCH = os.environ.get("PERSONA_REPO_BRANCH", "main")

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

    if action == "format_for_repo":
        # Same input as 'distill', but renders in the repo's exact format
        if not company and not person:
            raise HTTPException(400, "company or person required")
        sr = body.get("search_results") or search_persona(company or person, person if company else None)
        pat = extract_patterns(sr)
        out = format_for_repo(company or person, person, pat, search_results=sr)
        qc = quality_check(out, pat)
        return {"skill": out, "quality": qc, "search": sr,
                "patterns": {k: v for k, v in pat.items() if k != "sources"}}

    if action == "submit":
        # Open a draft PR against fxp/persona-distill-skills
        token = os.environ.get("GITHUB_TOKEN")
        if not token:
            raise HTTPException(503, "GITHUB_TOKEN not configured on server")
        # Two ways to call: provide a precomputed bundle, or do it from scratch
        bundle = body.get("bundle")
        if not bundle:
            if not company and not person:
                raise HTTPException(400, "company/person or bundle required")
            sr = body.get("search_results") or search_persona(company or person, person if company else None)
            pat = extract_patterns(sr)
            bundle = format_for_repo(company or person, person, pat, search_results=sr)
            qc = quality_check(bundle, pat)
        else:
            # rebuild a tiny patterns dict from bundle.meta for QC
            pat_from_meta = {
                "n_sources": bundle.get("meta", {}).get("n_sources", 0),
                "quotes": [None] * bundle.get("meta", {}).get("n_quotes", 0),
                "decisions": [None] * bundle.get("meta", {}).get("n_decisions", 0),
                "frameworks": [None] * bundle.get("meta", {}).get("n_frameworks", 0),
                "principles": [None] * bundle.get("meta", {}).get("n_principles", 0),
            }
            qc = quality_check(bundle, pat_from_meta)
        # Soft gate: require at least 1 source. Caller can choose to ignore quality issues.
        if bundle.get("meta", {}).get("n_sources", 0) == 0:
            raise HTTPException(400, "no sources to submit; refusing")
        force = bool(body.get("force", False))
        if not force and not qc["passed"] and qc["score"] < 30:
            raise HTTPException(400, {"error": "quality_gate_failed", "quality": qc})
        try:
            pr = submit_to_repo(bundle, token,
                                repo=body.get("repo", REPO_TARGET),
                                base_branch=body.get("base_branch", REPO_BASE_BRANCH))
        except Exception as e:
            raise HTTPException(502, f"submit failed: {e}")
        return {"submitted": True, "quality": qc, "pull_request": pr,
                "repo": body.get("repo", REPO_TARGET)}

    raise HTTPException(400, f"unknown action: {action}")


@app.get("/api/persona/repo")
async def repo_info():
    """Tells the frontend whether submit is available, and where it goes."""
    return {
        "repo": REPO_TARGET,
        "base_branch": REPO_BASE_BRANCH,
        "submit_enabled": bool(os.environ.get("GITHUB_TOKEN")),
        "repo_url": f"https://github.com/{REPO_TARGET}",
    }


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
