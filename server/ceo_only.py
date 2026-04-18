"""Minimal CEO-only FastAPI shim for local smoke testing the dashboard.
Mounts /api/ceo and serves docs/ as static. Not used in production."""
from __future__ import annotations
import sys, os, pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "demos" / "ceo-agent-py"))
from core import CEOAgent, ask_chips  # noqa: E402

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/ceo")
async def ceo(action: str = "all", company: str = "NewCo Inc", lang: str = "en", idx: int = 0):
    agent = CEOAgent(company=company)
    if action == "brief": return {"company": company, "idx": idx, "lang": lang, "brief": agent.morning_brief(brief_idx=idx, lang=lang)}
    if action == "metrics": return agent.metrics(lang=lang)
    if action == "decisions": return {"decisions": agent.decisions(lang=lang)}
    if action == "mood": return agent.mood_heatmap(lang=lang)
    if action == "competitors": return {"feed": agent.competitor_feed(lang=lang)}
    if action == "actions": return {"actions": agent.action_queue(lang=lang)}
    if action == "chips": return {"chips": ask_chips(lang=lang)}
    if action == "projects": return {"projects": agent.projects(lang=lang)}
    if action == "all": return agent.all(brief_idx=idx, lang=lang)
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


@app.get("/")
async def root():
    return RedirectResponse(url="/ceo-dashboard/")


app.mount("/", StaticFiles(directory=str(ROOT / "docs"), html=True), name="docs")
