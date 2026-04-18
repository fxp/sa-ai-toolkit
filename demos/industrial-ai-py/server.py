"""
Standalone FastAPI server for Industrial AI demo.
Mounts docs/industrial-ai/ as static site + /api/industrial endpoints.
"""
from __future__ import annotations
import pathlib
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Import the demo's core. When containerised, /app/demo is on sys.path.
from core import (
    PerceptionLayer, PredictionLayer, OntologyLayer, DiagnosisLayer,
    run_pipeline,
)

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Industrial AI Pipeline", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Health (for status aggregator) ──
@app.get("/health")
async def health():
    return {"status": "ok", "demo": "industrial-ai"}


# ── API ──
@app.get("/api/industrial")
async def industrial_get(action: str = "health", dataset: str | None = None):
    if action == "health":
        return {"status": "ok", "pipeline": "industrial-ai-v1",
                "layers": ["SAM3", "SAM-Audio", "TimesFM", "LLM"]}
    if action == "detect":
        return {
            "visual": PerceptionLayer.detect_visual(dataset=dataset) if "dataset" in PerceptionLayer.detect_visual.__code__.co_varnames else PerceptionLayer.detect_visual(),
            "audio": PerceptionLayer.detect_audio(),
        }
    if action == "predict":
        return {
            "yield_forecast": PredictionLayer.forecast(None, 72, "yield"),
            "rul": PredictionLayer.predict_equipment_rul(),
        }
    if action == "run":
        return run_pipeline(use_llm=False, verbose=False)
    raise HTTPException(400, f"unknown action {action}")


@app.post("/api/industrial")
async def industrial_post(action: str = "run", body: dict = Body(default={})):
    if action == "run":
        return run_pipeline(use_llm=body.get("use_llm", False), verbose=False)
    if action == "diagnose":
        vis = body.get("visual") or PerceptionLayer.detect_visual()
        aud = body.get("audio") or PerceptionLayer.detect_audio()
        pred = body.get("prediction") or PredictionLayer.predict_equipment_rul()
        ont = body.get("ontology") or OntologyLayer.trace_root_cause("defect")
        return DiagnosisLayer.diagnose(vis, pred, ont, aud, body.get("use_llm", False))
    raise HTTPException(400, f"unknown action {action}")


# ── Static frontend ──
# Root serves the demo's index.html; subpaths resolve against docs/industrial-ai/
if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
