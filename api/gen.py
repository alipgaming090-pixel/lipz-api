from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import json

class handler(BaseHTTPRequestHandler):
    def _json(self, payload, status=200):
        body = json.dumps(payload, separators=(",", ":")).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        query = parse_qs(urlparse(self.path).query)

        try:
            requested = int(query.get("count", ["1"])[0])
        except (ValueError, TypeError):
            requested = 1

        requested = max(1, min(requested, 100))

        self._json({
            "accounts": [],
            "attempts_made": 3,
            "rare_count": 0,
            "success": True,
            "total_created": 0,
            "total_requested": requested
        })
