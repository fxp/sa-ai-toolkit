from http.server import BaseHTTPRequestHandler
import json, sys, os

sys.path.insert(0, os.path.dirname(__file__))
from _pipeline import PredictionLayer

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = {
            "yield_forecast": PredictionLayer.forecast(None, 72, "yield"),
            "rul": PredictionLayer.predict_equipment_rul()
        }
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(result, ensure_ascii=False).encode())

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
