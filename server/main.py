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
    mod_name = f"demo_{demo.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(mod_name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod  # register BEFORE exec so @dataclass can resolve the module
    spec.loader.exec_module(mod)
    return mod

cores = {name: _load(name) for name in [
    "industrial-ai", "ceo-agent", "autoresearch", "autoresearch-vrp",
    "enterprise-gen", "gstack", "hypothesis", "karpathy-kb", "maestro",
    "org-uplift", "playwright", "ppt-gen", "sa-toolkit",
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
    if action == "brief": return {"company": company, "idx": idx, "lang": lang, "brief": agent.morning_brief(brief_idx=idx, lang=lang)}
    if action == "metrics": return agent.metrics(lang=lang)
    if action == "decisions": return {"decisions": agent.decisions(lang=lang)}
    if action == "mood": return agent.mood_heatmap(lang=lang)
    if action == "competitors": return {"feed": agent.competitor_feed(lang=lang)}
    if action == "actions": return {"actions": agent.action_queue(lang=lang)}
    if action == "chips": return {"chips": cores["ceo-agent"].ask_chips(lang=lang)}
    if action == "projects": return {"projects": agent.projects(lang=lang)}
    if action == "all": return agent.all(brief_idx=idx, lang=lang)
    raise HTTPException(400, f"unknown action {action}")


@app.post("/api/ceo")
async def ceo_post(action: str = "ask", body: dict = Body(default={})):
    CEOAgent = cores["ceo-agent"].CEOAgent
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


# ==========================
# 3. AutoResearch — autonomous algorithm-discovery loop on scheduling
# ==========================
@app.post("/api/research")
async def research_post(action: str = "iterate", body: dict = Body(default={})):
    """action=iterate — run one solver variant, return code + metric + schedule
       action=full    — run all variants and return the full trajectory"""
    c = cores["autoresearch"]
    lang = body.get("lang", "en")
    if action == "iterate":
        iter_idx = int(body.get("iter_idx", 0))
        return c.run_iteration(iter_idx, lang=lang)
    if action == "full":
        return c.run_full(lang=lang)
    raise HTTPException(400, f"unknown action {action}")


@app.get("/api/research")
async def research_get(action: str = "instance", lang: str = "en"):
    """action=instance — benchmark orders + program.md
       action=meta     — variant catalog (name/hypothesis only, no code)"""
    c = cores["autoresearch"]
    if action == "instance":
        return {
            "instance": c.get_instance_payload(),
            "program_md": c.get_program_md(lang=lang),
            "num_iterations": c.NUM_ITERATIONS,
        }
    if action == "meta":
        return {
            "num_iterations": c.NUM_ITERATIONS,
            "variants": [
                {"idx": v["idx"], "name": v["name"], "name_zh": v["name_zh"],
                 "hypothesis": v["hypothesis"], "hypothesis_zh": v["hypothesis_zh"]}
                for v in c.VARIANTS
            ],
        }
    raise HTTPException(400, f"unknown action {action}")


# ==========================
# 3b. AutoResearch-VRP — same pattern, applied to last-mile routing
# ==========================
@app.post("/api/vrp")
async def vrp_post(action: str = "iterate", body: dict = Body(default={})):
    c = cores["autoresearch-vrp"]
    lang = body.get("lang", "en")
    if action == "iterate":
        return c.run_iteration(int(body.get("iter_idx", 0)), lang=lang)
    if action == "full":
        return c.run_full(lang=lang)
    raise HTTPException(400, f"unknown action {action}")


@app.get("/api/vrp")
async def vrp_get(action: str = "instance", lang: str = "en"):
    c = cores["autoresearch-vrp"]
    if action == "instance":
        return {
            "instance": c.get_instance_payload(),
            "program_md": c.get_program_md(lang=lang),
            "num_iterations": c.NUM_ITERATIONS,
        }
    if action == "meta":
        return {
            "num_iterations": c.NUM_ITERATIONS,
            "variants": [
                {"idx": v["idx"], "name": v["name"], "name_zh": v["name_zh"],
                 "hypothesis": v["hypothesis"], "hypothesis_zh": v["hypothesis_zh"]}
                for v in c.VARIANTS
            ],
        }
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


@app.post("/api/gstack")
async def gstack_turn(body: dict = Body(default={})):
    """Multi-turn endpoint — client passes {command, turn, input, history}."""
    c = cores["gstack"]
    return c.run_turn(
        command=body.get("command") or "",
        turn=int(body.get("turn") or 0),
        user_input=body.get("input"),
        history=body.get("history") or [],
    )


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
# Status / health dashboard
# ==========================
# /api/status runs each demo's fast-path core function in-process, times it,
# and returns structured health info. Frontend polls this every 30s.

import time
import traceback

# Each entry: (display_name, fast-path callable returning any, endpoint_hint)
def _status_checks():
    ia = cores["industrial-ai"]
    ca = cores["ceo-agent"]
    ar = cores["autoresearch"]
    eg = cores["enterprise-gen"]
    gs = cores["gstack"]
    hy = cores["hypothesis"]
    kb = cores["karpathy-kb"]
    ms = cores["maestro"]
    ou = cores["org-uplift"]
    pw = cores["playwright"]
    pg = cores["ppt-gen"]
    sa = cores["sa-toolkit"]

    sample_profile = {
        "company": "Acme Inc", "industry": "banking-finance",
        "pain_points": ["A", "D"], "audience": "executives",
        "minutes": 90, "size": "1000-10000",
    }
    sample_yaml = "appId: com.test\n---\n- launchApp\n- assertVisible: \"Home\"\n"
    sample_text = "The market grew to $2.1T in 2024. However, consolidation is accelerating. We should focus on platform plays."

    return [
        ("industrial-ai", "/api/industrial?action=detect",
         lambda: {"detections": len(ia.PerceptionLayer.detect_visual().get("detections", []))}),
        ("ceo-agent", "/api/ceo?action=metrics",
         lambda: {"metrics_keys": len(ca.CEOAgent(company="NewCo Inc").metrics())}),
        ("autoresearch", "/api/research?action=stage",
         lambda: {"stage": ar.run_stage("AI agents 2026", 0, prev_results=[]).get("name", "?")}),
        ("enterprise-gen", "/api/enterprise?action=score",
         lambda: {"scored": len(eg.score_demos(sample_profile))}),
        ("gstack", "/api/gstack?command=office-hours",
         lambda: {"steps": len(gs.run_command("office-hours"))}),
        ("hypothesis", "/api/hypothesis",
         lambda: {"annotations": len(hy.classify_sentences(sample_text))}),
        ("karpathy-kb", "/api/karpathy?action=extract",
         lambda: {"concepts": len(kb.extract_concepts(sample_text, n=3))}),
        ("maestro", "/api/maestro?action=parse",
         lambda: {"steps": len((ms.parse_yaml(sample_yaml) or {}).get("steps") or [])}),
        ("org-uplift", "/api/org_uplift?action=execute",
         lambda: {"dice_success": ou.execute_task(
             task_description="write a spec",
             context="sprint planning",
             player="Alice",
             scenario="startup",
         ).get("dice", {}).get("success")}),
        ("playwright", "/api/playwright?scenario=bing",
         lambda: {"trace_steps": len(pw.simulate_run("bing"))}),
        ("ppt-gen", "/api/ppt",
         lambda: {"bytes": len(pg.generate_pptx(
             title="Smoke", subtitle="Check",
             slides=[{"template": "cover", "fields": {"title": "x"}}],
             theme="blue-orange",
         ))}),
        ("sa-toolkit", "/api/sa_toolkit?action=gen",
         lambda: {"fields": list((sa.search_company("Tencent") or {}).keys())}),
    ]


_STATUS_CACHE: dict[str, Any] = {"ts": 0, "payload": None}
_CACHE_TTL = 15  # seconds


def _compute_status() -> dict:
    demos = []
    fail = 0
    slow = 0
    total_ms = 0
    for name, endpoint, fn in _status_checks():
        t0 = time.perf_counter()
        entry: dict[str, Any] = {"name": name, "endpoint": endpoint}
        try:
            details = fn()
            ms = round((time.perf_counter() - t0) * 1000, 1)
            entry["status"] = "ok" if ms < 1500 else "slow"
            entry["latency_ms"] = ms
            entry["details"] = details
            if entry["status"] == "slow":
                slow += 1
            total_ms += ms
        except Exception as e:
            ms = round((time.perf_counter() - t0) * 1000, 1)
            entry["status"] = "down"
            entry["latency_ms"] = ms
            entry["error"] = f"{type(e).__name__}: {e}"
            entry["traceback"] = traceback.format_exc().splitlines()[-3:]
            fail += 1
        demos.append(entry)

    if fail > 0:
        overall = "down" if fail >= 3 else "degraded"
    elif slow > 0:
        overall = "degraded"
    else:
        overall = "ok"

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall": overall,
        "total_demos": len(demos),
        "healthy": len(demos) - fail - slow,
        "slow": slow,
        "down": fail,
        "total_check_ms": round(total_ms, 1),
        "demos": demos,
    }


@app.get("/api/status")
async def api_status(fresh: bool = False):
    now = time.time()
    if not fresh and _STATUS_CACHE["payload"] and now - _STATUS_CACHE["ts"] < _CACHE_TTL:
        return {**_STATUS_CACHE["payload"], "cached": True, "cache_age_s": round(now - _STATUS_CACHE["ts"], 1)}
    payload = _compute_status()
    _STATUS_CACHE["ts"] = now
    _STATUS_CACHE["payload"] = payload
    return {**payload, "cached": False}


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
    "xinglian-office-hour",  # static-only demo
    "status",                # live status dashboard
]
# Mount only directories that actually exist on disk
_DEMO_PATHS = [p for p in _DEMO_PATHS if (DOCS / p).is_dir()]
for demo in _DEMO_PATHS:
    app.mount(f"/{demo}", StaticFiles(directory=str(DOCS / demo), html=True), name=demo)

# Root: serve docs/index.html
@app.get("/")
async def root():
    return FileResponse(str(DOCS / "index.html"))

# Catch-all for assets at root (favicon, etc)
app.mount("/", StaticFiles(directory=str(DOCS), html=True), name="docs")
