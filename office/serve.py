#!/usr/bin/env python3
"""Serves the 3D office at http://localhost:8787 and streams live agent events from office/events.jsonl.

usage: python3 office/serve.py [port]
Open the URL in a browser, then run Claude Code in this repo: each sub-agent that starts lights up in its room.
"""
import json, os, sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
EVENTS = os.path.join(HERE, "events.jsonl")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8787


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=HERE, **kw)

    def log_message(self, *a):
        pass

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/events":
            since = int(parse_qs(u.query).get("since", ["0"])[0])
            lines = []
            if os.path.exists(EVENTS):
                with open(EVENTS, encoding="utf-8") as f:
                    lines = f.read().splitlines()
            body = json.dumps({"total": len(lines), "events": [json.loads(l) for l in lines[since:] if l.strip()]}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        if u.path == "/":
            self.path = "/index.html"
        super().do_GET()


if __name__ == "__main__":
    print(f"AI office: http://localhost:{PORT}  (events from {os.path.relpath(EVENTS)})")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
