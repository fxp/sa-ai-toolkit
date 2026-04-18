"""Consolidated org-uplift handler. ?action=execute|stats (POST)."""
from http.server import BaseHTTPRequestHandler
import json
import os
import urllib.parse
import importlib.util as _ilu

_CORE_PATH = os.path.join(os.path.dirname(__file__), '..', 'demos', 'org-uplift-py', 'core.py')
_spec = _ilu.spec_from_file_location("uplift_core", _CORE_PATH)
_mod = _ilu.module_from_spec(_spec); _spec.loader.exec_module(_mod)
execute_task = _mod.execute_task
compute_stats = _mod.compute_stats


class handler(BaseHTTPRequestHandler):
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
        try:
            if action == "execute":
                task = (body.get("task") or "").strip()
                if not task:
                    self._json(400, {"error": "missing task"})
                    return
                res = execute_task(
                    task_description=task,
                    context=body.get("context", ""),
                    player=body.get("player", ""),
                    scenario=body.get("scenario", ""),
                )
                self._json(200, res)
            elif action == "stats":
                tasks = body.get("tasks") or []
                if not isinstance(tasks, list):
                    self._json(400, {"error": "tasks must be a list"})
                    return
                self._json(200, compute_stats(tasks))
            else:
                self._json(400, {"error": "unknown action", "available": ["execute", "stats"]})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_GET(self):
        self._json(200, {"usage": "POST ?action=execute|stats"})

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
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode())
