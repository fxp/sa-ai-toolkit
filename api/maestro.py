"""Consolidated Maestro handler. ?action=parse|simulate (POST)."""
from http.server import BaseHTTPRequestHandler
import json
import os
import sys
import urllib.parse

sys.path.insert(
    0,
    os.path.join(os.path.dirname(__file__), "..", "demos", "maestro-py"),
)
from core import parse_yaml, simulate_execution  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(parsed_url.query)
        try:
            length = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(length).decode("utf-8") if length else "{}"
            data = json.loads(body or "{}")
        except Exception as e:
            return self._json(400, {"error": f"invalid JSON: {e}"})
        action = (params.get("action") or [""])[0] or data.get("action") or ""
        yaml_text = data.get("yaml", "")
        if not isinstance(yaml_text, str) or not yaml_text.strip():
            return self._json(400, {"error": "Missing 'yaml' in body"})
        try:
            if action == "parse":
                parsed = parse_yaml(yaml_text)
                self._json(200, {"parsed": parsed})
            elif action == "simulate":
                parsed = parse_yaml(yaml_text)
                trace = simulate_execution(parsed)
                self._json(200, {"parsed": parsed, "trace": trace})
            else:
                self._json(400, {"error": "unknown action", "available": ["parse", "simulate"]})
        except Exception as e:  # noqa: BLE001
            self._json(400, {"error": f"{action} error: {e}"})

    def do_GET(self):
        self._json(405, {"error": "Use POST with ?action=parse|simulate and {\"yaml\": \"...\"}"})

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
