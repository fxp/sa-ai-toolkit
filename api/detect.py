from http.server import BaseHTTPRequestHandler
import json, sys, os

# Add api/ to path so we can import _pipeline
sys.path.insert(0, os.path.dirname(__file__))
from _pipeline import PerceptionLayer

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        result = {
            "visual": PerceptionLayer.detect_visual(),
            "audio": PerceptionLayer.detect_audio()
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
