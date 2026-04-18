from http.server import BaseHTTPRequestHandler
import json
import os
import sys

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "demos", "hypothesis-py"),
)
from core import classify_sentences  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(body or "{}")
            text = data.get("text", "")
            if not isinstance(text, str) or not text.strip():
                return self._json(400, {"error": "Missing 'text' in body"})
            annotations = classify_sentences(text)
            self._json(200, {"annotations": annotations, "count": len(annotations)})
        except Exception as e:  # noqa: BLE001
            self._json(500, {"error": f"internal: {e}"})

    def do_GET(self):
        self._json(405, {"error": "Use POST with {\"text\": \"...\"}"})

    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _json(self, code, data):
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self._cors()
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))
