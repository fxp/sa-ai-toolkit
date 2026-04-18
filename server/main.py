"""
FastAPI server — unified HTTP entry point for all 12 demos.
Mounts every demo's core.py and serves the docs/ static site.
"""
from __future__ import annotations
import sys, os, base64, importlib.util, pathlib
from typing import Any

from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

ROOT = pathlib.Path(__file__).resolve().parent.parent
DEMOS = ROOT / "demos"
DOCS = ROOT / "docs"

# ── Load each demo's core.py as a uniquely-named module (avoid clash on `core`) ──
def _load(demo: str):
    path = DEMOS / f"{demo}-py" / "core.py"
    spec = importlib.util.spec_from_file_location(f"demo_{demo.replace('-', '_')}", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

cores = {name: _load(name) for name in [
    "industrial-ai", "ceo-agent", "autoresearch", "enterprise-gen", "gstack",
    "hypothesis", "karpathy-kb", "maestro", "org-uplift", "playwright",
    "ppt-gen", "sa-toolkit",
]}

# ── App ──
app = FastAPI(title="SA AI Toolkit — 13 Demo Server", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ==========================
# 1. Industrial AI
# ==========================
@app.get("/api/industrial")
async def industrial_get(action: str = "health"):
    c = cores["industrial-ai"]
    if action == "health":
        return {"status": "ok", "pipeline": "industrial-ai-v1", "layers": ["SAM3", "SAM-Audio", "TimesFM", "LLM"]}
    if action == "detect":
        return {"visual": c.PerceptionLayer.detect_visual(), "audio": c.PerceptionLayer.detect_audio()}
    if action == "predict":
        return {"yield_forecast": c.PredictionLayer.forecast(None, 72, "yield"), "rul": c.PredictionLayer.predict_equipment_rul()}
    if action == "run":
        return c.run_pipeline(use_llm=False, verbose=False)
    raise HTTPException(400, f"unknown action {action}")

@app.post("/api/industrial")
async def industrial_post(action: str = "run", body: dict = Body(default={})):
    c = cores["industrial-ai"]
    if action == "run":
        return c.run_pipeline(use_llm=body.get("use_llm", False), verbose=False)
    if action == "diagnose":
        vis = body.get("visual") or c.PerceptionLayer.detect_visual()
        aud = body.get("audio") or c.PerceptionLayer.detect_audio()
        pred = body.get("prediction") or c.PredictionLayer.predict_equipment_rul()
        ont = body.get("ontology") or c.OntologyLayer.trace_root_cause("defect")
        return c.DiagnosisLayer.diagnose(vis, pred, ont, aud, body.get("use_llm", False))
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 2. CEO Agent
# ==========================
@app.get("/api/ceo")
async def ceo(action: str = "all", company: str = "NewCo Inc", lang: str = "en", idx: int = 0):
    CEOAgent = cores["ceo-agent"].CEOAgent
    agent = CEOAgent(company=company)
    if action == "brief": return agent.morning_brief(brief_idx=idx, lang=lang)
    if action == "metrics": return agent.metrics(lang=lang)
    if action == "decisions": return agent.decisions(lang=lang)
    if action == "mood": return agent.mood_heatmap(lang=lang)
    if action == "competitors": return agent.competitor_feed(lang=lang)
    if action == "actions": return agent.action_queue(lang=lang)
    if action == "all": return agent.all(brief_idx=idx, lang=lang)
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 3. AutoResearch
# ==========================
@app.post("/api/research")
async def research_post(action: str = "stage", body: dict = Body(default={})):
    c = cores["autoresearch"]
    if action == "stage":
        topic = body.get("topic") or ""
        stage_idx = int(body.get("stage_idx", 0))
        prev = body.get("prev_results") or []
        result = c.run_stage(topic, stage_idx, prev_results=prev)
        # If this is the final stage, attach the report
        try:
            total = len(c.STAGES) if hasattr(c, "STAGES") else 23
        except Exception:
            total = 23
        if stage_idx == total - 1:
            all_results = prev + [result]
            result["report"] = c.build_report(topic, all_results, lang=body.get("lang", "en"))
        return result
    raise HTTPException(400, f"unknown action {action}")

@app.get("/api/research")
async def research_get(action: str = "search", q: str = "", n: int = 5):
    c = cores["autoresearch"]
    if action == "search":
        results = c._search_duckduckgo(q, n=n) if hasattr(c, "_search_duckduckgo") else []
        return {"query": q, "results": results, "count": len(results)}
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 4. Enterprise Gen
# ==========================
@app.post("/api/enterprise")
async def enterprise(action: str = "score", body: dict = Body(default={})):
    c = cores["enterprise-gen"]
    profile = body.get("profile") or body
    if action == "score":
        return {"scored": c.score_demos(profile)}
    if action == "generate":
        return c.generate_package(profile) if hasattr(c, "generate_package") else {
            "profile_md": c.build_profile_markdown(profile),
            "scored": c.score_demos(profile),
            "matrix_md": c.build_matrix_markdown(profile),
            "schedule_md": c.build_schedule_markdown(profile),
            "runbook_md": c.build_runbook_markdown(profile),
        }
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 5. GStack
# ==========================
@app.get("/api/gstack")
async def gstack(command: str = Query(...), input: str | None = None):
    c = cores["gstack"]
    return {"command": command, "script": c.run_command(command, user_input=input)}


# ==========================
# 6. Hypothesis
# ==========================
@app.post("/api/hypothesis")
async def hypothesis(body: dict = Body(default={})):
    c = cores["hypothesis"]
    text = body.get("text") or ""
    return {"annotations": c.classify_sentences(text)}


# ==========================
# 7. Karpathy KB
# ==========================
@app.post("/api/karpathy")
async def karpathy(action: str = "extract", body: dict = Body(default={})):
    c = cores["karpathy-kb"]
    if action == "extract":
        text = body.get("text") or ""
        n = int(body.get("n", 5))
        return {"concepts": c.extract_concepts(text, n=n)}
    if action == "lint":
        concepts = body.get("concepts") or []
        return c.lint_kb(concepts)
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 8. Maestro
# ==========================
@app.post("/api/maestro")
async def maestro(action: str = "parse", body: dict = Body(default={})):
    c = cores["maestro"]
    yaml_text = body.get("yaml") or ""
    parsed = c.parse_yaml(yaml_text)
    if action == "parse":
        return parsed
    if action == "simulate":
        return {"parsed": parsed, "trace": c.simulate_execution(parsed)}
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 9. Org-Uplift
# ==========================
@app.post("/api/org_uplift")
async def org_uplift(action: str = "execute", body: dict = Body(default={})):
    c = cores["org-uplift"]
    if action == "execute":
        return c.execute_task(
            task_description=body.get("task", ""),
            context=body.get("context", ""),
            player=body.get("player", ""),
            scenario=body.get("scenario", "startup"),
        )
    if action == "stats":
        return c.compute_stats(body.get("tasks") or [])
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 10. Playwright
# ==========================
@app.get("/api/playwright")
async def playwright(scenario: str = "bing"):
    c = cores["playwright"]
    trace = c.simulate_run(scenario)
    # core.SCENARIOS stores metadata
    meta = getattr(c, "SCENARIOS", {}).get(scenario, {})
    return {
        "scenario": scenario,
        "title": meta.get("title", scenario),
        "script": meta.get("script", []),
        "trace": trace,
    }


# ==========================
# 11. PPT Gen
# ==========================
@app.post("/api/ppt")
async def ppt(body: dict = Body(default={})):
    c = cores["ppt-gen"]
    pptx_bytes = c.generate_pptx(
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


# ==========================
# 12. SA Toolkit
# ==========================
@app.post("/api/sa_toolkit")
async def sa_toolkit(action: str = "gen", body: dict = Body(default={})):
    c = cores["sa-toolkit"]
    if action == "gen":
        company = body.get("company") or "Acme Inc"
        info = c.search_company(company)
        pkg = c.generate_package(info) if hasattr(c, "generate_package") else {"profile": info}
        return {"company_info": info, "package": pkg}
    if action == "customize":
        pkg = body.get("package") or {}
        act = body.get("sub_action") or body.get("act") or "replace_terms"
        params = body.get("params") or {}
        if act == "replace_terms": return c.replace_terms(pkg, params.get("mapping") or {})
        if act == "deepen_demo": return c.deepen_demo(pkg, params.get("demo_id", ""))
        if act == "switch_audience": return c.switch_audience(pkg, params.get("audience", "executives"))
        raise HTTPException(400, f"unknown sub_action {act}")
    if action == "present":
        pkg = body.get("package") or {}
        mode = body.get("mode") or "rehearse"
        if mode == "rehearse": return {"plan": c.rehearse(pkg)}
        if mode == "email": return {"email": c.export_email(pkg)}
        raise HTTPException(400, f"unknown mode {mode}")
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# Static file hosting
# ==========================
# Every /<demo>/ URL maps to docs/<demo>/index.html; /<demo>/<file> serves the file.

@app.get("/health")
async def health():
    return {"status": "ok", "demos": list(cores.keys())}

# Clean-URL redirects: /org-uplift → /org-uplift/
_DEMO_PATHS = [
    "org-uplift", "ceo-dashboard", "autoresearch", "industrial-ai",
    "karpathy-kb", "gstack", "hypothesis", "ppt-gen",
    "maestro", "playwright", "enterprise-gen", "sa-toolkit",
]
for demo in _DEMO_PATHS:
    app.mount(f"/{demo}", StaticFiles(directory=str(DOCS / demo), html=True), name=demo)

# Root: serve docs/index.html
@app.get("/")
async def root():
    return FileResponse(str(DOCS / "index.html"))

# Catch-all for assets at root (favicon, etc)
app.mount("/", StaticFiles(directory=str(DOCS), html=True), name="docs")
