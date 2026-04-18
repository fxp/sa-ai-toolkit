"""Consolidated industrial AI pipeline handler.

Dispatches: ?action=detect|predict|diagnose|run|health
- detect/predict/run/health: GET (run also accepts POST with body)
- diagnose: POST
"""
from http.server import BaseHTTPRequestHandler
import json, sys, os, urllib.parse

sys.path.insert(0, os.path.dirname(__file__))
from _pipeline import (
    PerceptionLayer,
    PredictionLayer,
    OntologyLayer,
    DiagnosisLayer,
    run_pipeline,
    DATASETS,
    DEFAULT_DATASET,
)


def _dataset_param(params, body=None):
    ds = (params.get("dataset") or [""])[0] if params else ""
    if not ds and body:
        ds = body.get("dataset") or ""
    return ds if ds in DATASETS else DEFAULT_DATASET


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        action = (params.get("action") or [""])[0]
        ds_id = _dataset_param(params)
        try:
            if action == "detect":
                result = {
                    "visual": PerceptionLayer.detect_visual(dataset=ds_id),
                    "audio": PerceptionLayer.detect_audio(),
                }
                self._json(200, result)
            elif action == "predict":
                result = {
                    "yield_forecast": PredictionLayer.forecast(None, 72, "yield"),
                    "rul": PredictionLayer.predict_equipment_rul(),
                }
                self._json(200, result)
            elif action == "run":
                self._json(200, run_pipeline(use_llm=False, verbose=False, dataset=ds_id))
            elif action == "datasets":
                # Expose the full real-data registry (minus any internal-only keys).
                self._json(200, {
                    "default": DEFAULT_DATASET,
                    "datasets": [
                        {k: v for k, v in d.items()}
                        for d in DATASETS.values()
                    ],
                })
            elif action == "health":
                self._json(200, {
                    "status": "ok",
                    "pipeline": "industrial-ai-v1",
                    "layers": ["SAM3", "SAM-Audio", "TimesFM", "LLM"],
                    "datasets": list(DATASETS.keys()),
                    "deployment": "vercel-serverless",
                })
            else:
                self._json(400, {"error": "unknown action",
                                 "available": ["detect", "predict", "run", "diagnose",
                                               "datasets", "health"]})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length)) if length else {}
        except Exception:
            self._json(400, {"error": "invalid JSON"})
            return
        action = (params.get("action") or [""])[0] or body.get("action") or ""
        ds_id = _dataset_param(params, body)
        try:
            if action == "diagnose":
                vis = body.get("visual", PerceptionLayer.detect_visual(dataset=ds_id))
                aud = body.get("audio", PerceptionLayer.detect_audio())
                pred = body.get("prediction", PredictionLayer.predict_equipment_rul())
                defect_seed = (vis.get("detections") or [{}])[0].get("label", "defect")
                ont = body.get("ontology", OntologyLayer.trace_root_cause(defect_seed))
                diag = DiagnosisLayer.diagnose(vis, pred, ont, aud, body.get("use_llm", False))
                diag["dataset"] = vis.get("dataset")
                self._json(200, diag)
            elif action == "run":
                use_llm = body.get("use_llm", False)
                self._json(200, run_pipeline(use_llm=use_llm, verbose=False, dataset=ds_id))
            else:
                self._json(400, {"error": "unknown action",
                                 "available": ["diagnose", "run"]})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
