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
    run_pipeline, DATASETS, DEFAULT_DATASET,
)

STATIC = pathlib.Path("/app/static")

app = FastAPI(title="Industrial AI Pipeline", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Health (for status aggregator) ──
@app.get("/health")
async def health():
    return {"status": "ok", "demo": "industrial-ai"}


# ── API ──
def _resolve_dataset(name: str | None) -> str:
    return name if name in DATASETS else DEFAULT_DATASET


@app.get("/api/industrial")
async def industrial_get(action: str = "health", dataset: str | None = None):
    if action == "health":
        return {"status": "ok", "pipeline": "industrial-ai-v1",
                "layers": ["SAM3", "SAM-Audio", "TimesFM", "LLM"],
                "datasets": list(DATASETS.keys())}
    if action == "datasets":
        return {"default": DEFAULT_DATASET,
                "datasets": [dict(d) for d in DATASETS.values()]}
    ds_id = _resolve_dataset(dataset)
    if action == "detect":
        return {
            "visual": PerceptionLayer.detect_visual(dataset=ds_id),
            "audio": PerceptionLayer.detect_audio(),
        }
    if action == "predict":
        return {
            "yield_forecast": PredictionLayer.forecast(None, 72, "yield"),
            "rul": PredictionLayer.predict_equipment_rul(),
        }
    if action == "run":
        return run_pipeline(use_llm=False, verbose=False, dataset=ds_id)
    raise HTTPException(400, f"unknown action {action}")


@app.post("/api/industrial")
async def industrial_post(action: str = "run", dataset: str | None = None,
                          body: dict = Body(default={})):
    ds_id = _resolve_dataset(dataset or body.get("dataset"))
    if action == "run":
        return run_pipeline(use_llm=body.get("use_llm", False), verbose=False, dataset=ds_id)
    if action == "diagnose":
        vis = body.get("visual") or PerceptionLayer.detect_visual(dataset=ds_id)
        aud = body.get("audio") or PerceptionLayer.detect_audio()
        pred = body.get("prediction") or PredictionLayer.predict_equipment_rul()
        seed = (vis.get("detections") or [{}])[0].get("label", "defect")
        ont = body.get("ontology") or OntologyLayer.trace_root_cause(seed)
        diag = DiagnosisLayer.diagnose(vis, pred, ont, aud, body.get("use_llm", False))
        diag["dataset"] = vis.get("dataset")
        return diag
    raise HTTPException(400, f"unknown action {action}")


# ── Static frontend ──
# Root serves the demo's index.html; subpaths resolve against docs/industrial-ai/
if STATIC.is_dir():
    app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")
