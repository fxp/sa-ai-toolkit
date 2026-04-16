from http.server import BaseHTTPRequestHandler
import json, sys, os

sys.path.insert(0, os.path.dirname(__file__))
from _pipeline import PerceptionLayer, PredictionLayer, OntologyLayer, DiagnosisLayer

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length)) if length else {}
        vis = body.get("visual", PerceptionLayer.detect_visual())
        aud = body.get("audio", PerceptionLayer.detect_audio())
        pred = body.get("prediction", PredictionLayer.predict_equipment_rul())
        ont = body.get("ontology", OntologyLayer.trace_root_cause("defect"))
        diag = DiagnosisLayer.diagnose(vis, pred, ont, aud, body.get("use_llm", False))
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(diag, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
