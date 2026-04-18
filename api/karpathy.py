"""Consolidated Karpathy KB handler. ?action=extract|lint (POST)."""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "demos", "karpathy-kb-py"),
)
from core import extract_concepts, lint_kb  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed.query)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(body or "{}")
        except Exception as e:
            return self._json(400, {"error": f"invalid JSON: {e}"})
        action = (params.get("action") or [""])[0] or data.get("action") or ""
        try:
            if action == "extract":
                text = data.get("text", "")
                n = int(data.get("n", 5))
                if not isinstance(text, str) or not text.strip():
                    return self._json(400, {"error": "Missing 'text' in body"})
                concepts = extract_concepts(text, n)
                self._json(200, {"concepts": concepts, "count": len(concepts)})
            elif action == "lint":
                concepts = data.get("concepts")
                if concepts is None:
                    return self._json(400, {"error": "Missing 'concepts' in body"})
                if not isinstance(concepts, list):
                    return self._json(400, {"error": "'concepts' must be a list"})
                self._json(200, lint_kb(concepts))
            else:
                self._json(400, {"error": "unknown action", "available": ["extract", "lint"]})
        except Exception as e:  # noqa: BLE001
            self._json(500, {"error": f"internal: {e}"})

    def do_GET(self):
        self._json(405, {"error": "Use POST with ?action=extract|lint"})

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
