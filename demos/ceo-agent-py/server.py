"""
Standalone FastAPI server for CEO Agent.
Mounts docs/ceo-dashboard/ as static site + /api/ceo endpoints.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from core import CEOAgent
try:
    from core import ask_chips  # type: ignore
except ImportError:  # pragma: no cover
    ask_chips = None  # type: ignore

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="CEO Agent", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/health")
async def health():
    return {"status": "ok", "demo": "ceo-agent"}


@app.get("/api/ceo")
async def ceo(action: str = "all", company: str = "NewCo Inc", lang: str = "en", idx: int = 0):
    agent = CEOAgent(company=company)
    if action == "brief":
        return {"company": company, "idx": idx, "lang": lang, "brief": agent.morning_brief(brief_idx=idx, lang=lang)}
    if action == "metrics":
        return agent.metrics(lang=lang)
    if action == "decisions":
        return {"decisions": agent.decisions(lang=lang)}
    if action == "mood":
        return agent.mood_heatmap(lang=lang)
    if action == "competitors":
        return {"feed": agent.competitor_feed(lang=lang)}
    if action == "actions":
        return {"actions": agent.action_queue(lang=lang)}
    if action == "chips":
        if ask_chips is None:
            raise HTTPException(501, "ask_chips not available in this build")
        return {"chips": ask_chips(lang=lang)}
    if action == "projects":
        return {"projects": agent.projects(lang=lang)}
    if action == "all":
        return agent.all(brief_idx=idx, lang=lang)
    raise HTTPException(400, f"unknown action {action}")


@app.post("/api/ceo")
async def ceo_post(action: str = "ask", body: dict = Body(default={})):
    agent = CEOAgent(company=body.get("company", "NewCo Inc"))
    lang = body.get("lang", "en")
    if action == "ask":
        return agent.ask(query=body.get("query", ""), lang=lang)
    if action == "project":
        detail = agent.project_detail(project_id=body.get("id", ""), lang=lang)
        if detail is None:
            raise HTTPException(404, f"project not found: {body.get('id')}")
        return detail
    raise HTTPException(400, f"unknown action {action}")


if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
