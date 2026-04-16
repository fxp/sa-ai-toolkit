from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "ok",
            "pipeline": "industrial-ai-v1",
            "layers": ["SAM3", "SAM-Audio", "TimesFM", "LLM"],
            "deployment": "vercel-serverless"
        }).encode())
