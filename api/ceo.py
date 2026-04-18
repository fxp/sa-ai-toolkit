"""Consolidated CEO agent handler.

Dispatches: ?action=brief|metrics|decisions|mood|competitors|actions|chips|all
All GET with ?company=X&lang=Y. 'brief' also accepts ?idx=N.
POST ?action=ask with body {query, company, lang} for the ask-anything agent.
"""
from http.server import BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "demos", "ceo-agent-py"))
from core import CEOAgent, ask_chips  # noqa: E402


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = parse_qs(urlparse(self.path).query)
        action = (q.get("action") or [""])[0]
        company = q.get("company", ["NewCo Inc"])[0]
        lang = q.get("lang", ["en"])[0]
        try:
            agent = CEOAgent(company=company)
            if action == "brief":
                idx = int(q.get("idx", ["0"])[0])
                data = agent.morning_brief(idx, lang)
                self._json(200, {"company": company, "idx": idx, "lang": lang, "brief": data})
            elif action == "metrics":
                self._json(200, agent.metrics(lang))
            elif action == "decisions":
                self._json(200, {"decisions": agent.decisions(lang)})
            elif action == "mood":
                self._json(200, agent.mood_heatmap(lang))
            elif action == "competitors":
                self._json(200, {"feed": agent.competitor_feed(lang)})
            elif action == "actions":
                self._json(200, {"actions": agent.action_queue(lang)})
            elif action == "chips":
                self._json(200, {"chips": ask_chips(lang)})
            elif action == "all":
                idx = int(q.get("idx", ["0"])[0])
                self._json(200, {
                    "company": company,
                    "lang": lang,
                    "brief": agent.morning_brief(idx, lang),
                    "metrics": agent.metrics(lang),
                    "decisions": agent.decisions(lang),
                    "mood": agent.mood_heatmap(lang),
                    "competitors": agent.competitor_feed(lang),
                    "actions": agent.action_queue(lang),
                })
            else:
                self._json(400, {"error": "unknown action", "available": [
                    "brief", "metrics", "decisions", "mood", "competitors", "actions", "chips", "all"]})
        except Exception as e:
            self._json(500, {"error": str(e)})

    def do_POST(self):
        length = int(self.headers.get("content-length") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            body = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            self._json(400, {"error": "invalid JSON body"})
            return
        q = parse_qs(urlparse(self.path).query)
        action = (q.get("action") or [body.get("action", "ask")])[0]
        if action != "ask":
            self._json(400, {"error": "unknown action (POST only supports 'ask')"})
            return
        try:
            agent = CEOAgent(company=body.get("company", "NewCo Inc"))
            self._json(200, agent.ask(query=body.get("query", ""), lang=body.get("lang", "en")))
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
